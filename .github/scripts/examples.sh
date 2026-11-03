#!/bin/bash
# Runs examples that have no test suite of their own, and checks their
# results, so that fixed examples keep working.
# Run from the repository root: bash .github/scripts/examples.sh

set -u
cd "$(dirname "$0")/../.."
out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT
export MPLBACKEND=Agg
failed=0

# expect <name> <dir> <text the output must contain> <command...>
expect() {
    local name=$1 dir=$2 want=$3
    shift 3
    (cd "$dir" && timeout 300 "$@") > "$out/$name.log" 2>&1
    local rc=$?
    if [ $rc -ne 0 ] || ! grep -q -F -- "$want" "$out/$name.log"; then
        echo "FAIL  $name (exit $rc, wanted \"$want\")"
        tail -20 "$out/$name.log"
        failed=1
    else
        echo "ok    $name"
    fi
}

expect ll1 ch05/sec5.5/LL1 "Input parsed successfully!" python3 LL1.py
expect max-parallel ch07/sec7.1.5/danc/max "Maximum element = 105" python3 maxelem.py
expect merge-parallel ch07/sec7.1.5/danc/merge "Sorted: [11, 12, 22, 25, 34, 64, 90]" python3 mergesort_parallel.py
expect applicative ch08/addition/category/lang/cool/05 "Result: Some(7)" python3 cat_applicative.py
expect free-monad ch08/addition/category/lang/cool/06 "[Console] Found: \"Alice\"" python3 cat_free.py
expect free-monad-next ch08/addition/category/lang/cool/06/next "[Console] Found: \"Alice\"" python3 cat_free.py
expect category-lisp ch08/addition/category/lang/lisp "(1 4 9 16)" python3 cat_lisp.py
expect continuation-lisp ch07/sec7.4/control/continue/lisp "0 failed" python3 test.py
expect cnn-feature-maps ch08/sec8.8/cnns "Saved feature_maps.png" python3 feature_maps.py
expect transformer ch08/sec8.7/ml/transformer "Demo completed successfully!" python3 sentiment.py

# The Lisp interpreter written in Lisp, on top of the Python Lisp
expect mini-lisp ch07/sec7.3/func/lisp "fib=21 sum=15" python3 -c "
from lisp import Lisp
import contextlib, io
lisp = Lisp()
with contextlib.redirect_stdout(io.StringIO()):
    lisp.run(open('mini-lisp.l').read())
    fib = lisp.run('(mini-eval example-fibonacci global-mini-env)')
    total = lisp.run('(mini-eval example-sum-list global-mini-env)')
print(f'fib={fib} sum={total}')
"

# The RISC-V assembler, linker and VM; setup.sh writes the sample programs
rm -rf "$out/riscv"
cp -r ch05/sec5.9/riscv/02 "$out/riscv"
expect riscv "$out/riscv" "All tests passed" bash -c "bash setup.sh > /dev/null && make -s all > /dev/null && python3 test.py"

# Files the examples write
rm -f ch08/sec8.8/cnns/feature_maps.png ch08/sec8.7/ml/transformer/advanced_transformer_model.pkl
find . -name __pycache__ -not -path './.git/*' -exec rm -rf {} +

exit $failed
