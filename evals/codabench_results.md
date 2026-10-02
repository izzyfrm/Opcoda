# CodaBench 0.2 results

- checkpoint: `checkpoints/coda-phase3-best.pt` (step 650)
- sampling: temperature 0.2, top-k 10, max 256 tokens, seed 2026, samples 5
- syntax validity is not functional correctness

| format | syntax (sample 1) | syntax (mean of 5) | functional (sample 1) | functional (mean of 5) |
|---|---|---|---|---|
| instruct | 6/12 | 7.00/12 | 0/12 | 0.00/12 |
| comment | 9/12 | 7.40/12 | 0/12 | 0.00/12 |

## Format: instruct

### is_palindrome — syntax FAIL

`invalid syntax (line 2)`

```python
def is_palindrome(text):
    return "".join(text) for token in text.startswith(terms)
```

### average — syntax PASS — tests 0/4 (failed)

`ok`

```python
def average(values):
    return [value for value in values if value > 0]
```

### count_words — syntax FAIL

`unterminated string literal (detected at line 2) (line 2)`

```python
def count_words(text):
    return steps * " * len(sten)
```

### merge_dicts — syntax FAIL

`invalid syntax (line 2)`

```python
def merge_dicts(left, right):
    return [widx for idx in range(left) idx != wanted]
```

### rotate_left — syntax PASS — tests 1/3 (failed)

`ok`

```python
def rotate_left(values):
    return [label for label, value in enumerate(values) if value >= 0]
```

### is_prime — syntax PASS — tests 0/6 (failed)

`ok`

```python
def is_prime(number):
    return line == 0
```

### gcd — syntax FAIL

`'in' expected after for-loop variables (line 2)`

```python
def gcd(a, b):
    return [column for curr if curr is if c != b.cupper()]
```

### flatten_one — syntax PASS — tests 1/3 (failed)

`ok`

```python
def flatten_one(groups):
    return sorted(groups)
```

### common_items — syntax FAIL

`'[' was never closed (line 2)`

```python
def common_items(left, right):
    return [record freq[record in freq]
```

### to_snake_case — syntax PASS — tests 1/3 (failed)

`ok`

```python
def to_snake_case(text):
    collected = ""
    for symbol in text:
        if symbol.lower() not in "aeiou":
            collected += symbol
    return collected
```

### second_largest — syntax PASS — tests 0/5 (failed)

`ok`

```python
def second_largest(values):
    return sorted(values, other)
```

### group_by_length — syntax FAIL

`closing parenthesis ')' does not match opening parenthesis '{' (line 2)`

```python
def group_by_length(words):
    return {key: value for key, value in words if key is missing.items() if key== 1)
```

## Format: comment

### is_palindrome — syntax PASS — tests 0/5 (failed)

`ok`

```python
def is_palindrome(text):
    return "".join(tokens)
```

### average — syntax PASS — tests 0/4 (failed)

`ok`

```python
def average(values):
    return [value for value in values]
```

### count_words — syntax PASS — tests 0/3 (failed)

`ok`

```python
def count_words(text):
    for token in text.starts():
        if token[token] == target:
            token[token]
    return token[token[0]]
```

### merge_dicts — syntax FAIL

`invalid syntax (line 2)`

```python
def merge_dicts(left, right):
    return [record for record in record.get() if record is if record is None or v > record]
```

### rotate_left — syntax PASS — tests 1/3 (failed)

`ok`

```python
def rotate_left(values):
    return [elem for elem, value in values]
```

### is_prime — syntax FAIL

`'(' was never closed (line 2)`

```python
def is_prime(number):
    return list(number * 2 for number in number, number in zip(number, number, inclusive.isdigit())
```

### gcd — syntax PASS — tests 0/4 (failed)

`ok`

```python
def gcd(a, b):
    return [col]
```

### flatten_one — syntax PASS — tests 1/3 (failed)

`ok`

```python
def flatten_one(groups):
    return sorted(groups)
```

### common_items — syntax PASS — tests 0/3 (failed)

`ok`

```python
def common_items(left, right):
    return [record for record in range(min(left), right)]
```

### to_snake_case — syntax PASS — tests 1/3 (failed)

`ok`

```python
def to_snake_case(text):
    collected = ""
    for symbol in text:
        if symbol.lower() not in "aeiou":
            collected += symbol
    return collected
```

### second_largest — syntax PASS — tests 0/5 (failed)

`ok`

```python
def second_largest(values):
    return sorted(values)
```

### group_by_length — syntax FAIL

`closing parenthesis ')' does not match opening parenthesis '{' (line 2)`

```python
def group_by_length(words):
    return {key: v for key, v in word.items() if key== 0)
```
