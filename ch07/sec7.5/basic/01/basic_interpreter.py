
import sys
import readline

from typing import Any, Optional
from basic_tokenizer import Tokenizer
from basic_evaluator import Evaluator
from basic_commands import CommandFactory, InterpreterEngine
from basic_utils import create_parser


CommandFactory.set_parser_factory(create_parser)

def main() -> None:
    interpreter = InterpreterEngine()
    
    if len(sys.argv) > 1:
        interpreter.load_program(sys.argv[1])
        try:
            interpreter.run()
        except KeyboardInterrupt:
            print("\n\nProgram paused by interrupt.")
            interpreter.state.paused = True
            current_line = interpreter.state.variables["#"]
            next_line = next((n for n in sorted(interpreter.state.code.keys()) if n > current_line), 0)
            interpreter.state.variables["#"] = next_line
        while interpreter.state.paused:
            try:
                line = input("> ").strip()
                if line:
                    interpreter.execute_line(line)
            except KeyboardInterrupt:
                print("\nProgram terminated by interrupt.")
                sys.exit(0)
            except EOFError:
                print("\nExiting.")
                sys.exit(0)
    else:
        import os
        os.system('cls||clear')
        print("BASIC Interpreter. Type BYE to exit.")
        while True:
            try:
                line = input("> ").strip()
                if not line:
                    continue
                tokenizer = Tokenizer(line)
                tokens = tokenizer.tokenize()
                if tokenizer.errors:
                    for error in tokenizer.errors:
                        print(f"Tokenization error: {error}")
                    continue
                parser = create_parser(tokens)
                try:
                    lineno = 0
                    line_content = line
                    if tokens and tokens[0].type == "NUMBER":
                        lineno_expr = parser.parse_number()
                        evaluator = Evaluator(interpreter.state)  # shared state
                        lineno = int(evaluator.evaluate(lineno_expr))
                        number_end_pos = tokens[0].position + len(tokens[0].value)
                        line_content = line[number_end_pos:].strip()
                    if lineno > 0:
                        interpreter.state.code[lineno] = line_content
                    else:
                        interpreter.execute_line(line)
                except Exception as e:
                    print(f"Error parsing line: {e}")
                    if not tokens or tokens[0].type != "NUMBER":
                        if line.strip() and line.strip() != "#":
                            interpreter.execute_line(line)
            except KeyboardInterrupt:
                print("Program terminated by interrupt.")
                sys.exit(0)
            except EOFError:
                print("\nExiting.")
                sys.exit(0)

if __name__ == "__main__":
    main()

