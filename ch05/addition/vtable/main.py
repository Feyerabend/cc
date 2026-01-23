from lexer import lex
from parser import *
from typing import Tuple, List
from vtable_builder import VTableBuilder
from visualizer import visualize_vtable, visualize_hierarchy
from codegen import generate_c_code


def main():
    print("\nVTABLE COMPILER")
    print("-"*50)
    
    # Source code
    source = """
class Dog inherits Object {
    def bark() {
        print("Woof!");
    }
}
"""
    
    print("\n[INPUT] Source Code:")
    print(source)
    
    # Phase 1: Lexing
    print("\n" + "-"*50)
    print("[PHASE 1] LEXICAL ANALYSIS")
    print("-"*50)
    tokens = lex(source)
    print(f"Tokens generated: {len(tokens)}")
    for tok in tokens[:5]:
        print(f"  {tok}")
    if len(tokens) > 5:
        print("  ...")
    
    # Phase 2: Parsing
    print("\n" + "-"*50)
    print("[PHASE 2] SYNTAX ANALYSIS")
    print("-"*50)
    parser = Parser(tokens)
    ast = parser.parse_class()
    print("AST Structure:")
    print(f"  Class: {ast['name']}")
    print(f"  Parent: {ast['parent']}")
    print(f"  Methods: {[m['name'] for m in ast['methods']]}")
    
    # Phase 3: VTable Construction
    print("\n" + "-"*50)
    print("[PHASE 3] VTABLE CONSTRUCTION")
    print("-"*50)
    builder = VTableBuilder()
    builder.add_class(ast)
    builder.build()
    
    vtables_data = builder.export()
    print("VTables built for classes:", list(vtables_data.keys()))
    
    # Phase 4: Code Generation
    print("\n" + "-"*50)
    print("[PHASE 4] C CODE GENERATION")
    print("-"*50)
    c_code = generate_c_code(ast)
    print(c_code)
    with open('output.c', 'w') as f:
        f.write(c_code)

if __name__ == "__main__":
    main()
