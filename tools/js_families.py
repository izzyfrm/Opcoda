"""JavaScript task families: pure functions, classes, and browser snippets.

Pure functions have several implementations; tools/make_code_curriculum.py runs every
implementation in Node on the same inputs and keeps only families whose variants agree.
Their example calls get the *real* output (computed by Node) as a trailing comment.
Templates use @name@ placeholders because JavaScript uses ${...} for its own templates.
"""
from __future__ import annotations

from dataclasses import dataclass
from random import Random


@dataclass(frozen=True)
class JsFunction:
    key: str
    names: tuple[str, ...]
    params: tuple[tuple[str, ...], ...]   # alternative parameter-name tuples
    tasks: tuple[str, ...]                 # may use @p0@, @p1@ ...
    variants: tuple[str, ...]              # bodies use @fn@ and @p0@ ...
    examples: tuple[str, ...]              # JS argument lists, e.g. "[1, 2, 3]"
    deterministic: bool = True


JS_FUNCTIONS: list[JsFunction] = []


def jsf(key, names, params, tasks, variants, examples, deterministic=True):
    JS_FUNCTIONS.append(JsFunction(key, tuple(names.split()), tuple(tuple(p.split(",")) for p in params),
                                   tuple(tasks), tuple(variants), tuple(examples), deterministic))


jsf("sum_array", "sumArray sum total", ["numbers", "values", "nums"],
    ["Write a JavaScript function that returns the sum of an array of numbers.", "Sum all numbers in @p0@ in JavaScript."],
    ["function @fn@(@p0@) {\n  return @p0@.reduce((total, n) => total + n, 0);\n}",
     "function @fn@(@p0@) {\n  let total = 0;\n  for (const n of @p0@) {\n    total += n;\n  }\n  return total;\n}",
     "const @fn@ = (@p0@) => @p0@.reduce((a, b) => a + b, 0);"],
    ["[1, 2, 3, 4]", "[]", "[10, -5, 7.5]"])

jsf("max_value", "maxValue largest findMax", ["numbers", "values", "list"],
    ["Write a JavaScript function that returns the largest number in an array, or null if it is empty."],
    ["function @fn@(@p0@) {\n  if (@p0@.length === 0) return null;\n  return Math.max(...@p0@);\n}",
     "function @fn@(@p0@) {\n  if (!@p0@.length) return null;\n  let best = @p0@[0];\n  for (const n of @p0@) {\n    if (n > best) best = n;\n  }\n  return best;\n}"],
    ["[3, 9, 2]", "[]", "[-4, -1, -7]"])

jsf("count_vowels", "countVowels vowelCount", ["text", "str", "sentence"],
    ["Write a JavaScript function that counts the vowels in a string.", "Count the vowels in @p0@ (case-insensitive) using JavaScript."],
    ["function @fn@(@p0@) {\n  const matches = @p0@.match(/[aeiou]/gi);\n  return matches ? matches.length : 0;\n}",
     "function @fn@(@p0@) {\n  let count = 0;\n  for (const ch of @p0@.toLowerCase()) {\n    if (\"aeiou\".includes(ch)) count++;\n  }\n  return count;\n}"],
    ['"Hello World"', '""', '"AEIOU xyz"'])

jsf("reverse_string", "reverseString reverseText", ["text", "str", "value"],
    ["Write a JavaScript function that reverses a string.", "Reverse @p0@ in JavaScript."],
    ['function @fn@(@p0@) {\n  return @p0@.split("").reverse().join("");\n}',
     'function @fn@(@p0@) {\n  let out = "";\n  for (let i = @p0@.length - 1; i >= 0; i--) {\n    out += @p0@[i];\n  }\n  return out;\n}',
     'const @fn@ = (@p0@) => [...@p0@].reverse().join("");'],
    ['"hello"', '""', '"JavaScript"'])

