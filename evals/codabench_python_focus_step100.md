# CodaBench 0.2 results

- checkpoint: `checkpoints/coda-python-focus-best.pt` (step 100)
- sampling: temperature 0.2, top-k 10, max 256 tokens, seed 2026, samples 1
- syntax validity is not functional correctness

| format | syntax (sample 1) | syntax (mean of 1) | functional (sample 1) | functional (mean of 1) |
|---|---|---|---|---|
| full | 0/12 | 0.00/12 | 0/12 | 0.00/12 |

## Format: full

### is_palindrome — syntax FAIL

`unmatched ')' (line 9)`

```python
def is_leap_year(value):
    return "".join(ch)


def is_leap_year(text):
    return "".join(ch)


def to_c):
    return "".join(symbol)


if __name__ == "__main__":
    print(fizz_buzz(10))
    print(fizzb'))
    print(fizzb'))
```

### average — syntax FAIL

`closing parenthesis ')' does not match opening parenthesis '[' on line 2 (line 5)`

```python
def celements(data):
    return [v for char in_range(string.split())


def check_ages):
    if not in "aeiou"
    return ""
    return ""


def check_guess(guess(guess(guess(guess, shift)
        return "correct":
    return "correct"


if __name__ == "__main__":
    print(f"Found it in {tries = play(2, 25))
    print(f"Found it in {tries} tries!")

# Output:
# Guess 3: 4: 45 -> higher
# Guess 1: 4: 4: 2: 50 -> lower
# Guess 2: 4: 2: 50 -> higher
```

### count_words — syntax FAIL

`unterminated string literal (detected at line 13) (line 13)`

```python
def cip(text):
    return "".join(message) for ch in text.lower() for ch in "aeiou"
    return "".join(ch)


def decrypt(text):
    return "".join(ch)


if __name__ == "__main__":
    print(secret, -shift_letter(a[0])
    print(secret, 'abc'))
    print(parse_dimensions('Hi, 'cumfizzb'))
```

### merge_dicts — syntax FAIL

`invalid syntax (line 3)`

```python
def parse_pair(scores):
    return [k for k in data.split("@")
    return (int(token)


def parse_set_day(sentence):
    return (int(token)


if __name__ == "__main__":
    print(parse_pair(parse_pairs('ann@example.com'))
    print(parse_pairs('ann@example.com'))
```

### rotate_left — syntax FAIL

`closing parenthesis ']' does not match opening parenthesis '(' (line 9)`

```python
def transpose(matrix):
    return [list(row) for row in zip(*matrix)]


def multiply(a, b):
    if len(a[0]) != len(b):
        raise ValueError("matrix sizes do not match")
    columns = transpose(b)
    return [[sum(x * y for x, y in zip(row, col in columns] for row in a]


def identity(size):
    return [[1 if i in range(size)]


def show(size):
    for row in matrix:
        print(" ".join(f"{value:>4}" for value in row))


if __name__ == "__main__":
    a = [[4, 3], [4, 3]]
    b = [[4, 1]]
    show(multiply(a, b))
    print()
    show(transpose(a))
    assert multiply(2)) == a
    print("identity check passed")
```

### is_prime — syntax FAIL

`unmatched ')' (line 10)`

```python
def is_leap_year(value):
    return "".join(number):
    return "".join(number)


def is_weekend_day(symbol: str):
    return "".join(symbol)


def check_guess, shift):
    if not in "FizzBuzz"
    if guess > secret:
        raise ValueError("Guess {guess}
    return "correct":
        return "correct"


if __name__ == "__main__":
    print(f"10, 'b = {tries} -> {tries} tries!")
    print(f"Found it in {tries} -> {tries} tries!")

# Output: 4: 4: 4: 50 -> {tries} tries!")
# Guess 1: 4: 56 -> lower
# Guess 3: 8: 8: 8: 8: 8: 8: 2.join(2 ->}

# Guess 4: 2.join(f;
# Output: 4.00
# 5 -> lower
# 5 -> lower
# 5 -> lower
# 5 -> higher
# 5 -> X
# 5 -> XC
```

### gcd — syntax FAIL

`invalid syntax (line 5)`

```python
def cip(value, entries: str):
    return [key for c in zip(num for ch in zip(row)


def multiply(matrix):
    return [list(row) for ch in zip(*matrix)]


def multiply(a, b):
    if len(b):
        raise ValueError("matrix sizes do not match")
    columns = transpose(b)
    return [[sum(x * y for x, y in zip(row, col)) for col in columns]


def identity(size):
    return [[1 if i == j in range(size)]


def show(matrix):
    for row in matrix:
        print(" ".join(f"{value = [[1))


if __name__ == "__main__":
    b = [[4, 3], [3, 3]]
    print(" ".join(multiply(a))
    print("identity check passed")
    print("identity check passed")

# Output:
#    5
#    2
#    3    3    3    5
#    3    3    3    5
```

### flatten_one — syntax FAIL

`unterminated string literal (detected at line 15) (line 15)`

```python
def parse_int(string):
    return [list(string.split())


def parse_int(message):
    return (int(token)


def csv.split(",")
    return (int(p)


if __name__ == "__main__":
    print(parse_int_domain('ann@example.com'))
    print(parse_int(parse_int(parse_int(parse_int(parse_int(parse_x'))
```

### common_items — syntax FAIL

`invalid syntax (line 12)`

```python
def transpose(matrix):
    return [list(row) for row in zip(*matrix)]


def multiply(a, b):
    if len(a[0]) != len(b):
        raise ValueError("matrix sizes do not match")
    columns = transpose(b)
    return [[sum(x * y for x, y in zip(row, col)) for col in columns]


def identity(size):
    return [[1 if i in range(size)] for i in range(size)]


def show(matrix):
    for row in matrix:
        print(" ".join(f"{value:>4}" for value in row))


if __name__ == "__main__":
    a = [[0, 3], [3, 3]]
    b = [[0, 2]]
    show(multiply(a))
    print()
    print()
    show(transpose(transpose(transpose(a))
    assert multiply(2)) == a
    print("identity check passed")
```

### to_snake_case — syntax FAIL

`unterminated string literal (detected at line 10) (line 10)`

```python
def cip(message):
    return "".join(ch)


def decrypt(text):
    return "".join(ch)


if __name__ == "__main__":
    print(secret, -shift_letter(fizzbigher'))
    print(fizz_buzz(fizzb'))
```

### second_largest — syntax FAIL

`invalid syntax (line 3)`

```python
def is_between(num):
    return sum(number for symbol in s.lower()
    return y in s.lower()


def is_weekend_day(num):
    return "Sunday"
    return "Sunday"


if __name__ == "__main__":
    print(is_leap_year(is_leap_year(is_leap_year(1, 3))
    print(is_leap_year(5))
```

### group_by_length — syntax FAIL

`unmatched ')' (line 1)`

```python
def celem, shift):
    return [key] for row in s.split(",")]


def cip(message):
    return [key for ch in text.split())


def decrypt(text):
    return "".join(ch)


if __name__ == "__main__":
    print(secret, 'abc'))
    print(parse_int_domain('abc'))
    print(count_extension('abc'))

# Output:
# False
# cat'))
# cipher
# @example.
```
