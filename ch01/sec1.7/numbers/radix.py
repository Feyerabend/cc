
# in PostScript there is a way to represent
# numbers with different bases called
# 'radix'. Explore radix .. with samples.

def parse_radix_number(radix_str):
    # split input based on '#'
    try:
        base_str, number_str = radix_str.split('#')
    except ValueError:
        raise ValueError("Invalid format. Use 'base#number'.")
    
    # base to integer
    base = int(base_str)
    
    # validate base
    if base < 2 or base > 36:
        raise ValueError("Base must be an integer between 2 and 36.")
    
    # attempt to parse number in given base
    try:
        decimal_value = int(number_str, base)
    except ValueError:
        raise ValueError(f"Invalid number '{number_str}' for base {base}.")
    
    return decimal_value

# example
try:
    radix_input = "16#1A3F"
    result = parse_radix_number(radix_input)
    print(f"The decimal value of {radix_input} is {result}")
except ValueError as e:
    print(e)