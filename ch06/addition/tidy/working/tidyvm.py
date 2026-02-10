# Lisp with VM-based execution

import sys
import traceback


Symbol = str

class Env(dict):
    "An environment: a dict of {'var':val} pairs, with an outer Env."
    
    def __init__(self, params=(), args=(), outer=None):
        self.update(list(zip(params, args)))
        self.outer = outer
    
    def find(self, var):
        "Find the innermost Env where var appears."
        if var in self:
            return self
        elif self.outer is not None:
            return self.outer.find(var)
        else:
            raise NameError(f"Variable '{var}' is not defined")



class Closure:
    "A closure: compiled code + captured environment."
    
    def __init__(self, code, env, params=()):
        self.code = code
        self.env = env
        self.params = params
    
    def __repr__(self):
        return f"<Closure params={self.params}>"



class VM:
    "A stack-based virtual machine for executing compiled Lisp."
    
    def __init__(self, env=None, debug=False):
        self.stack = []
        self.env = env if env is not None else Env()
        self.debug = debug
    
    def run(self, instructions):
        "Execute a list of instructions and return the result."
        pc = 0
        while pc < len(instructions):
            instr = instructions[pc]
            if self.debug:
                print(f"PC={pc} {instr} | Stack={self.stack}")
            self._execute(instr)
            pc += 1
        
        if len(self.stack) == 1:
            return self.stack.pop()
        elif len(self.stack) == 0:
            return None
        raise RuntimeError(f"Stack has {len(self.stack)} values instead of 1")
    
    def _execute(self, instr):
        "Execute a single instruction."
        if isinstance(instr, tuple):
            self._execute_tuple(instr)
        elif isinstance(instr, str):
            self._execute_string(instr)
        else:
            raise ValueError(f"Invalid instruction: {instr}")
    
    def _execute_tuple(self, instr):
        "Execute tuple-based instructions (IF, CLOSURE, etc)."
        op = instr[0]
        
        if op == 'IF':
            _, true_code, false_code = instr
            condition = self.stack.pop()
            branch = true_code if condition else false_code
            result = VM(self.env, self.debug).run(branch)
            self.stack.append(result)
        
        elif op == 'CLOSURE':
            _, code, params = instr
            # Capture reference to current environment
            self.stack.append(Closure(code, self.env, params))
        
        else:
            raise ValueError(f"Unknown tuple instruction: {op}")
    
    def _execute_string(self, instr):
        "Execute string-based instructions (PUSH, LOAD, ADD, etc)."
        parts = instr.split(maxsplit=1)
        opcode = parts[0]
        
        if opcode == 'PUSH':
            value = parts[1]
            self.stack.append(self._parse_value(value))
        
        elif opcode == 'LOAD':
            var = parts[1]
            self.stack.append(self.env.find(var)[var])
        
        elif opcode == 'STORE':
            var = parts[1]
            self.env[var] = self.stack.pop()
        
        elif opcode == 'APPLY':
            arg = self.stack.pop()
            func = self.stack.pop()
            
            if isinstance(func, Closure):
                new_env = Env(func.params, [arg], func.env)
                result = VM(new_env, self.debug).run(func.code)
                self.stack.append(result)
            elif callable(func):
                # Built-in function
                self.stack.append(func(arg))
            else:
                raise ValueError(f"Cannot apply {func}")
        
        elif opcode == 'CALL':
            n = int(parts[1]) if len(parts) > 1 else 0
            args = [self.stack.pop() for _ in range(n)][::-1]
            func = self.stack.pop()
            
            if isinstance(func, Closure):
                # Create new environment extending the closure's environment
                new_env = Env(func.params, args, func.env)
                result = VM(new_env, self.debug).run(func.code)
                self.stack.append(result)
            elif callable(func):
                self.stack.append(func(*args))
            else:
                raise ValueError(f"Cannot call {func}")
        
        elif opcode in ['ADD', 'SUB', 'MUL', 'DIV']:
            self._binary_op(opcode)
        
        elif opcode in ['GT', 'LT', 'GTE', 'LTE', 'EQ']:
            self._compare_op(opcode)
        
        elif opcode == 'LIST':
            n = int(parts[1]) if len(parts) > 1 else 0
            lst = [self.stack.pop() for _ in range(n)][::-1]
            self.stack.append(lst)
        
        elif opcode == 'CAR':
            lst = self.stack.pop()
            self.stack.append(lst[0])
        
        elif opcode == 'CDR':
            lst = self.stack.pop()
            self.stack.append(lst[1:])
        
        elif opcode == 'CONS':
            cdr = self.stack.pop()
            car = self.stack.pop()
            self.stack.append([car] + cdr)
        
        elif opcode == 'NULL?':
            val = self.stack.pop()
            self.stack.append(val == [])
        
        elif opcode == 'ATOM?':
            val = self.stack.pop()
            self.stack.append(not isinstance(val, list))
        
        elif opcode == 'RET':
            pass  # Stack top is the return value
        
        elif opcode == 'POP':
            if self.stack:
                self.stack.pop()
        
        else:
            raise ValueError(f"Unknown opcode: {opcode}")
    
    def _parse_value(self, value):
        "Parse a string value into int, float, bool, or string."
        if value == 'True':
            return True
        elif value == 'False':
            return False
        elif value == '[]':
            return []
        try:
            return int(value)
        except ValueError:
            try:
                return float(value)
            except ValueError:
                return value
    
    def _binary_op(self, opcode):
        "Execute binary arithmetic operations."
        b = self.stack.pop()
        a = self.stack.pop()
        if opcode == 'ADD':
            self.stack.append(a + b)
        elif opcode == 'SUB':
            self.stack.append(a - b)
        elif opcode == 'MUL':
            self.stack.append(a * b)
        elif opcode == 'DIV':
            self.stack.append(a / b)
    
    def _compare_op(self, opcode):
        "Execute comparison operations."
        b = self.stack.pop()
        a = self.stack.pop()
        if opcode == 'GT':
            self.stack.append(a > b)
        elif opcode == 'LT':
            self.stack.append(a < b)
        elif opcode == 'GTE':
            self.stack.append(a >= b)
        elif opcode == 'LTE':
            self.stack.append(a <= b)
        elif opcode == 'EQ':
            self.stack.append(a == b)



