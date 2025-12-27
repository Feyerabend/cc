"""
Categorical Compilation Pipeline

All examples now run correctly with full categorical optimisation:
- Product β-reduction eliminates unnecessary pairs
- Sum β-reduction eliminates case analysis via proper substitution
"""

from abc import ABC
from typing import Any, List, Dict
from dataclasses import dataclass
from enum import Enum


# STAGE 1: SURFACE LANGUAGE

class Type(ABC):
    pass

@dataclass(frozen=True)
class IntType(Type):
    def __repr__(self): return "Int"

@dataclass(frozen=True)
class ProductType(Type):
    left: Type
    right: Type
    def __repr__(self): return f"({self.left} × {self.right})"

@dataclass(frozen=True)
class SumType(Type):
    left: Type
    right: Type
    def __repr__(self): return f"({self.left} + {self.right})"


class Expr(ABC):
    def type_of(self, ctx: Dict[str, Type]) -> Type:
        raise NotImplementedError


@dataclass
class Var(Expr):
    name: str
    def type_of(self, ctx: Dict[str, Type]) -> Type:
        if self.name not in ctx:
            raise NameError(f"Undefined variable: {self.name}")
        return ctx[self.name]
    def __repr__(self): return self.name


@dataclass
class Lit(Expr):
    value: int
    def type_of(self, ctx): return IntType()
    def __repr__(self): return str(self.value)


@dataclass
class BinOp(Expr):
    op: str
    left: Expr
    right: Expr
    def type_of(self, ctx):
        lt = self.left.type_of(ctx)
        rt = self.right.type_of(ctx)
        if not (isinstance(lt, IntType) and isinstance(rt, IntType)):
            raise TypeError(f"BinOp requires Int arguments, got {lt}, {rt}")
        return IntType()
    def __repr__(self): return f"({self.left} {self.op} {self.right})"


@dataclass
class Pair(Expr):
    fst: Expr
    snd: Expr
    def type_of(self, ctx):
        return ProductType(self.fst.type_of(ctx), self.snd.type_of(ctx))
    def __repr__(self): return f"⟨{self.fst}, {self.snd}⟩"


@dataclass
class Fst(Expr):
    expr: Expr
    def type_of(self, ctx):
        t = self.expr.type_of(ctx)
        if not isinstance(t, ProductType):
            raise TypeError(f"fst requires product type, got {t}")
        return t.left
    def __repr__(self): return f"fst({self.expr})"


@dataclass
class Snd(Expr):
    expr: Expr
    def type_of(self, ctx):
        t = self.expr.type_of(ctx)
        if not isinstance(t, ProductType):
            raise TypeError(f"snd requires product type, got {t}")
        return t.right
    def __repr__(self): return f"snd({self.expr})"


@dataclass
class InL(Expr):
    expr: Expr
    right_type: Type
    def type_of(self, ctx):
        return SumType(self.expr.type_of(ctx), self.right_type)
    def __repr__(self): return f"inl({self.expr})"


@dataclass
class InR(Expr):
    expr: Expr
    left_type: Type
    def type_of(self, ctx):
        return SumType(self.left_type, self.expr.type_of(ctx))
    def __repr__(self): return f"inr({self.expr})"


@dataclass
class Case(Expr):
    scrutinee: Expr
    left_var: str
    left_branch: Expr
    right_var: str
    right_branch: Expr
    def type_of(self, ctx):
        st = self.scrutinee.type_of(ctx)
        if not isinstance(st, SumType):
            raise TypeError(f"case requires sum type, got {st}")
        lctx = {**ctx, self.left_var: st.left}
        rctx = {**ctx, self.right_var: st.right}
        lt = self.left_branch.type_of(lctx)
        rt = self.right_branch.type_of(rctx)
        if lt != rt:
            raise TypeError(f"case branches must have same type: {lt} vs {rt}")
        return lt
    def __repr__(self):
        return f"case {self.scrutinee} of inl {self.left_var} → {self.left_branch} | inr {self.right_var} → {self.right_branch}"


# STAGE 2: CATEGORICAL IR (de Bruijn indices)

class CatIR(ABC):
    pass


@dataclass
class IRLit(CatIR):
    value: int
    def __repr__(self): return f"#{self.value}"


@dataclass
class IRVar(CatIR):
    index: int
    def __repr__(self): return f"${self.index}"


