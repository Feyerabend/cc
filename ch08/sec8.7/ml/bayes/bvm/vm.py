import random
import math
from typing import List, Dict, Any #, Callable, Union
from dataclasses import dataclass
from enum import Enum

class OpCode(Enum):
    PUSH = "PUSH"
    POP = "POP"
    DUP = "DUP"
    SWAP = "SWAP"
    
    ADD = "ADD"
    SUB = "SUB"
    MUL = "MUL"
    DIV = "DIV"
    
    EQ = "EQ"
    LT = "LT"
    GT = "GT"
    
    JMP = "JMP"
    JMP_IF = "JMP_IF"
    CALL = "CALL"
    RET = "RET"
    
    STORE = "STORE"
    LOAD = "LOAD"
    
    # probabilistic ops
    SAMPLE = "SAMPLE"
    OBSERVE = "OBSERVE"
    PRIOR = "PRIOR"
    
    # distributions
    NORMAL = "NORMAL"
    UNIFORM = "UNIFORM"
    BERNOULLI = "BERNOULLI"
    BETA = "BETA"
    
    # inference
    INFER = "INFER"
    HALT = "HALT"

@dataclass
class Instruction:
    opcode: OpCode
    arg: Any = None

class Distribution:
    def sample(self) -> float:
        raise NotImplementedError
    
    def log_prob(self, value: float) -> float:
        raise NotImplementedError

class Normal(Distribution):
    def __init__(self, mu: float, sigma: float):
        self.mu = mu
        self.sigma = sigma
    
    def sample(self) -> float:
        return random.gauss(self.mu, self.sigma)
    
    def log_prob(self, value: float) -> float:
        return -0.5 * math.log(2 * math.pi * self.sigma**2) - \
               (value - self.mu)**2 / (2 * self.sigma**2)

class Uniform(Distribution):
    def __init__(self, a: float, b: float):
        self.a = a
        self.b = b
    
    def sample(self) -> float:
        return random.uniform(self.a, self.b)
    
    def log_prob(self, value: float) -> float:
        if self.a <= value <= self.b:
            return -math.log(self.b - self.a)
        return float('-inf')

class Bernoulli(Distribution):
    def __init__(self, p: float):
        self.p = p
    
    def sample(self) -> float:
        return 1.0 if random.random() < self.p else 0.0
    
    def log_prob(self, value: float) -> float:
        if value == 1.0:
            return math.log(self.p)
        elif value == 0.0:
            return math.log(1 - self.p)
        return float('-inf')

class Beta(Distribution):
    def __init__(self, alpha: float, beta: float):
        self.alpha = alpha
        self.beta = beta
    
    def sample(self) -> float:
        return random.betavariate(self.alpha, self.beta)
    
    def log_prob(self, value: float) -> float:
        if 0 <= value <= 1:
            return (self.alpha - 1) * math.log(value) + \
                   (self.beta - 1) * math.log(1 - value) + \
                   math.lgamma(self.alpha + self.beta) - \
                   math.lgamma(self.alpha) - math.lgamma(self.beta)
        return float('-inf')

