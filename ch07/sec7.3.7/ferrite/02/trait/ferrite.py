#!/usr/bin/env python3
"""
Ferrite Compiler with Trait System
"""

import sys
import os
import subprocess
import re
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple, Any, Set
from enum import Enum


# PARSER

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



# COMPILER

def sanitize_name(name: str) -> str:
    return name.replace('-', '_')

class Ownership(Enum):
    OWN = "own"
    BORROW = "borrow"
    BORROW_MUT = "borrow_mut"

@dataclass
class Lifetime:
    name: str

@dataclass
class Type:
    name: str
    is_ref: bool = False
    is_mut: bool = False
    lifetime: Optional[Lifetime] = None
    
    def is_copy(self, compiler: 'Compiler') -> bool:
        # Primitive types are Copy
        if self.name in ["i32", "i64", "u32", "u64", "bool", "unit"]:
            return True
        # References are Copy
        if self.is_ref:
            return True
        # Check if type implements Copy trait
        if self.name in compiler.structs:
            return compiler.type_implements_trait(self.name, "Copy")
        return False
    
    def to_c(self) -> str:
        base_map = {"i32": "int", "unit": "void", "List": "void"}
        base = base_map.get(self.name, sanitize_name(self.name))
        return f"{base}*" if self.is_ref else base

@dataclass
class TraitDef:
    name: str
    methods: Dict[str, Tuple[List[Type], Type]]  # method_name -> (params, return_type)
    
@dataclass
class TraitImpl:
    trait_name: str
    type_name: str
    method_impls: Dict[str, str]  # method_name -> function_name

