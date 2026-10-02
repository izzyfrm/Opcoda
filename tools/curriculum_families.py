"""Task families for Coda's Phase 3 Python curriculum.

Each family is one programming task with:
- several function-name synonyms (no numbered clones like add_1/add_2),
- several task phrasings,
- several *different* implementations (loop vs builtin vs comprehension ...),
- sample inputs ("checks") used to verify that all implementations agree.

Templates use ``$name`` placeholders (string.Template syntax):
- ``$fn`` is the chosen function (or class) name,
- placeholders listed in ``sig`` are parameters drawn from PARAM_POOLS/PAIR_POOLS,
- every other placeholder is a local variable drawn from LOCAL_POOLS.

The generator picks fresh names for every example so the model has to read
the task and the signature instead of memorising fixed token sequences.

Families that overlap the held-out CodaBench tasks are deliberately absent
(see evals/heldout_tasks.json; the generator enforces the ban list).
"""
from __future__ import annotations

from dataclasses import dataclass

# --------------------------------------------------------------------------
# Name pools
# --------------------------------------------------------------------------

PARAM_POOLS: dict[str, list[str]] = {
    "STR": ["text", "s", "string", "value", "message", "content"],
    "WORD": ["word", "s", "text", "name", "token", "term"],
    "SENT": ["sentence", "text", "line", "phrase", "message", "s"],
    "CHAR": ["ch", "char", "c", "letter", "target", "symbol"],
    "FILL": ["fill", "pad", "ch", "filler"],
    "INT": ["n", "num", "number", "x", "value", "k"],
    "NNEG": ["n", "num", "number", "value", "x"],
    "POSINT": ["n", "num", "number", "value"],
    "NUM": ["x", "n", "num", "number", "value"],
    "COUNT": ["count", "k", "n", "times", "how_many", "repeats"],
    "DIVISOR": ["d", "divisor", "k", "m", "step"],
    "NUMS": ["nums", "numbers", "values", "data", "scores", "xs", "arr", "readings", "amounts", "items"],
    "ITEMS": ["items", "values", "elements", "seq", "lst", "entries", "things", "data", "xs", "collection"],
    "WORDS": ["words", "names", "strings", "tokens", "labels", "items", "terms"],
    "LISTS": ["groups", "lists", "chunks", "batches", "rows", "parts"],
    "DICT": ["d", "mapping", "table", "data", "lookup", "record"],
    "NUMDICT": ["scores", "prices", "counts", "totals", "stock", "d", "ages", "points"],
    "MATRIX": ["matrix", "grid", "rows", "table", "board"],
    "RECORDS": ["rows", "records", "people", "items", "entries", "users"],
    "FIELD": ["field", "key", "column", "name", "attr"],
    "TARGET": ["target", "x", "item", "value", "needle", "wanted"],
    "LIMIT": ["limit", "threshold", "cutoff", "minimum", "bound"],
    "PREFIX": ["prefix", "start", "head", "p"],
    "SUFFIX": ["suffix", "ending", "end", "tail"],
    "SUB": ["sub", "part", "pattern", "needle", "piece"],
    "FACTOR": ["factor", "k", "scale", "multiplier", "m"],
    "OFFSET": ["offset", "delta", "k", "amount", "shift"],
    "WIDTH": ["width", "size", "length", "n", "total"],
    "SIZE": ["size", "n", "k", "limit", "length", "max_len"],
    "YEAR": ["year", "y", "yr"],
    "AGE": ["age", "years", "a"],
    "SCORE": ["score", "points", "mark", "result"],
    "FLAG": ["flag", "value", "ok", "answer", "b"],
    "DAY": ["day", "name", "weekday", "d"],
    "KEY": ["key", "k", "name", "item"],
    "DEFAULT": ["default", "fallback", "missing", "otherwise"],
    "BITS": ["bits", "s", "binary", "text", "digits"],
    "FILENAME": ["filename", "name", "path", "fname"],
    "EMAIL": ["email", "address", "s", "addr"],
    "CSV": ["s", "text", "line", "csv", "raw", "data"],
    "TIME": ["s", "text", "clock", "time_str", "hhmm"],
    "MINUTES": ["minutes", "total", "mins", "n"],
    "SECONDS": ["seconds", "secs", "total", "duration", "s"],
    "CELSIUS": ["celsius", "c", "temp", "degrees"],
    "FAHR": ["fahrenheit", "f", "temp", "degrees"],
    "RADIUS": ["radius", "r"],
    "STEP": ["k", "shift", "offset", "n", "amount"],
    "PCT": ["pct", "percent", "rate", "discount"],
    "PIVOT": ["pivot", "split_at", "cutoff", "value"],
    "N": ["n", "k", "count", "size"],
}

PAIR_POOLS: dict[str, list[tuple[str, ...]]] = {
    "PAIR_NUM": [("a", "b"), ("x", "y"), ("first", "second"), ("m", "n"), ("left", "right"), ("p", "q"), ("num1", "num2")],
    "PAIR_LIST": [("a", "b"), ("xs", "ys"), ("first", "second"), ("left", "right"), ("list1", "list2"), ("items", "others"), ("values", "other")],
    "PAIR_STR": [("a", "b"), ("s1", "s2"), ("first", "second"), ("word1", "word2"), ("left", "right"), ("text", "other")],
    "TRIPLE": [("a", "b", "c"), ("x", "y", "z"), ("first", "second", "third"), ("p", "q", "r")],
    "RANGE": [("low", "high"), ("lo", "hi"), ("start", "end"), ("minimum", "maximum"), ("floor", "ceiling"), ("lower", "upper")],
    "DIMS": [("width", "height"), ("w", "h"), ("length", "breadth"), ("base", "height")],
    "BASEEXP": [("base", "exp"), ("x", "n"), ("b", "e"), ("base", "exponent"), ("value", "times")],
    "OLDNEW": [("old", "new"), ("before", "after"), ("target", "replacement"), ("find", "repl"), ("a", "b")],
    "KEYSVALS": [("keys", "values"), ("names", "scores"), ("ks", "vs"), ("labels", "amounts"), ("fields", "data")],
    "PARTWHOLE": [("part", "whole"), ("count", "total"), ("value", "maximum"), ("x", "total")],
    "RC": [("rows", "cols"), ("height", "width"), ("n_rows", "n_cols"), ("r", "c")],
    "KEY2": [("key1", "key2"), ("outer", "inner"), ("first", "second"), ("k1", "k2")],
    "POINTS": [("x1", "y1", "x2", "y2"), ("ax", "ay", "bx", "by"), ("x0", "y0", "x1", "y1")],
    "FIELDVAL": [("field", "value"), ("key", "wanted"), ("column", "target"), ("attr", "match")],
}

LOCAL_POOLS: dict[str, list[str]] = {
    "x": ["x", "item", "value", "v", "elem", "element", "entry"],
    "y": ["y", "other", "partner", "rhs"],
    "num": ["num", "n", "x", "value", "number", "v"],
    "ch": ["ch", "c", "char", "letter", "symbol"],
    "c": ["c", "letter", "char", "symbol", "current"],
    "w": ["word", "w", "token", "part", "piece"],
    "p": ["part", "piece", "chunk", "p", "field", "token"],
    "i": ["i", "idx", "index", "pos", "j"],
    "j": ["j", "k", "m", "inner"],
    "out": ["result", "out", "output", "res", "answer", "collected"],
    "total": ["total", "acc", "running", "subtotal", "accum"],
    "count": ["count", "counter", "tally", "hits", "found"],
    "seen": ["seen", "visited", "known", "already", "used"],
    "hi": ["largest", "biggest", "best", "top", "highest", "current"],
    "lo": ["smallest", "lowest", "least", "best", "current"],
    "k": ["key", "k", "name", "label"],
    "v": ["value", "v", "val", "amount"],
    "d": ["counts", "freq", "table", "tally", "mapping", "lookup"],
    "row": ["row", "line", "r", "record"],
    "g": ["group", "chunk", "part", "sub", "inner"],
    "prev": ["prev", "a", "previous", "older"],
    "cur": ["cur", "b", "curr", "current", "newer"],
    "fahr": ["fahrenheit", "f", "result", "temp_f"],
    "cels": ["celsius", "c", "result", "temp_c"],
    "dx": ["dx", "delta_x", "run_x"],
    "dy": ["dy", "delta_y", "rise"],
    "h": ["h", "hours", "hh"],
    "m": ["m", "minutes", "mm"],
    "sec": ["sec", "secs", "ss"],
    "rest": ["rest", "remainder", "leftover"],
    "mid": ["mid", "middle", "center"],
    "left": ["left", "lo", "low", "start"],
    "right": ["right", "hi", "high", "end"],
    "swapped": ["swapped", "changed", "moved"],
    "pair": ["pair", "item", "kv", "entry"],
    "parts": ["parts", "pieces", "fields", "chunks"],
    "idx": ["idx", "pos", "at", "where", "spot"],
    "run": ["run", "streak", "current_run", "length"],
    "best": ["best", "record", "top"],
    "longest": ["longest", "best", "record"],
    "shortest": ["shortest", "best", "record"],
    "best_i": ["best", "best_index", "max_idx", "top"],
    "min_i": ["min_idx", "smallest", "lowest_index"],
    "key": ["key", "name", "existing"],
    "val": ["val", "value", "v"],
    "width": ["width", "w", "cols"],
    "height": ["height", "h", "rows"],
    "steps": ["steps", "count", "moves", "n_steps"],
    "r": ["r", "root", "guess"],
    "sides": ["sides", "lengths", "ordered"],
    "letter": ["letter", "grade", "mark"],
    "cut": ["limit", "cutoff", "threshold", "bound"],
    "alphabet": ["alphabet", "letters", "abc"],
    "words": ["words", "parts", "tokens", "pieces"],
    "lines": ["lines", "rows"],
    "mask": ["mask", "stars", "hidden"],
    "groups": ["groups", "result", "buckets", "index"],
    "evens": ["evens", "even_values", "even"],
    "odds": ["odds", "odd_values", "odd"],
    "below": ["below", "smaller", "lower", "left"],
    "above": ["above", "larger", "upper", "right"],
    "pos": ["pos", "where", "loc", "found"],
    "bit": ["bit", "digit", "b"],
    "col": ["col", "column", "j"],
    "t": ["t", "tmp", "temp"],
    "inner": ["inner", "level", "child", "nested"],
    "attr": ["items", "data", "elements", "values", "contents"],
    "num_attr": ["count", "value", "total", "clicks"],
}

# Parameter type hints are only emitted when *every* parameter has one.
TYPE_HINTS: dict[str, tuple[str, ...]] = {
    **{p: ("str",) for p in ["STR", "WORD", "SENT", "CHAR", "FILL", "BITS", "FILENAME", "EMAIL", "CSV", "TIME", "PREFIX", "SUFFIX", "SUB", "DAY", "FIELD"]},
    **{p: ("int",) for p in ["INT", "NNEG", "POSINT", "COUNT", "DIVISOR", "YEAR", "AGE", "WIDTH", "SIZE", "STEP", "MINUTES", "SECONDS", "N"]},
    **{p: ("float",) for p in ["NUM", "CELSIUS", "FAHR", "RADIUS"]},
    "NUMS": ("list",), "ITEMS": ("list",), "WORDS": ("list[str]",), "LISTS": ("list[list]",),
    "DICT": ("dict",), "NUMDICT": ("dict",), "MATRIX": ("list[list[int]]",), "RECORDS": ("list[dict]",),
    "FLAG": ("bool",), "PCT": ("float",), "FACTOR": ("float",),
    "PAIR_NUM": ("int", "int"), "PAIR_LIST": ("list", "list"), "PAIR_STR": ("str", "str"),
    "OLDNEW": ("str", "str"), "KEYSVALS": ("list", "list"), "DIMS": ("float", "float"),
    "RC": ("int", "int"), "POINTS": ("float", "float", "float", "float"),
}


@dataclass(frozen=True)
class Family:
    key: str
    topic: str
    names: tuple[str, ...]
    sig: tuple[tuple[tuple[str, ...], str], ...]
    tasks: tuple[str, ...]
    impls: tuple[str, ...]
    checks: tuple[tuple, ...] = ()
    kind: str = "function"


FAMILIES: list[Family] = []


def _parse_sig(sig: str):
    out = []
    for part in filter(None, (p.strip() for p in sig.split(","))):
        placeholders, pool = part.split(":")
        out.append((tuple(placeholders.split("/")), pool))
    return tuple(out)


def F(key, topic, names, sig, tasks, impls, checks=()):
    FAMILIES.append(Family(key, topic, tuple(names.split()), _parse_sig(sig), tuple(tasks), tuple(impls), tuple(checks)))


def C(key, names, tasks, impls):
    FAMILIES.append(Family(key, "classes", tuple(names.split()), (), tuple(tasks), tuple(impls), (), kind="class"))


# ==========================================================================
# Math
# ==========================================================================

F("add_two", "math", "add add_numbers sum_two plus", "a/b:PAIR_NUM",
  ["Return the sum of $a and $b.", "Add $a and $b.", "Return $a plus $b."],
  ["return $a + $b", "$out = $a + $b\nreturn $out"],
  [(2, 3), (-4, 1), (0, 0)])

F("subtract_two", "math", "subtract minus subtract_numbers", "a/b:PAIR_NUM",
  ["Return $a minus $b.", "Subtract $b from $a."],
  ["return $a - $b", "$out = $a - $b\nreturn $out"],
  [(5, 3), (0, 4)])

