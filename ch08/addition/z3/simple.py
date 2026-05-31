from z3 import *

# Instruction opcodes
LOAD_A = 0
LOAD_B = 1
ADD    = 2
SUB    = 3
MUL    = 4
DIV    = 5
JNZ    = 6  # Jump if B != 0
HALT   = 7


class SymRegVM:
    """
    A minimal symbolic register-based virtual machine backed by the Z3 SMT solver.

    Each program state at time step t is represented as a tuple of Z3 integer
    variables (pc, A, B, Z, N). Instructions are encoded as constraints relating
    consecutive states, allowing Z3 to reason about all possible executions at once.
    """

    def __init__(self, program, max_steps=20):
        self.program   = program
        self.max_steps = max_steps

        self.s = Solver()

        # Symbolic state arrays: one variable per register per time step
        self.pc = [Int(f'pc_{t}') for t in range(max_steps + 1)]
        self.A  = [Int(f'A_{t}')  for t in range(max_steps + 1)]
        self.B  = [Int(f'B_{t}')  for t in range(max_steps + 1)]
        self.Z  = [Int(f'Z_{t}')  for t in range(max_steps + 1)]
        self.N  = [Int(f'N_{t}')  for t in range(max_steps + 1)]

        # Initial state: pc starts at 0, all registers and flags cleared
        self.s.add(self.pc[0] == 0)
        self.s.add(self.A[0]  == 0)
        self.s.add(self.B[0]  == 0)
        self.s.add(self.Z[0]  == 0)
        self.s.add(self.N[0]  == 0)

        self._add_step_constraints()

    def _add_step_constraints(self):
        for t in range(self.max_steps):
            pc_t = self.pc[t]
            A_t  = self.A[t]
            B_t  = self.B[t]
            Z_t  = self.Z[t]
            N_t  = self.N[t]

            # pc must be non-negative or equal to the halt sentinel -1
            self.s.add(Or(pc_t >= 0, pc_t == -1))

            # Once halted, all state remains frozen
            self.s.add(
                If(pc_t == -1,
                   And(
                       self.pc[t + 1] == -1,
                       self.A[t + 1]  == A_t,
                       self.B[t + 1]  == B_t,
                       self.Z[t + 1]  == Z_t,
                       self.N[t + 1]  == N_t
                   ),
                   self._step_constraints(t, pc_t, A_t, B_t, Z_t, N_t)
                )
            )

    def _step_constraints(self, t, pc_t, A_t, B_t, Z_t, N_t):
        """
        Build Z3 constraints for a single execution step. For each instruction in the
        program, an If-expression guards the corresponding state transition with the
        condition pc_t == <instruction index>.
        """
        cases = []

        for pc_val, (instr, operand) in enumerate(self.program):
            cond = (pc_t == pc_val)

            if instr == LOAD_A:
                cases.append(If(cond,
                    And(
                        self.pc[t + 1] == pc_t + 1,
                        self.A[t + 1]  == operand,
                        self.B[t + 1]  == B_t,
                        self.Z[t + 1]  == (operand == 0),
                        self.N[t + 1]  == (operand < 0)
                    ), True))

            elif instr == LOAD_B:
                cases.append(If(cond,
                    And(
                        self.pc[t + 1] == pc_t + 1,
                        self.A[t + 1]  == A_t,
                        self.B[t + 1]  == operand,
                        self.Z[t + 1]  == (operand == 0),
                        self.N[t + 1]  == (operand < 0)
                    ), True))

            elif instr == ADD:
                val = A_t + B_t
                cases.append(If(cond,
                    And(
                        self.pc[t + 1] == pc_t + 1,
                        self.A[t + 1]  == val,
                        self.B[t + 1]  == B_t,
                        self.Z[t + 1]  == (val == 0),
                        self.N[t + 1]  == (val < 0)
                    ), True))

            elif instr == SUB:
                val = A_t - B_t
                cases.append(If(cond,
                    And(
                        self.pc[t + 1] == pc_t + 1,
                        self.A[t + 1]  == val,
                        self.B[t + 1]  == B_t,
                        self.Z[t + 1]  == (val == 0),
                        self.N[t + 1]  == (val < 0)
                    ), True))

            elif instr == MUL:
                val = A_t * B_t
                cases.append(If(cond,
                    And(
                        self.pc[t + 1] == pc_t + 1,
                        self.A[t + 1]  == val,
                        self.B[t + 1]  == B_t,
                        self.Z[t + 1]  == (val == 0),
                        self.N[t + 1]  == (val < 0)
                    ), True))

            elif instr == DIV:
                # Guard against division by zero; result is 0 if B is zero
                val = If(B_t != 0, A_t / B_t, 0)
                cases.append(If(cond,
                    And(
                        self.pc[t + 1] == pc_t + 1,
                        self.A[t + 1]  == val,
                        self.B[t + 1]  == B_t,
                        self.Z[t + 1]  == (val == 0),
                        self.N[t + 1]  == (val < 0)
                    ), True))

            elif instr == JNZ:
                # Jump to operand if B != 0, otherwise fall through
                cases.append(If(cond,
                    And(
                        If(B_t != 0,
                           self.pc[t + 1] == operand,
                           self.pc[t + 1] == pc_t + 1),
                        self.A[t + 1] == A_t,
                        self.B[t + 1] == B_t,
                        self.Z[t + 1] == Z_t,
                        self.N[t + 1] == N_t
                    ), True))

            elif instr == HALT:
                cases.append(If(cond,
                    And(
                        self.pc[t + 1] == -1,
                        self.A[t + 1]  == A_t,
                        self.B[t + 1]  == B_t,
                        self.Z[t + 1]  == Z_t,
                        self.N[t + 1]  == N_t
                    ), True))

            else:
                # Unknown instruction: halt the machine
                cases.append(If(cond,
                    And(
                        self.pc[t + 1] == -1,
                        self.A[t + 1]  == A_t,
                        self.B[t + 1]  == B_t,
                        self.Z[t + 1]  == Z_t,
                        self.N[t + 1]  == N_t
                    ), True))

        return And(cases)

    def check_property(self, expected_A):
        """
        Ask Z3 whether A == expected_A holds whenever the machine is halted at
        max_steps. Adds the negation of the property and checks for unsatisfiability:
        unsat means no counterexample exists, so the property holds universally.
        """
        pc_last = self.pc[self.max_steps]
        A_last  = self.A[self.max_steps]
        prop    = And(pc_last == -1, A_last == expected_A)
        self.s.add(Not(prop))
        return self.s.check() == unsat

    def get_trace(self):
        """
        If the current constraint set is satisfiable, extract and return a concrete
        execution trace from Z3's model. Returns None if no satisfying model exists.
        """
        if self.s.check() != sat:
            return None

        model = self.s.model()
        trace = []
        for t in range(self.max_steps + 1):
            trace.append({
                'pc': model.evaluate(self.pc[t]).as_long(),
                'A':  model.evaluate(self.A[t]).as_long(),
                'B':  model.evaluate(self.B[t]).as_long(),
                'Z':  model.evaluate(self.Z[t]).as_long(),
                'N':  model.evaluate(self.N[t]).as_long(),
            })
        return trace


# Program: load B = 5, load A = 0, compute A = A * B (= 0), then halt.
# We then verify that A == 0 at the point of halting.
program = [
    (LOAD_B, 5),
    (LOAD_A, 0),
    (MUL,    0),
    (HALT,   0),
]

vm    = SymRegVM(program, max_steps=10)
holds = vm.check_property(expected_A=0)

if holds:
    print("Property holds: A == 0 at halt.")
else:
    print("Property does not hold.")
    trace = vm.get_trace()
    if trace:
        for i, step in enumerate(trace):
            print(f"  Step {i}: pc={step['pc']}  A={step['A']}  B={step['B']}"
                  f"  Z={step['Z']}  N={step['N']}")
