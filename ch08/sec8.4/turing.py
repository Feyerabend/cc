from collections import defaultdict

BLANK = '_'
LEFT, RIGHT, STAY = -1, 1, 0
HALT = -1


class TuringMachine:
    def __init__(self, rules, initial, tape_input=''):
        self.tape = {}
        for i, sym in enumerate(tape_input):
            self.tape[i] = sym
        self.head = 0
        self.state = initial
        # rules: {(state, read_sym): (write_sym, direction, next_state)}
        self.rules = rules

    def step(self):
        sym = self.tape.get(self.head, BLANK)
        action = self.rules.get((self.state, sym))
        if action is None:
            return False
        write, move, next_state = action
        if write == BLANK:
            self.tape.pop(self.head, None)
        else:
            self.tape[self.head] = write
        self.head += move
        self.state = next_state
        return True

    def run(self, max_steps=100_000):
        steps = 0
        while self.state != HALT and steps < max_steps:
            if not self.step():
                break
            steps += 1
        return steps

    def read_tape(self):
        if not self.tape:
            return BLANK
        lo, hi = min(self.tape), max(self.tape)
        s = ''.join(self.tape.get(i, BLANK) for i in range(lo, hi + 1))
        return s.strip(BLANK) or BLANK

    def snapshot(self):
        if not self.tape:
            return f'[{BLANK}]'
        lo, hi = min(self.tape), max(self.tape)
        parts = []
        for i in range(lo, hi + 1):
            c = self.tape.get(i, BLANK)
            parts.append(f'[{c}]' if i == self.head else f' {c} ')
        return ''.join(parts)


# Binary increment machine
# State 0: scan right to find the blank marking the end of input
# State 1: scan left, propagating carry (like adding 1 by hand)
rules = {
    (0, '0'):   ('0',   RIGHT, 0),
    (0, '1'):   ('1',   RIGHT, 0),
    (0, BLANK): (BLANK, LEFT,  1),    # reached end; begin carry phase
    (1, '1'):   ('0',   LEFT,  1),    # 1 + carry = 10; write 0, carry on
    (1, '0'):   ('1',   STAY,  HALT), # 0 + carry = 1; done
    (1, BLANK): ('1',   STAY,  HALT), # overflow: write leading 1
}

if __name__ == '__main__':
    examples = ['0', '1', '101', '1011', '111', '1111']

    print(f"{'Input':>8}  {'Dec':>4}   {'Output':<8}  {'Dec':>4}   Steps")
    print(f"{'-----':>8}  {'---':>4}   {'------':<8}  {'---':>4}   -----")

    for inp in examples:
        tm = TuringMachine(rules, initial=0, tape_input=inp)
        steps = tm.run()
        result = tm.read_tape()
        dec_in = int(inp, 2)
        dec_out = int(result, 2) if set(result) <= {'0', '1'} else 0
        print(f'{inp:>8}  {dec_in:>4}   {result:<8}  {dec_out:>4}   {steps}')
