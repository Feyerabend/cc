
## Autonomous Vehicles: Where the Abstractions Land

### Introduction: The Richest Case Study

Most AI debates take place at a comfortable distance from consequences.
The alignment problem is discussed in terms of hypothetical superintelligences
and paperclip maximisers. The governance problem is discussed in terms of
regulatory frameworks that have not yet been tested against serious capability.
The embodied cognition argument is discussed in terms of what robots might
eventually do. The trolley problem is discussed as a philosophical thought
experiment.

Autonomous vehicles collapse that distance. They are the most widely deployed
embodied AI in the world, operating in uncontrolled public environments,
making decisions in real time that affect people who never consented to be
participants in an AI experiment. When an autonomous vehicle misclassifies
a pedestrian, the consequence is not a degraded benchmark score--it is
a person's death. When a company decides whose safety its vehicle will
prioritise in an unavoidable collision, that is an alignment decision encoded
in software, distributed to millions of cars, affecting people who have
no knowledge of and no voice in the decision. When regulators try to write
rules for systems that learn and change, the governance problem is not
theoretical--it is a question with a specific deadline, a specific
jurisdiction, and specific lives depending on the answer.

Autonomous vehicles are, for this reason, the best available case study for
what the debates in this collection actually look like when they meet physical
reality. Every major thread connects:
- The embodied cognition argument, for and against
- The scaling versus caution dispute, as product strategy
- Alignment in practice, including its failure modes
- AI governance under genuine pressure
- Non-Western approaches to deployment and regulation
- Legal and moral liability in novel configurations

This piece traces those connections through the specific history and present
state of autonomous vehicle development.

*See the embodied README for the broader context of embodied AI.
See appraisal/governance for the governance framework context.
See appraisal/practice for the alignment methods being applied.*


### Part I: How Autonomous Vehicles Work

#### The Technical Stack

An autonomous vehicle is, at its core, a system that must solve three
sequential problems in real time: perceiving the environment, predicting
what will happen, and deciding what to do. Each of these problems is
hard. Their combination, under the time pressure of highway driving,
is what has made autonomous vehicles one of the most challenging AI
deployments ever attempted.

*Perception* is the problem of constructing a reliable model of the
vehicle's immediate environment from sensor data. Modern AVs use some
combination of cameras, radar, and lidar. Cameras provide rich visual
information but are affected by lighting conditions and cannot directly
measure distance. Radar is robust in poor weather and directly measures
velocity but has low spatial resolution. Lidar--laser-based ranging--
provides precise three-dimensional maps of the environment but is expensive,
bulky, and degraded by heavy precipitation.

The choice of sensor suite reflects a fundamental design philosophy.
Waymo, Cruise, and most traditional AV developers use lidar as a primary
sensor, arguing that its depth information is essential for reliable
perception. Tesla has operated without lidar since 2019, arguing that
cameras alone--with sufficient neural network sophistication--are
adequate, and that the human visual system navigates successfully with
cameras alone (eyes). This disagreement is not merely technical. It
reflects a deeper dispute about whether AV safety requires sensor
redundancy and explicit depth information, or whether end-to-end
learning from visual data can acquire sufficient implicit understanding
of the three-dimensional world.

*Prediction* is the problem of anticipating what other agents in the
environment--pedestrians, cyclists, other vehicles, animals--will
do. This is not a physics problem with deterministic solutions. It is
a problem about intent, habit, and the subtle social signalling of
street behaviour. A pedestrian at a crossing who makes eye contact with
a driver is communicating something that a camera can detect but that
a system must be trained to interpret correctly. A cyclist's hand signal,
a delivery driver's hazard lights, a child chasing a ball--all of
these carry information that human drivers process with accumulated
social knowledge and that AV systems must learn from data.

*Planning and control* is the problem of deciding what to do given
the perception and prediction outputs, and then executing that decision
through smooth, safe vehicle control. This includes both high-level
decisions (which route, which lane) and low-level control (steering,
braking, acceleration) coordinated in real time.

#### Two Philosophies

The technical debate between Waymo and Tesla is the most visible
instantiation of the broader scaling versus caution dispute (see
appraisal/scaling README), applied to a domain where the costs of
error are measured in human lives.

