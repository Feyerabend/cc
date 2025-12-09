# Stack VM + fuzzer & mutation tester
import random
import struct
import time

OP_PUSH = 0x01
OP_ADD  = 0x02
OP_SUB  = 0x03
OP_MUL  = 0x04
OP_DIV  = 0x05
OP_DUP  = 0x06
OP_POP  = 0x07
OP_HALT = 0x08
OP_PRINT= 0x09
OP_JZ   = 0x0A
OP_JNZ  = 0x0B

VM_OK = 0
VM_ERR_STACK_UNDERFLOW = 1
VM_ERR_STACK_OVERFLOW  = 2
VM_ERR_DIV_ZERO        = 3
VM_ERR_INVALID_OPCODE  = 4
VM_ERR_PC_OOB          = 5
VM_ERR_TIMEOUT         = 6

STACK_MAX = 256
PROGRAM_MAX = 1024
PRINT_BUF_MAX = 64
STEP_LIMIT = 10000

class VM:
    def __init__(self, program=b''):
        self.stack = []
        self.program = bytearray(program)
        self.outputs = []

    def push(self, v):
        if len(self.stack) >= STACK_MAX:
            return VM_ERR_STACK_OVERFLOW
        self.stack.append(int(v))
        return VM_OK

    def pop(self):
        if not self.stack:
            return None, VM_ERR_STACK_UNDERFLOW
        return self.stack.pop(), VM_OK

    def run(self):
        pc = 0
        steps = 0
        while pc < len(self.program):
            steps += 1
            if steps > STEP_LIMIT:
                return VM_ERR_TIMEOUT
            op = self.program[pc]; pc += 1
            if op == OP_PUSH:
                if pc + 4 > len(self.program):
                    return VM_ERR_PC_OOB
                imm = struct.unpack_from('<i', self.program, pc)[0]
                pc += 4
                rc = self.push(imm)
                if rc != VM_OK: return rc
            elif op == OP_ADD:
                b, rc = self.pop(); 
                if rc: return rc
                a, rc = self.pop(); 
                if rc: return rc
                if self.push(a + b) != VM_OK: return VM_ERR_STACK_OVERFLOW
            elif op == OP_SUB:
                b, rc = self.pop(); 
                if rc: return rc
                a, rc = self.pop(); 
                if rc: return rc
                if self.push(a - b) != VM_OK: return VM_ERR_STACK_OVERFLOW
            elif op == OP_MUL:
                b, rc = self.pop(); 
                if rc: return rc
                a, rc = self.pop(); 
                if rc: return rc
                if self.push(a * b) != VM_OK: return VM_ERR_STACK_OVERFLOW
            elif op == OP_DIV:
                b, rc = self.pop(); 
                if rc: return rc
                a, rc = self.pop(); 
                if rc: return rc
                if b == 0:
                    return VM_ERR_DIV_ZERO
                if self.push(a // b) != VM_OK: return VM_ERR_STACK_OVERFLOW
            elif op == OP_DUP:
                if not self.stack: return VM_ERR_STACK_UNDERFLOW
                if len(self.stack) >= STACK_MAX: return VM_ERR_STACK_OVERFLOW
                self.stack.append(self.stack[-1])
            elif op == OP_POP:
                if not self.stack: return VM_ERR_STACK_UNDERFLOW
                self.stack.pop()
            elif op == OP_PRINT:
                v, rc = self.pop()
                if rc: return rc
                if len(self.outputs) < PRINT_BUF_MAX:
                    self.outputs.append(v)
            elif op == OP_JZ:
                if pc >= len(self.program): return VM_ERR_PC_OOB
                offset = self.program[pc]; pc += 1
                v, rc = self.pop()
                if rc: return rc
                if v == 0:
                    newpc = pc + offset
                    if newpc >= len(self.program): return VM_ERR_PC_OOB
                    pc = newpc
            elif op == OP_JNZ:
                if pc >= len(self.program): return VM_ERR_PC_OOB
                offset = self.program[pc]; pc += 1
                v, rc = self.pop()
                if rc: return rc
                if v != 0:
                    newpc = pc + offset
                    if newpc >= len(self.program): return VM_ERR_PC_OOB
                    pc = newpc
            elif op == OP_HALT:
                return VM_OK
            else:
                return VM_ERR_INVALID_OPCODE
        return VM_ERR_PC_OOB

def emit_push(program, value):
    program += bytes([OP_PUSH]) + struct.pack('<i', int(value))
    return program

def random_program(max_len=64):
    program = bytearray()
    length = random.randint(1, max_len)
    while len(program) < length:
        if random.random() < 0.15 and len(program) + 5 <= length:
            program = bytearray(emit_push(program, random.randint(-100,100)))
        else:
            ops = [OP_ADD, OP_SUB, OP_MUL, OP_DIV, OP_DUP, OP_POP, OP_PRINT, OP_HALT, 0xAA, 0xBB]
            program.append(random.choice(ops))
    program.append(OP_HALT)
    return bytes(program)

def mutate_program(src):
    b = bytearray(src)
    op = random.randrange(4)
    if op == 0 and len(b) > 0:
        i = random.randrange(len(b))
        b[i] ^= (1 << random.randrange(8))
    elif op == 1:
        i = random.randrange(len(b))
        random_ops = [OP_PUSH, OP_ADD, OP_SUB, OP_MUL, OP_DIV, OP_DUP, OP_POP, OP_PRINT, OP_JZ, OP_JNZ, OP_HALT, 0xAB, 0xCD]
        b[i] = random.choice(random_ops)
    elif op == 2 and len(b) + 1 < PROGRAM_MAX:
        i = random.randrange(len(b) + 1)
        b[i:i] = bytes([random.randrange(256)])
    elif op == 3 and len(b) > 1:
        i = random.randrange(len(b))
        del b[i]
    if len(b) > 0:
        b[-1] = OP_HALT
    return bytes(b)

def hex_dump(program):
    return ' '.join(f'{c:02X}' for c in program)

def run_and_report(program):
    vm = VM(program)
    rc = vm.run()
    return rc, list(vm.outputs)

def main():
    random.seed(int(time.time()))
    print("Tiny VM fuzz + mutation test (Python)")

    # Seed program: (3 + 4) * 5 -> print 35
    seed = b''
    seed = emit_push(seed, 3)
    seed = emit_push(seed, 4)
    seed += bytes([OP_ADD])
    seed = emit_push(seed, 5)
    seed += bytes([OP_MUL, OP_PRINT, OP_HALT])

    print("Seed hex:", hex_dump(seed))
    seed_rc, seed_out = run_and_report(seed)
    print("Seed run -> rc={} out={}".format(seed_rc, seed_out))

    # Mutation testing
    MUTATIONS = 200
    detected = 0
    for i in range(MUTATIONS):
        m = mutate_program(seed)
        rc, out = run_and_report(m)
        outputs_differ = (out != seed_out)
        if rc != seed_rc or outputs_differ:
            detected += 1
            print(f"Mutation {i:3d} detected rc={rc} out={out}")
            print(" mutated hex:", hex_dump(m))
    print(f"Mutation testing: {detected}/{MUTATIONS} detected differences")

    # Fuzzing
    RUNS = 1000
    ok = invalid = timeouts = crashes = 0
    for _ in range(RUNS):
        p = random_program(64)
        rc, out = run_and_report(p)
        if rc == VM_OK:
            ok += 1
        elif rc == VM_ERR_TIMEOUT:
            timeouts += 1
        elif rc in (VM_ERR_INVALID_OPCODE, VM_ERR_PC_OOB):
            invalid += 1
        else:
            crashes += 1
    print(f"Fuzzing summary (runs={RUNS}): OK={ok} INVALID={invalid} TIMEOUT={timeouts} OTHER_CRASHES={crashes}")

if __name__ == '__main__':
    main()
