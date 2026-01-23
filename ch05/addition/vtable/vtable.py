from dataclasses import dataclass
from typing import Optional, List, Dict

@dataclass
class Method:
    """Represents a method entry in a VTable."""
    name: str
    implementation: str  # which class implements it
    overridden_from: Optional[str] = None

@dataclass  
class VTable:
    """Represents a Virtual Method Table."""
    class_name: str
    parent: Optional[str]
    methods: List[Method]
    
    def to_dict(self) -> Dict:
        """Export as dictionary for visualization."""
        return {
            'class_name': self.class_name,
            'parent': self.parent,
            'methods': [
                {
                    'name': m.name,
                    'implementation': m.implementation,
                    'overridden': m.overridden_from is not None,
                    'overridden_from': m.overridden_from
                }
                for m in self.methods
            ]
        }
