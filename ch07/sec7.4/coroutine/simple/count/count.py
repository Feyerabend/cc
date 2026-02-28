def count_up_to(limit):
    count = 1
    while count <= limit:
        yield count  # pause and return the value of count
        count += 1

# using coroutine
counter = count_up_to(5)

for number in counter:
    print(number)  # Output: prints numbers 1 through 5