@dataclass
class StructDef:
    name: str
    fields: Dict[str, Type]
    derives: Set[str] = field(default_factory=set)
    
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
        self.borrowed_immut_count = 0
        self.borrowed_mut = False

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
    
    def lookup_in_chain(self, name: str) -> Optional[Var]:
        return self.lookup(name)

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
        self.traits: Dict[str, TraitDef] = {}
        self.trait_impls: List[TraitImpl] = []
        self.codegen = CCodeGen()
        self.scope = Scope()
        self.errors: List[str] = []
        self.lt_counter = 0
        
        # Built-in traits
        self._register_builtin_traits()
    
    def _register_builtin_traits(self):
        # Copy trait (marker trait with no methods)
        self.traits["Copy"] = TraitDef("Copy", {})
        
        # Clone trait
        self.traits["Clone"] = TraitDef("Clone", {
            "clone": ([Type("Self", is_ref=True)], Type("Self"))
        })
        
        # Debug trait
        self.traits["Debug"] = TraitDef("Debug", {
            "debug": ([Type("Self", is_ref=True)], Type("unit"))
        })
    
    def type_implements_trait(self, type_name: str, trait_name: str) -> bool:
        # Check for explicit implementations
        for impl in self.trait_impls:
            if impl.type_name == type_name and impl.trait_name == trait_name:
                return True
        
        # Check derives
        if type_name in self.structs:
            if trait_name in self.structs[type_name].derives:
                return True
        
        return False
    
    def get_trait_method(self, type_name: str, trait_name: str, method_name: str) -> Optional[str]:
        """Get the implementation function name for a trait method"""
        for impl in self.trait_impls:
            if impl.type_name == type_name and impl.trait_name == trait_name:
                return impl.method_impls.get(method_name)
        return None
    
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
    
    def check_can_use(self, var: Var, var_name: str):
        if var.moved:
            self.errors.append(f"ERROR: Use of moved value '{var_name}'")
    
    def check_can_borrow_immut(self, var: Var, var_name: str):
        if var.moved:
            self.errors.append(f"ERROR: Cannot borrow moved value '{var_name}'")
        if var.borrowed_mut:
            self.errors.append(f"ERROR: Cannot borrow '{var_name}' as immutable because it is already borrowed as mutable")
    
    def check_can_borrow_mut(self, var: Var, var_name: str):
        if var.moved:
            self.errors.append(f"ERROR: Cannot borrow moved value '{var_name}'")
        if var.borrowed_mut:
            self.errors.append(f"ERROR: Cannot borrow '{var_name}' as mutable more than once")
        if var.borrowed_immut_count > 0:
            self.errors.append(f"ERROR: Cannot borrow '{var_name}' as mutable because it is already borrowed as immutable")
    
    def mark_moved_if_needed(self, var: Var, var_name: str):
        if var.ownership == Ownership.OWN and not var.typ.is_copy(self):
            var.moved = True
    
    def generate_derived_trait_impl(self, struct_name: str, trait_name: str):
        """Generate implementation for derived traits"""
        if trait_name == "Copy":
            # Copy is a marker trait, no implementation needed
            pass
        
        elif trait_name == "Clone":
            # Generate clone method
            struct = self.structs[struct_name]
            c_name = sanitize_name(struct_name)
            func_name = f"{c_name}_clone"
            
            self.codegen.emit(f"{c_name} {func_name}({c_name}* self) {{")
            self.codegen.indent += 1
            self.codegen.emit(f"{c_name} result;")
            for field_name in struct.fields:
                f_cname = sanitize_name(field_name)
                self.codegen.emit(f"result.{f_cname} = self->{f_cname};")
            self.codegen.emit("return result;")
            self.codegen.indent -= 1
            self.codegen.emit("}")
            self.codegen.emit("")
            
            # Register the implementation with proper return type
            self.trait_impls.append(TraitImpl(
                trait_name="Clone",
                type_name=struct_name,
                method_impls={"clone": func_name}
            ))
            
            # Register the function signature
            self.functions[func_name] = ([Type(struct_name, is_ref=True)], Type(struct_name))
        
        elif trait_name == "Debug":
            # Generate debug method
            struct = self.structs[struct_name]
            c_name = sanitize_name(struct_name)
            func_name = f"{c_name}_debug"
            
            self.codegen.emit(f"void {func_name}({c_name}* self) {{")
            self.codegen.indent += 1
            self.codegen.emit(f'printf("{struct_name} {{ ");')
            for i, field_name in enumerate(struct.fields):
                f_cname = sanitize_name(field_name)
                if i > 0:
                    self.codegen.emit(f'printf(", ");')
                self.codegen.emit(f'printf("{field_name}: %d", self->{f_cname});')
            self.codegen.emit('printf(" }}\\n");')
            self.codegen.indent -= 1
            self.codegen.emit("}")
            self.codegen.emit("")
            
            # Register the implementation
            self.trait_impls.append(TraitImpl(
                trait_name="Debug",
                type_name=struct_name,
                method_impls={"debug": func_name}
            ))
            
            # Register the function signature
            self.functions[func_name] = ([Type(struct_name, is_ref=True)], Type("unit"))
    
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
                self.check_can_use(var, expr)
                return c_name, var.typ
            self.errors.append(f"ERROR: Unknown variable '{expr}'")
            return c_name, Type("i32")
        
        if not isinstance(expr, list) or not expr:
            return "0", Type("unit")
        
        op = expr[0]
        
        # Trait method call or field access: (. obj method-or-field args...)
        if op == "." and len(expr) >= 3:
            obj_expr = expr[1]
            method_or_field = expr[2]
            
            # Compile object
            obj_code, obj_typ = self.compile_expr(obj_expr, True)
            
            # Get the underlying type (strip reference if present)
            type_name = obj_typ.name
            
            # First, try to find a trait method with this name
            found_impl = None
            for trait_name, trait_def in self.traits.items():
                if method_or_field in trait_def.methods:
                    impl_func = self.get_trait_method(type_name, trait_name, method_or_field)
                    if impl_func:
                        found_impl = impl_func
                        break
            
            # If we found a trait method implementation, call it
            if found_impl:
                # Always pass as reference for trait methods
                if obj_typ.is_ref:
                    args_codes = [obj_code]
                else:
                    args_codes = [f"&{obj_code}"]
                
                for arg in expr[3:]:
                    arg_code, _ = self.compile_expr(arg, True)
                    args_codes.append(arg_code)
                
                # Get return type from function registry
                ret_type = Type("i32")
                if found_impl in self.functions:
                    _, ret_type = self.functions[found_impl]
                
                if not value_needed:
                    args_str = ", ".join(args_codes)
                    self.codegen.emit(f"{found_impl}({args_str});")
                    return "0", ret_type
                
                temp = self.codegen.new_temp()
                args_str = ", ".join(args_codes)
                self.codegen.emit(f"{ret_type.to_c()} {temp} = {found_impl}({args_str});")
                return temp, ret_type
            
            # Not a trait method, try field access
            if isinstance(method_or_field, str) and type_name in self.structs:
                struct = self.structs[type_name]
                if method_or_field in struct.fields:
                    f_cname = sanitize_name(method_or_field)
                    field_type = struct.fields[method_or_field]
                    if not value_needed:
                        return "0", field_type
                    temp = self.codegen.new_temp()
                    access = f"{obj_code}->{f_cname}" if obj_typ.is_ref else f"{obj_code}.{f_cname}"
                    self.codegen.emit(f"{field_type.to_c()} {temp} = {access};")
                    return temp, field_type
            
            # If we get here, it's neither a trait method nor a field
            if type_name in self.structs:
                self.errors.append(f"ERROR: Unknown field '{method_or_field}' in struct '{type_name}'")
            else:
                self.errors.append(f"ERROR: Unknown method or field '{method_or_field}' for type '{type_name}'")
            return "0", Type("i32")
        
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
                    val_code, val_typ = self.compile_expr(expr[i + 1], True)
                    
                    if isinstance(expr[i + 1], str):
                        var = self.scope.lookup(sanitize_name(expr[i + 1]))
                        if var and var.ownership == Ownership.OWN and not val_typ.is_ref:
                            self.mark_moved_if_needed(var, expr[i + 1])
                    
                    f_cname = sanitize_name(field_names[i])
                    self.codegen.emit(f"{temp}.{f_cname} = {val_code};")
            return temp, Type(op)
        
        if op == "borrow":
            var_expr = expr[1]
            
            if isinstance(var_expr, list):
                var_code, var_typ = self.compile_expr(var_expr, True)
                if not value_needed:
                    return "0", Type(var_typ.name, is_ref=True)
                temp = self.codegen.new_temp()
                ref_typ = Type(var_typ.name, is_ref=True)
                self.codegen.emit(f"{ref_typ.to_c()} {temp} = &{var_code};")
                return temp, ref_typ
            
            if isinstance(var_expr, str):
                c_name = sanitize_name(var_expr)
                var = self.scope.lookup(c_name)
                if var:
                    self.check_can_borrow_immut(var, var_expr)
                    var.borrowed_immut_count += 1
                    
                    var_code, var_typ = c_name, var.typ
                    if not value_needed:
                        return "0", Type(var_typ.name, is_ref=True)
                    temp = self.codegen.new_temp()
                    ref_typ = Type(var_typ.name, is_ref=True)
                    self.codegen.emit(f"{ref_typ.to_c()} {temp} = &{var_code};")
                    return temp, ref_typ
                else:
                    self.errors.append(f"ERROR: Cannot borrow unknown variable '{var_expr}'")
                    return "0", Type("i32", is_ref=True)
            
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
            
            bindings = expr[1] if len(expr) > 1 else []
            for bind in bindings:
                if not isinstance(bind, list) or len(bind) < 2:
                    self.errors.append(f"ERROR: Invalid let binding: {bind}")
                    continue
                name, val_expr = bind[0], bind[1]
                c_name = sanitize_name(name)
                val_code, val_typ = self.compile_expr(val_expr, True)
                
                if isinstance(val_expr, str):
                    source_var = old_scope.lookup(sanitize_name(val_expr))
                    if source_var and source_var.ownership == Ownership.OWN and not val_typ.is_ref:
                        self.mark_moved_if_needed(source_var, val_expr)
                
                self.codegen.emit(f"{val_typ.to_c()} {c_name} = {val_code};")
                
                if val_typ.is_mut:
                    ownership = Ownership.BORROW_MUT
                elif val_typ.is_ref:
                    ownership = Ownership.BORROW
                else:
                    ownership = Ownership.OWN
                
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
            if isinstance(expr[1], str):
                val_code = sanitize_name(expr[1])
                var = self.scope.lookup(val_code)
                if var is None:
                    self.errors.append(f"ERROR: Unknown variable '{expr[1]}' in match")
                    val_code = "/* error */"
                    val_typ = Type("unknown")
                else:
                    self.check_can_use(var, expr[1])
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
                self.errors.append("ERROR: Non-exhaustive pattern match")
                self.codegen.emit(f"{result_temp} = 0;")
            
            return result_temp, Type("i32")
        
        # Function call
        c_func = sanitize_name(op)
        args_codes = []
        for i, arg in enumerate(expr[1:]):
            arg_code, arg_typ = self.compile_expr(arg, True)
            args_codes.append(arg_code)
            
            if isinstance(arg, str):
                var = self.scope.lookup(sanitize_name(arg))
                if var and var.ownership == Ownership.OWN and not arg_typ.is_ref:
                    if op in self.functions:
                        param_types, _ = self.functions[op]
                        if i < len(param_types) and not param_types[i].is_ref:
                            self.mark_moved_if_needed(var, arg)
        
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
    
    def compile_deftrait(self, form):
        """(deftrait TraitName (method-name [params] return-type) ...)"""
        name = form[1]
        methods = {}
        
        for method_decl in form[2:]:
            if not isinstance(method_decl, list) or len(method_decl) < 3:
                continue
            method_name = method_decl[0]
            params_list = method_decl[1]
            ret_type = self.parse_type(method_decl[2])
            
            param_types = [self.parse_type(p[1]) if isinstance(p, list) else Type("Self") for p in params_list]
            methods[method_name] = (param_types, ret_type)
        
        self.traits[name] = TraitDef(name, methods)
    
    def compile_impl(self, form):
        """(impl TraitName for TypeName (defn method-name ...))"""
        trait_name = form[1]
        type_name = form[3]
        
        if trait_name not in self.traits:
            self.errors.append(f"ERROR: Unknown trait '{trait_name}'")
            return
        
        method_impls = {}
        
        for method_def in form[4:]:
            if isinstance(method_def, list) and method_def[0] == "defn":
                method_name = method_def[1]
                func_name = f"{sanitize_name(type_name)}_{sanitize_name(method_name)}"
                
                # Compile the method as a regular function
                self.compile_defn(method_def, prefix=f"{sanitize_name(type_name)}_")
                
                method_impls[method_name] = func_name
        
        self.trait_impls.append(TraitImpl(trait_name, type_name, method_impls))
    
    def compile_defstruct(self, form):
        name = form[1]
        fields = {}
        derives = set()
        i = 2
        
        # Check for derive clause
        if i < len(form) and isinstance(form[i], list) and form[i] and form[i][0] == "derive":
            derives = set(form[i][1:])
            i += 1
        
        for f in form[i:]:
            if not f:
                continue
            f_name, f_type_expr = f
            fields[f_name] = self.parse_type(f_type_expr)
        
        self.structs[name] = StructDef(name, fields, derives)
        self.codegen.emit(self.structs[name].to_c())
        self.codegen.emit("")
        
        # Generate derived trait implementations
        for trait_name in derives:
            if trait_name in self.traits:
                self.generate_derived_trait_impl(name, trait_name)
    
    def compile_defn(self, form, prefix: str = ""):
        name = form[1]
        params = form[2]
        i = 3
        ret_type = Type("i32")
        
        # Check if next element is a return type (string or list) or body (list starting with expression)
        if len(form) > 3:
            next_elem = form[3]
            # If it's a string, it's a return type
            if isinstance(next_elem, str) and next_elem not in ["let", "if", "print", "+", "-", "*", "/", "match"]:
                ret_type = self.parse_type(next_elem)
                i = 4
            # If it's a list starting with "&", it's a reference type
            elif isinstance(next_elem, list) and next_elem and next_elem[0] == "&":
                ret_type = self.parse_type(next_elem)
                i = 4
        
        body = form[i:]
        
        param_types = []
        param_names = []
        for p in params:
            if isinstance(p, list) and len(p) >= 2:
                param_names.append(sanitize_name(p[0]))
                param_types.append(self.parse_type(p[1]))
            elif isinstance(p, list) and len(p) == 1:
                # Handle parameters without type (default to i32)
                param_names.append(sanitize_name(p[0]))
                param_types.append(Type("i32"))
        
        self.functions[name] = (param_types, ret_type)
        
        c_name = prefix + sanitize_name(name)
        c_params = ", ".join(f"{pt.to_c()} {pn}" for pt, pn in zip(param_types, param_names))
        self.codegen.emit(f"{ret_type.to_c()} {c_name}({c_params}) {{")
        self.codegen.indent += 1
        
        old_scope = self.scope
        self.scope = Scope(old_scope)
        
        for pn, pt in zip(param_names, param_types):
            if pt.is_mut:
                own = Ownership.BORROW_MUT
            elif pt.is_ref:
                own = Ownership.BORROW
            else:
                own = Ownership.OWN
            self.scope.add(Var(pn, pt, own))
        
        value_needed = (c_name != "main" and prefix + "main" != c_name)
        
        if body:
            for e in body[:-1]:
                self.compile_expr(e, False)
            last_code, _ = self.compile_expr(body[-1], value_needed)
        else:
            last_code = "0"
        
        if c_name == "main" or prefix + "main" == c_name:
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
        
        # First pass: define traits
        for form in ast:
            if form and form[0] == "deftrait":
                self.compile_deftrait(form)
        
        # Second pass: define structs (with derives)
        for form in ast:
            if form and form[0] == "defstruct":
                self.compile_defstruct(form)
        
        self.codegen.emit("typedef void* List;")
        self.codegen.emit("")
        
        # Third pass: process impl blocks (before functions so trait methods are available)
        for form in ast:
            if form and form[0] == "impl":
                self.compile_impl(form)
        
        # Fourth pass: define standalone functions (now trait methods are available)
        for form in ast:
            if form and form[0] == "defn":
                self.compile_defn(form)
        
        if self.errors:
            raise Exception("Compilation errors:\n" + "\n".join(self.errors))
        
        return self.codegen.get_code()


# CLI

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
    print(f"  Generated {output_path}")
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
