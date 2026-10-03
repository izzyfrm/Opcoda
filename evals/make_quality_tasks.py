"""Build evals/quality_tasks.json: harder Python tasks for measuring the serving backend.

CodaBench's 12 tasks are one-liners that any pretrained model passes. These need real
logic and edge cases. Every task has a reference solution; this script checks each
reference against its own tests in the sandbox before writing the file.

    python evals/make_quality_tasks.py
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evals import sandbox  # noqa: E402

T = []


def task(name, signature, description, reference, tests, compare=None):
    T.append({"name": name, "signature": signature, "description": description, "reference": reference,
              "tests": [{"args": a, "expected": e} for a, e in tests], **({"compare": compare} if compare else {})})


task("roman_to_int", "def roman_to_int(numeral):",
     "Convert a Roman numeral string (I, V, X, L, C, D, M, with subtractive forms like IV and CM) to an integer.",
     "def roman_to_int(numeral):\n    v = {'I': 1, 'V': 5, 'X': 10, 'L': 50, 'C': 100, 'D': 500, 'M': 1000}\n    total = 0\n    for i, c in enumerate(numeral):\n        if i + 1 < len(numeral) and v[c] < v[numeral[i + 1]]:\n            total -= v[c]\n        else:\n            total += v[c]\n    return total\n",
     [("('III',)", "3"), ("('IV',)", "4"), ("('MCMXCIV',)", "1994"), ("('LVIII',)", "58"), ("('MMXXIV',)", "2024")])
task("int_to_roman", "def int_to_roman(number):",
     "Convert an integer from 1 to 3999 to a Roman numeral string using subtractive notation (4 is IV, 900 is CM).",
     "def int_to_roman(number):\n    pairs = [(1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'), (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'), (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')]\n    out = ''\n    for value, sym in pairs:\n        while number >= value:\n            out += sym\n            number -= value\n    return out\n",
     [("(3,)", "'III'"), ("(4,)", "'IV'"), ("(1994,)", "'MCMXCIV'"), ("(3999,)", "'MMMCMXCIX'"), ("(40,)", "'XL'")])
task("run_length_encode", "def run_length_encode(text):",
     "Run-length encode a string: each run of the same character becomes the count followed by the character, e.g. 'aaabcc' -> '3a1b2c'. Empty input returns ''.",
     "def run_length_encode(text):\n    out = []\n    i = 0\n    while i < len(text):\n        j = i\n        while j < len(text) and text[j] == text[i]:\n            j += 1\n        out.append(str(j - i) + text[i])\n        i = j\n    return ''.join(out)\n",
     [("('aaabcc',)", "'3a1b2c'"), ("('',)", "''"), ("('x',)", "'1x'"), ("('aaaaaaaaaaaa',)", "'12a'"), ("('abab',)", "'1a1b1a1b'")])
task("run_length_decode", "def run_length_decode(encoded):",
     "Decode a run-length string where each character is preceded by its count (which may have several digits), e.g. '3a1b12c' -> 'aaab' followed by twelve 'c'.",
     "def run_length_decode(encoded):\n    out = []\n    num = ''\n    for ch in encoded:\n        if ch.isdigit():\n            num += ch\n        else:\n            out.append(ch * int(num))\n            num = ''\n    return ''.join(out)\n",
     [("('3a1b2c',)", "'aaabcc'"), ("('',)", "''"), ("('12x',)", "'xxxxxxxxxxxx'"), ("('1a1b',)", "'ab'")])
task("balanced_brackets", "def balanced_brackets(text):",
     "Return True if every (, [ and { in text is closed by the matching bracket in the right order. Other characters are ignored.",
     "def balanced_brackets(text):\n    pairs = {')': '(', ']': '[', '}': '{'}\n    stack = []\n    for ch in text:\n        if ch in '([{':\n            stack.append(ch)\n        elif ch in pairs:\n            if not stack or stack.pop() != pairs[ch]:\n                return False\n    return not stack\n",
     [("('(a[b]{c})',)", "True"), ("('([)]',)", "False"), ("('',)", "True"), ("('((',)", "False"), ("('}{',)", "False"), ("('no brackets',)", "True")])
task("merge_intervals", "def merge_intervals(intervals):",
     "Given a list of [start, end] pairs, merge every overlapping or touching pair and return the merged list sorted by start. [[1,3],[2,6],[8,10]] -> [[1,6],[8,10]].",
     "def merge_intervals(intervals):\n    out = []\n    for s, e in sorted(intervals):\n        if out and s <= out[-1][1]:\n            out[-1][1] = max(out[-1][1], e)\n        else:\n            out.append([s, e])\n    return out\n",
     [("([[1, 3], [2, 6], [8, 10]],)", "[[1, 6], [8, 10]]"), ("([],)", "[]"), ("([[5, 7], [1, 2]],)", "[[1, 2], [5, 7]]"), ("([[1, 4], [4, 5]],)", "[[1, 5]]"), ("([[1, 10], [2, 3]],)", "[[1, 10]]")])
task("top_k_words", "def top_k_words(text, k):",
     "Return the k most frequent words in text (case-insensitive, words are runs of letters), most frequent first; ties are broken alphabetically.",
     "import re\nfrom collections import Counter\n\ndef top_k_words(text, k):\n    counts = Counter(re.findall(r'[a-z]+', text.lower()))\n    return [w for w, _ in sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[:k]]\n",
     [("('the cat and the hat and the bat', 2)", "['the', 'and']"), ("('B a b A c', 2)", "['a', 'b']"), ("('', 3)", "[]"), ("('Hello, hello! World.', 5)", "['hello', 'world']")])
task("levenshtein", "def levenshtein(a, b):",
     "Return the edit distance between strings a and b: the minimum number of single-character insertions, deletions or substitutions.",
     "def levenshtein(a, b):\n    prev = list(range(len(b) + 1))\n    for i, ca in enumerate(a, 1):\n        cur = [i]\n        for j, cb in enumerate(b, 1):\n            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))\n        prev = cur\n    return prev[-1]\n",
     [("('kitten', 'sitting')", "3"), ("('', 'abc')", "3"), ("('same', 'same')", "0"), ("('flaw', 'lawn')", "2"), ("('a', '')", "1")])
task("parse_duration", "def parse_duration(text):",
     "Parse a duration like '1h30m', '45s', '2h5s' or '1h2m3s' into a total number of seconds. Units are h, m and s, each optional but in that order.",
     "import re\n\ndef parse_duration(text):\n    total = 0\n    for amount, unit in re.findall(r'(\\d+)([hms])', text):\n        total += int(amount) * {'h': 3600, 'm': 60, 's': 1}[unit]\n    return total\n",
     [("('1h30m',)", "5400"), ("('45s',)", "45"), ("('2h5s',)", "7205"), ("('1h2m3s',)", "3723"), ("('10m',)", "600")])
task("format_bytes", "def format_bytes(size):",
     "Format a byte count for people using 1024-based units B, KB, MB, GB, TB with one decimal place, except plain bytes which have none: 512 -> '512 B', 1536 -> '1.5 KB', 1048576 -> '1.0 MB'.",
     "def format_bytes(size):\n    if size < 1024:\n        return f'{size} B'\n    for unit in ['KB', 'MB', 'GB', 'TB']:\n        size /= 1024\n        if size < 1024 or unit == 'TB':\n            return f'{size:.1f} {unit}'\n",
     [("(512,)", "'512 B'"), ("(1536,)", "'1.5 KB'"), ("(1048576,)", "'1.0 MB'"), ("(0,)", "'0 B'"), ("(1099511627776,)", "'1.0 TB'")])
task("spiral_order", "def spiral_order(matrix):",
     "Return the elements of a rectangular matrix (list of rows) in clockwise spiral order starting at the top-left.",
     "def spiral_order(matrix):\n    out = []\n    rows = [list(r) for r in matrix]\n    while rows:\n        out += rows.pop(0)\n        rows = [list(r) for r in zip(*rows)][::-1]\n    return out\n",
     [("([[1, 2, 3], [4, 5, 6], [7, 8, 9]],)", "[1, 2, 3, 6, 9, 8, 7, 4, 5]"), ("([],)", "[]"), ("([[1, 2], [3, 4], [5, 6]],)", "[1, 2, 4, 6, 5, 3]"), ("([[7]],)", "[7]")])
task("group_anagrams", "def group_anagrams(words):",
     "Group words that are anagrams of each other. Return a list of groups; each group keeps the words in input order, and groups are ordered by the first appearance of their first word.",
     "def group_anagrams(words):\n    groups = {}\n    for w in words:\n        groups.setdefault(''.join(sorted(w)), []).append(w)\n    return list(groups.values())\n",
     [("(['eat', 'tea', 'tan', 'ate', 'nat', 'bat'],)", "[['eat', 'tea', 'ate'], ['tan', 'nat'], ['bat']]"), ("([],)", "[]"), ("(['a'],)", "[['a']]")])
task("caesar_cipher", "def caesar_cipher(text, shift):",
     "Shift every letter in text by shift places in the alphabet, wrapping around and keeping case; non-letters are unchanged. Negative shifts move backwards.",
     "def caesar_cipher(text, shift):\n    out = []\n    for ch in text:\n        if ch.isalpha() and ch.isascii():\n            base = ord('A') if ch.isupper() else ord('a')\n            out.append(chr((ord(ch) - base + shift) % 26 + base))\n        else:\n            out.append(ch)\n    return ''.join(out)\n",
     [("('Hello, World!', 3)", "'Khoor, Zruog!'"), ("('xyz', 3)", "'abc'"), ("('abc', -1)", "'zab'"), ("('Same', 26)", "'Same'")])
task("pascal_row", "def pascal_row(n):",
     "Return row n (0-based) of Pascal's triangle as a list of integers. Row 0 is [1], row 4 is [1, 4, 6, 4, 1].",
     "def pascal_row(n):\n    row = [1]\n    for _ in range(n):\n        row = [1] + [a + b for a, b in zip(row, row[1:])] + [1]\n    return row\n",
     [("(0,)", "[1]"), ("(1,)", "[1, 1]"), ("(4,)", "[1, 4, 6, 4, 1]"), ("(6,)", "[1, 6, 15, 20, 15, 6, 1]")])
task("dedupe_keep_order", "def dedupe_keep_order(items):",
     "Remove duplicates from a list while keeping the first occurrence of each item in its original position.",
     "def dedupe_keep_order(items):\n    seen = set()\n    out = []\n    for x in items:\n        if x not in seen:\n            seen.add(x)\n            out.append(x)\n    return out\n",
     [("([3, 1, 3, 2, 1],)", "[3, 1, 2]"), ("([],)", "[]"), ("(['b', 'a', 'b'],)", "['b', 'a']")])
task("longest_common_prefix", "def longest_common_prefix(words):",
     "Return the longest string that every word in the list starts with. Return '' for an empty list or when there is no common prefix.",
     "def longest_common_prefix(words):\n    if not words:\n        return ''\n    prefix = words[0]\n    for w in words[1:]:\n        while not w.startswith(prefix):\n            prefix = prefix[:-1]\n    return prefix\n",
     [("(['flower', 'flow', 'flight'],)", "'fl'"), ("(['dog', 'car'],)", "''"), ("([],)", "''"), ("(['same'],)", "'same'"), ("(['ab', 'a'],)", "'a'")])
task("binary_search", "def binary_search(values, target):",
     "Return the index of target in the sorted list values using binary search, or -1 if it is not present.",
     "def binary_search(values, target):\n    lo, hi = 0, len(values) - 1\n    while lo <= hi:\n        mid = (lo + hi) // 2\n        if values[mid] == target:\n            return mid\n        if values[mid] < target:\n            lo = mid + 1\n        else:\n            hi = mid - 1\n    return -1\n",
     [("([1, 3, 5, 7, 9], 7)", "3"), ("([1, 3, 5], 4)", "-1"), ("([], 1)", "-1"), ("([2], 2)", "0"), ("([1, 2, 3, 4, 5, 6], 1)", "0")])
task("deep_flatten", "def deep_flatten(value):",
     "Flatten arbitrarily nested lists into a single flat list, keeping the order of the non-list items.",
     "def deep_flatten(value):\n    out = []\n    for item in value:\n        if isinstance(item, list):\n            out.extend(deep_flatten(item))\n        else:\n            out.append(item)\n    return out\n",
     [("([1, [2, [3, [4]], 5]],)", "[1, 2, 3, 4, 5]"), ("([],)", "[]"), ("([[[]]],)", "[]"), ("(['a', ['b']],)", "['a', 'b']")])
task("is_valid_ipv4", "def is_valid_ipv4(address):",
     "Return True if address is a dotted IPv4 address: exactly four decimal parts from 0 to 255, no leading zeros (except a single 0), digits only.",
     "def is_valid_ipv4(address):\n    parts = address.split('.')\n    if len(parts) != 4:\n        return False\n    for p in parts:\n        if not p.isdigit() or not p.isascii() or (len(p) > 1 and p[0] == '0') or int(p) > 255:\n            return False\n    return True\n",
     [("('192.168.1.1',)", "True"), ("('255.255.255.255',)", "True"), ("('256.1.1.1',)", "False"), ("('1.2.3',)", "False"), ("('01.2.3.4',)", "False"), ("('1.2.3.a',)", "False"), ("('0.0.0.0',)", "True")])
task("matrix_multiply", "def matrix_multiply(a, b):",
     "Multiply two matrices given as lists of rows and return the product as a list of rows. Raise ValueError if the inner dimensions don't match.",
     "def matrix_multiply(a, b):\n    if a and b and len(a[0]) != len(b):\n        raise ValueError('incompatible')\n    return [[sum(x * y for x, y in zip(row, col)) for col in zip(*b)] for row in a]\n",
     [("([[1, 2], [3, 4]], [[5, 6], [7, 8]])", "[[19, 22], [43, 50]]"), ("([[1, 2, 3]], [[1], [2], [3]])", "[[14]]"), ("([[2]], [[3]])", "[[6]]")])
task("word_wrap", "def word_wrap(text, width):",
     "Wrap text into lines of at most width characters, breaking only at spaces and never splitting words (a word longer than width gets its own line). Return the list of lines.",
     "def word_wrap(text, width):\n    lines = []\n    line = ''\n    for word in text.split():\n        if not line:\n            line = word\n        elif len(line) + 1 + len(word) <= width:\n            line += ' ' + word\n        else:\n            lines.append(line)\n            line = word\n    if line:\n        lines.append(line)\n    return lines\n",
     [("('the quick brown fox jumps', 10)", "['the quick', 'brown fox', 'jumps']"), ("('', 5)", "[]"), ("('extraordinary is long', 5)", "['extraordinary', 'is', 'long']"), ("('a b c', 5)", "['a b c']")])
task("count_islands", "def count_islands(grid):",
     "Count groups of horizontally or vertically connected '1' cells in a grid given as a list of strings of '0' and '1'.",
     "def count_islands(grid):\n    seen = set()\n    count = 0\n    for r in range(len(grid)):\n        for c in range(len(grid[r])):\n            if grid[r][c] == '1' and (r, c) not in seen:\n                count += 1\n                stack = [(r, c)]\n                while stack:\n                    y, x = stack.pop()\n                    if (y, x) in seen or not (0 <= y < len(grid) and 0 <= x < len(grid[y])) or grid[y][x] != '1':\n                        continue\n                    seen.add((y, x))\n                    stack += [(y + 1, x), (y - 1, x), (y, x + 1), (y, x - 1)]\n    return count\n",
     [("(['11000', '11000', '00100', '00011'],)", "3"), ("([],)", "0"), ("(['111', '010', '111'],)", "1"), ("(['101', '010', '101'],)", "5")])
task("next_greater", "def next_greater(values):",
     "For each number, return the next number to its right that is strictly larger, or -1 if there is none. [2, 1, 3] -> [3, 3, -1].",
     "def next_greater(values):\n    out = [-1] * len(values)\n    stack = []\n    for i, v in enumerate(values):\n        while stack and values[stack[-1]] < v:\n            out[stack.pop()] = v\n        stack.append(i)\n    return out\n",
     [("([2, 1, 3],)", "[3, 3, -1]"), ("([],)", "[]"), ("([5, 4, 3],)", "[-1, -1, -1]"), ("([1, 3, 2, 4],)", "[3, 4, 4, -1]")])
task("slugify", "def slugify(title):",
     "Turn a title into a URL slug: lowercase, keep only a-z and 0-9, join the words with single hyphens, no hyphen at either end. 'Hello, World! 2024' -> 'hello-world-2024'.",
     "import re\n\ndef slugify(title):\n    return '-'.join(re.findall(r'[a-z0-9]+', title.lower()))\n",
     [("('Hello, World! 2024',)", "'hello-world-2024'"), ("('  Spaces   everywhere  ',)", "'spaces-everywhere'"), ("('---',)", "''"), ("('Already-a-slug',)", "'already-a-slug'")])

if __name__ == "__main__":
    bad = 0
    for t in T:
        res = sandbox.run_tests(t["reference"], t["name"], t["tests"], t.get("compare"), module=True)
        if res["status"] != "passed":
            bad += 1
            print("REFERENCE FAILS:", t["name"], res)
    out = Path(__file__).with_name("quality_tasks.json")
    out.write_text(json.dumps({"version": "1.0", "note": "Harder serving-quality tasks; see make_quality_tasks.py.",
                               "tasks": T}, indent=1), encoding="utf-8")
    print(f"{len(T)} tasks, {bad} broken references -> {out}")
    sys.exit(1 if bad else 0)
