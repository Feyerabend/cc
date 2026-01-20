
## Modified PL/0 Grammar in EBNF

The grammar of PL/0 can be expressed in Extended Backus-Naur Form (EBNF).
EBNF is a notation for formalising the grammar rules of a language.
Here we will though introduce a modified version of PL/0: *PL/E*.

```ebnf
<program>       ::= <block> "." .

<block>         ::= [ "const" <const-declaration> ";" ]
                    [ "var" <var-declaration> ";" ]
                    { "procedure" <ident> ";" <procedure-body> ";" }
                    <statement> .

<procedure-body> ::= [ "var" <var-declaration> ";" ]
                     <statement> .

<const-declaration> ::= <ident> "=" <number> { "," <ident> "=" <number> } .

<var-declaration>   ::= <ident> { "," <ident> } .

<statement>     ::= <assignment>
                 | <procedure-call>
                 | <begin-end>
                 | <if-statement>
                 | <while-statement>
                 | .

<assignment>    ::= <ident> ":=" <expression> .

<procedure-call>::= "call" <ident> .

<begin-end>     ::= "begin" <statement> { ";" <statement> { ";" } } "end" .

<if-statement>  ::= "if" <condition> "then" <statement> .

<while-statement> ::= "while" <condition> "do" <statement> .

<condition>     ::= "(" <expression> <relational-operator> <expression> ")" .

<relational-operator> ::= "=" | "#" | "<" | "<=" | ">" | ">=" .

<expression>    ::= [ "+" | "-" ] <term> { ("+" | "-") <term> } .

<term>          ::= <factor> { ("*" | "/") <factor> } .

<factor>        ::= <ident>
                 | <number>
                 | "(" <expression> ")" .

<ident>         ::= [a-zA-Z_][a-zA-Z_0-9]* .

<number>        ::= [0-9]+ .
```

### Explanation of Grammar

__1. Program Structure__
- A program consists of a block followed by a `.` to signify its end.

__2. Block__
- A block may declare constants, variables, and procedures, followed by a main statement.
- No nested procedures are allowed; only one level procedures.

__3. Declarations__
- const declarations assign constant values to identifiers. Constants can not be declared inside a procedure body.
- var declarations define variable names.
- procedure declarations define subprograms that can be invoked.

__4. Statements__
- Statements are the building blocks of the program and include:
- Assignments (:=).
- Procedure calls (call).
- Compound statements enclosed in begin and end.
- A statement can be ended with a semicolon.
- Control flow like if and while.

__5. Expressions__
- Expressions follow arithmetic rules, allowing operators (+, -, *, /) and parentheses.

__6. Conditions__
- Conditions include relational operators (=, #, <, <=, >, >=). They are enclosed by parentheses.

__7. Identifiers and Numbers__
- Identifiers are alphanumeric names starting with a letter or underscore.
- Numbers are sequences of digits.


### Example Modified PL/0 Program

```pascal
const max = 100;

var arg, ret, answer;

procedure isprime;
var i;
begin
  ret := 1;
  i := 2;
  while (i < arg) do
    begin
      if (arg / i * i = arg) then
        begin
          ret := 0;
          i := arg;
        end;
      i := i + 1;
    end
end;

begin
  arg := 2;
  while (arg < max) do
    begin
      call isprime;
      if (ret = 1) then answer := arg;
      arg := arg + 1;
    end
end.
```