jsf("capitalize_words", "capitalizeWords titleCase", ["text", "sentence", "str"],
    ["Write a JavaScript function that capitalizes the first letter of every word.", "Capitalize each word in @p0@."],
    ['function @fn@(@p0@) {\n  return @p0@\n    .split(" ")\n    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))\n    .join(" ");\n}',
     'function @fn@(@p0@) {\n  return @p0@.replace(/\\b\\w/g, (ch) => ch.toUpperCase());\n}'],
    ['"hello big world"', '"javascript is fun"', '""'])

jsf("unique_values", "unique uniqueValues removeDuplicates", ["items", "values", "arr"],
    ["Write a JavaScript function that removes duplicates from an array and keeps the original order."],
    ["function @fn@(@p0@) {\n  return [...new Set(@p0@)];\n}",
     "function @fn@(@p0@) {\n  return @p0@.filter((item, index) => @p0@.indexOf(item) === index);\n}",
     "function @fn@(@p0@) {\n  const seen = new Set();\n  const result = [];\n  for (const item of @p0@) {\n    if (!seen.has(item)) {\n      seen.add(item);\n      result.push(item);\n    }\n  }\n  return result;\n}"],
    ["[3, 1, 3, 2, 1]", "[]", '["a", "b", "a"]'])

jsf("chunk_array", "chunk chunkArray splitIntoChunks", ["items,size", "arr,size", "values,n"],
    ["Write a JavaScript function that splits an array into chunks of a given size."],
    ["function @fn@(@p0@, @p1@) {\n  const chunks = [];\n  for (let i = 0; i < @p0@.length; i += @p1@) {\n    chunks.push(@p0@.slice(i, i + @p1@));\n  }\n  return chunks;\n}",
     "function @fn@(@p0@, @p1@) {\n  return Array.from({ length: Math.ceil(@p0@.length / @p1@) }, (_, i) =>\n    @p0@.slice(i * @p1@, i * @p1@ + @p1@)\n  );\n}"],
    ["[1, 2, 3, 4, 5], 2", "[], 3", "[1, 2, 3], 5"])

jsf("range", "range numberRange", ["start,end", "from,to", "low,high"],
    ["Write a JavaScript function that returns an array of integers from start to end inclusive."],
    ["function @fn@(@p0@, @p1@) {\n  const result = [];\n  for (let i = @p0@; i <= @p1@; i++) {\n    result.push(i);\n  }\n  return result;\n}",
     "function @fn@(@p0@, @p1@) {\n  if (@p1@ < @p0@) return [];\n  return Array.from({ length: @p1@ - @p0@ + 1 }, (_, i) => @p0@ + i);\n}"],
    ["1, 5", "3, 3", "5, 2"])

jsf("clamp", "clamp clampNumber", ["value,min,max", "n,low,high", "x,lower,upper"],
    ["Write a JavaScript function that clamps a number between a minimum and a maximum."],
    ["function @fn@(@p0@, @p1@, @p2@) {\n  return Math.min(Math.max(@p0@, @p1@), @p2@);\n}",
     "function @fn@(@p0@, @p1@, @p2@) {\n  if (@p0@ < @p1@) return @p1@;\n  if (@p0@ > @p2@) return @p2@;\n  return @p0@;\n}"],
    ["5, 0, 10", "-3, 0, 10", "42, 0, 10"])

jsf("factorial", "factorial fact", ["n", "num", "number"],
    ["Write a JavaScript function that returns the factorial of n.", "Factorial function in JavaScript."],
    ["function @fn@(@p0@) {\n  let result = 1;\n  for (let i = 2; i <= @p0@; i++) {\n    result *= i;\n  }\n  return result;\n}",
     "function @fn@(@p0@) {\n  return @p0@ <= 1 ? 1 : @p0@ * @fn@(@p0@ - 1);\n}"],
    ["5", "0", "10"])

