## BASIC III: Running the Classics

The interpreter in [03](./../03/) (BASIC II) has a clean architecture, but it was
built for *simple programs*. Next to it, in [03/bas](./../03/bas/), lie the 102
programs from David Ahl's *BASIC Computer Games* (1978): Hammurabi, Super Star
Trek, Bagels and the rest. They were written for the BASICs of the late 1970s,
and most of them do not run on BASIC II.

Your task is to build *BASIC III*: an interpreter that runs as many of these
games as possible. You start from BASIC II and extend it in stages. Each stage
adds a feature the games need, and each one can be measured.


### Measuring progress

[`run_games.py`](./run_games.py) runs every game with the same scripted answers
(numbers, YES/NO, words) and reports how far each one got:

```sh
python3 run_games.py                          # BASIC II, the baseline
python3 run_games.py "python3 main.py --debug"   # your interpreter
python3 run_games.py "python3 main.py --debug" hammurabi.bas bagels.bas
```

With `--debug`, an interpreter built from BASIC II stops at the first error
instead of going on with the next line, which makes the results clearer.

| Outcome | Meaning |
| --- | --- |
| finished | ran to the end without errors |
| out of input | used up all 400 answers: it works, it just wanted more |
| running | still running after 5 seconds, often waiting in a loop |
| unsupported | stopped at a statement the interpreter does not know |
| error / crashed | an error from the interpreter, or a Python exception |

BASIC II, the baseline: *17 finished, 37 out of input, 21 running,
25 unsupported, 2 errors*. The goal of BASIC III is to get *unsupported*,
*error* and *crashed* to zero. "Finished" and "out of input" are both good
results.

What the games need, counted over all 102 programs:

| Feature | Games |
| --- | --- |
| Several statements on a line (`:`) | 102 |
| `PRINT` with `TAB(` and `;` | 101 |
| `GOTO` or `THEN n` after a `:` | 47 |
| `READ` / `DATA` | 31 |
| `IF ... THEN` followed by a statement | 30 |
| `STOP` | 26 |
| `LEFT$`, `RIGHT$`, `MID$` | 21 |
| `ON ... GOTO` / `ON ... GOSUB` | 20 |
| `DEF FN` (BASIC II has it) | 11 |
| `RESTORE` | 9 |

Before you start, copy BASIC II:

```sh
cp -r ../03/basic_ii basic_iii
cp ../03/main.py .            # then change basic_ii to basic_iii in it
python3 run_games.py "python3 main.py --debug"
```

Keep `../03/test_interpreter.py` passing (adapted to `basic_iii`) as you go.


### Stage 1: Keywords without spaces

Old BASICs ignored spaces, and the games rely on it:

```basic
10 PRINT"HAMURABI"
20 REM***SETUP***
30 IFX>5THEN100
40 FORI=1TO10
```

BASIC II finds the command by splitting the statement at the first space, so
`PRINT"HAMURABI"` is an unknown command `PRINT"HAMURABI"`.

*Hints:*
- Match the start of the statement against the keywords, longest first
  (`GOSUB` before `GO`, `RESTORE` before `REM`... and think about why that
  order matters).
- `REM` takes the rest of the statement as it is, including any `:`.
- A statement that starts with no keyword is an assignment: `X=5`.
- The keywords inside a statement (`THEN`, `TO`, `STEP`) need the same care:
  `IFX>5THEN100`.
- Careful with variable names that begin with a keyword. Classic BASIC simply
  did not allow them; you may do the same.


### Stage 2: A program counter for statements

This is the heart of the project. BASIC II keeps only a *line number* as its
program counter. When a line has several statements, it runs all of them, and
then looks at the line number. That breaks three things the games use all the
time:

```basic
10 IF X>5 THEN PRINT "BIG": GOTO 100
20 PRINT "SMALL"
```

When `X>5` is false, classic BASIC skips *the rest of the line*, both the
`PRINT` and the `GOTO`. BASIC II only skips the `PRINT`.

```basic
10 PRINT "A": GOTO 30: PRINT "NEVER"
```

After `GOTO 30`, the rest of line 10 must not run.

```basic
10 FOR I=1 TO 3: PRINT I;: NEXT I
```

`NEXT I` must jump back to the statement after the `FOR`, not to the start
of the line.

*Hints:*
- Load the program into a flat list of statements, in line order, and keep a
  map from each line number to the index of its first statement. The program
  counter is then an index into that list.

  ```python
  statements = []      # (line_number, text)
  line_start = {}      # line_number -> index in statements
  for number in sorted(code):
      line_start[number] = len(statements)
      for text in split_statements(code[number]):
          statements.append((number, text))
  ```

- `GOTO n` sets the counter to `line_start[n]`. `GOSUB` pushes the index of
  the *next statement* and jumps; `RETURN` pops it.
