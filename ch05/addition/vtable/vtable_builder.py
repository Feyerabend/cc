from typing import Dict, List
from vtable import VTable, Method

class VTableBuilder:
    """Build VTables from class ASTs."""
    
    def __init__(self):
        self.classes: Dict[str, Dict] = {}
        self.vtables: Dict[str, VTable] = {}
        
        # Base Object class
        self.classes['Object'] = {
            'name': 'Object',
            'parent': None,
            'methods': [{'name': 'destroy', 'body': []}]
        }
    
    def add_class(self, ast: Dict):
        """Add a class AST."""
        self.classes[ast['name']] = ast
    
    def build(self):
        """Build all VTables in dependency order."""
        for class_name in self._topological_sort():
            self._build_vtable(class_name)
    
    def _topological_sort(self) -> List[str]:
        """Sort classes: parents before children."""
        visited = set()
        result = []
        
        def visit(name):
            if name in visited:
                return
            visited.add(name)
            
            cls = self.classes[name]
            parent = cls.get('parent')
            if parent and parent in self.classes:
                visit(parent)
            result.append(name)
        
        for name in self.classes:
            visit(name)
        return result
    
    def _build_vtable(self, class_name: str):
        """Build VTable for one class."""
        cls = self.classes[class_name]
        parent_name = cls.get('parent')
        
        methods = []
        inherited = {}
        
        # Inherit from parent
        if parent_name and parent_name in self.vtables:
            parent_vtable = self.vtables[parent_name]
            for method in parent_vtable.methods:
                inherited[method.name] = method
                methods.append(Method(
                    name=method.name,
                    implementation=method.implementation
                ))
        
        # Add/override methods
        for method_def in cls['methods']:
            method_name = method_def['name']
            
            if method_name in inherited:
                # Override
                for i, m in enumerate(methods):
                    if m.name == method_name:
                        methods[i] = Method(
                            name=method_name,
                            implementation=class_name,
                            overridden_from=inherited[method_name].implementation
                        )
                        break
            else:
                # New method
                methods.append(Method(
                    name=method_name,
                    implementation=class_name
                ))
        
        self.vtables[class_name] = VTable(
            class_name=class_name,
            parent=parent_name,
            methods=methods
        )
    
    def export(self) -> Dict:
        """Export all VTables as data."""
        return {
            name: vtable.to_dict() 
            for name, vtable in self.vtables.items()
        }

