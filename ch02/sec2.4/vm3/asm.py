import sys
import getopt
import re

def no_comments(content):
    ncontent = []
    for line_num, line in enumerate(content, start=1):
        temp = re.sub('#.*', '', line)
        ncontent.append((line_num, temp))
    return ncontent

def prepare(content):
    content = no_comments(content)
    content = [(line_num, ' '.join(line.split())) for line_num, line in content]
    content = [(line_num, line) for line_num, line in content if line.strip()]
    content = [(line_num, line.split()) for line_num, line in content if line]
    return content

def to_decimal(number, line_num):
    try:
        return int(number)
    except ValueError:
        print(f"Error: Invalid number '{number}' on line {line_num}")
        sys.exit(1)

def parse(line_num, line, ops):
    if line[0] in ops:
        nline = []
        opcode, arity = ops[line[0]]
        nline.append(opcode)
        if arity == 1:
            if len(line) < 2:
                print(f"Error: Missing argument for '{line[0]}' on line {line_num}")
                sys.exit(1)
            nline.append(line[1])
        elif arity == 0 and len(line) > 1:
            print(f"Error: Extra argument for '{line[0]}' on line {line_num}")
            sys.exit(1)
        return nline
    else:
        print(f"Error: Unknown opcode '{line[0]}' on line {line_num}")
        sys.exit(1)

def assemble(inputfile, outputfile, enum_dict, verbose):
    try:
        with open(inputfile) as f:
            content = f.readlines()
    except FileNotFoundError:
        print(f"Error: Input file '{inputfile}' not found")
        sys.exit(1)

    content = prepare(content)

    # step 1: first pass - identify labels and calculate offsets
    ncontent = []
    labels = {}
    offset = 0

    for line_num, line in content:
        if line[0].endswith(':'):  # label declaration (e.g., START:)
            label = ':' + line[0][:-1]
            if label in labels:
                print(f"Error: Duplicate label '{label}' on line {line_num}")
                sys.exit(1)
            labels[label] = offset
        else:
            parsed_line = parse(line_num, line, enum_dict)
            ncontent.append((line_num, parsed_line))
            offset += len(parsed_line)  # increase offset based on instruction length

    # step 2: second pass - replace labels with actual addresses
    final_content = []
    for line_num, line in ncontent:
        for token in line:
            if isinstance(token, str) and token.startswith(':'):
                if token not in labels:
                    print(f"Error: Undefined label '{token}' on line {line_num}")
                    sys.exit(1)
                final_content.append(labels[token])
            else:
                final_content.append(token)

    # convert tokens to decimal
    final = [to_decimal(token, line_num) for line_num, token in enumerate(final_content)]

    if verbose:
        print("Final bytecode:", final)
        print("Labels:", labels)

    # insert start address (based on :START label)
    start_address = labels.get(':START', 0)
    final.insert(0, start_address)
    final_str = [str(int) for int in final]

    # write the final bytecode to the output file
    with open(outputfile, "w") as f:
        f.write(','.join(final_str))

def extract(file_path):
    enum_dict = {}
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
    except FileNotFoundError:
        print(f"Error: Header file '{file_path}' not found")
        sys.exit(1)

    inside_enum = False
    enum_counter = 0
    for line in lines:
        if 'enum' in line:
            inside_enum = True
            continue
        if inside_enum and '};' in line:
            break
        if inside_enum:
            match = re.match(r'(\w+)\s*,\s*//\s*(\d+)', line.strip())
            if match:
                enum_name = match.group(1)
                arity = int(match.group(2))
                enum_dict[enum_name] = (enum_counter, arity)
                enum_counter += 1
    return enum_dict

def main(argv):
    inputfile = ''
    outputfile = ''
    verbose = False

    try:
        opts, args = getopt.getopt(argv,"vhi:o:",["ifile=","ofile="])
    except getopt.GetoptError:
        print('usage: asm.py -i <inputfile> -o <outputfile>')
        sys.exit(2)

    for opt, arg in opts:
        if opt == '-v':
            verbose = True
        if opt == '-h':
            print('usage: asm.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            inputfile = arg
        elif opt in ("-o", "--ofile"):
            outputfile = arg

    if not inputfile or not outputfile:
        print('usage: asm.py -i <inputfile> -o <outputfile>')
        sys.exit(2)

    headerfile = 'vm3.h'  # hardcoded header file
    enum_dict = extract(headerfile)

    assemble(inputfile, outputfile, enum_dict, verbose)

if __name__ == "__main__":
   main(sys.argv[1:])