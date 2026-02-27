#!/usr/bin/env python3
"""
asm_concurrent.py — RISC-V RV32IM Assembler (Concurrent Edition)
=================================================================

USAGE:
    python3 asm_concurrent.py  input.asm  output.bin  [-v] [-d]

This assembler targets the vm_concurrent.py virtual machine and supports the
full RV32IM base + M-extension instruction set, plus concurrency pseudo-ops.



INSTRUCTION SET SUMMARY

Standard RV32I:
  Arithmetic:  add, sub, and, or, xor, sll, srl, sra, slt, sltu
               addi, andi, ori, xori, slti, sltiu, slli, srli, srai
  Load/Store:  lw, lh, lb, lhu, lbu   /   sw, sh, sb
  Branch:      beq, bne, blt, bge, bltu, bgeu
  Jump:        jal, jalr
  Upper imm:   lui, auipc
  System:      ecall, ebreak, fence

M-extension:   mul, mulh, mulhu, mulhsu, div, divu, rem, remu

Standard pseudo-ops:
  nop                        → addi zero, zero, 0
  mv   rd, rs                → addi rd, rs, 0
  not  rd, rs                → xori rd, rs, -1
  neg  rd, rs                → sub  rd, zero, rs
  li   rd, imm               → addi rd, zero, imm       (12-bit values)
                             → lui rd, upper + addi rd, rd, lower  (>12-bit)
  la   rd, label             → auipc rd, upper + addi rd, rd, lower
  j    label                 → jal zero, label
  jr   rs                    → jalr zero, rs, 0
  ret                        → jalr zero, ra, 0
  call label                 → jal ra, label
  beqz rs, label             → beq  rs, zero, label
  bnez rs, label             → bne  rs, zero, label
  bltz rs, label             → blt  rs, zero, label
  bgez rs, label             → bge  rs, zero, label
  blez rs, label             → bge  zero, rs, label
  bgtz rs, label             → blt  zero, rs, label
  seqz rd, rs                → sltiu rd, rs, 1
  snez rd, rs                → sltu  rd, zero, rs

Stack helpers:
  push rs                    → addi sp, sp, -4  +  sw rs, 0(sp)
  pop  rd                    → lw rd, 0(sp)     +  addi sp, sp, 4

Concurrency pseudo-ops (vm_concurrent.py syscall interface):
  yield                      → li a7, 20; ecall
  thread.create [rd]         → li a7, 21; ecall  [; mv rd, a0 if rd≠a0]
                                 (caller sets a0=entry, a1=arg first)
  thread.exit                → li a7, 22; ecall
  thread.join  rs            → mv a0, rs; li a7, 23; ecall
  get.tid      rd            → li a7, 24; ecall  [; mv rd, a0 if rd≠a0]
  mutex.lock   rs            → mv a0, rs; li a7, 25; ecall
  mutex.unlock rs            → mv a0, rs; li a7, 26; ecall

Directives:
  .set  name, value          define integer constant (also .equ)
  .word value                emit 32-bit word
  .byte v1, v2, ...          emit bytes (padded to 4-byte alignment after)
  .space n                   emit n zero bytes
  .string "text"             emit null-terminated UTF-8, padded to 4-byte align
  .align n                   align to 2^n bytes

Comments:   # to end of line
Labels:     name:  (before instruction or on its own line)
Local labels: .name  (prefixed with dot — not exported to .sym file)
"""

import sys
import os
import struct
import argparse
from dataclasses import dataclass
from typing import List, Dict, Tuple, Optional



# Encoding helpers

def sign_extend(val: int, bits: int) -> int:
    mask = 1 << (bits - 1)
    return val - (1 << bits) if val & mask else val

def fits_signed(val: int, bits: int) -> bool:
    lo = -(1 << (bits - 1))
    hi = (1 << (bits - 1)) - 1
    return lo <= val <= hi

def split_imm32(val: int) -> Tuple[int, int]:
    """
    Split a 32-bit value into (upper20, lower12) suitable for lui+addi.
    Accounts for sign-extension: if lower12 bit 11 is set, addi will
    sign-extend it negatively, so we add 1 to upper to compensate.
    Returns (upper20, lower12_signed).
    """
    val = val & 0xFFFFFFFF
    lo = val & 0xFFF
    hi = val >> 12
    # if lo will be sign-extended as negative, compensate hi
    if lo & 0x800:
        hi = (hi + 1) & 0xFFFFF
    lo_signed = sign_extend(lo, 12)
    return hi, lo_signed