*Waymo's approach* is modular, heavily engineered, and conservative.
Lidar plus cameras plus radar provides sensor redundancy. High-definition
maps of operating areas encode detailed prior knowledge of road geometry,
traffic patterns, and infrastructure. The perception, prediction, and
planning modules are relatively independent, which makes individual
components interpretable and testable. Waymo has tested extensively
in simulation--billions of simulated miles--before deploying on
public roads, and has expanded its operational design domain slowly
and deliberately. It operates in Phoenix, San Francisco, and a small
number of other US cities.

*Tesla's approach* is end-to-end, data-hungry, and iterative. Cameras
only, trained on data from millions of deployed vehicles running in
"shadow mode"--continuously recording what the human driver does in
situations where the system would have acted differently, creating a
vast dataset of human driving decisions. The neural network learns
from this fleet data continuously. Tesla's Full Self-Driving system
improves through over-the-air software updates deployed to its entire
fleet simultaneously. It has been deployed, in various forms, to
millions of cars globally.

Tesla's approach embodies Sutton's bitter lesson (see appraisal/scaling
README) applied to driving: learning from data at scale will outperform
hand-engineered solutions. Waymo's approach reflects the cognitive
science critique: robust intelligence requires structured priors,
multiple sensing modalities, and interpretable components that can
be verified and corrected. The dispute has not been resolved by
the safety data, in part because the data is contested and the
operational conditions are not directly comparable.


### Part II: The Death of Elaine Herzberg

#### The First Fatality

On the evening of 18 March 2018, Elaine Herzberg was walking her bicycle
across a four-lane road in Tempe, Arizona, outside a marked crossing.
An Uber ATG autonomous test vehicle, operating in autonomous mode with
a human safety driver present, struck and killed her. She was 49 years
old. She was the first pedestrian killed by an autonomous vehicle.

The subsequent investigation by the National Transportation Safety Board
produced findings that illuminate almost every major theme in this collection.

The system detected Herzberg approximately six seconds before impact.
But the system's classification module cycled through multiple categories
as it processed the sensor data--first an unknown object, then a vehicle,
then a bicycle--without arriving at a stable classification in time to
initiate emergency braking. The system was not designed to brake for
unknown objects: a design decision that prioritised smooth driving over
conservative safety behaviour.

The human safety driver was watching Hulu on her phone. She was not
monitoring the road. Uber had disabled the vehicle's emergency braking
system to reduce what it called "erratic vehicle behaviour"--the system
braking for false positives. The choice to disable automatic braking
was a product decision that prioritised the appearance of smooth, capable
autonomous operation over the redundancy that safety required.

Uber ATG was subsequently sold to Aurora Innovation. The criminal case
against the safety driver was eventually resolved with a plea agreement.
No criminal charges were brought against Uber.

#### What the Case Reveals

The Herzberg case is a near-perfect instance of the specification gaming
problem (see appraisal/practice README): a system optimised for smooth,
confident driving--because that is what demonstrates capability and
builds commercial confidence--produced behaviour that was competent
by that measure and catastrophically unsafe by others.

The disabled emergency braking is also an instance of the corrigibility
dilemma from the philosophical alignment framework: the system had been
designed with a safety mechanism that was removed because it produced
behaviour inconsistent with the operational goal. The mechanism to
correct the system was deliberately bypassed in the interest of performance.

The human safety driver is an instance of automation complacency--
a well-documented phenomenon in which human operators in supervisory
roles over automated systems reduce their vigilance because the system
"usually works." Uber's operational practice did not adequately account
for this. The governance framework in Arizona at the time imposed no
specific requirements on human monitoring in AV test operations.

The case generated the most detailed public record of AV decision-making
available. It forced a reckoning with the gap between demonstrated test
performance and safety in edge cases. It contributed directly to NHTSA's
subsequent Standing General Order requiring incident reporting for AV
crashes. It was, in the grim tradition of aviation safety, a catastrophe
that made future catastrophes less likely.


### Part III: The Trolley Problem Moves Off Campus

#### Alignment Decisions in Software

The philosophical trolley problem asks: if you can divert a runaway trolley
to kill one person rather than five, should you? It has been a staple of
ethics courses for decades. For autonomous vehicles, it is not a thought
experiment. It is a software specification.

