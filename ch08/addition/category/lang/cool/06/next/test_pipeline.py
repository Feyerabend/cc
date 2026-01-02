# test_pipeline.py

from cat_free import (
    print_line,
    Free
)
from ir_lowering import lower_free
from trace_algebra import TraceAlgebra
from codegen_driver import generate


def build_test_program() -> Free:
    return (
        print_line("Hello")
        .bind(lambda _: print_line("World"))
    )


def test_ir_and_algebra():
    program = build_test_program()

    # STEP 1: Lower to IR
    ir = lower_free(program)

    assert len(ir.instructions) == 2, "IR should contain two instructions"

    # STEP 2: Run code algebra
    algebra = TraceAlgebra()
    generate(ir, algebra)

    output = algebra.state.dump()
    print(output)

    # Assertions = proof of correctness
    assert "PrintLine(Hello)" in output
    assert "PrintLine(World)" in output
    assert output.startswith("BEGIN")
    assert output.endswith("END")

    print("\nTEST PASSED")


if __name__ == "__main__":
    test_ir_and_algebra()