jsf("fibonacci", "fibonacci fib", ["n", "count", "length"],
    ["Write a JavaScript function that returns the first n Fibonacci numbers as an array."],
    ["function @fn@(@p0@) {\n  const sequence = [];\n  let a = 0;\n  let b = 1;\n  for (let i = 0; i < @p0@; i++) {\n    sequence.push(a);\n    [a, b] = [b, a + b];\n  }\n  return sequence;\n}",
     "function @fn@(@p0@) {\n  const sequence = [0, 1];\n  while (sequence.length < @p0@) {\n    sequence.push(sequence[sequence.length - 1] + sequence[sequence.length - 2]);\n  }\n  return sequence.slice(0, @p0@);\n}"],
    ["8", "1", "0"])

jsf("word_frequency", "wordFrequency countEachWord tallyWords", ["text", "sentence", "str"],
    ["Write a JavaScript function that returns an object with how often each word appears in a string."],
    ["function @fn@(@p0@) {\n  const counts = {};\n  for (const word of @p0@.toLowerCase().split(/\\s+/).filter(Boolean)) {\n    counts[word] = (counts[word] || 0) + 1;\n  }\n  return counts;\n}",
     "function @fn@(@p0@) {\n  return @p0@\n    .toLowerCase()\n    .split(/\\s+/)\n    .filter(Boolean)\n    .reduce((counts, word) => {\n      counts[word] = (counts[word] ?? 0) + 1;\n      return counts;\n    }, {});\n}"],
    ['"the cat and the hat"', '""', '"Go go GO"'])

jsf("truncate", "truncate shorten", ["text,max", "str,limit", "value,length"],
    ['Write a JavaScript function that shortens text to a maximum length and adds "..." when it was cut.'],
    ['function @fn@(@p0@, @p1@) {\n  return @p0@.length > @p1@ ? @p0@.slice(0, @p1@) + "..." : @p0@;\n}',
     'function @fn@(@p0@, @p1@) {\n  if (@p0@.length <= @p1@) return @p0@;\n  return `${@p0@.slice(0, @p1@)}...`;\n}'],
    ['"hello world", 5', '"hi", 5', '"", 3'])

jsf("is_anagram", "isAnagram areAnagrams", ["a,b", "first,second", "word1,word2"],
    ["Write a JavaScript function that checks if two words are anagrams of each other."],
    ['function @fn@(@p0@, @p1@) {\n  const normalize = (s) => s.toLowerCase().split("").sort().join("");\n  return normalize(@p0@) === normalize(@p1@);\n}',
     'function @fn@(@p0@, @p1@) {\n  if (@p0@.length !== @p1@.length) return false;\n  const counts = {};\n  for (const ch of @p0@.toLowerCase()) counts[ch] = (counts[ch] || 0) + 1;\n  for (const ch of @p1@.toLowerCase()) {\n    if (!counts[ch]) return false;\n    counts[ch]--;\n  }\n  return true;\n}'],
    ['"listen", "silent"', '"abc", "abd"', '"", ""'])

jsf("digit_sum", "sumDigits digitSum", ["n", "num", "number"],
    ["Write a JavaScript function that adds up the digits of a non-negative integer."],
    ["function @fn@(@p0@) {\n  return String(@p0@)\n    .split(\"\")\n    .reduce((total, digit) => total + Number(digit), 0);\n}",
     "function @fn@(@p0@) {\n  let total = 0;\n  while (@p0@ > 0) {\n    total += @p0@ % 10;\n    @p0@ = Math.floor(@p0@ / 10);\n  }\n  return total;\n}"],
    ["1234", "0", "99"])

jsf("to_binary", "toBinary binaryString", ["n", "num", "value"],
    ["Write a JavaScript function that converts a non-negative integer to a binary string."],
    ["function @fn@(@p0@) {\n  return @p0@.toString(2);\n}",
     'function @fn@(@p0@) {\n  if (@p0@ === 0) return "0";\n  let bits = "";\n  while (@p0@ > 0) {\n    bits = (@p0@ % 2) + bits;\n    @p0@ = Math.floor(@p0@ / 2);\n  }\n  return bits;\n}'],
    ["5", "0", "255"])