In 2016, Mercedes-Benz's manager of driver assistance systems stated publicly
that the company's AVs would be programmed to prioritise passenger safety
over pedestrian safety in unavoidable collision scenarios. The reasoning was
pragmatic: the company knew more about protecting its passengers than about
protecting pedestrians, and passengers were the ones who had chosen to be
in the car.

The statement provoked immediate controversy. It was largely walked back in
subsequent communication. But the underlying problem did not go away: AVs
must be programmed with some decision rule for unavoidable collision scenarios,
and any rule embodies a value judgement about whose safety takes priority.

The value judgements embedded in AV collision avoidance include:
- Passenger versus pedestrian safety weighting
- Child versus adult weighting (should AVs swerve to avoid children at
  higher cost to passengers?)
- Driver responsibility versus pedestrian responsibility for collisions
  at unmarked crossings
- How much risk to impose on other road users to reduce risk to passengers

These decisions are being made by engineers and product managers in
automobile and technology companies, encoded in software, and distributed
to millions of vehicles affecting millions of people who have no voice
in the decisions. This is the democratic deficit from the governance
analysis, applied with specific urgency: the people most affected by
alignment decisions have the least influence over them.

Awad et al.'s Moral Machine experiment (2018) surveyed global responses
to trolley-problem scenarios in autonomous vehicles and found significant
variation across cultures: preferences for sparing children versus adults,
pedestrians versus passengers, and the weighting of legal compliance
varied substantially across regions. The AV alignment problem is not
merely a problem of discovering the right answer--it is a problem
of whose values get to determine the answer, across a global technology
deployed in diverse cultural contexts.


### Part IV: The Scaling Versus Caution Dispute in Practice

#### Tesla's Strategy

Tesla's Full Self-Driving system is the most controversial deployment
decision in autonomous vehicles. The name "Full Self-Driving" implies a
capability the system does not have: it requires continuous driver attention
and is not autonomous in the SAE Level 4 sense. This naming decision--
which Tesla has defended and regulators have challenged--creates a specific
risk: drivers who interpret the name literally may reduce their attention
below what the system actually requires, reproducing the automation
complacency that contributed to Herzberg's death.

NHTSA has opened multiple investigations into Tesla Autopilot and FSD
crashes, several involving fatalities. Tesla's response has consistently
been that its systems require driver attention, that crashes occur when
drivers misuse the system, and that the overall safety statistics of
Tesla vehicles with Autopilot engaged compare favourably with human
driving statistics. The last claim is contested: the comparison requires
controlling for the fact that Autopilot is used disproportionately on
highways, which are significantly safer than urban roads regardless of
driver assistance.

The fleet learning approach does produce genuine capability improvements.
Tesla vehicles have, through over-the-air updates, improved performance
on a wide range of scenarios that earlier versions handled poorly.
The system is better than it was. Whether it is good enough, and whether
the deployment strategy--learning through deployment rather than
before it--is appropriate for a system operating at highway speeds,
is the substantive dispute.

#### Waymo's Strategy

Waymo's record is substantially different. As of 2024, Waymo One has
operated millions of fully driverless rider trips in Phoenix and San
Francisco. Its per-mile safety record compares favourably with human
driving. It has had incidents--including a collision in San Francisco
in 2024 that regulators investigated--but its overall record suggests
that the cautious, heavily tested approach can produce genuinely safe
autonomous operation in defined operational areas.

The limitation is deployment scale and geographic breadth. Waymo operates
in a small number of cities, in defined weather conditions, with HD maps
that must be created and maintained for each area. Expanding to new
cities is expensive and slow. The system that is safe in Phoenix may
encounter conditions in a new city that its training and maps do not
cover. Waymo's conservatism about expansion reflects honest acknowledgement
of this limitation.

#### Cruise: The Failure Mode

General Motors' Cruise provides a cautionary case about the fragility
of safety reputations in AV deployment. Cruise had operated successfully
in San Francisco for several years, accumulating a reasonable safety
record. In October 2023, a Cruise vehicle struck a pedestrian who had
already been hit by another car, and then--attempting to pull over
to the side of the road--dragged her approximately six metres before
stopping. The vehicle's sensors had not correctly registered that a
person was beneath it.

