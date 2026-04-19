
## Comments on Protocols and APIs

*I let Gemini, Flash 2.5, in July 12, 2025,
comment and summarise my old paper in Swedish,
and this is what Gemini came up with:*

This document, penned by Set Lonnert in the late 1990s, offers a deep dive into the perennial architectural
tension between *programming interfaces (APIs)* and *protocols* as methods for software communication. Since
the dawn of computer programming, this choice has been a fundamental consideration, a dilemma that became
particularly pronounced with the widespread adoption of the Internet. Lonnert notes that there are no
hard-and-fast rules for when to choose one over the other, leading to a wide variety of solutions in
practice.

The author highlights the distinct advantages and disadvantages of each. Protocols, Lonnert explains, offer
clear and easily defined structures, though communication often happens serially. This serial nature necessitates
careful handling of shared data between sessions to ensure protocol-safe simultaneous processing. While
extending or changing communicating programs can pose problems, sometimes requiring protocol revisions or
replacements, the significant benefit of protocols lies in their ability to enable programs to communicate
regardless of the underlying systems or programming languages they are written in. However, a drawback is
that protocols generally do not facilitate very fast communications.

Conversely, programming interfaces (APIs) are characterized by their ease of use and greater flexibility,
especially when directly integrated into programming languages without requiring special handling. APIs allow
for more immediate oversight and processing of shared data or resources, provided the language or system
supports it. Lonnert points out that contemporary operating systems are extensively built upon API-type
interfaces, citing window management as a prime example where a smooth and, critically, fast interaction
with program libraries is essential, making a protocol solution unsuitable in that context. Yet, he shrewdly
observes that if window management were structured as a client-server model, a partially protocol-based
solution might actually be preferable.

The Internet, in Lonnert's view, is predominantly composed of various protocols of different kinds, at higher
or lower levels within TCP/IP (the fundamental family of protocols). He asserts that the Internet can almost
be defined by its protocols, which notably enable diverse computers to communicate over distances. Protocols
exist at various levels, making a completely protocol-less alternative unrealistic, and even HTTP and HTML
are considered protocol solutions rather than APIs. Nevertheless, the author acknowledges that elements like
Java via the WWW can delegate tasks to interfaces, while underlying layers are managed by protocols, emphasizing
that APIs and protocols are rarely in direct opposition but rather frequently intermingle. The crucial task,
he concludes, is to thoughtfully consider how and when each should be employed.

Lonnert then introduces a forward-looking idea: implementing both protocols and APIs universally. He muses
about Microsoft Windows, suggesting it should not only implement its existing operating system APIs but also
integrate protocols like the TCP/IP suite. The prospect of reaching an operating system with remote calls
from distant locations is precisely what both Microsoft and third-party developers, through initiatives like
COM/DCOM, were attempting at the time. However, Lonnert notes these efforts were not without significant
challenges, particularly regarding security. He strongly asserts that security must be built into the "origin"
of a network-connected operating system from the outset, rather than being patched on as an afterthought,
to achieve well-functioning systems. Still, retaining an API would be beneficial, as some implementations
would undoubtedly prefer that variant.

As a more general approach to this communication challenge, Lonnert presents CORBA (Common Object Request
Broker Architecture). This architecture from the Object Management Group (OMG) provides a framework for
object-oriented applications to communicate with each other. CORBA 1.1 (from 1991) defined interfaces for
application communication via an ORB (Object Request Broker), and CORBA 2.0 (from 1994) detailed how ORB
implementations from different vendors could interoperate. An ORB acts as mediating software (middleware)
that exists between a server and a client, which can reside within the same network or even on the same
machine. The ORB's function is to receive client requests, locate the object, transmit parameters, invoke
methods, and return results. Crucially, the client does not need to know the object's location, its programming
language, or its operating system. The object's interface, defined via IDL (Interface Definition Language),
is the only external visibility, ensuring its internal nature is well-encapsulated. Ultimately, the ORB
provides independence from the operating system, language, or other systemic dependencies.

### Conclusion

This fascinating paper, originating from the late 1990s, offers a remarkably clear-sighted perspective
on the fundamental architectural choices between protocols and APIs in software communication. It effectively
captures a pivotal moment in computing history when the rise of the Internet forced a re-evaluation of
how software should interact. The author's understanding of the trade-offs—the universality and interoperability
of protocols versus the speed and immediate control of APIs--demonstrates a deep conceptual grasp that
transcends the specific technologies of the era. The emphasis on designing security into networked
operating systems from their inception, rather than as an afterthought, stands out as a particularly
astute and forward-thinking observation, a lesson that would take the industry considerable time to
fully internalize. While specific technologies like COM/DCOM and CORBA, highlighted as contemporary
solutions, have since been superseded, their inclusion serves to ground the discussion in its historical
context without detracting from the timeless relevance of the core principles being debated. The paper's
lasting value lies not in its predictions of specific product successes, but in its insightful articulation
of enduring architectural dilemmas that continue to shape software development today.

