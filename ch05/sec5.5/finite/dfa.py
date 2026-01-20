class DFA:    
    def __init__(self, states, alphabet, transitions, start_state, final_states):
        self.states = states # set of states
        self.alphabet = alphabet # set of input symbols
        self.transitions = transitions # transition function
        self.start_state = start_state # initial state
        self.final_states = final_states # set of accepting states
    
    def simulate(self, input_string, verbose=False):
        current_state = self.start_state
        
        if verbose:
            print(f"Starting in state: {current_state}")
        
        for i, symbol in enumerate(input_string):
            if symbol not in self.alphabet:
                if verbose:
                    print(f"Invalid symbol: {symbol}")
                return False
            
            # Get next state
            if (current_state, symbol) not in self.transitions:
                if verbose:
                    print(f"No transition from {current_state} on '{symbol}'")
                return False
            
            next_state = self.transitions[(current_state, symbol)]
            
            if verbose:
                print(f"  Step {i+1}: {current_state} --({symbol})--> {next_state}")
            
            current_state = next_state
        
        is_accepted = current_state in self.final_states
        if verbose:
            print(f"Final state: {current_state} ({'ACCEPTING' if is_accepted else 'REJECTING'})")
        
        return is_accepted


class NFA:
    def __init__(self, states, alphabet, transitions, start_state, final_states):
        self.states = states # set of states
        self.alphabet = alphabet # set of input symbols
        self.transitions = transitions # dictionary of transitions {(state, symbol): set of next states}
        self.start_state = start_state # initial state
        self.final_states = final_states # set of accepting states
    
    def epsilon_closure(self, states):
        closure = set(states)
        stack = list(states)
        
        while stack:
            state = stack.pop()
            # Check for epsilon transitions
            if (state, '') in self.transitions:
                for next_state in self.transitions[(state, '')]:
                    if next_state not in closure:
                        closure.add(next_state)
                        stack.append(next_state)
        
        return closure
    
    def simulate(self, input_string, verbose=False):
        current_states = self.epsilon_closure({self.start_state})
        
        if verbose:
            print(f"Starting states: {current_states}")
        
        for i, symbol in enumerate(input_string):
            if symbol not in self.alphabet:
                if verbose:
                    print(f"Invalid symbol: {symbol}")
                return False
            
            next_states = set()
            
            # For each current state, find all possible next states
            for state in current_states:
                if (state, symbol) in self.transitions:
                    next_states.update(self.transitions[(state, symbol)])
            
            # Apply epsilon closure
            current_states = self.epsilon_closure(next_states)
            
            if verbose:
                print(f"  Step {i+1}: on '{symbol}' -> {current_states}")
            
            if not current_states:
                if verbose:
                    print("No valid states remaining")
                return False
        
        # Check if any current state is accepting
        is_accepted = bool(current_states & self.final_states)
        
        if verbose:
            print(f"Final states: {current_states}")
            print(f"Result: {'ACCEPTED' if is_accepted else 'REJECTED'}")
        
        return is_accepted


# Example DFAs

# DFA 1: Strings ending with "ab"
def create_ends_with_ab():
    states = {'q0', 'q1', 'q2'}
    alphabet = {'a', 'b'}
    transitions = {
        ('q0', 'a'): 'q1',
        ('q0', 'b'): 'q0',
        ('q1', 'a'): 'q1',
        ('q1', 'b'): 'q2',
        ('q2', 'a'): 'q1',
        ('q2', 'b'): 'q0',
    }
    start_state = 'q0'
    final_states = {'q2'}
    
    return DFA(states, alphabet, transitions, start_state, final_states)

# DFA 2: Even number of a'
def create_even_as():
    states = {'even', 'odd'}
    alphabet = {'a', 'b'}
    transitions = {
        ('even', 'a'): 'odd',
        ('even', 'b'): 'even',
        ('odd', 'a'): 'even',
        ('odd', 'b'): 'odd',
    }
    start_state = 'even'
    final_states = {'even'}
    
    return DFA(states, alphabet, transitions, start_state, final_states)

