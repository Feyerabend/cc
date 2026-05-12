
## Bayesian Virtual Machine

This is a small probabilistic virtual machine (VM) implemented in Python. It extends a
conventional stack-based bytecode interpreter with probabilistic operations -- `SAMPLE`,
`OBSERVE`, `PRIOR`, and `INFER` -- alongside standard distributions (Normal, Uniform,
Bernoulli, Beta). The goal is to show how probabilistic programming can be expressed at
the instruction level, making Bayesian inference a first-class operation in a VM.

The VM demonstrates one way to embed uncertainty directly into the execution model: instead
of computing a single deterministic result, a program can sample from distributions and
condition on observations, and the `INFER` instruction triggers approximate posterior
inference over the program's latent variables.