def compile_expr(expr, env=None):
    "Compile a Lisp expression to VM instructions."
    
    if isinstance(expr, Symbol):  # variable reference
        return [f'LOAD {expr}']
    
    elif not isinstance(expr, list):  # constant literal
        return [f'PUSH {expr}']
    
    elif expr[0] == 'quote' or expr[0] == 'q':  # (quote exp)
        _, exp = expr
        # Push the quoted expression as a literal value
        if isinstance(exp, list):
            # For lists, we need to build them at runtime
            if exp == []:
                return ['PUSH []']
            else:
                # Recursively quote list elements
                code = []
                for elem in reversed(exp):
                    if isinstance(elem, list):
                        code.extend(compile_expr(['quote', elem], env))
                    else:
                        code.append(f'PUSH {elem}')
                # Build the list from elements
                code.append(f'LIST {len(exp)}')
                return code
        else:
            return [f'PUSH {exp}']
    
    elif expr[0] == 'if':  # (if test conseq alt)
        _, test, conseq, alt = expr
        test_code = compile_expr(test, env)
        true_code = compile_expr(conseq, env)
        false_code = compile_expr(alt, env)
        return test_code + [('IF', true_code, false_code)]
    
    elif expr[0] == 'lambda':  # (lambda (var) body)
        _, vars, body = expr
        if not isinstance(vars, list):
            vars = [vars]
        body_code = compile_expr(body, env) + ['RET']
        return [('CLOSURE', body_code, tuple(vars))]
    
    elif expr[0] == 'define':  # (define var exp)
        _, var, exp = expr
        # Simple approach: compile expression and store it
        # The key insight: when the lambda is stored, its environment
        # already contains the variable because STORE updates the current env
        # Then when we LOAD it later, the closure's env will have the binding
        exp_code = compile_expr(exp, env)
        return exp_code + [f'STORE {var}', f'LOAD {var}']
    
    elif expr[0] == 'begin':  # (begin exp*)
        code = []
        for i, e in enumerate(expr[1:]):
            code.extend(compile_expr(e, env))
            # Pop intermediate values except for the last expression
            if i < len(expr[1:]) - 1:
                code.append('POP')
        return code
    
    # List operations
    elif expr[0] == 'car':
        _, e = expr
        return compile_expr(e, env) + ['CAR']
    
    elif expr[0] == 'cdr':
        _, e = expr
        return compile_expr(e, env) + ['CDR']
    
    elif expr[0] == 'cons':
        _, e1, e2 = expr
        return compile_expr(e1, env) + compile_expr(e2, env) + ['CONS']
    
    elif expr[0] == 'null?':
        _, e = expr
        return compile_expr(e, env) + ['NULL?']
    
    elif expr[0] == 'atom?':
        _, e = expr
        return compile_expr(e, env) + ['ATOM?']
    
    # Arithmetic
    elif expr[0] == '+':
        _, *args = expr
        code = compile_expr(args[0], env)
        for arg in args[1:]:
            code.extend(compile_expr(arg, env))
            code.append('ADD')
        return code
    
    elif expr[0] == '-':
        _, a, b = expr
        return compile_expr(a, env) + compile_expr(b, env) + ['SUB']
    
    elif expr[0] == '*':
        _, *args = expr
        code = compile_expr(args[0], env)
        for arg in args[1:]:
            code.extend(compile_expr(arg, env))
            code.append('MUL')
        return code
    
    elif expr[0] == '/':
        _, a, b = expr
        return compile_expr(a, env) + compile_expr(b, env) + ['DIV']
    
    # Comparisons
    elif expr[0] == '>':
        _, a, b = expr
        return compile_expr(a, env) + compile_expr(b, env) + ['GT']
    
    elif expr[0] == '<':
        _, a, b = expr
        return compile_expr(a, env) + compile_expr(b, env) + ['LT']
    
    elif expr[0] == '>=':
        _, a, b = expr
        return compile_expr(a, env) + compile_expr(b, env) + ['GTE']
    
    elif expr[0] == '<=':
        _, a, b = expr
        return compile_expr(a, env) + compile_expr(b, env) + ['LTE']
    
    elif expr[0] == '=':
        _, a, b = expr
        return compile_expr(a, env) + compile_expr(b, env) + ['EQ']
    
    else:  # (proc exp*) - function application
        code = compile_expr(expr[0], env)
        for arg in expr[1:]:
            code.extend(compile_expr(arg, env))
        code.append(f'CALL {len(expr) - 1}')
        return code