jsf("sort_by_key", "sortBy sortByKey", ["items,key", "list,field", "records,prop"],
    ["Write a JavaScript function that sorts an array of objects by a given key without changing the original array."],
    ["function @fn@(@p0@, @p1@) {\n  return [...@p0@].sort((a, b) => (a[@p1@] > b[@p1@] ? 1 : a[@p1@] < b[@p1@] ? -1 : 0));\n}",
     "function @fn@(@p0@, @p1@) {\n  return @p0@.slice().sort((a, b) => {\n    if (a[@p1@] < b[@p1@]) return -1;\n    if (a[@p1@] > b[@p1@]) return 1;\n    return 0;\n  });\n}"],
    ['[{ name: "Zoe", age: 31 }, { name: "Ava", age: 25 }], "name"', '[{ n: 3 }, { n: 1 }, { n: 2 }], "n"', '[], "x"'])

jsf("pick_keys", "pick pickKeys", ["obj,keys", "source,fields", "record,props"],
    ["Write a JavaScript function that returns a new object with only the given keys."],
    ["function @fn@(@p0@, @p1@) {\n  const result = {};\n  for (const key of @p1@) {\n    if (key in @p0@) result[key] = @p0@[key];\n  }\n  return result;\n}",
     "function @fn@(@p0@, @p1@) {\n  return Object.fromEntries(@p1@.filter((key) => key in @p0@).map((key) => [key, @p0@[key]]));\n}"],
    ['{ a: 1, b: 2, c: 3 }, ["a", "c"]', '{}, ["x"]', '{ x: 1 }, []'])

jsf("zip_arrays", "zip zipArrays pairUp", ["a,b", "left,right", "first,second"],
    ["Write a JavaScript function that pairs up items from two arrays by position."],
    ["function @fn@(@p0@, @p1@) {\n  const length = Math.min(@p0@.length, @p1@.length);\n  const pairs = [];\n  for (let i = 0; i < length; i++) {\n    pairs.push([@p0@[i], @p1@[i]]);\n  }\n  return pairs;\n}",
     "function @fn@(@p0@, @p1@) {\n  return @p0@.slice(0, @p1@.length).map((item, i) => [item, @p1@[i]]);\n}"],
    ['[1, 2, 3], ["a", "b", "c"]', "[1], []", '[1, 2], ["x"]'])

jsf("fizzbuzz", "fizzBuzz fizzbuzz", ["n", "count", "limit"],
    ["Write a JavaScript function that returns the FizzBuzz sequence from 1 to n as an array."],
    ['function @fn@(@p0@) {\n  const result = [];\n  for (let i = 1; i <= @p0@; i++) {\n    if (i % 15 === 0) result.push("FizzBuzz");\n    else if (i % 3 === 0) result.push("Fizz");\n    else if (i % 5 === 0) result.push("Buzz");\n    else result.push(String(i));\n  }\n  return result;\n}',
     'function @fn@(@p0@) {\n  return Array.from({ length: @p0@ }, (_, index) => {\n    const i = index + 1;\n    return (i % 3 === 0 ? "Fizz" : "") + (i % 5 === 0 ? "Buzz" : "") || String(i);\n  });\n}'],
    ["15", "1", "0"])

jsf("escape_html", "escapeHtml escapeHTML", ["text", "str", "input"],
    ["Write a JavaScript function that escapes &, <, >, \" and ' so text is safe to put in HTML."],
    ['function @fn@(@p0@) {\n  return @p0@\n    .replace(/&/g, "&amp;")\n    .replace(/</g, "&lt;")\n    .replace(/>/g, "&gt;")\n    .replace(/"/g, "&quot;")\n    .replace(/\'/g, "&#39;");\n}',
     'function @fn@(@p0@) {\n  const map = { "&": "&amp;", "<": "&lt;", ">": "&gt;", \'"\': "&quot;", "\'": "&#39;" };\n  return @p0@.replace(/[&<>"\']/g, (ch) => map[ch]);\n}'],
    ['"<b>Tom & Jerry</b>"', '"plain"', '""'])

