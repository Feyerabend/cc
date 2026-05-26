
## HoTT

Homotopy Type Theory grows out of Martin-Löf Type Theory, and one of the easiest mistakes
to make at first is to think that HoTT is some kind of external geometric interpretation
attached afterward to ordinary type theory. Historically that is understandable, because
topology entered the story later, but conceptually it is misleading. The homotopical
interpretation emerges because the identity structure already present in MLTT turns out
to behave in a very peculiar and very rich way when one examines it carefully enough.

So it is best to begin with [MLTT](./mltt) itself.

In ordinary set theory, mathematical objects are usually conceived as elements inside 
collections. One writes something like "x belongs to S," and equality is taken as primitive.
Either two things are equal or they are not. Equality itself has no internal structure.
It is a flat relation. If two objects are equal, then all distinctions vanish immediately
and absolutely.

MLTT begins somewhere very different. Instead of sets and membership, one starts from
judgments. One does not primarily say that an object belongs to a collection. One instead
says that a term inhabits a type. One writes something like

```text id="f6vm7m"
a : A
```

which means that the term `a` has type `A`.

At first this may appear merely notational, but philosophically it is a profound shift.
Mathematics becomes organized around construction rather than collection. A type is not
merely a passive container of objects. It behaves more like a specification of possible
constructions or admissible forms of evidence.

This is why MLTT is constructive at its core. To assert existence means that one can
actually produce something inhabiting the relevant type. Existence becomes tied to
construction rather than to abstract logical possibility. This is already very far
from classical set-theoretic ontology.

Dependent types deepen this further. A type may itself depend on a term. One may have
a family of types varying over another type. For example, instead of merely speaking
of vectors in general, one may speak of vectors of a particular length. So the length
becomes internal to the type itself. A vector of length three and a vector of length
five belong to genuinely different types. Structural information that in ordinary
mathematics might be carried externally as predicates or constraints becomes internalised
into the logical framework itself.

Now the crucial point for HoTT is that MLTT already contains identity types.
Suppose one has two terms of the same type:
```
a : A
b : A
```

Then one may form the identity type
```
Id_A(a,b)
```

which is often written more simply as
```
a =_A b
```

A beginner naturally interprets this as ordinary equality. But something very strange is
hiding here. In MLTT, the identity itself is a type. That means an equality is not merely
a truth value. It may have inhabitants. A proof that `a` equals `b` is itself an object.

This is the decisive conceptual turning point.

In ordinary logic, equality is merely asserted. In MLTT, equality is inhabited. One can
ask not merely whether two things are equal, but how they are equal, because a proof
of equality is itself mathematical structure.

And then another question immediately appears. Suppose there are two proofs that `a` equals `b`.
Are those proofs themselves equal? Since proofs are objects, one may again form an identity
type between them. But then equalities between equalities may themselves possess equalities.
The process continues indefinitely.

At this point one has accidentally wandered into higher-dimensional structure.

This is where the homotopical interpretation enters. Mathematicians discovered that the formal
behavior of identity types corresponds remarkably closely to the behaviour of paths in topology.
One may interpret a type as a space, a term as a point in that space, and an identity proof
as a path connecting two points. Then equality between proofs becomes a homotopy between paths.
Higher equalities become higher homotopies.

What is astonishing is that this is not merely poetic analogy. The formal algebraic structure
actually matches.

So [HoTT](./code/) emerges when one begins interpreting MLTT geometrically. Types are no
longer merely logical collections of constructions. They become spaces of connectivity
and transformation.

This changes the meaning of identity itself. Equality no longer behaves like a primitive
logical fact. It behaves like navigability inside a structured space.

In classical mathematics, if two things are equal, that is the end of the story. In HoTT,
equality may possess many distinct witnesses, many paths, many layers of structure.
Identity becomes something rich and potentially higher-dimensional.

This is philosophically radical because Western metaphysics has often treated identity as
absolute and transparent. HoTT instead suggests that sameness itself may possess geometry.

One of the most famous developments in HoTT is the Univalence Axiom introduced by Vladimir
Voevodsky. Very roughly speaking, univalence says that equivalent structures may be identified.
In ordinary mathematics, one constantly treats isomorphic or equivalent structures as
"essentially the same," but classical foundations maintain a rigid distinction between
equality and equivalence. HoTT weakens that distinction dramatically.

Under univalence, if two structures are equivalent in the appropriate sense, then this
equivalence itself induces identity. Identity becomes invariant under structural equivalence
rather than dependent upon rigid objecthood.

This has enormous philosophical consequences. Objects cease being isolated atoms with
intrinsic essence. Instead, structure and transformability become primary.

This is why HoTT resonates so strongly with category theory and structural mathematics.
Modern mathematics increasingly studies transformations, equivalences, mappings, and
coherence conditions rather than isolated substances. HoTT internalizes this tendency
into the foundations themselves.

Another important development is the notion of higher inductive types. Ordinary inductive
definitions generate points or elements. Higher inductive types additionally generate paths
and higher identifications directly. One can, for example, define a circle not as a set of
points embedded somewhere else, but synthetically, by specifying a point together with a
loop from that point back to itself.

This is one of the strangest and most beautiful ideas in HoTT. Geometry becomes internally
generative inside logic itself. Topological structure no longer has to be imported externally
through sets and constructions. It may arise directly from the rules generating the type.

This is part of why HoTT feels so different from ordinary set-theoretic thinking. In set
theory, one usually begins with objects and then imposes structure. In HoTT, structure is
there from the beginning because identity itself already carries transformational content.

And despite all of this abstraction, HoTT remains deeply computational. This comes directly
from its roots in MLTT. Proofs are still constructions. Type checking remains algorithmic.
Formal reasoning can still be mechanised inside proof assistants such as Coq, Lean, and Agda.

This computational aspect is crucial. HoTT is not merely metaphysical speculation disguised 
as mathematics. It is operational. Proofs can be executed, checked, transformed, and
manipulated computationally.

The remarkable thing is that the same formal object may simultaneously be understood
as a proof, a program, a path, a transformation, or a homotopy. Logic, computation,
and geometry begin collapsing into one another.

This is why many people find HoTT philosophically fascinating. It destabilizes several
classical assumptions at once. Identity becomes structured rather than absolute. Objects
become relational rather than atomic. Equivalence becomes more fundamental than rigid
equality. Mathematics becomes constructive, transformational, and geometric simultaneously.

The deepest conceptual leap in HoTT is actually very simple to state, although it takes
a long time to absorb fully:

__Equality is not merely a yes-or-no fact. Equality itself has internal structure.__

Almost everything else in HoTT unfolds from taking that idea completely seriously.

### Reference

* [The HoTT Book](https://homotopytypetheory.org/book/)

* A fun introdution to [MLTT/HoTT](https://www8.cs.fau.de/ext/teaching/sose2021/hott/mltt-intro.pdf)

