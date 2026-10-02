"""Longer Python programs for Coda's Phase 4 curriculum.

Every program here is complete and runnable (no input(), no files, no network): classes
with several methods, small apps, algorithms with self-checks. tools/make_code_curriculum.py
executes each generated program (these are our own templates, not model output) and
discards anything that raises; it can also append the real printed output as comments.
"""
from __future__ import annotations

import random as _random
from dataclasses import dataclass
from random import Random
from typing import Callable


@dataclass(frozen=True)
class Program:
    key: str
    topic: str
    make: Callable[[Random], tuple[str, str]]


PROGRAMS: list[Program] = []


def program(key: str, topic: str):
    def register(fn):
        PROGRAMS.append(Program(key, topic, fn))
        return fn
    return register


PEOPLE = ["Ada", "Grace", "Linus", "Margaret", "Alan", "Barbara", "Dennis", "Frances", "Ken", "Radia", "Tim", "Katherine"]
ITEMS = [("apples", 0.5), ("bread", 3.25), ("coffee", 8.99), ("eggs", 4.2), ("milk", 2.75), ("rice", 6.4), ("tea", 5.5),
         ("pasta", 1.99), ("cheese", 7.8), ("bananas", 0.3)]


def maybe_doc(rng: Random, text: str, indent: str = "    ") -> str:
    return f'{indent}"""{text}"""\n' if rng.random() < 0.35 else ""


@program("bank_account", "classes")
def bank_account(rng: Random) -> tuple[str, str]:
    cls = rng.choice(["BankAccount", "Account", "Wallet", "SavingsAccount"])
    owner = rng.choice(PEOPLE)
    start = rng.choice([0, 50, 100, 250])
    history = rng.random() < 0.6
    raise_errors = rng.random() < 0.6
    deposits = rng.sample([20, 40, 75, 120, 200, 300], 2)
    withdraw_ok = rng.choice([10, 30, 60])
    withdraw_bad = 10_000
    hist_init = "\n        self.history = []" if history else ""
    hist_dep = '\n        self.history.append(("deposit", amount))' if history else ""
    hist_wd = '\n        self.history.append(("withdraw", amount))' if history else ""
    if raise_errors:
        wd_check = '        if amount > self.balance:\n            raise ValueError("insufficient funds")\n'
        wd_ret = ""
        demo_bad = f"""try:
    account.withdraw({withdraw_bad})
except ValueError as error:
    print("Error:", error)"""
    else:
        wd_check = "        if amount > self.balance:\n            return False\n"
        wd_ret = "\n        return True"
        demo_bad = f'print("Large withdrawal allowed?", account.withdraw({withdraw_bad}))'
    statement = """

    def statement(self):
        for kind, amount in self.history:
            sign = "+" if kind == "deposit" else "-"
            print(f"{sign}{amount:>8.2f}  {kind}")
        print(f"Balance: {self.balance:.2f}")""" if history else ""
    code = f"""class {cls}:
{maybe_doc(rng, "A simple bank account with deposits and withdrawals.")}    def __init__(self, owner, balance={start}):
        self.owner = owner
        self.balance = balance{hist_init}

    def deposit(self, amount):
        if amount <= 0:
            raise ValueError("deposit must be positive")
        self.balance += amount{hist_dep}

    def withdraw(self, amount):
        if amount <= 0:
            raise ValueError("withdrawal must be positive")
{wd_check}        self.balance -= amount{hist_wd}{wd_ret}{statement}


if __name__ == "__main__":
    account = {cls}("{owner}")
    account.deposit({deposits[0]})
    account.deposit({deposits[1]})
    account.withdraw({withdraw_ok})
    {demo_bad.replace(chr(10), chr(10) + "    ")}
    {"account.statement()" if history else 'print(f"{account.owner} has {account.balance:.2f}")'}
"""
    task = rng.choice([f"Write a Python {cls} class with deposit and withdraw methods" + (" and a transaction history" if history else "") +
                       (". Raise an error when there are not enough funds." if raise_errors else ". Withdraw should return False when there are not enough funds."),
                       "Python bank account class with deposit, withdraw and balance.",
                       f"Create a {cls} class in Python and show how to use it."])
    return task, code


