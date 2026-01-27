
## CYK

Your task here is to build a CYK parser. The CYK parser (Cocke–Younger–Kasami)
is a classic bottom-up dynamic programming algorithm for parsing strings generated
by a context-free grammar (CFG). It only works for grammars written in
*Chomsky Normal Form* (CNF).

It answers the question: Given a grammar G and a string w, does G generate w?
Optionally: how can w be parsed (parse trees)?


#### 1. Context-Free Grammar (CFG)

A CFG is a 4-tuple:
```
G = (V, Σ, P, S)
```
Where:
```
V = set of non-terminals
Σ = set of terminals
P = set of productions
S = start symbol
```
Example:
```
S → NP VP
NP → Det N
VP → V NP
Det → "the"
N → "cat"
V → "sees"
```



#### 2. Chomsky Normal Form (CNF)

CYK requires the grammar to be in CNF.

A grammar is in CNF if all rules have one of these forms:
```
A → BC        (two non-terminals)
A → a         (one terminal)
S → ε         (only if empty string, ε, is allowed)
```
Where:
```
A, B, C ∈ V
a ∈ Σ
```
No other forms are allowed:
- No mixed terminal/non-terminal
- No rules longer than 2 symbols on the right
- No ε-rules except possibly S → ε
- No unit rules like A → B



#### 3. Converting CFG → CNF

To use CYK you must:
1. Remove ε-productions
2. Remove unit productions
3. Remove useless symbols
4. Replace terminals in long rules
5. Break long rules into binary rules

Example:
```
A → B C D
```
Becomes:
```
A  → B X1
X1 → C D
```
If terminals appear in longer rules:
```
A → "a" B
```
Introduce new symbol:
```
Ta → "a"
A  → Ta B
```



#### 4. CYK Parsing Table

For input string:
```
w = w1 w2 ... wn
```
Create a triangular table:
```
T[i][l]
```
Meaning:
```
T[i][l] = set of non-terminals that can derive substring starting at i with length l
```
Indices:
```
i = 1 .. n
l = 1 .. n
```
Visualization:
```
l
^
|   T[1][4]
|  T[1][3] T[2][3]
| T[1][2] T[2][2] T[3][2]
|T[1][1] T[2][1] T[3][1] T[4][1]
+-----------------------------> i
```



#### 5. CYK Algorithm

Given grammar in CNF and input string w of length n.

```
Initialisation (length = 1):

For each position i:

For each rule A → wi:
    Add A to T[i][1]
```
Main DP:
```
For lengths l = 2..n:

For i = 1..n-l+1:
    For k = 1..l-1:
        For each rule A → B C:
            If B ∈ T[i][k] and C ∈ T[i+k][l-k]:
                Add A to T[i][l]
```
Acceptance:
```
If S ∈ T[1][n] then w ∈ L(G)
```



#### 6. Example

Grammar in CNF:
```
S  → NP VP
VP → V NP
NP → Det N
Det → "the"
N → "cat"
V → "sees"
```
String:
```
the cat sees the cat
```
After filling the table, if:
```
S ∈ T[1][5]
```
then the string is valid.



#### 7. Parse Tree Construction

To build parse trees, not just recognition, you store backpointers:

Instead of:
```
T[i][l] = {A, B, C}
```
You store:
```
T[i][l][A] = (k, B, C)
```
Meaning:
```
A → B C
split at k
```
This allows reconstruction of the parse tree recursively.



#### 8. Complexity

Time complexity:
```
O(|P| · n³)
```
Where:
- |P| = number of productions
- n = length of input

Space complexity:
```
O(n² · |V|)
```
CYK is slow compared to practical parsers, but:
- Simple
- Guaranteed correctness
- Good for teaching, theory, and small grammars



#### 9. What Is Required to Build a CYK Parser

You need:

__1. Grammar representation__

```
NonTerminals
Terminals
Productions in CNF
Start symbol
```
__2. CNF conversion pipeline__

```
CFG → CNF
```
__3. Table structure__

```
T[i][l] : set or map
```
__4. Production indexing__

For speed, pre-index rules:
```
Terminal rules:
    "a" → {A}

Binary rules:
    (B, C) → {A}
```
So lookup becomes fast:
```
For B in T[i][k]:
    For C in T[i+k][l-k]:
        For A in rules[(B,C)]:
            add A
```
__5. Optional parse tree storage__

Backpointer data structure.



#### 10. Minimal Pseudocode
```
function CYK(G, w):
    n = length(w)
    create T[n][n+1] as empty sets

    for i = 1 to n:
        for each A → w[i] in P:
            T[i][1].add(A)

    for l = 2 to n:
        for i = 1 to n-l+1:
            for k = 1 to l-1:
                for each A → B C in P:
                    if B in T[i][k] and C in T[i+k][l-k]:
                        T[i][l].add(A)

    return (S in T[1][n])
```



#### 11. CYK vs Practical Parsers

CYK is:
- Recognition-first
- Grammar-normal-form dependent
- Cubic time

Real parsers (LL, LR, Earley, GLR):
- Work on general CFGs
- Much faster
- Used in compilers and NLP

CYK is primarily a *theoretical baseline* showing how
CFG parsing can be reduced to dynamic programming.