@dataclass
class IRBinOp(CatIR):
    op: str
    left: CatIR
    right: CatIR
    def __repr__(self): return f"({self.left} {self.op} {self.right})"


@dataclass
class IRPair(CatIR):
    fst: CatIR
    snd: CatIR
    def __repr__(self): return f"⟨{self.fst}, {self.snd}⟩"


@dataclass
class IRFst(CatIR):
    expr: CatIR
    def __repr__(self): return f"π₁({self.expr})"


@dataclass
class IRSnd(CatIR):
    expr: CatIR
    def __repr__(self): return f"π₂({self.expr})"


@dataclass
class IRInL(CatIR):
    expr: CatIR
    def __repr__(self): return f"ι₁({self.expr})"


@dataclass
class IRInR(CatIR):
    expr: CatIR
    def __repr__(self): return f"ι₂({self.expr})"


@dataclass
class IRCase(CatIR):
    scrutinee: CatIR
    left_branch: CatIR
    right_branch: CatIR
    def __repr__(self):
        return f"[case {self.scrutinee} | {self.left_branch} | {self.right_branch}]"


# STAGE 3: OPTIMIZER WITH SUBSTITUTION

class CategoricalOptimizer:
    @staticmethod
    def optimize(ir: CatIR) -> CatIR:
        prev = None
        current = ir
        while prev != current:
            prev = current
            current = CategoricalOptimizer.rewrite(current)
        return current

    @staticmethod
    def rewrite(ir: CatIR) -> CatIR:
        if isinstance(ir, IRFst):
            e = CategoricalOptimizer.rewrite(ir.expr)
            if isinstance(e, IRPair):
                return CategoricalOptimizer.rewrite(e.fst)
            return IRFst(e)
        elif isinstance(ir, IRSnd):
            e = CategoricalOptimizer.rewrite(ir.expr)
            if isinstance(e, IRPair):
                return CategoricalOptimizer.rewrite(e.snd)
            return IRSnd(e)
        elif isinstance(ir, IRCase):
            scrut = CategoricalOptimizer.rewrite(ir.scrutinee)
            left = CategoricalOptimizer.rewrite(ir.left_branch)
            right = CategoricalOptimizer.rewrite(ir.right_branch)
            if isinstance(scrut, IRInL):
                return CategoricalOptimizer.subst(left, 0, scrut.expr)
            elif isinstance(scrut, IRInR):
                return CategoricalOptimizer.subst(right, 0, scrut.expr)
            return IRCase(scrut, left, right)
        elif isinstance(ir, IRBinOp):
            return IRBinOp(ir.op, CategoricalOptimizer.rewrite(ir.left), CategoricalOptimizer.rewrite(ir.right))
        elif isinstance(ir, IRPair):
            return IRPair(CategoricalOptimizer.rewrite(ir.fst), CategoricalOptimizer.rewrite(ir.snd))
        elif isinstance(ir, IRInL):
            return IRInL(CategoricalOptimizer.rewrite(ir.expr))
        elif isinstance(ir, IRInR):
            return IRInR(CategoricalOptimizer.rewrite(ir.expr))
        else:
            return ir

    @staticmethod
    def subst(ir: CatIR, depth: int, replacement: CatIR) -> CatIR:
        if isinstance(ir, IRLit):
            return ir
        elif isinstance(ir, IRVar):
            if ir.index == depth:
                return replacement
            elif ir.index > depth:
                return IRVar(ir.index - 1)
            else:
                return ir
        elif isinstance(ir, IRBinOp):
            return IRBinOp(ir.op,
                           CategoricalOptimizer.subst(ir.left, depth, replacement),
                           CategoricalOptimizer.subst(ir.right, depth, replacement))
        elif isinstance(ir, IRPair):
            return IRPair(CategoricalOptimizer.subst(ir.fst, depth, replacement),
                          CategoricalOptimizer.subst(ir.snd, depth, replacement))
        elif isinstance(ir, IRFst):
            return IRFst(CategoricalOptimizer.subst(ir.expr, depth, replacement))
        elif isinstance(ir, IRSnd):
            return IRSnd(CategoricalOptimizer.subst(ir.expr, depth, replacement))
        elif isinstance(ir, IRInL):
            return IRInL(CategoricalOptimizer.subst(ir.expr, depth, replacement))
        elif isinstance(ir, IRInR):
            return IRInR(CategoricalOptimizer.subst(ir.expr, depth, replacement))
        elif isinstance(ir, IRCase):
            return IRCase(
                CategoricalOptimizer.subst(ir.scrutinee, depth, replacement),
                CategoricalOptimizer.subst(ir.left_branch, depth + 1, replacement),
                CategoricalOptimizer.subst(ir.right_branch, depth + 1, replacement)
            )
        return ir