# DFA 3: Strings containing '101' as substring
def create_contains_substring():
    states = {'q0', 'q1', 'q2', 'q3'}
    alphabet = {'0', '1'}
    transitions = {
        ('q0', '0'): 'q0',
        ('q0', '1'): 'q1',
        ('q1', '0'): 'q2',
        ('q1', '1'): 'q1',
        ('q2', '0'): 'q0',
        ('q2', '1'): 'q3',
        ('q3', '0'): 'q3',
        ('q3', '1'): 'q3',
    }
    start_state = 'q0'
    final_states = {'q3'}
    
    return DFA(states, alphabet, transitions, start_state, final_states)


# Example NFAs

# NFA 1: Strings ending with "01" or "10"
def create_nfa_ends_with_01_or_10():
    states = {'q0', 'q1', 'q2', 'q3', 'q4'}
    alphabet = {'0', '1'}
    transitions = {
        ('q0', '0'): {'q0', 'q1'},  # Stay or start pattern "0_"
        ('q0', '1'): {'q0', 'q3'},  # Stay or start pattern "1_"
        ('q1', '1'): {'q2'},        # Complete "01"
        ('q3', '0'): {'q4'},        # Complete "10"
    }
    start_state = 'q0'
    final_states = {'q2', 'q4'}
    
    return NFA(states, alphabet, transitions, start_state, final_states)

# NFA 2: With epsilon transitions for (a|b)*abb
def create_nfa_with_epsilon():
    states = {'q0', 'q1', 'q2', 'q3', 'q4'}
    alphabet = {'a', 'b'}
    transitions = {
        ('q0', ''): {'q1'},      # Epsilon to main path
        ('q0', 'a'): {'q0'},     # Loop on 'a'
        ('q0', 'b'): {'q0'},     # Loop on 'b'
        ('q1', 'a'): {'q2'},     # Start "abb"
        ('q2', 'b'): {'q3'},     # Second char
        ('q3', 'b'): {'q4'},     # Complete "abb"
    }
    start_state = 'q0'
    final_states = {'q4'}
    
    return NFA(states, alphabet, transitions, start_state, final_states)

# Testing framework
def test_automaton(name, automaton, test_cases):
    print(f"\nTesting: {name}\n")
    
    for test in test_cases:
        print(f"\nInput: '{test}'")
        result = automaton.simulate(test, verbose=True)
        print(f"{'ACCEPTED' if result else 'REJECTED'}")


def main():
    print("Finite Automata Testing Framework\n")
    
    # Test DFA 1: Ends with "ab"
    dfa1 = create_ends_with_ab()
    test_automaton(
        "DFA: Strings ending in 'ab'",
        dfa1,
        ["ab", "aab", "bab", "abab", "ba", "aa"]
    )
    
    # Test DFA 2: Even number of a's
    dfa2 = create_even_as()
    test_automaton(
        "DFA: Even number of 'a's",
        dfa2,
        ["", "aa", "aaa", "aaaa", "bbb", "abab"]
    )
    
    # Test DFA 3: Contains "101"
    dfa3 = create_contains_substring()
    test_automaton(
        "DFA: Contains substring '101'",
        dfa3,
        ["101", "0101", "1010", "11011", "000", "111"]
    )
    
    # Test NFA 1: Ends with "01" or "10"
    nfa1 = create_nfa_ends_with_01_or_10()
    test_automaton(
        "NFA: Ends with '01' or '10'",
        nfa1,
        ["01", "10", "001", "110", "0101", "00", "11"]
    )
    
    # Test NFA 2: With epsilon transitions
    nfa2 = create_nfa_with_epsilon()
    test_automaton(
        "NFA: Strings ending in 'abb' (with ε-transitions)",
        nfa2,
        ["abb", "aabb", "babb", "ababb", "ab", "bb"]
    )


if __name__ == "__main__":
    main()