F("multiply_two", "math", "multiply times mul product_of_two", "a/b:PAIR_NUM",
  ["Return the product of $a and $b.", "Multiply $a by $b."],
  ["return $a * $b", "$out = $a * $b\nreturn $out"],
  [(3, 4), (-2, 5)])

F("square", "math", "square squared square_of", "x:NUM",
  ["Return the square of $x.", "Return $x multiplied by itself."],
  ["return $x * $x", "return $x ** 2", "return pow($x, 2)"],
  [(3,), (-2,), (0,)])

F("cube", "math", "cube cubed cube_of", "x:NUM",
  ["Return the cube of $x.", "Return $x raised to the third power."],
  ["return $x ** 3", "return $x * $x * $x", "return pow($x, 3)"],
  [(2,), (-3,)])

F("absolute", "math", "absolute abs_value magnitude", "x:NUM",
  ["Return the absolute value of $x.", "Return $x without its sign."],
  ["if $x < 0:\n    return -$x\nreturn $x", "return -$x if $x < 0 else $x", "return abs($x)"],
  [(-5,), (3,), (0,)])

F("sign", "math", "sign signum sign_of", "x:NUM",
  ["Return 1 if $x is positive, -1 if it is negative, and 0 otherwise."],
  [r"""
   if $x > 0:
       return 1
   elif $x < 0:
       return -1
   else:
       return 0
   """,
   r"""
   if $x > 0:
       return 1
   if $x < 0:
       return -1
   return 0
   """,
   "return 1 if $x > 0 else (-1 if $x < 0 else 0)"],
  [(5,), (-2,), (0,)])

F("is_even", "math", "is_even even check_even", "n:INT",
  ["Return True if $n is even.", "Check whether $n is even."],
  ["return $n % 2 == 0", "if $n % 2 == 0:\n    return True\nreturn False", "return not $n % 2"],
  [(4,), (7,), (0,), (-3,)])

F("is_odd", "math", "is_odd odd check_odd", "n:INT",
  ["Return True if $n is odd.", "Check whether $n is odd."],
  ["return $n % 2 != 0", "return $n % 2 == 1", "if $n % 2 == 1:\n    return True\nreturn False"],
  [(3,), (8,), (-5,)])

F("is_divisible", "math", "is_divisible divides_evenly is_multiple", "n:INT, d:DIVISOR",
  ["Return True if $n is divisible by $d.", "Check whether $d divides $n evenly."],
  ["return $n % $d == 0", "if $n % $d == 0:\n    return True\nreturn False"],
  [(10, 5), (7, 2)])

F("larger_of_two", "math", "larger bigger max_of_two greater_of", "a/b:PAIR_NUM",
  ["Return the larger of $a and $b.", "Return whichever of $a and $b is bigger."],
  ["if $a > $b:\n    return $a\nreturn $b", "return $a if $a > $b else $b", "return max($a, $b)"],
  [(3, 9), (5, 2), (4, 4)])

F("smaller_of_two", "math", "smaller lesser min_of_two", "a/b:PAIR_NUM",
  ["Return the smaller of $a and $b.", "Return whichever of $a and $b is smaller."],
  ["if $a < $b:\n    return $a\nreturn $b", "return $a if $a < $b else $b", "return min($a, $b)"],
  [(3, 9), (5, 2)])

F("max_of_three", "math", "max_of_three largest_of_three biggest_of_three", "a/b/c:TRIPLE",
  ["Return the largest of $a, $b, and $c."],
  ["return max($a, $b, $c)",
   r"""
   $hi = $a
   if $b > $hi:
       $hi = $b
   if $c > $hi:
       $hi = $c
   return $hi
   """,
   r"""
   if $a >= $b and $a >= $c:
       return $a
   if $b >= $c:
       return $b
   return $c
   """],
  [(1, 2, 3), (9, 4, 7), (5, 8, 2), (3, 3, 1)])

F("min_of_three", "math", "min_of_three smallest_of_three", "a/b/c:TRIPLE",
  ["Return the smallest of $a, $b, and $c."],
  ["return min($a, $b, $c)",
   r"""
   $lo = $a
   if $b < $lo:
       $lo = $b
   if $c < $lo:
       $lo = $c
   return $lo
   """],
  [(1, 2, 3), (9, 4, 7), (5, 8, 2)])

F("clamp", "math", "clamp clip_value bound_value", "x:NUM, lo/hi:RANGE",
  ["Return $x limited to the range $lo to $hi.", "Clamp $x so it is at least $lo and at most $hi."],
  [r"""
   if $x < $lo:
       return $lo
   if $x > $hi:
       return $hi
   return $x
   """,
   "return max($lo, min($x, $hi))",
   "return $lo if $x < $lo else $hi if $x > $hi else $x"],
  [(5, 0, 10), (-3, 0, 10), (42, 0, 10)])

F("is_between", "logic", "is_between in_range within_range", "x:NUM, lo/hi:RANGE",
  ["Return True if $x is between $lo and $hi, inclusive."],
  ["return $lo <= $x <= $hi", "return $x >= $lo and $x <= $hi",
   "if $x < $lo or $x > $hi:\n    return False\nreturn True"],
  [(5, 1, 10), (0, 1, 10), (10, 1, 10)])

F("factorial", "math", "factorial fact factorial_of", "n:NNEG",
  ["Return the factorial of $n.", "Return $n! for a non-negative integer $n."],
  [r"""
   $out = 1
   for $i in range(2, $n + 1):
       $out *= $i
   return $out
   """,
   r"""
   if $n <= 1:
       return 1
   return $n * $fn($n - 1)
   """,
   r"""
   $out = 1
   while $n > 1:
       $out *= $n
       $n -= 1
   return $out
   """],
  [(0,), (1,), (5,)])

F("sum_to_n", "math", "sum_to_n sum_up_to triangle_number", "n:NNEG",
  ["Return the sum of the integers from 1 to $n."],
  [r"""
   $total = 0
   for $i in range(1, $n + 1):
       $total += $i
   return $total
   """,
   "return $n * ($n + 1) // 2", "return sum(range(1, $n + 1))"],
  [(0,), (1,), (10,)])

F("power", "math", "power raise_to int_power", "x/e:BASEEXP",
  ["Return $x raised to the power $e, where $e is a non-negative integer."],
  [r"""
   $out = 1
   for _ in range($e):
       $out *= $x
   return $out
   """,
   "return $x ** $e"],
  [(2, 10), (3, 0), (5, 3)])

F("digit_sum", "math", "digit_sum sum_digits sum_of_digits", "n:NNEG",
  ["Return the sum of the digits of $n.", "Add up the digits of the non-negative integer $n."],
  [r"""
   $total = 0
   while $n > 0:
       $total += $n % 10
       $n //= 10
   return $total
   """,
   "return sum(int($ch) for $ch in str($n))",
   r"""
   $total = 0
   for $ch in str($n):
       $total += int($ch)
   return $total
   """],
  [(0,), (7,), (1234,)])

F("count_digits", "math", "count_digits num_digits digit_count", "n:NNEG",
  ["Return how many digits the non-negative integer $n has."],
  ["return len(str($n))",
   r"""
   $count = 1
   while $n >= 10:
       $n //= 10
       $count += 1
   return $count
   """],
  [(0,), (9,), (12345,)])

F("reverse_digits", "math", "reverse_digits reversed_number flip_digits", "n:NNEG",
  ["Return the number formed by reversing the digits of $n."],
  ["return int(str($n)[::-1])",
   r"""
   $out = 0
   while $n > 0:
       $out = $out * 10 + $n % 10
       $n //= 10
   return $out
   """],
  [(123,), (1200,), (0,)])

F("is_power_of_two", "math", "is_power_of_two power_of_two", "n:INT",
  ["Return True if $n is a power of two."],
  [r"""
   if $n < 1:
       return False
   while $n % 2 == 0:
       $n //= 2
   return $n == 1
   """,
   "return $n > 0 and $n & ($n - 1) == 0"],
  [(1,), (8,), (12,), (0,), (-4,)])

F("fibonacci", "math", "fibonacci fib nth_fibonacci", "n:NNEG",
  ["Return the $n-th Fibonacci number, where the sequence starts 0, 1, 1, 2."],
  [r"""
   $prev, $cur = 0, 1
   for _ in range($n):
       $prev, $cur = $cur, $prev + $cur
   return $prev
   """,
   r"""
   if $n < 2:
       return $n
   return $fn($n - 1) + $fn($n - 2)
   """],
  [(0,), (1,), (2,), (10,)])

F("fib_list", "math", "fibonacci_list fib_sequence first_fibonacci", "n:NNEG",
  ["Return a list of the first $n Fibonacci numbers."],
  [r"""
   $out = []
   $prev, $cur = 0, 1
   for _ in range($n):
       $out.append($prev)
       $prev, $cur = $cur, $prev + $cur
   return $out
   """,
   r"""
   $out = [0, 1]
   while len($out) < $n:
       $out.append($out[-1] + $out[-2])
   return $out[:$n]
   """],
  [(0,), (1,), (7,)])

F("c_to_f", "math", "celsius_to_fahrenheit c_to_f to_fahrenheit", "c:CELSIUS",
  ["Convert $c degrees Celsius to Fahrenheit."],
  ["return $c * 9 / 5 + 32", "return $c * 1.8 + 32", "$fahr = $c * 9 / 5 + 32\nreturn $fahr"],
  [(0,), (100,), (-40,)])

F("f_to_c", "math", "fahrenheit_to_celsius f_to_c to_celsius", "f:FAHR",
  ["Convert $f degrees Fahrenheit to Celsius."],
  ["return ($f - 32) * 5 / 9", "$cels = ($f - 32) * 5 / 9\nreturn $cels"],
  [(32,), (212,), (-40,)])

F("percent_of", "math", "percentage percent_of as_percent", "part/whole:PARTWHOLE",
  ["Return $part as a percentage of $whole, or 0 when $whole is 0."],
  ["if $whole == 0:\n    return 0\nreturn $part / $whole * 100",
   "return 0 if $whole == 0 else $part / $whole * 100",
   "if not $whole:\n    return 0\nreturn 100 * $part / $whole"],
  [(1, 4), (3, 0), (5, 5)])

F("safe_divide", "math", "safe_divide divide_or_none checked_divide", "a/b:PAIR_NUM",
  ["Divide $a by $b, returning None when $b is zero."],
  ["if $b == 0:\n    return None\nreturn $a / $b",
   "return None if $b == 0 else $a / $b",
   r"""
   try:
       return $a / $b
   except ZeroDivisionError:
       return None
   """],
  [(6, 3), (1, 0), (7, 2)])

F("hypotenuse", "math", "hypotenuse hyp diagonal_length", "a/b:PAIR_NUM",
  ["Return the hypotenuse of a right triangle with legs $a and $b."],
  ["return ($a ** 2 + $b ** 2) ** 0.5", "return ($a * $a + $b * $b) ** 0.5"],
  [(3, 4), (5, 12)])

F("distance", "math", "distance point_distance dist", "x1/y1/x2/y2:POINTS",
  ["Return the distance between the points ($x1, $y1) and ($x2, $y2)."],
  ["$dx = $x2 - $x1\n$dy = $y2 - $y1\nreturn ($dx ** 2 + $dy ** 2) ** 0.5",
   "return (($x2 - $x1) ** 2 + ($y2 - $y1) ** 2) ** 0.5"],
  [(0, 0, 3, 4), (1, 1, 1, 1)])

F("rect_area", "math", "rectangle_area rect_area area_of_rectangle", "w/h:DIMS",
  ["Return the area of a rectangle with sides $w and $h."],
  ["return $w * $h", "$out = $w * $h\nreturn $out"],
  [(3, 4)])

F("rect_perimeter", "math", "rectangle_perimeter rect_perimeter perimeter", "w/h:DIMS",
  ["Return the perimeter of a rectangle with sides $w and $h."],
  ["return 2 * ($w + $h)", "return 2 * $w + 2 * $h", "return $w + $w + $h + $h"],
  [(3, 4)])

F("circle_area", "math", "circle_area area_of_circle", "r:RADIUS",
  ["Return the area of a circle with radius $r, using 3.14159 for pi."],
  ["return 3.14159 * $r * $r", "return 3.14159 * $r ** 2"],
  [(1,), (2,)])

F("circumference", "math", "circumference circle_perimeter", "r:RADIUS",
  ["Return the circumference of a circle with radius $r, using 3.14159 for pi."],
  ["return 2 * 3.14159 * $r", "return 3.14159 * 2 * $r"],
  [(1,), (3,)])

F("count_divisors", "math", "count_divisors num_divisors divisor_count", "n:POSINT",
  ["Return how many positive divisors $n has."],
  [r"""
   $count = 0
   for $i in range(1, $n + 1):
       if $n % $i == 0:
           $count += 1
   return $count
   """,
   "return sum(1 for $i in range(1, $n + 1) if $n % $i == 0)",
   "return len([$i for $i in range(1, $n + 1) if $n % $i == 0])"],
  [(1,), (6,), (12,)])

F("divisors", "math", "divisors list_divisors factors_of", "n:POSINT",
  ["Return a list of the positive divisors of $n in increasing order."],
  ["return [$i for $i in range(1, $n + 1) if $n % $i == 0]",
   r"""
   $out = []
   for $i in range(1, $n + 1):
       if $n % $i == 0:
           $out.append($i)
   return $out
   """],
  [(12,), (1,), (7,)])

