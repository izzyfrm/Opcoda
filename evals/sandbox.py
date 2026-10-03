"""Run model-generated functions against held-out tests with layered isolation.

This is a *lightweight* sandbox meant for tiny, pure functions produced by
Coda. Layers, outermost first:

1. Static gate (in this process, nothing is executed): the source must be a
   single top-level ``def`` using a pure-computation subset of Python. No
   imports, no dunder names or attributes, no names like open/exec/eval/
   getattr, no classes, ``with``, ``global``, async, or "__" in strings.
2. Separate interpreter: ``python -I -S`` in a temporary working directory
   with a minimal environment. The model's code never runs in the training or
   benchmark process.
3. OS limits applied by the child *before* it reads the code:
   Windows Job Object (memory cap, no child processes, CPU-time cap) or POSIX
   rlimits. If limits cannot be applied the child refuses to run anything.
4. Restricted builtins: the code only sees an allowlist (len, range, sorted, ...).
5. Wall-clock timeout enforced by the parent, which kills the process.

It is a reasonable guard for a 3M-parameter model's toy functions. It is not
a security boundary against a determined attacker; for that, run CodaBench
inside a disposable VM or container.
"""
from __future__ import annotations

import ast
import json
import os
import subprocess
import sys
import tempfile

SAFE_BUILTINS = [
    "abs", "all", "any", "bool", "chr", "dict", "divmod", "enumerate", "filter", "float",
    "format", "frozenset", "int", "isinstance", "len", "list", "map", "max", "min", "next",
    "ord", "pow", "range", "repr", "reversed", "round", "set", "sorted", "str", "sum",
    "tuple", "zip", "bin", "hex", "oct", "iter", "slice",
    "True", "False", "None",
    "Exception", "ValueError", "TypeError", "KeyError", "IndexError", "ZeroDivisionError",
    "StopIteration", "ArithmeticError", "LookupError",
]

FORBIDDEN_NAMES = {
    "open", "exec", "eval", "compile", "__import__", "globals", "locals", "vars", "dir",
    "getattr", "setattr", "delattr", "hasattr", "input", "breakpoint", "exit", "quit",
    "help", "memoryview", "bytearray", "type", "object", "super", "classmethod",
    "staticmethod", "property", "callable", "id", "hash", "print", "copyright", "credits",
    "license",
}

FORBIDDEN_NODES = (
    ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal, ast.ClassDef, ast.AsyncFunctionDef,
    ast.Await, ast.AsyncFor, ast.AsyncWith, ast.With, ast.Delete,
)

# Pure-computation standard library modules a program may import in "module" mode.
SAFE_MODULES = {"math", "re", "collections", "itertools", "functools", "string", "heapq", "bisect",
                "statistics", "operator", "typing", "dataclasses", "fractions", "decimal"}

MEMORY_LIMIT_BYTES = 256 * 1024 * 1024
CPU_SECONDS = 5
WALL_SECONDS = 10

