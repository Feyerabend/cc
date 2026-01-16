
## Teaching / Learning

This part of the material focuses on experimentation, construction, and shared exploration.
Rather than presenting finished solutions, it is designed to support learning through building,
discussion, and iteration. The emphasis is on understanding systems by engaging with them directly,
both in hardware and in software.

*Group work* plays an important role here. Modern computing systems are rarely understood in isolation,
and neither is learning. By working together, participants can divide attention between different
aspects of the system: electronics, firmware, graphics, timing, data representation, and interaction.
Explaining discoveries to one another is itself a powerful learning mechanism, often revealing
assumptions that would otherwise remain implicit.

*Practice* is central. The examples in this folder are not meant to be read passively but to be modified,
broken, rebuilt, and extended. Small experiments accumulate into a broader understanding of how
computation emerges from simple components: registers, memory, signals, and code. Repetition with
variation is encouraged; running the same idea in slightly different forms often exposes deeper structure.

*Large Language Models* may be used as tools when appropriate. They can assist with exploration,
explanation, and alternative formulations, but they are not substitutes for understanding.
Their role here is pragmatic: to support learning and experimentation, not to replace reasoning
or design. Knowing when and how to use such tools is itself becoming an important computing skill.

This chapter, and the accompanying software, centres on the Raspberry Pi Pico, together with the
Pimoroni Display Pack 2.0. Despite its small size, the Pico is a powerful and expressive platform.
It sits at an interesting boundary between hardware and software: close enough to the metal to expose
timing, concurrency, and resource constraints, yet rich enough to support graphics, interaction,
and non-trivial program structure.

Through these experiments, participants will encounter a wide range of computing concepts in concrete
form. These include event-driven programming, state machines, concurrency and scheduling, memory management,
communication protocols, and basic graphics pipelines. Some examples may naturally lead towards operating
system concepts, even if no full operating system is present. Others connect outward, showing how small
embedded systems relate to larger technical and social systems, such as distributed computation or
block-chain-inspired ideas.

The goal is not to teach one specific technology, but to illustrate how ideas recur across scales.
The same principles that govern a microcontroller reacting to button presses also appear in servers
handling network traffic or distributed systems coordinating across continents. By starting small and
tangible, the abstractions remain grounded.

This folder should therefore be read as a workshop rather than a library. It is a place to try things out,
to ask "what happens if ..", and to connect theory with practice. The hardware is simple enough to invite
experimentation, yet rich enough to reward careful thought.

One of the projects (2FA) also creates a natural platform for experimenting with *teamwork*, security,
and adversarial design, where different groups can take on complementary and competing roles.
One team may design and implement a secure communication scheme, inspired by ideas such as two-factor
authentication, where commands are only accepted when multiple independent conditions are satisfied,
such as a valid signature combined with a time- or sequence-based token. Another team can act as an
attacking group, attempting to disrupt communication by injecting malformed commands, replaying messages,
or exploiting weaknesses in the protocol. This transforms the system into a small, controlled laboratory
for studying secure data transfer, protocol robustness, and fault tolerance in embedded systems. Because
the display Pico produces immediate visual feedback, the effects of both good design and successful attacks
become directly observable, turning abstract security concepts into something concrete, interactive,
and educational.
