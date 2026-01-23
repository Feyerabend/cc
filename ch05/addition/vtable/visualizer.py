from typing import Dict

def visualize_vtable(vtable_data: Dict) -> str:
    """Create ASCII visualization of a VTable."""
    lines = []
    class_name = vtable_data['class_name']
    parent = vtable_data['parent']
    methods = vtable_data['methods']
    
    # Header
    lines.append(f"┌─ {class_name}VTable ──────────────────┐")
    
    # Parent pointer
    if parent:
        lines.append(f"│ parent: {parent}VTable*           │")
        lines.append("├───────────────────────────────┤")
    
    # Methods
    for method in methods:
        name = method['name']
        impl = method['implementation']
        override = " ⚡" if method['overridden'] else ""
        
        lines.append(f"│ {name:12} → {impl}_{name}{override}")
    
    lines.append("└───────────────────────────────┘")
    
    return '\n'.join(lines)


def visualize_hierarchy(vtables_data: Dict) -> str:
    """Visualize entire class hierarchy."""
    lines = []
    
    def show_class(class_name: str, indent: int = 0):
        if class_name not in vtables_data:
            return
        
        vtable = vtables_data[class_name]
        prefix = "  " * indent
        
        # Show VTable
        vtable_viz = visualize_vtable(vtable)
        for line in vtable_viz.split('\n'):
            lines.append(prefix + line)
        
        # Find children
        children = [
            name for name, vt in vtables_data.items()
            if vt['parent'] == class_name
        ]
        
        if children:
            lines.append(prefix + "  │")
            lines.append(prefix + "  └─ inherited by:")
            for child in children:
                lines.append(prefix + "     ↓")
                show_class(child, indent + 1)
    
    show_class('Object')
    return '\n'.join(lines)