# STAGE 4: VM AND CODE GENERATION

class Opcode(Enum):
    PUSH = "PUSH"
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    DIV = "DIV"
    PAIR = "PAIR"
    FST = "FST"
    SND = "SND"
    TAG_LEFT = "TAG_LEFT"
    TAG_RIGHT = "TAG_RIGHT"
    BRANCH = "BRANCH"


@dataclass
class Instruction:
    opcode: Opcode
    arg: Any = None
    def __repr__(self):
        return f"{self.opcode.value} {self.arg}" if self.arg is not None else self.opcode.value


class SimpleVM:
    def __init__(self):
        self.stack: List[Any] = []

    def execute(self, code: List[Instruction]):
        ip = 0
        while ip < len(code):
            instr = code[ip]
            if instr.opcode == Opcode.PUSH:
                self.stack.append(instr.arg)
            elif instr.opcode == Opcode.ADD:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a + b)
            elif instr.opcode == Opcode.SUB:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a - b)
            elif instr.opcode == Opcode.MUL:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a * b)
            elif instr.opcode == Opcode.DIV:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append(a // b)
            elif instr.opcode == Opcode.PAIR:
                b, a = self.stack.pop(), self.stack.pop()
                self.stack.append((a, b))
            elif instr.opcode == Opcode.FST:
                self.stack.append(self.stack.pop()[0])
            elif instr.opcode == Opcode.SND:
                self.stack.append(self.stack.pop()[1])
            elif instr.opcode == Opcode.TAG_LEFT:
                val = self.stack.pop()
                self.stack.append(("L", val))
            elif instr.opcode == Opcode.TAG_RIGHT:
                val = self.stack.pop()
                self.stack.append(("R", val))
            elif instr.opcode == Opcode.BRANCH:
                tag, val = self.stack.pop()
                self.stack.append(val)
                if tag == "R":
                    ip = instr.arg
                    continue
            ip += 1

    def top(self):
        return self.stack[-1] if self.stack else None


class CodeGen:
    @staticmethod
    def compile(ir: CatIR) -> List[Instruction]:
        if isinstance(ir, IRLit):
            return [Instruction(Opcode.PUSH, ir.value)]
        elif isinstance(ir, IRVar):
            raise ValueError("Free IRVar in closed term after optimization")
        elif isinstance(ir, IRBinOp):
            code = CodeGen.compile(ir.left) + CodeGen.compile(ir.right)
            opmap = {'+': Opcode.ADD, '-': Opcode.SUB, '*': Opcode.MUL, '/': Opcode.DIV}
            code.append(Instruction(opmap[ir.op]))
            return code
        elif isinstance(ir, IRPair):
            return CodeGen.compile(ir.fst) + CodeGen.compile(ir.snd) + [Instruction(Opcode.PAIR)]
        elif isinstance(ir, IRFst):
            return CodeGen.compile(ir.expr) + [Instruction(Opcode.FST)]
        elif isinstance(ir, IRSnd):
            return CodeGen.compile(ir.expr) + [Instruction(Opcode.SND)]
        elif isinstance(ir, IRInL):
            return CodeGen.compile(ir.expr) + [Instruction(Opcode.TAG_LEFT)]
        elif isinstance(ir, IRInR):
            return CodeGen.compile(ir.expr) + [Instruction(Opcode.TAG_RIGHT)]
        elif isinstance(ir, IRCase):
            scrut_code = CodeGen.compile(ir.scrutinee)
            left_code = CodeGen.compile(ir.left_branch)
            right_code = CodeGen.compile(ir.right_branch)
            right_start = len(scrut_code) + 1 + len(left_code)
            return scrut_code + [Instruction(Opcode.BRANCH, right_start)] + left_code + right_code
        raise NotImplementedError(f"Codegen: {type(ir)}")


# COMPILER PIPELINE

class Compiler:
    @staticmethod
    def to_ir(expr: Expr, env: Dict[str, int]) -> CatIR:
        if isinstance(expr, Lit):
            return IRLit(expr.value)
        elif isinstance(expr, Var):
            if expr.name not in env:
                raise NameError(f"Unbound variable: {expr.name}")
            return IRVar(env[expr.name])
        elif isinstance(expr, BinOp):
            return IRBinOp(expr.op, Compiler.to_ir(expr.left, env), Compiler.to_ir(expr.right, env))
        elif isinstance(expr, Pair):
            return IRPair(Compiler.to_ir(expr.fst, env), Compiler.to_ir(expr.snd, env))
        elif isinstance(expr, Fst):
            return IRFst(Compiler.to_ir(expr.expr, env))
        elif isinstance(expr, Snd):
            return IRSnd(Compiler.to_ir(expr.expr, env))
        elif isinstance(expr, InL):
            return IRInL(Compiler.to_ir(expr.expr, env))
        elif isinstance(expr, InR):
            return IRInR(Compiler.to_ir(expr.expr, env))
        elif isinstance(expr, Case):
            scrut = Compiler.to_ir(expr.scrutinee, env)
            # Shift all existing variables up by 1 and bind the new ones at index 0
            branch_env = {k: v + 1 for k, v in env.items()}
            branch_env[expr.left_var] = 0
            branch_env[expr.right_var] = 0
            left = Compiler.to_ir(expr.left_branch, branch_env)
            right = Compiler.to_ir(expr.right_branch, branch_env)
            return IRCase(scrut, left, right)
        raise NotImplementedError(f"to_ir: {type(expr)}")

    @staticmethod
    def compile_expr(expr: Expr, show_stages: bool = False) -> List[Instruction]:
        expr.type_of({})  # type check closed term

        ir = Compiler.to_ir(expr, {})
        if show_stages:
            print(f"  IR (raw): {ir}")

        opt_ir = CategoricalOptimizer.optimize(ir)
        if show_stages:
            print(f"  IR (opt): {opt_ir}")

        code = CodeGen.compile(opt_ir)
        if show_stages:
            print(f"  Code ({len(code)} instrs):")
            for i, instr in enumerate(code):
                print(f"    {i:2d}: {instr}")

        return code


# EXAMPLES

def example1():
    print("\n" + "="*80)
    print("EXAMPLE 1: Product β-reduction - pair eliminated")
    print("="*80)
    expr = Fst(Pair(BinOp('+', Lit(3), Lit(4)), BinOp('*', Lit(10), Lit(2))))
    print(f"Surface: {expr}")
    code = Compiler.compile_expr(expr, show_stages=True)
    vm = SimpleVM()
    vm.execute(code)
    print(f"\nResult: {vm.top()}  ← pair construction eliminated!")


def example2():
    print("\n" + "="*80)
    print("EXAMPLE 2: Sum β-reduction - case eliminated via substitution")
    print("="*80)
    expr = Case(
        InL(Lit(42), IntType()),
        "x", BinOp('*', Var("x"), Lit(2)),
        "y", Lit(0)
    )
    print(f"Surface: {expr}")
    code = Compiler.compile_expr(expr, show_stages=True)
    vm = SimpleVM()
    vm.execute(code)
    print(f"\nResult: {vm.top()}  ← case and variable fully eliminated!")


def example3():
    print("\n" + "="*80)
    print("EXAMPLE 3: Nested products")
    print("="*80)
    expr = Snd(Fst(Pair(Pair(Lit(1), Lit(2)), Lit(3))))
    print(f"Surface: {expr}")
    code = Compiler.compile_expr(expr, show_stages=True)
    vm = SimpleVM()
    vm.execute(code)
    print(f"\nResult: {vm.top()}")


def example4():
    print("\n" + "="*80)
    print("EXAMPLE 4: Simple arithmetic")
    print("="*80)
    expr = BinOp('*', BinOp('+', Lit(3), Lit(4)), BinOp('-', Lit(10), Lit(2)))
    print(f"Surface: {expr}")
    code = Compiler.compile_expr(expr, show_stages=True)
    vm = SimpleVM()
    vm.execute(code)
    print(f"\nResult: {vm.top()}")


if __name__ == "__main__":
    example1()
    example2()
    example3()
    example4()
