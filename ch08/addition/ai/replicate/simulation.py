import copy
from typing import List, Tuple #Dict, Tuple, Optional
from enum import Enum

class ComponentType(Enum):
    EMPTY = 0
    CONSTRUCTOR = 1
    MEMORY = 2
    COPIER = 3
    CONTROLLER = 4
    RAW_MATERIAL = 5

class Instruction:
    def __init__(self, opcode: str, args: List[int]):
        self.opcode = opcode
        self.args = args
    
    def __repr__(self):
        return f"{self.opcode}({','.join(map(str, self.args))})"

class UniversalConstructor:
    def __init__(self, world_size: int = 50):
        self.world_size = world_size
        self.world = [[ComponentType.EMPTY for _ in range(world_size)] 
                      for _ in range(world_size)]
        self.machines = {}  # machine_id -> Machine instance
        self.next_machine_id = 1
        self.raw_materials = 1000  # Global resource pool
        
    def add_raw_materials(self, amount: int):
        self.raw_materials += amount
        
    def place_component(self, x: int, y: int, component_type: ComponentType) -> bool:
        if (0 <= x < self.world_size and 0 <= y < self.world_size and 
            self.world[y][x] == ComponentType.EMPTY and self.raw_materials > 0):
            self.world[y][x] = component_type
            self.raw_materials -= 1
            return True
        return False
    
    def get_component(self, x: int, y: int) -> ComponentType:
        if 0 <= x < self.world_size and 0 <= y < self.world_size:
            return self.world[y][x]
        return ComponentType.EMPTY
    
    def create_machine(self, x: int, y: int, program: List[Instruction]) -> int:
        machine_id = self.next_machine_id
        self.next_machine_id += 1
        
        machine = Machine(machine_id, x, y, program, self)
        self.machines[machine_id] = machine
        
        # Place the constructor component
        self.place_component(x, y, ComponentType.CONSTRUCTOR)
        
        return machine_id
    
    def step(self):
        """Execute one step for all machines"""
        for machine in list(self.machines.values()):
            if machine.active:
                machine.execute_step()
    
    def print_world(self, show_area: Tuple[int, int, int, int] = None):
        if show_area is None:
            start_x, start_y, end_x, end_y = 0, 0, self.world_size, self.world_size
        else:
            start_x, start_y, end_x, end_y = show_area
            
        symbol_map = {
            ComponentType.EMPTY: '.',
            ComponentType.CONSTRUCTOR: 'C',
            ComponentType.MEMORY: 'M',
            ComponentType.COPIER: 'P',
            ComponentType.CONTROLLER: 'T',
            ComponentType.RAW_MATERIAL: 'R'
        }
        
        print(f"Raw materials: {self.raw_materials}")
        print(f"Active machines: {len([m for m in self.machines.values() if m.active])}")
        print()
        
        for y in range(start_y, min(end_y, self.world_size)):
            row = ""
            for x in range(start_x, min(end_x, self.world_size)):
                row += symbol_map[self.world[y][x]]
            print(row)
        print()

class Machine:
    def __init__(self, machine_id: int, x: int, y: int, program: List[Instruction], world: UniversalConstructor):
        self.id = machine_id
        self.x = x
        self.y = y
        self.program = program
        self.world = world
        self.pc = 0  # Program counter
        self.active = True
        self.construction_head_x = x
        self.construction_head_y = y
        self.memory = {}  # Local memory storage
        
    def execute_step(self):
        if self.pc >= len(self.program):
            return
            
        instruction = self.program[self.pc]
        
        try:
            if instruction.opcode == "MOVE":
                # Move construction head
                dx, dy = instruction.args
                self.construction_head_x += dx
                self.construction_head_y += dy
                
            elif instruction.opcode == "BUILD":
                # Build component at construction head
                component_type = ComponentType(instruction.args[0])
                success = self.world.place_component(
                    self.construction_head_x, 
                    self.construction_head_y, 
                    component_type
                )
                if not success:
                    print(f"Machine {self.id}: Failed to build at ({self.construction_head_x}, {self.construction_head_y})")
                    
            elif instruction.opcode == "COPY_PROGRAM":
                # Copy program to memory components in local area
                start_x, start_y, size = instruction.args
                program_copy = copy.deepcopy(self.program)
                
                # Store program in memory (simplified - in reality this would be
                # stored in physical memory components)
                memory_key = f"program_{start_x}_{start_y}"
                self.memory[memory_key] = program_copy
                
            elif instruction.opcode == "SPAWN":
                # Create new machine with copied program
                new_x, new_y = instruction.args
                if f"program_{new_x}_{new_y}" in self.memory:
                    program_copy = self.memory[f"program_{new_x}_{new_y}"]
                    new_machine_id = self.world.create_machine(new_x, new_y, program_copy)
                    print(f"Machine {self.id}: Spawned new machine {new_machine_id} at ({new_x}, {new_y})")
                    
            elif instruction.opcode == "SENSE":
                # Sense environment
                sense_x, sense_y = instruction.args
                component = self.world.get_component(sense_x, sense_y)
                self.memory[f"sense_{sense_x}_{sense_y}"] = component
                
            elif instruction.opcode == "JUMP_IF":
                # Conditional jump
                condition, target_pc = instruction.args
                if self.evaluate_condition(condition):
                    self.pc = target_pc - 1  # -1 because pc will be incremented
                    
            elif instruction.opcode == "HALT":
                # Stop execution
                self.active = False
                print(f"Machine {self.id}: Halted")
                
            else:
                print(f"Machine {self.id}: Unknown instruction {instruction.opcode}")
                
        except Exception as e:
            print(f"Machine {self.id}: Error executing {instruction}: {e}")
            
        self.pc += 1
    
    def evaluate_condition(self, condition: int) -> bool:
        # In a real implementation, this would check various conditions
        # For now, just return True for condition 1, False for others
        return condition == 1

