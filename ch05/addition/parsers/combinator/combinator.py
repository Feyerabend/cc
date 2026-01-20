import re

# base parser combinators
def literal(s):
    def parse(inp):
        if inp.startswith(s):
            return s, inp[len(s):]
        return None
    return parse

def regex(pattern):
    compiled = re.compile(pattern)
    def parse(inp):
        match = compiled.match(inp)
        if match:
            return match.group(), inp[match.end():]
        return None
    return parse

def seq(*parsers):
    def parse(inp):
        result = []
        remaining = inp
        for p in parsers:
            res = p(remaining)
            if res is None:
                return None
            value, remaining = res
            result.append(value)
        return result, remaining
    return parse

def choice(*parsers):
    def parse(inp):
        for p in parsers:
            res = p(inp)
            if res is not None:
                return res
        return None
    return parse

def opt(p):
    def parse(inp):
        res = p(inp)
        if res is None:
            return None, inp
        return res
    return parse

def many(p):
    def parse(inp):
        result = []
        remaining = inp
        while True:
            res = p(remaining)
            if res is None:
                break
            value, remaining = res
            result.append(value)
        return result, remaining
    return parse

# custom parsers
def parse_symbol():
    return regex(r'[a-zA-Z_+\-*/><=][a-zA-Z0-9_+\-*/><=]*')

def parse_number():
    int_parser = regex(r'-?\d+')
    float_parser = regex(r'-?\d+\.\d*')
    def parse(inp):
        res = choice(float_parser, int_parser)(inp)
        if res:
            value, remaining = res
            try:
                return int(value), remaining
            except ValueError:
                try:
                    return float(value), remaining
                except ValueError:
                    raise Exception(f"Parser assumption of a number as '{value}' failed.")
        return None
    return parse

def parse_whitespace():
    return regex(r'\s*')

def parse_list():
    def parse(inp):
        if inp.startswith('('):
            remaining = inp[1:]
            if remaining.startswith(')'):
                return [], remaining[1:] # empty
            items = []
            while remaining:
                _, remaining = parse_whitespace()(remaining)
                if remaining.startswith(')'):
                    return items, remaining[1:]
                item, remaining = parse_expr()(remaining)
                if item is None:
                    return None
                items.append(item)
            return None
        return None
    return parse

def parse_atom():
    return choice(parse_number(), parse_symbol())

def parse_expr():
    return choice(parse_atom(), parse_list())

def parse_top():
    def parse(inp):
        exprs = []
        remaining = inp.strip()
        while remaining:
            _, remaining = parse_whitespace()(remaining)
            if not remaining:
                break
            expr, remaining = parse_expr()(remaining)
            if expr:
                exprs.append(expr)
            remaining = remaining.strip()
        return exprs, remaining
    return parse

def parse(program):
    exprs, remaining = parse_top()(program)
    if remaining.strip():
        raise SyntaxError("Unexpected characters after expression: " + str(remaining))
    return exprs


test_cases = [
    # basic
    {
        "description": "Single number",
        "input": "42",
        "expected_output": [42]
    },
    {
        "description": "Single symbol",
        "input": "symbol",
        "expected_output": ["symbol"]
    },

    # lists
    {
        "description": "Empty list",
        "input": "()",
        "expected_output": [] # not [[]]
    },
    {
        "description": "Two empty lists",
        "input": "(()())",
        "expected_output": [[[],[]]]
    },
    {
        "description": "Nested list",
        "input": "(1 (2 (3)))",
        "expected_output": [[1, [2, [3]]]]
    },
    {
        "description": "List with mixed types",
        "input": "(42 foo (bar 3.14))",
        "expected_output": [[42, "foo", ["bar", 3.14]]]
    },

    # expressions
    {
        "description": "Arithmetic expression",
        "input": "(+ 1 2)",
        "expected_output": [["+", 1, 2]]
    },
    {
        "description": "Define statement",
        "input": "(define x 10)",
        "expected_output": [["define", "x", 10]]
    },
    {
        "description": "If statement with nested expressions",
        "input": "(if (> z 5) (* x 2) (/ x 2))",
        "expected_output": [["if", [">", "z", 5], ["*", "x", 2], ["/", "x", 2]]]
    },

    # complex expr
    {
        "description": "Multiple statements",
        "input": "(define add (x y)(+ x y)) (define x 10) (define y 90)",
        "expected_output": [
            ["define", "add", ["x", "y"], ["+", "x", "y"]],
            ["define", "x", 10],
            ["define", "y", 90]
        ]
    },
    {
        "description": "Expression with whitespace",
        "input": " (   +   1    2  ) ",
        "expected_output": [["+", 1, 2]]
    },
    {
        "description": "Expression with multiple nested lists",
        "input": "((a b) (c (d e)))",
        "expected_output": [[["a", "b"], ["c", ["d", "e"]]]]
    }
]


for test in test_cases:
    try:
        result = parse(test["input"])
        assert result == test["expected_output"], f"Test failed: {test['description']}"
        print(f"Test passed: {test['description']}")
    except AssertionError as e:
        print(e)
    except Exception as ex:
        print(f"Unexpected error in test '{test['description']}': {ex}")