@program("inventory", "classes")
def inventory(rng: Random) -> tuple[str, str]:
    cls = rng.choice(["Inventory", "Stockroom", "Warehouse"])
    stock = rng.sample(["widgets", "bolts", "screws", "cables", "batteries", "fuses", "gaskets", "valves"], 4)
    threshold = rng.choice([3, 5, 10])
    adds = "\n".join(f'    store.add("{s}", {rng.randint(1, 20)})' for s in stock)
    code = f"""class {cls}:
{maybe_doc(rng, "Track item quantities.")}    def __init__(self):
        self.items = {{}}

    def add(self, name, quantity):
        if quantity <= 0:
            raise ValueError("quantity must be positive")
        self.items[name] = self.items.get(name, 0) + quantity

    def remove(self, name, quantity):
        available = self.items.get(name, 0)
        if quantity > available:
            raise ValueError(f"only {{available}} {{name}} left")
        self.items[name] = available - quantity
        if self.items[name] == 0:
            del self.items[name]

    def low_stock(self, threshold={threshold}):
        return sorted(name for name, qty in self.items.items() if qty < threshold)

    def report(self):
        for name in sorted(self.items):
            print(f"{{name:<12}}{{self.items[name]:>4}}")


if __name__ == "__main__":
    store = {cls}()
{adds}
    store.remove("{stock[0]}", 1)
    store.report()
    print("Low stock:", store.low_stock())
"""
    task = rng.choice([f"Write a Python {cls} class that can add and remove items, list low-stock items (under {threshold}) and print a report.",
                       "Python inventory management class with add, remove and report methods."])
    return task, code


@program("task_list", "classes")
def task_list(rng: Random) -> tuple[str, str]:
    cls = rng.choice(["TaskList", "TodoList", "TaskManager"])
    tasks = rng.sample(["Buy groceries", "Write report", "Call the bank", "Clean the kitchen", "Fix the bike", "Plan the trip", "Read a chapter"], 4)
    with_priority = rng.random() < 0.6
    if with_priority:
        add_sig, field_line, item = "def add(self, title, priority=2):", '{"id": self.next_id, "title": title, "priority": priority, "done": False}', \
            "sorted((t for t in self.tasks if not t[\"done\"]), key=lambda t: t[\"priority\"])"
        adds = "\n".join(f'    todo.add("{t}", priority={rng.randint(1, 3)})' for t in tasks)
    else:
        add_sig, field_line, item = "def add(self, title):", '{"id": self.next_id, "title": title, "done": False}', \
            "[t for t in self.tasks if not t[\"done\"]]"
        adds = "\n".join(f'    todo.add("{t}")' for t in tasks)
    code = f"""class {cls}:
{maybe_doc(rng, "Keep track of tasks and mark them done.")}    def __init__(self):
        self.tasks = []
        self.next_id = 1

    {add_sig}
        task = {field_line}
        self.tasks.append(task)
        self.next_id += 1
        return task["id"]

    def complete(self, task_id):
        for task in self.tasks:
            if task["id"] == task_id:
                task["done"] = True
                return True
        return False

    def pending(self):
        return {item}

    def summary(self):
        done = sum(1 for t in self.tasks if t["done"])
        return f"{{done}}/{{len(self.tasks)}} tasks done"


if __name__ == "__main__":
    todo = {cls}()
{adds}
    todo.complete(2)
    for task in todo.pending():
        print("-", task["title"])
    print(todo.summary())
"""
    task = rng.choice([f"Write a Python {cls} class to add tasks" + (" with priorities" if with_priority else "") + ", mark them complete, list pending tasks and show a summary.",
                       "Simple to-do list manager in Python."])
    return task, code