jsf("parse_query", "parseQuery parseQueryString", ["query", "qs", "search"],
    ["Write a JavaScript function that turns a query string like \"a=1&b=2\" into an object."],
    ['function @fn@(@p0@) {\n  const result = {};\n  for (const part of @p0@.replace(/^\\?/, "").split("&")) {\n    if (!part) continue;\n    const [key, value = ""] = part.split("=");\n    result[decodeURIComponent(key)] = decodeURIComponent(value);\n  }\n  return result;\n}',
     'function @fn@(@p0@) {\n  return Object.fromEntries(new URLSearchParams(@p0@));\n}'],
    ['"a=1&b=2"', '"?name=Ada&lang=js"', '""'])

jsf("format_currency", "formatCurrency formatPrice toDollars", ["amount", "value", "price"],
    ["Write a JavaScript function that formats a number as US dollars, like $1,234.50."],
    ['function @fn@(@p0@) {\n  return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD" }).format(@p0@);\n}',
     'function @fn@(@p0@) {\n  return @p0@.toLocaleString("en-US", { style: "currency", currency: "USD" });\n}'],
    ["1234.5", "0", "99.999"])

jsf("celsius_to_fahrenheit", "celsiusToFahrenheit cToF", ["celsius", "c", "temp"],
    ["Write a JavaScript function that converts Celsius to Fahrenheit."],
    ["function @fn@(@p0@) {\n  return (@p0@ * 9) / 5 + 32;\n}", "const @fn@ = (@p0@) => @p0@ * 1.8 + 32;"],
    ["0", "100", "-40"])

jsf("group_by", "groupBy groupItems", ["items,keyFn", "list,getKey", "values,fn"],
    ["Write a JavaScript function that groups array items into an object using a key function."],
    ["function @fn@(@p0@, @p1@) {\n  const groups = {};\n  for (const item of @p0@) {\n    const key = @p1@(item);\n    (groups[key] ||= []).push(item);\n  }\n  return groups;\n}",
     "function @fn@(@p0@, @p1@) {\n  return @p0@.reduce((groups, item) => {\n    const key = @p1@(item);\n    groups[key] = groups[key] || [];\n    groups[key].push(item);\n    return groups;\n  }, {});\n}"],
    ['["apple", "avocado", "banana"], (w) => w[0]', "[1, 2, 3, 4], (n) => (n % 2 ? \"odd\" : \"even\")", "[], (x) => x"])

jsf("debounce", "debounce", ["fn,delay", "callback,ms", "func,wait"],
    ["Write a debounce function in JavaScript.", "Create a JavaScript debounce helper that waits @p1@ milliseconds after the last call."],
    ["function @fn@(@p0@, @p1@) {\n  let timer;\n  return (...args) => {\n    clearTimeout(timer);\n    timer = setTimeout(() => @p0@(...args), @p1@);\n  };\n}",
     "function @fn@(@p0@, @p1@ = 300) {\n  let timeoutId = null;\n  return function (...args) {\n    if (timeoutId) clearTimeout(timeoutId);\n    timeoutId = setTimeout(() => {\n      timeoutId = null;\n      @p0@.apply(this, args);\n    }, @p1@);\n  };\n}"],
    [], deterministic=False)

jsf("random_int", "randomInt randomBetween", ["min,max", "low,high", "from,to"],
    ["Write a JavaScript function that returns a random integer between min and max, inclusive."],
    ["function @fn@(@p0@, @p1@) {\n  return Math.floor(Math.random() * (@p1@ - @p0@ + 1)) + @p0@;\n}"],
    [], deterministic=False)

jsf("shuffle", "shuffle shuffleArray", ["items", "arr", "list"],
    ["Write a JavaScript function that shuffles an array with the Fisher-Yates algorithm and returns a new array."],
    ["function @fn@(@p0@) {\n  const result = [...@p0@];\n  for (let i = result.length - 1; i > 0; i--) {\n    const j = Math.floor(Math.random() * (i + 1));\n    [result[i], result[j]] = [result[j], result[i]];\n  }\n  return result;\n}"],
    [], deterministic=False)