F("collatz_steps", "math", "collatz_steps collatz_length", "n:POSINT",
  ["Return how many steps it takes $n to reach 1 if you halve even numbers and map odd numbers to 3 * $n + 1."],
  [r"""
   $steps = 0
   while $n != 1:
       if $n % 2 == 0:
           $n //= 2
       else:
           $n = 3 * $n + 1
       $steps += 1
   return $steps
   """,
   r"""
   $steps = 0
   while $n > 1:
       $n = $n // 2 if $n % 2 == 0 else 3 * $n + 1
       $steps += 1
   return $steps
   """],
  [(1,), (6,), (7,)])

F("is_perfect_square", "math", "is_perfect_square is_square", "n:NNEG",
  ["Return True if $n is a perfect square."],
  ["$r = int($n ** 0.5)\nreturn $r * $r == $n",
   r"""
   $i = 0
   while $i * $i < $n:
       $i += 1
   return $i * $i == $n
   """],
  [(0,), (1,), (16,), (15,)])

F("to_binary", "math", "to_binary binary_string as_binary", "n:NNEG",
  ["Return the binary representation of the non-negative integer $n as a string."],
  ["return bin($n)[2:]", 'return format($n, "b")',
   r"""
   if $n == 0:
       return "0"
   $out = ""
   while $n > 0:
       $out = str($n % 2) + $out
       $n //= 2
   return $out
   """],
  [(0,), (5,), (8,)])

F("from_binary", "math", "from_binary parse_binary binary_to_int", "s:BITS",
  ["Convert the binary string $s to an integer."],
  ["return int($s, 2)",
   r"""
   $out = 0
   for $bit in $s:
       $out = $out * 2 + int($bit)
   return $out
   """],
  [("101",), ("0",), ("1111",)])

F("split_seconds", "math", "split_seconds to_hms seconds_to_hms", "s:SECONDS",
  ["Convert $s seconds into a tuple of (hours, minutes, seconds)."],
  ["return ($s // 3600, $s % 3600 // 60, $s % 60)",
   "$h, $rest = divmod($s, 3600)\n$m, $sec = divmod($rest, 60)\nreturn ($h, $m, $sec)"],
  [(3725,), (59,), (0,)])

F("multiples", "math", "multiples list_multiples first_multiples", "n:INT, k:COUNT",
  ["Return the first $k multiples of $n, starting with $n itself."],
  ["return [$n * $i for $i in range(1, $k + 1)]",
   r"""
   $out = []
   for $i in range(1, $k + 1):
       $out.append($n * $i)
   return $out
   """],
  [(3, 4), (5, 0)])

F("is_triangle", "logic", "is_triangle valid_triangle can_form_triangle", "a/b/c:TRIPLE",
  ["Return True if side lengths $a, $b, and $c can form a triangle."],
  ["return $a + $b > $c and $a + $c > $b and $b + $c > $a",
   "$sides = sorted([$a, $b, $c])\nreturn $sides[0] + $sides[1] > $sides[2]"],
  [(3, 4, 5), (1, 2, 3), (2, 2, 3)])

F("round_down", "math", "round_down floor_to_multiple round_to_multiple", "n:NNEG, k:DIVISOR",
  ["Round $n down to the nearest multiple of $k."],
  ["return $n - $n % $k", "return $n // $k * $k"],
  [(17, 5), (20, 5), (3, 10)])

# ==========================================================================
# Logic / conditions
# ==========================================================================

F("letter_grade", "logic", "letter_grade grade_for to_letter", "score:SCORE",
  ['Return "A" for a $score of 90 or more, "B" for 80 or more, "C" for 70 or more, "D" for 60 or more, and "F" otherwise.'],
  [r"""
   if $score >= 90:
       return "A"
   elif $score >= 80:
       return "B"
   elif $score >= 70:
       return "C"
   elif $score >= 60:
       return "D"
   return "F"
   """,
   r"""
   for $cut, $letter in ((90, "A"), (80, "B"), (70, "C"), (60, "D")):
       if $score >= $cut:
           return $letter
   return "F"
   """],
  [(95,), (85,), (72,), (60,), (12,)])

F("fizzbuzz", "logic", "fizzbuzz fizz_buzz", "n:POSINT",
  ['Return "Fizz" if $n is divisible by 3, "Buzz" if divisible by 5, "FizzBuzz" if divisible by both, and otherwise $n as a string.'],
  [r"""
   if $n % 15 == 0:
       return "FizzBuzz"
   if $n % 3 == 0:
       return "Fizz"
   if $n % 5 == 0:
       return "Buzz"
   return str($n)
   """,
   r"""
   $out = ""
   if $n % 3 == 0:
       $out += "Fizz"
   if $n % 5 == 0:
       $out += "Buzz"
   return $out or str($n)
   """],
  [(3,), (5,), (15,), (7,)])

F("classify_sign", "logic", "describe_number classify_number number_kind", "n:INT",
  ['Return "positive", "negative", or "zero" depending on $n.'],
  [r"""
   if $n > 0:
       return "positive"
   elif $n < 0:
       return "negative"
   return "zero"
   """,
   'return "positive" if $n > 0 else "negative" if $n < 0 else "zero"'],
  [(3,), (-1,), (0,)])

F("yes_no", "logic", "yes_no to_yes_no as_yes_no", "flag:FLAG",
  ['Return "yes" if $flag is true, otherwise "no".'],
  ['return "yes" if $flag else "no"', 'if $flag:\n    return "yes"\nreturn "no"'],
  [(True,), (False,)])

F("ticket_price", "logic", "ticket_price price_for_age admission_price", "age:AGE",
  ["Return 0 when $age is under 3, 8 when it is under 13, 12 when it is 65 or more, and 15 otherwise."],
  [r"""
   if $age < 3:
       return 0
   if $age < 13:
       return 8
   if $age >= 65:
       return 12
   return 15
   """,
   r"""
   if $age < 3:
       return 0
   elif $age < 13:
       return 8
   elif $age >= 65:
       return 12
   else:
       return 15
   """],
  [(1,), (10,), (30,), (70,)])

F("is_weekend", "logic", "is_weekend weekend_day", "day:DAY",
  ['Return True if $day is "Saturday" or "Sunday".'],
  ['return $day in ("Saturday", "Sunday")', 'return $day == "Saturday" or $day == "Sunday"',
   'if $day in ["Saturday", "Sunday"]:\n    return True\nreturn False'],
  [("Monday",), ("Sunday",)])

F("validate_age", "logic", "validate_age check_age ensure_valid_age", "age:AGE",
  ["Return $age, but raise ValueError if it is negative."],
  ['if $age < 0:\n    raise ValueError("age cannot be negative")\nreturn $age',
   'if $age < 0:\n    raise ValueError("age must be non-negative")\nreturn $age'],
  [(5,), (0,)])

F("is_leap_year", "logic", "is_leap_year leap_year is_leap", "y:YEAR",
  ["Return True if $y is a leap year."],
  ["return $y % 4 == 0 and ($y % 100 != 0 or $y % 400 == 0)",
   r"""
   if $y % 400 == 0:
       return True
   if $y % 100 == 0:
       return False
   return $y % 4 == 0
   """],
  [(2000,), (1900,), (2024,), (2023,)])

F("xor_bool", "logic", "exactly_one only_one xor", "a/b:PAIR_NUM",
  ["Return True if exactly one of $a and $b is truthy."],
  ["return bool($a) != bool($b)", "return (bool($a) and not $b) or (bool($b) and not $a)"],
  [(1, 0), (1, 1), (0, 0), (0, 5)])

# ==========================================================================
# Strings
# ==========================================================================

F("reverse_text", "strings", "reverse_string reverse_text backwards", "s:STR",
  ["Return $s reversed.", "Return the characters of $s in reverse order.", "Reverse the string $s."],
  ["return $s[::-1]",
   r"""
   $out = ""
   for $ch in $s:
       $out = $ch + $out
   return $out
   """,
   'return "".join(reversed($s))',
   r"""
   $out = ""
   for $i in range(len($s) - 1, -1, -1):
       $out += $s[$i]
   return $out
   """],
  [("hello",), ("",), ("ab",)])

F("to_upper", "strings", "shout to_upper make_upper", "s:STR",
  ["Return $s in uppercase."],
  ["return $s.upper()", 'return "".join($ch.upper() for $ch in $s)'],
  [("Hi there",)])

F("to_lower", "strings", "to_lower make_lower lowercase", "s:STR",
  ["Return $s in lowercase."],
  ["return $s.lower()", 'return "".join($ch.lower() for $ch in $s)'],
  [("Hi There",)])

F("count_char", "strings", "count_char count_letter char_count occurrences_of", "s:STR, ch:CHAR",
  ["Return how many times $ch appears in $s.", "Count the occurrences of $ch in $s."],
  ["return $s.count($ch)",
   r"""
   $count = 0
   for $c in $s:
       if $c == $ch:
           $count += 1
   return $count
   """,
   "return sum(1 for $c in $s if $c == $ch)"],
  [("banana", "a"), ("", "x")])

F("count_vowels", "strings", "count_vowels vowel_count num_vowels", "s:STR",
  ["Return the number of vowels in $s, ignoring case.", "Count the vowels in $s."],
  [r"""
   $count = 0
   for $ch in $s.lower():
       if $ch in "aeiou":
           $count += 1
   return $count
   """,
   'return sum(1 for $ch in $s.lower() if $ch in "aeiou")',
   'return len([$ch for $ch in $s.lower() if $ch in "aeiou"])'],
  [("Hello World",), ("",), ("AEIOU xyz",)])

F("remove_vowels", "strings", "remove_vowels strip_vowels without_vowels", "s:STR",
  ["Return $s with all vowels removed."],
  ['return "".join($ch for $ch in $s if $ch.lower() not in "aeiou")',
   r"""
   $out = ""
   for $ch in $s:
       if $ch.lower() not in "aeiou":
           $out += $ch
   return $out
   """],
  [("Education",), ("xyz",)])

F("count_upper", "strings", "count_upper count_capitals uppercase_count", "s:STR",
  ["Return how many uppercase letters are in $s."],
  ["return sum(1 for $ch in $s if $ch.isupper())",
   r"""
   $count = 0
   for $ch in $s:
       if $ch.isupper():
           $count += 1
   return $count
   """],
  [("Hello World",), ("abc",)])

F("capitalize_words", "strings", "capitalize_words title_words capitalize_each", "s:SENT",
  ["Return $s with every word capitalized and single spaces between words."],
  ['return " ".join($w.capitalize() for $w in $s.split())',
   r"""
   $words = []
   for $w in $s.split():
       $words.append($w.capitalize())
   return " ".join($words)
   """],
  [("hello big world",), ("",)])

F("first_word", "strings", "first_word leading_word get_first_word", "s:SENT",
  ["Return the first word in $s, or an empty string if there are no words."],
  ['$words = $s.split()\nif not $words:\n    return ""\nreturn $words[0]',
   '$words = $s.split()\nreturn $words[0] if $words else ""'],
  [("hello there",), ("",), ("   x  y",)])

F("last_word", "strings", "last_word final_word get_last_word", "s:SENT",
  ["Return the last word in $s, or an empty string if there are no words."],
  ['$words = $s.split()\nif not $words:\n    return ""\nreturn $words[-1]',
   '$words = $s.split()\nreturn $words[-1] if $words else ""'],
  [("hello there",), ("",)])

F("longest_word", "strings", "longest_word find_longest_word", "s:SENT",
  ["Return the longest word in $s, which has at least one word. Ties go to the first word."],
  [r"""
   $longest = ""
   for $w in $s.split():
       if len($w) > len($longest):
           $longest = $w
   return $longest
   """,
   "return max($s.split(), key=len)"],
  [("a bb ccc dd",), ("one two six",)])

F("shortest_word", "strings", "shortest_word find_shortest_word", "s:SENT",
  ["Return the shortest word in $s, which has at least one word. Ties go to the first word."],
  [r"""
   $shortest = None
   for $w in $s.split():
       if $shortest is None or len($w) < len($shortest):
           $shortest = $w
   return $shortest
   """,
   "return min($s.split(), key=len)"],
  [("aaa bb c dd",), ("one two six",)])

F("word_lengths", "strings", "word_lengths lengths_of_words", "s:SENT",
  ["Return a list with the length of each word in $s."],
  ["return [len($w) for $w in $s.split()]",
   r"""
   $out = []
   for $w in $s.split():
       $out.append(len($w))
   return $out
   """],
  [("the quick fox",), ("",)])

F("acronym", "strings", "acronym initials make_acronym", "s:SENT",
  ["Return the uppercase first letter of each word in $s, joined together."],
  ['return "".join($w[0].upper() for $w in $s.split())',
   r"""
   $out = ""
   for $w in $s.split():
       $out += $w[0].upper()
   return $out
   """],
  [("portable network graphics",), ("",)])

F("is_anagram", "strings", "is_anagram are_anagrams anagrams", "a/b:PAIR_STR",
  ["Return True if $a and $b contain exactly the same characters in any order."],
  ["return sorted($a) == sorted($b)",
   r"""
   if len($a) != len($b):
       return False
   for $ch in $a:
       if $a.count($ch) != $b.count($ch):
           return False
   return True
   """],
  [("listen", "silent"), ("abc", "abd"), ("", "")])

F("replace_char", "strings", "replace_char substitute_char swap_char", "s:STR, old/new:OLDNEW",
  ["Return $s with every character $old replaced by $new."],
  ["return $s.replace($old, $new)",
   r"""
   $out = ""
   for $ch in $s:
       if $ch == $old:
           $out += $new
       else:
           $out += $ch
   return $out
   """,
   'return "".join($new if $ch == $old else $ch for $ch in $s)'],
  [("banana", "a", "o"), ("", "x", "y")])

