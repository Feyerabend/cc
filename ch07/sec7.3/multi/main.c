// main.c -- Mol Language REPL & Runner
#include "mol.h"

void run_code(const char *code) {
    Expr  *program = parse(code);
    Env   *env     = make_global_env();
    Value *result  = eval(program, env);
    print_value(result);
    printf("\n");
}

void run_file(const char *path) {
    FILE *f = fopen(path, "r");
    if (!f) { fprintf(stderr, "Cannot open file: %s\n", path); exit(1); }
    char *code = malloc(MAX_INPUT);
    size_t len = fread(code, 1, MAX_INPUT - 1, f);
    code[len] = '\0';
    fclose(f);
    run_code(code);
    free(code);
}

void run_repl(void) {
    char line[4096];
    Env *env = make_global_env();
    printf("Mol REPL -- type 'exit' or Ctrl-D to quit\n\n");
    while (1) {
        printf("mol> ");
        fflush(stdout);
        if (!fgets(line, sizeof(line), stdin)) { printf("\nBye!\n"); break; }
        size_t len = strlen(line);
        while (len > 0 && (line[len-1] == '\n' || line[len-1] == '\r')) line[--len] = '\0';
        if (strcmp(line, "exit") == 0 || strcmp(line, "quit") == 0) { printf("Bye!\n"); break; }
        if (len == 0) continue;
        Expr  *prog   = parse(line);
        Value *result = eval(prog, env);
        printf("=> ");
        println_value(result);
    }
}

/*  built-in test suite  */

static int test_count = 0, pass_count = 0;

static void test(const char *label, const char *code, const char *expected) {
    test_count++;
    Expr  *prog = parse(code);
    Env   *env  = make_global_env();
    Value *r    = eval(prog, env);

    /* capture print_value output into a buffer */
    char buf[1024]; FILE *tmp = fmemopen(buf, sizeof(buf) - 1, "w");
    FILE *old = stdout; stdout = tmp;
    print_value(r);
    fflush(tmp); fclose(tmp); stdout = old;
    buf[strlen(buf)] = '\0';

    if (strcmp(buf, expected) == 0) {
        pass_count++;
        printf("  \033[32m✓\033[0m %s\n", label);
    } else {
        printf("  \033[31m✗\033[0m %s\n    expected: %s\n    got:      %s\n",
               label, expected, buf);
    }
}

static void run_tests(void) {
    printf("Running tests..\n\n");

    /* integers & arithmetic */
    test("integer literal",   "42",              "42");
    test("addition",          "1 + 2",           "3");
    test("subtraction",       "10 - 3",          "7");
    test("multiplication",    "6 * 7",           "42");
    test("division",          "10 / 2",          "5");
    test("modulo",            "10 % 3",          "1");
    test("precedence",        "2 + 3 * 4",       "14");
    test("unary minus",       "-5 + 10",         "5");
    test("nested arithmetic", "(2 + 3) * (4 - 1)","15");

    /* booleans */
    test("true",              "true",            "true");
    test("false",             "false",           "false");
    test("not true",          "not true",        "false");
    test("!false",            "!false",          "true");
    test("and short-circuit", "false and error(\"!\")","false");
    test("or short-circuit",  "true or error(\"!\")", "true");

    /* comparisons */
    test("equal ints",        "3 == 3",          "true");
    test("not equal",         "3 != 4",          "true");
    test("less than",         "2 < 3",           "true");
    test("greater than",      "5 > 4",           "true");
    test("lte",               "3 <= 3",          "true");
    test("gte",               "4 >= 5",          "false");

    /* let & closures */
    test("let binding",       "let x = 10; x",   "10");
    test("closure",
         "let f = fn(x) x + 1; f(41)",           "42");
    test("curried",
         "let add = fn(a) fn(b) a + b; add(10)(32)", "42");
    test("higher order",
         "let apply = fn(f, x) f(x);"
         "let double = fn(x) x * 2;"
         "apply(double, 21)",                     "42");

    /* recursion via letrec */
    test("letrec factorial",
         "letrec fact = fn(n) if n == 0 1 else n * fact(n-1);"
         "fact(10)",
         "3628800");
    test("letrec fibonacci",
         "letrec fib = fn(n) if n <= 1 n else fib(n-1) + fib(n-2);"
         "fib(10)",
         "55");
    test("letrec closure captures binding",
         "letrec count = fn(n) if n == 0 0 else 1 + count(n - 1);"
         "count(42)",
         "42");

    /* if/else */
    test("if true",           "if true 1 else 2",  "1");
    test("if false",          "if false 1 else 2", "2");
    test("nested if",
         "let x = 5;"
         "if x > 10 \"big\" else if x > 3 \"med\" else \"small\"",
         "med");

    /* strings */
    test("string literal",    "\"hello\"",         "hello");
    test("string concat ++",  "\"hello\" ++ \" \" ++ \"world\"", "hello world");
    test("string equality",   "\"abc\" == \"abc\"","true");
    test("string inequality", "\"a\" == \"b\"",    "false");

    /* structs */
    test("struct literal",    "{x: 10, y: 20}.x",  "10");
    test("struct nested",
         "let p = {x: {v: 42}}; p.x.v",            "42");
    test("struct mutate",
         "let s = {x: 1};"
         "let _ = s.x = 99;"
         "s.x",                                     "99");

    /* lists */
    test("empty list",        "nil",               "[]");
    test("list literal",      "[1, 2, 3]",         "[1, 2, 3]");
    test("cons/head/tail",
         "let xs = cons(1, cons(2, nil));"
         "head(xs)",                               "1");
    test("nil?",              "nil?(nil)",          "true");
    test("nil? false",        "nil?([1,2])",        "false");
    test("len list",          "len([1,2,3,4])",     "4");
    test("len string",        "len(\"hello\")",     "5");
    test("list append ++",    "[1,2] ++ [3,4]",    "[1, 2, 3, 4]");

    /* map/filter/foldl */
    test("map double",
         "letrec double = fn(x) x * 2;"
         "map(double, [1,2,3])",
         "[2, 4, 6]");
    test("filter even",
         "letrec even = fn(x) x % 2 == 0;"
         "filter(even, [1,2,3,4,5,6])",
         "[2, 4, 6]");
    test("foldl sum",
         "letrec add = fn(a,b) a+b;"
         "foldl(add, 0, [1,2,3,4,5])",
         "15");

    /* variadic */
    test("variadic fn",
         "let f = fn(x, ..rest) len(rest);"
         "f(1, 2, 3, 4)",                         "3");

    /* vtable / OOP */
    test("vtable method",
         "let VT = { speak: fn(self) self.sound };"
         "let dog = { vptr: VT, sound: \"woof\" };"
         "dog.speak()",                            "woof");
    test("polymorphism",
         "let IntVT = { get: fn(self) self.value };"
         "let PairVT = { get: fn(self) self.first + self.second };"
         "let a = {vptr: IntVT, value: 42};"
         "let b = {vptr: PairVT, first: 10, second: 20};"
         "a.get() + b.get()",                     "72");

    /* closures + letrec combined */
    test("make adder",
         "let makeAdder = fn(n) fn(x) x + n;"
         "let add10 = makeAdder(10);"
         "add10(32)",                             "42");

    printf("\n%d / %d tests passed\n", pass_count, test_count);
    if (pass_count == test_count)
        printf("\033[32mAll tests passed!\033[0m\n");
    else
        printf("\033[31m%d test(s) failed.\033[0m\n", test_count - pass_count);
}

