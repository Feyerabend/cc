
## Governing AI: Institutions, Frameworks, and the Problem of Speed

### Introduction: The Governance Gap

Every major technology that has reshaped society has eventually acquired governance
frameworks--regulatory structures, legal liabilities, institutional oversight,
international agreements--that attempt to manage its risks while preserving its
benefits. The pharmaceutical industry took decades and several catastrophes
(thalidomide, most visibly) before robust drug approval frameworks existed.
Nuclear technology acquired governance structures partly through the near-misses
that made the stakes viscerally clear. Aviation safety became what it is through
accumulated accident investigation and mandatory reporting. In each case, the
governance followed the technology, often at significant cost in the interim.

AI governance is attempting something different and more difficult: to build
adequate frameworks before the most consequential capabilities arrive, on the
basis of capabilities that are already significant and accelerating, without
the clarity that catastrophe provides. This is genuinely novel. The frameworks
being built now are being built in the dark, by institutions whose timescales
and incentive structures were not designed for this kind of problem.

The result, as of the mid-2020s, is a patchwork. There is serious, technically
sophisticated legislation in the European Union. There are executive orders,
voluntary commitments, and emerging agency frameworks in the United States.
There is a nascent international process anchored in the Bletchley Declaration
and its successors. There are substantial gaps, enforcement questions, and
jurisdictional problems that no current framework has solved. And there is
a persistent underlying tension: the institutions most capable of governing
AI are not the ones building it, and the ones building it have structural
reasons to prefer governance that does not constrain capability development.

Understanding what has been built, what it does and does not cover, and what
the hardest remaining problems are, is essential for anyone who wants to
think clearly about where AI development is actually going--as distinct from
where various interested parties say it is going.


### Part I: The European Union--The AI Act

#### The World's First Comprehensive AI Legislation

The EU AI Act, finalised in 2024 after several years of negotiation and
significant amendment, is the most comprehensive attempt to govern AI
systems through legislation yet produced. It is worth understanding in some
detail, both for what it achieves and for what it reveals about the
difficulties of the project.

The Act organises AI systems into risk tiers:

*Unacceptable risk* systems are prohibited outright. These include social
scoring systems of the kind deployed in China, real-time biometric surveillance
in public spaces (with narrow exceptions for law enforcement), AI systems
that exploit psychological vulnerabilities, and systems that manipulate
people subliminally. The prohibition of social scoring reflects a direct
judgement that this application of AI is incompatible with European values
of human dignity and non-discrimination, regardless of its technical
sophistication.

*High-risk* systems require conformity assessment before deployment, ongoing
monitoring, transparent documentation, and human oversight mechanisms.
High-risk categories include AI used in critical infrastructure, education,
employment decisions, essential services, law enforcement, migration management,
and the administration of justice. The underlying logic is that in these
domains, AI errors have consequences that cannot simply be corrected after
the fact--a wrong hiring decision, a wrongful deportation, a misidentified
suspect.

*Limited risk* systems face transparency obligations: users must be informed
when they are interacting with an AI system, when content is AI-generated,
and when emotion recognition or biometric categorisation is being used.

*Minimal risk* systems--most AI applications--face no specific obligations
under the Act.

*General purpose AI* (GPAI) models, added in later negotiations following
the emergence of large language models as a dominant paradigm, face additional
obligations including transparency about training data, technical documentation,
and for the most capable models ("systemic risk" models above a compute threshold),
adversarial testing and incident reporting requirements.

#### What the Act Gets Right

The risk-tiered approach reflects genuine insight. Not all AI systems carry
the same risks, and applying the same regulatory burden to a chatbot and to
an AI system making bail decisions would be both inefficient and politically
unsustainable. Focusing intense requirements on high-stakes domains--where
errors compound and are difficult to reverse--is defensible and sensible.