@program("shopping_cart", "classes")
def shopping_cart(rng: Random) -> tuple[str, str]:
    items = rng.sample(ITEMS, 4)
    tax = rng.choice([0, 0.05, 0.08, 0.1])
    codes = rng.choice([{"SAVE10": 10}, {"WELCOME": 15}, {"HALF": 50, "SAVE5": 5}])
    code_name = list(codes)[0]
    adds = "\n".join(f'    cart.add("{n}", {p}, {rng.randint(1, 4)})' for n, p in items)
    tax_line = f"\n    TAX_RATE = {tax}" if tax else ""
    total_body = ("        subtotal = self.subtotal() * (1 - self.discount / 100)\n        return round(subtotal * (1 + self.TAX_RATE), 2)"
                  if tax else "        return round(self.subtotal() * (1 - self.discount / 100), 2)")
    code = f"""from dataclasses import dataclass


@dataclass
class Item:
    name: str
    price: float
    quantity: int = 1


class Cart:
    CODES = {codes!r}{tax_line}

    def __init__(self):
        self.items = {{}}
        self.discount = 0

    def add(self, name, price, quantity=1):
        if name in self.items:
            self.items[name].quantity += quantity
        else:
            self.items[name] = Item(name, price, quantity)

    def remove(self, name):
        self.items.pop(name, None)

    def apply_code(self, code):
        if code not in self.CODES:
            return False
        self.discount = self.CODES[code]
        return True

    def subtotal(self):
        return sum(item.price * item.quantity for item in self.items.values())

    def total(self):
{total_body}


if __name__ == "__main__":
    cart = Cart()
{adds}
    cart.remove("{items[1][0]}")
    print("Code accepted:", cart.apply_code("{code_name}"))
    print(f"Subtotal: ${{cart.subtotal():.2f}}")
    print(f"Total: ${{cart.total():.2f}}")
"""
    task = rng.choice(["Write a shopping cart in Python with items, quantities, discount codes" + (f" and {int(tax * 100)}% tax." if tax else "."),
                       "Python Cart class using a dataclass for items, with subtotal and total."])
    return task, code


@program("gradebook", "data")
def gradebook(rng: Random) -> tuple[str, str]:
    students = rng.sample(PEOPLE, 4)
    scores = {s: [rng.randint(55, 100) for _ in range(3)] for s in students}
    passing = rng.choice([60, 65, 70])
    code = f"""SCORES = {{
{chr(10).join(f'    "{s}": {v},' for s, v in scores.items())}
}}


def letter_grade(score):
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def final_score(scores):
    return round(sum(scores) / len(scores), 1)


def report(gradebook, passing={passing}):
    results = {{name: final_score(scores) for name, scores in gradebook.items()}}
    for name, score in sorted(results.items(), key=lambda item: item[1], reverse=True):
        status = "pass" if score >= passing else "fail"
        print(f"{{name:<10}} {{score:>5}}  {{letter_grade(score)}}  {{status}}")
    best = max(results, key=results.get)
    print(f"Top student: {{best}} ({{results[best]}})")


if __name__ == "__main__":
    report(SCORES)
"""
    task = rng.choice([f"Write a Python grade report: each student has three scores; show each final score, letter grade and pass/fail (pass is {passing}), sorted from highest, plus the top student.",
                       "Python gradebook program with letter grades."])
    return task, code


@program("library", "classes")
def library(rng: Random) -> tuple[str, str]:
    books = rng.sample([("Dune", "Frank Herbert"), ("Emma", "Jane Austen"), ("Beloved", "Toni Morrison"), ("Hamlet", "William Shakespeare"),
                        ("Ulysses", "James Joyce"), ("Matilda", "Roald Dahl"), ("Persuasion", "Jane Austen"), ("Ivanhoe", "Walter Scott")], 4)
    member = rng.choice(PEOPLE)
    adds = "\n".join(f'    library.add(Book("{t}", "{a}"))' for t, a in books)
    code = f"""from dataclasses import dataclass


@dataclass
class Book:
    title: str
    author: str
    borrower: str | None = None


class Library:
    def __init__(self):
        self.books = {{}}

    def add(self, book):
        self.books[book.title.lower()] = book

    def checkout(self, title, member):
        book = self.books.get(title.lower())
        if book is None:
            raise KeyError(f"no book called {{title!r}}")
        if book.borrower:
            return False
        book.borrower = member
        return True

    def return_book(self, title):
        book = self.books.get(title.lower())
        if book and book.borrower:
            book.borrower = None
            return True
        return False

    def available(self):
        return sorted(b.title for b in self.books.values() if b.borrower is None)


if __name__ == "__main__":
    library = Library()
{adds}
    print(library.checkout("{books[0][0]}", "{member}"))
    print(library.checkout("{books[0][0]}", "Someone else"))
    print("Available:", library.available())
    library.return_book("{books[0][0]}")
    print("Available:", library.available())
"""
    task = rng.choice(["Write a small library system in Python: add books, check out, return, and list available books.",
                       "Python Library and Book classes with checkout and return."])
    return task, code