The incident led to the suspension of Cruise's California permits,
the resignation of several executives, a substantial reduction in the
company's operations, and investigations into whether Cruise had
provided regulators with complete information about the incident.
The latter finding--that Cruise may have withheld relevant video
evidence from regulators--reflects a governance failure as much as
a technical one. The institutional incentives for AV companies are
strongly against candid disclosure of incidents, which is precisely
why mandatory incident reporting and independent investigation matter.


### Part V: China--A Different Deployment Philosophy

#### Baidu Apollo and the Scale of Chinese Deployment

China's approach to autonomous vehicle deployment is as different from
the US approach as China's approach to AI governance generally (see
appraisal/governance and appraisal/philosophy/nonwestern READMEs).
Baidu's Apollo Go robotaxi service operates fully driverless--without
a human safety driver--in multiple Chinese cities including Wuhan,
Chongqing, and Beijing. It is the world's largest fully driverless
commercial robotaxi operation.

The deployment context differs from the US in several ways. Chinese cities
are mapping their road infrastructure for AV use as part of national
infrastructure investment. The regulatory framework for AV testing and
deployment has been developed in close coordination between companies
and government agencies, enabling faster expansion than the US regulatory
patchwork allows. Public tolerance for robotic vehicles in service roles
is higher in China, influenced in part by the cultural dispositions
toward technology discussed in the nonwestern README.

The speed of Chinese AV deployment--and the scale at which Baidu,
Pony.ai, WeRide, and others are operating--means that the learning
curve is being traversed faster in China than in the US or EU.
The feedback loop between deployment, incident, investigation, and
improvement is tighter. Whether this produces a better safety outcome
than the US approach of slower, more cautious deployment, or whether
it produces more incidents in exchange for faster capability development,
is an empirical question being answered in real time, on Chinese roads.

#### The Governance Comparison

The Chinese AV regulatory framework is more permissive at the frontier
of deployment--willing to allow fully driverless operation at scales
that US regulators have not yet permitted--while being more prescriptive
about data sharing and government access to operational data. AV companies
operating in China must share operational data with government agencies.
This creates a governance model that is simultaneously more enabling
(faster deployment) and more extractive (government access to private
company data) than the US model.

This reflects the broader Chinese AI governance philosophy: AI deployment
in the service of national capability development, with government
maintaining access and oversight not through independent regulation but
through data requirements built into operating licenses. Whether this
produces better or worse safety outcomes than the US approach is not yet
clear from available evidence. What is clear is that it is a coherent
and intentional governance philosophy, not an absence of governance.


### Part VI: Liability, Law, and Novel Questions

#### Who Is Responsible When an AV Kills?

The legal doctrine of liability was developed in a world where vehicles
had human drivers. Negligence claims required showing that a human
driver acted below the standard of care. Product liability claims required
showing that a manufacturer's product was defective. These doctrines
are strained but not broken by autonomous vehicles; the harder questions
are at the frontier.

When an AV operating in fully autonomous mode kills a pedestrian, who is
liable? The manufacturer, for a defective product? The software developer,
for a flawed algorithm? The company that deployed the system, for inadequate
testing? The passenger, for engaging the system? The pedestrian, for being
outside a crossing? US courts are developing doctrine in this area through
litigation arising from specific incidents, rather than through legislation.
This is the common law tradition working as it is supposed to: doctrine
developing through cases, each adding specificity to general principles.

The Herzberg case was resolved through a criminal plea agreement with the
safety driver, not through a civil determination of the deeper liability
questions. The significant civil case against Uber was settled out of court.
The legal doctrine for AV liability remains genuinely unsettled.

#### The Insurance Question

Insurance companies have been faster than regulators to confront the AV
liability question, because they have direct financial exposure to its
resolution. The question of whether AV incidents are product liability
claims (against manufacturers) or automobile liability claims (against
operators) determines which insurance product applies and who bears the
cost. Several jurisdictions are moving toward product liability frameworks
for Level 4 and Level 5 vehicles, which would shift liability from
individual users to manufacturers. This changes the incentive structure
for safety: manufacturers who bear liability have stronger incentives
to invest in safety than users who are indemnified.


### Part VII: What Autonomous Vehicles Reveal About the Broader Debate

#### The Embodied Cognition Thesis, Tested