/*  main  */

int main(int argc, char **argv) {
    if (argc == 2 && strcmp(argv[1], "--test") == 0) {
        run_tests(); return 0;
    }
    if (argc == 2 && strcmp(argv[1], "--repl") == 0) {
        run_repl(); return 0;
    }
    if (argc == 2) {
        run_file(argv[1]); return 0;
    }
    if (argc == 3 && strcmp(argv[1], "-e") == 0) {
        run_code(argv[2]); return 0;
    }

    /* default: demo */
    printf("Mol -- OO & Functional Language\n");
    printf("----------------------------------\n\n");

    printf("1. Closures & higher-order functions:\n   ");
    run_code("let makeAdder = fn(n) fn(x) x + n; let add10 = makeAdder(10); add10(32)");

    printf("\n2. Recursion with letrec:\n   ");
    run_code("letrec fact = fn(n) if n == 0 1 else n * fact(n-1); fact(10)");

    printf("\n3. Lists, map, filter, foldl:\n   ");
    run_code(
        "letrec double = fn(x) x * 2;"
        "letrec sum    = fn(a, b) a + b;"
        "foldl(sum, 0, map(double, filter(fn(x) x % 2 == 0, [1,2,3,4,5,6,7,8,9,10])))");

    printf("\n4. Strings:\n   ");
    run_code("let greet = fn(name) \"Hello, \" ++ name ++ \"!\"; greet(\"World\")");

    printf("\n5. Structs & OOP via vtable:\n   ");
    run_code(
        "let AnimalVT = { speak: fn(self) self.name ++ \" says \" ++ self.sound };"
        "let dog = {vptr: AnimalVT, name: \"Dog\", sound: \"woof\"};"
        "let cat = {vptr: AnimalVT, name: \"Cat\", sound: \"meow\"};"
        "dog.speak() ++ \" / \" ++ cat.speak()");

    printf("\n6. Fibonacci (letrec):\n   ");
    run_code("letrec fib = fn(n) if n <= 1 n else fib(n-1) + fib(n-2); fib(12)");

    printf("\n7. Variadic functions:\n   ");
    run_code(
        "let sum_all = fn(..xs) foldl(fn(a,b) a+b, 0, xs);"
        "sum_all(1, 2, 3, 4, 5, 6, 7, 8, 9, 10)");

    printf("\n\nRun with --test for the full test suite, --repl for interactive mode.\n");
    printf("Run with -e 'expr' to evaluate a single expression.\n");
    printf("Run with <file.mol> to run a script.\n");
    return 0;
}