@program("contact_book", "classes")
def contact_book(rng: Random) -> tuple[str, str]:
    people = rng.sample(PEOPLE, 4)
    adds = "\n".join(f'    book.add("{p} {rng.choice(["Lovelace", "Hopper", "Turing", "Ritchie", "Allen", "Perlman", "Berners-Lee"])}", "555-{rng.randint(1000, 9999)}")' for p in people)
    code = f"""class ContactBook:
{maybe_doc(rng, "Store names and phone numbers.")}    def __init__(self):
        self.contacts = {{}}

    def add(self, name, phone):
        self.contacts[name] = phone

    def remove(self, name):
        return self.contacts.pop(name, None) is not None

    def search(self, text):
        text = text.lower()
        return {{name: phone for name, phone in self.contacts.items() if text in name.lower()}}

    def show(self):
        for name in sorted(self.contacts):
            print(f"{{name:<24}}{{self.contacts[name]}}")


if __name__ == "__main__":
    book = ContactBook()
{adds}
    print(book.search("{people[0][:2].lower()}"))
    book.remove(next(iter(book.contacts)))
    book.show()
"""
    task = rng.choice(["Write a ContactBook class in Python to add, remove, search (case-insensitive) and print contacts.", "python phone book program"])
    return task, code


@program("text_stats", "strings")
def text_stats(rng: Random) -> tuple[str, str]:
    text = rng.choice([
        "The quick brown fox jumps over the lazy dog. The dog sleeps. A fox runs fast!",
        "Python is fun. Python is readable. Write code, test code, and ship code.",
        "Rain fell all day. The streets were quiet. By night the rain had stopped and the stars came out.",
        "Good tests catch bugs early. Good names make code clear. Good habits add up.",
    ])
    top = rng.choice([3, 5])
    code = f"""import re
from collections import Counter

TEXT = "{text}"


def words(text):
    return re.findall(r"[a-z']+", text.lower())


def word_frequencies(text):
    return Counter(words(text))


def top_words(text, n={top}):
    return word_frequencies(text).most_common(n)


def sentence_total(text):
    return len([s for s in re.split(r"[.!?]+", text) if s.strip()])


def longest_word(text):
    return max(words(text), key=len)


if __name__ == "__main__":
    print("Sentences:", sentence_total(TEXT))
    print("Longest word:", longest_word(TEXT))
    for word, count in top_words(TEXT):
        print(f"{{word:<10}}{{count}}")
"""
    task = rng.choice([f"Write a Python text analyzer that reports how many sentences a text has, its longest word, and the top {top} most frequent words.",
                       "Python program for text statistics using collections.Counter."])
    return task, code


@program("tic_tac_toe", "games")
def tic_tac_toe(rng: Random) -> tuple[str, str]:
    boards = rng.sample([["X", "X", "X", "O", "O", " ", " ", " ", " "], ["O", "X", "X", "O", "X", " ", "O", " ", " "],
                         ["X", "O", "X", "O", "X", "O", "O", "X", "O"], ["X", "O", " ", " ", "X", "O", " ", " ", "X"],
                         ["O", "O", "X", "X", "X", "O", "O", "X", "X"]], 3)
    code = f"""LINES = [
    (0, 1, 2), (3, 4, 5), (6, 7, 8),
    (0, 3, 6), (1, 4, 7), (2, 5, 8),
    (0, 4, 8), (2, 4, 6),
]


def winner(board):
    for a, b, c in LINES:
        if board[a] != " " and board[a] == board[b] == board[c]:
            return board[a]
    if " " not in board:
        return "draw"
    return None


def show(board):
    rows = [board[i:i + 3] for i in range(0, 9, 3)]
    print("\\n---------\\n".join(" | ".join(row) for row in rows))


if __name__ == "__main__":
    boards = {boards!r}
    for board in boards:
        show(board)
        print("Result:", winner(board) or "still playing")
        print()
"""
    task = rng.choice(["Write a Python function that checks a tic-tac-toe board for a winner or a draw, and print a few example boards.",
                       "tic tac toe winner checker in python"])
    return task, code


