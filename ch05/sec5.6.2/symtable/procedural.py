class SymbolTable:
    def __init__(self):
        self.scopes = [{}]
        self.scope_level = 0
    
    def enter_scope(self):
        self.scopes.append({})
        self.scope_level += 1
    
    def exit_scope(self):
        if len(self.scopes) > 1:
            self.scopes.pop()
            self.scope_level -= 1
        else:
            raise RuntimeError("Cannot exit global scope")
    
    def insert(self, name, info):
        if name in self.scopes[-1]:
            raise RuntimeError(f"Symbol '{name}' already defined in current scope")
        self.scopes[-1][name] = info
    
    def lookup(self, name):
        for scope in reversed(self.scopes):
            if name in scope:
                return scope[name]
        return None
    
    def display(self):
        for i, scope in enumerate(self.scopes):
            print(f"\nScope Level {i}:")
            for name, info in scope.items():
                print(f"  {name}: {info}")

## Helper functions
def create_variable_entry(var_type, scope_level, value=None, is_const=False):
    return {
        'kind': 'variable',
        'type': var_type,
        'scope': scope_level,
        'value': value,
        'const': is_const
    }

def create_function_entry(return_type, parameters, scope_level):
    return {
        'kind': 'function',
        'return_type': return_type,
        'parameters': parameters,
        'scope': scope_level
    }

## Example: Simulating this program
## int x = 10;
## int add(int a, int b) {
##     int result = a + b;
##     return result;
## }

st = SymbolTable()

## Global scope
st.insert('x', create_variable_entry('int', 0, value=10))
st.insert('add', create_function_entry('int', [('int', 'a'), ('int', 'b')], 0))

## Enter function 'add' scope
st.enter_scope()
st.insert('a', create_variable_entry('int', 1, is_const=True))  ## parameter
st.insert('b', create_variable_entry('int', 1, is_const=True))  ## parameter
st.insert('result', create_variable_entry('int', 1))

st.display()
st.exit_scope()