The transparency requirements for general-purpose models are a concrete response
to a real problem: the opacity of large models makes it difficult to assess
their risks, audit their training data, or identify failure modes before
deployment. Requiring documentation does not solve the opacity problem, but
it creates accountability anchors and enables external scrutiny.

The Act's prohibition of social scoring is philosophically significant: it
is a statement that some applications of AI are incompatible with a certain
conception of the person and political community, regardless of their
technical effectiveness. This is the kind of value-grounded limit that the
philosophical alignment discussion (see philosophy/alignment README) suggests
is necessary--a line drawn not on the basis of risk calculation but on
the basis of what kind of society Europeans have decided they want to live in.

#### What the Act Does Not Resolve

Several significant problems remain outside or inadequately addressed by
the Act's framework.

*The enforcement problem.* The Act creates obligations and establishes
national market surveillance authorities and an EU AI Office as oversight
bodies. But the gap between obligation and enforcement is substantial.
Conformity assessments for high-risk systems are primarily self-assessments
by developers; independent third-party auditing is required only in narrow
cases. The capacity of national authorities to audit complex AI systems is
not established. In pharmaceuticals, regulatory agencies have the technical
capacity to assess drug safety; no equivalent capacity for AI assessment
currently exists at the required scale.

*The foundation model problem.* The GPAI provisions were added late and
reflect the political difficulty of regulating the most capable systems.
The compute threshold approach--systems trained above a certain FLOP count
face additional obligations--is a rough proxy for capability and risk.
It creates obvious incentives to game the threshold. It also embeds an
assumption that compute is the right measure of risk, which may not remain
true as architectures evolve.

*The extraterritorial limit.* The Act applies to AI systems deployed in
the EU market, regardless of where they are developed. This extends its
reach significantly--any system serving EU users is covered. But it
cannot govern the development of AI systems that are never deployed in
the EU, and it cannot prevent capabilities developed elsewhere from being
used in ways that affect EU citizens indirectly. The most consequential
AI development is happening in the US, China, and a handful of other
jurisdictions. The EU can shape its own market; it cannot shape the
global trajectory.

*The security carve-out.* National security applications are largely
exempt from the Act's requirements. This is a significant gap: AI systems
used in military and intelligence contexts may carry the highest risks
of all, and they face the least scrutiny.


### Part II: The United States--Executive Orders, Voluntary Commitments,
and Sectoral Regulation

#### A Different Approach

The United States has not produced comprehensive AI legislation comparable
to the EU AI Act, and may not do so in the near term. The US approach has
instead been executive-led, voluntary-commitment-based, and increasingly
sectoral--different agencies applying existing regulatory frameworks to
AI in their domains, combined with White House-level coordination efforts.

The October 2023 Executive Order on the Safe, Secure, and Trustworthy
Development and Use of Artificial Intelligence was the most significant
federal action to date. It directed agencies to develop guidelines for
AI use in their domains, established reporting requirements for developers
of powerful AI systems (invoking the Defense Production Act to require
reporting of training runs above certain compute thresholds), and created
coordination mechanisms across the federal government. It also directed
the National Institute of Standards and Technology to develop AI safety
standards and established an AI Safety Institute within NIST.

The voluntary commitments secured from major AI developers--including
commitments to pre-deployment safety testing, information sharing about
risks, and watermarking of AI-generated content--reflect the political
difficulty of legislating in this area. They are not enforceable in the
way that legal obligations are. Their value depends on the continued
willingness of developers to honour them, which depends in turn on
competitive dynamics and political pressure.

#### The Sectoral Approach

Several US agencies have moved to apply existing regulatory frameworks
to AI in their domains:

The Food and Drug Administration has been developing frameworks for AI
in medical devices and clinical decision support, building on its existing
software-as-medical-device framework. AI diagnostic tools and treatment
recommendation systems already face regulatory scrutiny under this framework.

The Federal Trade Commission has asserted jurisdiction over AI systems
that engage in unfair or deceptive practices, applying its consumer
protection mandate to AI-generated misinformation, discriminatory systems,
and deceptive design.

