class WAM:
    def __init__(self):
        self.registers = {
            'IP': 0,    # instruction pointer
            'CP': 0,    # current predicate
            'HP': 0,    # heap pointer
        }
        self.heap = []          # term storage
        self.stack = []         # execution stack
        self.call_stack = []    # procedure return addresses
        self.choice_points = [] # backtrack points
        self.instructions = []  # loaded program
        self.predicates = {}    # predicate table
        self.constants = {}     # constant table
        self.variables = {}     # variable table
        self.trail = []         # trail for variable bindings (for backtracking)
        self.solutions = []     # store found solutions

    def load(self, compiler):
        self.instructions = compiler.instructions
        self.predicates = compiler.predicates
        self.constants = {v:k for k,v in compiler.constants.items()}
        self.variables = compiler.vars
        self.heap = [None] * (len(compiler.vars) + len(compiler.constants) + 10)  # +10 buffer

    def create_choice_point(self, alternatives):
        """Create a choice point for backtracking"""
        choice_point = {
            'IP': self.registers['IP'],
            'stack': self.stack.copy(),
            'heap': self.heap.copy(),
            'trail': self.trail.copy(),
            'call_stack': self.call_stack.copy(),
            'alternatives': alternatives,
            'next_alternative': 0
        }
        self.choice_points.append(choice_point)
        return len(self.choice_points) - 1  # Return index of the new choice point

    def backtrack(self):
        """Backtrack to the last choice point"""
        if not self.choice_points:
            return False  # No more choice points, fail
        
        choice_point = self.choice_points[-1]
        
        # Try the next alternative
        if choice_point['next_alternative'] >= len(choice_point['alternatives']):
            # No more alternatives, backtrack to previous choice point
            self.choice_points.pop()
            return self.backtrack()
        
        # Restore state
        self.registers['IP'] = choice_point['alternatives'][choice_point['next_alternative']]
        choice_point['next_alternative'] += 1  # Move to next alternative for future backtracking
        self.stack = choice_point['stack'].copy()
        self.heap = choice_point['heap'].copy()
        self.trail = choice_point['trail'].copy()
        self.call_stack = choice_point['call_stack'].copy()
        
        return True  # Successfully backtracked

    def unify(self, term1, term2):
        """Unify two terms, return True if successful"""
        # Dereference terms to their values
        term1_val = self.deref(term1)
        term2_val = self.deref(term2)
        
        # If both are references to unbound variables
        if term1_val[0] == 'REF' and term2_val[0] == 'REF':
            if term1_val[1] == term2_val[1]:  # Same variable
                return True
            # Bind one variable to another
            self.bind(term1_val[1], term2_val)
            return True
        
        # If term1 is an unbound variable
        if term1_val[0] == 'REF':
            self.bind(term1_val[1], term2_val)
            return True
        
        # If term2 is an unbound variable
        if term2_val[0] == 'REF':
            self.bind(term2_val[1], term1_val)
            return True
        
        # If both are constants
        if term1_val[0] == 'CONST' and term2_val[0] == 'CONST':
            return term1_val[1] == term2_val[1]
        
        # If neither match, unification fails
        return False

    def deref(self, term):
        """Dereference a term to find its value"""
        if isinstance(term, tuple) and term[0] == 'REF':
            # Find the actual value by following reference chain
            addr = term[1]
            while isinstance(self.heap[addr], tuple) and self.heap[addr][0] == 'REF' and self.heap[addr][1] != addr:
                addr = self.heap[addr][1]
            return self.heap[addr] if self.heap[addr] is not None else ('REF', addr)
        return term

    def bind(self, var_addr, value):
        """Bind a variable to a value and record in trail for backtracking"""
        self.trail.append((var_addr, self.heap[var_addr]))
        self.heap[var_addr] = value

    def fetch_execute(self, find_all=False):
        try:
            while self.registers['IP'] < len(self.instructions):
                instr = self.instructions[self.registers['IP']]
                op, arg1, arg2 = instr
                current_ip = self.registers['IP']
                self.registers['IP'] += 1
                
                # tracing
                print(f"\n[{current_ip}] {op} {arg1} {arg2 if arg2 else ''}")
                print(f"Registers: {self.registers}")
                print(f"Stack: {self.stack}")
                print(f"Heap: {[x for x in self.heap if x is not None]}")
                print(f"Call Stack: {self.call_stack}")
                print(f"Choice Points: {len(self.choice_points)}")

                if op == 'CALL':
                    pred_name, arity = arg1
                    # Check if predicate exists
                    if (pred_name, arity) in self.predicates:
                        # Create a choice point if there are multiple clauses
                        if isinstance(self.predicates[(pred_name, arity)], list):
                            # Multiple clause addresses
                            clause_addrs = self.predicates[(pred_name, arity)]
                            self.create_choice_point(clause_addrs)
                            self.registers['IP'] = clause_addrs[0]  # Try first clause
                        else:
                            # Single clause address
                            self.call_stack.append(self.registers['IP'])
                            self.registers['IP'] = self.predicates[(pred_name, arity)]
                    else:
                        print(f"Predicate {pred_name}/{arity} not found")
                        if not self.backtrack():
                            break  # No more choice points
                elif op == 'TRY_ME_ELSE':
                    # First clause of multiple, next is at arg1
                    choice_point_idx = self.create_choice_point([arg1])
                elif op == 'RETRY_ME_ELSE':
                    # Middle clause of multiple, next is at arg1
                    if self.choice_points:
                        self.choice_points[-1]['alternatives'].append(arg1)
                elif op == 'TRUST_ME':
                    # Last clause of multiple, no next
                    pass
                elif op == 'PROCEED':
                    # End of a clause, return to caller
                    if self.call_stack:
                        self.registers['IP'] = self.call_stack.pop()
                    else:
                        # End of query, we found a solution
                        self.save_solution()
                        if find_all:
                            # Try to find more solutions
                            if not self.backtrack():
                                print("\nNo more solutions")
                                return
                        else:
                            print("\nExecution completed successfully")
                            return
                elif op == 'GET_VARIABLE':
                    # Push variable reference onto stack
                    self.stack.append(('REF', arg1))
                elif op == 'GET_CONSTANT':
                    # Push constant onto stack
                    self.stack.append(('CONST', self.constants[arg1]))
                elif op == 'PUT_CONSTANT':
                    # Store constant in heap
                    self.heap[arg1] = ('CONST', self.constants[arg2])
                elif op == 'PUT_VARIABLE':
                    # Initialize variable on heap
                    self.heap[arg1] = ('REF', arg1)
                elif op == 'UNIFY_VARIABLE':
                    # Try to unify top of stack with variable
                    term = self.stack.pop()
                    if not self.unify(('REF', arg1), term):
                        if not self.backtrack():
                            print("\nUnification failed, no more alternatives")
                            return False
                elif op == 'PUT_ANY':
                    # Store anonymous variable
                    self.heap[arg1] = ('REF', arg1)
                elif op == 'GET_ANY':
                    # Create a new reference for anonymous variable
                    new_addr = len(self.heap)
                    self.heap.append(('REF', new_addr))
                    self.stack.append(('REF', new_addr))
                elif op == 'CUT':
                    # Remove choice points created since arg1
                    self.choice_points = self.choice_points[:arg1]
                elif op == 'BUILTIN':
                    # Execute built-in predicate
                    if not self.execute_builtin(arg1):
                        if not self.backtrack():
                            break  # No more choice points
                elif op == 'HALT':
                    print("\nExecution completed successfully")
                    return True
                else:
                    raise ValueError(f"Unknown instruction: {op}")

        except Exception as e:
            print(f"\nERROR AT [{current_ip}] {instr}: {e}")
            raise

    def execute_builtin(self, builtin):
        if builtin == r'\=':
            right = self.stack.pop()
            left = self.stack.pop()
            # Dereference before comparison
            left_val = self.deref(left)
            right_val = self.deref(right)
            
            if left_val[0] == 'REF' or right_val[0] == 'REF':
                # One is an unbound variable, can't determine equality yet
                return False
            
            if left_val == right_val:
                # Values are equal, which means inequality fails
                return False
            return True
        else:
            raise ValueError(f"Unknown built-in predicate: {builtin}")

    def save_solution(self):
        """Save the current variable bindings as a solution"""
        solution = {}
        for var_name, var_idx in self.variables.items():
            # Skip system variables and anonymous variables
            if var_name != '_' and var_name[0].isupper():
                solution[var_name] = self.pretty_print_term(('REF', var_idx))
        self.solutions.append(solution)
        print(f"\nSolution found: {solution}")

    def pretty_print_term(self, term):
        """Print a term in a readable format"""
        term_val = self.deref(term)
        if term_val[0] == 'REF':
            return f"_{term_val[1]}"  # Unbound variable
        elif term_val[0] == 'CONST':
            return term_val[1]  # Constant
        return str(term_val)  # Default case


