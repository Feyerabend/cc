import sys
from jvm_interpreter import JavaClassInterpreter

def main():
    if len(sys.argv) < 3:
        print("Usage: python main.py <classfile> <classpath> [-v]")
        sys.exit(1)
    filename = sys.argv[1]
    class_path = sys.argv[2].split(':')
    verbose = '-v' in sys.argv
    try:
        interpreter = JavaClassInterpreter(class_path)
        class_file = interpreter.load_and_parse_class(filename)
        if verbose:
            interpreter.print_class_details(class_file)
        result = interpreter.run_method(class_file.this_class.name, 'main', verbose)
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