def parse(s):
    "Parse a Lisp expression from a string."
    return read_from(tokenize(s))

def tokenize(s):
    "Convert a string into a list of tokens."
    # Remove comments (everything after semicolon)
    if ';' in s:
        s = s[:s.index(';')]
    return s.replace("(", " ( ").replace(")", " ) ").split()

def read_from(tokens):
    "Read an expression from a sequence of tokens."
    if len(tokens) == 0:
        raise SyntaxError('unexpected EOF while reading')
    token = tokens.pop(0)
    if '(' == token:
        L = []
        while tokens[0] != ')':
            L.append(read_from(tokens))
        tokens.pop(0)  # pop off ')'
        return L
    elif ')' == token:
        raise SyntaxError('unexpected )')
    else:
        return atom(token)

def atom(token):
    "Numbers become numbers; every other token is a symbol."
    try:
        return int(token)
    except ValueError:
        try:
            return float(token)
        except ValueError:
            return Symbol(token)

def to_string(exp):
    "Convert a Python object back into a Lisp-readable string."
    if isinstance(exp, bool):
        return 'True' if exp else 'False'
    elif not isinstance(exp, list):
        return str(exp)
    else:
        return '(' + ' '.join(map(to_string, exp)) + ')'



def eval_expr(expr, env=None, debug=False):
    "Evaluate a Lisp expression by compiling and running it."
    if env is None:
        env = global_env
    code = compile_expr(expr, env)
    vm = VM(env, debug)
    return vm.run(code)



def add_globals(env):
    "Add some built-in procedures and variables to the environment."
    env.update({'True': True, 'False': False})
    return env

global_env = add_globals(Env())



def repl(prompt='vm> ', debug=False):
    "A prompt-read-eval-print loop."
    env = global_env
    while True:
        try:
            user_input = input(prompt)
            if user_input.strip() == '':
                continue
            if user_input.strip() == ':debug':
                debug = not debug
                print(f"Debug mode: {'ON' if debug else 'OFF'}")
                continue
            val = eval_expr(parse(user_input), env, debug)
            if val is not None:
                print(to_string(val))
        except KeyboardInterrupt:
            print("\nExiting tidyvm\n")
            sys.exit()
        except EOFError:
            print("\nExiting tidyvm\n")
            sys.exit()
        except:
            handle_error()



def load(filename, debug=False, repl_after=False):
    "Load and execute a tidyvm program from a file."
    print(f"Loading and executing {filename}")
    with open(filename, "r") as f:
        program = f.readlines()
    
    rps = running_paren_sums(program)
    full_line = ""
    env = global_env
    
    for (paren_sum, program_line) in zip(rps, program):
        program_line = program_line.strip()
        # Skip empty lines and comments
        if not program_line or program_line.startswith(';'):
            continue
        full_line += program_line + " "
        if paren_sum == 0 and full_line.strip() != "":
            try:
                val = eval_expr(parse(full_line), env, debug)
                if val is not None:
                    print(to_string(val))
            except:
                handle_error()
                print(f"\nThe line in which the error occurred:\n{full_line}")
                break
            full_line = ""
    
    if repl_after:
        repl(debug=debug)

def running_paren_sums(program):
    "Track running sum of parenthesis balance."
    count_open_parens = lambda line: line.count("(") - line.count(")")
    paren_counts = list(map(count_open_parens, program))
    rps = []
    total = 0
    for paren_count in paren_counts:
        total += paren_count
        rps.append(total)
    return rps



def handle_error():
    "Simple error handling for both the repl and load."
    print("An error occurred. Here's the Python stack trace:\n")
    traceback.print_exc()



if __name__ == "__main__":
    print("tidyVM - A stack-based Lisp")
    print("Type :debug to toggle debug mode")
    print()
    
    if len(sys.argv) > 1:
        # Check if user wants REPL after loading
        repl_after = '--repl' in sys.argv or '-i' in sys.argv
        load(sys.argv[1], repl_after=repl_after)
    else:
        repl()