jsf("fetch_json", "fetchJson getJson loadJson", ["url", "endpoint", "path"],
    ["Write an async JavaScript function that fetches JSON from a URL and throws a helpful error when the request fails."],
    ["async function @fn@(@p0@) {\n  const response = await fetch(@p0@);\n  if (!response.ok) {\n    throw new Error(`Request failed: ${response.status} ${response.statusText}`);\n  }\n  return response.json();\n}",
     "async function @fn@(@p0@, options = {}) {\n  try {\n    const response = await fetch(@p0@, options);\n    if (!response.ok) throw new Error(`HTTP ${response.status}`);\n    return await response.json();\n  } catch (error) {\n    console.error(`Could not load ${@p0@}:`, error);\n    throw error;\n  }\n}"],
    [], deterministic=False)

jsf("memoize", "memoize cacheResults", ["fn", "func", "callback"],
    ["Write a memoize helper in JavaScript that caches results by argument."],
    ["function @fn@(@p0@) {\n  const cache = new Map();\n  return (...args) => {\n    const key = JSON.stringify(args);\n    if (!cache.has(key)) cache.set(key, @p0@(...args));\n    return cache.get(key);\n  };\n}"],
    [], deterministic=False)


# ---------------------------------------------------------------------------
# Classes and browser snippets (validated for syntax; classes also run a demo)
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class JsProgram:
    key: str
    make: object  # Callable[[Random], tuple[str, str, bool]] -> (task, code, runnable_in_node)


JS_PROGRAMS: list[JsProgram] = []


def jsp(key):
    def register(fn):
        JS_PROGRAMS.append(JsProgram(key, fn))
        return fn
    return register


@jsp("js_stack_class")
def js_stack_class(rng: Random):
    name = rng.choice(["Stack", "ItemStack"])
    field = rng.choice(["items", "data", "elements"])
    code = f"""class {name} {{
  constructor() {{
    this.{field} = [];
  }}

  push(item) {{
    this.{field}.push(item);
  }}

  pop() {{
    if (this.isEmpty()) {{
      throw new Error("Stack is empty");
    }}
    return this.{field}.pop();
  }}

  peek() {{
    return this.{field}[this.{field}.length - 1];
  }}

  isEmpty() {{
    return this.{field}.length === 0;
  }}

  get size() {{
    return this.{field}.length;
  }}
}}

const stack = new {name}();
stack.push(1);
stack.push(2);
stack.push(3);
console.log(stack.pop());
console.log(stack.peek());
console.log(stack.size);
"""
    return rng.choice([f"Write a {name} class in JavaScript with push, pop, peek, isEmpty and size.", "JavaScript stack class"]), code, True


@jsp("js_queue_class")
def js_queue_class(rng: Random):
    code = """class Queue {
  #items = [];

  enqueue(item) {
    this.#items.push(item);
  }

  dequeue() {
    return this.#items.shift();
  }

  peek() {
    return this.#items[0];
  }

  get length() {
    return this.#items.length;
  }
}

const queue = new Queue();
queue.enqueue("first");
queue.enqueue("second");
console.log(queue.dequeue());
console.log(queue.length);
"""
    return rng.choice(["Write a Queue class in JavaScript using a private field.", "JavaScript queue with enqueue and dequeue"]), code, True


@jsp("js_event_emitter")
def js_event_emitter(rng: Random):
    code = """class EventEmitter {
  constructor() {
    this.listeners = {};
  }

  on(event, listener) {
    (this.listeners[event] ||= []).push(listener);
    return () => this.off(event, listener);
  }

  off(event, listener) {
    this.listeners[event] = (this.listeners[event] || []).filter((fn) => fn !== listener);
  }

  emit(event, ...args) {
    for (const listener of this.listeners[event] || []) {
      listener(...args);
    }
  }
}

const emitter = new EventEmitter();
const stop = emitter.on("greet", (name) => console.log(`Hello, ${name}!`));
emitter.emit("greet", "Ada");
stop();
emitter.emit("greet", "Grace");
"""
    return rng.choice(["Write a small EventEmitter class in JavaScript with on, off and emit.", "event emitter in javascript"]), code, True


