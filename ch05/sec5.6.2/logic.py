class LogicSymbolTable:
    def __init__(self):
        self.bindings = {}
        self.facts = []
    
    def add_fact(self, fact):
        """Add a fact to the knowledge base"""
        self.facts.append(fact)
    
    def bind(self, var, value):
        if var in self.bindings:
            return self.unify(self.bindings[var], value)
        self.bindings[var] = value
        return True
    
    def lookup(self, var):
        if var not in self.bindings:
            return var
        value = self.bindings[var]
        if isinstance(value, str) and value in self.bindings:
            return self.lookup(value)
        return value
    
    def unify(self, term1, term2):
        term1 = self.lookup(term1) if isinstance(term1, str) else term1
        term2 = self.lookup(term2) if isinstance(term2, str) else term2
        
        if term1 == term2:
            return True
        
        if isinstance(term1, str) and term1 not in self.bindings:
            self.bindings[term1] = term2
            return True
        
        if isinstance(term2, str) and term2 not in self.bindings:
            self.bindings[term2] = term1
            return True
        
        ## Handle compound terms like parent(tom, bob)
        if isinstance(term1, tuple) and isinstance(term2, tuple):
            if len(term1) != len(term2):
                return False
            return all(self.unify(t1, t2) for t1, t2 in zip(term1, term2))
        
        return False
    
    def query(self, pattern):
        """Find all facts that unify with the pattern"""
        solutions = []
        
        for fact in self.facts:
            ## Create a fresh copy of bindings for each attempt
            saved_bindings = self.bindings.copy()
            
            if self.unify(pattern, fact):
                ## Found a solution - record the bindings
                solution = {k: self.lookup(k) for k in self.bindings 
                           if isinstance(k, str) and k.isupper()}
                solutions.append(solution)
            
            ## Restore bindings for next attempt (backtracking)
            self.bindings = saved_bindings
        
        return solutions
    
    def display(self):
        print("Knowledge Base:")
        for fact in self.facts:
            print(f"  {fact}")
        print("\nCurrent Bindings:")
        for var, value in self.bindings.items():
            print(f"  {var} = {self.lookup(var)}")

## Example: Family relationships
## Facts: parent(tom, bob), parent(tom, liz), parent(bob, ann)

kb = LogicSymbolTable()
kb.add_fact(('parent', 'tom', 'bob'))
kb.add_fact(('parent', 'tom', 'liz'))
kb.add_fact(('parent', 'bob', 'ann'))

## Query: parent(tom, X)? (Who are tom's children?)
print("Query: parent(tom, X)?")
results = kb.query(('parent', 'tom', 'X'))
for result in results:
    print(f"  Solution: {result}")

## Query: parent(X, ann)? (Who is ann's parent?)
print("\nQuery: parent(X, ann)?")
results = kb.query(('parent', 'X', 'ann'))
for result in results:
    print(f"  Solution: {result}")
