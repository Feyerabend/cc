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


def z3_bool_to_python(expr, model):
    """
    Evaluate a Z3 boolean expression under a concrete model and return a Python bool.
    Returns None if the value is neither definitively true nor false (symbolic residual).
    """
    evaluated = model.evaluate(expr)
    if is_true(evaluated):
        return True
    if is_false(evaluated):
        return False
    return None


class SymRegVM:
    """
    An enhanced symbolic register-based virtual machine backed by the Z3 SMT solver.

    Compared to the simple version this adds:
      - Out-of-bounds PC detection (forces a halt instead of undefined behaviour)
      - A separate solver for property checking so the main constraint set stays clean
      - Correct boolean flag handling in trace output via z3_bool_to_python
      - A higher default step limit to accommodate longer programs

    Encoding principle: the execution of a program is expressed as a set of integer
    constraints over state variables indexed by time step t. Verifying a property then
    reduces to asking Z3 whether the negation of that property is unsatisfiable.
    """

    def __init__(self, program, max_steps=50):
        self.program   = program
        self.max_steps = max_steps

        self.s = Solver()

        self.pc = [Int(f'pc_{t}') for t in range(max_steps + 1)]
        self.A  = [Int(f'A_{t}')  for t in range(max_steps + 1)]
        self.B  = [Int(f'B_{t}')  for t in range(max_steps + 1)]
        self.Z  = [Int(f'Z_{t}')  for t in range(max_steps + 1)]
        self.N  = [Int(f'N_{t}')  for t in range(max_steps + 1)]

        # Initial state: pc at instruction 0, everything else zeroed
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

            # pc must be a valid instruction index or the halt sentinel -1
            self.s.add(
                Or(And(pc_t >= 0, pc_t < len(self.program)), pc_t == -1)
            )

            # Once halted, the entire state is frozen at every subsequent step
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
        Build the Z3 constraint for one execution step. Each instruction is guarded
        by a condition on the current pc value. An out-of-bounds pc forces a halt.
        """
        halt_state = And(
            self.pc[t + 1] == -1,
            self.A[t + 1]  == A_t,
            self.B[t + 1]  == B_t,
            self.Z[t + 1]  == Z_t,
            self.N[t + 1]  == N_t
        )
        out_of_bounds = Or(pc_t < 0, pc_t >= len(self.program))

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
                # Integer division; result is 0 when B is zero to avoid undefined behaviour
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
                # Jump to operand address if B != 0, otherwise advance normally
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

        # An out-of-bounds pc triggers an implicit halt; otherwise dispatch by instruction
        return If(out_of_bounds, halt_state, And(cases))

    def check_property(self, expected_A):
        """
        Verify that A == expected_A holds at every step where pc == -1 (i.e. the
        machine has halted). Uses a fresh solver so the main constraint set is
        unaffected and can still be used for trace generation.

        Returns True if the property holds for all executions, False otherwise.
        """
        prop_solver = Solver()
        prop_solver.add(self.s.assertions())

        # The property is satisfied if any halted state has A == expected_A.
        # We add the negation and look for unsatisfiability.
        halt_with_correct_A = Or(*[
            And(self.pc[t] == -1, self.A[t] == expected_A)
            for t in range(self.max_steps + 1)
        ])
        prop_solver.add(Not(halt_with_correct_A))
        return prop_solver.check() == unsat

    def get_trace(self):
        """
        Extract a concrete execution trace from Z3's model for the current constraint
        set. Stops at the first halted step. Returns None if the constraints are
        unsatisfiable.
        """
        if self.s.check() != sat:
            return None

        model = self.s.model()
        trace = []
        for t in range(self.max_steps + 1):
            step = {
                'pc': model.evaluate(self.pc[t]).as_long(),
                'A':  model.evaluate(self.A[t]).as_long(),
                'B':  model.evaluate(self.B[t]).as_long(),
                'Z':  z3_bool_to_python(self.Z[t], model),
                'N':  z3_bool_to_python(self.N[t], model),
            }
            trace.append(step)
            if step['pc'] == -1:
                break
        return trace


def run_example(label, program, expected_A, max_steps=15):
    """Run a single verification example, print the trace, and report the result."""
    print(f"\n{'=' * 60}")
    print(f"  {label}")
    print(f"{'=' * 60}")

    vm    = SymRegVM(program, max_steps=max_steps)
    trace = vm.get_trace()

    if trace:
        print("Execution trace:")
        for i, step in enumerate(trace):
            print(f"  Step {i:2d}: pc={step['pc']:3d}  A={step['A']:6d}  "
                  f"B={step['B']:6d}  Z={step['Z']}  N={step['N']}")
    else:
        print("  No satisfying execution found within step limit.")

    holds = vm.check_property(expected_A=expected_A)
    status = "PASS" if holds else "FAIL"
    print(f"\nProperty A == {expected_A} at halt: {status}")


# 5! = 120
# Computed by loading each successive factor into B and multiplying into A
factorial_5 = [
    (LOAD_A, 1),   # A = 1
    (LOAD_B, 2),   # B = 2
    (MUL,    0),   # A = 1 * 2 = 2
    (LOAD_B, 3),   # B = 3
    (MUL,    0),   # A = 2 * 3 = 6
    (LOAD_B, 4),   # B = 4
    (MUL,    0),   # A = 6 * 4 = 24
    (LOAD_B, 5),   # B = 5
    (MUL,    0),   # A = 24 * 5 = 120
    (HALT,   0),
]

# 3! = 6
factorial_3 = [
    (LOAD_A, 1),   # A = 1
    (LOAD_B, 2),   # B = 2
    (MUL,    0),   # A = 1 * 2 = 2
    (LOAD_B, 3),   # B = 3
    (MUL,    0),   # A = 2 * 3 = 6
    (HALT,   0),
]

# 4! = 24  (descending factor order)
factorial_4 = [
    (LOAD_A, 4),   # A = 4
    (LOAD_B, 3),   # B = 3
    (MUL,    0),   # A = 4 * 3 = 12
    (LOAD_B, 2),   # B = 2
    (MUL,    0),   # A = 12 * 2 = 24
    (LOAD_B, 1),   # B = 1
    (MUL,    0),   # A = 24 * 1 = 24
    (HALT,   0),
]

run_example("5! = 120", factorial_5, expected_A=120, max_steps=15)
run_example("3! = 6",   factorial_3, expected_A=6,   max_steps=10)
run_example("4! = 24",  factorial_4, expected_A=24,  max_steps=10)
