"""
Samples in FunLang

Collection of example programs demonstrating the syntax and features.
Each sample can be run independently.
"""

from funlang_parser import run_funlang, compile_funlang
from functional_vm import FunctionalVM



SAMPLES = {
    
    "hello": """
    -- Simple arithmetic
    (2 + 3) * 4
    """,
    
    "lambda": """
    -- Lambda function
    let double = fn x -> x * 2
    in double 21
    """,
    
    "composition": """
    -- Function composition
    let double = fn x -> x * 2
    in let increment = fn x -> x + 1
    in let compose = fn f -> fn g -> fn x -> f (g x)
    in let composed = compose double increment
    in composed 5
    """,
    
    "maybe_map": """
    -- Maybe type with map
    let double = fn x -> x * 2
    in let value = Some(10)
    in case value of
        Some(x) -> Some(double x);
        Nothing -> Nothing;
    """,
    
    "maybe_chain": """
    -- Maybe monad chain
    let value = Some(10)
    in case value of
        Some(x) -> 
            case Some(x * 2) of
                Some(y) -> Some(y + 5);
                Nothing -> Nothing;
            ;
        Nothing -> Nothing;
    """,
    
    "result_success": """
    -- Result type - success case
    let validate = fn x -> 
        if x > 0 
        then Ok(x) 
        else Err("Not positive")
    in validate 42
    """,
    
    "result_failure": """
    -- Result type - error case
    let validate = fn x -> 
        if x > 0 
        then Ok(x) 
        else Err("Not positive")
    in validate (-5)
    """,
    
    "pattern_match": """
    -- Pattern matching on Maybe
    let value = Some(42)
    in case value of
        Some(x) -> x * 2;
        Nothing -> 0;
    """,
    
    "nested_pattern": """
    -- Nested pattern matching
    let value = Some(Ok(42))
    in case value of
        Some(Ok(x)) -> x * 2;
        Some(Err(e)) -> 0;
        Nothing -> -1;
    """,
    
    "list_literal": """
    -- List literal
    [1, 2, 3, 4, 5]
    """,
    
    "currying": """
    -- Curried function
    let add = fn a -> fn b -> a + b
    in let add5 = add 5
    in add5 10
    """,
    
    "three_args": """
    -- Three-argument curried function
    let add3 = fn a -> fn b -> fn c -> a + b + c
    in add3 1 2 3
    """,
    
    "conditional": """
    -- If expression
    let x = 10
    in if x > 5
       then 100
       else 200
    """,
    
    "nested_conditional": """
    -- Nested if expressions
    let x = 7
    in if x > 10
       then 1
       else if x > 5
            then 2
            else 3
    """,
    
    "factorial_partial": """
    -- Partial factorial (manually unrolled)
    let n = 5
    in n * 4 * 3 * 2 * 1
    """,
    
    "church_numeral": """
    -- Church numeral (3)
    let three = fn f -> fn x -> f (f (f x))
    in let increment = fn x -> x + 1
    in three increment 0
    """,
    
    "church_boolean": """
    -- Church boolean (true)
    let true_fn = fn t -> fn f -> t
    in true_fn 42 100
    """,
    
    "combinator_k": """
    -- K combinator
    let k = fn x -> fn y -> x
    in k 42 100
    """,
    
    "combinator_i": """
    -- I combinator (identity)
    let i = fn x -> x
    in i 42
    """,
    
    "combinator_s": """
    -- S combinator
    let s = fn x -> fn y -> fn z -> (x z) (y z)
    in let k = fn x -> fn y -> x
    in let skk = s k k
    in skk 42
    """,
    
    "point_free": """
    -- Point-free style
    let compose = fn f -> fn g -> fn x -> f (g x)
    in let double = fn x -> x * 2
    in let increment = fn x -> x + 1
    in let pipeline = compose double increment
    in pipeline 5
    """,
    
    "multi_let": """
    -- Multiple let bindings
    let x = 5
    in let y = 3
    in let z = x * y
    in z + 10
    """,
    
    "pythagorean": """
    -- Pythagorean theorem (without sqrt)
    let a = 3
    in let b = 4
    in let square = fn x -> x * x
    in square a + square b
    """,
    
    "comparison": """
    -- Comparison operators
    let x = 10
    in if x == 10
       then if x < 20
            then 1
            else 2
       else 3
    """,
    
    "string_match": """
    -- String literal
    let greeting = "Hello, World!"
    in greeting
    """,
    
    "boolean_ops": """
    -- Boolean values
    if True
    then 1
    else 0
    """,
    
    "option_or_else": """
    -- Option with fallback
    let value = Nothing
    in case value of
        Some(x) -> x;
        Nothing -> 42;
    """,
    
    "result_chain": """
    -- Result chaining
    let parse = fn x -> Ok(x)
    in let validate = fn x ->
        if x > 0
        then Ok(x)
        else Err("Not positive")
    in case parse 10 of
        Ok(x) -> validate x;
        Err(e) -> Err(e);
    """,
    
    "eta_expansion": """
    -- Eta expansion
    let add_one = fn x -> x + 1
    in let expanded = fn y -> add_one y
    in expanded 5
    """,
    
    "pipe_simple": """
    -- Simple pipe
    let double = fn x -> x * 2
    in 5 |> double
    """,
    
    "pipe_chain": """
    -- Pipe chain
    let double = fn x -> x * 2
    in let increment = fn x -> x + 1
    in let square = fn x -> x * x
    in 5 |> increment |> double |> square
    """,
    
    "pipe_with_partial": """
    -- Pipe with partial application
    let add = fn a -> fn b -> a + b
    in let multiply = fn a -> fn b -> a * b
    in 10 |> add 5 |> multiply 2
    """,
    
    "pipe_complex": """
    -- Complex pipe with Maybe
    let double = fn x -> Some(x * 2)
    in let validate = fn x -> 
        if x > 0 then Some(x) else Nothing
    in case (10 |> validate) of
        Some(x) -> case (x |> double) of
            Some(y) -> y;
            Nothing -> 0;
        ;
        Nothing -> 0;
    """,
    
}