@program("matrix_utils", "math")
def matrix_utils(rng: Random) -> tuple[str, str]:
    a = [[rng.randint(1, 5) for _ in range(2)] for _ in range(2)]
    b = [[rng.randint(0, 4) for _ in range(2)] for _ in range(2)]
    code = f"""def transpose(matrix):
    return [list(row) for row in zip(*matrix)]


def multiply(a, b):
    if len(a[0]) != len(b):
        raise ValueError("matrix sizes do not match")
    columns = transpose(b)
    return [[sum(x * y for x, y in zip(row, col)) for col in columns] for row in a]


def identity(size):
    return [[1 if i == j else 0 for j in range(size)] for i in range(size)]


def show(matrix):
    for row in matrix:
        print(" ".join(f"{{value:>4}}" for value in row))


if __name__ == "__main__":
    a = {a}
    b = {b}
    show(multiply(a, b))
    print()
    show(transpose(a))
    assert multiply(a, identity(2)) == a
    print("identity check passed")
"""
    task = rng.choice(["Write Python functions to transpose and multiply matrices (lists of lists), build an identity matrix and print them.",
                       "matrix multiplication in python without numpy"])
    return task, code


@program("roman_numerals", "algorithms")
def roman_numerals(rng: Random) -> tuple[str, str]:
    samples = rng.sample([1, 4, 9, 14, 40, 90, 400, 1994, 2024, 3999, 58, 621], 4)
    code = f"""NUMERALS = [
    (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
    (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
    (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
]


def to_roman(number):
    if not 0 < number < 4000:
        raise ValueError("number must be between 1 and 3999")
    result = []
    for value, symbol in NUMERALS:
        while number >= value:
            result.append(symbol)
            number -= value
    return "".join(result)


def from_roman(text):
    values = {{symbol: value for value, symbol in NUMERALS if len(symbol) == 1}}
    total = 0
    for i, ch in enumerate(text):
        value = values[ch]
        if i + 1 < len(text) and values[text[i + 1]] > value:
            total -= value
        else:
            total += value
    return total


if __name__ == "__main__":
    for n in {samples}:
        roman = to_roman(n)
        print(n, "->", roman)
        assert from_roman(roman) == n
    print("round trip OK")
"""
    task = rng.choice(["Write Python functions to convert integers to Roman numerals and back, and test a round trip.",
                       "roman numeral converter in python"])
    return task, code


@program("bracket_checker", "algorithms")
def bracket_checker(rng: Random) -> tuple[str, str]:
    tests = rng.sample([("()[]{}", True), ("([)]", False), ("{[()]}", True), ("((", False), ("", True), ("f(a[0]) + {b}", True), ("]", False)], 5)
    code = f"""PAIRS = {{")": "(", "]": "[", "}}": "{{"}}


def is_balanced(text):
    stack = []
    for ch in text:
        if ch in "([{{":
            stack.append(ch)
        elif ch in PAIRS:
            if not stack or stack.pop() != PAIRS[ch]:
                return False
    return not stack


if __name__ == "__main__":
    tests = {tests!r}
    for text, expected in tests:
        result = is_balanced(text)
        print(f"{{text!r:<16}} {{result}}")
        assert result == expected
"""
    task = rng.choice(["Write a Python function that checks whether brackets (), [] and {} are balanced using a stack, with tests.",
                       "balanced parentheses checker python"])
    return task, code


@program("caesar_program", "strings")
def caesar_program(rng: Random) -> tuple[str, str]:
    shift = rng.randint(1, 25)
    message = rng.choice(["Meet me at noon", "Hello, World!", "Attack at dawn", "Python is great", "Keep it secret"])
    code = f"""import string


def shift_letter(ch, shift):
    for alphabet in (string.ascii_lowercase, string.ascii_uppercase):
        if ch in alphabet:
            return alphabet[(alphabet.index(ch) + shift) % 26]
    return ch


def encrypt(text, shift):
    return "".join(shift_letter(ch, shift) for ch in text)


def decrypt(text, shift):
    return encrypt(text, -shift)


if __name__ == "__main__":
    secret = encrypt("{message}", {shift})
    print(secret)
    print(decrypt(secret, {shift}))
    assert decrypt(secret, {shift}) == "{message}"
"""
    task = rng.choice([f"Write a Caesar cipher in Python with encrypt and decrypt functions that keep case and punctuation (shift {shift}).",
                       "caesar cipher encrypt and decrypt python"])
    return task, code