The Equal Employment Opportunity Commission has issued guidance on the
application of employment discrimination law to AI-assisted hiring,
clarifying that employers cannot evade anti-discrimination obligations by
delegating decisions to algorithmic systems.

The Consumer Financial Protection Bureau has moved to clarify that
fair lending laws apply to algorithmic credit decisions.

This sectoral approach has the advantage of building on established
institutional expertise and legal frameworks with enforcement teeth.
It has the disadvantage of fragmentation: an AI system used across
multiple regulated domains may face inconsistent requirements from
multiple agencies, and entirely new applications may fall through gaps
between existing sectoral frameworks.

#### The Political Economy Problem

The US approach to AI governance is shaped by a political economy that
is difficult to ignore. The companies most capable of shaping AI
governance are the same companies whose competitive positions are most
affected by it. The revolving door between major AI laboratories and
government positions is well-documented. Research funding for AI safety
and governance from private foundations and companies creates dependencies
that may not be consistent with genuinely independent oversight.

This is not unique to AI. The pharmaceutical industry shapes drug regulation;
the financial industry shapes financial regulation. But the pace of AI
development and the concentration of relevant technical expertise in a
small number of private organisations make the capture problem particularly
acute. Independent technical assessment of AI systems requires expertise
that is currently concentrated in precisely the organisations being assessed.


### Part III: The International Process--Bletchley and Its Successors

#### The Bletchley Declaration

In November 2023, representatives of twenty-eight countries gathered at
Bletchley Park--the site of Turing's wartime codebreaking, chosen with
deliberate symbolic weight--and signed a declaration on AI safety.
The Bletchley Declaration was the first multilateral agreement specifically
addressing risks from frontier AI systems.

Its content was modest: a shared acknowledgement that certain AI capabilities
could pose serious risks, a commitment to information sharing about those risks,
and an agreement to establish a process for further international cooperation.
It did not create binding obligations, enforcement mechanisms, or governance
institutions. What it did was establish that the major powers--including
the US, the EU, China, and others--agreed that frontier AI safety was a
legitimate subject for international coordination.

China's participation was significant. The AI safety discourse has often
been framed in terms that implicitly exclude Chinese development as ungovernable
from outside. Bletchley demonstrated that Chinese officials were willing
to engage in a multilateral process on these questions, even while the
underlying competitive dynamics between the US and China in AI development
remain intense.

#### Subsequent Processes

The Bletchley process spawned several successor initiatives. The Seoul AI
Safety Summit (May 2024) produced the Seoul Statement, which advanced
commitments on safety testing and information sharing among frontier model
developers. The Paris AI Action Summit (February 2025) broadened the frame
to include AI for development, democratic governance of AI, and the interests
of the Global South--a significant expansion from Bletchley's narrower
frontier safety focus.

The UN has been developing its own AI governance frameworks through the
High-Level Advisory Body on Artificial Intelligence, whose 2024 report
recommended a global AI governance framework with representation from
all member states and particular attention to the interests of developing
nations.

These processes share a common structure: they produce declarations, statements,
and recommendations rather than binding agreements. The gap between
international consensus and enforceable obligation is wide and has not
been bridged. But the processes are doing something: they are establishing
shared vocabulary, building relationships among policymakers, and creating
norms that--while not legally binding--shape what is publicly defensible
and what is not.

#### The Arms Control Analogy and Its Limits

Hinton, Russell, and others have proposed arms control treaties as a model
for AI governance--international agreements with verification mechanisms,
comparable to the Nuclear Non-Proliferation Treaty or the Chemical Weapons
Convention.

