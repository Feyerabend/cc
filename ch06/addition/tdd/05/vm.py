"""
Virtual Machine Implementation
A register-based VM with comprehensive TDD coverage

- 10 general-purpose registers (R0-R9)
- Stack for temporary storage
- Call stack for function calls
- Status flags for comparisons
- Debug logging
- Comprehensive error handling
"""

from typing import List, Tuple, Any, Optional, Dict
import logging


class VMError(Exception):
    """Base exception for VM errors"""
    pass


class StackUnderflowError(VMError):
    """Raised when popping from empty stack"""
    pass


class InvalidRegisterError(VMError):
    """Raised when accessing invalid register"""
    pass


class DivisionByZeroError(VMError):
    """Raised on division by zero"""
    pass


class InvalidJumpError(VMError):
    """Raised when jumping to invalid address"""
    pass


class ReturnWithoutCallError(VMError):
    """Raised when RET without matching CALL"""
    pass


class VirtualMachine:
    """
    Register-based virtual machine with stack support.
    
    Instruction Set:
    
    Data Movement:
        MOV dest, src       - Move value to register
        PUSH src            - Push value onto stack
        POP dest            - Pop value from stack to register
    
    Arithmetic:
        ADD dest, src       - Add: dest += src
        SUB dest, src       - Subtract: dest -= src
        MUL dest, src       - Multiply: dest *= src
        DIV dest, src       - Divide: dest //= src (integer division)
        MOD dest, src       - Modulo: dest %= src
    
    Bitwise Logic:
        AND dest, src       - Bitwise AND: dest &= src
        OR dest, src        - Bitwise OR: dest |= src
        XOR dest, src       - Bitwise XOR: dest ^= src
        NOT dest            - Bitwise NOT: dest = ~dest
    
    Comparison:
        CMP op1, op2        - Compare values, set flag (LESS/GREATER/ZERO)
    
    Control Flow:
        JMP addr            - Unconditional jump
        JMP_IF flag, addr   - Conditional jump if flag matches
        CALL addr           - Call function (saves return address)
        RET                 - Return from function
    
    I/O:
        PRINT src           - Print value
        READ dest           - Read value from input (interactive mode)
    
    System:
        HALT                - Stop execution
        NOP                 - No operation
    
    Examples:
    ====
    # Simple addition
    [
        ("MOV", "R0", 10),
        ("ADD", "R0", 5),
        ("PRINT", "R0"),    # Outputs: 15
    ]
    
    # Loop (count from 5 to 0)
    [
        ("MOV", "R0", 5),
        ("CMP", "R0", 0),
        ("JMP_IF", "ZERO", 5),
        ("SUB", "R0", 1),
        ("JMP", 1),
        ("HALT",)
    ]
    
    # Function call
    [
        ("CALL", 2),
        ("HALT",),
        ("MOV", "R0", 42),  # Function body
        ("RET",)
    ]
    """
    
    def __init__(self, debug: bool = False):
        """
        Init virtual machine.
        
        Args:
            debug: If True, enable detailed execution logging
        """
        # Core state
        self.registers: Dict[str, int] = {f"R{i}": 0 for i in range(10)}
        self.stack: List[int] = []
        self.call_stack: List[int] = []
        self.status_flag: Optional[str] = None
        
        # Execution state
        self.halted: bool = False
        self.instruction_count: int = 0
        
        # Debug and logging
        self.debug: bool = debug
        self.execution_log: List[Dict[str, Any]] = []
        
        # Setup logging
        if debug:
            logging.basicConfig(
                level=logging.DEBUG,
                format='[%(levelname)s] %(message)s'
            )
        self.logger = logging.getLogger(__name__)
    
    def resolve_operand(self, operand: Any) -> int:
        """
        Resolve an operand to its actual value.
        
        If operand is a register name (e.g., "R0"), returns the register's value.
        Otherwise, returns the operand as-is (literal value).
        
        Args:
            operand: Register name or literal value
        
        Returns:
            The resolved integer value
        
        Raises:
            InvalidRegisterError: If register name is invalid
        """
        if isinstance(operand, str) and operand.startswith("R"):
            if operand not in self.registers:
                raise InvalidRegisterError(f"Invalid register: {operand}")
            return self.registers[operand]
        return int(operand)
    
    def _log_execution(self, ip: int, instruction: Tuple, message: str = ""):
        """
        Log execution step if debug mode is enabled.
        
        Args:
            ip: Current instruction pointer
            instruction: Current instruction tuple
            message: Additional message to log
        """
        if not self.debug:
            return
        
        log_entry = {
            "ip": ip,
            "instruction": instruction,
            "message": message,
            "registers": self.registers.copy(),
            "stack": self.stack.copy(),
            "call_stack": self.call_stack.copy(),
            "flag": self.status_flag,
            "instruction_count": self.instruction_count
        }
        
        self.execution_log.append(log_entry)
        
        # Format and print debug output
        instr_str = " ".join(str(x) for x in instruction)
        self.logger.debug(f"IP={ip:3d} | {instr_str:30s} | {message}")
    
    def _validate_jump_target(self, target: int, program_length: int):
        """
        Validate that jump target is within program bounds.
        
        Args:
            target: Jump target address
            program_length: Length of the program
        
        Raises:
            InvalidJumpError: If target is out of bounds
        """
        if target < 0 or target >= program_length:
            raise InvalidJumpError(
                f"Jump target {target} out of bounds [0, {program_length})"
            )
    
    def execute(self, instructions: List[Tuple]) -> None:
        """
        Execute a program.
        
        Args:
            instructions: List of instruction tuples
        
        Raises:
            VMError: On various execution errors
        """
        ip = 0  # Instruction pointer
        self.halted = False
        self.instruction_count = 0
        program_length = len(instructions)
        
        while ip < program_length and not self.halted:
            instruction = instructions[ip]
            opcode = instruction[0]
            self.instruction_count += 1
            
            try:
                #  DATA MOVEMENT 
                
                if opcode == "MOV":
                    _, dest, src = instruction
                    if dest not in self.registers:
                        raise InvalidRegisterError(f"Invalid register: {dest}")
                    value = self.resolve_operand(src)
                    self.registers[dest] = value
                    self._log_execution(ip, instruction, f"{dest} ← {value}")
                
                elif opcode == "PUSH":
                    _, src = instruction
                    value = self.resolve_operand(src)
                    self.stack.append(value)
                    self._log_execution(
                        ip, instruction, 
                        f"Push {value} (stack: {len(self.stack)})"
                    )
                
                elif opcode == "POP":
                    _, dest = instruction
                    if dest not in self.registers:
                        raise InvalidRegisterError(f"Invalid register: {dest}")
                    if not self.stack:
                        raise StackUnderflowError("Cannot POP from empty stack")
                    value = self.stack.pop()
                    self.registers[dest] = value
                    self._log_execution(
                        ip, instruction,
                        f"Pop {value} → {dest} (stack: {len(self.stack)})"
                    )
                
                #  ARITHMETIC 
                
                elif opcode == "ADD":
                    _, dest, src = instruction
                    if dest not in self.registers:
                        raise InvalidRegisterError(f"Invalid register: {dest}")
                    value = self.resolve_operand(src)
                    old_val = self.registers[dest]
                    self.registers[dest] += value
                    self._log_execution(
                        ip, instruction,
                        f"{dest}: {old_val} + {value} = {self.registers[dest]}"
                    )
                
                elif opcode == "SUB":
                    _, dest, src = instruction
                    if dest not in self.registers:
                        raise InvalidRegisterError(f"Invalid register: {dest}")
                    value = self.resolve_operand(src)
                    old_val = self.registers[dest]
                    self.registers[dest] -= value
                    self._log_execution(
                        ip, instruction,
                        f"{dest}: {old_val} - {value} = {self.registers[dest]}"
                    )
                
                elif opcode == "MUL":
                    _, dest, src = instruction
                    if dest not in self.registers:
                        raise InvalidRegisterError(f"Invalid register: {dest}")
                    value = self.resolve_operand(src)
                    old_val = self.registers[dest]
                    self.registers[dest] *= value
                    self._log_execution(
                        ip, instruction,
                        f"{dest}: {old_val} × {value} = {self.registers[dest]}"
                    )
                
                elif opcode == "DIV":
                    _, dest, src = instruction
                    if dest not in self.registers:
                        raise InvalidRegisterError(f"Invalid register: {dest}")
                    divisor = self.resolve_operand(src)
                    if divisor == 0:
                        raise DivisionByZeroError("Division by zero")
                    old_val = self.registers[dest]
                    self.registers[dest] //= divisor
                    self._log_execution(
                        ip, instruction,
                        f"{dest}: {old_val} ÷ {divisor} = {self.registers[dest]}"
                    )
                
                elif opcode == "MOD":
                    _, dest, src = instruction
                    if dest not in self.registers:
                        raise InvalidRegisterError(f"Invalid register: {dest}")
                    modulus = self.resolve_operand(src)
                    if modulus == 0:
                        raise DivisionByZeroError("Modulo by zero")
                    old_val = self.registers[dest]
                    self.registers[dest] %= modulus
                    self._log_execution(
                        ip, instruction,
                        f"{dest}: {old_val} % {modulus} = {self.registers[dest]}"
                    )
                
                #  BITWISE LOGIC 
                
                elif opcode == "AND":
                    _, dest, src = instruction
                    if dest not in self.registers:
                        raise InvalidRegisterError(f"Invalid register: {dest}")
                    value = self.resolve_operand(src)
                    old_val = self.registers[dest]
                    self.registers[dest] &= value
                    self._log_execution(
                        ip, instruction,
                        f"{dest}: {old_val} & {value} = {self.registers[dest]}"
                    )
                
                elif opcode == "OR":
                    _, dest, src = instruction
                    if dest not in self.registers:
                        raise InvalidRegisterError(f"Invalid register: {dest}")
                    value = self.resolve_operand(src)
                    old_val = self.registers[dest]
                    self.registers[dest] |= value
                    self._log_execution(
                        ip, instruction,
                        f"{dest}: {old_val} | {value} = {self.registers[dest]}"
                    )
                
                elif opcode == "XOR":
                    _, dest, src = instruction
                    if dest not in self.registers:
                        raise InvalidRegisterError(f"Invalid register: {dest}")
                    value = self.resolve_operand(src)
                    old_val = self.registers[dest]
                    self.registers[dest] ^= value
                    self._log_execution(
                        ip, instruction,
                        f"{dest}: {old_val} ^ {value} = {self.registers[dest]}"
                    )
                
                elif opcode == "NOT":
                    _, dest = instruction
                    if dest not in self.registers:
                        raise InvalidRegisterError(f"Invalid register: {dest}")
                    old_val = self.registers[dest]
                    self.registers[dest] = ~old_val
                    self._log_execution(
                        ip, instruction,
                        f"{dest}: ~{old_val} = {self.registers[dest]}"
                    )
                
                #  COMPARISON 
                
                elif opcode == "CMP":
                    _, op1, op2 = instruction
                    val1 = self.resolve_operand(op1)
                    val2 = self.resolve_operand(op2)
                    
                    if val1 < val2:
                        self.status_flag = "LESS"
                    elif val1 > val2:
                        self.status_flag = "GREATER"
                    else:
                        self.status_flag = "ZERO"
                    
                    self._log_execution(
                        ip, instruction,
                        f"Compare {val1} vs {val2} → {self.status_flag}"
                    )
                
                #  CONTROL FLOW 
                
                elif opcode == "JMP":
                    _, target = instruction
                    self._validate_jump_target(target, program_length)
                    self._log_execution(ip, instruction, f"Jump to {target}")
                    ip = target
                    continue  # Don't increment IP
                
                elif opcode == "JMP_IF":
                    _, condition, target = instruction
                    if self.status_flag == condition:
                        self._validate_jump_target(target, program_length)
                        self._log_execution(
                            ip, instruction,
                            f"Condition {condition} met, jump to {target}"
                        )
                        ip = target
                        continue
                    else:
                        self._log_execution(
                            ip, instruction,
                            f"Condition {condition} not met, continue"
                        )
                
                elif opcode == "CALL":
                    _, target = instruction
                    self._validate_jump_target(target, program_length)
                    return_addr = ip + 1
                    self.call_stack.append(return_addr)
                    self._log_execution(
                        ip, instruction,
                        f"Call {target}, return to {return_addr}"
                    )
                    ip = target
                    continue
                
                elif opcode == "RET":
                    if not self.call_stack:
                        raise ReturnWithoutCallError("RET without matching CALL")
                    return_addr = self.call_stack.pop()
                    self._log_execution(ip, instruction, f"Return to {return_addr}")
                    ip = return_addr
                    continue
                
                #  I/O 
                
                elif opcode == "PRINT":
                    _, src = instruction
                    value = self.resolve_operand(src)
                    print(value)
                    self._log_execution(ip, instruction, f"Print: {value}")
                
                elif opcode == "READ":
                    _, dest = instruction
                    if dest not in self.registers:
                        raise InvalidRegisterError(f"Invalid register: {dest}")
                    value = int(input("Enter value: "))
                    self.registers[dest] = value
                    self._log_execution(ip, instruction, f"Read {value} → {dest}")
                
                #  SYSTEM 
                
                elif opcode == "HALT":
                    self.halted = True
                    self._log_execution(ip, instruction, "HALT - Program terminated")
                    return
                
                elif opcode == "NOP":
                    self._log_execution(ip, instruction, "No operation")
                    pass  # No operation
                
                else:
                    raise VMError(f"Unknown opcode: {opcode}")
                
                ip += 1
                
            except VMError:
                # Re-raise VM-specific errors
                raise
            except Exception as e:
                # Wrap other exceptions
                raise VMError(f"Error at IP={ip}, instruction {instruction}: {e}")
    
    def get_register(self, reg: str) -> int:
        """
        Get the value of a register.
        
        Args:
            reg: Register name (e.g., "R0")
        
        Returns:
            Register value
        
        Raises:
            InvalidRegisterError: If register doesn't exist
        """
        if reg not in self.registers:
            raise InvalidRegisterError(f"Invalid register: {reg}")
        return self.registers[reg]
    
    def set_register(self, reg: str, value: int) -> None:
        """
        Set the value of a register.
        
        Args:
            reg: Register name
            value: Value to set
        
        Raises:
            InvalidRegisterError: If register doesn't exist
        """
        if reg not in self.registers:
            raise InvalidRegisterError(f"Invalid register: {reg}")
        self.registers[reg] = value
    
    def get_status_flag(self) -> Optional[str]:
        """Get the current status flag."""
        return self.status_flag
    
    def get_stack(self) -> List[int]:
        """Get a copy of the stack."""
        return self.stack.copy()
    
    def get_execution_log(self) -> List[Dict[str, Any]]:
        """Get the complete execution log."""
        return self.execution_log.copy()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get execution statistics.
        
        Returns:
            Dictionary with execution stats
        """
        return {
            "instruction_count": self.instruction_count,
            "stack_size": len(self.stack),
            "call_stack_depth": len(self.call_stack),
            "halted": self.halted,
            "status_flag": self.status_flag
        }
    
    def reset(self) -> None:
        """Reset the VM to initial state."""
        self.__init__(debug=self.debug)
    
    def __repr__(self) -> str:
        """String representation of VM state."""
        reg_str = ", ".join(f"{k}={v}" for k, v in self.registers.items() if v != 0)
        return (
            f"VM(registers=[{reg_str}], "
            f"stack={self.stack}, "
            f"flag={self.status_flag}, "
            f"instructions={self.instruction_count})"
        )


# Convenience function for quick testing
def run_program(program: List[Tuple], debug: bool = False) -> VirtualMachine:
    """
    Quick helper to run a program and return the VM.
    
    Args:
        program: List of instruction tuples
        debug: Enable debug logging
    
    Returns:
        The VM after execution
    
    Example:
        >>> vm = run_program([
        ...     ("MOV", "R0", 10),
        ...     ("ADD", "R0", 5),
        ...     ("PRINT", "R0")
        ... ])
        15
        >>> vm.get_register("R0")
        15
    """
    vm = VirtualMachine(debug=debug)
    vm.execute(program)
    return vm


if __name__ == "__main__":
    # Example usage
    print("- Example 1: Simple Arithmetic")
    vm1 = run_program([
        ("MOV", "R0", 10),
        ("ADD", "R0", 5),
        ("MUL", "R0", 2),
        ("PRINT", "R0"),
        ("HALT",)
    ])
    
    print("\n- Example 2: Loop (Countdown)")
    vm2 = run_program([
        ("MOV", "R0", 5),           # Counter
        ("MOV", "R1", 0),           # Sum
        ("CMP", "R0", 0),           # Loop condition
        ("JMP_IF", "ZERO", 8),      # Exit when zero
        ("ADD", "R1", "R0"),        # Sum += counter
        ("SUB", "R0", 1),           # Decrement
        ("JMP", 2),                 # Loop back
        ("PRINT", "R1"),            # Print result
        ("HALT",)
    ], debug=True)
    
    print("\n- Example 3: Factorial Function")
    vm3 = run_program([
        ("MOV", "R0", 1),           # Result = 1
        ("MOV", "R1", 5),           # N = 5
        ("CMP", "R1", 0),           # Check if N > 0
        ("JMP_IF", "ZERO", 7),      # Done
        ("MUL", "R0", "R1"),        # Result *= N
        ("SUB", "R1", 1),           # N--
        ("JMP", 2),                 # Loop
        ("PRINT", "R0"),            # Print result (120)
        ("HALT",)
    ])
