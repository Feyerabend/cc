# codegen.py - C CODE GENERATION ONLY (uses template)
from typing import Dict

C_TEMPLATE = """#include <stdio.h>
#include <stdlib.h>

// Base Object
typedef struct Object {{
    struct ObjectVTable* vtable;
}} Object;

typedef struct ObjectVTable {{
    void (*destroy)(Object* self);
}} ObjectVTable;

void object_destroy(Object* self) {{
    free(self);
}}

ObjectVTable object_vtable = {{
    .destroy = object_destroy
}};

// {class_name} Class
typedef struct {class_name} {{
    {parent} base;
}} {class_name};

typedef struct {class_name}VTable {{
    ObjectVTable base;
{method_declarations}
}} {class_name}VTable;

{method_implementations}

{class_name}VTable {class_name_lower}_vtable = {{
    .base = {{ .destroy = object_destroy }},
{vtable_entries}
}};

{class_name}* {class_name}_create() {{
    {class_name}* self = malloc(sizeof({class_name}));
    self->base.vtable = (ObjectVTable*)&{class_name_lower}_vtable;
    return self;
}}

int main() {{
    {class_name}* obj = {class_name}_create();
    (({class_name}VTable*)obj->base.vtable)->{first_method}((Object*)obj);
    ((ObjectVTable*)obj->base.vtable)->destroy((Object*)obj);
    return 0;
}}
"""

def generate_c_code(ast: Dict) -> str:
    """Generate C code from AST using template."""
    class_name = ast['name']
    parent = ast['parent']
    methods = ast['methods']
    
    # Build method declarations
    method_decls = []
    for method in methods:
        method_decls.append(f'    void (*{method["name"]})(Object* self);')
    
    # Build method implementations
    method_impls = []
    for method in methods:
        impl = [f'void {class_name}_{method["name"]}(Object* self) {{']
        for stmt in method['body']:
            if stmt['type'] == 'print':
                impl.append(f'    printf("{stmt["value"]}\\n");')
        impl.append('}\n')
        method_impls.append('\n'.join(impl))
    
    # Build vtable entries
    vtable_entries = []
    for method in methods:
        vtable_entries.append(f'    .{method["name"]} = {class_name}_{method["name"]},')
    
    return C_TEMPLATE.format(
        class_name=class_name,
        class_name_lower=class_name.lower(),
        parent=parent,
        method_declarations='\n'.join(method_decls),
        method_implementations='\n'.join(method_impls),
        vtable_entries='\n'.join(vtable_entries),
        first_method=methods[0]['name'] if methods else 'destroy'
    )