The autonomous vehicle record provides the most extensive test of the
embodied cognition thesis available. AV systems are learning to navigate
complex physical environments through sensorimotor interaction--exactly
what the embodied cognition framework suggests should produce robust
intelligence. The results are instructive.

In defined operational areas, with good weather, on mapped roads, the
best AV systems are demonstrably safe by most measures. They do not
get tired, distracted, or drunk. They have faster reaction times than
humans. They do not make the errors of inattention that cause many
human accidents.

In edge cases--novel road configurations, unusual objects, scenarios
not represented in the training data--they fail in ways that human
drivers do not. The Herzberg case was an edge case: a person in dark
clothing, pushing a bicycle, crossing a wide road outside a crossing,
at night. Human drivers have navigated variations of this scenario
millions of times; the AV system had not acquired the robust generalisation
from training data that the embodied cognition thesis might predict.

The honest reading of the AV evidence is that embodied learning in
specific domains produces robust capability within the training
distribution and brittle performance outside it--consistent with
Marcus's brittleness critique (see appraisal/critique README) even
for embodied systems.

#### The Scaling Versus Caution Dispute, Concretely

The Tesla/Waymo dispute is the clearest available instance of the
scaling versus caution dispute in a domain where the costs are
measurable. Waymo has demonstrated that the cautious approach produces
safe operation in defined domains. Tesla has demonstrated that the
scaling approach produces rapid improvement across a wide range of
scenarios. Neither approach has produced the general, robust autonomy
that both companies' marketing materials have implied was imminent
since at least 2016.

The recurring pattern--impressive performance on most scenarios, failure
on edge cases, optimistic timelines repeatedly revised--mirrors the
broader pattern in AI capability development: scaling has worked better
than expected in aggregate, produced less robust generalisation than
hoped, and generated claims about future capability that outrun the
evidence. Autonomous vehicles were, for much of the 2010s, considered
the imminent proof of concept for strong AI. They are now a more
sobering case study in what capable, deployed, embodied AI systems
can and cannot do.

#### The Governance Lessons

Autonomous vehicles have produced more developed sector-specific AI
governance than any other application--not because the policy community
is more sophisticated about AVs than about AI generally, but because
the incidents are physically legible, the causation is investigable,
and the stakes are obvious. The National Transportation Safety Board's
investigation of the Herzberg case is a model of what AI incident
investigation could look like: technically rigorous, publicly accessible,
and drawing conclusions that shaped subsequent regulation.

The AV governance experience suggests several lessons for AI governance
more broadly. Mandatory incident reporting works: it creates the data
that makes governance evidence-based rather than anticipatory.
Independent investigation works: NTSB's independence from NHTSA and
from the industry it investigates is what makes its reports credible.
The sectoral approach works better than general frameworks for domains
where the risk profile is specific and technical assessment requires
domain expertise.

It also reveals the limits of governance: the naming of "Full Self-Driving"
as a product feature, despite regulatory concern, illustrates that
companies have significant ability to shape public expectations in ways
that regulators cannot easily prevent without explicit legislative
authority. The gap between capability and marketing claim is a governance
problem that the AV sector has not resolved and that applies with
equal or greater force to AI systems generally.


### Part VIII: Synthesis

Autonomous vehicles are not the most important application of AI.
Healthcare AI, climate modelling, scientific discovery, and the broad
productivity applications of language models likely have larger aggregate
impacts. But autonomous vehicles are the most important case study
for what AI looks like when it is physically deployed in uncontrolled
environments at scale, when its failures are visible and legally
consequential, and when the abstract debates of AI research have to
produce answers that work on wet roads at night.

What the case study shows is that the abstractions are not wrong
but incomplete. The embodied cognition thesis captures something real:
embodied systems do develop capabilities that purely language-based
systems do not. It does not fully predict the brittleness at the edge
of the training distribution. The scaling thesis captures something
real: more data and more capable systems do produce better performance
across more scenarios. It does not fully predict the persistence of
edge case failures. The alignment framework captures something real:
the decisions encoded in AV systems reflect value choices that have
human consequences. It does not provide a procedure for making those
choices that commands democratic legitimacy.