# Instruction encoding

@dataclass
class Instr:
    op:     str
    rd:     int = 0
    rs1:    int = 0
    rs2:    int = 0
    imm:    int = 0
    funct3: int = 0
    funct7: int = 0

    def encode(self) -> int:
        op = self.op
        # R-type
        if op in ('ADD','SUB','AND','OR','XOR','SLL','SRL','SRA','SLT','SLTU',
                  'MUL','MULH','MULHSU','MULHU','DIV','DIVU','REM','REMU'):
            return ((self.funct7 << 25) | (self.rs2 << 20) | (self.rs1 << 15) |
                    (self.funct3 << 12) | (self.rd << 7) | 0b0110011)
        # I-type arithmetic
        if op in ('ADDI','ANDI','ORI','XORI','SLTI','SLTIU'):
            return (((self.imm & 0xFFF) << 20) | (self.rs1 << 15) |
                    (self.funct3 << 12) | (self.rd << 7) | 0b0010011)
        # I-type shifts
        if op in ('SLLI','SRLI','SRAI'):
            shamt  = self.imm & 0x1F
            upper  = 0b0100000 if op == 'SRAI' else 0
            imm12  = (upper << 5) | shamt
            return ((imm12 << 20) | (self.rs1 << 15) |
                    (self.funct3 << 12) | (self.rd << 7) | 0b0010011)
        # Loads
        if op in ('LB','LH','LW','LBU','LHU'):
            return (((self.imm & 0xFFF) << 20) | (self.rs1 << 15) |
                    (self.funct3 << 12) | (self.rd << 7) | 0b0000011)
        # Stores
        if op in ('SB','SH','SW'):
            imm12   = self.imm & 0xFFF
            imm11_5 = (imm12 >> 5) & 0x7F
            imm4_0  = imm12 & 0x1F
            return ((imm11_5 << 25) | (self.rs2 << 20) | (self.rs1 << 15) |
                    (self.funct3 << 12) | (imm4_0 << 7) | 0b0100011)
        # Branches
        if op in ('BEQ','BNE','BLT','BGE','BLTU','BGEU'):
            i = self.imm & 0x1FFF
            return (((i>>12)&1)<<31 | ((i>>5)&0x3F)<<25 | (self.rs2<<20) |
                    (self.rs1<<15) | (self.funct3<<12) |
                    ((i>>1)&0xF)<<8 | ((i>>11)&1)<<7 | 0b1100011)
        # JAL
        if op == 'JAL':
            i = self.imm & 0x1FFFFF
            return (((i>>20)&1)<<31 | ((i>>1)&0x3FF)<<21 | ((i>>11)&1)<<20 |
                    ((i>>12)&0xFF)<<12 | (self.rd<<7) | 0b1101111)
        # JALR
        if op == 'JALR':
            return (((self.imm&0xFFF)<<20) | (self.rs1<<15) |
                    (self.funct3<<12) | (self.rd<<7) | 0b1100111)
        # LUI
        if op == 'LUI':
            return ((self.imm & 0xFFFFF) << 12) | (self.rd << 7) | 0b0110111
        # AUIPC
        if op == 'AUIPC':
            return ((self.imm & 0xFFFFF) << 12) | (self.rd << 7) | 0b0010111
        # System
        if op == 'ECALL':  return 0x00000073
        if op == 'EBREAK': return 0x00100073
        if op == 'FENCE':  return 0x0FF0000F   # FENCE iorw,iorw
        raise ValueError(f"Cannot encode: {op!r}")



# Assembler

