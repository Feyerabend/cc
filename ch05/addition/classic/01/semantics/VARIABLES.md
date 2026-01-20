
## Rules for Variables and Scope in the modified PL/0


__1. Declaration and Scope__

- In this implementation we will separate *mutable variables* from *immutable variables*.
  The immutable variables are corresponding to constants (const declaration) in the programs.

- Variables must be declared in the declaration section of a block before they can be used,
  which goes for the constants also. This applies to the main program block as well as procedure
  blocks.

- The scope of a variable is limited to the block in which it is declared, including procedures.
  However, inner blocks can shadow variables from outer blocks. These inner variables
  are called local variables, in contrast to global variables.


__2. Global vs. Local Variables__

- Global variables:
    - Variables declared in the main program block are global.
    - They are accessible throughout the entire program, including inside procedures,
      unless shadowed by a local variable with the same name.

- Local variables:
    - Variables declared within a procedure block are local to that procedure.
    - They are not accessible outside the procedure in which they are defined.


__3. Lifetime__

- The lifetime of a variable is tied to the activation of the block in which it is declared:
    - Global variables persist for the lifetime of the entire program.
    - Local variables are created when the block or procedure is entered and destroyed when
      the block or procedure exits. (Runtime.)

__4. Usage in Expressions__

- Variables can be used in expressions and assignments once declared. For example:

```pascal
var x, y;
x := y + 5;
```

__5. Variable Shadowing__

- A variable declared in an inner block can shadow a variable with the same name from an outer
  block. In such cases, the inner variable takes precedence within the inner block.
  In this implementation this is illustrated by global and local variables.


__6. Procedures and Parameters__

- PL/0 does not support procedure parameters in its standard form. We do not either.
  A program in our case can look like:

```pascal
var x, y;           // global variables
procedure P;
    var y, z;       // local variables to P
    begin
        y := 10;    // refers to local y
        z := x + y; // refers to global x and local y
    end;

begin
    x := 5;         // assign to global x
    call P;         // call procedure P
end.
```

- Global Variables:
    - x and y are declared at the program level and accessible throughout the entire program.
- Local Variables:
    - y and z inside P are local to P and not accessible outside it.
- Shadowing:
    - The y inside P shadows the global y. Any reference to y inside P uses the local y.

In extended versions of PL/0 (which often support procedure parameters),
the behavior aligns more closely with Pascal.

In the original PL/0 nested blocks are also possible, like:

```pascal
procedure A;
    var x;

    procedure B;
        var y;

        procedure C;
            var z;
        begin
            z := y + 1
        end;

    begin
        y := x * 2;
        call C
    end;

begin
    x := 10;
    call B
end;

begin
    call A
end.
```

### Summary

- Variables in PL/0 are declared in the declaration section of a block.

- Global variables are declared in the main program block and are accessible
  everywhere unless shadowed.

- Local variables are declared in procedures and are accessible only within
  that procedure.

- PL/0 uses block scoping rules, where each block introduces a new scope,
  and variables have a lifetime tied to their block's execution.
