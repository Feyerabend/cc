
#!/usr/bin/env python3
"""
Ferrite Compiler - Zero warnings on all examples (final)
"""

import sys
import os
import subprocess
import re
from dataclasses import dataclass
from typing import List, Dict, Optional, Tuple, Any
from enum import Enum

# ============================================================================
# PARSER (robust)
# ============================================================================

class ParseError(Exception):
    pass

def skip_whitespace(source: str, pos: int) -> int:
    while pos < len(source):
        if source[pos].isspace():
            pos += 1
        elif source[pos] == ';':
            nl = source.find('\n', pos)
            pos = nl + 1 if nl != -1 else len(source)
        else:
            break
    return pos

def parse_atom(source: str, pos: int) -> Tuple[Any, int]:
    pos = skip_whitespace(source, pos)
    if pos >= len(source):
        raise ParseError("Unexpected EOF")
    
    m = re.match(r'-?\d+', source[pos:])
    if m:
        return int(m.group(0)), pos + m.end()
    
    m = re.match(r"[^\s()]+", source[pos:])
    if m:
        return m.group(0), pos + m.end()
    
    raise ParseError(f"Invalid atom at position {pos}")

def parse_list(source: str, pos: int) -> Tuple[List[Any], int]:
    pos = skip_whitespace(source, pos)
    if pos >= len(source) or source[pos] != '(':
        raise ParseError(f"Expected '(' at {pos}")
    pos += 1
    
    elements = []
    while True:
        pos = skip_whitespace(source, pos)
        if pos >= len(source):
            raise ParseError("Unclosed list")
        if source[pos] == ')':
            pos += 1
            return elements, pos
        elem, pos = parse_sexp(source, pos)
        elements.append(elem)

def parse_sexp(source: str, pos: int) -> Tuple[Any, int]:
    pos = skip_whitespace(source, pos)
    if pos >= len(source):
        raise ParseError("Unexpected EOF")
    if source[pos] == '(':
        return parse_list(source, pos)
    return parse_atom(source, pos)

def parse_program(source: str) -> List[Any]:
    forms = []
    pos = 0
    while pos < len(source):
        pos = skip_whitespace(source, pos)
        if pos >= len(source):
            break
        form, pos = parse_sexp(source, pos)
        forms.append(form)
    return forms

# ============================================================================
# COMPILER
# ============================================================================

def sanitize_name(name: str) -> str:
    return name.replace('-', '_')

class Ownership(Enum):
    OWN = "own"
    BORROW = "borrow"

@dataclass
class Lifetime:
    name: str

@dataclass
class Type:
    name: str
    is_ref: bool = False
    is_mut: bool = False
    lifetime: Optional[Lifetime] = None
    
    def to_c(self) -> str:
        base_map = {"i32": "int", "unit": "void", "List": "void"}
        base = base_map.get(self.name, sanitize_name(self.name))
        return f"{base}*" if self.is_ref else base

@dataclass
class StructDef:
    name: str
    fields: Dict[str, Type]
    
    def to_c(self) -> str:
        c_name = sanitize_name(self.name)
        lines = [f"{t.to_c()} {sanitize_name(f)};" for f, t in self.fields.items()]
        body = " ".join(lines) if lines else ""
        return f"typedef struct {{ {body} }} {c_name};"

class Var:
    def __init__(self, name: str, typ: Type, ownership: Ownership):
        self.name = name
        self.typ = typ
        self.ownership = ownership
        self.moved = False

class Scope:
    def __init__(self, parent: Optional['Scope'] = None):
        self.vars: Dict[str, Var] = {}
        self.parent = parent
    
    def lookup(self, name: str) -> Optional[Var]:
        if name in self.vars:
            return self.vars[name]
        return self.parent.lookup(name) if self.parent else None
    
    def add(self, var: Var):
        self.vars[var.name] = var

class CCodeGen:
    def __init__(self):
        self.lines: List[str] = []
        self.indent = 0
        self.temp_cnt = 0
    
    def emit(self, line: str = ""):
        self.lines.append("  " * self.indent + line)
    
    def new_temp(self) -> str:
        self.temp_cnt += 1
        return f"t{self.temp_cnt}"
    
    def get_code(self) -> str:
        return "\n".join(self.lines) + "\n"