# The child program. It applies OS limits first, then runs the tests.
RUNNER = r'''
import sys

MEM = int(sys.argv[1])
CPU = int(sys.argv[2])


def apply_limits():
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        class IO_COUNTERS(ctypes.Structure):
            _fields_ = [(n, ctypes.c_ulonglong) for n in (
                "ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]

        class BASIC(ctypes.Structure):
            _fields_ = [
                ("PerProcessUserTimeLimit", ctypes.c_int64), ("PerJobUserTimeLimit", ctypes.c_int64),
                ("LimitFlags", wintypes.DWORD), ("MinimumWorkingSetSize", ctypes.c_size_t),
                ("MaximumWorkingSetSize", ctypes.c_size_t), ("ActiveProcessLimit", wintypes.DWORD),
                ("Affinity", ctypes.c_size_t), ("PriorityClass", wintypes.DWORD),
                ("SchedulingClass", wintypes.DWORD)]

        class EXTENDED(ctypes.Structure):
            _fields_ = [
                ("BasicLimitInformation", BASIC), ("IoInfo", IO_COUNTERS),
                ("ProcessMemoryLimit", ctypes.c_size_t), ("JobMemoryLimit", ctypes.c_size_t),
                ("PeakProcessMemoryUsed", ctypes.c_size_t), ("PeakJobMemoryUsed", ctypes.c_size_t)]

        k32 = ctypes.WinDLL("kernel32", use_last_error=True)
        k32.CreateJobObjectW.restype = wintypes.HANDLE
        k32.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
        k32.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
        k32.GetCurrentProcess.restype = wintypes.HANDLE
        k32.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]

        job = k32.CreateJobObjectW(None, None)
        if not job:
            raise OSError("CreateJobObject failed")
        info = EXTENDED()
        # PROCESS_TIME | ACTIVE_PROCESS | PROCESS_MEMORY | KILL_ON_JOB_CLOSE
        info.BasicLimitInformation.LimitFlags = 0x2 | 0x8 | 0x100 | 0x2000
        info.BasicLimitInformation.PerProcessUserTimeLimit = CPU * 10_000_000
        info.BasicLimitInformation.ActiveProcessLimit = 1
        info.ProcessMemoryLimit = MEM
        if not k32.SetInformationJobObject(job, 9, ctypes.byref(info), ctypes.sizeof(info)):
            raise OSError("SetInformationJobObject failed")
        if not k32.AssignProcessToJobObject(job, k32.GetCurrentProcess()):
            raise OSError("AssignProcessToJobObject failed")
        globals()["_JOB"] = job  # keep the handle alive
    else:
        import resource
        resource.setrlimit(resource.RLIMIT_AS, (MEM, MEM))
        resource.setrlimit(resource.RLIMIT_CPU, (CPU, CPU))
        if hasattr(resource, "RLIMIT_NPROC"):
            resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))
        resource.setrlimit(resource.RLIMIT_FSIZE, (0, 0))


try:
    apply_limits()
except Exception as exc:
    sys.stdout.write('{"sandbox_error": "could not apply limits: %s"}' % type(exc).__name__)
    sys.exit(3)

import ast
import builtins
import copy
import json
import math

payload = json.loads(sys.stdin.read())


def same(a, b, mode):
    if mode == "unordered" and isinstance(a, list) and isinstance(b, list):
        try:
            return sorted(a) == sorted(b) and len(a) == len(b)
        except TypeError:
            return False
    if isinstance(a, bool) or isinstance(b, bool):
        return a is b
    if isinstance(a, (int, float)) and isinstance(b, (int, float)):
        return math.isclose(a, b, rel_tol=1e-9, abs_tol=1e-9)
    return a == b


safe = {name: getattr(builtins, name) for name in payload["builtins"]}
modules = set(payload.get("modules") or ())
if modules:
    _real_import = builtins.__import__

    def _limited_import(name, globals=None, locals=None, fromlist=(), level=0):
        if level or name.split(".")[0] not in modules:
            raise ImportError("import of %s is not allowed" % name)
        return _real_import(name, globals, locals, fromlist, level)

    safe["__import__"] = _limited_import
    safe["print"] = lambda *args, **kwargs: None  # demo output is irrelevant to the tests
namespace = {"__builtins__": safe}
results = []
try:
    exec(compile(payload["source"], "<generated>", "exec"), namespace)
    fn = namespace[payload["name"]]
except BaseException as exc:
    results = [{"ok": False, "error": "load: " + type(exc).__name__} for _ in payload["tests"]]
else:
    for test in payload["tests"]:
        args = ast.literal_eval(test["args"])
        expected = ast.literal_eval(test["expected"])
        try:
            got = fn(*copy.deepcopy(args))
            results.append({"ok": bool(same(got, expected, payload.get("compare"))), "got": repr(got)[:120]})
        except BaseException as exc:
            results.append({"ok": False, "error": type(exc).__name__})
sys.stdout.write(json.dumps({"results": results}))
'''