The analogy is instructive and has limits. Arms control works where there is
a physically identifiable thing to control--a nuclear warhead, a chemical
agent--and where the number of actors capable of producing it is small enough
to make verification tractable. AI presents different problems. The relevant
"thing"--a large language model, a capable AI system--is software running
on hardware that is widely distributed and rapidly evolving. Verification
is difficult: how would an inspector confirm that a particular model has not
been trained above a given capability threshold? Compute governance--
controlling access to the chips used to train frontier models--is the
most tractable version of the arms control approach, and it is being pursued
through export controls on advanced semiconductors. But compute controls
are a blunt instrument and their long-term effectiveness as AI hardware
evolves is uncertain.

The more fundamental limit is that nuclear weapons have no peaceful applications
that are difficult to separate from weapons applications. AI does. Any
governance framework that restricted AI capability development enough to
meaningfully slow progress toward dangerous systems would also restrict
medical AI, climate modelling, scientific discovery, and the many other
applications that provide the political and economic motivation for AI
investment. The dual-use character of AI makes arms control models much
harder to apply than they were for nuclear technology.


### Part IV: Compute Governance

#### The Hardware Chokepoint

A distinctive feature of frontier AI development is its extreme hardware
dependence. Training the most capable AI systems requires vast quantities
of the most advanced semiconductors--specifically the GPUs and specialised
AI accelerators produced by a small number of companies, dominated by NVIDIA,
with AMD and Intel as secondary players. The fabrication of these chips
is itself concentrated: the most advanced chips are manufactured almost
exclusively by TSMC in Taiwan, with Samsung as a secondary source.

This concentration creates a governance chokepoint that does not exist for
software in general. Controlling who has access to advanced AI chips is
technically feasible in a way that controlling who can run AI software is not.
The Biden administration's October 2022 and October 2023 export controls on
advanced semiconductors to China were the most significant implementation of
this approach: restricting China's access to the chips needed to train
frontier models, and restricting the export of chip manufacturing equipment
that would allow China to produce them domestically.

The strategic logic is clear: if frontier AI capability depends on advanced
chips, and if advanced chips can be controlled at the chokepoint of fabrication,
then compute governance offers a lever on the pace and distribution of frontier
AI development that software governance does not.

#### The Limits of Compute Governance

Several limitations qualify this logic. The export controls have already
prompted Chinese investment in domestic semiconductor capability--SMIC and
Huawei's HiSilicon have made progress on advanced chip production, though
they remain behind the frontier. Controls that slow but do not prevent
Chinese frontier AI development may achieve less than intended while
accelerating the very investment they are designed to discourage.

The controls also affect legitimate research and commercial applications
in China and among US allies. Allies' compliance with US export controls
has been imperfect: chips controlled for Chinese end-users have reached
Chinese companies through intermediaries in third countries.

More fundamentally, compute governance addresses only one input to frontier
AI development. Algorithms, data, and software are also crucial, and are
much harder to control. The efficiency gains from algorithmic improvements--
achieving the same capability with less compute--mean that compute thresholds
may become less predictive of capability over time. A governance framework
that controls chips while algorithms continue to improve is governing a
moving target.

Phuong et al. (2024) and others working on compute governance have argued
for a layered approach: chip controls combined with know-your-customer
requirements on compute providers, model registries for frontier AI systems,
and international coordination on compute thresholds. Each layer has
implementation challenges, but the layered approach addresses the limitations
of any single lever.


### Part V: What Governance Cannot Do Alone

#### The Technical Dependency

Effective AI governance depends on technical capabilities that do not yet
fully exist: the ability to evaluate AI systems for dangerous capabilities
before deployment, to audit AI systems for compliance with safety requirements,
to detect AI-generated content reliably, and to verify that AI systems behave
as documented. Without these technical tools, governance frameworks are
aspirational rather than effective.

This is not a counsel of despair. Drug regulation works partly because
clinical trials are technically possible--we can test whether a drug is
effective and what its side effects are. Aviation safety works because
flight recorders and accident investigation create legible data about
what went wrong. AI governance will be more effective when analogous
technical infrastructure exists: evaluation methods that reliably assess
capabilities and risks, interpretability tools that make it possible to
audit what systems have learned, incident reporting systems that create
legible data about AI failures.