@jsp("js_shopping_cart")
def js_shopping_cart(rng: Random):
    items = rng.sample([("Coffee beans", 14.5), ("Mug", 9.0), ("Notebook", 6.25), ("T-shirt", 20.0), ("Tote bag", 12.0), ("Stickers", 3.5)], 3)
    adds = "\n".join(f'cart.add({{ id: {i + 1}, name: "{n}", price: {p} }}, {rng.randint(1, 3)});' for i, (n, p) in enumerate(items))
    discount = rng.random() < 0.5
    disc = """

  applyDiscount(percent) {
    this.discount = Math.min(Math.max(percent, 0), 100);
  }""" if discount else ""
    total_line = "    return Math.round(subtotal * (1 - this.discount / 100) * 100) / 100;" if discount else "    return Math.round(subtotal * 100) / 100;"
    code = f"""class ShoppingCart {{
  constructor() {{
    this.items = new Map();
    this.discount = 0;
  }}

  add(product, quantity = 1) {{
    const line = this.items.get(product.id) || {{ product, quantity: 0 }};
    line.quantity += quantity;
    this.items.set(product.id, line);
  }}

  remove(id) {{
    this.items.delete(id);
  }}{disc}

  get total() {{
    let subtotal = 0;
    for (const {{ product, quantity }} of this.items.values()) {{
      subtotal += product.price * quantity;
    }}
{total_line}
  }}
}}

const cart = new ShoppingCart();
{adds}
cart.remove({rng.randint(1, 3)});
{"cart.applyDiscount(10);" + chr(10) if discount else ""}console.log(`Total: $${{cart.total.toFixed(2)}}`);
"""
    task = rng.choice(["Write a ShoppingCart class in JavaScript with add, remove and a total getter" + (", plus a percentage discount." if discount else "."),
                       "javascript shopping cart class"])
    return task, code, True


@jsp("js_dom_click_toggle")
def js_dom_click_toggle(rng: Random):
    cls = rng.choice(["open", "active", "expanded", "is-visible"])
    code = f"""const button = document.querySelector("#menu-button");
const menu = document.querySelector("#menu");

button.addEventListener("click", () => {{
  const isOpen = menu.classList.toggle("{cls}");
  button.setAttribute("aria-expanded", String(isOpen));
}});

document.addEventListener("keydown", (event) => {{
  if (event.key === "Escape" && menu.classList.contains("{cls}")) {{
    menu.classList.remove("{cls}");
    button.setAttribute("aria-expanded", "false");
    button.focus();
  }}
}});
"""
    return rng.choice([f'Toggle a "{cls}" class on a menu when a button is clicked, and close it with Escape.', "javascript toggle menu on click"]), code, False


@jsp("js_dom_copy_button")
def js_dom_copy_button(rng: Random):
    code = """document.querySelectorAll("[data-copy]").forEach((button) => {
  button.addEventListener("click", async () => {
    const target = document.querySelector(button.dataset.copy);
    try {
      await navigator.clipboard.writeText(target.textContent);
      button.textContent = "Copied!";
    } catch {
      button.textContent = "Copy failed";
    }
    setTimeout(() => (button.textContent = "Copy"), 1500);
  });
});
"""
    return "Make copy-to-clipboard buttons in JavaScript that copy the text of the element named in data-copy.", code, False


@jsp("js_dom_fetch_list")
def js_dom_fetch_list(rng: Random):
    what = rng.choice([("users", "name"), ("posts", "title"), ("todos", "title"), ("products", "name")])
    code = f"""const list = document.querySelector("#{what[0]}");
const status = document.querySelector("#status");

async function load{what[0].capitalize()}() {{
  status.textContent = "Loading...";
  try {{
    const response = await fetch("/api/{what[0]}");
    if (!response.ok) throw new Error(`HTTP ${{response.status}}`);
    const data = await response.json();
    list.innerHTML = "";
    for (const item of data) {{
      const li = document.createElement("li");
      li.textContent = item.{what[1]};
      list.append(li);
    }}
    status.textContent = data.length ? "" : "Nothing to show yet.";
  }} catch (error) {{
    status.textContent = "Could not load {what[0]}. Please try again.";
    console.error(error);
  }}
}}

load{what[0].capitalize()}();
"""
    return f"Fetch a list of {what[0]} from /api/{what[0]} and render each {what[1]} as a list item, with loading and error messages.", code, False