class Compiler:
    def __init__(self):
        self.vars = {}        # maps variables (VARIABLES) to indices
        self.constants = {}   # maps constants (lowercase) to indices
        self.predicates = {}  # maps predicates to code addresses
        self.instructions = []
        self.pred_clauses = {} # maps predicates to lists of clauses for multi-clause compilation

        # register built-in predicates
        self.builtins = {r'\=': self.compile_inequality}

    def compile_inequality(self, args):
        left, right = args

        if left[0].isupper():  # variable, X, Y, etc.
            self.instructions.append(('GET_VARIABLE', self.vars[left], 0))
        else:  # constant, a, b, etc.
            self.instructions.append(('GET_CONSTANT', self.constants[left], 0))
        
        if right[0].isupper():
            self.instructions.append(('GET_VARIABLE', self.vars[right], 0))
        else:
            self.instructions.append(('GET_CONSTANT', self.constants[right], 0))
        
        self.instructions.append(('BUILTIN', r'\=', 0))

    # First collect all clauses, then compile them to handle multiple clauses per predicate
    def compile(self, clauses):
        # First pass: collect clauses by predicate
        for clause in clauses:
            if clause[0] == ':-':
                head = clause[1]
                pred_name, pred_args = head[0], head[1:]
                pred_key = (pred_name, len(pred_args))
                if pred_key not in self.pred_clauses:
                    self.pred_clauses[pred_key] = []
                self.pred_clauses[pred_key].append(clause)
            elif clause[0] == '?-':
                # Queries are handled separately
                pass
            else:
                # Facts are single-clause predicates
                pred_name, pred_args = clause[0], clause[1:]
                pred_key = (pred_name, len(pred_args))
                if pred_key not in self.pred_clauses:
                    self.pred_clauses[pred_key] = []
                self.pred_clauses[pred_key].append(clause)
        
        # Second pass: compile predicates with multiple clauses
        for pred_key, pred_clauses in self.pred_clauses.items():
            if len(pred_clauses) > 1:
                self.compile_multi_clause_predicate(pred_key, pred_clauses)
            else:
                # Single clause predicate
                clause = pred_clauses[0]
                if clause[0] == ':-':
                    self.compile_rule(clause[1], clause[2:])
                else:
                    self.compile_fact(clause)
        
        # Compile queries last
        for clause in clauses:
            if clause[0] == '?-':
                self.compile_query(clause[1])
        
        # HALT at the end
        self.instructions.append(('HALT', 0, 0))

    def compile_multi_clause_predicate(self, pred_key, clauses):
        """Compile a predicate with multiple clauses using TRY/RETRY/TRUST instructions"""
        pred_name, arity = pred_key
        clause_addrs = []
        
        print(f"\nCompiling multi-clause predicate {pred_name}/{arity} with {len(clauses)} clauses")
        
        # Store the predicate entry point
        self.predicates[pred_key] = len(self.instructions)
        
        # TRY_ME_ELSE points to the next clause
        for i in range(len(clauses) - 1):
            # Record where this clause begins
            clause_addr = len(self.instructions)
            clause_addrs.append(clause_addr)
            
            # The next clause will be at the end of the current instructions plus this clause's instructions
            next_clause_addr = None  # Will be filled in after compiling this clause
            
            if i == 0:
                self.instructions.append(('TRY_ME_ELSE', next_clause_addr, 0))
            else:
                self.instructions.append(('RETRY_ME_ELSE', next_clause_addr, 0))
                
            # Compile the clause body
            clause = clauses[i]
            if clause[0] == ':-':
                self.compile_rule_body(clause[1], clause[2:], updating_addrs=True)
            else:
                self.compile_fact_body(clause, updating_addrs=True)
            
            # Now update the next_clause_addr in the TRY/RETRY instruction
            next_clause_addr = len(self.instructions)
            self.instructions[clause_addr] = (self.instructions[clause_addr][0], next_clause_addr, 0)
        
        # Last clause uses TRUST_ME
        clause_addr = len(self.instructions)
        clause_addrs.append(clause_addr)
        self.instructions.append(('TRUST_ME', 0, 0))
        
        # Compile the last clause
        clause = clauses[-1]
        if clause[0] == ':-':
            self.compile_rule_body(clause[1], clause[2:], updating_addrs=True)
        else:
            self.compile_fact_body(clause, updating_addrs=True)

    def compile_rule_body(self, head, body, updating_addrs=False):
        """Compile just the body of a rule, without creating a new predicate entry"""
        pred_name, pred_args = head[0], head[1:]
        
        if not updating_addrs:
            print(f"\nCompiling rule body {pred_name}/{len(pred_args)}")
        
        # Register all variables from the head
        for arg in pred_args:
            if arg != '_' and arg not in self.vars and arg[0].isupper():
                self.vars[arg] = len(self.vars)
                print(f"  Variable {arg} => v{self.vars[arg]}")

        # Register all variables from the body
        for goal in body:
            if isinstance(goal, list):  # skip cut operator '!'
                for arg in goal[1:]:   # skip the functor
                    if arg != '_' and arg not in self.vars and arg[0].isupper():
                        self.vars[arg] = len(self.vars)
                        print(f"  Variable {arg} => v{self.vars[arg]}")

        # Compile body
        for goal in body:
            if goal == '!':
                print("  Compiling cut")
                self.instructions.append(('CUT', len(self.vars), 0))
            elif isinstance(goal, list) and goal[0] in self.builtins:
                print(f"  Compiling built-in {goal[0]}")
                # built-in predicates
                self.builtins[goal[0]](goal[1:])
            else:
                self.compile_goal(goal)

        self.instructions.append(('PROCEED', 0, 0))

    def compile_rule(self, head, body):
        pred_name, pred_args = head[0], head[1:]
        arity = len(pred_args)
        self.predicates[(pred_name, arity)] = len(self.instructions)
        
        print(f"\nCompiling rule {pred_name}/{arity}")
        
        self.compile_rule_body(head, body)

    def compile_fact_body(self, fact, updating_addrs=False):
        """Compile just the body of a fact, without creating a new predicate entry"""
        pred_name, pred_args = fact[0], fact[1:]
        
        if not updating_addrs:
            print(f"\nCompiling fact body {pred_name}/{len(pred_args)}")
        
        for i, arg in enumerate(pred_args):
            if arg == '_':
                self.instructions.append(('PUT_ANY', i, 0))
            elif isinstance(arg, str) and arg[0].islower():
                if arg not in self.constants:
                    self.constants[arg] = len(self.constants)
                    print(f"  Constant {arg} => c{self.constants[arg]}")
                self.instructions.append(('PUT_CONSTANT', i, self.constants[arg]))
            else:
                if arg not in self.vars:
                    self.vars[arg] = len(self.vars)
                    print(f"  Variable {arg} => v{self.vars[arg]}")
                self.instructions.append(('PUT_VARIABLE', self.vars[arg], 0))

        self.instructions.append(('PROCEED', 0, 0))

    def compile_fact(self, fact):
        pred_name, pred_args = fact[0], fact[1:]
        arity = len(pred_args)
        self.predicates[(pred_name, arity)] = len(self.instructions)
        
        print(f"\nCompiling fact {pred_name}/{arity}")
        
        self.compile_fact_body(fact)

    def compile_goal(self, goal):
        pred_name, pred_args = goal[0], goal[1:]
        arity = len(pred_args)
        
        print(f"  Compiling goal {pred_name}/{arity}")
        
        for arg in pred_args:
            if arg == '_':
                self.instructions.append(('GET_ANY', 0, 0))
            elif isinstance(arg, str) and arg[0].islower():
                if arg not in self.constants:
                    self.constants[arg] = len(self.constants)
                    print(f"  Constant {arg} => c{self.constants[arg]}")
                self.instructions.append(('GET_CONSTANT', self.constants[arg], 0))
            else:
                self.instructions.append(('GET_VARIABLE', self.vars[arg], 0))
        
        self.instructions.append(('CALL', (pred_name, arity), 0))

    def compile_query(self, query):
        print(f"\nCompiling query: {query}")
        
        # Register variables in the query
        for arg in query[1:]:  # skip the functor
            if arg != '_' and arg not in self.vars and arg[0].isupper():
                self.vars[arg] = len(self.vars)
                print(f"  Variable {arg} => v{self.vars[arg]}")

        # Compile the query as a goal
        self.compile_goal(query)