F("remove_spaces", "strings", "remove_spaces strip_spaces no_spaces", "s:STR",
  ["Return $s with all spaces removed."],
  ['return $s.replace(" ", "")', 'return "".join($ch for $ch in $s if $ch != " ")',
   r"""
   $out = ""
   for $ch in $s:
       if $ch != " ":
           $out += $ch
   return $out
   """],
  [("a b  c",), ("",)])

F("normalize_spaces", "strings", "normalize_spaces collapse_spaces squeeze_spaces", "s:STR",
  ["Collapse runs of whitespace in $s into single spaces and trim the ends."],
  ['return " ".join($s.split())', '$words = $s.split()\nreturn " ".join($words)'],
  [("  a   b ",), ("",)])

F("repeat_text", "strings", "repeat_text repeat_string echo", "s:STR, n:COUNT",
  ["Return $s repeated $n times."],
  ["return $s * $n",
   r"""
   $out = ""
   for _ in range($n):
       $out += $s
   return $out
   """],
  [("ab", 3), ("x", 0)])

F("pad_left", "strings", "pad_left left_pad pad_start", "s:STR, width:WIDTH, ch:FILL",
  ["Pad $s on the left with $ch until it is at least $width characters long."],
  ["return $s.rjust($width, $ch)",
   "while len($s) < $width:\n    $s = $ch + $s\nreturn $s",
   "return $ch * ($width - len($s)) + $s"],
  [("7", 3, "0"), ("hello", 2, "*")])

F("pad_right", "strings", "pad_right right_pad pad_end", "s:STR, width:WIDTH, ch:FILL",
  ["Pad $s on the right with $ch until it is at least $width characters long."],
  ["return $s.ljust($width, $ch)",
   "while len($s) < $width:\n    $s = $s + $ch\nreturn $s",
   "return $s + $ch * ($width - len($s))"],
  [("7", 3, "0"), ("hello", 2, "*")])

F("truncate", "strings", "truncate shorten clip_text", "s:STR, n:SIZE",
  ['Return $s cut to at most $n characters, adding "..." if anything was removed.'],
  ['if len($s) <= $n:\n    return $s\nreturn $s[:$n] + "..."',
   'return $s if len($s) <= $n else $s[:$n] + "..."'],
  [("hello world", 5), ("hi", 5)])

F("starts_with_vowel", "strings", "starts_with_vowel begins_with_vowel", "s:WORD",
  ["Return True if $s starts with a vowel, ignoring case."],
  ['return len($s) > 0 and $s[0].lower() in "aeiou"',
   'if not $s:\n    return False\nreturn $s[0].lower() in "aeiou"'],
  [("apple",), ("Egg",), ("tree",), ("",)])

F("all_digits", "strings", "is_digits all_digits is_numeric_text", "s:STR",
  ["Return True if $s is non-empty and contains only digits."],
  ["return $s.isdigit()",
   r"""
   if not $s:
       return False
   for $ch in $s:
       if $ch not in "0123456789":
           return False
   return True
   """],
  [("123",), ("12a",), ("",)])

F("extract_digits", "strings", "extract_digits digits_only keep_digits", "s:STR",
  ["Return a string containing only the digits from $s."],
  ['return "".join($ch for $ch in $s if $ch.isdigit())',
   r"""
   $out = ""
   for $ch in $s:
       if $ch.isdigit():
           $out += $ch
   return $out
   """],
  [("a1b2c3",), ("none",)])

F("char_frequency", "strings", "char_frequency letter_counts count_chars", "s:STR",
  ["Return a dictionary mapping each character in $s to how many times it appears."],
  [r"""
   $d = {}
   for $ch in $s:
       $d[$ch] = $d.get($ch, 0) + 1
   return $d
   """,
   r"""
   $d = {}
   for $ch in $s:
       if $ch in $d:
           $d[$ch] += 1
       else:
           $d[$ch] = 1
   return $d
   """],
  [("hello",), ("",)])

F("most_common_char", "strings", "most_common_char most_frequent_char top_char", "s:STR",
  ["Return the character that appears most often in the non-empty string $s. Break ties by first appearance."],
  [r"""
   $d = {}
   for $ch in $s:
       $d[$ch] = $d.get($ch, 0) + 1
   return max($d, key=$d.get)
   """,
   r"""
   $best = $s[0]
   for $ch in $s:
       if $s.count($ch) > $s.count($best):
           $best = $ch
   return $best
   """],
  [("banana",), ("abcabc",)])

F("first_unique_char", "strings", "first_unique_char first_non_repeating", "s:STR",
  ["Return the first character in $s that appears only once, or None if there is none."],
  [r"""
   for $ch in $s:
       if $s.count($ch) == 1:
           return $ch
   return None
   """,
   r"""
   $d = {}
   for $ch in $s:
       $d[$ch] = $d.get($ch, 0) + 1
   for $ch in $s:
       if $d[$ch] == 1:
           return $ch
   return None
   """],
  [("swiss",), ("aabb",)])

F("swap_case", "strings", "swap_case invert_case flip_case", "s:STR",
  ["Return $s with uppercase letters made lowercase and lowercase letters made uppercase."],
  ["return $s.swapcase()",
   r"""
   $out = ""
   for $ch in $s:
       if $ch.isupper():
           $out += $ch.lower()
       else:
           $out += $ch.upper()
   return $out
   """],
  [("Hello World",)])

F("count_substring", "strings", "count_substring substring_count occurrences", "s:STR, sub:SUB",
  ["Return how many non-overlapping times $sub appears in $s. $sub is not empty."],
  ["return $s.count($sub)",
   r"""
   $count = 0
   $i = $s.find($sub)
   while $i != -1:
       $count += 1
       $i = $s.find($sub, $i + len($sub))
   return $count
   """],
  [("banana", "an"), ("aaaa", "aa"), ("abc", "z")])

F("char_positions", "strings", "char_positions find_all positions_of", "s:STR, ch:CHAR",
  ["Return a list of every index where $ch appears in $s."],
  ["return [$i for $i, $c in enumerate($s) if $c == $ch]",
   r"""
   $out = []
   for $i in range(len($s)):
       if $s[$i] == $ch:
           $out.append($i)
   return $out
   """],
  [("banana", "a"), ("", "x")])

F("censor", "strings", "censor mask_word hide_word", "s:SENT, w:SUB",
  ["Return $s with every occurrence of $w replaced by asterisks of the same length."],
  ['return $s.replace($w, "*" * len($w))', '$mask = "*" * len($w)\nreturn $s.replace($w, $mask)'],
  [("the cat sat", "cat"), ("aaa", "b")])

F("count_lines", "strings", "count_lines line_count num_lines", "s:STR",
  ["Return how many lines are in $s."],
  ["return len($s.splitlines())", "$lines = $s.splitlines()\nreturn len($lines)"],
  [("a\nb\nc",), ("",)])

F("is_pangram", "strings", "is_pangram uses_every_letter", "s:SENT",
  ["Return True if $s contains every letter of the alphabet, ignoring case."],
  ['return set("abcdefghijklmnopqrstuvwxyz") <= set($s.lower())',
   r"""
   for $ch in "abcdefghijklmnopqrstuvwxyz":
       if $ch not in $s.lower():
           return False
   return True
   """],
  [("The quick brown fox jumps over the lazy dog",), ("hello",)])

F("caesar_shift", "strings", "caesar_shift shift_letters caesar_cipher", "s:STR, k:STEP",
  ["Shift each lowercase letter in $s forward by $k places in the alphabet, wrapping from z back to a. Leave other characters unchanged."],
  [r"""
   $out = ""
   for $ch in $s:
       if "a" <= $ch <= "z":
           $out += chr((ord($ch) - ord("a") + $k) % 26 + ord("a"))
       else:
           $out += $ch
   return $out
   """,
   r"""
   $alphabet = "abcdefghijklmnopqrstuvwxyz"
   $out = ""
   for $ch in $s:
       if $ch in $alphabet:
           $out += $alphabet[($alphabet.index($ch) + $k) % 26]
       else:
           $out += $ch
   return $out
   """],
  [("abc xyz", 3), ("hello!", 0)])

F("run_length", "strings", "run_length_encode rle_encode compress_runs", "s:STR",
  ['Return the run-length encoding of $s, so "aaab" becomes "a3b1".'],
  [r"""
   if not $s:
       return ""
   $out = ""
   $prev = $s[0]
   $count = 1
   for $ch in $s[1:]:
       if $ch == $prev:
           $count += 1
       else:
           $out += $prev + str($count)
           $prev = $ch
           $count = 1
   $out += $prev + str($count)
   return $out
   """,
   r"""
   $out = ""
   $i = 0
   while $i < len($s):
       $j = $i
       while $j < len($s) and $s[$j] == $s[$i]:
           $j += 1
       $out += $s[$i] + str($j - $i)
       $i = $j
   return $out
   """],
  [("aaabcc",), ("",), ("x",)])

F("join_words", "strings", "join_words comma_join join_with_commas", "words:WORDS",
  ['Join the strings in $words with ", " between them.'],
  ['return ", ".join($words)',
   r"""
   $out = ""
   for $i, $w in enumerate($words):
       if $i > 0:
           $out += ", "
       $out += $w
   return $out
   """],
  [(["a", "b", "c"],), ([],)])

F("remove_punctuation", "strings", "remove_punctuation strip_punctuation", "s:SENT",
  ["Return $s without the characters . , ! ? ; and :."],
  ['return "".join($ch for $ch in $s if $ch not in ".,!?;:")',
   r"""
   $out = ""
   for $ch in $s:
       if $ch not in ".,!?;:":
           $out += $ch
   return $out
   """],
  [("Hi, there! Ok?",), ("",)])

F("ends_with", "strings", "ends_with has_suffix", "s:STR, suffix:SUFFIX",
  ["Return True if $s ends with $suffix."],
  ["return $s.endswith($suffix)", "return $s[len($s) - len($suffix):] == $suffix"],
  [("report.txt", ".txt"), ("abc", "xabc"), ("abc", "")])

F("starts_with", "strings", "starts_with has_prefix begins_with", "s:STR, prefix:PREFIX",
  ["Return True if $s begins with $prefix."],
  ["return $s.startswith($prefix)", "return $s[:len($prefix)] == $prefix"],
  [("hello", "he"), ("hello", "lo"), ("", "")])

F("has_digit", "strings", "has_digit contains_digit any_digit", "s:STR",
  ["Return True if $s contains at least one digit."],
  ["return any($ch.isdigit() for $ch in $s)",
   r"""
   for $ch in $s:
       if $ch.isdigit():
           return True
   return False
   """],
  [("abc1",), ("abc",)])

F("middle_char", "strings", "middle_char center_char middle", "s:WORD",
  ["Return the middle character of the non-empty string $s, or the middle two characters if its length is even."],
  [r"""
   $mid = len($s) // 2
   if len($s) % 2 == 0:
       return $s[$mid - 1:$mid + 1]
   return $s[$mid]
   """,
   r"""
   $mid = len($s) // 2
   return $s[$mid - 1:$mid + 1] if len($s) % 2 == 0 else $s[$mid]
   """],
  [("abc",), ("abcd",), ("x",)])

F("double_chars", "strings", "double_chars stutter double_letters", "s:STR",
  ["Return $s with every character repeated twice."],
  ['return "".join($ch * 2 for $ch in $s)',
   r"""
   $out = ""
   for $ch in $s:
       $out += $ch + $ch
   return $out
   """],
  [("abc",), ("",)])

F("is_lower_word", "strings", "is_all_lower all_lowercase", "s:STR",
  ["Return True if every letter in $s is lowercase."],
  ["return $s == $s.lower()",
   r"""
   for $ch in $s:
       if $ch.isupper():
           return False
   return True
   """],
  [("abc",), ("aBc",), ("",)])

# ==========================================================================
# Parsing
# ==========================================================================

F("parse_int_list", "parsing", "parse_numbers parse_int_list ints_from_csv", "s:CSV",
  ['Parse a comma-separated string of integers such as "1,2,3" into a list of ints.'],
  ['return [int($p) for $p in $s.split(",")]',
   'return list(map(int, $s.split(",")))',
   r"""
   $out = []
   for $p in $s.split(","):
       $out.append(int($p))
   return $out
   """],
  [("1,2,3",), ("10, -4",)])

F("sum_csv", "parsing", "sum_csv total_from_text add_csv", "s:CSV",
  ["Return the sum of the comma-separated integers in $s."],
  ['return sum(int($p) for $p in $s.split(","))',
   r"""
   $total = 0
   for $p in $s.split(","):
       $total += int($p)
   return $total
   """],
  [("1,2,3",), ("5",)])

F("parse_key_values", "parsing", "parse_pairs parse_key_values parse_settings", "s:CSV",
  ['Parse a string such as "a=1;b=2" into a dictionary that maps each key to its value as a string.'],
  [r"""
   $out = {}
   for $p in $s.split(";"):
       if "=" in $p:
           $k, $v = $p.split("=", 1)
           $out[$k.strip()] = $v.strip()
   return $out
   """,
   r"""
   $out = {}
   for $pair in $s.split(";"):
       if "=" not in $pair:
           continue
       $parts = $pair.split("=", 1)
       $out[$parts[0].strip()] = $parts[1].strip()
   return $out
   """],
  [("a=1;b=2",), ("x = 5",), ("",)])

