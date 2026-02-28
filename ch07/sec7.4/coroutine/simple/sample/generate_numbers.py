# generate_numbers.py

import random

def generate_numbers(filename, count=1_000_000, min_val=1, max_val=100):
    with open(filename, 'w') as f:
        for _ in range(count):
            number = random.randint(min_val, max_val)
            f.write(f"{number}\n")

if __name__ == '__main__':
    generate_numbers('numbers.txt')
