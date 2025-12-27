
## From monads to abstract machines

Many well-known machines fit this pattern:
- State monad -> store-passing machines
- Writer monad -> tracing and logging machines
- Maybe monad -> machines with failure
- Continuation monad -> control-flow machines
- IO monad -> interaction machines

The SECD machine as we have seen previously in this workbook
[ch05](./../../../../ch05/addition/am/secd/),
[CEK](./cek/) machine,
and many interpreters can be derived by choosing:
- a state space,
- a set of monadic actions,
- a sequencing rule.

*Category theory does not replace operational semantics.
It organises it.*