F("time_to_minutes", "parsing", "time_to_minutes to_minutes parse_time", "s:TIME",
  ['Convert a time string such as "02:30" into the total number of minutes.'],
  ['$h, $m = $s.split(":")\nreturn int($h) * 60 + int($m)',
   '$parts = $s.split(":")\nreturn int($parts[0]) * 60 + int($parts[1])'],
  [("02:30",), ("00:05",)])

F("format_minutes", "parsing", "format_minutes minutes_to_clock to_clock", "n:MINUTES",
  ['Format $n minutes as hours and minutes, such as "2:05".'],
  ['$h = $n // 60\n$m = $n % 60\nreturn f"{$h}:{$m:02d}"',
   'return str($n // 60) + ":" + str($n % 60).zfill(2)'],
  [(125,), (59,), (0,)])

F("parse_bool", "parsing", "parse_bool to_bool is_truthy_text", "s:STR",
  ['Return True if $s is "yes", "true", or "1", ignoring case and surrounding spaces; otherwise return False.'],
  ['return $s.strip().lower() in ("yes", "true", "1")',
   r"""
   $s = $s.strip().lower()
   if $s == "yes" or $s == "true" or $s == "1":
       return True
   return False
   """],
  [("Yes",), ("no",), (" TRUE ",), ("1",)])

F("file_extension", "parsing", "file_extension get_extension extension_of", "name:FILENAME",
  ["Return the extension of $name without the dot, or an empty string if it has none."],
  ['if "." not in $name:\n    return ""\nreturn $name.rsplit(".", 1)[1]',
   '$idx = $name.rfind(".")\nif $idx == -1:\n    return ""\nreturn $name[$idx + 1:]'],
  [("report.pdf",), ("archive.tar.gz",), ("README",)])

F("parse_size", "parsing", "parse_size parse_dimensions", "s:STR",
  ['Parse a size string such as "3x4" into a tuple of two ints.'],
  ['$width, $height = $s.split("x")\nreturn (int($width), int($height))',
   '$parts = $s.split("x")\nreturn (int($parts[0]), int($parts[1]))'],
  [("3x4",), ("10x2",)])

F("email_domain", "parsing", "email_domain get_domain domain_of", "s:EMAIL",
  ["Return the part of the email address $s after the @ sign."],
  ['return $s.split("@")[-1]', '$idx = $s.index("@")\nreturn $s[$idx + 1:]',
   '$parts = $s.split("@")\nreturn $parts[1]'],
  [("ann@example.com",)])

F("email_user", "parsing", "email_user username_of user_part", "s:EMAIL",
  ["Return the part of the email address $s before the @ sign."],
  ['return $s.split("@")[0]', '$idx = $s.index("@")\nreturn $s[:$idx]'],
  [("ann@example.com",)])

F("strip_comment", "parsing", "strip_comment remove_comment drop_comment", "line:CSV",
  ["Remove everything from the first # in $line onward, then strip trailing spaces."],
  ['return $line.split("#", 1)[0].rstrip()',
   r"""
   $idx = $line.find("#")
   if $idx != -1:
       $line = $line[:$idx]
   return $line.rstrip()
   """],
  [("x = 1  # set x",), ("# only",), ("plain",)])

F("expand_range", "parsing", "expand_range parse_range range_from_text", "s:STR",
  ['Turn a string such as "3-7" into the list of integers from 3 to 7 inclusive.'],
  ['$left, $right = $s.split("-")\nreturn list(range(int($left), int($right) + 1))',
   r"""
   $parts = $s.split("-")
   $out = []
   for $num in range(int($parts[0]), int($parts[1]) + 1):
       $out.append($num)
   return $out
   """],
  [("3-7",), ("5-5",)])

F("word_frequencies", "parsing", "word_frequencies word_freq tally_words", "s:SENT",
  ["Return a dictionary that maps each word in $s to how many times it appears."],
  [r"""
   $d = {}
   for $w in $s.split():
       $d[$w] = $d.get($w, 0) + 1
   return $d
   """,
   r"""
   $d = {}
   for $w in $s.split():
       if $w not in $d:
           $d[$w] = 0
       $d[$w] += 1
   return $d
   """],
  [("a b a",), ("",)])

F("valid_identifier", "parsing", "is_valid_name valid_identifier is_identifier", "s:STR",
  ["Return True if $s is non-empty, does not start with a digit, and has only letters, digits, and underscores."],
  [r"""
   if not $s or $s[0].isdigit():
       return False
   for $ch in $s:
       if not ($ch.isalnum() or $ch == "_"):
           return False
   return True
   """,
   r"""
   if not $s or $s[0] in "0123456789":
       return False
   return all($ch.isalnum() or $ch == "_" for $ch in $s)
   """],
  [("my_var1",), ("1abc",), ("",), ("a-b",)])

F("parse_record", "parsing", "parse_record parse_person split_record", "s:CSV",
  ['Split a line such as "Ann,32" into a tuple of the name and the age as an int.'],
  ['$k, $v = $s.split(",")\nreturn ($k, int($v))',
   '$parts = $s.split(",")\nreturn ($parts[0], int($parts[1]))'],
  [("Ann,32",)])

# ==========================================================================
# Lists
# ==========================================================================

F("sum_list", "lists", "sum_list list_total add_all", "nums:NUMS",
  ["Return the sum of the numbers in $nums.", "Add up all the values in $nums."],
  [r"""
   $total = 0
   for $num in $nums:
       $total += $num
   return $total
   """,
   "return sum($nums)"],
  [([1, 2, 3],), ([],)])

F("product", "lists", "product multiply_all list_product", "nums:NUMS",
  ["Return the product of the numbers in $nums, or 1 if it is empty."],
  [r"""
   $out = 1
   for $num in $nums:
       $out *= $num
   return $out
   """,
   r"""
   $out = 1
   $i = 0
   while $i < len($nums):
       $out *= $nums[$i]
       $i += 1
   return $out
   """],
  [([2, 3, 4],), ([],)])

F("find_max", "lists", "find_max largest max_value", "nums:NUMS",
  ["Return the largest number in the non-empty list $nums."],
  [r"""
   $hi = $nums[0]
   for $num in $nums:
       if $num > $hi:
           $hi = $num
   return $hi
   """,
   "return max($nums)", "return sorted($nums)[-1]"],
  [([3, 9, 2],), ([-5, -1],)])

F("find_min", "lists", "find_min smallest min_value", "nums:NUMS",
  ["Return the smallest number in the non-empty list $nums."],
  [r"""
   $lo = $nums[0]
   for $num in $nums[1:]:
       if $num < $lo:
           $lo = $num
   return $lo
   """,
   "return min($nums)", "return sorted($nums)[0]"],
  [([3, 9, 2],), ([-5, -1],)])

F("max_or_none", "lists", "max_or_none safe_max largest_or_none", "nums:NUMS",
  ["Return the largest value in $nums, or None if $nums is empty."],
  ["if not $nums:\n    return None\nreturn max($nums)",
   r"""
   $hi = None
   for $num in $nums:
       if $hi is None or $num > $hi:
           $hi = $num
   return $hi
   """],
  [([4, 1],), ([],)])

F("index_of_max", "lists", "index_of_max argmax max_index", "nums:NUMS",
  ["Return the index of the first largest value in the non-empty list $nums."],
  ["return $nums.index(max($nums))",
   r"""
   $best_i = 0
   for $i in range(1, len($nums)):
       if $nums[$i] > $nums[$best_i]:
           $best_i = $i
   return $best_i
   """],
  [([3, 9, 2, 9],), ([1],)])

F("value_range", "lists", "value_range spread max_minus_min", "nums:NUMS",
  ["Return the difference between the largest and smallest values in the non-empty list $nums."],
  ["return max($nums) - min($nums)",
   r"""
   $lo = $nums[0]
   $hi = $nums[0]
   for $num in $nums:
       if $num < $lo:
           $lo = $num
       if $num > $hi:
           $hi = $num
   return $hi - $lo
   """],
  [([3, 9, 2],), ([4],)])

F("min_and_max", "lists", "min_and_max bounds extremes", "nums:NUMS",
  ["Return a tuple of the smallest and largest values in the non-empty list $nums."],
  ["return (min($nums), max($nums))",
   "$out = sorted($nums)\nreturn ($out[0], $out[-1])"],
  [([3, 9, 2],), ([4],)])

F("count_positive", "lists", "count_positive num_positive positives_count", "nums:NUMS",
  ["Return how many numbers in $nums are greater than zero."],
  [r"""
   $count = 0
   for $num in $nums:
       if $num > 0:
           $count += 1
   return $count
   """,
   "return sum(1 for $num in $nums if $num > 0)",
   "return len([$num for $num in $nums if $num > 0])"],
  [([1, -2, 3, 0],), ([],)])

F("sum_positive", "lists", "sum_positive positive_total", "nums:NUMS",
  ["Return the sum of only the positive numbers in $nums."],
  [r"""
   $total = 0
   for $num in $nums:
       if $num > 0:
           $total += $num
   return $total
   """,
   "return sum($num for $num in $nums if $num > 0)"],
  [([1, -2, 3],), ([],)])

F("sum_even", "lists", "sum_even even_total sum_of_evens", "nums:NUMS",
  ["Return the sum of the even numbers in $nums."],
  [r"""
   $total = 0
   for $num in $nums:
       if $num % 2 == 0:
           $total += $num
   return $total
   """,
   "return sum($num for $num in $nums if $num % 2 == 0)"],
  [([1, 2, 3, 4],), ([],)])

F("filter_even", "lists", "filter_even evens only_even get_evens", "nums:NUMS",
  ["Return a list of the even numbers in $nums."],
  ["return [$num for $num in $nums if $num % 2 == 0]",
   r"""
   $out = []
   for $num in $nums:
       if $num % 2 == 0:
           $out.append($num)
   return $out
   """,
   "return list(filter(lambda $num: $num % 2 == 0, $nums))"],
  [([1, 2, 3, 4],), ([],)])

F("filter_odd", "lists", "filter_odd odds only_odd get_odds", "nums:NUMS",
  ["Return a list of the odd numbers in $nums."],
  ["return [$num for $num in $nums if $num % 2 != 0]",
   r"""
   $out = []
   for $num in $nums:
       if $num % 2 == 1:
           $out.append($num)
   return $out
   """],
  [([1, 2, 3, 4],), ([],)])

F("remove_negatives", "lists", "remove_negatives non_negative drop_negatives", "nums:NUMS",
  ["Return $nums without its negative numbers."],
  ["return [$num for $num in $nums if $num >= 0]",
   r"""
   $out = []
   for $num in $nums:
       if $num < 0:
           continue
       $out.append($num)
   return $out
   """],
  [([1, -2, 0, 3],), ([],)])

F("greater_than", "lists", "greater_than above filter_above", "nums:NUMS, limit:LIMIT",
  ["Return the values in $nums that are greater than $limit."],
  ["return [$num for $num in $nums if $num > $limit]",
   r"""
   $out = []
   for $num in $nums:
       if $num > $limit:
           $out.append($num)
   return $out
   """],
  [([1, 5, 3, 8], 3), ([], 0)])

F("count_above", "lists", "count_above count_greater", "nums:NUMS, limit:LIMIT",
  ["Return how many values in $nums are greater than $limit."],
  ["return sum(1 for $num in $nums if $num > $limit)",
   r"""
   $count = 0
   for $num in $nums:
       if $num > $limit:
           $count += 1
   return $count
   """],
  [([1, 5, 3, 8], 3), ([], 0)])

F("square_all", "lists", "square_all squares squared_values", "nums:NUMS",
  ["Return a list with every number in $nums squared."],
  ["return [$num * $num for $num in $nums]",
   r"""
   $out = []
   for $num in $nums:
       $out.append($num ** 2)
   return $out
   """,
   "return list(map(lambda $num: $num * $num, $nums))"],
  [([1, 2, 3],), ([],)])

F("double_all", "lists", "double_all doubled times_two", "nums:NUMS",
  ["Return a new list with every number in $nums doubled."],
  ["return [$num * 2 for $num in $nums]",
   r"""
   $out = []
   for $num in $nums:
       $out.append(2 * $num)
   return $out
   """],
  [([1, 2, 3],), ([],)])

F("scale_values", "lists", "scale_values multiply_each scale_list", "nums:NUMS, k:FACTOR",
  ["Return a new list with every number in $nums multiplied by $k."],
  ["return [$num * $k for $num in $nums]",
   r"""
   $out = []
   for $num in $nums:
       $out.append($num * $k)
   return $out
   """],
  [([1, 2, 3], 3), ([], 2)])

F("add_to_each", "lists", "add_to_each shift_values offset_all", "nums:NUMS, k:OFFSET",
  ["Return a new list with $k added to every number in $nums."],
  ["return [$num + $k for $num in $nums]",
   r"""
   $out = []
   for $num in $nums:
       $out.append($num + $k)
   return $out
   """],
  [([1, 2, 3], 10), ([], 2)])

F("cumulative_sum", "lists", "cumulative_sum running_total prefix_sums", "nums:NUMS",
  ["Return a list where each element is the sum of $nums up to and including that position."],
  [r"""
   $out = []
   $total = 0
   for $num in $nums:
       $total += $num
       $out.append($total)
   return $out
   """,
   "return [sum($nums[:$i + 1]) for $i in range(len($nums))]"],
  [([1, 2, 3],), ([],)])