@program("sorting_algorithms", "algorithms")
def sorting_algorithms(rng: Random) -> tuple[str, str]:
    data = [rng.randint(0, 99) for _ in range(rng.choice([6, 8]))]
    algos = rng.sample(["bubble", "insertion", "selection", "quick"], 2)
    bodies = {
        "bubble": """def bubble_sort(values):
    items = list(values)
    for end in range(len(items) - 1, 0, -1):
        for i in range(end):
            if items[i] > items[i + 1]:
                items[i], items[i + 1] = items[i + 1], items[i]
    return items""",
        "insertion": """def insertion_sort(values):
    items = list(values)
    for i in range(1, len(items)):
        current = items[i]
        j = i - 1
        while j >= 0 and items[j] > current:
            items[j + 1] = items[j]
            j -= 1
        items[j + 1] = current
    return items""",
        "selection": """def selection_sort(values):
    items = list(values)
    for i in range(len(items)):
        smallest = min(range(i, len(items)), key=items.__getitem__)
        items[i], items[smallest] = items[smallest], items[i]
    return items""",
        "quick": """def quick_sort(values):
    if len(values) <= 1:
        return list(values)
    pivot, *rest = values
    smaller = [v for v in rest if v < pivot]
    larger = [v for v in rest if v >= pivot]
    return quick_sort(smaller) + [pivot] + quick_sort(larger)""",
    }
    funcs = "\n\n\n".join(bodies[a] for a in algos)
    names = ", ".join(f"{a}_sort" for a in algos)
    code = f"""{funcs}


if __name__ == "__main__":
    data = {data}
    for sort in ({names}):
        result = sort(data)
        assert result == sorted(data)
        print(f"{{sort.__name__:<15}}{{result}}")
"""
    task = rng.choice([f"Implement {algos[0]} sort and {algos[1]} sort in Python and check them against sorted().",
                       f"Python sorting algorithms: {algos[0]} sort and {algos[1]} sort with a test."])
    return task, code


@program("binary_search_program", "algorithms")
def binary_search_program(rng: Random) -> tuple[str, str]:
    size = rng.choice([16, 32, 100])
    target = rng.randint(0, size * 2)
    code = f"""def binary_search(items, target):
    low, high = 0, len(items) - 1
    steps = 0
    while low <= high:
        steps += 1
        mid = (low + high) // 2
        if items[mid] == target:
            return mid, steps
        if items[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1, steps


def linear_search(items, target):
    for index, value in enumerate(items):
        if value == target:
            return index, index + 1
    return -1, len(items)


if __name__ == "__main__":
    numbers = list(range(0, {size * 2}, 2))
    for search in (binary_search, linear_search):
        index, steps = search(numbers, {target})
        print(f"{{search.__name__:<14}} index={{index:<4}} steps={{steps}}")
"""
    task = rng.choice(["Write binary search and linear search in Python and compare how many steps each takes.", "binary search python example"])
    return task, code


@program("traffic_light", "classes")
def traffic_light(rng: Random) -> tuple[str, str]:
    durations = {"green": rng.choice([20, 30, 45]), "yellow": rng.choice([3, 4, 5]), "red": rng.choice([20, 30, 40])}
    code = f"""class TrafficLight:
    ORDER = ["green", "yellow", "red"]
    DURATIONS = {durations!r}

    def __init__(self):
        self.index = 0

    @property
    def color(self):
        return self.ORDER[self.index]

    def next(self):
        self.index = (self.index + 1) % len(self.ORDER)
        return self.color

    def cycle_time(self):
        return sum(self.DURATIONS.values())


if __name__ == "__main__":
    light = TrafficLight()
    for _ in range(4):
        print(f"{{light.color:<7}} for {{light.DURATIONS[light.color]}}s")
        light.next()
    print("Full cycle:", light.cycle_time(), "seconds")
"""
    task = rng.choice(["Write a traffic light state machine class in Python that cycles green, yellow, red.", "python traffic light simulation"])
    return task, code


@program("temperature_log", "data")
def temperature_log(rng: Random) -> tuple[str, str]:
    days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
    temps = [rng.randint(8, 30) for _ in days]
    unit = rng.choice(["C", "F"])
    if unit == "F":
        temps = [round(t * 9 / 5 + 32) for t in temps]
    code = f"""READINGS = {dict(zip(days, temps))!r}


def warmest(readings):
    day = max(readings, key=readings.get)
    return day, readings[day]


def coldest(readings):
    day = min(readings, key=readings.get)
    return day, readings[day]


def trend(readings):
    values = list(readings.values())
    rises = sum(1 for a, b in zip(values, values[1:]) if b > a)
    falls = sum(1 for a, b in zip(values, values[1:]) if b < a)
    if rises > falls:
        return "warming"
    if falls > rises:
        return "cooling"
    return "steady"


if __name__ == "__main__":
    day, value = warmest(READINGS)
    print(f"Warmest: {{day}} ({{value}}°{unit})")
    day, value = coldest(READINGS)
    print(f"Coldest: {{day}} ({{value}}°{unit})")
    print("Trend:", trend(READINGS))
"""
    task = rng.choice([f"Write a Python program that takes a week of temperatures (°{unit}) and prints the warmest day, the coldest day and whether it is warming or cooling.",
                       "python weekly temperature report"])
    return task, code


