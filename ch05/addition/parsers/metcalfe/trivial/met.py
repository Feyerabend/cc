#!/usr/bin/env python3
# coding: utf-8

import re
import sys
import getopt
from typing import List, Dict, Any, Tuple


class Opcodes:
    NOP = 0
    CALL = 1
    FALSE = 2
    FFLAG = 3
    TFLAG = 4
    MATCH = 5
    PRINT = 6
    RETURN = 7
    STOP = 8
    THEN = 9
    TRUE = 10

    # Maps opcodes to their string representation
    OPCODE_MAP = {
        CALL: 'call',
        FALSE: 'false',
        FFLAG: 'fflag',
        TFLAG: 'tflag',
        MATCH: 'match',
        PRINT: 'print',
        RETURN: 'return',
        STOP: 'stop',
        THEN: 'then',
        TRUE: 'true'
    }

    # Maps opcodes to their arity (number of arguments)
    OPCODE_ARITY = [
        0,  # NOP: no operand
        1,  # CALL: addr
        1,  # FALSE: addr
        0,  # FFLAG
        0,  # TFLAG
        1,  # MATCH: item
        1,  # PRINT: item
        0,  # RETURN
        0,  # STOP
        1,  # THEN: item
        1   # TRUE: addr
    ]


class Assembler:

    def __init__(self, verbose: bool = False):
        self.verbose = verbose

    def remove_comments(self, content: List[str]) -> List[str]:
        return [re.sub('#.*', '', line) for line in content]

    def prepare(self, content: List[str]) -> List[List[str]]:
        # Remove comments
        content = self.remove_comments(content)
        
        # Normalize whitespace
        content = [' '.join(line.split()) for line in content]
        
        # Remove empty lines
        content = [line for line in content if line.strip()]
        
        # Split into tokens
        content = [line.split() for line in content if line]
        
        return content

    def parse_line(self, line: List[str]) -> List[Any]:
        # Check if first token is an opcode
        opcode_matches = [i for i in Opcodes.OPCODE_MAP if Opcodes.OPCODE_MAP[i] == line[0]]
        
        if opcode_matches:
            result = []
            opcode = opcode_matches[0]
            arity = Opcodes.OPCODE_ARITY[opcode]
            
            # Add opcode
            result.append(opcode)
            
            # Add argument if needed
            if arity == 1:
                result.append(line[1])
                
            return result
        else:
            # Not an opcode, return as is
            return line

    def assemble(self, input_file: str, output_file: str) -> str:
        # Read input file
        with open(input_file, 'r') as f:
            content = f.readlines()
        
        # Prepare and parse content
        content = self.prepare(content)
        parsed_content = []
        for line in content:
            parsed_line = self.parse_line(line)
            parsed_content.append(parsed_line)
        
        if self.verbose:
            print("Parsed:", parsed_content)
        
        # Resolve labels
        resolved_content = []
        labels = {}  # Dictionary of labels to their addresses
        offset = 0   # Current address
        
        # First pass: collect labels
        for item in [val for sublist in parsed_content for val in sublist]:
            is_label = isinstance(item, str) and item.endswith(':')
            if is_label:
                label_name = ':' + item[:-1]  # Convert "LABEL:" to ":LABEL"
                labels[label_name] = offset
            else:
                offset += 1
                resolved_content.append(item)
        
        # Second pass: replace label references with addresses
        final_content = []
        for token in resolved_content:
            if isinstance(token, str) and token.startswith(':'):
                if token in labels:
                    final_content.append(labels[token])
                else:
                    raise ValueError(f"Label {token} not found")
            else:
                final_content.append(token)
        
        if self.verbose:
            print("No labels:", final_content)
        
        # Convert to string
        final_string = ','.join(str(item) for item in final_content)
        
        if self.verbose:
            print("Output to file:", final_string)
        
        # Write to output file
        with open(output_file, 'w') as f:
            f.write(final_string)
        
        return final_string


def main():
    input_file = ''
    output_file = ''
    verbose = False
    
    try:
        opts, args = getopt.getopt(sys.argv[1:], "vhi:o:", ["ifile=", "ofile="])
    except getopt.GetoptError:
        print('met.py -i <inputfile> -o <outputfile>')
        sys.exit(2)
    
    for opt, arg in opts:
        if opt == '-v':
            verbose = True
        elif opt == '-h':
            print('usage: met.py -i <inputfile> -o <outputfile>')
            sys.exit()
        elif opt in ("-i", "--ifile"):
            input_file = arg
        elif opt in ("-o", "--ofile"):
            output_file = arg
    
    if not input_file or not output_file:
        print('Error: Input and output files must be specified')
        print('usage: met.py -i <inputfile> -o <outputfile>')
        sys.exit(2)
    
    if verbose:
        print("Assembling...")
    
    assembler = Assembler(verbose)
    assembler.assemble(input_file, output_file)
    
    if verbose:
        print("Done.")


if __name__ == "__main__":
    main()