The most important lesson of the AV case study may be the simplest:
the distance between a capability being impressive in average cases
and a capability being safe in all cases is much larger than it looks
from the outside, and much of the work of closing it is unglamorous,
slow, and institutionally demanding. The companies that have learned
this lesson most thoroughly--through incidents, investigations,
and the hard revision of optimistic timelines--are the ones whose
systems are most trustworthy. The ones that have not learned it remain
a source of risk that their marketing does not convey.

That pattern--impressive average performance, edge case brittleness,
optimistic external communication, slow institutional learning--is
not unique to autonomous vehicles. It is a description of where AI
development currently is, across most of its domains.


### References and Further Reading

*Incident Reports and Regulatory Documents*:

- National Transportation Safety Board. (2019). *Collision Between Vehicle
  Controlled by Developmental Automated Driving System and Pedestrian,
  Tempe, Arizona, March 18, 2018*. Highway Accident Report NTSB/HAR-19/03.
  *(The definitive public record of the Herzberg fatality)*

- NHTSA. (2022 onwards). Standing General Order 2021-01: Incident Reporting
  for Automated Driving Systems and Advanced Driver Assistance Systems.
  *National Highway Traffic Safety Administration*.

- California DMV. Autonomous Vehicle Collision Reports (ongoing).
  *California Department of Motor Vehicles*.


*Technical and Industry*:

- Waymo Team. (2020). Waymo's safety methodologies and safety readiness
  determinations. *Waymo Safety Report*.

- Bansal, M., Krizhevsky, A., & Ogale, A. (2019). ChauffeurNet: Learning
  to drive by imitating the best and synthesizing the worst. *Robotics:
  Science and Systems 2019*.

- Bojarski, M., Del Testa, D., Dworakowski, D., Firner, B., Flepp, B.,
  Goyal, P., Jackel, L. D., Monfort, M., Muller, U., Zhang, J.,
  Zhang, X., Zhao, J., & Zieba, K. (2016). End to end learning for
  self-driving cars. *arXiv preprint arXiv:1604.07316*. *(NVIDIA; influential
  early demonstration of end-to-end learning for driving)*


*Ethics and Alignment*:

- Awad, E., Dsouza, S., Kim, R., Schulz, J., Henrich, J., Shariff, A.,
  Bonnefon, J.-F., & Rahwan, I. (2018). The moral machine experiment.
  *Nature*, 563(7729), 59--64.
  *(Global survey of trolley-problem intuitions for AV scenarios;
  documents significant cross-cultural variation)*

- Bonnefon, J.-F., Shariff, A., & Rahwan, I. (2016). The social dilemma
  of autonomous vehicles. *Science*, 352(6293), 1573--1576.

- Lin, P. (2016). Why ethics matters for autonomous cars. In M. Maurer,
  J. C. Gerdes, B. Lenz, & H. Winner (Eds.), *Autonomous Driving*
  (pp. 69--85). Springer.


*Governance and Law*:

- Marchetti, N. (2023). Autonomous vehicle liability: A comparative
  analysis of US, EU, and Chinese frameworks. *Journal of Law and
  Emerging Technologies*, 4(1), 1--42.

- Schellekens, M. (2015). Self-driving cars and the chilling effect of
  liability law. *Computer Law and Security Review*, 31(4), 506--517.

- Anderson, J. M., Nidhi, K., Stanley, K. D., Sorensen, P., Samaras, C.,
  & Oluwatola, O. A. (2016). *Autonomous Vehicle Technology: A Guide
  for Policymakers*. RAND Corporation.


*China*:

- Lee, K.-F. (2018). *AI Superpowers*. Houghton Mifflin Harcourt.
  *(See also nonwestern and embodied READMEs)*

- Baidu Apollo. (2023). *Apollo Open Platform Technical Documentation*.
  *(Primary source for Chinese AV technical approach)*

- Triolo, P. (2020). China's push to lead in autonomous vehicles.
  *New America Foundation*.


*Connection to Broader AI Debates*:

- Brooks, R. A. (1991). Intelligence without representation.
  *Artificial Intelligence*, 47(1--3), 139--159.
  *(See also embodied README)*

- Marcus, G., & Davis, E. (2019). *Rebooting AI*. Pantheon.
  *(Brittleness critique; directly relevant to AV edge cases)*