@program("password_checker", "strings")
def password_checker(rng: Random) -> tuple[str, str]:
    min_len = rng.choice([8, 10, 12])
    samples = rng.sample(["password", "Sunshine2024", "c0rrect-Horse!", "abc", "Tr0ub4dor&3", "LETMEIN", "ok_but_long_enough"], 4)
    code = f"""import string

RULES = [
    ("at least {min_len} characters", lambda p: len(p) >= {min_len}),
    ("a lowercase letter", lambda p: any(c.islower() for c in p)),
    ("an uppercase letter", lambda p: any(c.isupper() for c in p)),
    ("a digit", lambda p: any(c.isdigit() for c in p)),
    ("a symbol", lambda p: any(c in string.punctuation for c in p)),
]


def check_password(password):
    missing = [name for name, rule in RULES if not rule(password)]
    score = len(RULES) - len(missing)
    label = ["very weak", "weak", "fair", "good", "strong", "very strong"][score]
    return label, missing


if __name__ == "__main__":
    for password in {samples!r}:
        label, missing = check_password(password)
        print(f"{{password:<20}} {{label}}")
        if missing:
            print("  needs:", ", ".join(missing))
"""
    task = rng.choice([f"Write a Python password strength checker (min length {min_len}) that scores a password and says what it is missing.", "password strength checker in python"])
    return task, code


@program("linked_list", "classes")
def linked_list(rng: Random) -> tuple[str, str]:
    values = rng.sample(range(1, 50), 4)
    code = f"""class Node:
    def __init__(self, value, next_node=None):
        self.value = value
        self.next = next_node


class LinkedList:
    def __init__(self):
        self.head = None
        self.size = 0

    def append(self, value):
        node = Node(value)
        if self.head is None:
            self.head = node
        else:
            current = self.head
            while current.next:
                current = current.next
            current.next = node
        self.size += 1

    def prepend(self, value):
        self.head = Node(value, self.head)
        self.size += 1

    def remove(self, value):
        previous, current = None, self.head
        while current:
            if current.value == value:
                if previous:
                    previous.next = current.next
                else:
                    self.head = current.next
                self.size -= 1
                return True
            previous, current = current, current.next
        return False

    def to_list(self):
        values, current = [], self.head
        while current:
            values.append(current.value)
            current = current.next
        return values


if __name__ == "__main__":
    items = LinkedList()
    for value in {values}:
        items.append(value)
    items.prepend(0)
    items.remove({values[1]})
    print(items.to_list(), "size:", items.size)
"""
    task = rng.choice(["Write a singly linked list in Python with append, prepend, remove and to_list.", "linked list class python"])
    return task, code


@program("unit_converter", "math")
def unit_converter(rng: Random) -> tuple[str, str]:
    kind = rng.choice(["length", "weight"])
    table = ({"mm": 0.001, "cm": 0.01, "m": 1, "km": 1000, "in": 0.0254, "ft": 0.3048, "mi": 1609.344} if kind == "length"
             else {"g": 0.001, "kg": 1, "lb": 0.45359237, "oz": 0.028349523125})
    pairs = rng.sample([(a, b) for a in table for b in table if a != b], 3)
    calls = "\n".join(f"    print(f\"{v} {a} = {{convert({v}, '{a}', '{b}'):.3f}} {b}\")" for (a, b), v in zip(pairs, rng.sample([1, 2.5, 10, 42, 100], 3)))
    code = f"""FACTORS = {table!r}


def convert(value, from_unit, to_unit):
    if from_unit not in FACTORS or to_unit not in FACTORS:
        raise ValueError(f"unknown unit: {{from_unit}} or {{to_unit}}")
    return value * FACTORS[from_unit] / FACTORS[to_unit]


if __name__ == "__main__":
{calls}
"""
    task = rng.choice([f"Write a Python {kind} unit converter using a table of conversion factors.", f"convert {kind} units in python"])
    return task, code