F("differences", "lists", "differences pairwise_differences deltas", "nums:NUMS",
  ["Return the differences between each pair of neighbouring values in $nums."],
  ["return [$nums[$i + 1] - $nums[$i] for $i in range(len($nums) - 1)]",
   "return [$y - $x for $x, $y in zip($nums, $nums[1:])]",
   r"""
   $out = []
   for $i in range(1, len($nums)):
       $out.append($nums[$i] - $nums[$i - 1])
   return $out
   """],
  [([1, 4, 9],), ([5],)])

F("is_sorted", "lists", "is_sorted sorted_check in_order", "nums:NUMS",
  ["Return True if $nums is in non-decreasing order."],
  [r"""
   for $i in range(len($nums) - 1):
       if $nums[$i] > $nums[$i + 1]:
           return False
   return True
   """,
   "return all($x <= $y for $x, $y in zip($nums, $nums[1:]))",
   "return $nums == sorted($nums)"],
  [([1, 2, 2, 5],), ([3, 1],), ([],)])

F("reverse_list", "lists", "reverse_list reversed_list backwards_list", "items:ITEMS",
  ["Return a new list with the items of $items in reverse order."],
  ["return $items[::-1]", "return list(reversed($items))",
   r"""
   $out = []
   for $x in $items:
       $out.insert(0, $x)
   return $out
   """],
  [([1, 2, 3],), ([],)])

F("dedupe", "lists", "dedupe unique remove_duplicates distinct", "items:ITEMS",
  ["Return $items without duplicates, keeping the first occurrence of each value."],
  [r"""
   $seen = set()
   $out = []
   for $x in $items:
       if $x not in $seen:
           $seen.add($x)
           $out.append($x)
   return $out
   """,
   "return list(dict.fromkeys($items))",
   r"""
   $out = []
   for $x in $items:
       if $x not in $out:
           $out.append($x)
   return $out
   """],
  [([3, 1, 3, 2, 1],), ([],)])

F("has_duplicates", "lists", "has_duplicates contains_duplicates any_repeats", "items:ITEMS",
  ["Return True if any value appears more than once in $items."],
  ["return len(set($items)) != len($items)",
   r"""
   $seen = set()
   for $x in $items:
       if $x in $seen:
           return True
       $seen.add($x)
   return False
   """],
  [([1, 2, 1],), ([1, 2, 3],), ([],)])

F("count_occurrences", "lists", "count_occurrences count_of how_many", "items:ITEMS, t:TARGET",
  ["Return how many times $t appears in $items."],
  ["return $items.count($t)",
   r"""
   $count = 0
   for $x in $items:
       if $x == $t:
           $count += 1
   return $count
   """],
  [([1, 2, 1, 1], 1), ([], 3)])

F("remove_all", "lists", "remove_all without drop_value", "items:ITEMS, t:TARGET",
  ["Return a new list with every occurrence of $t removed from $items."],
  ["return [$x for $x in $items if $x != $t]",
   r"""
   $out = []
   for $x in $items:
       if $x != $t:
           $out.append($x)
   return $out
   """],
  [([1, 2, 1, 3], 1), ([], 0)])

F("find_index", "lists", "find_index index_of position_of", "items:ITEMS, t:TARGET",
  ["Return the first index of $t in $items, or -1 if it is missing."],
  [r"""
   for $i, $x in enumerate($items):
       if $x == $t:
           return $i
   return -1
   """,
   "if $t in $items:\n    return $items.index($t)\nreturn -1",
   r"""
   for $i in range(len($items)):
       if $items[$i] == $t:
           return $i
   return -1
   """],
  [([4, 5, 6, 5], 5), ([1], 9)])

F("last_index", "lists", "last_index last_position rindex_of", "items:ITEMS, t:TARGET",
  ["Return the last index of $t in $items, or -1 if it is missing."],
  [r"""
   for $i in range(len($items) - 1, -1, -1):
       if $items[$i] == $t:
           return $i
   return -1
   """,
   r"""
   $pos = -1
   for $i, $x in enumerate($items):
       if $x == $t:
           $pos = $i
   return $pos
   """],
  [([4, 5, 6, 5], 5), ([1], 9)])

F("contains", "lists", "contains includes has_item", "items:ITEMS, t:TARGET",
  ["Return True if $t is in $items."],
  ["return $t in $items",
   r"""
   for $x in $items:
       if $x == $t:
           return True
   return False
   """],
  [([1, 2], 2), ([], 1)])

F("first_n", "lists", "first_n take head_items", "items:ITEMS, n:N",
  ["Return the first $n items of $items."],
  ["return $items[:$n]",
   r"""
   $out = []
   for $x in $items:
       if len($out) == $n:
           break
       $out.append($x)
   return $out
   """],
  [([1, 2, 3, 4], 2), ([1], 5), ([1, 2], 0)])

F("last_n", "lists", "last_n tail_items take_last", "items:ITEMS, n:N",
  ["Return the last $n items of $items."],
  ["if $n <= 0:\n    return []\nreturn $items[-$n:]",
   "return $items[max(0, len($items) - $n):]"],
  [([1, 2, 3, 4], 2), ([1], 5), ([1, 2], 0)])

F("swap_ends", "lists", "swap_ends swap_first_last", "items:ITEMS",
  ["Return a copy of $items with the first and last elements swapped."],
  [r"""
   $out = list($items)
   if len($out) >= 2:
       $out[0], $out[-1] = $out[-1], $out[0]
   return $out
   """,
   r"""
   if len($items) < 2:
       return list($items)
   return [$items[-1]] + $items[1:-1] + [$items[0]]
   """],
  [([1, 2, 3, 4],), ([1],), ([],)])

F("chunk", "lists", "chunk chunks split_into_chunks batches_of", "items:ITEMS, size:SIZE",
  ["Split $items into lists of at most $size items. $size is positive."],
  ["return [$items[$i:$i + $size] for $i in range(0, len($items), $size)]",
   r"""
   $out = []
   for $i in range(0, len($items), $size):
       $out.append($items[$i:$i + $size])
   return $out
   """],
  [([1, 2, 3, 4, 5], 2), ([], 3)])

F("zip_pairs", "lists", "pair_up zip_lists make_pairs", "a/b:PAIR_LIST",
  ["Return a list of tuples that pair items from $a and $b by position."],
  ["return list(zip($a, $b))",
   r"""
   $out = []
   for $i in range(min(len($a), len($b))):
       $out.append(($a[$i], $b[$i]))
   return $out
   """],
  [([1, 2, 3], ["a", "b", "c"]), ([1], [])])

F("interleave", "lists", "interleave alternate weave", "a/b:PAIR_LIST",
  ["Return a list that alternates items from $a and $b, then adds any leftover items."],
  [r"""
   $out = []
   for $i in range(max(len($a), len($b))):
       if $i < len($a):
           $out.append($a[$i])
       if $i < len($b):
           $out.append($b[$i])
   return $out
   """,
   r"""
   $out = []
   $i = 0
   while $i < len($a) or $i < len($b):
       if $i < len($a):
           $out.append($a[$i])
       if $i < len($b):
           $out.append($b[$i])
       $i += 1
   return $out
   """],
  [([1, 2, 3], [9]), ([], [1, 2])])

F("difference", "lists", "difference only_in_first missing_from", "a/b:PAIR_LIST",
  ["Return the items in $a that are not in $b, keeping their order."],
  ["return [$x for $x in $a if $x not in $b]",
   r"""
   $out = []
   for $x in $a:
       if $x not in $b:
           $out.append($x)
   return $out
   """],
  [([1, 2, 3, 4], [2, 4]), ([], [1])])

F("count_in_range", "lists", "count_in_range count_between", "nums:NUMS, lo/hi:RANGE",
  ["Return how many numbers in $nums are between $lo and $hi, inclusive."],
  ["return sum(1 for $num in $nums if $lo <= $num <= $hi)",
   r"""
   $count = 0
   for $num in $nums:
       if $num >= $lo and $num <= $hi:
           $count += 1
   return $count
   """],
  [([1, 5, 7, 10], 2, 7), ([], 0, 1)])

F("all_positive", "lists", "all_positive every_positive", "nums:NUMS",
  ["Return True if every number in $nums is greater than zero."],
  ["return all($num > 0 for $num in $nums)",
   r"""
   for $num in $nums:
       if $num <= 0:
           return False
   return True
   """],
  [([1, 2],), ([1, -1],), ([],)])

F("any_negative", "lists", "any_negative has_negative", "nums:NUMS",
  ["Return True if $nums contains a negative number."],
  ["return any($num < 0 for $num in $nums)",
   r"""
   for $num in $nums:
       if $num < 0:
           return True
   return False
   """],
  [([1, 2],), ([1, -1],), ([],)])

F("sum_of_squares", "lists", "sum_of_squares squares_total", "nums:NUMS",
  ["Return the sum of the squares of the numbers in $nums."],
  ["return sum($num * $num for $num in $nums)",
   r"""
   $total = 0
   for $num in $nums:
       $total += $num ** 2
   return $total
   """],
  [([1, 2, 3],), ([],)])

F("dot_product", "lists", "dot_product dot", "a/b:PAIR_LIST",
  ["Return the dot product of the equal-length number lists $a and $b."],
  ["return sum($x * $y for $x, $y in zip($a, $b))",
   r"""
   $total = 0
   for $i in range(len($a)):
       $total += $a[$i] * $b[$i]
   return $total
   """],
  [([1, 2, 3], [4, 5, 6]), ([], [])])

F("add_lists", "lists", "add_lists elementwise_sum vector_add", "a/b:PAIR_LIST",
  ["Return a list with the sums of the numbers at matching positions in $a and $b."],
  ["return [$x + $y for $x, $y in zip($a, $b)]",
   r"""
   $out = []
   for $i in range(min(len($a), len($b))):
       $out.append($a[$i] + $b[$i])
   return $out
   """],
  [([1, 2, 3], [4, 5, 6]), ([], [])])

F("window_sums", "lists", "window_sums sliding_sums", "nums:NUMS, k:SIZE",
  ["Return the sums of every run of $k consecutive numbers in $nums."],
  ["return [sum($nums[$i:$i + $k]) for $i in range(len($nums) - $k + 1)]",
   r"""
   $out = []
   for $i in range(len($nums) - $k + 1):
       $total = 0
       for $j in range($i, $i + $k):
           $total += $nums[$j]
       $out.append($total)
   return $out
   """],
  [([1, 2, 3, 4], 2), ([1, 2], 3)])

F("max_subarray", "algorithms", "max_subarray_sum best_slice_sum", "nums:NUMS",
  ["Return the largest sum of any non-empty run of consecutive numbers in the non-empty list $nums."],
  [r"""
   $best = $nums[0]
   $total = 0
   for $num in $nums:
       $total = max($num, $total + $num)
       $best = max($best, $total)
   return $best
   """,
   r"""
   $best = $nums[0]
   for $i in range(len($nums)):
       $total = 0
       for $j in range($i, len($nums)):
           $total += $nums[$j]
           if $total > $best:
               $best = $total
   return $best
   """],
  [([-2, 1, -3, 4, -1, 2, 1, -5, 4],), ([-3, -1],)])

F("two_sum", "algorithms", "two_sum find_pair pair_with_sum", "nums:NUMS, t:TARGET",
  ["Return the indices of two different positions in $nums whose values add up to $t, or None."],
  [r"""
   for $i in range(len($nums)):
       for $j in range($i + 1, len($nums)):
           if $nums[$i] + $nums[$j] == $t:
               return ($i, $j)
   return None
   """,
   r"""
   $seen = {}
   for $i, $num in enumerate($nums):
       if $t - $num in $seen:
           return ($seen[$t - $num], $i)
       $seen[$num] = $i
   return None
   """],
  [([2, 7, 11, 15], 9), ([1, 2], 10)])

F("binary_search", "algorithms", "binary_search bsearch search_sorted", "nums:NUMS, t:TARGET",
  ["Return the index of $t in the sorted list $nums, or -1 if it is missing."],
  [r"""
   $left = 0
   $right = len($nums) - 1
   while $left <= $right:
       $mid = ($left + $right) // 2
       if $nums[$mid] == $t:
           return $mid
       if $nums[$mid] < $t:
           $left = $mid + 1
       else:
           $right = $mid - 1
   return -1
   """,
   r"""
   $left, $right = 0, len($nums)
   while $left < $right:
       $mid = ($left + $right) // 2
       if $nums[$mid] < $t:
           $left = $mid + 1
       else:
           $right = $mid
   if $left < len($nums) and $nums[$left] == $t:
       return $left
   return -1
   """],
  [([1, 3, 5, 7, 9], 7), ([1, 3, 5], 4), ([], 1)])

F("bubble_sort", "algorithms", "bubble_sort sort_numbers simple_sort", "nums:NUMS",
  ["Return a sorted copy of $nums using bubble sort."],
  [r"""
   $out = list($nums)
   for $i in range(len($out)):
       for $j in range(len($out) - 1 - $i):
           if $out[$j] > $out[$j + 1]:
               $out[$j], $out[$j + 1] = $out[$j + 1], $out[$j]
   return $out
   """,
   r"""
   $out = list($nums)
   $swapped = True
   while $swapped:
       $swapped = False
       for $i in range(len($out) - 1):
           if $out[$i] > $out[$i + 1]:
               $out[$i], $out[$i + 1] = $out[$i + 1], $out[$i]
               $swapped = True
   return $out
   """],
  [([5, 2, 9, 1],), ([],)])

