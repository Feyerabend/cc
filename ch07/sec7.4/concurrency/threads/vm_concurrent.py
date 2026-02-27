#!/usr/bin/env python3
"""
RISC-V RV32IM Virtual Machine — Concurrent Edition
----------------------------------==
Extends the base VM with:

  GREEN THREADS  — cooperative, user-space. Switched only on YIELD (syscall 20)
                   or THREAD_EXIT (syscall 22). Perfect for illustrating voluntary
                   context switches and re-entrant shared functions.

  KERNEL THREADS — preemptive. A simulated timer fires every QUANTUM instructions
                   and the "kernel" saves the running thread's full register file
                   + PC and picks the next runnable one. Illustrates involuntary
                   preemption and why shared data needs protection.

  FENCE          — decoded and logged as a memory barrier. In a real SMP system
                   this orders loads/stores; here it is a visibility annotation
                   in the trace log — good for teaching/learning why barriers matter.

  CONTEXT SWITCH LOG — every switch prints what was preempted, why, what runs next,
                        and a snapshot of the saved/restored register state.

Memory layout (default, 128 KiB total):
  0x0000 - 0x3FFF  code / static data             (16 KiB)
  0x4000 - 0x7FFF  heap / shared variables        (16 KiB)
  0x8000 - 0xFFFF  thread stacks (8 x 4 KiB each) (64 KiB)
    thread 0 stack top: 0xA000 - 1 = 0x9FFF
    thread 1 stack top: 0xC000 - 1 = 0xBFFF
    ...

Syscall ABI (a7 = number, args in a0-a5, return in a0):
  1   print_int       a0 = signed integer
  4   print_str       a0 = address of null-terminated string
  10  exit            terminates the VM
  11  print_char      a0 = char code
  20  yield           voluntarily give up the CPU
  21  thread_create   a0 = entry-point address, a1 = arg (placed in a0 of new thread)
                     returns thread-id in a0
  22  thread_exit     current thread ends; scheduler picks next
  23  thread_join     a0 = tid; blocks until that tid has exited
  24  get_tid         returns current thread id in a0
  25  mutex_lock      a0 = mutex address (word in shared mem, 0=free, 1=locked)
  26  mutex_unlock    a0 = mutex address

FENCE instruction:
  Encoded as opcode 0b0001111 (MISC-MEM), funct3=0. The VM logs it and continues.
  Use it in assembly around accesses to shared variables.
"""

import sys
import struct
import argparse
import textwrap
from collections import deque
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Set
from enum import Enum, auto



# Instruction dataclass (same as original, extended with FENCE)

@dataclass
class Instruction:
    opcode: str
    rd:     int = 0
    rs1:    int = 0
    rs2:    int = 0
    imm:    int = 0
    funct3: int = 0
    funct7: int = 0


# Thread state

class ThreadStatus(Enum):
    RUNNABLE  = auto()
    RUNNING   = auto()
    BLOCKED   = auto()   # waiting on join or mutex
    EXITED    = auto()


@dataclass
class ThreadControlBlock:
    """
    Thread Control Block — everything the scheduler needs to suspend / resume a thread.

    saved_regs   — snapshot of all 32 registers at the moment of last context-switch-out
    saved_pc     — program counter at that moment
    status       — RUNNABLE / RUNNING / BLOCKED / EXITED
    stack_top    — initial stack pointer value (for display)
    join_waiting — set of tids waiting for this thread to exit (for thread_join)
    blocking_on  — tid this thread is waiting for (join) or mutex addr (mutex_lock)
    """
    tid:          int
    name:         str
    thread_type:  str          # 'green' or 'kernel'
    saved_regs:   List[int]    = field(default_factory=lambda: [0]*32)
    saved_pc:     int          = 0
    status:       ThreadStatus = ThreadStatus.RUNNABLE
    stack_top:    int          = 0
    join_waiting: Set[int]     = field(default_factory=set)
    blocking_on:  int          = -1   # tid or mutex addr
    instruction_count: int     = 0    # instructions run by this thread



# Scheduler