class BayesVM:
    def __init__(self):
        self.stack: List[Any] = []
        self.variables: Dict[str, Any] = {}
        self.pc = 0
        self.call_stack: List[int] = []
        self.log_prob = 0.0
        self.observations: List[tuple] = []
        self.samples: Dict[str, Any] = {}
        
    def push(self, value: Any):
        self.stack.append(value)
    
    def pop(self) -> Any:
        if not self.stack:
            raise RuntimeError("Stack underflow")
        return self.stack.pop()
    
    def peek(self) -> Any:
        if not self.stack:
            raise RuntimeError("Stack empty")
        return self.stack[-1]
    
    def execute(self, program: List[Instruction]) -> Dict[str, Any]:
        self.pc = 0
        
        while self.pc < len(program):
            instr = program[self.pc]
            self._execute_instruction(instr)
            self.pc += 1
        
        return {
            'samples': self.samples,
            'log_prob': self.log_prob,
            'observations': self.observations
        }
    
    def _execute_instruction(self, instr: Instruction):
        op = instr.opcode
        
        if op == OpCode.PUSH:
            self.push(instr.arg)
        
        elif op == OpCode.POP:
            self.pop()
        
        elif op == OpCode.DUP:
            self.push(self.peek())
        
        elif op == OpCode.SWAP:
            a = self.pop()
            b = self.pop()
            self.push(a)
            self.push(b)
        
        elif op == OpCode.ADD:
            b = self.pop()
            a = self.pop()
            self.push(a + b)
        
        elif op == OpCode.SUB:
            b = self.pop()
            a = self.pop()
            self.push(a - b)
        
        elif op == OpCode.MUL:
            b = self.pop()
            a = self.pop()
            self.push(a * b)
        
        elif op == OpCode.DIV:
            b = self.pop()
            a = self.pop()
            self.push(a / b)
        
        elif op == OpCode.EQ:
            b = self.pop()
            a = self.pop()
            self.push(1.0 if a == b else 0.0)
        
        elif op == OpCode.LT:
            b = self.pop()
            a = self.pop()
            self.push(1.0 if a < b else 0.0)
        
        elif op == OpCode.GT:
            b = self.pop()
            a = self.pop()
            self.push(1.0 if a > b else 0.0)
        
        elif op == OpCode.JMP:
            self.pc = instr.arg - 1  # pc will be incremented
        
        elif op == OpCode.JMP_IF:
            condition = self.pop()
            if condition:
                self.pc = instr.arg - 1
        
        elif op == OpCode.CALL:
            self.call_stack.append(self.pc)
            self.pc = instr.arg - 1
        
        elif op == OpCode.RET:
            if self.call_stack:
                self.pc = self.call_stack.pop()
        
        elif op == OpCode.STORE:
            value = self.pop()
            self.variables[instr.arg] = value
        
        elif op == OpCode.LOAD:
            if instr.arg in self.variables:
                self.push(self.variables[instr.arg])
            else:
                raise RuntimeError(f"Variable '{instr.arg}' not found")
        
        elif op == OpCode.NORMAL:
            sigma = self.pop()
            mu = self.pop()
            self.push(Normal(mu, sigma))
        
        elif op == OpCode.UNIFORM:
            b = self.pop()
            a = self.pop()
            self.push(Uniform(a, b))
        
        elif op == OpCode.BERNOULLI:
            p = self.pop()
            self.push(Bernoulli(p))
        
        elif op == OpCode.BETA:
            beta = self.pop()
            alpha = self.pop()
            self.push(Beta(alpha, beta))
        
        elif op == OpCode.SAMPLE:
            dist = self.pop()
            var_name = instr.arg
            sample_value = dist.sample()
            self.samples[var_name] = sample_value
            self.variables[var_name] = sample_value  # .. variables too
            self.push(sample_value)
        
        elif op == OpCode.OBSERVE:
            if len(self.stack) < 2:
                raise RuntimeError(f"OBSERVE requires 2 values on stack, got {len(self.stack)}")
            
            observed_value = self.pop()
            dist = self.pop()
            
            if not hasattr(dist, 'log_prob'):
                raise RuntimeError(f"Expected distribution object, got {type(dist)}: {dist}")
            
            log_p = dist.log_prob(observed_value)
            self.log_prob += log_p
            self.observations.append((dist, observed_value, log_p))
        
        elif op == OpCode.HALT:
            self.pc = float('inf')