class Assembler:
    """
    Two-pass RISC-V assembler.

    First pass:  collect labels and constants, compute addresses.
    Second pass: emit machine code, resolving all labels.

    Key design decisions:
    - Pseudo-ops that expand to multiple real instructions (li, la, push, pop,
      thread.create, etc.) must report the SAME size in both passes. This is
      enforced by _expand() which returns a list of Instr objects — the same
      function is called in both passes, so sizes are always consistent.
    - Large immediates in li/la are silently expanded; values that still don't
      fit after expansion raise a clear error.
    """

    REG_MAP: Dict[str, int] = {
        'zero':0,'ra':1,'sp':2,'gp':3,'tp':4,
        't0':5,'t1':6,'t2':7,
        's0':8,'fp':8,'s1':9,
        'a0':10,'a1':11,'a2':12,'a3':13,'a4':14,'a5':15,'a6':16,'a7':17,
        's2':18,'s3':19,'s4':20,'s5':21,'s6':22,'s7':23,
        's8':24,'s9':25,'s10':26,'s11':27,
        't3':28,'t4':29,'t5':30,'t6':31,
    }

    # funct3 for each opcode
    F3: Dict[str, int] = {
        'ADD':0,'SUB':0,'SLL':1,'SLT':2,'SLTU':3,'XOR':4,'SRL':5,'SRA':5,'OR':6,'AND':7,
        'MUL':0,'MULH':1,'MULHSU':2,'MULHU':3,'DIV':4,'DIVU':5,'REM':6,'REMU':7,
        'ADDI':0,'SLTI':2,'SLTIU':3,'XORI':4,'ORI':6,'ANDI':7,'SLLI':1,'SRLI':5,'SRAI':5,
        'LB':0,'LH':1,'LW':2,'LBU':4,'LHU':5,
        'SB':0,'SH':1,'SW':2,
        'BEQ':0,'BNE':1,'BLT':4,'BGE':5,'BLTU':6,'BGEU':7,
    }

    SYSCALL_NUM: Dict[str, int] = {
        'YIELD': 20, 'THREAD.CREATE': 21, 'THREAD.EXIT': 22,
        'THREAD.JOIN': 23, 'GET.TID': 24,
        'MUTEX.LOCK': 25, 'MUTEX.UNLOCK': 26,
    }

    def __init__(self, verbose: bool = False):
        self.labels:    Dict[str, int] = {}
        self.constants: Dict[str, int] = {}
        self.verbose = verbose

    #  Register / immediate parsing 

    def _reg(self, s: str) -> int:
        s = s.strip().lower().rstrip(',')
        if s in self.REG_MAP:
            return self.REG_MAP[s]
        if s.startswith('x') and s[1:].isdigit():
            n = int(s[1:])
            if 0 <= n <= 31:
                return n
        raise ValueError(f"Unknown register: {s!r}")

    def _imm(self, s: str, addr: int = 0) -> int:
        """
        Parse an immediate: integer literal, hex (0x…), named constant, or label.
        Labels resolve to their absolute address (not PC-relative — callers
        handle PC-relative arithmetic themselves).
        """
        s = s.strip().rstrip(',')
        if s in self.labels:
            return self.labels[s]
        if s in self.constants:
            return self.constants[s]
        if s.startswith('0x') or s.startswith('0X'):
            return int(s, 16)
        if s.startswith('-0x') or s.startswith('-0X'):
            return -int(s[1:], 16)
        try:
            return int(s)
        except ValueError:
            raise ValueError(
                f"Unknown symbol or invalid immediate: {s!r}\n"
                f"  (If this is a label, make sure it's defined before use or "
                f"check spelling)"
            ) from None

    def _parse_offset(self, s: str) -> Tuple[int, int]:
        """Parse  offset(reg)  or bare  reg  → (offset, reg_num)."""
        s = s.strip().rstrip(',')
        if '(' in s:
            off_str, rest = s.split('(', 1)
            reg = self._reg(rest.rstrip(')'))
            off = self._imm(off_str) if off_str.strip() else 0
            return off, reg
        return 0, self._reg(s)

    #  Instruction expansion 
    #
    # _expand(op, parts, addr) → List[Instr]
    #
    # This is THE central method. It is called identically in both passes.
    # First pass: uses dummy labels (address 0) to keep sizes stable.
    # Second pass: uses real labels.
    #
    # Returning a list means every pseudo-op has exactly one place that
    # determines its size. There is no separate _pseudo_size() function that
    # can get out of sync.

    def _expand(self, op: str, parts: List[str], addr: int) -> List[Instr]:
        """
        Expand one assembly statement (possibly a pseudo-op) into a list of
        machine instructions. Raises ValueError on bad syntax.
        """
        op = op.upper()

        def r(i): return self._reg(parts[i])
        def imm(i): return self._imm(parts[i], addr)

        #  Concurrency pseudo-ops 

        if op == 'YIELD':
            return [
                Instr('ADDI', rd=17, rs1=0, imm=20, funct3=0),  # li a7, 20
                Instr('ECALL'),
            ]

        if op == 'THREAD.EXIT':
            return [
                Instr('ADDI', rd=17, rs1=0, imm=22, funct3=0),  # li a7, 22
                Instr('ECALL'),
            ]

        if op == 'THREAD.CREATE':
            # li a7, 21; ecall; [mv rd, a0 if rd given and rd != a0]
            result = [
                Instr('ADDI', rd=17, rs1=0, imm=21, funct3=0),
                Instr('ECALL'),
            ]
            if len(parts) > 1:
                rd = self._reg(parts[1])
                result.append(Instr('ADDI', rd=rd, rs1=10, imm=0, funct3=0))  # mv rd, a0
            return result

        if op == 'THREAD.JOIN':
            # mv a0, rs; li a7, 23; ecall
            rs = self._reg(parts[1]) if len(parts) > 1 else 10
            return [
                Instr('ADDI', rd=10, rs1=rs, imm=0, funct3=0),  # mv a0, rs
                Instr('ADDI', rd=17, rs1=0, imm=23, funct3=0),  # li a7, 23
                Instr('ECALL'),
            ]

        if op == 'GET.TID':
            # li a7, 24; ecall; [mv rd, a0 if rd != a0]
            result = [
                Instr('ADDI', rd=17, rs1=0, imm=24, funct3=0),
                Instr('ECALL'),
            ]
            if len(parts) > 1:
                rd = self._reg(parts[1])
                result.append(Instr('ADDI', rd=rd, rs1=10, imm=0, funct3=0))
            return result

        if op == 'MUTEX.LOCK':
            rs = self._reg(parts[1]) if len(parts) > 1 else 10
            return [
                Instr('ADDI', rd=10, rs1=rs, imm=0, funct3=0),  # mv a0, rs
                Instr('ADDI', rd=17, rs1=0, imm=25, funct3=0),  # li a7, 25
                Instr('ECALL'),
            ]

        if op == 'MUTEX.UNLOCK':
            rs = self._reg(parts[1]) if len(parts) > 1 else 10
            return [
                Instr('ADDI', rd=10, rs1=rs, imm=0, funct3=0),
                Instr('ADDI', rd=17, rs1=0, imm=26, funct3=0),
                Instr('ECALL'),
            ]

        #  Stack helpers 

        if op == 'PUSH':
            rs = r(1)
            return [
                Instr('ADDI', rd=2, rs1=2, imm=-4, funct3=0),          # addi sp, sp, -4
                Instr('SW',   rs1=2, rs2=rs, imm=0, funct3=0b010),     # sw rs, 0(sp)
            ]

        if op == 'POP':
            rd = r(1)
            return [
                Instr('LW',   rd=rd, rs1=2, imm=0, funct3=0b010),      # lw rd, 0(sp)
                Instr('ADDI', rd=2, rs1=2, imm=4, funct3=0),           # addi sp, sp, 4
            ]

        #  Standard pseudo-ops 

        if op == 'NOP':
            return [Instr('ADDI', rd=0, rs1=0, imm=0, funct3=0)]

        if op == 'MV':
            return [Instr('ADDI', rd=r(1), rs1=r(2), imm=0, funct3=0)]

        if op == 'NOT':
            return [Instr('XORI', rd=r(1), rs1=r(2), imm=-1, funct3=self.F3['XORI'])]

        if op == 'NEG':
            return [Instr('SUB', rd=r(1), rs1=0, rs2=r(2),
                          funct3=self.F3['SUB'], funct7=0b0100000)]

        if op == 'SEQZ':
            return [Instr('SLTIU', rd=r(1), rs1=r(2), imm=1, funct3=self.F3['SLTIU'])]

        if op == 'SNEZ':
            return [Instr('SLTU', rd=r(1), rs1=0, rs2=r(2), funct3=self.F3['SLTU'])]

        if op == 'BEQZ':
            target = parts[2]
            off = (self.labels.get(target, 0) - addr) if target in self.labels else self._imm(target)
            return [Instr('BEQ', rs1=r(1), rs2=0, imm=off, funct3=self.F3['BEQ'])]

        if op == 'BNEZ':
            target = parts[2]
            off = (self.labels.get(target, 0) - addr) if target in self.labels else self._imm(target)
            return [Instr('BNE', rs1=r(1), rs2=0, imm=off, funct3=self.F3['BNE'])]

        if op == 'BLTZ':
            target = parts[2]
            off = (self.labels.get(target, 0) - addr) if target in self.labels else self._imm(target)
            return [Instr('BLT', rs1=r(1), rs2=0, imm=off, funct3=self.F3['BLT'])]

        if op == 'BGEZ':
            target = parts[2]
            off = (self.labels.get(target, 0) - addr) if target in self.labels else self._imm(target)
            return [Instr('BGE', rs1=r(1), rs2=0, imm=off, funct3=self.F3['BGE'])]

        if op == 'BLEZ':
            target = parts[2]
            off = (self.labels.get(target, 0) - addr) if target in self.labels else self._imm(target)
            return [Instr('BGE', rs1=0, rs2=r(1), imm=off, funct3=self.F3['BGE'])]

        if op == 'BGTZ':
            target = parts[2]
            off = (self.labels.get(target, 0) - addr) if target in self.labels else self._imm(target)
            return [Instr('BLT', rs1=0, rs2=r(1), imm=off, funct3=self.F3['BLT'])]

        if op == 'J':
            target = parts[1]
            off = (self.labels.get(target, 0) - addr) if target in self.labels else self._imm(target)
            return [Instr('JAL', rd=0, imm=off)]

        if op == 'JR':
            return [Instr('JALR', rd=0, rs1=r(1), imm=0, funct3=0)]

        if op == 'RET':
            return [Instr('JALR', rd=0, rs1=1, imm=0, funct3=0)]

        if op == 'CALL':
            target = parts[1]
            off = (self.labels.get(target, 0) - addr) if target in self.labels else self._imm(target)
            return [Instr('JAL', rd=1, imm=off)]

        if op == 'LI':
            rd  = r(1)
            val = self._imm(parts[2]) if parts[2] not in self.labels else self.labels[parts[2]]
            val32 = val & 0xFFFFFFFF
            if fits_signed(val, 12):
                # Small value — single ADDI
                return [Instr('ADDI', rd=rd, rs1=0, imm=val & 0xFFF, funct3=0)]
            else:
                # Large value — LUI + ADDI
                hi, lo = split_imm32(val32)
                result = [Instr('LUI', rd=rd, imm=hi)]
                if lo != 0:
                    result.append(Instr('ADDI', rd=rd, rs1=rd, imm=lo & 0xFFF, funct3=0))
                return result

        if op == 'LA':
            # Load address of label — use AUIPC + ADDI (PC-relative, position-independent)
            rd     = r(1)
            target = parts[2]
            t_addr = self.labels.get(target, 0)
            offset = t_addr - addr          # PC-relative offset
            hi, lo = split_imm32(offset & 0xFFFFFFFF)
            return [
                Instr('AUIPC', rd=rd, imm=hi),
                Instr('ADDI',  rd=rd, rs1=rd, imm=lo & 0xFFF, funct3=0),
            ]

        #  Fence

        if op == 'FENCE':
            return [Instr('FENCE')]

        #  Real instructions 

        R_OPS = {'ADD','SUB','AND','OR','XOR','SLL','SRL','SRA','SLT','SLTU',
                 'MUL','MULH','MULHSU','MULHU','DIV','DIVU','REM','REMU'}
        M_OPS = {'MUL','MULH','MULHSU','MULHU','DIV','DIVU','REM','REMU'}

        if op in R_OPS:
            funct7 = (0b0000001 if op in M_OPS else
                      0b0100000 if op in ('SUB','SRA') else 0)
            return [Instr(op, rd=r(1), rs1=r(2), rs2=r(3),
                          funct3=self.F3[op], funct7=funct7)]

        if op in ('ADDI','ANDI','ORI','XORI','SLTI','SLTIU'):
            val = imm(3)
            if not fits_signed(val, 12):
                raise ValueError(
                    f"{op} immediate {val} (0x{val&0xFFFFFFFF:x}) doesn't fit "
                    f"in 12 bits [-2048..2047]. Use 'li' for large values.")
            return [Instr(op, rd=r(1), rs1=r(2), imm=val & 0xFFF, funct3=self.F3[op])]

        if op in ('SLLI','SRLI','SRAI'):
            raw_shamt = imm(3)
            if not (0 <= raw_shamt <= 31):
                raise ValueError(f"{op} shamt must be 0–31, got {raw_shamt}")
            return [Instr(op, rd=r(1), rs1=r(2), imm=raw_shamt & 0x1F, funct3=self.F3[op])]

        if op in ('LB','LH','LW','LBU','LHU'):
            off, base = self._parse_offset(parts[2])
            off_s = sign_extend(off, 12) if off < 0x800 else off
            # Use the value as-is if it came in signed; normalize to signed 12-bit range
            off_s = sign_extend(off & 0xFFF, 12) if not fits_signed(off, 12) and fits_signed(sign_extend(off & 0xFFF, 12), 12) else off
            if not fits_signed(off, 12):
                raise ValueError(
                    f"{op} offset {off} doesn't fit in 12-bit signed [-2048..2047]")
            return [Instr(op, rd=r(1), rs1=base, imm=off & 0xFFF, funct3=self.F3[op])]

        if op in ('SB','SH','SW'):
            off, base = self._parse_offset(parts[2])
            if not fits_signed(off, 12):
                raise ValueError(
                    f"{op} offset {off} doesn't fit in 12-bit signed [-2048..2047]")
            return [Instr(op, rs1=base, rs2=r(1), imm=off & 0xFFF, funct3=self.F3[op])]

        if op in ('BEQ','BNE','BLT','BGE','BLTU','BGEU'):
            target = parts[3]
            off = ((self.labels[target] - addr)
                   if target in self.labels else self._imm(target))
            if not fits_signed(off, 13):
                raise ValueError(
                    f"{op} branch offset {off} doesn't fit in 13-bit signed [-4096..4094]")
            if off % 2 != 0:
                raise ValueError(f"{op} branch offset {off} must be a multiple of 2")
            return [Instr(op, rs1=r(1), rs2=r(2), imm=off, funct3=self.F3[op])]

        if op == 'JAL':
            if len(parts) > 2:
                rd_r   = r(1)
                target = parts[2]
            else:
                rd_r   = 1
                target = parts[1]
            off = ((self.labels[target] - addr)
                   if target in self.labels else self._imm(target))
            if not fits_signed(off, 21):
                raise ValueError(
                    f"JAL offset {off} doesn't fit in 21-bit signed [-1048576..1048574]")
            if off % 2 != 0:
                raise ValueError(f"JAL offset {off} must be a multiple of 2")
            return [Instr('JAL', rd=rd_r, imm=off)]

        if op == 'JALR':
            rd_r = r(1)
            if len(parts) > 2 and '(' in parts[2]:
                off, base = self._parse_offset(parts[2])
            elif len(parts) > 2:
                off = 0; base = r(2)
            else:
                off = 0; base = r(1)
            if not fits_signed(off, 12):
                raise ValueError(
                    f"JALR offset {off} doesn't fit in 12-bit signed [-2048..2047]")
            return [Instr('JALR', rd=rd_r, rs1=base,
                          imm=sign_extend(off, 12) & 0xFFF, funct3=0)]

        if op == 'LUI':
            val = imm(2)
            if not (0 <= val <= 0xFFFFF):
                raise ValueError(f"LUI immediate {val} (0x{val&0xFFFFFFFF:x}) must be 0..0xFFFFF (20 bits)")
            return [Instr('LUI', rd=r(1), imm=val & 0xFFFFF)]

        if op == 'AUIPC':
            val = imm(2)
            if not (0 <= val <= 0xFFFFF):
                raise ValueError(f"AUIPC immediate {val} (0x{val&0xFFFFFFFF:x}) must be 0..0xFFFFF (20 bits)")
            return [Instr('AUIPC', rd=r(1), imm=val & 0xFFFFF)]

        if op == 'ECALL':  return [Instr('ECALL')]
        if op == 'EBREAK': return [Instr('EBREAK')]

        raise ValueError(f"Unknown instruction or pseudo-op: {op!r}")

    #  Directive sizing 

    def _directive_size(self, line: str) -> int:
        """Return byte count for a directive line (first pass use)."""
        parts = line.split()
        d = parts[0]
        if d == '.word':
            return 4
        if d == '.byte':
            vals = ' '.join(parts[1:]).split(',')
            raw = len([v for v in vals if v.strip()])
            # pad to 4-byte alignment handled elsewhere; just count the bytes here
            return raw
        if d == '.space':
            return int(parts[1], 0) if len(parts) > 1 else 0
        if d == '.string':
            content = line.split('"', 1)[1].rsplit('"', 1)[0] if '"' in line else ''
            raw = len(content.encode('utf-8')) + 1   # +1 for null terminator
            # align to 4
            pad = (4 - raw % 4) % 4
            return raw + pad
        if d == '.align':
            # conservative: up to 2^n-1 padding; we don't know current addr here
            # The actual padding is computed during second pass
            return 0   # handled specially in both passes
        return 0

    #  First pass: collect labels 

    def _first_pass(self, lines: List[str]):
        addr = 0
        for raw in lines:
            line = raw.split('#')[0].strip()
            if not line:
                continue

            # Constants
            if line.startswith(('.set', '.equ')):
                toks = line.split(None, 2)
                if len(toks) >= 3:
                    name = toks[1].rstrip(',').strip()
                    try:
                        self.constants[name] = int(toks[2].strip(), 0)
                    except ValueError:
                        pass
                continue

            # Label — includes dot-labels like .loop (local, not exported to .sym)
            if ':' in line and not line.startswith('.set') and not line.startswith('.equ'):
                # Check: a label line looks like  "name:"  or  "name: instruction"
                # A directive starts with '.' but a LOCAL label also starts with '.'
                # We distinguish: if the part before ':' contains spaces it's not a label
                before_colon = line.split(':', 1)[0]
                if ' ' not in before_colon and '\t' not in before_colon:
                    self.labels[before_colon.strip()] = addr
                    line = line.split(':', 1)[1].strip()
                    if not line:
                        continue

            # Directive
            if line.startswith('.'):
                if line.split()[0] == '.align':
                    toks = line.split()
                    n = int(toks[1], 0) if len(toks) > 1 else 2
                    align = 1 << n
                    pad = (align - addr % align) % align
                    addr += pad
                else:
                    addr += self._directive_size(line)
                continue

            # Instruction — expand to get size (uses dummy label values = 0)
            toks = line.split()
            if not toks:
                continue
            op = toks[0].upper()
            try:
                instrs = self._expand(op, toks, addr)
                addr += len(instrs) * 4
            except Exception:
                # If expand fails during first pass, estimate 4 bytes
                # (will fail properly in second pass with a good error message)
                addr += 4

        if self.verbose:
            print(f"Labels:    {self.labels}")
            print(f"Constants: {self.constants}")

    #  Second pass: emit code

    def assemble(self, source: str) -> bytes:
        lines = source.split('\n')
        self._first_pass(lines)

        if self.verbose:
            print("\n=== Second Pass ===")

        chunks: List[bytes] = []
        addr = 0

        def emit_word(w: int):
            nonlocal addr
            chunks.append(struct.pack('<I', w & 0xFFFFFFFF))
            addr += 4

        for line_num, raw in enumerate(lines, 1):
            line = raw.split('#')[0].strip()
            if not line:
                continue

            # Constants — skip
            if line.startswith(('.set', '.equ')):
                continue

            # Label — strip (handles both normal and dot-labels like .loop)
            if ':' in line and not line.startswith('.set') and not line.startswith('.equ'):
                before_colon = line.split(':', 1)[0]
                if ' ' not in before_colon and '\t' not in before_colon:
                    line = line.split(':', 1)[1].strip()
                    if not line:
                        continue

            # Directive
            if line.startswith('.'):
                toks = line.split()
                d = toks[0]

                if d == '.align':
                    n     = int(toks[1], 0) if len(toks) > 1 else 2
                    align = 1 << n
                    pad   = (align - addr % align) % align
                    chunks.append(b'\x00' * pad)
                    addr += pad

                elif d == '.word':
                    val_str = ' '.join(toks[1:]).strip().rstrip(',')
                    val = self._imm(val_str) if val_str else 0
                    emit_word(val)

                elif d == '.byte':
                    raw_vals = ' '.join(toks[1:]).split(',')
                    byte_data = bytes(self._imm(v.strip()) & 0xFF
                                      for v in raw_vals if v.strip())
                    chunks.append(byte_data)
                    addr += len(byte_data)

                elif d == '.space':
                    n = int(toks[1], 0) if len(toks) > 1 else 0
                    chunks.append(b'\x00' * n)
                    addr += n

                elif d == '.string':
                    content = line.split('"', 1)[1].rsplit('"', 1)[0] if '"' in line else ''
                    encoded = content.encode('utf-8') + b'\x00'
                    chunks.append(encoded)
                    addr += len(encoded)
                    pad = (4 - addr % 4) % 4
                    chunks.append(b'\x00' * pad)
                    addr += pad

                continue

            # Instruction
            toks = line.split()
            if not toks:
                continue
            op = toks[0]

            try:
                instrs = self._expand(op, toks, addr)
            except ValueError as e:
                raise ValueError(f"Line {line_num}: {raw.strip()!r}\n  → {e}") from None

            for instr in instrs:
                word = instr.encode()
                if self.verbose:
                    print(f"  0x{addr:04x}: {word:08x}  {instr.op}")
                emit_word(word)

        return b''.join(chunks)