class Scheduler:
    """
    Round-robin scheduler that manages both green and kernel threads.

    The VM calls  maybe_preempt()  after every instruction; for green threads
    this is a no-op (only YIELD/EXIT cause a switch), for kernel threads the
    scheduler preempts when the tick counter reaches QUANTUM.
    """

    QUANTUM = 10   # instructions between preemption checks for kernel threads

    def __init__(self, verbose: bool = True):
        self.threads:  Dict[int, ThreadControlBlock] = {}
        self.run_queue: deque = deque()   # tids of RUNNABLE threads
        self.current_tid: int = -1
        self._next_tid = 0
        self.verbose = verbose
        self._tick = 0                    # instructions since last preemption
        self.switch_log: List[str] = []   # full history of every context switch (verbose only)
        self.switch_count: int = 0         # always incremented, regardless of verbosity

    #  Thread lifecycle 

    def create_thread(self, name: str, thread_type: str,
                      entry_pc: int, init_regs: List[int],
                      stack_top: int) -> int:
        tid = self._next_tid
        self._next_tid += 1

        tcb = ThreadControlBlock(
            tid=tid,
            name=name,
            thread_type=thread_type,
            saved_regs=list(init_regs),
            saved_pc=entry_pc,
            status=ThreadStatus.RUNNABLE,
            stack_top=stack_top,
        )
        tcb.saved_regs[2] = stack_top   # sp = stack_top (grows down)
        self.threads[tid] = tcb
        self.run_queue.append(tid)

        if self.verbose:
            self._log(f"[THREAD CREATE] tid={tid} name={name!r} type={thread_type}"
                      f" entry=0x{entry_pc:04x} sp=0x{stack_top:04x}")
        return tid

    def exit_thread(self, tid: int):
        """Mark thread as exited; wake any joiners."""
        tcb = self.threads[tid]
        tcb.status = ThreadStatus.EXITED
        if self.verbose:
            self._log(f"[THREAD EXIT] tid={tid} name={tcb.name!r}"
                      f" ran {tcb.instruction_count} instructions")
        # Wake everyone waiting for this thread
        for other_tid, other in self.threads.items():
            if other.status == ThreadStatus.BLOCKED and other.blocking_on == tid:
                other.status = ThreadStatus.RUNNABLE
                other.blocking_on = -1
                self.run_queue.append(other_tid)
                if self.verbose:
                    self._log(f"[THREAD UNBLOCK] tid={other_tid} name={other.name!r}"
                              f" unblocked (join target tid={tid} exited)")

    def block_on_join(self, blocker_tid: int, target_tid: int):
        tcb = self.threads[blocker_tid]
        # If target already exited, return immediately
        if self.threads[target_tid].status == ThreadStatus.EXITED:
            return False  # no actual block needed
        tcb.status = ThreadStatus.BLOCKED
        tcb.blocking_on = target_tid
        if self.verbose:
            self._log(f"[THREAD BLOCK] tid={blocker_tid} name={tcb.name!r}"
                      f" waiting for tid={target_tid} to exit")
        return True  # did block

    def block_on_mutex(self, tid: int, mutex_addr: int) -> bool:
        """Returns True if thread actually blocked (mutex was held)."""
        tcb = self.threads[tid]
        tcb.status = ThreadStatus.BLOCKED
        tcb.blocking_on = mutex_addr
        if self.verbose:
            self._log(f"[MUTEX BLOCK] tid={tid} name={tcb.name!r}"
                      f" blocked waiting for mutex @ 0x{mutex_addr:04x}")
        return True

    def unblock_mutex_waiters(self, mutex_addr: int):
        """Wake the first thread waiting on this mutex address."""
        for tid, tcb in self.threads.items():
            if tcb.status == ThreadStatus.BLOCKED and tcb.blocking_on == mutex_addr:
                tcb.status = ThreadStatus.RUNNABLE
                tcb.blocking_on = -1
                self.run_queue.append(tid)
                if self.verbose:
                    self._log(f"[MUTEX UNBLOCK] tid={tid} name={tcb.name!r}"
                              f" unblocked (mutex @ 0x{mutex_addr:04x} released)")
                return   # wake only one (ownership transfer semantics)

    #  Context switch 

    def save_context(self, tid: int, regs: List[int], pc: int):
        """Save the running thread's register file and PC into its TCB."""
        tcb = self.threads[tid]
        tcb.saved_regs = list(regs)
        tcb.saved_pc = pc

    def restore_context(self, tid: int) -> tuple:
        """Return (regs_copy, pc) for the next thread to run."""
        tcb = self.threads[tid]
        return list(tcb.saved_regs), tcb.saved_pc

    def switch(self, vm_regs: List[int], vm_pc: int,
               reason: str) -> Optional[int]:
        """
        Perform a context switch.

        Saves the current thread, picks the next runnable thread from the queue,
        restores its context into vm_regs / vm_pc.  Returns the new tid, or None
        if no runnable threads exist (all done or all blocked — deadlock).
        """
        old_tid  = self.current_tid
        old_tcb  = self.threads.get(old_tid)

        #  Save current context 
        if old_tcb and old_tcb.status == ThreadStatus.RUNNING:
            old_tcb.status = ThreadStatus.RUNNABLE
            self.save_context(old_tid, vm_regs, vm_pc)
            self.run_queue.append(old_tid)

        #  Pick next runnable thread 
        new_tid = None
        while self.run_queue:
            candidate = self.run_queue.popleft()
            tcb = self.threads[candidate]
            if tcb.status == ThreadStatus.RUNNABLE:
                new_tid = candidate
                break

        if new_tid is None:
            # Check for active threads (not all exited)
            alive = [t for t in self.threads.values()
                     if t.status not in (ThreadStatus.EXITED,)]
            if alive:
                self._log("[DEADLOCK?] No runnable threads but some are still alive.")
            return None

        new_tcb = self.threads[new_tid]
        new_tcb.status = ThreadStatus.RUNNING
        self.current_tid = new_tid
        self._tick = 0  # reset quantum timer
        self.switch_count += 1   # always count

        #  Log the switch 
        if self.verbose:
            msg_parts = [
                f"\n{'─'*70}",
                f"  CONTEXT SWITCH  ({reason})",
                f"{'─'*70}",
            ]
            if old_tcb:
                msg_parts += [
                    f"  OUT <- tid={old_tid} [{old_tcb.thread_type}] {old_tcb.name!r}",
                    f"        PC saved  = 0x{vm_pc:04x}",
                    f"        SP saved  = 0x{vm_regs[2]:04x}",
                    f"        ra saved  = 0x{vm_regs[1]:04x}",
                    f"        ran {old_tcb.instruction_count} instructions total",
                ]
            new_regs, new_pc = self.restore_context(new_tid)
            msg_parts += [
                f"  IN  -> tid={new_tid} [{new_tcb.thread_type}] {new_tcb.name!r}",
                f"        PC restore = 0x{new_pc:04x}",
                f"        SP restore = 0x{new_regs[2]:04x}",
                f"        ra restore = 0x{new_regs[1]:04x}",
                f"{'─'*70}\n",
            ]
            entry = "\n".join(msg_parts)
            print(entry)
            self.switch_log.append(entry)

        #  Restore next thread 
        new_regs, new_pc = self.restore_context(new_tid)
        vm_regs[:] = new_regs
        return new_tid, new_pc   # caller updates vm.pc

    def maybe_preempt(self, tid: int, regs: List[int], pc: int) -> Optional[tuple]:
        """
        Called after every instruction.

        Green threads: never preempt (returns None).
        Kernel threads: preempt when tick reaches QUANTUM.
        """
        tcb = self.threads.get(tid)
        if tcb is None:
            return None
        tcb.instruction_count += 1
        if tcb.thread_type == 'green':
            return None   # cooperative only
        # Kernel thread — check quantum
        self._tick += 1
        if self._tick >= self.QUANTUM:
            # Check if there's actually another runnable thread to switch to
            others = [t for t in self.run_queue
                      if self.threads[t].status == ThreadStatus.RUNNABLE and t != tid]
            if others:
                return self.switch(regs, pc, f"TIMER tick={self.tick_total}")
        return None

    @property
    def tick_total(self):
        return sum(t.instruction_count for t in self.threads.values())

    def all_done(self) -> bool:
        return all(t.status == ThreadStatus.EXITED for t in self.threads.values())

    def _log(self, msg: str):
        print(msg)
        self.switch_log.append(msg)

    def print_summary(self, mode: str = '?', quantum: int = 0):
        print("\n" + "-"*70)
        print("  THREAD EXECUTION SUMMARY")
        mode_desc = {
            'green':  'cooperative — switches on YIELD/EXIT/JOIN only',
            'kernel': f'preemptive — timer every {quantum} instructions',
        }.get(mode, mode)
        print(f"  scheduling: {mode_desc}")
        print("-"*70)
        total_instrs = 0
        for tcb in self.threads.values():
            print(f"  tid={tcb.tid}  [{tcb.thread_type:6s}]  {tcb.name!r:20s}"
                  f"  status={tcb.status.name:8s}  instructions={tcb.instruction_count}")
            total_instrs += tcb.instruction_count
        print("-"*70)
        print(f"  Total instructions  : {total_instrs}")
        print(f"  Context switches    : {self.switch_count}")
        print("-"*70 + "\n")


 
# VM