# TEST

def run_sample(name: str, debug: bool = False):
    """Run a single sample program."""
    if name not in SAMPLES:
        print(f"Sample '{name}' not found")
        return
    
    source = SAMPLES[name]
    print(f"{'='*60}")
    print(f"Running: {name}")
    print(f"{'='*60}")
    print("Source:")
    print(source)
    print()
    
    try:
        result = run_funlang(source, debug=debug)
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")
    
    print()


def run_all_samples(debug: bool = False):
    """Run all sample programs."""
    print(f"{'#'*60}")
    print(f"# Running All FunLang Samples")
    print(f"{'#'*60}")
    print()
    
    for name in SAMPLES.keys():
        run_sample(name, debug=debug)
    
    print(f"{'#'*60}")
    print(f"# All samples completed!")
    print(f"{'#'*60}")


def list_samples():
    """List all available samples."""
    print("Available samples:")
    for i, name in enumerate(SAMPLES.keys(), 1):
        # Extract first comment line as description
        lines = SAMPLES[name].strip().split('\n')
        desc = lines[0].replace('--', '').strip() if lines and lines[0].strip().startswith('--') else ""
        print(f"  {i:2d}. {name:25s} - {desc}")


def interactive():
    """Interactive mode - choose samples to run."""
    while True:
        print("\n" + "="*60)
        print("FunLang Sample Runner")
        print("="*60)
        print("1. List all samples")
        print("2. Run a specific sample")
        print("3. Run all samples")
        print("4. Exit")
        print()
        
        choice = input("Choose an option: ").strip()
        
        if choice == "1":
            list_samples()
        elif choice == "2":
            sample_name = input("Enter sample name: ").strip()
            debug = input("Debug mode? (y/n): ").strip().lower() == 'y'
            run_sample(sample_name, debug=debug)
        elif choice == "3":
            debug = input("Debug mode? (y/n): ").strip().lower() == 'y'
            run_all_samples(debug=debug)
        elif choice == "4":
            print("Goodbye!")
            break
        else:
            print("Invalid choice")




if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Run specific sample from command line
        sample_name = sys.argv[1]
        debug = "--debug" in sys.argv
        run_sample(sample_name, debug=debug)
    else:
        # Run all samples
        run_all_samples(debug=False)
