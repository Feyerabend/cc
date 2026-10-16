#!/bin/sh
# Runs the tests with the PC build of the VM: sh tests/run.sh ./lisp_host

host=${1:-./lisp_host}
dir=$(dirname "$0")
failed=0

pass() { echo "ok    $1"; }
fail() { echo "FAIL  $1"; failed=1; }

# Language: compare printed output with the expected output
if "$host" "$dir/language.lisp" > "$dir/language.out" 2>/dev/null &&
   diff -u "$dir/language.expected" "$dir/language.out"; then
    pass "language"
else
    fail "language"
fi

# Errors must be reported, not crash the VM
check_error() {
    printf '%s\n' "$1" > "$dir/error.lisp"
    msg=$("$host" "$dir/error.lisp" 2>&1 >/dev/null)
    case "$msg" in
        *"$2"*) pass "error: $2" ;;
        *) fail "error: $2 (got: $msg)" ;;
    esac
    rm -f "$dir/error.lisp"
}

check_error '(undefined-thing)' 'Undefined: undefined-thing'
check_error '(1 2)' 'Not a function'
check_error '(car 5)' 'car: not a list'
check_error '(+ 1 "a")' 'Expected a number'
check_error '(/ 1 0)' 'division by zero'
check_error '(define (f x) x) (f)' 'Wrong number of arguments'
check_error '(define (deep n) (+ 1 (deep n))) (deep 1)' 'Nested too deeply'
check_error '(define (grow l) (grow (cons 1 l))) (grow ())' 'Out of memory'
check_error '(+ 1 2' 'Missing )'
check_error ')' 'Unexpected )'
check_error '"open' 'Missing closing "'
check_error '(set! nothing 1)' 'set!: undefined: nothing'
check_error '(make-sprite 0 5)' 'Sprite size'
check_error '(on-update (lambda () (car 1))) (start)' 'Error in frame 0'

# Games: run with button presses and check they draw without errors
for game in minimal shooter snake; do
    if "$host" "$dir/../examples/$game.lisp" -q -f 600 \
        -p a@20 -p x@30-90 -p y@100-160 -p b@200 -p a@260 -p x@300 \
        2> "$dir/$game.out"; then
        pass "game: $game"
    else
        fail "game: $game ($(cat "$dir/$game.out"))"
    fi
done

exit $failed