class ConcurrentRISCVVM:
    """
    RISC-V RV32IM VM with concurrent thread support.

    Inherits the full instruction set of the original VM and adds:
    - Thread scheduling (green + kernel)
    - FENCE instruction (memory barrier annotation)
    - Extended syscall table (see module docstring)
    """

    REG_NAMES = [
        'zero','ra','sp','gp','tp','t0','t1','t2',
        's0','s1','a0','a1','a2','a3','a4','a5',
        'a6','a7','s2','s3','s4','s5','s6','s7',
        's8','s9','s10','s11','t3','t4','t5','t6'
    ]

    # Stack layout: 8 threads × 4 KiB each, stacks grow down from high address
    STACK_BASE   = 0x8000
    STACK_SIZE   = 0x1000   # 4 KiB per thread
    MAX_THREADS  = 8

    def __init__(self,
                 mem_size:    int  = 0x20000,   # 128 KiB
                 debug:       bool = False,
                 trace:       bool = False,
                 thread_mode: str  = 'green',   # 'green' or 'kernel'
                 quantum:     int  = 10):
        self.regs    = [0] * 32
        self.pc      = 0
        self.memory  = bytearray(mem_size)
        self.running = True
        self.debug   = debug
        self.trace   = trace
        self.thread_mode = thread_mode
        self.instruction_count = 0

        self.scheduler = Scheduler(verbose=(debug or trace))
        self.scheduler.QUANTUM = quantum

        # Barrier log (for teaching memory ordering)
        self.barrier_log: List[dict] = []

    #  Memory 

    def signed(self, val: int) -> int:
        val &= 0xFFFFFFFF
        return val - 0x100000000 if val & 0x80000000 else val

    def unsigned(self, val: int) -> int:
        return val & 0xFFFFFFFF

    def sign_extend(self, val: int, bits: int) -> int:
        mask = 1 << (bits - 1)
        return val | (~((1 << bits) - 1)) if val & mask else val

    def read_mem(self, addr: int, size: int, signed: bool = False) -> int:
        addr &= 0xFFFFFFFF
        if addr + size > len(self.memory):
            raise ValueError(f"Memory OOB read @ 0x{addr:08x}")
        if size == 1:
            v = self.memory[addr]
            return self.sign_extend(v, 8) if signed else v
        elif size == 2:
            v = struct.unpack_from('<H', self.memory, addr)[0]
            return self.sign_extend(v, 16) if signed else v
        else:
            return struct.unpack_from('<I', self.memory, addr)[0]

    def write_mem(self, addr: int, val: int, size: int):
        addr &= 0xFFFFFFFF
        if addr + size > len(self.memory):
            raise ValueError(f"Memory OOB write @ 0x{addr:08x}")
        if size == 1:
            self.memory[addr] = val & 0xFF
        elif size == 2:
            struct.pack_into('<H', self.memory, addr, val & 0xFFFF)
        else:
            struct.pack_into('<I', self.memory, addr, val & 0xFFFFFFFF)

    #  Program loading 

    def load_program(self, filename: str):
        with open(filename, 'rb') as f:
            prog = f.read()
        self.memory[:len(prog)] = prog
        if self.debug:
            print(f"Loaded {len(prog)} bytes")

    def load_bytes(self, data: bytes):
        self.memory[:len(data)] = data

    #  Decode 

    def decode(self, word: int) -> Instruction:
        opcode = word & 0x7F
        rd     = (word >> 7)  & 0x1F
        funct3 = (word >> 12) & 0x7
        rs1    = (word >> 15) & 0x1F
        rs2    = (word >> 20) & 0x1F
        funct7 = (word >> 25) & 0x7F

        #  FENCE (MISC-MEM) ~ very simple encoding, no funct7, just log it as a memory barrier
        if opcode == 0b0001111:
            return Instruction('FENCE', funct3=funct3)

        #  R-type 
        if opcode == 0b0110011:
            if funct7 == 0b0000000:
                ops = {0:'ADD',4:'XOR',6:'OR',7:'AND',1:'SLL',5:'SRL',2:'SLT',3:'SLTU'}
                op = ops.get(funct3)
                if op is None: raise ValueError("Unknown R-type funct3")
            elif funct7 == 0b0100000:
                ops = {0:'SUB',5:'SRA'}
                op = ops.get(funct3)
                if op is None: raise ValueError("Unknown R-type funct3")
            elif funct7 == 0b0000001:
                ops = {0:'MUL',1:'MULH',2:'MULHSU',3:'MULHU',4:'DIV',5:'DIVU',6:'REM',7:'REMU'}
                op = ops.get(funct3)
                if op is None: raise ValueError("Unknown M funct3")
            else:
                raise ValueError("Unknown R-type funct7")
            return Instruction(op, rd=rd, rs1=rs1, rs2=rs2, funct3=funct3, funct7=funct7)

        #  I-type arithmetic / shifts 
        elif opcode == 0b0010011:
            imm = self.sign_extend(word >> 20, 12)
            if funct3 == 0:   op = 'ADDI'
            elif funct3 == 4: op = 'XORI'
            elif funct3 == 6: op = 'ORI'
            elif funct3 == 7: op = 'ANDI'
            elif funct3 == 2: op = 'SLTI'
            elif funct3 == 3: op = 'SLTIU'
            elif funct3 == 1:
                op = 'SLLI'; imm = imm & 0x1F
            elif funct3 == 5:
                shamt = imm & 0x1F
                op = 'SRAI' if (word >> 25) == 0b0100000 else 'SRLI'
                imm = shamt
            else:
                raise ValueError("Unknown I-type funct3")
            return Instruction(op, rd=rd, rs1=rs1, imm=imm, funct3=funct3)

        #  Loads 
        elif opcode == 0b0000011:
            imm = self.sign_extend(word >> 20, 12)
            ops = {0:'LB',1:'LH',2:'LW',4:'LBU',5:'LHU'}
            op  = ops.get(funct3)
            if op is None: raise ValueError("Unknown load funct3")
            return Instruction(op, rd=rd, rs1=rs1, imm=imm, funct3=funct3)

        #  Stores 
        elif opcode == 0b0100011:
            imm = self.sign_extend(((word>>25)&0x7F)<<5 | ((word>>7)&0x1F), 12)
            ops = {0:'SB',1:'SH',2:'SW'}
            op  = ops.get(funct3)
            if op is None: raise ValueError("Unknown store funct3")
            return Instruction(op, rs1=rs1, rs2=rs2, imm=imm, funct3=funct3)

        #  Branches 
        elif opcode == 0b1100011:
            imm = self.sign_extend(
                ((word>>31)&1)<<12 | ((word>>7)&1)<<11 |
                ((word>>25)&0x3F)<<5 | ((word>>8)&0xF)<<1, 13)
            ops = {0:'BEQ',1:'BNE',4:'BLT',5:'BGE',6:'BLTU',7:'BGEU'}
            op  = ops.get(funct3)
            if op is None: raise ValueError("Unknown branch funct3")
            return Instruction(op, rs1=rs1, rs2=rs2, imm=imm, funct3=funct3)

        #  JAL 
        elif opcode == 0b1101111:
            imm = self.sign_extend(
                ((word>>31)&1)<<20 | ((word>>12)&0xFF)<<12 |
                ((word>>20)&1)<<11 | ((word>>21)&0x3FF)<<1, 21)
            return Instruction('JAL', rd=rd, imm=imm)

        #  JALR 
        elif opcode == 0b1100111:
            imm = self.sign_extend(word >> 20, 12)
            return Instruction('JALR', rd=rd, rs1=rs1, imm=imm, funct3=funct3)

        #  LUI / AUIPC 
        elif opcode == 0b0110111:
            return Instruction('LUI', rd=rd, imm=word>>12)
        elif opcode == 0b0010111:
            return Instruction('AUIPC', rd=rd, imm=word>>12)

        #  System 
        elif opcode == 0b1110011:
            if word == 0x00000073: return Instruction('ECALL')
            if word == 0x00100073: return Instruction('EBREAK')
            raise ValueError("Unknown system instruction")

        raise ValueError(f"Unknown opcode: 0b{opcode:07b} @ PC=0x{self.pc:04x}")

    #  Format for trace 

    def fmt(self, instr: Instruction) -> str:
        op, n = instr.opcode, self.REG_NAMES
        if op in ('ADD','SUB','AND','OR','XOR','SLL','SRL','SRA','SLT','SLTU',
                  'MUL','MULH','MULHSU','MULHU','DIV','DIVU','REM','REMU'):
            return f"{op} {n[instr.rd]},{n[instr.rs1]},{n[instr.rs2]}"
        if op in ('ADDI','ANDI','ORI','XORI','SLTI','SLTIU','SLLI','SRLI','SRAI'):
            return f"{op} {n[instr.rd]},{n[instr.rs1]},{instr.imm}"
        if op in ('LB','LH','LW','LBU','LHU'):
            return f"{op} {n[instr.rd]},{instr.imm}({n[instr.rs1]})"
        if op in ('SB','SH','SW'):
            return f"{op} {n[instr.rs2]},{instr.imm}({n[instr.rs1]})"
        if op in ('BEQ','BNE','BLT','BGE','BLTU','BGEU'):
            return f"{op} {n[instr.rs1]},{n[instr.rs2]},0x{(self.pc+instr.imm)&0xFFFFFFFF:x}"
        if op == 'JAL':
            return f"JAL {n[instr.rd]},0x{(self.pc+instr.imm)&0xFFFFFFFF:x}"
        if op == 'JALR':
            return f"JALR {n[instr.rd]},{instr.imm}({n[instr.rs1]})"
        if op in ('LUI','AUIPC'):
            return f"{op} {n[instr.rd]},0x{instr.imm:x}"
        if op == 'FENCE':
            return f"FENCE  <- memory barrier"
        return f"{op}"

    #  Execution loop 

    def execute(self):
        """Main execution loop with scheduler integration."""
        sched = self.scheduler
        current_tid = sched.current_tid

        if self.debug:
            mode_desc = {
                'green':  'cooperative (threads switch only on YIELD/EXIT/JOIN)',
                'kernel': f'preemptive (timer fires every {self.scheduler.QUANTUM} instructions)',
            }.get(self.thread_mode, self.thread_mode)
            print(f"\n{'═'*70}")
            print(f"  VM START")
            print(f"  mode    : {self.thread_mode}  —  {mode_desc}")
            print(f"  threads : {len(sched.threads)}")
            print(f"  memory  : {len(self.memory)//1024} KiB")
            print(f"{'═'*70}\n")

        while self.running:
            # Stop if no runnable threads remain
            if sched.all_done():
                break
            if sched.current_tid == -1:
                # Scheduler has no current thread — pick first
                result = sched.switch(self.regs, self.pc, "initial dispatch")
                if result is None:
                    break
                sched.current_tid, self.pc = result

            # PC out of memory -> thread probably fell off the end
            if self.pc >= len(self.memory):
                if self.debug:
                    print(f"PC 0x{self.pc:04x} out of bounds — ending thread {sched.current_tid}")
                self._do_thread_exit()
                continue

            # Fetch & decode
            word = self.read_mem(self.pc, 4)
            try:
                instr = self.decode(word)
            except Exception as e:
                print(f"Decode error @ 0x{self.pc:04x}: {e}")
                self.running = False
                break

            tid  = sched.current_tid
            tname = sched.threads[tid].name if tid in sched.threads else '?'

            if self.trace:
                print(f"  [tid={tid} {tname:10s}] 0x{self.pc:04x}: {word:08x}  {self.fmt(instr)}")

            # Execute
            try:
                self.execute_instruction(instr)
                self.instruction_count += 1
            except Exception as e:
                print(f"Execute error @ 0x{self.pc:04x}: {e}")
                import traceback; traceback.print_exc()
                self.running = False
                break

            # x0 always zero
            self.regs[0] = 0

            # Scheduler tick — may preempt (kernel threads only)
            result = sched.maybe_preempt(sched.current_tid, self.regs, self.pc)
            if result is not None:
                sched.current_tid, self.pc = result

        if self.debug or True:
            sched.print_summary(mode=self.thread_mode, quantum=self.scheduler.QUANTUM)

    #  Instruction execution 

    def execute_instruction(self, instr: Instruction):
        op = instr.opcode
        r  = self.regs

        #  FENCE — log it and continue (no actual memory ordering semantics in this VM, but we want to teach the concept)
        if op == 'FENCE':
            tid = self.scheduler.current_tid
            tname = self.scheduler.threads[tid].name if tid >= 0 else '?'
            entry = {
                'tid': tid, 'name': tname,
                'pc': self.pc,
                'instruction_count': self.instruction_count,
            }
            self.barrier_log.append(entry)
            if self.debug or self.trace:
                print(f"  MEMORY BARRIER  tid={tid} {tname!r}  PC=0x{self.pc:04x}"
                      f"  (ensures prior stores visible before subsequent loads)")
            self.pc += 4
            return

        #  R-type
        if op == 'ADD':
            r[instr.rd] = (r[instr.rs1] + r[instr.rs2]) & 0xFFFFFFFF; self.pc += 4
        elif op == 'SUB':
            r[instr.rd] = (r[instr.rs1] - r[instr.rs2]) & 0xFFFFFFFF; self.pc += 4
        elif op == 'AND':
            r[instr.rd] = (r[instr.rs1] & r[instr.rs2]) & 0xFFFFFFFF; self.pc += 4
        elif op == 'OR':
            r[instr.rd] = (r[instr.rs1] | r[instr.rs2]) & 0xFFFFFFFF; self.pc += 4
        elif op == 'XOR':
            r[instr.rd] = (r[instr.rs1] ^ r[instr.rs2]) & 0xFFFFFFFF; self.pc += 4
        elif op == 'SLL':
            r[instr.rd] = (r[instr.rs1] << (r[instr.rs2]&0x1F)) & 0xFFFFFFFF; self.pc += 4
        elif op == 'SRL':
            r[instr.rd] = (self.unsigned(r[instr.rs1]) >> (r[instr.rs2]&0x1F)) & 0xFFFFFFFF; self.pc += 4
        elif op == 'SRA':
            r[instr.rd] = (self.signed(r[instr.rs1]) >> (r[instr.rs2]&0x1F)) & 0xFFFFFFFF; self.pc += 4
        elif op == 'SLT':
            r[instr.rd] = 1 if self.signed(r[instr.rs1]) < self.signed(r[instr.rs2]) else 0; self.pc += 4
        elif op == 'SLTU':
            r[instr.rd] = 1 if self.unsigned(r[instr.rs1]) < self.unsigned(r[instr.rs2]) else 0; self.pc += 4
        elif op == 'MUL':
            r[instr.rd] = (self.signed(r[instr.rs1]) * self.signed(r[instr.rs2])) & 0xFFFFFFFF; self.pc += 4
        elif op == 'MULH':
            r[instr.rd] = ((self.signed(r[instr.rs1]) * self.signed(r[instr.rs2])) >> 32) & 0xFFFFFFFF; self.pc += 4
        elif op == 'MULHU':
            r[instr.rd] = ((self.unsigned(r[instr.rs1]) * self.unsigned(r[instr.rs2])) >> 32) & 0xFFFFFFFF; self.pc += 4
        elif op == 'MULHSU':
            r[instr.rd] = ((self.signed(r[instr.rs1]) * self.unsigned(r[instr.rs2])) >> 32) & 0xFFFFFFFF; self.pc += 4
        elif op == 'DIV':
            a,b = self.signed(r[instr.rs1]), self.signed(r[instr.rs2])
            r[instr.rd] = (0xFFFFFFFF if b==0 else (0x80000000 if a==-0x80000000 and b==-1 else (a//b))) & 0xFFFFFFFF; self.pc += 4
        elif op == 'DIVU':
            a,b = self.unsigned(r[instr.rs1]), self.unsigned(r[instr.rs2])
            r[instr.rd] = (0xFFFFFFFF if b==0 else a//b) & 0xFFFFFFFF; self.pc += 4
        elif op == 'REM':
            a,b = self.signed(r[instr.rs1]), self.signed(r[instr.rs2])
            r[instr.rd] = (a if b==0 else (0 if a==-0x80000000 and b==-1 else a%b)) & 0xFFFFFFFF; self.pc += 4
        elif op == 'REMU':
            a,b = self.unsigned(r[instr.rs1]), self.unsigned(r[instr.rs2])
            r[instr.rd] = (a if b==0 else a%b) & 0xFFFFFFFF; self.pc += 4

        #  I-type arithmetic 
        elif op == 'ADDI':
            r[instr.rd] = (r[instr.rs1] + instr.imm) & 0xFFFFFFFF; self.pc += 4
        elif op == 'ANDI':
            r[instr.rd] = (r[instr.rs1] & instr.imm) & 0xFFFFFFFF; self.pc += 4
        elif op == 'ORI':
            r[instr.rd] = (r[instr.rs1] | instr.imm) & 0xFFFFFFFF; self.pc += 4
        elif op == 'XORI':
            r[instr.rd] = (r[instr.rs1] ^ instr.imm) & 0xFFFFFFFF; self.pc += 4
        elif op == 'SLTI':
            r[instr.rd] = 1 if self.signed(r[instr.rs1]) < self.signed(instr.imm) else 0; self.pc += 4
        elif op == 'SLTIU':
            r[instr.rd] = 1 if self.unsigned(r[instr.rs1]) < self.unsigned(instr.imm) else 0; self.pc += 4
        elif op == 'SLLI':
            r[instr.rd] = (r[instr.rs1] << instr.imm) & 0xFFFFFFFF; self.pc += 4
        elif op == 'SRLI':
            r[instr.rd] = (self.unsigned(r[instr.rs1]) >> instr.imm) & 0xFFFFFFFF; self.pc += 4
        elif op == 'SRAI':
            r[instr.rd] = (self.signed(r[instr.rs1]) >> instr.imm) & 0xFFFFFFFF; self.pc += 4

        #  Loads 
        elif op == 'LB':
            r[instr.rd] = self.read_mem((r[instr.rs1]+instr.imm)&0xFFFFFFFF,1,signed=True)&0xFFFFFFFF; self.pc+=4
        elif op == 'LH':
            r[instr.rd] = self.read_mem((r[instr.rs1]+instr.imm)&0xFFFFFFFF,2,signed=True)&0xFFFFFFFF; self.pc+=4
        elif op == 'LW':
            r[instr.rd] = self.read_mem((r[instr.rs1]+instr.imm)&0xFFFFFFFF,4)&0xFFFFFFFF; self.pc+=4
        elif op == 'LBU':
            r[instr.rd] = self.read_mem((r[instr.rs1]+instr.imm)&0xFFFFFFFF,1)&0xFFFFFFFF; self.pc+=4
        elif op == 'LHU':
            r[instr.rd] = self.read_mem((r[instr.rs1]+instr.imm)&0xFFFFFFFF,2)&0xFFFFFFFF; self.pc+=4

        #  Stores 
        elif op == 'SB':
            self.write_mem((r[instr.rs1]+instr.imm)&0xFFFFFFFF, r[instr.rs2], 1); self.pc+=4
        elif op == 'SH':
            self.write_mem((r[instr.rs1]+instr.imm)&0xFFFFFFFF, r[instr.rs2], 2); self.pc+=4
        elif op == 'SW':
            self.write_mem((r[instr.rs1]+instr.imm)&0xFFFFFFFF, r[instr.rs2], 4); self.pc+=4

        #  Branches 
        elif op == 'BEQ':
            self.pc = (self.pc+instr.imm)&0xFFFFFFFF if r[instr.rs1]==r[instr.rs2] else self.pc+4
        elif op == 'BNE':
            self.pc = (self.pc+instr.imm)&0xFFFFFFFF if r[instr.rs1]!=r[instr.rs2] else self.pc+4
        elif op == 'BLT':
            self.pc = (self.pc+instr.imm)&0xFFFFFFFF if self.signed(r[instr.rs1])<self.signed(r[instr.rs2]) else self.pc+4
        elif op == 'BGE':
            self.pc = (self.pc+instr.imm)&0xFFFFFFFF if self.signed(r[instr.rs1])>=self.signed(r[instr.rs2]) else self.pc+4
        elif op == 'BLTU':
            self.pc = (self.pc+instr.imm)&0xFFFFFFFF if self.unsigned(r[instr.rs1])<self.unsigned(r[instr.rs2]) else self.pc+4
        elif op == 'BGEU':
            self.pc = (self.pc+instr.imm)&0xFFFFFFFF if self.unsigned(r[instr.rs1])>=self.unsigned(r[instr.rs2]) else self.pc+4

        #  Jumps 
        elif op == 'JAL':
            r[instr.rd] = (self.pc+4)&0xFFFFFFFF
            self.pc = (self.pc+instr.imm)&0xFFFFFFFF
        elif op == 'JALR':
            tmp = (self.pc+4)&0xFFFFFFFF
            self.pc = (r[instr.rs1]+instr.imm)&0xFFFFFFFE
            r[instr.rd] = tmp

        #  Upper immediate 
        elif op == 'LUI':
            r[instr.rd] = (instr.imm << 12) & 0xFFFFFFFF; self.pc += 4
        elif op == 'AUIPC':
            r[instr.rd] = (self.pc + (instr.imm << 12)) & 0xFFFFFFFF; self.pc += 4

        #  System 
        elif op == 'ECALL':
            self._handle_syscall()
            # pc advanced inside syscall handlers that don't switch (most of them)
        elif op == 'EBREAK':
            if self.debug:
                print("EBREAK hit — halting")
            self.running = False

        else:
            raise ValueError(f"Unknown opcode: {op}")

    #  Syscall handler 

    def _handle_syscall(self):
        num = self.regs[17]   # a7
        sched = self.scheduler

        #  Legacy I/O 
        if num == 1:   # print_int
            val = self.signed(self.regs[10])
            tid = sched.current_tid
            tname = sched.threads[tid].name if tid >= 0 else '?'
            print(f"  [tid={tid} {tname}] {val}")
            self.pc += 4

        elif num == 4:  # print_str
            addr = self.regs[10]
            chars = []
            while addr < len(self.memory):
                ch = self.memory[addr]
                if ch == 0: break
                chars.append(chr(ch))
                addr += 1
            tid = sched.current_tid
            tname = sched.threads[tid].name if tid >= 0 else '?'
            print(f"  [tid={tid} {tname}] {''.join(chars)}", end='')
            self.pc += 4

        elif num == 10:  # exit (whole VM halt — mark current thread exited too)
            tid = sched.current_tid
            if tid >= 0 and tid in sched.threads:
                sched.exit_thread(tid)
            self.running = False
            self.pc += 4

        elif num == 11:  # print_char
            print(chr(self.regs[10] & 0xFF), end='')
            self.pc += 4

        #  Threading syscalls 

        elif num == 20:  # yield
            self.pc += 4   # advance past ECALL before saving context
            tid = sched.current_tid
            tcb = sched.threads[tid]
            tcb.status = ThreadStatus.RUNNABLE
            sched.save_context(tid, self.regs, self.pc)
            sched.run_queue.append(tid)
            result = sched._pick_next(self.regs, self.pc, "YIELD")
            if result is not None:
                sched.current_tid, self.pc = result

        elif num == 21:  # thread_create
            entry = self.regs[10]   # a0 = entry point
            arg   = self.regs[11]   # a1 = argument

            new_tid = sched._next_tid
            # Allocate stack for new thread
            stack_top = self.STACK_BASE + (new_tid + 1) * self.STACK_SIZE
            if stack_top > len(self.memory):
                print(f"ERROR: Out of stack space for thread {new_tid}")
                self.regs[10] = 0xFFFFFFFF
                self.pc += 4
                return

            init_regs = [0] * 32
            init_regs[10] = arg  # a0 = argument passed to thread
            init_regs[2]  = stack_top  # sp

            sched.create_thread(
                name=f"thread-{new_tid}",
                thread_type=self.thread_mode,
                entry_pc=entry,
                init_regs=init_regs,
                stack_top=stack_top,
            )
            self.regs[10] = new_tid   # return tid in a0
            self.pc += 4

        elif num == 22:  # thread_exit
            self._do_thread_exit()
            # _do_thread_exit handles pc update via scheduler switch

        elif num == 23:  # thread_join
            target_tid = self.regs[10]
            if target_tid not in sched.threads:
                self.regs[10] = -1  # error
                self.pc += 4
                return
            self.pc += 4   # advance past ECALL
            blocked = sched.block_on_join(sched.current_tid, target_tid)
            if blocked:
                sched.save_context(sched.current_tid, self.regs, self.pc)
                result = sched._pick_next(self.regs, self.pc, f"JOIN tid={target_tid}")
                if result is not None:
                    sched.current_tid, self.pc = result

        elif num == 24:  # get_tid  — result already lands in a0 (reg 10) via caller's mv
            self.regs[10] = sched.current_tid & 0xFFFFFFFF
            self.pc += 4

        elif num == 25:  # mutex_lock
            mutex_addr = self.regs[10]
            current_val = self.read_mem(mutex_addr, 4)
            if current_val == 0:
                # Free — acquire it
                self.write_mem(mutex_addr, 1, 4)
                if self.debug:
                    print(f"  [MUTEX LOCK] tid={sched.current_tid} acquired 0x{mutex_addr:04x}")
                self.pc += 4
            else:
                # Held — block
                self.pc += 4
                sched.save_context(sched.current_tid, self.regs, self.pc)
                sched.block_on_mutex(sched.current_tid, mutex_addr)
                result = sched._pick_next(self.regs, self.pc, f"MUTEX_BLOCK addr=0x{mutex_addr:04x}")
                if result is not None:
                    sched.current_tid, self.pc = result

        elif num == 26:  # mutex_unlock
            mutex_addr = self.regs[10]
            self.write_mem(mutex_addr, 0, 4)
            if self.debug:
                print(f"  [MUTEX UNLOCK] tid={sched.current_tid} released 0x{mutex_addr:04x}")
            sched.unblock_mutex_waiters(mutex_addr)
            self.pc += 4

        else:
            if self.debug:
                print(f"Unknown syscall {num}")
            self.pc += 4

    def _do_thread_exit(self):
        sched = self.scheduler
        tid   = sched.current_tid
        sched.exit_thread(tid)
        result = sched._pick_next(self.regs, self.pc, f"THREAD_EXIT tid={tid}")
        if result is not None:
            sched.current_tid, self.pc = result
        elif sched.all_done():
            self.running = False

    def print_regs(self):
        print("\n-- Register State --")
        for i in range(0, 32, 4):
            parts = []
            for j in range(4):
                if i+j < 32:
                    parts.append(f"{self.REG_NAMES[i+j]:4s}=0x{self.regs[i+j]:08x}")
            print("  ".join(parts))


# Attach _pick_next as a helper method on Scheduler
def _sched_pick_next(self, vm_regs, vm_pc, reason):
    """Pick next runnable thread and switch. Returns (new_tid, new_pc) or None."""
    old_tid = self.current_tid
    old_tcb = self.threads.get(old_tid)

    new_tid = None
    while self.run_queue:
        candidate = self.run_queue.popleft()
        tcb = self.threads[candidate]
        if tcb.status == ThreadStatus.RUNNABLE:
            new_tid = candidate
            break

    if new_tid is None:
        alive = [t for t in self.threads.values() if t.status != ThreadStatus.EXITED]
        if alive and self.verbose:
            self._log(f"[SCHEDULER] No runnable threads ({len(alive)} blocked/waiting)")
        return None

    new_tcb = self.threads[new_tid]
    new_tcb.status = ThreadStatus.RUNNING
    self.current_tid = new_tid
    self._tick = 0
    self.switch_count += 1   # always count, regardless of verbosity

    if self.verbose:
        old_info = f"tid={old_tid} {old_tcb.name!r}" if old_tcb else "(none)"
        new_regs, new_pc = self.restore_context(new_tid)
        msg = (
            f"\n{'─'*70}\n"
            f"  CONTEXT SWITCH  ({reason})\n"
            f"{'─'*70}\n"
            f"  OUT <- {old_info}\n"
            f"         PC saved   = 0x{vm_pc:04x}  SP = 0x{vm_regs[2]:04x}\n"
            f"  IN  -> tid={new_tid} [{new_tcb.thread_type}] {new_tcb.name!r}\n"
            f"         PC restore = 0x{new_pc:04x}  SP = 0x{new_regs[2]:04x}\n"
            f"{'─'*70}\n"
        )
        print(msg)
        self.switch_log.append(msg)

    new_regs, new_pc = self.restore_context(new_tid)
    vm_regs[:] = new_regs
    return new_tid, new_pc

Scheduler._pick_next = _sched_pick_next


# Demo runner — assembles + runs inline examples without needing the assembler

def encode_addi(rd, rs1, imm):
    funct3 = 0b000
    imm12  = imm & 0xFFF
    return (imm12<<20)|(rs1<<15)|(funct3<<12)|(rd<<7)|0b0010011

def encode_li(rd, imm):
    return encode_addi(rd, 0, imm)

def encode_ecall():
    return 0x00000073

def encode_fence():
    return 0x0000000F   # FENCE iorw,iorw

def encode_jal(rd, offset):
    imm = offset & 0x1FFFFF
    b20    = (imm>>20)&1
    b19_12 = (imm>>12)&0xFF
    b11    = (imm>>11)&1
    b10_1  = (imm>>1)&0x3FF
    return (b20<<31)|(b10_1<<21)|(b11<<20)|(b19_12<<12)|(rd<<7)|0b1101111

def encode_jalr(rd, rs1, imm=0):
    imm12 = imm & 0xFFF
    return (imm12<<20)|(rs1<<15)|(0<<12)|(rd<<7)|0b1100111

def encode_sw(rs2, rs1, imm):
    imm12 = imm & 0xFFF
    imm11_5 = (imm12>>5)&0x7F
    imm4_0  = imm12&0x1F
    return (imm11_5<<25)|(rs2<<20)|(rs1<<15)|(0b010<<12)|(imm4_0<<7)|0b0100011

def encode_lw(rd, rs1, imm):
    imm12 = imm & 0xFFF
    return (imm12<<20)|(rs1<<15)|(0b010<<12)|(rd<<7)|0b0000011

def encode_add(rd, rs1, rs2):
    return (0<<25)|(rs2<<20)|(rs1<<15)|(0<<12)|(rd<<7)|0b0110011

def encode_bne(rs1, rs2, offset):
    imm13 = offset & 0x1FFF
    b12   = (imm13>>12)&1
    b11   = (imm13>>11)&1
    b10_5 = (imm13>>5)&0x3F
    b4_1  = (imm13>>1)&0xF
    return (b12<<31)|(b10_5<<25)|(rs2<<20)|(rs1<<15)|(0b001<<12)|(b4_1<<8)|(b11<<7)|0b1100011

def pack(*words):
    return b''.join(struct.pack('<I', w) for w in words)



def demo_green_threads():
    """
    Green thread demo: two cooperative threads, each prints its TID three times
    then YIELDs.  Illustrates voluntary context switching.

    Register usage:
      a7 = syscall number
      a0 = syscall arg / return
      t0 = loop counter
      t1 = iteration limit
    """
    print("\n" + "-"*70)
    print("  DEMO 1: GREEN THREADS (cooperative, YIELD-based)")
    print("-"*70)

    # - Thread body - (self-contained; entry point passed to thread_create)
    # We build the machine code by hand here because the full assembler
    # lives in a separate file. In a real workflow you'd assemble .asm files.
    #
    # thread_body:
    #   t0 = 0           # counter
    #   t1 = 3           # limit
    # loop:
    #   a7 = 24          # get_tid syscall
    #   ecall
    #   a7 = 1           # print_int (prints a0 = our tid)
    #   ecall
    #   a7 = 20          # yield
    #   ecall
    #   t0 = t0 + 1
    #   bne t0, t1, loop
    #   a7 = 22          # thread_exit
    #   ecall

    # Registers: t0=5, t1=6, a0=10, a1=11, a7=17
    t0,t1,a0,a1,a7 = 5,6,10,11,17

    thread_body_words = [
        encode_li(t0, 0),                  # 0x00: t0 = 0
        encode_li(t1, 3),                  # 0x04: t1 = 3
        # loop: (offset 0x08)
        encode_li(a7, 24),                 # 0x08: a7 = 24 (get_tid)
        encode_ecall(),                    # 0x0c: ecall -> a0 = tid
        encode_li(a7, 1),                  # 0x10: a7 = 1 (print_int)
        encode_ecall(),                    # 0x14: ecall -> prints tid
        encode_li(a7, 20),                 # 0x18: a7 = 20 (yield)
        encode_ecall(),                    # 0x1c: ecall -> yield
        encode_addi(t0, t0, 1),            # 0x20: t0++
        encode_bne(t0, t1, -(0x20-0x08)),  # 0x24: bne t0,t1,loop (offset = 0x08-0x28 = -0x20)
        encode_li(a7, 22),                 # 0x28: a7 = 22 (thread_exit)
        encode_ecall(),                    # 0x2c: ecall -> exit
    ]

    # - Main - (lives at offset right after thread body)
    # main:
    #   a0 = &thread_body   (address 0x00)
    #   a1 = 0              (arg)
    #   a7 = 21             # thread_create
    #   ecall -> tid1 in a0
    #   (repeat for second thread — same body)
    #   a7 = 22             # thread_exit (main exits, letting threads run)

    body_addr = 0  # thread body starts at address 0
    main_offset = len(thread_body_words) * 4  # 0x30

    main_words = [
        encode_li(a0, body_addr),   # a0 = entry
        encode_li(a1, 0),           # a1 = arg
        encode_li(a7, 21),          # thread_create
        encode_ecall(),
        encode_li(a0, body_addr),   # second thread, same entry
        encode_li(a1, 0),
        encode_li(a7, 21),
        encode_ecall(),
        encode_li(a7, 22),          # main thread exits
        encode_ecall(),
    ]

    program = pack(*thread_body_words) + pack(*main_words)

    vm = ConcurrentRISCVVM(debug=True, trace=True, thread_mode='green')
    vm.load_bytes(program)

    # Create the main thread manually (tid 0)
    init_regs = [0]*32
    init_regs[2] = vm.STACK_BASE + vm.STACK_SIZE   # sp for main
    vm.scheduler.create_thread(
        name='main',
        thread_type='green',
        entry_pc=main_offset,
        init_regs=init_regs,
        stack_top=vm.STACK_BASE + vm.STACK_SIZE,
    )
    vm.scheduler.current_tid = -1  # force initial dispatch

    vm.execute()


def demo_kernel_threads():
    """
    Kernel thread demo: two threads each busy-loop counting.
    The timer preempts them — no YIELD needed.
    Illustrates involuntary context switch.
    """
    print("\n" + "-"*70)
    print("  DEMO 2: KERNEL THREADS (preemptive, timer-based)")
    print("-"*70)

    t0,t1,a0,a7 = 5,6,10,17

    # count_body: prints TID then counts from 0 to 5, then exits
    count_body = [
        encode_li(t0, 0),                  # 0x00: counter = 0
        encode_li(t1, 5),                  # 0x04: limit = 5
        # loop: 0x08
        encode_li(a7, 24),                 # 0x08: get_tid
        encode_ecall(),                    # 0x0c
        encode_li(a7, 1),                  # 0x10: print_int (tid)
        encode_ecall(),                    # 0x14
        encode_addi(t0, t0, 1),            # 0x18: counter++
        encode_bne(t0, t1, -(0x18-0x08)),  # 0x1c: bne t0,t1,loop
        encode_li(a7, 22),                 # 0x20: thread_exit
        encode_ecall(),                    # 0x24
    ]

    main_offset = len(count_body)*4
    main = [
        encode_li(a0, 0),                    # entry = 0 (count_body)
        encode_li(17, 21), encode_ecall(),   # thread_create -> thread 1
        encode_li(a0, 0),
        encode_li(17, 21), encode_ecall(),   # thread_create -> thread 2
        encode_li(17, 22), encode_ecall(),   # main exits
    ]

    program = pack(*count_body) + pack(*main)

    vm = ConcurrentRISCVVM(debug=True, trace=True, thread_mode='kernel', quantum=4)
    vm.load_bytes(program)
    init_regs = [0]*32
    init_regs[2] = vm.STACK_BASE + vm.STACK_SIZE
    vm.scheduler.create_thread('main','kernel', main_offset, init_regs, vm.STACK_BASE + vm.STACK_SIZE)
    vm.scheduler.current_tid = -1
    vm.execute()


def demo_memory_barrier():
    """
    Memory barrier demo: two kernel threads share a word in memory (0x4000).
    Thread A writes then issues FENCE; thread B reads.
    The FENCE appears in the trace annotated as a visibility boundary.
    (In a real CPU this prevents store-load reordering across the barrier.)
    """
    print("\n" + "-"*70)
    print("  DEMO 3: MEMORY BARRIER (FENCE instruction)")
    print("-"*70)

    a0,a1,a7 = 10,11,17
    t0,t1    = 5,6
    SHARED   = 0x4000   # shared word address

    # Writer thread: stores value then FENCE
    # writer_body: (starts at 0x00)
    writer = [
        encode_li(t0, 0x4000 >> 12),  # lui t0, upper (won't work for small imm)
        # simpler: use addi with known address < 2048
    ]
    # SHARED = 0x4000 = 16384 — too big for 12-bit immediate.
    # Use two instructions: lui + addi approach, or just pick SHARED=0x100 for demo
    SHARED = 0x100
    MUTEX  = 0x104 # unused in this demo, but reserved for future mutex demo at same time

    # writer_body @ 0x00
    writer_body = [
        encode_li(t0, 42),              # 0x00: t0 = 42
        encode_li(t1, SHARED),          # 0x04: t1 = shared_addr
        encode_sw(t0, t1, 0),           # 0x08: mem[SHARED] = 42
        encode_fence(),                 # 0x0c: FENCE — writes above are visible
        encode_li(a7, 1),               # 0x10: print_int
        encode_li(a0, 42),              # 0x14: a0 = 42
        encode_ecall(),                 # 0x18
        encode_li(a7, 22),              # 0x1c: thread_exit
        encode_ecall(),                 # 0x20
    ]

    # reader_body @ 0x24
    reader_body = [
        encode_li(t1, SHARED),          # t1 = shared_addr
        encode_lw(a0, t1, 0),           # a0 = mem[SHARED]
        encode_fence(),                 # FENCE — ensure we see the write
        encode_li(a7, 1),               # print_int
        encode_ecall(),
        encode_li(a7, 22),
        encode_ecall(),
    ]

    writer_addr = 0
    reader_addr = len(writer_body)*4

    main_offset = reader_addr + len(reader_body)*4
    main = [
        encode_li(a0, writer_addr), encode_li(17,21), encode_ecall(),
        encode_li(a0, reader_addr), encode_li(17,21), encode_ecall(),
        encode_li(17,22), encode_ecall(),
    ]

    program = pack(*writer_body) + pack(*reader_body) + pack(*main)

    vm = ConcurrentRISCVVM(debug=True, trace=True,
                           thread_mode='kernel', quantum=3)
    vm.load_bytes(program)
    init_regs = [0]*32
    init_regs[2] = vm.STACK_BASE + vm.STACK_SIZE
    vm.scheduler.create_thread('main','kernel', main_offset, init_regs,
                               vm.STACK_BASE + vm.STACK_SIZE)
    vm.scheduler.current_tid = -1
    vm.execute()

    print(f"\nBarrier events recorded: {len(vm.barrier_log)}")
    for b in vm.barrier_log:
        print(f"  FENCE  tid={b['tid']} {b['name']!r}  PC=0x{b['pc']:04x}"
              f"  after {b['instruction_count']} instructions")




def main():
    parser = argparse.ArgumentParser(
        description='RISC-V Concurrent VM',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""\
            Examples:
              # Run a binary with green threads
              python vm_concurrent.py prog.bin --mode green --trace

              # Run with kernel (preemptive) threads, quantum=8
              python vm_concurrent.py prog.bin --mode kernel --quantum 8 --trace

              # Run built-in demos
              python vm_concurrent.py --demo green
              python vm_concurrent.py --demo kernel
              python vm_concurrent.py --demo barrier
        """)
    )
    parser.add_argument('binary',   nargs='?',  help='Binary file')
    parser.add_argument('--mode',   default='green', choices=['green','kernel'], help='Thread scheduling mode')
    parser.add_argument('--quantum',type=int, default=10, help='Instructions per quantum (kernel mode)')
    parser.add_argument('-d','--debug', action='store_true')
    parser.add_argument('-t','--trace', action='store_true')
    parser.add_argument('-r','--regs',  action='store_true')
    parser.add_argument('--entry', type=lambda x: int(x,16), default=None, metavar='HEX', help='Entry point address in hex (default: from .sym file or 0)')
    parser.add_argument('--demo', choices=['green','kernel','barrier'], help='Run a built-in demo')
    args = parser.parse_args()

    if args.demo == 'green':
        demo_green_threads()
    elif args.demo == 'kernel':
        demo_kernel_threads()
    elif args.demo == 'barrier':
        demo_memory_barrier()
    elif args.binary:
        vm = ConcurrentRISCVVM(
            debug=args.debug, trace=args.trace,
            thread_mode=args.mode, quantum=args.quantum,
        )
        vm.load_program(args.binary)

        # Determine entry point: --entry hex addr, or companion .sym file, or 0
        entry_pc = args.entry
        if entry_pc is None:
            # Look for a symbol file  prog.bin -> prog.sym  with  label addr  lines
            sym_path = args.binary.replace('.bin', '.sym')
            import os
            if os.path.exists(sym_path):
                with open(sym_path) as sf:
                    for line in sf:
                        parts = line.split()
                        if len(parts) == 2 and parts[0] == 'main':
                            entry_pc = int(parts[1], 16)
                            if args.debug:
                                print(f"Found 'main' in {sym_path} @ 0x{entry_pc:04x}")
                            break
            if entry_pc is None:
                entry_pc = 0

        init_regs = [0]*32
        init_regs[2] = vm.STACK_BASE + vm.STACK_SIZE
        vm.scheduler.create_thread('main', args.mode, entry_pc, init_regs, vm.STACK_BASE + vm.STACK_SIZE)
        vm.scheduler.current_tid = -1
        vm.execute()
        if args.regs:
            vm.print_regs()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
