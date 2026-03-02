dispatch_table = {}
def register(name):
    def decorator(func):
        dispatch_table[name] = func
        return func
    return decorator
@register("add")
def add(a, b): return a + b
@register("subtract")
def subtract(a, b): return a - b
print(dispatch_table["add"](2, 3))  # 5
# print(dispatch_table["subtract"](5, 2))  # 3