@program("guessing_game", "games")
def guessing_game(rng: Random) -> tuple[str, str]:
    secret = rng.randint(1, 100)
    guesses = []
    low, high = 1, 100
    while True:
        g = (low + high) // 2
        guesses.append(g)
        if g == secret:
            break
        if g < secret:
            low = g + 1
        else:
            high = g - 1
    code = f"""def check_guess(guess, secret):
    if guess < secret:
        return "higher"
    if guess > secret:
        return "lower"
    return "correct"


def play(secret, guesses):
    for attempt, guess in enumerate(guesses, start=1):
        result = check_guess(guess, secret)
        print(f"Guess {{attempt}}: {{guess}} -> {{result}}")
        if result == "correct":
            return attempt
    return None


if __name__ == "__main__":
    tries = play({secret}, {guesses})
    print(f"Found it in {{tries}} tries!")
"""
    task = rng.choice(["Write a number guessing game in Python that says higher or lower, and simulate a game with a list of guesses.",
                       "python higher lower guessing game logic"])
    return task, code


@program("recipe_scaler", "data")
def recipe_scaler(rng: Random) -> tuple[str, str]:
    recipe = rng.choice([("pancakes", {"flour (g)": 200, "milk (ml)": 300, "eggs": 2, "sugar (g)": 25}, 4),
                         ("cookies", {"flour (g)": 250, "butter (g)": 120, "sugar (g)": 100, "eggs": 1}, 12),
                         ("soup", {"stock (ml)": 1000, "carrots": 3, "onion": 1, "lentils (g)": 150}, 4)])
    target = rng.choice([2, 6, 8, 24 if recipe[2] == 12 else 10])
    code = f"""RECIPE = {recipe[1]!r}
SERVES = {recipe[2]}


def scale(recipe, serves, wanted):
    factor = wanted / serves
    return {{name: round(amount * factor, 1) for name, amount in recipe.items()}}


def show(recipe):
    for name, amount in recipe.items():
        amount = int(amount) if float(amount).is_integer() else amount
        print(f"- {{amount}} {{name}}")


if __name__ == "__main__":
    print("{recipe[0].capitalize()} for {target}:")
    show(scale(RECIPE, SERVES, {target}))
"""
    task = rng.choice([f"Write a Python recipe scaler that adjusts the {recipe[0]} ingredients from {recipe[2]} servings to {target}.", "scale a recipe in python"])
    return task, code


# ---------------------------------------------------------------------------
# Modules composed from the short function families
# ---------------------------------------------------------------------------

def make_composed_module(families, render, rng: Random) -> tuple[str, str] | None:
    """2-3 related short functions in one module, plus a demo that calls each of them."""
    pool = [f for f in families if f.kind == "function" and f.checks]
    topic = rng.choice(sorted({f.topic for f in pool}))
    candidates = [f for f in pool if f.topic == topic]
    if len(candidates) < 2:
        return None
    chosen = rng.sample(candidates, min(len(candidates), rng.choice([2, 3])))
    used_names, parts, demos, descriptions = set(), [], [], []
    for fam in chosen:
        rendered = None
        for _ in range(6):
            rendered = render(fam, rng)
            if rendered and rendered.fn not in used_names:
                break
        if not rendered or rendered.fn in used_names:
            return None
        used_names.add(rendered.fn)
        parts.append(rendered.code.rstrip("\n"))
        args = rng.choice(fam.checks)
        demos.append(f"    print({rendered.fn}({', '.join(repr(a) for a in args)}))")
        descriptions.append(rendered.task.rstrip(".").replace("Return ", "returns ", 1) if rendered.task.startswith("Return ")
                            else rendered.task.rstrip("."))
    code = "\n\n\n".join(parts) + "\n\n\nif __name__ == \"__main__\":\n" + "\n".join(demos) + "\n"
    names = ", ".join(f"{n}()" for n in sorted(used_names))
    task = rng.choice([f"Write a Python module with these functions: {names}. Include a short demo.",
                       f"Write a Python {topic} utilities module ({names}) and show example calls.",
                       f"Python helpers module: {'; '.join(descriptions)}."])
    return task, code