class Compiler:
    def __init__(self):
        self.structs: Dict[str, StructDef] = {}
        self.functions: Dict[str, Tuple[List[Type], Type]] = {}
        self.codegen = CCodeGen()
        self.scope = Scope()
        self.errors: List[str] = []
        self.lt_counter = 0
    
    def fresh_lt(self) -> Lifetime:
        self.lt_counter += 1
        return Lifetime(f"a{self.lt_counter}")
    
    def parse_type(self, expr: Any) -> Type:
        if isinstance(expr, str):
            return Type(expr)
        if isinstance(expr, list) and expr and expr[0] == "&":
            lt = None
            mut = False
            i = 1
            if i < len(expr) and isinstance(expr[i], str) and expr[i].startswith("'"):
                lt = Lifetime(expr[i][1:])
                i += 1
            if i < len(expr) and expr[i] == "mut":
                mut = True
                i += 1
            base_name = expr[i]
            return Type(base_name, is_ref=True, is_mut=mut, lifetime=lt)
        return Type("i32")
    
    def compile_expr(self, expr: Any, value_needed: bool = True) -> Tuple[str, Type]:
        if isinstance(expr, int):
            if not value_needed:
                return "0", Type("i32")
            temp = self.codegen.new_temp()
            self.codegen.emit(f"int {temp} = {expr};")
            return temp, Type("i32")
        
        if isinstance(expr, str):
            c_name = sanitize_name(expr)
            var = self.scope.lookup(c_name)
            if var:
                if var.moved:
                    self.errors.append(f"Use of moved value '{expr}'")
                return c_name, var.typ
            self.errors.append(f"Unknown variable '{expr}'")
            return c_name, Type("i32")
        
        if not isinstance(expr, list) or not expr:
            return "0", Type("unit")
        
        op = expr[0]
        
        if op in self.structs:
            struct = self.structs[op]
            if not value_needed:
                return "0", Type(op)
            temp = self.codegen.new_temp()
            c_name = sanitize_name(op)
            self.codegen.emit(f"{c_name} {temp};")
            field_names = list(struct.fields.keys())
            for i in range(len(field_names)):
                if i + 1 < len(expr):
                    val_code, _ = self.compile_expr(expr[i + 1], True)
                    f_cname = sanitize_name(field_names[i])
                    self.codegen.emit(f"{temp}.{f_cname} = {val_code};")
            return temp, Type(op)
        
        if op == ".":
            obj_code, obj_typ = self.compile_expr(expr[1], True)
            field_name = expr[2]
            f_cname = sanitize_name(field_name)
            if not value_needed:
                return "0", Type("i32")
            temp = self.codegen.new_temp()
            access = f"{obj_code}->{f_cname}" if obj_typ.is_ref else f"{obj_code}.{f_cname}"
            self.codegen.emit(f"int {temp} = {access};")
            return temp, Type("i32")
        
        if op == "borrow":
            var_expr = expr[1]
            var_code, var_typ = self.compile_expr(var_expr, True)
            if not value_needed:
                return "0", Type(var_typ.name, is_ref=True)
            temp = self.codegen.new_temp()
            ref_typ = Type(var_typ.name, is_ref=True)
            self.codegen.emit(f"{ref_typ.to_c()} {temp} = &{var_code};")
            return temp, ref_typ
        
        if op == "let":
            old_scope = self.scope
            self.scope = Scope(old_scope)
            
            for bind in expr[1]:
                name, val_expr = bind
                c_name = sanitize_name(name)
                val_code, val_typ = self.compile_expr(val_expr, True)
                self.codegen.emit(f"{val_typ.to_c()} {c_name} = {val_code};")
                ownership = Ownership.BORROW if val_typ.is_ref else Ownership.OWN
                self.scope.add(Var(c_name, val_typ, ownership))
            
            body_exprs = expr[2:]
            if not body_exprs:
                result_code, result_typ = "0", Type("unit")
            else:
                for e in body_exprs[:-1]:
                    self.compile_expr(e, False)
                result_code, result_typ = self.compile_expr(body_exprs[-1], value_needed)
            
            self.scope = old_scope
            return result_code, result_typ
        
        if op == "print":
            arg_code, arg_typ = self.compile_expr(expr[1], True)
            deref = "*" if arg_typ.is_ref else ""
            self.codegen.emit(f'printf("%d\\n", {deref}{arg_code});')
            return "0", Type("i32")
        
        if op == "if":
            cond_code, _ = self.compile_expr(expr[1], True)
            if not value_needed:
                self.codegen.emit(f"if ({cond_code}) {{")
                self.codegen.indent += 1
                self.compile_expr(expr[2], False)
                self.codegen.indent -= 1
                self.codegen.emit("} else {")
                self.codegen.indent += 1
                self.compile_expr(expr[3], False)
                self.codegen.indent -= 1
                self.codegen.emit("}")
                return "0", Type("i32")
            else:
                result_temp = self.codegen.new_temp()
                self.codegen.emit(f"int {result_temp};")
                self.codegen.emit(f"if ({cond_code}) {{")
                self.codegen.indent += 1
                then_code, _ = self.compile_expr(expr[2], True)
                self.codegen.emit(f"{result_temp} = {then_code};")
                self.codegen.indent -= 1
                self.codegen.emit("} else {")
                self.codegen.indent += 1
                else_code, _ = self.compile_expr(expr[3], True)
                self.codegen.emit(f"{result_temp} = {else_code};")
                self.codegen.indent -= 1
                self.codegen.emit("}")
                return result_temp, Type("i32")
        
        ops = {"==": "==", "!=": "!=", "<": "<", ">": ">", "<=": "<=", ">=": ">=",
               "+": "+", "-": "-", "*": "*", "/": "/", "%": "%"}
        if op in ops:
            left_code, _ = self.compile_expr(expr[1], True)
            right_code, _ = self.compile_expr(expr[2], True)
            if not value_needed:
                return "0", Type("i32")
            temp = self.codegen.new_temp()
            c_op = ops[op]
            self.codegen.emit(f"int {temp} = {left_code} {c_op} {right_code};")
            return temp, Type("i32")
        
        if op == "match":
            # Key fix: if matching on a variable, use it directly
            if isinstance(expr[1], str):
                val_code = sanitize_name(expr[1])
                var = self.scope.lookup(val_code)
                if var is None:
                    self.errors.append(f"Unknown variable '{expr[1]}' in match")
                    val_code = "/* error */"
                    val_typ = Type("unknown")
                else:
                    val_typ = var.typ
            else:
                val_code, val_typ = self.compile_expr(expr[1], True)
            
            if not value_needed:
                for case in expr[2:]:
                    pat = case[0]
                    body = case[1]
                    pat_kind = pat[0]
                    if pat_kind in ["Nil", "Cons"]:
                        old_scope = self.scope
                        self.scope = Scope(old_scope)
                        struct = self.structs.get(pat_kind)
                        if struct:
                            field_names = list(struct.fields.keys())
                            for i, pat_var in enumerate(pat[1:]):
                                if i >= len(field_names):
                                    break
                                f_name = field_names[i]
                                f_cname = sanitize_name(f_name)
                                access = f"(({pat_kind}*){val_code})->{f_cname}"
                                v_cname = sanitize_name(pat_var)
                                self.codegen.emit(f"int {v_cname} = {access};")
                                self.scope.add(Var(v_cname, Type("i32"), Ownership.BORROW))
                        self.compile_expr(body, False)
                        self.scope = old_scope
                        return "0", Type("i32")
                return "0", Type("i32")
            
            result_temp = self.codegen.new_temp()
            self.codegen.emit(f"int {result_temp};")
            
            matched = False
            for case in expr[2:]:
                pat = case[0]
                body = case[1]
                pat_kind = pat[0]
                
                if pat_kind in ["Nil", "Cons"]:
                    old_scope = self.scope
                    self.scope = Scope(old_scope)
                    
                    struct = self.structs.get(pat_kind)
                    if struct:
                        field_names = list(struct.fields.keys())
                        for i, pat_var in enumerate(pat[1:]):
                            if i >= len(field_names):
                                break
                            f_name = field_names[i]
                            f_cname = sanitize_name(f_name)
                            access = f"(({pat_kind}*){val_code})->{f_cname}"
                            v_cname = sanitize_name(pat_var)
                            self.codegen.emit(f"int {v_cname} = {access};")
                            self.scope.add(Var(v_cname, Type("i32"), Ownership.BORROW))
                    
                    body_code, _ = self.compile_expr(body, True)
                    self.codegen.emit(f"{result_temp} = {body_code};")
                    matched = True
                    
                    self.scope = old_scope
                    break
            
            if not matched:
                self.errors.append("No matching pattern in match")
                self.codegen.emit(f"{result_temp} = 0;")
            
            return result_temp, Type("i32")
        
        c_func = sanitize_name(op)
        args_codes = [self.compile_expr(a, True)[0] for a in expr[1:]]
        if not value_needed:
            args_str = ", ".join(args_codes)
            self.codegen.emit(f"{c_func}({args_str});")
            return "0", Type("i32")
        temp = self.codegen.new_temp()
        args_str = ", ".join(args_codes)
        ret_typ = Type("i32")
        if op in self.functions:
            _, ret_typ = self.functions[op]
        self.codegen.emit(f"{ret_typ.to_c()} {temp} = {c_func}({args_str});")
        return temp, ret_typ
    
    def compile_defstruct(self, form):
        name = form[1]
        fields = {}
        for f in form[2:]:
            if not f:
                continue
            f_name, f_type_expr = f
            fields[f_name] = self.parse_type(f_type_expr)
        self.structs[name] = StructDef(name, fields)
        self.codegen.emit(self.structs[name].to_c())
        self.codegen.emit("")
    
    def compile_defn(self, form):
        name = form[1]
        params = form[2]
        i = 3
        ret_type = Type("i32")
        if len(form) > 3 and isinstance(form[3], str):
            ret_type = self.parse_type(form[3])
            i = 4
        
        body = form[i:]
        
        param_types = [self.parse_type(p[1]) for p in params]
        param_names = [sanitize_name(p[0]) for p in params]
        
        self.functions[name] = (param_types, ret_type)
        
        c_name = sanitize_name(name)
        c_params = ", ".join(f"{pt.to_c()} {pn}" for pt, pn in zip(param_types, param_names))
        self.codegen.emit(f"{ret_type.to_c()} {c_name}({c_params}) {{")
        self.codegen.indent += 1
        
        old_scope = self.scope
        self.scope = Scope(old_scope)
        
        for pn, pt in zip(param_names, param_types):
            own = Ownership.BORROW if pt.is_ref else Ownership.OWN
            self.scope.add(Var(pn, pt, own))
        
        value_needed = (c_name != "main")
        
        if body:
            for e in body[:-1]:
                self.compile_expr(e, False)
            last_code, _ = self.compile_expr(body[-1], value_needed)
        else:
            last_code = "0"
        
        if c_name == "main":
            self.codegen.emit("return 0;")
        elif ret_type.name != "unit":
            self.codegen.emit(f"return {last_code};")
        
        self.scope = old_scope
        self.codegen.indent -= 1
        self.codegen.emit("}")
        self.codegen.emit("")
    
    def compile_program(self, ast: List[Any]) -> str:
        self.codegen.emit("#include <stdio.h>")
        self.codegen.emit("")
        
        for form in ast:
            if form and form[0] == "defstruct":
                self.compile_defstruct(form)
        
        self.codegen.emit("typedef void* List;")
        self.codegen.emit("")
        
        for form in ast:
            if form and form[0] == "defn":
                self.compile_defn(form)
        
        if self.errors:
            raise Exception("Compilation errors:\n" + "\n".join(self.errors))
        
        return self.codegen.get_code()

# ============================================================================
# CLI
# ============================================================================

def compile_file(input_path: str, output_path: Optional[str] = None):
    if not output_path:
        output_path = input_path.replace('.fe', '.c')
    with open(input_path, 'r') as f:
        source = f.read()
    ast = parse_program(source)
    compiler = Compiler()
    c_code = compiler.compile_program(ast)
    with open(output_path, 'w') as f:
        f.write(c_code)
    print(f"✓ Generated {output_path}")
    return output_path

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 ferrite.py <input.fe> [-o output.c]")
        sys.exit(1)
    
    input_file = sys.argv[1]
    
    if '-o' in sys.argv:
        idx = sys.argv.index('-o')
        if idx + 1 < len(sys.argv):
            compile_file(input_file, sys.argv[idx + 1])
        else:
            print("Error: -o needs output file")
            sys.exit(1)
    else:
        compile_file(input_file)

if __name__ == "__main__":
    main()
