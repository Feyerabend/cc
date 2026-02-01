class Optimizer:
    def __init__(self, tac_code):
        self.tac_code = tac_code
        self.optimized_tac = []
        self.symbol_table = {}

    def optimize(self):
        for line in self.tac_code:
            self._process_tac(line)
        return self.optimized_tac

    def _process_tac(self, line):
        parts = line.split(" = ")
        lhs = parts[0].strip()  # left-hand: variable
        rhs = parts[1].strip()  # right-hand: expression

        if rhs.isdigit():
            # constant assignment
            self.optimized_tac.append(f"{lhs} = {rhs}")

        elif "+" in rhs or "-" in rhs or "*" in rhs or "/" in rhs:
            # arithmetic
            self._process_expression(lhs, rhs)

        else:
            # variable or other simple expression
            self.optimized_tac.append(f"{lhs} = {rhs}")

    def _process_expression(self, lhs, rhs):
        # Constant Folding: evaluate simple constants
        rhs_parts = rhs.split(" ")
        for i, part in enumerate(rhs_parts):
            if part.isdigit():
                rhs_parts[i] = str(int(part))  # convert to int for constant folding

        # if both operands are constants, fold the expression
        if len(rhs_parts) == 3 and rhs_parts[0].isdigit() and rhs_parts[2].isdigit():
            left = int(rhs_parts[0])
            op = rhs_parts[1]
            right = int(rhs_parts[2])
            result = self._evaluate_constant_expression(left, op, right)
            self.optimized_tac.append(f"{lhs} = {result}")

        else:
            # Common Subexpression Elimination
            if rhs in self.symbol_table:
                self.optimized_tac.append(f"{lhs} = {self.symbol_table[rhs]}")
            else:
                self.optimized_tac.append(f"{lhs} = {rhs}")
                self.symbol_table[rhs] = lhs

    def _evaluate_constant_expression(self, left, op, right):
        if op == "+":
            return left + right
        elif op == "-":
            return left - right
        elif op == "*":
            return left * right
        elif op == "/":
            return left // right
        return None

# example TAC (before)
tac_code = [
    "x = 2025",
    "y = 1477",
    "t1 = x + y",
    "t2 = 7 + 9",
    "t3 = 5 * t2",
    "t4 = t3 / 2",
    "t5 = t1 - t4",
    "z = t5"
]

optimizer = Optimizer(tac_code)
optimized_tac = optimizer.optimize()

print("Optimised TAC:")
for line in optimized_tac:
    print(line)
