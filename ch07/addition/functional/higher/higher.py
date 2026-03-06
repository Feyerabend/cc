# higher.py
# Functional Patterns -- 4. Higher-Order Functions
#
# Demonstrates map, filter, reduce, and custom higher-order functions.
# Shows declarative vs. imperative style and pipeline construction.
#
# Run:  python higher.py

from functools import reduce
from concurrent.futures import ProcessPoolExecutor



# Concrete functions used as arguments throughout

def square(x):  return x * x
def negate(x):  return -x
def double(x):  return x * 2



# Manual implementations (section 7) -- defined at module level so the
# parallel worker (section 9) can import them without re-running demos.

def my_map(f, iterable):
    for x in iterable:
        yield f(x)

def my_filter(pred, iterable):
    for x in iterable:
        if pred(x):
            yield x

def my_reduce(f, iterable, initial):
    acc = initial
    for x in iterable:
        acc = f(acc, x)
    return acc

def heavy_square(x):
    """Stateless -- safe to run in any worker process."""
    return x * x



# Demo functions (sections 5, 6)

def apply_twice(f, x):
    return f(f(x))

def take_while(pred, iterable):
    for item in iterable:
        if not pred(item):
            break
        yield item

def drop_while(pred, iterable):
    dropping = True
    for item in iterable:
        if dropping and pred(item):
            continue
        dropping = False
        yield item



# main -- all output lives here so worker processes don't repeat it

def main():
    nums = [1, 2, 3, 4, 5, 6, 7, 8]

    # --- 1. map
    print("-- 1. map --")
    print(f"  nums:    {nums}")
    print(f"  squared: {list(map(square, nums))}")
    print(f"  negated: {list(map(negate, nums))}")
    print(f"  as_str:  {list(map(str,    nums))}")
    print(f"  doubled: {list(map(double, nums))}")

    # --- 2. filter
    print("\n-- 2. filter --")
    print(f"  evens:   {list(filter(lambda x: x % 2 == 0, nums))}")
    print(f"  odds:    {list(filter(lambda x: x % 2 != 0, nums))}")
    print(f"  > 4:     {list(filter(lambda x: x > 4,      nums))}")

    # --- 3. reduce
    print("\n-- 3. reduce --")
    print(f"  sum:     {reduce(lambda acc, x: acc + x, nums, 0)}")    # 36
    print(f"  product: {reduce(lambda acc, x: acc * x, nums, 1)}")   # 40320
    print(f"  max:     {reduce(lambda a, x: a if a > x else x, nums, nums[0])}")  # 8

    # --- 4. Pipeline
    print("\n-- 4. Pipeline: evens -> squared -> sum --")
    evens_it   = filter(lambda x: x % 2 == 0, nums)
    squares_it = map(square, evens_it)
    total      = reduce(lambda acc, x: acc + x, squares_it, 0)
    print(f"  result: {total}")   # 120

    # --- 5. Custom higher-order functions
    print("\n-- 5. Custom higher-order functions --")
    print(f"  apply_twice(square, 3) = {apply_twice(square, 3)}")   # 81
    print(f"  apply_twice(negate, 5) = {apply_twice(negate, 5)}")   # 5

    data = [1, 2, 3, 7, 8, 1, 2]
    print(f"  take_while(<4): {list(take_while(lambda x: x < 4, data))}")
    print(f"  drop_while(<4): {list(drop_while(lambda x: x < 4, data))}")

    # --- 6. sorted with key
    print("\n-- 6. sorted with key function --")
    words = ["banana", "fig", "apple", "kiwi", "date"]
    print(f"  by length:    {sorted(words, key=len)}")
    print(f"  by last char: {sorted(words, key=lambda w: w[-1])}")

    # --- 7. Manual implementations
    print("\n-- 7. Manual map / filter / reduce --")
    result = my_reduce(
        lambda acc, x: acc + x,
        my_map(square,
               my_filter(lambda x: x % 2 == 0, nums)),
        0
    )
    print(f"  manual pipeline (evens -> squared -> sum): {result}")  # 120

    # --- 8. Stateless vs. stateful
    print("\n-- 8. Stateless vs. stateful map --")
    print(f"  pure squares: {list(map(square, nums))}")

    running = [0]
    def cumulative(x):
        running[0] += x
        return running[0]

    print(f"  cumulative sums (sequential only): {list(map(cumulative, nums))}")
    print("  (would race if parallelised -- stateful transform)")

    # --- 9. Parallel map
    print("\n-- 9. Parallel map (ProcessPoolExecutor) --")
    with ProcessPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(heavy_square, range(1, 9)))
    print(f"  parallel squares: {results}")
    print("  (each worker received its own slice -- no shared state)")


if __name__ == "__main__":
    main()
