#!/bin/bash
# Builds C programs with AddressSanitizer and UBSan and runs them, so that
# memory errors and undefined behaviour fixed earlier cannot come back.
# Run from the repository root: bash .github/scripts/sanitize.sh

set -u
cd "$(dirname "$0")/../.."
root=$(pwd)
out=$(mktemp -d)
trap 'rm -rf "$out"' EXIT

export ASAN_OPTIONS=detect_leaks=0
SAN="-std=gnu11 -g -O1 -fno-omit-frame-pointer -fsanitize=address,undefined -fno-sanitize-recover=all"
failed=0

# check <name> <dir> <input file or -> <expected exit code> <sources...>
check() {
    local name=$1 dir=$2 input=$3 expect=$4
    shift 4
    if ! (cd "$dir" && gcc $SAN -I. -w "$@" -o "$out/$name" -lm) > "$out/$name.cc" 2>&1; then
        echo "FAIL  $name (build)"
        cat "$out/$name.cc"
        failed=1
        return
    fi
    local rc
    if [ "$input" = "-" ]; then
        (cd "$dir" && timeout 60 "$out/$name" < /dev/null) > "$out/$name.log" 2>&1
    else
        (cd "$dir" && timeout 60 "$out/$name" < "$input") > "$out/$name.log" 2>&1
    fi
    rc=$?
    if [ $rc -ne "$expect" ] || grep -q -E 'ERROR: AddressSanitizer|runtime error:' "$out/$name.log"; then
        echo "FAIL  $name (exit $rc, expected $expect)"
        tail -20 "$out/$name.log"
        failed=1
    else
        echo "ok    $name"
    fi
}

check regvm      ch02/sec2.2.4/regvm                      -       0 regvm.c
check mem3       ch02/addition/mems                       -       0 mem3.c
check vm3-noarg  ch02/sec2.4/vm3                          -       1 main.c vm3.c
check scpu       ch04/addition/vms/cpu/scpu               -       0 test_cpu.c cpu.c
check schem      ch05/addition/interpreter/03             -       0 schem.c
check aspects    ch07/addition/effect/aspects             -       0 aspect_lang_v4_clean.c
check coroutine  ch07/sec7.4/coroutine/vm                 -       0 coroutine_vm.c
check gc-vm      ch07/sec7.4/memory/gc                    -       0 gc_vm_extended.c
check cek        ch08/addition/category/am/cek            -       0 cek.c
check conversion ch01/addition/base                       -       0 conversion.c
for f in ch07/sec7.3/concat/forth/*.f; do
    check "forth-$(basename "$f" .f)" ch07/sec7.3/concat/forth "$(basename "$f")" 0 forth.c
done

# The PL/0 compilers, on all their samples
for v in 03 04 05 06 07; do
    dir=ch05/addition/classic/$v
    work="$out/pl0-$v"
    cp -r "$dir" "$work"
    if ! make -C "$work" -s CC="gcc $SAN" > "$work.build" 2>&1; then
        echo "FAIL  pl0-$v (build)"
        cat "$work.build"
        failed=1
        continue
    fi
    # Each version takes its own set of output files, so the Makefile runs
    # the compiler. Its loop ignores exit codes; instead every sample must
    # leave an AST file, and the sanitizers must stay quiet.
    timeout 300 make -C "$work" -s samples > "$work.run" 2>&1
    pl0_ok=1
    if grep -q -E 'ERROR: AddressSanitizer|runtime error:' "$work.run"; then
        pl0_ok=0
    fi
    for sample in "$work"/samples/sample*.pas; do
        [ -s "$work/ast/$(basename "$sample" .pas).json" ] || pl0_ok=0
    done
    if [ $pl0_ok -eq 0 ]; then
        echo "FAIL  pl0-$v"
        grep -E -A20 'ERROR: AddressSanitizer|runtime error:' "$work.run" | head -40
        failed=1
        continue
    fi
    echo "ok    pl0-$v"
done

cd "$root"
exit $failed