- An `IF` whose condition is false jumps to the first statement of the next
  line.
- `FOR` pushes a record with the variable, the end value, the step, and the
  index of the statement after the `FOR`. `NEXT` looks for the record of its
  variable on the stack, removes any loops nested inside it, and either jumps
  back or pops the record. `NEXT J,I` is `NEXT J` followed by `NEXT I`.
- A loop whose start is already past its end (`FOR I=1 TO 0`) still runs its
  body once in many BASICs of the time, Microsoft's among them, but not in
  others. Decide which behaviour you want, and write it down.
- With this in place, BASIC II's `_skip_to_next` and the line searches in
  `WHILE` can go: the stack holds what they search for.


### Stage 3: READ, DATA and RESTORE

```basic
10 READ N$, A
20 PRINT N$; " IS"; A
30 DATA "SMITH", 42, JONES, -3.5
40 RESTORE 30
```

*Hints:*
- Collect all `DATA` items when the program is loaded, in program order, and
  remember for each item the line it came from. `DATA` itself does nothing
  when it is reached.
- `READ` takes the next item. A string variable (`N$`) gets the text, a
  numeric one needs a number, or it is an error: `?SYNTAX ERROR IN 30`.
  Running out gives `?OUT OF DATA`.
- Items are separated by commas. A quoted item keeps its commas and spaces;
  an unquoted one is trimmed. Numbers may look like `.5`, `-3` or `1E3`.
- `RESTORE` goes back to the first item, `RESTORE n` to the first item at or
  after line `n`.
- The `INPUT` command in BASIC II already converts a field by variable type
  (`_read_values` in `io_commands.py`): you can share that code.


### Stage 4: ON ... GOTO and ON ... GOSUB

```basic
10 ON X GOTO 100, 200, 300
```

*Hints:*
- Evaluate `X`, take its integer part, and jump to the line in that position,
  counting from 1. If it is below 1 or beyond the list, go on to the next
  statement.
- With Stage 2 done, `ON ... GOSUB` is `GOSUB` with a computed target.


### Stage 5: The rest

Run `run_games.py`, look at what stops the most games, and fix that. Things
you are likely to meet:

- *Number formatting.* `PRINT 42` shows `42.0` in BASIC II. Classic BASIC
  prints ` 42 `: a space or minus sign before, and a space after.
- *`PRINT` layout:* `;` keeps the cursor where it is, `,` moves to the next
  14-column zone, `TAB(n)` moves to column `n`.
- *Arrays and plain variables* with the same name are separate: `A` and
  `A(3)` can exist side by side.
- *A string at the end of a line* may lack its closing quote:
  `PRINT "WARP ENGINE CONTROL --`.
- *Functions:* `INT` rounds down (`INT(-2.5)` is -3), `RND(1)` gives a number
  from 0 up to 1, `LEFT$`, `RIGHT$`, `MID$`, `LEN`, `STR$`, `VAL`, `ASC`,
  `CHR$`, `ABS`, `SGN`, `SQR`.
- *Machine-specific statements* such as `POKE` have no meaning here. Ignore
  them, or print a warning once.


### Testing as you go

For each stage, write small programs that show the behaviour and what they
should print, before you change the interpreter:

```basic
10 FOR I=1 TO 3: PRINT I;: NEXT I
20 PRINT
30 IF 1=2 THEN PRINT "NO": PRINT "NOT THIS EITHER"
40 PRINT "DONE"
```

should print ` 1  2  3 ` and then `DONE`. BASIC II prints this instead,
which shows two of the problems from Stage 2 and one from Stage 5:

```
1.0
NOT THIS EITHER
DONE
```

Turn such programs into automated tests,
and run `run_games.py` after each stage. The games are a good final check,
but they make poor tests on their own: when one fails, it is hard to see why.


### Further work

- `INPUT` with a prompt and several variables, as the games use it
  (`INPUT "YOUR NAME";N$`), in every form you find in the games.
- Line-based error messages in the style of the time: `?SYNTAX ERROR IN 120`.
- `STOP` and `CONT`: stop with the program counter kept, and go on later.
- Speed: parse each statement once, when the program is loaded, instead of
  every time it runs. Compare the run time of a long game before and after.


### Questions to reflect on

1. Stage 2 changes what the program counter *is*. Which commands became
   simpler, and which became more complicated? Why?
2. BASIC II searches the program text to find a matching `NEXT` or `WEND`.
   What does a stack of open loops give you instead, and what can still go
   wrong with badly nested loops in a game?
3. `DATA` is read when the program is loaded, not when the line is reached.
   What would happen in the games if it were the other way round?
4. Compare BASIC III with the interpreter in [01](./../01/). Which
   architectural changes in 03 made the stages above easier, and which got
   in the way?