The AI Safety Institutes established in the UK, the US, and several other
countries are attempting to build this technical infrastructure. Their
work--developing evaluation methods, red-teaming frontier models,
establishing standards for safety testing--is less visible than
legislation but arguably more foundational. Governance frameworks without
the technical capacity to implement them are frameworks in name only.

#### The Speed Problem

The most fundamental challenge for AI governance is the mismatch between
the speed of AI development and the speed of institutional response.
Legislative processes take years. International negotiation takes years.
Judicial interpretation of new technologies in existing legal frameworks
takes years. The AI Act took four years from initial proposal to finalisation,
during which time the technology it was designed to govern transformed
significantly--the emergence of large language models as the dominant
paradigm required substantial amendments to a framework designed for a
different landscape.

This is not a solvable problem in any clean sense. Institutions move at
the speed they move for reasons that are structural, not incidental.
Democratic deliberation takes time; regulatory processes have procedural
requirements for good reasons; international negotiations require building
consensus across diverse interests.

Several adaptations are available. Principles-based regulation--which
sets outcome requirements rather than specifying methods--is more
durable than prescriptive rules as technology evolves. Regulatory sandboxes
allow governance frameworks to be tested and refined before full deployment.
Sunset clauses and mandatory review requirements build in adaptation
mechanisms. Delegated authority to technical bodies--analogous to the
way financial regulators set capital requirements within legislative
frameworks--allows faster technical adaptation without requiring
full legislative processes.

None of these fully close the gap. The honest assessment is that AI
governance will always be playing catch-up with a technology that moves
faster than institutions can follow. The question is not how to eliminate
this gap but how to keep it small enough that course correction remains
possible before the most consequential capabilities arrive.

#### The Democratic Deficit

A thread running through the governance debate--connecting the
institutional critique of Gebru, the philosophical analysis of the
alignment problem, and the democratic dimension of the nonwestern perspectives
-- is the question of who is actually making the decisions about AI development
and governance, and on whose behalf.

Current AI governance is predominantly shaped by a small number of actors:
the major AI laboratories, a handful of government agencies in wealthy
nations, a network of academics and think tanks substantially funded by
the same laboratories, and the international processes that these actors
have convened. The communities most affected by AI deployment--workers
facing automation, communities subject to facial recognition surveillance,
individuals whose data trains AI systems without their consent, populations
in the Global South who have the least voice in governance processes--
have the least influence over those processes.

This is not unique to AI. But it is a genuine problem that technical
governance frameworks do not automatically address. A technically sound
governance framework that lacks democratic legitimacy will face resistance
and may not produce the outcomes it promises. The Paris AI Action Summit's
emphasis on the Global South and on inclusive governance reflects a
recognition of this problem, though recognition is not the same as solution.


### Part VI: Synthesis--What Adequate Governance Would Require

Drawing the threads together, adequate AI governance would require at minimum:

*Technical infrastructure.* Evaluation methods that reliably assess AI
capabilities and risks. Interpretability tools that enable auditing.
Incident reporting systems that create legible data about failures.
None of these are fully available now. Building them is as important
as building regulatory frameworks, because frameworks without technical
implementation capacity are empty.

*Institutional capacity.* Regulatory bodies with genuine technical expertise,
adequate resourcing, and independence from the industries they oversee.
The FDA model--a technically capable agency with genuine authority--is
the relevant benchmark. No current AI regulatory body fully meets it.

*International coordination.* Not necessarily binding treaties on the arms
control model, which faces the dual-use problem. But shared standards for
safety testing, mutual recognition of conformity assessments, information
sharing about risks and incidents, and coordination on compute governance.
The Bletchley process is a beginning. It is not adequate to the scale
of the problem.