F("selection_sort", "algorithms", "selection_sort sort_by_selection", "nums:NUMS",
  ["Return a sorted copy of $nums using selection sort."],
  [r"""
   $out = list($nums)
   for $i in range(len($out)):
       $min_i = $i
       for $j in range($i + 1, len($out)):
           if $out[$j] < $out[$min_i]:
               $min_i = $j
       $out[$i], $out[$min_i] = $out[$min_i], $out[$i]
   return $out
   """],
  [([5, 2, 9, 1],), ([],)])

F("insertion_sort", "algorithms", "insertion_sort sort_by_insertion", "nums:NUMS",
  ["Return a sorted copy of $nums using insertion sort."],
  [r"""
   $out = list($nums)
   for $i in range(1, len($out)):
       $x = $out[$i]
       $j = $i - 1
       while $j >= 0 and $out[$j] > $x:
           $out[$j + 1] = $out[$j]
           $j -= 1
       $out[$j + 1] = $x
   return $out
   """],
  [([5, 2, 9, 1],), ([],)])

F("sort_descending", "lists", "sort_descending sorted_desc largest_first", "nums:NUMS",
  ["Return the numbers in $nums sorted from largest to smallest."],
  ["return sorted($nums, reverse=True)", "$out = sorted($nums)\n$out.reverse()\nreturn $out",
   "return sorted($nums)[::-1]"],
  [([3, 1, 2],), ([],)])

F("top_n", "lists", "top_n largest_n highest_values", "nums:NUMS, n:N",
  ["Return the $n largest values in $nums, from largest to smallest."],
  ["return sorted($nums, reverse=True)[:$n]", "$out = sorted($nums)\nreturn $out[::-1][:$n]"],
  [([5, 1, 9, 3], 2), ([1], 3)])

F("sort_by_length", "lists", "sort_by_length shortest_first order_by_size", "words:WORDS",
  ["Return the strings in $words ordered from shortest to longest, keeping ties in their original order."],
  ["return sorted($words, key=len)", "return sorted($words, key=lambda $w: len($w))"],
  [(["ccc", "a", "bb", "d"],), ([],)])

F("most_common", "lists", "most_common most_frequent mode_value", "items:ITEMS",
  ["Return the value that appears most often in the non-empty list $items. Break ties by first appearance."],
  [r"""
   $d = {}
   for $x in $items:
       $d[$x] = $d.get($x, 0) + 1
   return max($d, key=$d.get)
   """,
   r"""
   $best = $items[0]
   for $x in $items:
       if $items.count($x) > $items.count($best):
           $best = $x
   return $best
   """],
  [([1, 2, 2, 3],), (["a", "b"],)])

F("frequency", "lists", "frequency count_values tally", "items:ITEMS",
  ["Return a dictionary mapping each value in $items to how many times it appears."],
  [r"""
   $d = {}
   for $x in $items:
       $d[$x] = $d.get($x, 0) + 1
   return $d
   """,
   r"""
   $d = {}
   for $x in $items:
       if $x not in $d:
           $d[$x] = 0
       $d[$x] += 1
   return $d
   """],
  [([1, 2, 2, 3],), ([],)])

F("count_even_odd", "lists", "count_even_odd parity_counts", "nums:NUMS",
  ["Return a tuple of how many numbers in $nums are even and how many are odd."],
  [r"""
   $evens = 0
   $odds = 0
   for $num in $nums:
       if $num % 2 == 0:
           $evens += 1
       else:
           $odds += 1
   return ($evens, $odds)
   """,
   r"""
   $evens = sum(1 for $num in $nums if $num % 2 == 0)
   return ($evens, len($nums) - $evens)
   """],
  [([1, 2, 3, 4, 6],), ([],)])

F("split_even_odd", "lists", "split_by_parity partition_even_odd", "nums:NUMS",
  ["Return a tuple of two lists: the even numbers in $nums and the odd numbers in $nums."],
  [r"""
   $evens = []
   $odds = []
   for $num in $nums:
       if $num % 2 == 0:
           $evens.append($num)
       else:
           $odds.append($num)
   return ($evens, $odds)
   """,
   "return ([$num for $num in $nums if $num % 2 == 0], [$num for $num in $nums if $num % 2 != 0])"],
  [([1, 2, 3, 4],), ([],)])

F("partition", "lists", "partition split_at_value", "nums:NUMS, p:PIVOT",
  ["Return a tuple of two lists: the values in $nums below $p, and the rest."],
  [r"""
   $below = []
   $above = []
   for $num in $nums:
       if $num < $p:
           $below.append($num)
       else:
           $above.append($num)
   return ($below, $above)
   """,
   "return ([$num for $num in $nums if $num < $p], [$num for $num in $nums if $num >= $p])"],
  [([5, 1, 8, 3], 4), ([], 0)])

F("transpose", "lists", "transpose transpose_matrix swap_axes", "m:MATRIX",
  ["Return the transpose of the rectangular matrix $m."],
  ["return [list($row) for $row in zip(*$m)]",
   r"""
   if not $m:
       return []
   $out = []
   for $col in range(len($m[0])):
       $out.append([$row[$col] for $row in $m])
   return $out
   """],
  [([[1, 2, 3], [4, 5, 6]],), ([],)])

F("row_sums", "lists", "row_sums sum_rows totals_per_row", "m:MATRIX",
  ["Return a list with the sum of each row of $m."],
  ["return [sum($row) for $row in $m]",
   r"""
   $out = []
   for $row in $m:
       $out.append(sum($row))
   return $out
   """],
  [([[1, 2], [3, 4]],), ([],)])

F("column_sums", "lists", "column_sums sum_columns", "m:MATRIX",
  ["Return a list with the sum of each column of the non-empty rectangular matrix $m."],
  ["return [sum($row[$col] for $row in $m) for $col in range(len($m[0]))]",
   r"""
   $out = [0] * len($m[0])
   for $row in $m:
       for $col in range(len($row)):
           $out[$col] += $row[$col]
   return $out
   """],
  [([[1, 2], [3, 4]],)])

F("diagonal", "lists", "diagonal main_diagonal", "m:MATRIX",
  ["Return the values on the main diagonal of the square matrix $m."],
  ["return [$m[$i][$i] for $i in range(len($m))]",
   r"""
   $out = []
   for $i in range(len($m)):
       $out.append($m[$i][$i])
   return $out
   """],
  [([[1, 2], [3, 4]],), ([],)])

F("grid_total", "lists", "grid_total sum_matrix total_of_grid", "m:MATRIX",
  ["Return the sum of every number in the matrix $m."],
  ["return sum(sum($row) for $row in $m)",
   r"""
   $total = 0
   for $row in $m:
       for $num in $row:
           $total += $num
   return $total
   """],
  [([[1, 2], [3, 4]],), ([],)])

F("make_grid", "lists", "make_grid zeros_grid empty_grid", "r/c:RC",
  ["Return a grid of $r rows and $c columns filled with zeros."],
  ["return [[0] * $c for _ in range($r)]",
   r"""
   $out = []
   for _ in range($r):
       $out.append([0] * $c)
   return $out
   """,
   "return [[0 for _ in range($c)] for _ in range($r)]"],
  [(2, 3), (0, 4)])

F("number_items", "lists", "number_items label_items numbered_lines", "items:WORDS",
  ['Return a list of strings such as "1. apple" for each item in $items, numbered from 1.'],
  ['return [f"{$i}. {$x}" for $i, $x in enumerate($items, 1)]',
   r"""
   $out = []
   for $i, $x in enumerate($items):
       $out.append(str($i + 1) + ". " + $x)
   return $out
   """],
  [(["apple", "pear"],), ([],)])

F("range_list", "lists", "numbers_between range_list inclusive_range", "lo/hi:RANGE",
  ["Return a list of the integers from $lo to $hi, inclusive."],
  ["return list(range($lo, $hi + 1))",
   r"""
   $out = []
   $num = $lo
   while $num <= $hi:
       $out.append($num)
       $num += 1
   return $out
   """],
  [(2, 5), (3, 2)])

F("evens_up_to", "lists", "evens_up_to even_numbers evens_through", "n:NNEG",
  ["Return a list of the even numbers from 0 to $n, inclusive."],
  ["return list(range(0, $n + 1, 2))", "return [$i for $i in range($n + 1) if $i % 2 == 0]"],
  [(6,), (0,), (7,)])

F("countdown", "lists", "countdown count_down", "n:NNEG",
  ["Return a list counting down from $n to 1."],
  ["return list(range($n, 0, -1))",
   r"""
   $out = []
   while $n > 0:
       $out.append($n)
       $n -= 1
   return $out
   """],
  [(3,), (0,)])

F("replace_value", "lists", "replace_value swap_values substitute_items", "items:ITEMS, old/new:OLDNEW",
  ["Return a copy of $items with every $old replaced by $new."],
  ["return [$new if $x == $old else $x for $x in $items]",
   r"""
   $out = []
   for $x in $items:
       if $x == $old:
           $out.append($new)
       else:
           $out.append($x)
   return $out
   """],
  [([1, 2, 1], 1, 9), ([], 0, 1)])

F("remove_empty", "lists", "remove_empty drop_empty non_empty", "words:WORDS",
  ["Return the strings in $words that are not empty."],
  ["return [$w for $w in $words if $w]",
   r"""
   $out = []
   for $w in $words:
       if $w != "":
           $out.append($w)
   return $out
   """],
  [(["a", "", "b"],), ([],)])

F("string_lengths", "lists", "string_lengths lengths", "words:WORDS",
  ["Return a list with the length of each string in $words."],
  ["return [len($w) for $w in $words]", "return list(map(len, $words))"],
  [(["a", "bb"],), ([],)])

F("longest_string", "lists", "longest_string longest_item", "words:WORDS",
  ["Return the longest string in the non-empty list $words. Ties go to the first one."],
  ["return max($words, key=len)",
   r"""
   $longest = $words[0]
   for $w in $words:
       if len($w) > len($longest):
           $longest = $w
   return $longest
   """],
  [(["a", "ccc", "bb", "ddd"],)])

F("filter_prefix", "lists", "filter_by_prefix starting_with words_starting_with", "words:WORDS, prefix:PREFIX",
  ["Return the strings in $words that start with $prefix."],
  ["return [$w for $w in $words if $w.startswith($prefix)]",
   r"""
   $out = []
   for $w in $words:
       if $w[:len($prefix)] == $prefix:
           $out.append($w)
   return $out
   """],
  [(["apple", "banana", "apricot"], "ap"), ([], "x")])

F("upper_all", "lists", "upper_all shout_all uppercase_all", "words:WORDS",
  ["Return a list with every string in $words converted to uppercase."],
  ["return [$w.upper() for $w in $words]", "return list(map(str.upper, $words))",
   r"""
   $out = []
   for $w in $words:
       $out.append($w.upper())
   return $out
   """],
  [(["a", "Bc"],), ([],)])

F("join_lines", "lists", "join_lines to_lines lines_from", "words:WORDS",
  ["Join the strings in $words with newlines."],
  [r'return "\n".join($words)',
   r"""
   $out = ""
   for $i, $w in enumerate($words):
       if $i > 0:
           $out += "\n"
       $out += $w
   return $out
   """],
  [(["a", "b"],), ([],)])

F("total_length", "lists", "total_length count_all_items", "groups:LISTS",
  ["Return the total number of items across all the lists in $groups."],
  ["return sum(len($g) for $g in $groups)",
   r"""
   $total = 0
   for $g in $groups:
       $total += len($g)
   return $total
   """],
  [([[1, 2], [3], []],), ([],)])

F("longest_list", "lists", "longest_list biggest_group", "groups:LISTS",
  ["Return the longest list in the non-empty list of lists $groups. Ties go to the first one."],
  ["return max($groups, key=len)",
   r"""
   $longest = $groups[0]
   for $g in $groups:
       if len($g) > len($longest):
           $longest = $g
   return $longest
   """],
  [([[1], [2, 3], [4, 5]],)])

F("first_negative", "lists", "first_negative find_negative", "nums:NUMS",
  ["Return the first negative number in $nums, or None if there is none."],
  [r"""
   for $num in $nums:
       if $num < 0:
           return $num
   return None
   """,
   "return next(($num for $num in $nums if $num < 0), None)"],
  [([3, -1, -5],), ([1, 2],)])

F("longest_streak", "lists", "longest_streak max_run longest_run", "items:ITEMS",
  ["Return the length of the longest run of equal neighbouring values in $items."],
  [r"""
   if not $items:
       return 0
   $longest = 1
   $run = 1
   for $i in range(1, len($items)):
       if $items[$i] == $items[$i - 1]:
           $run += 1
           $longest = max($longest, $run)
       else:
           $run = 1
   return $longest
   """,
   r"""
   $longest = 0
   $run = 0
   $prev = None
   for $x in $items:
       $run = $run + 1 if $x == $prev else 1
       $prev = $x
       if $run > $longest:
           $longest = $run
   return $longest
   """],
  [([1, 1, 2, 2, 2, 3],), ([],), ([5],)])

F("running_max", "lists", "running_max prefix_max max_so_far", "nums:NUMS",
  ["Return a list where each element is the largest value of $nums seen so far."],
  [r"""
   $out = []
   $hi = None
   for $num in $nums:
       if $hi is None or $num > $hi:
           $hi = $num
       $out.append($hi)
   return $out
   """,
   "return [max($nums[:$i + 1]) for $i in range(len($nums))]"],
  [([1, 3, 2, 5],), ([],)])

