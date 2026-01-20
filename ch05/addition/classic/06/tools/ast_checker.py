import json
import sys

NODE_RULES = {
    "PROGRAM": {"required_children": ["children"], "required_fields": ["type", "value"]},
    "BLOCK": {"required_children": ["children"], "required_fields": ["type", "value"]},
    "VAR_DECL": {"required_children": [], "required_fields": ["type", "value"]},
    "CONST_DECL": {"required_children": [], "required_fields": ["type", "value"]},
    "PROC_DECL": {"required_children": ["children"], "required_fields": ["type", "value"]},
    "ASSIGNMENT": {"required_children": ["children"], "required_fields": ["type", "value"]},
    "EXPRESSION": {"required_children": ["children"], "required_fields": ["type", "value"]},
    "IDENTIFIER": {"required_children": [], "required_fields": ["type", "value"]},
    "NUMBER": {"required_children": [], "required_fields": ["type", "value"]},
    "WHILE": {"required_children": ["children"], "required_fields": ["type", "value"]},
    "CONDITION": {"required_children": ["children"], "required_fields": ["type", "value"]},
    "IF": {"required_children": ["children"], "required_fields": ["type", "value"]},
    "OPERATOR": {"required_children": ["children"], "required_fields": ["type", "value"]},
    "TERM": {"required_children": ["children"], "required_fields": ["type", "value"]},
    "CALL": {"required_children": [], "required_fields": ["type", "value"]},
}

def validate_node(node, path="root"):
    errors = []

    if "type" not in node or node["type"] not in NODE_RULES:
        errors.append(f"{path}: Unknown or missing 'type': {node.get('type', None)}")
        return errors
    
    node_type = node["type"]
    rules = NODE_RULES[node_type]
    
    for field in rules["required_fields"]:
        if field not in node:
            errors.append(f"{path}: Missing required field '{field}'")
    
    if "children" in rules["required_children"]:
        if "children" not in node or not isinstance(node["children"], list):
            errors.append(f"{path}: Missing or invalid 'children'")
        else:
            for i, child in enumerate(node["children"]):
                child_path = f"{path}.children[{i}]"
                errors.extend(validate_node(child, child_path))
    
    return errors

def validate_ast(ast):
    return validate_node(ast)


if __name__ == "__main__":
    input_file = sys.argv[1]

    try:
        with open(input_file, "r") as file:
            ast = json.load(file)
    except FileNotFoundError:
        print(f"Error: The file '{input_file}' was not found.")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse JSON from the file '{input_file}': {e}")
        sys.exit(1)

    validation_errors = validate_ast(ast)
    if validation_errors:
        print("Validation Errors:")
        for error in validation_errors:
            print(f"- {error}")
    else:
        print("The AST seems valid.")
