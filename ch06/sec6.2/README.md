
## Four Methodological Perspectives in Relation to Sustainable Computing

The purpose here is not really building things, but to *discuss* what
methodologies, philosophies, methods, and so on, can be used in
relation to a given task/project. In this case the given will be
about a certain idea on sustainability and computers described in
[SUSTAIN.md](./SUSTAIN.md).

This overview connects four complementary philosophies *Lean*,
*Frugal Engineering*, *Systems Thinking*, and *Design Science Research (DSR)*
to the sustainable distributed microcontroller-based computing
vision.


__Context: Sustainable Computing Vision__

The project proposes rethinking computing around:
* Distributed microcontroller-based architectures
* Task-specific processing nodes
* Minimal software stacks
* Energy-efficient operation
* Modular, resilient system design

The central challenge is not only technical feasibility but also:
* Energy proportionality
* Resource efficiency
* Architectural simplicity
* Long-term sustainability



### 1. Lean Philosophy

#### Core Focus

Maximize value while eliminating waste.

#### Relevance to Sustainable Computing

Lean frames inefficiency as *waste*, including:
* Idle energy consumption
* Overprovisioned hardware
* Unnecessary computation
* Software stack inflation
* Redundant features

#### Contribution to the Project

Lean encourages:
* Identifying what users actually need
* Removing non-value-adding functionality
* Reducing baseline energy usage
* Iterative prototype refinement
* Fast feedback via measurement

#### Example Application

Instead of designing a "full alternative computer,"
Lean might suggests:
* Start with minimal viable functionality
* Measure energy/performance
* Eliminate architectural waste
* Iterate toward efficiency



### 2. Frugal Engineering (Minimalism)

#### Core Focus

Deliver essential functionality with minimal resources.

#### Relevance to Sustainable Computing

Frugal Engineering directly supports:
* Low-power microcontroller architectures
* Minimal hardware complexity
* Lightweight software
* Cost and material reduction

It reframes performance goals:
* From *maximum capability* -> *adequate capability*

#### Contribution to the Project

Frugal principles guide:
* Selection of MCU-class devices[^mcu]
* Simplification of system components
* Minimal runtime/software layers
* Energy-aware design decisions

[^mcu]: MCU = Microcontroller Unit

#### Example Application

* Use microcontrollers instead of CPUs
* Replace monolithic OS with task-specific modules
* Reduce memory/storage demands
* Favor simplicity over feature density



### 3. Systems Thinking

#### Core Focus

Understand the system as an interconnected whole.

#### Relevance to Sustainable Computing

Sustainability is inherently systemic:
* Energy production & consumption
* Hardware lifecycle impacts
* Network overhead
* User behavior
* Maintenance & repairability

Local optimizations may produce *global inefficiencies*.

#### Contribution to the Project

Systems Thinking helps:
* Avoid shifting energy costs elsewhere
* Analyze trade-offs (compute vs communication)
* Identify feedback loops (load, latency, scaling)
* Consider lifecycle sustainability
* Reveal unintended consequences

#### Example Application

Evaluating distributed MCUs requires examining:
* Node energy savings vs network energy cost
* Reliability vs redundancy
* Performance vs modularity
* Longevity vs upgrade cycles



### 4. Design Science Research (DSR)

#### Core Focus

Create and rigorously evaluate artifacts.

#### Relevance to Sustainable Computing

The project is artifact-centered:
* New architecture
* Prototype platform
* Communication mechanisms
* Design principles

DSR provides the *research structure*.

#### Contribution to the Project

DSR formalises:
1. Problem definition (energy inefficiency, complexity)
2. Design objectives (efficiency, modularity, sustainability)
3. Artifact creation (distributed MCU system)
4. Demonstration (real workloads)
5. Evaluation (energy, latency, robustness)
6. Knowledge extraction (principles, patterns)

#### Example Application

Transforming ideas from *SUSTAIN.md* into:
* A validated prototype
* Measured sustainability claims
* Transferable design knowledge


### Complementary Roles of the Methodologies

| Philosophy         | Primary Role in Project                  |
|--------------------|------------------------------------------|
| Lean               | Eliminating waste & guiding iteration    |
| Frugal Engineering | Resource-minimal design principles       |
| Systems Thinking   | Holistic analysis & trade-off awareness  |
| DSR                | Research structure & artifact validation |



### Integrated View?

Together, these approaches create a coherent framework:

#### Lean

Ensures the system avoids:
* Feature bloat
* Energy waste
* Overengineering

#### Frugal Engineering

Shapes:
* Hardware selection
* Software minimalism
* Architectural simplicity

#### Systems Thinking

Provides:
* Holistic sustainability evaluation
* Lifecycle awareness
* Understanding of emergent effects


#### DSR

Enables:
* Systematic design process
* Prototype-based inquiry
* Rigorous evaluation
* Academic/research legitimacy


### Practical Synthesis?

A combined methodological stance might be:
1. *Systems Thinking* -> Frame the problem holistically
2. *Frugal Engineering* -> Define minimal, constraint-driven design
3. *Lean* -> Iteratively remove waste & refine
4. *DSR* -> Build, demonstrate, evaluate, and formalize knowledge

