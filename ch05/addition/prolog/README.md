
## Prolog

Prolog is a declarative programming language based on formal logic, where
programs describe relations rather than sequences of commands. Computation
is performed by attempting to satisfy logical goals through unification
and systematic search, using mechanisms such as backtracking and resolution.
This makes Prolog particularly well suited for problems involving symbolic
reasoning, pattern matching, and knowledge representation.

Unlike procedural languages, Prolog separates what is true from how it is
computed. The programmer specifies facts and rules, and the language runtime
determines how to derive solutions. This shift in perspective was central
to its appeal in artificial intelligence research, where reasoning, inference,
and problem solving could be expressed in a form close to mathematical logic.

You might study examples of *interpreters*: [Simple-Prolog](./sprolog.py)
and [Mini-Prolog](mprolog.py). Example application [NLP](./nlp/).


### A Small Prolog Tutorial

Prolog is a *logic programming* language. You do NOT tell Prolog *how* to
compute things, you describe *facts* and *rules*,
and Prolog answers questions about them.

Think in terms of:
- Facts: what is true
- Rules: how truths relate
- Queries: what you ask

It can be hard to get around starting from an "imperative" perspective.
Imperative is like: "Do this, then do that."
Prolog is more:
```
This is true.
That is true.
Find values that make this statement true.
```
You describe logic, Prolog handles search. If you already think in terms
of relations and recursion, Prolog feels extremely powerful and minimalistic.


#### 1. Facts

Facts are simple statements that end with a period.

```prolog
parent(john, mary).
parent(mary, alice).
parent(john, bob).
male(john).
female(mary).
female(alice).
male(bob).
```
Each fact is a predicate:
```prolog
predicate(argument1, argument2, ...).
```



#### 2. Queries

You ask Prolog questions in the REPL:
```prolog
?- parent(john, mary).
true.

?- parent(mary, john).
false.
```
Using variables (capitalised):
```prolog
?- parent(john, X).
X = mary ;
X = bob ;
false.
```
Prolog finds all values that make the statement true.



#### 3. Rules

Rules describe relationships using facts and other rules.
Syntax:
```
head :- body.
```
Meaning:
"head is true if body is true"

Example: define a grandparent.
```prolog
grandparent(X, Z) :-
    parent(X, Y),
    parent(Y, Z).
```
Query:
```prolog
?- grandparent(john, X).
X = alice ;
false.
```



#### 4. Multiple Conditions

Comma means logical AND.
```prolog
father(X, Y) :-
    parent(X, Y),
    male(X).

mother(X, Y) :-
    parent(X, Y),
    female(X).
```



#### 5. Recursion

Prolog shines with recursive definitions.
Example: ancestor.
```prolog
ancestor(X, Y) :- parent(X, Y).
ancestor(X, Y) :-
    parent(X, Z),
    ancestor(Z, Y).
```
Query:
```prolog
?- ancestor(john, X).
X = mary ;
X = alice ;
X = bob ;
false.
```



#### 6. Lists

Lists look like this:
```prolog
[1,2,3]
[a,b,c]
[Head|Tail]
```
Example:
```prolog
member(X, [X|_]).
member(X, [_|Tail]) :-
    member(X, Tail).
```
Query:
```prolog
?- member(2, [1,2,3]).
true.

?- member(X, [a,b,c]).
X = a ;
X = b ;
X = c ;
false.
```



#### 7. Simple Arithmetic

Use is for evaluation:
```prolog
square(X, Y) :-
    Y is X * X.

?- square(5, Y).
Y = 25.
```
Comparison operators:
```
=:=   arithmetic equal
=\=   arithmetic not equal
<     less than
>     greater than
=<    less or equal
>=    greater or equal
```
Example:
```prolog
adult(X) :-
    age(X, A),
    A >= 18.
```



#### 8. Backtracking

Prolog automatically searches all possible solutions.
Example:
```prolog
color(red).
color(green).
color(blue).

?- color(X).
X = red ;
X = green ;
X = blue ;
false.
```
This is called backtracking.



#### 9. Typical Workflow (Unimplemented!)
1. Write facts and rules in a file, e.g. 'family.pl'
2. Load it:
```
?- consult(family).
```
or
```prolog
?- [family].
```
3. Ask queries.



### Prolog .. in the Early 1980s

Prolog emerged in the late 1970s as a logic programming language grounded in
formal logic and automated theorem proving. By the early 1980s, it had transitioned
from a research curiosity to a central focus of international research communities.
One marker of this transition was the Second International Logic Programming Conference
in 1984, held at Uppsala University in Sweden, in which I participated.
At this stage, Prolog was being explored not just as a programming language,
but as a foundation for a new paradigm where computation was expressed in terms of
logical relations and inference. The conference highlighted active research in
unification algorithms, execution models, and the efficient implementation
of logic interpreters and compilers.

Simultaneously, Prolog gained spectacular visibility through the Fifth Generation Computer
Systems (FGCS) project initiated by Japan’s Ministry of International Trade and Industry
(MITI) in 1982. The FGCS program aimed to leapfrog existing computer architectures by
focusing on massively parallel hardware and knowledge-based systems. Prolog was chosen
as the principal language of the project because of its declarative semantics and natural
fit with knowledge representation and automated reasoning. Researchers in Japan proposed
that Prolog, supported by new parallel architectures, could enable expert systems, natural
language understanding, and intelligent applications far beyond the capabilities of conventional
procedural languages. FGCS thus served both as a research incubator for parallel logic
programming and as a strategic statement about the potential of Prolog and logic
programming more broadly.

The Japanese emphasis on Prolog and logic programming provoked responses in the United States
and Europe. In the U.S., research funding agencies and academic groups accelerated work
on logic programming theory, Prolog implementations, and compiler technologies. But
unsurprisingly, there was strong interest in further developing already established
AI languages, especially variations of LISP, as well as in building specialised
hardware such as Lisp machines. Efforts such as the development of the
[WAM](./../am/wam/) (Warren Abstract Machine) by David H. D. Warren and others led
to much faster Prolog interpreters and compilers, making logic programming more
competitive with conventional languages. The WAM, first circulated in the early 1980s,
provided a practical abstract machine tailored to Prolog's execution model and became
a cornerstone of efficient Prolog implementations worldwide. Eventually, an AI winter
set in, as it became clear that Prolog was not the answer, and interest in the language waned.

* Clocksin, W. F., & Mellish, C. S. (1981). *Programming in Prolog*. Springer-Verlag.

* Feigenbaum, E. A., McCorduck, P., & Nii, H. P. (1983). *The fifth generation: Artificial intelligence and Japan's computer challenge to the world*. Reading, MA: Addison-Wesley.

* Kowalski, R. (1979). *Logic for problem solving*. New York, NY: North-Holland.

* Tärnlund, S.-Å. (Ed.). (1984). *Proceedings of the Second International Logic Programming Conference: Uppsala University, Uppsala, Sweden, July 2-6, 1984*. Ord & Form.  [oai_citation:0‡ci.nii.ac.jp](https://ci.nii.ac.jp/ncid/BA35940414)



![Clocksin](./../../assets/image/clocksin.png) ![Second](./../../assets/image/second.png) ![Logic](./../../assets/image/kowalski.png) ![Fifth](./../../assets/image/fifth.png) ![AI Prolog](./../../assets/image/aiprolog.png) ![Expert](./../../assets/image/expert.png) ![Art](./../../assets/image/art.png) ![Bratko](./../../assets/image/bratko.png)