def static_check(source: str, fn_name: str, module: bool = False) -> str | None:
    """Return a rejection reason, or None if the source may be executed in the sandbox.

    Default mode (CodaBench): exactly one top-level function, no imports.
    Module mode (quality benchmark): top-level functions plus imports of SAFE_MODULES.
    """
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        return f"syntax error: {exc.msg}"
    if module:
        if fn_name not in [n.name for n in tree.body if isinstance(n, ast.FunctionDef)]:
            return f"no top-level function named {fn_name}"
        for node in tree.body:
            if isinstance(node, ast.FunctionDef) or (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant)):
                continue
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.ImportFrom) and node.level:
                    return "relative imports are not allowed"
                mods = [a.name for a in node.names] if isinstance(node, ast.Import) else [node.module or ""]
                bad = [m for m in mods if m.split(".")[0] not in SAFE_MODULES]
                if bad:
                    return f"import of {bad[0]} is not allowed"
                continue
            return f"top-level {type(node).__name__} is not allowed"
    elif len(tree.body) != 1 or not isinstance(tree.body[0], ast.FunctionDef) or tree.body[0].name != fn_name:
        return f"must be exactly one top-level function named {fn_name}"
    if any(isinstance(n, ast.FunctionDef) and n.decorator_list for n in tree.body):
        return "decorators are not allowed"
    allowed = (ast.Import, ast.ImportFrom) if module else ()
    for node in ast.walk(tree):
        if isinstance(node, FORBIDDEN_NODES) and not isinstance(node, allowed):
            return f"forbidden construct: {type(node).__name__}"
        if isinstance(node, ast.Name) and ((node.id in FORBIDDEN_NAMES and not (module and node.id == "print"))
                                           or node.id.startswith("__")):
            return f"forbidden name: {node.id}"
        if isinstance(node, ast.Attribute) and node.attr.startswith("_"):
            return f"forbidden attribute: {node.attr}"
        if isinstance(node, ast.Constant) and isinstance(node.value, (str, bytes)) and (
            "__" in str(node.value) or len(node.value) > 1000
        ):
            return "suspicious string constant"
        if isinstance(node, ast.Constant) and isinstance(node.value, int) and abs(node.value) > 10**9:
            return "huge integer constant"
    return None


def run_tests(source: str, fn_name: str, tests: list[dict], compare: str | None = None,
              module: bool = False) -> dict:
    """Return {"status": "passed"|"failed"|"rejected"|"timeout"|"error", "passed": n, "total": n, ...}."""
    total = len(tests)
    reason = static_check(source, fn_name, module=module)
    if reason:
        return {"status": "rejected", "passed": 0, "total": total, "detail": reason}

    payload = json.dumps({"source": source, "name": fn_name, "tests": tests,
                          "compare": compare, "builtins": SAFE_BUILTINS,
                          "modules": sorted(SAFE_MODULES) if module else []})
    env = {"SYSTEMROOT": os.environ.get("SYSTEMROOT", r"C:\Windows")} if sys.platform == "win32" else {}
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    # On Windows a venv's python.exe is a launcher that spawns the real interpreter;
    # call the base interpreter directly so a timeout kill reaches the right process.
    python = getattr(sys, "_base_executable", None) or sys.executable
    with tempfile.TemporaryDirectory(prefix="codabench-") as tmp:
        try:
            proc = subprocess.run(
                [python, "-I", "-S", "-c", RUNNER, str(MEMORY_LIMIT_BYTES), str(CPU_SECONDS)],
                input=payload, capture_output=True, text=True, timeout=WALL_SECONDS,
                cwd=tmp, env=env, creationflags=flags,
            )
        except subprocess.TimeoutExpired:
            return {"status": "timeout", "passed": 0, "total": total, "detail": f"> {WALL_SECONDS}s"}

    try:
        data = json.loads(proc.stdout or "{}")
    except json.JSONDecodeError:
        data = {}
    if "sandbox_error" in data:
        return {"status": "error", "passed": 0, "total": total, "detail": data["sandbox_error"]}
    if "results" not in data:
        if proc.returncode in (0xC0000044, -9, -24):  # Windows job quota / POSIX SIGKILL, SIGXCPU
            detail = "killed by the CPU-time limit"
        else:
            detail = f"exit code {proc.returncode} (killed by a resource limit?)"
        return {"status": "error", "passed": 0, "total": total, "detail": detail}
    passed = sum(1 for r in data["results"] if r.get("ok"))
    return {"status": "passed" if passed == total else "failed", "passed": passed, "total": total,
            "results": data["results"]}