*Democratic legitimacy.* Governance processes that include the communities
affected by AI deployment, not just the communities producing it. This is
the hardest requirement to operationalise, but it is also the one that
determines whether governance frameworks are sustainable over time.

*Speed matching.* Institutional forms--sandboxes, principles-based
frameworks, delegated technical authority--that can adapt to a technology
moving faster than traditional legislative timescales allow.

The governance frameworks that exist are, taken together, more substantial
than they were five years ago and less adequate than the pace of AI
development requires. They are being built in real time, by institutions
with imperfect information, under competitive pressures that distort
incentives, without the catastrophic clarity that has historically
motivated adequate governance of transformative technologies.

Whether they will be adequate--whether course correction will remain
possible when it is needed--is not knowable in advance. What is knowable
is that the gap between capability and governance is a real risk, that
it is being taken seriously by some of the relevant institutions, and that
the technical, political, and philosophical work of closing it deserves
the same quality of attention as the work of building the capabilities
themselves.


### References and Further Reading

*Primary Policy Documents*:

- European Parliament and Council. (2024). *Regulation (EU) 2024/1689 on
  Artificial Intelligence (AI Act)*. Official Journal of the European Union.

- The White House. (2023). Executive Order on the Safe, Secure, and Trustworthy
  Development and Use of Artificial Intelligence. *Federal Register*, 88(210).

- Bletchley Declaration. (2023). *The Bletchley Declaration by Countries
  Attending the AI Safety Summit*. UK Government.

- High-Level Advisory Body on AI. (2024). *Governing AI for Humanity: Final Report*.
  United Nations.


*Academic and Policy Analysis*:

- Dafoe, A. (2018). AI governance: A research agenda. *Future of Humanity
  Institute, University of Oxford*.

- Cihon, P. (2019). Standards for AI governance: International standards
  to enable global coordination in AI research and development.
  *Future of Humanity Institute, University of Oxford*.

- Hadfield, G. K., & Clark, J. (2023). Regulatory markets: The future of
  AI governance. *arXiv preprint arXiv:2304.04914*.

- Krakovna, V., Martic, M., & Leike, J. (2023). Safety evaluations for
  frontier AI: A survey. *DeepMind Technical Report*.

- Ho, L., Barnhart, J., Trager, R., Bengio, Y., Brundage, M., Clark, J.,
  Hadfield, G., Ngo, R., Pilz, L., & Whittlestone, J. (2023). International
  institutions for advanced AI. *arXiv preprint arXiv:2307.04699*.


*Compute Governance*:

- Sastry, G., Heim, L., Belfield, H., Anderljung, M., Brundage, M.,
  Hazell, J., Ho, L., Leike, J., Ngo, R., Pilz, L., Rao, S.,
  Schneider, T., Sheridan, J., Trager, R., Wasil, A., Whittlestone, J.,
  & Clark, J. (2024). Computing power and the governance of artificial
  intelligence. *arXiv preprint arXiv:2402.08797*.

- Allen, G. C., & Chan, T. (2017). *Artificial Intelligence and National
  Security*. Belfer Center for Science and International Affairs.


*Historical Analogies and Governance Theory*:

- Collingridge, D. (1980). *The Social Control of Technology*. Frances Pinter.
  *(The Collingridge dilemma: technologies are easiest to govern before their
  impacts are clear, and hardest to govern after--relevant to the speed problem)*

- Jasanoff, S. (2016). *The Ethics of Invention: Technology and the Human Future*.
  W. W. Norton. *(Comparative analysis of technology governance across cultures)*

- Russell, S. (2019). *Human Compatible*. Viking.
  *(See also cautionary/russell README; Russell's governance proposals)*

- Bengio, Y., Hinton, G., et al. (2023). Managing AI risks in an era of
  rapid progress. *arXiv preprint arXiv:2310.17688*.
  *(The joint statement from leading AI researchers on governance priorities)*