class BayesCompiler:
    def __init__(self):
        self.instructions = []
        self.labels = {}
        self.label_counter = 0
    
    def compile_program(self, source: str) -> List[Instruction]:
        lines = [line.strip() for line in source.split('\n') if line.strip()]
        self.instructions = []
        self.labels = {}
        
        # 1: collect labels and filter out label lines
        non_label_lines = []
        for line in lines:
            if line.endswith(':'):
                label = line[:-1]
                self.labels[label] = len(non_label_lines)
            else:
                non_label_lines.append(line)
        
        # 2: compile instructions
        for line in non_label_lines:
            self._compile_line(line)
        
        return self.instructions
    
    def _compile_line(self, line: str):
        tokens = line.split()
        if not tokens:
            return
        
        cmd = tokens[0].upper()
        
        if cmd == 'PUSH':
            value = float(tokens[1]) if '.' in tokens[1] else int(tokens[1])
            self.instructions.append(Instruction(OpCode.PUSH, value))
        
        elif cmd in ['POP', 'DUP', 'SWAP', 'ADD', 'SUB', 'MUL', 'DIV', 
                     'EQ', 'LT', 'GT', 'RET', 'HALT']:
            self.instructions.append(Instruction(OpCode[cmd]))
        
        elif cmd in ['NORMAL', 'UNIFORM', 'BERNOULLI', 'BETA']:
            self.instructions.append(Instruction(OpCode[cmd]))
        
        elif cmd == 'SAMPLE':
            var_name = tokens[1]
            self.instructions.append(Instruction(OpCode.SAMPLE, var_name))
        
        elif cmd == 'OBSERVE':
            self.instructions.append(Instruction(OpCode.OBSERVE))
        
        elif cmd == 'STORE':
            var_name = tokens[1]
            self.instructions.append(Instruction(OpCode.STORE, var_name))
        
        elif cmd == 'LOAD':
            var_name = tokens[1]
            self.instructions.append(Instruction(OpCode.LOAD, var_name))
        
        elif cmd == 'JMP':
            label = tokens[1]
            self.instructions.append(Instruction(OpCode.JMP, self.labels[label]))
        
        elif cmd == 'JMP_IF':
            label = tokens[1]
            self.instructions.append(Instruction(OpCode.JMP_IF, self.labels[label]))

def run_mcmc_inference(source: str, num_samples: int = 1000) -> Dict[str, List[float]]:
    compiler = BayesCompiler()
    program = compiler.compile_program(source)
    
    results = {}
    log_probs = []
    
    for _ in range(num_samples):
        vm = BayesVM()
        result = vm.execute(program)
        
        # keep samples with finite log probability
        if math.isfinite(result['log_prob']):
            for var, value in result['samples'].items():
                if var not in results:
                    results[var] = []
                results[var].append(value)
            
            log_probs.append(result['log_prob'])
    
    return {'samples': results, 'log_probs': log_probs}


# Examples
if __name__ == "__main__":

    # Example 1: Simple coin flip model
    coin_model = """
    PUSH 0.5
    BERNOULLI
    SAMPLE coin
    
    PUSH 0.5
    BERNOULLI
    PUSH 1.0
    OBSERVE
    
    HALT
    """
    
    # Example 2: Linear regression model
    regression_model = """
    PUSH 0.0
    PUSH 1.0
    NORMAL
    SAMPLE slope
    
    PUSH 0.0
    PUSH 1.0
    NORMAL
    SAMPLE intercept
    
    PUSH 1.0
    LOAD slope
    MUL
    LOAD intercept
    ADD
    PUSH 0.1
    NORMAL
    PUSH 1.2
    OBSERVE
    
    HALT
    """

    print("\nTesting coin flip model ..")
    vm = BayesVM()
    compiler = BayesCompiler()
    program = compiler.compile_program(coin_model)
    result = vm.execute(program)
    print(f"Coin sample: {result['samples']}")
    print(f"Log probability: {result['log_prob']:.4f}")
    
    print("\nTesting linear regression model ..")
    vm = BayesVM()
    program = compiler.compile_program(regression_model)
    result = vm.execute(program)
    print(f"Regression samples: {result['samples']}")
    print(f"Log probability: {result['log_prob']:.4f}")