program = [
    ['parent', 'zeb', 'john'],
    ['parent', 'zeb', 'jane'],
    ['parent', 'john', 'jim'],
    ['parent', 'jane', 'alice'],
    [':-', ['child', 'X'], ['parent', 'X', '_'], '!'],
    [':-', ['grandparent', 'X', 'Z'], ['parent', 'X', 'Y'], ['parent', 'Y', 'Z']],
    [':-', ['sibling', 'X', 'Y'], ['parent', 'Z', 'X'], ['parent', 'Z', 'Y'], [r'\=', 'X', 'Y']],
    ['?-', ['child', 'X']],
    ['?-', ['grandparent', 'zeb', 'Who']],
    ['?-', ['sibling', 'john', 'Sibling']]
]


print("=== COMPILATION ===")
compiler = Compiler()
compiler.compile(program)

print("\n=== COMPILATION RESULTS ===")
print(f"Variables: {compiler.vars}")
print(f"Constants: {compiler.constants}")
print(f"Predicates: {compiler.predicates}")
print("\nGenerated Code:")
for addr, instr in enumerate(compiler.instructions):
    print(f"{addr:3d}: {instr}")

print("\n=== EXECUTION ===")
vm = WAM()
vm.load(compiler)

print("Starting execution with child(X)...")
try:
    # init call stack with HALT
    vm.call_stack.append(len(vm.instructions)-1)  # address of HALT
    # start execution at child/1
    vm.registers['IP'] = vm.predicates[('child', 1)]
    vm.fetch_execute(find_all=True)  # Set to True to find all solutions
    
    print("\nFound solutions:", vm.solutions)
    
    # Try the next query: grandparent(zeb, Who)
    print("\nStarting execution with grandparent(zeb, Who)...")
    vm = WAM()  # Create a new VM instance
    vm.load(compiler)
    vm.call_stack.append(len(vm.instructions)-1)  # address of HALT
    vm.registers['IP'] = vm.predicates[('grandparent', 2)]
    vm.fetch_execute(find_all=True)
    
    print("\nFound solutions:", vm.solutions)
    
    # Try the next query: sibling(john, Sibling)
    print("\nStarting execution with sibling(john, Sibling)...")
    vm = WAM()  # Create a new VM instance
    vm.load(compiler)
    vm.call_stack.append(len(vm.instructions)-1)  # address of HALT
    vm.registers['IP'] = vm.predicates[('sibling', 2)]
    vm.fetch_execute(find_all=True)
    
    print("\nFound solutions:", vm.solutions)
    
except Exception as e:
    print(f"Execution failed: {e}")