F("count_matches", "lists", "count_matches same_positions", "a/b:PAIR_LIST",
  ["Return how many positions hold equal values in $a and $b."],
  ["return sum(1 for $x, $y in zip($a, $b) if $x == $y)",
   r"""
   $count = 0
   for $i in range(min(len($a), len($b))):
       if $a[$i] == $b[$i]:
           $count += 1
   return $count
   """],
  [([1, 2, 3], [1, 5, 3]), ([], [1])])

F("every_other", "lists", "every_other alternate_items even_positions", "items:ITEMS",
  ["Return every other item of $items, starting with the first."],
  ["return $items[::2]", "return [$items[$i] for $i in range(0, len($items), 2)]"],
  [([1, 2, 3, 4, 5],), ([],)])

F("drop_first", "lists", "drop_first rest_of without_first", "items:ITEMS",
  ["Return all items of $items except the first one."],
  ["return $items[1:]", "return [$x for $i, $x in enumerate($items) if $i > 0]"],
  [([1, 2, 3],), ([],)])

# ==========================================================================
# Dicts
# ==========================================================================

F("invert_dict", "dicts", "invert_dict swap_keys_values flip_dict", "d:DICT",
  ["Return a new dictionary with the keys and values of $d swapped."],
  ["return {$v: $k for $k, $v in $d.items()}",
   r"""
   $out = {}
   for $k, $v in $d.items():
       $out[$v] = $k
   return $out
   """],
  [({"a": 1, "b": 2},), ({},)])

F("keys_with_value", "dicts", "keys_with_value find_keys keys_for", "d:DICT, t:TARGET",
  ["Return a list of the keys in $d whose value equals $t."],
  ["return [$k for $k, $v in $d.items() if $v == $t]",
   r"""
   $out = []
   for $k in $d:
       if $d[$k] == $t:
           $out.append($k)
   return $out
   """],
  [({"a": 1, "b": 2, "c": 1}, 1), ({}, 0)])

F("dict_from_lists", "dicts", "make_dict zip_to_dict dict_from_lists", "keys/vals:KEYSVALS",
  ["Return a dictionary that maps each item in $keys to the item at the same position in $vals."],
  ["return dict(zip($keys, $vals))",
   "return {$keys[$i]: $vals[$i] for $i in range(min(len($keys), len($vals)))}",
   r"""
   $out = {}
   for $k, $v in zip($keys, $vals):
       $out[$k] = $v
   return $out
   """],
  [(["a", "b"], [1, 2]), ([], [])])

F("sum_values", "dicts", "sum_values total_value dict_total", "d:NUMDICT",
  ["Return the sum of all the values in $d."],
  ["return sum($d.values())",
   r"""
   $total = 0
   for $k in $d:
       $total += $d[$k]
   return $total
   """],
  [({"a": 1, "b": 2},), ({},)])

F("key_with_max", "dicts", "key_with_max best_key top_key", "d:NUMDICT",
  ["Return the key of the largest value in the non-empty dictionary $d."],
  ["return max($d, key=$d.get)",
   r"""
   $best = None
   for $k, $v in $d.items():
       if $best is None or $v > $d[$best]:
           $best = $k
   return $best
   """],
  [({"a": 1, "b": 5, "c": 2},)])

F("filter_dict", "dicts", "filter_dict above_threshold keep_large", "d:NUMDICT, limit:LIMIT",
  ["Return a new dictionary with only the items of $d whose value is at least $limit."],
  ["return {$k: $v for $k, $v in $d.items() if $v >= $limit}",
   r"""
   $out = {}
   for $k, $v in $d.items():
       if $v >= $limit:
           $out[$k] = $v
   return $out
   """],
  [({"a": 1, "b": 5}, 3), ({}, 0)])

F("get_or_default", "dicts", "lookup get_or_default safe_get", "d:DICT, k:KEY, default:DEFAULT",
  ["Return the value for $k in $d, or $default if $k is missing."],
  ["return $d.get($k, $default)",
   "if $k in $d:\n    return $d[$k]\nreturn $default",
   r"""
   try:
       return $d[$k]
   except KeyError:
       return $default
   """],
  [({"a": 1}, "a", 0), ({}, "x", -1)])

F("increment_count", "dicts", "increment_count add_count bump", "d:NUMDICT, k:KEY",
  ["Increase the count for $k in $d by one, adding it if missing, and return $d."],
  ["$d[$k] = $d.get($k, 0) + 1\nreturn $d",
   r"""
   if $k in $d:
       $d[$k] += 1
   else:
       $d[$k] = 1
   return $d
   """],
  [({"a": 1}, "a"), ({}, "x")])

F("keys_by_value", "dicts", "keys_by_value rank_keys sorted_keys_by_value", "d:NUMDICT",
  ["Return the keys of $d sorted by their values from smallest to largest."],
  ["return sorted($d, key=$d.get)",
   "return [$k for $k, $v in sorted($d.items(), key=lambda $pair: $pair[1])]"],
  [({"a": 3, "b": 1, "c": 2},), ({},)])

F("pluck", "dicts", "pluck get_field column_values", "rows:RECORDS, field:FIELD",
  ["Return the value of $field from every dictionary in $rows."],
  ["return [$row[$field] for $row in $rows]",
   r"""
   $out = []
   for $row in $rows:
       $out.append($row[$field])
   return $out
   """],
  [([{"n": 1}, {"n": 2}], "n"), ([], "x")])

F("filter_records", "dicts", "filter_records select_where find_matching", "rows:RECORDS, field/value:FIELDVAL",
  ["Return the dictionaries in $rows whose $field equals $value."],
  ["return [$row for $row in $rows if $row.get($field) == $value]",
   r"""
   $out = []
   for $row in $rows:
       if $row.get($field) == $value:
           $out.append($row)
   return $out
   """],
  [([{"n": 1}, {"n": 2}, {}], "n", 2), ([], "x", 1)])

F("group_by_first_letter", "dicts", "group_by_first_letter index_by_letter", "words:WORDS",
  ["Group the non-empty strings in $words into a dictionary keyed by their first letter."],
  [r"""
   $groups = {}
   for $w in $words:
       $groups.setdefault($w[0], []).append($w)
   return $groups
   """,
   r"""
   $groups = {}
   for $w in $words:
       if $w[0] not in $groups:
           $groups[$w[0]] = []
       $groups[$w[0]].append($w)
   return $groups
   """],
  [(["apple", "bob", "avocado"],), ([],)])

F("nested_get", "dicts", "nested_get deep_get get_nested", "d:DICT, k1/k2:KEY2",
  ["Return $d[$k1][$k2], or None if either key is missing."],
  [r"""
   if $k1 not in $d:
       return None
   $inner = $d[$k1]
   if $k2 not in $inner:
       return None
   return $inner[$k2]
   """,
   r"""
   try:
       return $d[$k1][$k2]
   except KeyError:
       return None
   """,
   "return $d.get($k1, {}).get($k2)"],
  [({"a": {"b": 1}}, "a", "b"), ({"a": {}}, "a", "b"), ({}, "x", "y")])

F("sorted_items", "dicts", "sorted_items items_sorted ordered_pairs", "d:DICT",
  ["Return the (key, value) pairs of $d as a list sorted by key."],
  ["return sorted($d.items())", "return [($k, $d[$k]) for $k in sorted($d)]"],
  [({"b": 2, "a": 1},), ({},)])

F("apply_discount", "dicts", "apply_discount discount_prices", "d:NUMDICT, pct:PCT",
  ["Return a new dictionary with every value in $d reduced by $pct percent."],
  ["return {$k: $v * (1 - $pct / 100) for $k, $v in $d.items()}",
   r"""
   $out = {}
   for $k, $v in $d.items():
       $out[$k] = $v * (1 - $pct / 100)
   return $out
   """],
  [({"a": 100, "b": 50}, 10), ({}, 5)])

F("in_stock", "dicts", "in_stock is_available has_stock", "d:NUMDICT, k:KEY",
  ["Return True if $k is in $d with a count above zero."],
  ["return $d.get($k, 0) > 0", "return $k in $d and $d[$k] > 0"],
  [({"a": 2, "b": 0}, "a"), ({"a": 2, "b": 0}, "b"), ({}, "c")])

F("without_key", "dicts", "without_key remove_key drop_key", "d:DICT, k:KEY",
  ["Return a copy of $d without the key $k."],
  ["return {$key: $val for $key, $val in $d.items() if $key != $k}",
   "$out = dict($d)\n$out.pop($k, None)\nreturn $out"],
  [({"a": 1, "b": 2}, "a"), ({}, "x")])

F("with_key", "dicts", "with_key set_key updated_copy", "d:DICT, k:KEY, v:TARGET",
  ["Return a copy of $d with $k set to $v, leaving $d unchanged."],
  ["$out = dict($d)\n$out[$k] = $v\nreturn $out",
   "$out = $d.copy()\n$out[$k] = $v\nreturn $out"],
  [({"a": 1}, "b", 2), ({"a": 1}, "a", 5)])

F("count_keys_above", "dicts", "count_keys_above count_large_values", "d:NUMDICT, limit:LIMIT",
  ["Return how many values in $d are greater than $limit."],
  ["return sum(1 for $v in $d.values() if $v > $limit)",
   r"""
   $count = 0
   for $v in $d.values():
       if $v > $limit:
           $count += 1
   return $count
   """],
  [({"a": 1, "b": 5}, 2), ({}, 0)])

F("dict_keys_sorted", "dicts", "sorted_keys keys_in_order", "d:DICT",
  ["Return the keys of $d as a sorted list."],
  ["return sorted($d)", "return sorted($d.keys())", "$out = list($d)\n$out.sort()\nreturn $out"],
  [({"b": 1, "a": 2},), ({},)])

# ==========================================================================
# Classes
# ==========================================================================

C("stack_class", "Stack ItemStack Pile",
  ["Create a class $fn with push, pop, peek, and is_empty methods that behave like a stack."],
  [r"""
   class $fn:
       def __init__(self):
           self.$attr = []

       def push(self, $x):
           self.$attr.append($x)

       def pop(self):
           return self.$attr.pop()

       def peek(self):
           return self.$attr[-1]

       def is_empty(self):
           return len(self.$attr) == 0
   """,
   r"""
   class $fn:
       def __init__(self):
           self.$attr = []

       def push(self, $x):
           self.$attr.append($x)

       def pop(self):
           if not self.$attr:
               raise IndexError("pop from empty stack")
           return self.$attr.pop()

       def peek(self):
           return self.$attr[-1] if self.$attr else None

       def is_empty(self):
           return not self.$attr
   """])

C("queue_class", "Queue LineQueue WaitingLine",
  ["Create a class $fn with enqueue, dequeue, and size methods that behave like a first-in, first-out queue."],
  [r"""
   class $fn:
       def __init__(self):
           self.$attr = []

       def enqueue(self, $x):
           self.$attr.append($x)

       def dequeue(self):
           return self.$attr.pop(0)

       def size(self):
           return len(self.$attr)
   """])

C("counter_class", "Counter ClickCounter Tally",
  ["Create a class $fn that starts at zero and has increment, reset, and get methods."],
  [r"""
   class $fn:
       def __init__(self):
           self.$num_attr = 0

       def increment(self):
           self.$num_attr += 1

       def reset(self):
           self.$num_attr = 0

       def get(self):
           return self.$num_attr
   """,
   r"""
   class $fn:
       def __init__(self, start=0):
           self.$num_attr = start

       def increment(self, step=1):
           self.$num_attr += step
           return self.$num_attr

       def reset(self):
           self.$num_attr = 0

       def get(self):
           return self.$num_attr
   """])

C("account_class", "BankAccount Account Wallet",
  ["Create a class $fn with deposit and withdraw methods that track a balance and refuse to overdraw."],
  [r"""
   class $fn:
       def __init__(self, balance=0):
           self.balance = balance

       def deposit(self, amount):
           if amount <= 0:
               raise ValueError("amount must be positive")
           self.balance += amount

       def withdraw(self, amount):
           if amount > self.balance:
               raise ValueError("insufficient funds")
           self.balance -= amount
   """,
   r"""
   class $fn:
       def __init__(self):
           self.balance = 0

       def deposit(self, amount):
           self.balance += amount
           return self.balance

       def withdraw(self, amount):
           if amount > self.balance:
               return False
           self.balance -= amount
           return True
   """])

C("rectangle_class", "Rectangle Rect Box",
  ["Create a class $fn that stores a width and height and has area and perimeter methods."],
  [r"""
   class $fn:
       def __init__(self, width, height):
           self.width = width
           self.height = height

       def area(self):
           return self.width * self.height

       def perimeter(self):
           return 2 * (self.width + self.height)
   """,
   r"""
   class $fn:
       def __init__(self, width, height):
           self.width = width
           self.height = height

       def area(self):
           return self.width * self.height

       def perimeter(self):
           return 2 * self.width + 2 * self.height

       def is_square(self):
           return self.width == self.height
   """])

C("point_class", "Point Vector2 Position",
  ["Create a class $fn with x and y attributes, a move method, and a distance_to method."],
  [r"""
   class $fn:
       def __init__(self, x, y):
           self.x = x
           self.y = y

       def move(self, dx, dy):
           self.x += dx
           self.y += dy

       def distance_to(self, other):
           return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
   """])

C("todo_class", "TodoList Checklist TaskList",
  ["Create a class $fn that can add items, remove items, and report how many items it holds."],
  [r"""
   class $fn:
       def __init__(self):
           self.$attr = []

       def add(self, $x):
           self.$attr.append($x)

       def remove(self, $x):
           if $x in self.$attr:
               self.$attr.remove($x)

       def count(self):
           return len(self.$attr)
   """])