@jsp("js_dom_local_storage_form")
def js_dom_local_storage_form(rng: Random):
    key = rng.choice(["draft", "contact-form", "notes", "profile"])
    code = f"""const form = document.querySelector("form");
const STORAGE_KEY = "{key}";

const saved = JSON.parse(localStorage.getItem(STORAGE_KEY) || "{{}}");
for (const [name, value] of Object.entries(saved)) {{
  if (form.elements[name]) form.elements[name].value = value;
}}

form.addEventListener("input", () => {{
  const data = Object.fromEntries(new FormData(form));
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
}});

form.addEventListener("submit", () => {{
  localStorage.removeItem(STORAGE_KEY);
}});
"""
    return "Save a form's fields to localStorage as the user types, restore them on load, and clear them on submit.", code, False


@jsp("js_dom_countdown")
def js_dom_countdown(rng: Random):
    target = rng.choice(["2026-12-31T23:59:59", "2027-01-01T00:00:00", "2026-11-26T09:00:00"])
    code = f"""const output = document.querySelector("#countdown");
const target = new Date("{target}");

function pad(value) {{
  return String(value).padStart(2, "0");
}}

function tick() {{
  const remaining = target - new Date();
  if (remaining <= 0) {{
    output.textContent = "It's here!";
    clearInterval(timer);
    return;
  }}
  const days = Math.floor(remaining / 86400000);
  const hours = Math.floor((remaining % 86400000) / 3600000);
  const minutes = Math.floor((remaining % 3600000) / 60000);
  const seconds = Math.floor((remaining % 60000) / 1000);
  output.textContent = `${{days}}d ${{pad(hours)}}h ${{pad(minutes)}}m ${{pad(seconds)}}s`;
}}

const timer = setInterval(tick, 1000);
tick();
"""
    return f"Show a live countdown to {target[:10]} in days, hours, minutes and seconds.", code, False


@jsp("js_dom_smooth_scroll")
def js_dom_smooth_scroll(rng: Random):
    code = """document.querySelectorAll('a[href^="#"]').forEach((link) => {
  link.addEventListener("click", (event) => {
    const target = document.querySelector(link.getAttribute("href"));
    if (!target) return;
    event.preventDefault();
    target.scrollIntoView({ behavior: "smooth", block: "start" });
    history.pushState(null, "", link.getAttribute("href"));
  });
});
"""
    return "Make anchor links scroll smoothly to their section with JavaScript.", code, False


@jsp("js_dom_password_toggle")
def js_dom_password_toggle(rng: Random):
    code = """const password = document.querySelector("#password");
const toggle = document.querySelector("#toggle-password");

toggle.addEventListener("click", () => {
  const showing = password.type === "text";
  password.type = showing ? "password" : "text";
  toggle.textContent = showing ? "Show" : "Hide";
  toggle.setAttribute("aria-pressed", String(!showing));
});
"""
    return "Add a show/hide password button with JavaScript.", code, False


@jsp("js_dom_keyboard_shortcuts")
def js_dom_keyboard_shortcuts(rng: Random):
    key = rng.choice(["k", "/", "s"])
    code = f"""const search = document.querySelector("#search");

document.addEventListener("keydown", (event) => {{
  const typing = ["INPUT", "TEXTAREA"].includes(document.activeElement.tagName);
  if (event.key === "{key}" && (event.ctrlKey || event.metaKey || !typing)) {{
    event.preventDefault();
    search.focus();
    search.select();
  }}
  if (event.key === "Escape" && document.activeElement === search) {{
    search.blur();
  }}
}});
"""
    return f'Focus the search box when the user presses "{key}" (or Ctrl/Cmd+{key}) and blur it on Escape.', code, False