def main():
    parser = argparse.ArgumentParser(
        prog='asm_concurrent.py',
        description='RISC-V RV32IM Assembler (Concurrent Edition)',
        epilog=(
            'USAGE EXAMPLE:\n'
            '  python3 asm_concurrent.py  my_program.asm  my_program.bin\n'
            '  python3 vm_concurrent.py   my_program.bin  --mode green --trace\n\n'
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument('input',           help='Input assembly file (.asm)')
    parser.add_argument('output',          help='Output binary file (.bin)')
    parser.add_argument('-v','--verbose',  action='store_true', help='Verbose output')
    parser.add_argument('-d','--dump',     action='store_true', help='Hex + disassembly dump')
    args = parser.parse_args()

    # Detect accidental "python3 foo.asm args" invocation
    if args.input.endswith('.bin') or args.output.endswith('.asm'):
        print("ERROR: Arguments look reversed. Usage:")
        print("  python3 asm_concurrent.py  INPUT.asm  OUTPUT.bin")
        sys.exit(1)

    with open(args.input) as f:
        source = f.read()

    asm = Assembler(verbose=args.verbose)
    try:
        binary = asm.assemble(source)
    except ValueError as e:
        print(f"\nAssembly error:\n  {e}")
        sys.exit(1)

    with open(args.output, 'wb') as f:
        f.write(binary)

    # Write .sym file so vm_concurrent.py can find entry points by label name
    sym_path = os.path.splitext(args.output)[0] + '.sym'
    with open(sym_path, 'w') as f:
        for label, laddr in sorted(asm.labels.items(), key=lambda x: x[1]):
            if not label.startswith('.'):   # skip local/dot labels
                f.write(f"{label} {laddr:x}\n")

    n_instrs = sum(1 for chunk in [binary[i:i+4] for i in range(0, len(binary), 4)]
                   if len(chunk) == 4)
    print(f"✓ Assembled {len(binary)} bytes ({n_instrs} words) → {args.output}")
    print(f"✓ Symbols → {sym_path}")
    if args.verbose:
        print(f"\nLabel table:")
        for label, laddr in sorted(asm.labels.items(), key=lambda x: x[1]):
            print(f"  {laddr:6x}  {label}")

    if args.dump:
        print("\n=== Hex Dump ===")
        for i in range(0, len(binary), 16):
            row  = binary[i:i+16]
            hex_ = ' '.join(f'{b:02x}' for b in row)
            asc  = ''.join(chr(b) if 32 <= b < 127 else '.' for b in row)
            print(f"  0x{i:04x}:  {hex_:47s}  {asc}")


if __name__ == '__main__':
    main()