def create_self_replicating_program() -> List[Instruction]:
    return [
        # Move construction head to build area
        Instruction("MOVE", [1, 0]),
        
        # Build basic structure for offspring
        Instruction("BUILD", [ComponentType.CONSTRUCTOR.value]),
        Instruction("MOVE", [1, 0]),
        Instruction("BUILD", [ComponentType.MEMORY.value]),
        Instruction("MOVE", [1, 0]),
        Instruction("BUILD", [ComponentType.COPIER.value]),
        
        # Copy program to memory
        Instruction("COPY_PROGRAM", [1, 0, 3]),
        
        # Spawn new machine
        Instruction("SPAWN", [1, 0]),
        
        # Move to new location for next replication
        Instruction("MOVE", [0, 2]),
        
        # Jump back to start for continuous replication
        Instruction("JUMP_IF", [1, 0]),
        
        # Halt (shouldn't reach here due to jump)
        Instruction("HALT", [])
    ]

def create_structure_builder_program() -> List[Instruction]:
    return [
        # Build a 3x3 square
        Instruction("BUILD", [ComponentType.CONTROLLER.value]),
        Instruction("MOVE", [1, 0]),
        Instruction("BUILD", [ComponentType.CONTROLLER.value]),
        Instruction("MOVE", [1, 0]),
        Instruction("BUILD", [ComponentType.CONTROLLER.value]),
        Instruction("MOVE", [-2, 1]),
        Instruction("BUILD", [ComponentType.CONTROLLER.value]),
        Instruction("MOVE", [1, 0]),
        Instruction("BUILD", [ComponentType.CONTROLLER.value]),
        Instruction("MOVE", [1, 0]),
        Instruction("BUILD", [ComponentType.CONTROLLER.value]),
        Instruction("MOVE", [-2, 1]),
        Instruction("BUILD", [ComponentType.CONTROLLER.value]),
        Instruction("MOVE", [1, 0]),
        Instruction("BUILD", [ComponentType.CONTROLLER.value]),
        Instruction("MOVE", [1, 0]),
        Instruction("BUILD", [ComponentType.CONTROLLER.value]),
        Instruction("HALT", [])
    ]


# Example
if __name__ == "__main__":
    world = UniversalConstructor(20)
    
    print("--- von Neumann Universal Constructor Demo ---\n")
    
    # Create a self-replicating machine
    replicator_program = create_self_replicating_program()
    machine1_id = world.create_machine(5, 5, replicator_program)
    
    print("Initial state:")
    world.print_world((0, 0, 15, 15))
    
    print("Running self-replicating machine ..")
    for step in range(20):
        world.step()
        if step % 5 == 4:  # print every 5 steps
            print(f"After step {step + 1}:")
            world.print_world((0, 0, 15, 15))
    
    print("\n" + "="*50 + "\n")
    
    # Create a fresh world for structure building demo
    world2 = UniversalConstructor(15)
    
    # Create a structure-building machine
    builder_program = create_structure_builder_program()
    machine2_id = world2.create_machine(3, 3, builder_program)
    
    print("Structure building demonstration:")
    print("Initial state:")
    world2.print_world((0, 0, 12, 12))
    
    print("Building structure ..")
    for step in range(len(builder_program)):
        world2.step()
        if step % 3 == 2:  # print every 3 steps
            print(f"After step {step + 1}:")
            world2.print_world((0, 0, 12, 12))
    
    print("\n-- Demo ---")
    print("1. Universal Construction: Machines read instructions and build accordingly")
    print("2. Self-Replication: Programs can copy themselves and spawn new machines")
    print("3. Instruction Processing: Step-by-step execution of construction commands")
    print("4. Resource Management: Construction requires raw materials")
    print("5. Programmability: Different programs create different behaviors")
    print("\nLegend: C=Constructor, M=Memory, P=Copier, T=Controller, R=Raw Material, .=Empty")

