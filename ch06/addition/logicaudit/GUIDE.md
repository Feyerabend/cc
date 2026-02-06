
## Deontic Action Logic: A Practical Guide

### For Software Engineers and Domain Experts

This is a *semantic discipline* for capturing what *must*, *must not*,
and *may* happen in systems where rules matter—emergency response,
healthcare protocols, regulatory compliance, mission-critical operations.

*Core idea*: Normativity = selecting which possible futures are acceptable.

*Not*: A theorem-proving system or moral philosophy framework.

*Yes*: A rigorous way to translate client requirements into verifiable system constraints.


### Three Perspectives

#### For Stakeholders (Intuitive)

Think of your system as having many possible futures. Some are acceptable, some forbidden.

When you say "emergency responders must never travel more than 30 minutes,"
you're *ruling out entire classes of futures* where that happens.

This formalism lets you:
- State which futures are forbidden
- State which must happen under conditions
- Declare priorities when rules conflict
- Verify your system respects boundaries

#### For Engineers (Semi-Formal)

We model normative constraints as a *partition over possible worlds*.

- Each "world" = complete trajectory or state of your system
- Admissible worlds = those satisfying all applicable norms
- Norms are *filters* that reject worlds, not inference rules
- Priority ordering resolves conflicts without logical explosion

Your job: translate domain rules into world-filtering predicates,
then verify implementation produces only admissible executions.

#### For Verification Specialists (Formal)

*Semantic structure*: $\langle W, A, V, \succ \rangle$ where:
- $W$ is a non-empty set of possible worlds
- $A \subseteq W$ is the admissible subset
- $V: W \times Prop \rightarrow \{\top, \bot\}$ is a valuation function
- $\succ$ is a strict partial order over norms

*Interpretation*: Deontic operators quantify over $A$, not $W$.
Conditional norms restrict the quantification domain. Priority ordering
determines $A$ when norms conflict. No axiomatic closure over logical consequence.


### Practical Workflow

#### Step 1: Define Your World Structure

*Question*: What does a "world" mean for your system?

*Options*:
- *Static state*: snapshot (database state, configuration)
- *Trajectory*: complete execution trace (event log, temporal sequence)
- *Hybrid*: state + next-action possibilities

*Example* (emergency dispatch):
```
A world w is a complete 24-hour execution trace containing:
- All emergency events
- All responder assignments
- All travel times
- All status transitions
```

#### Step 2: Define Your Propositions

*Question*: What properties can we check at/across worlds?

*Examples*:
```
response_time(incident_id) ≤ 30 minutes
assigned_responders(incident_id) ≥ 2
vehicle_capacity(vehicle_id) ≥ passenger_count
responder_certified(responder_id, incident_type)
```

These become your atomic propositions $\varphi$, $\psi$, etc.

#### Step 3: Encode Your Norms

For each domain rule, choose the appropriate operator:

*Use `O φ` when*: Every acceptable outcome must have $\varphi$
```
O(response_time ≤ 30)
"We must always respond within 30 minutes"
```

*Use `F φ` when*: No acceptable outcome has $\varphi$
```
F(uncertified_assignment)
"We must never assign uncertified responders"
```

*Use `P φ` when*: At least one acceptable outcome has $\varphi$ (rare in practice)
```
P(overtime_authorized)
"Overtime is permitted (but not required)"
```

*Use `R φ` when*: $\varphi$ is a constitutive invariant, not a derived property
```
R(battery_level > 0)
"Devices must always have power (non-negotiable)"
```

*Use `O(φ | ψ)` when*: $\varphi$ is required only when $\psi$ holds
```
O(hazmat_team_present | chemical_incident)
"Hazmat team required for chemical incidents"
```

#### Step 4: Specify Priorities

When norms conflict, priority determines resolution:

```
CRITICAL: responder_safe
HIGH: fast_response, proper_certification
MEDIUM: adequate_crew
LOW: no_overload
```

A world is admissible iff it satisfies all maximal (highest-priority unviolated) norms.

#### Step 5: Verification

Choose your verification approach:

*Formal model checking*:
- Alloy: bounded instance-finding
- TLA+: temporal property verification
- SAT/SMT solvers: constraint satisfaction

*Runtime monitoring*:
- Log-based verification
- Enforcement hooks
- Violation detection

*Testing*:
- Generate test cases from admissible/inadmissible worlds
- Coverage over norm combinations
- Conflict scenario testing


### Complete Example: Emergency Dispatch

#### Step 1: Define Worlds

A world $w$ is a complete 24-hour execution trace:
- Set of incidents: $I = \{i_1, i_2, \ldots\}$
- Set of responders: $R = \{r_1, r_2, \ldots\}$
- Assignment function: $assign: I \rightarrow 2^R$
- Timing function: $response\_time: I \rightarrow \mathbb{N}$ (minutes)
- Certification: $certified: R \times IncidentType \rightarrow Bool$
- Availability: $available: R \times Time \rightarrow Bool$

#### Step 2: Define Propositions

```
fast_response(i) ≜ response_time(i) ≤ 30
proper_cert(i) ≜ ∀r ∈ assign(i): certified(r, type(i))
adequate_crew(i) ≜ |assign(i)| ≥ min_crew(type(i))
no_overload(r) ≜ |{i | r ∈ assign(i) ∧ overlaps(i)}| ≤ 1
responder_safe(r) ≜ ¬injured(r) ∧ equipment_ok(r)
```

#### Step 3: Encode Norms

From requirements document:

1. "Responders must never be put in unsafe conditions"
 → `R(∀r ∈ R: responder_safe(r))` — Priority: CRITICAL

2. "All responses must arrive within 30 minutes"
 → `O(∀i ∈ I: fast_response(i))` — Priority: HIGH

3. "Only certified personnel may respond to specialised incidents"
 → `O(∀i ∈ I: proper_cert(i))` — Priority: HIGH

4. "Each incident requires minimum crew size"
 → `O(∀i ∈ I: adequate_crew(i))` — Priority: MEDIUM

5. "Responders should not be double-booked"
 → `O(∀r ∈ R: no_overload(r))` — Priority: LOW

6. "In mass casualty events, double-booking is permitted"
 → `mass\_casualty \succ no\_overload`

#### Step 4: Admissibility Computation

```
A = {w ∈ W | w satisfies all CRITICAL norms}
∩ {w ∈ W | w satisfies all HIGH norms or CRITICAL requires violation}
∩ {w ∈ W | w satisfies all MEDIUM norms or higher priority requires violation}
∩ {w ∈ W | w satisfies all LOW norms or higher priority requires violation}
```

#### Step 5: Conflict Scenarios

*Scenario 1*: Rush hour, all units busy, new critical incident

- Conflict: `fast_response` vs `no_overload`
- Resolution: `fast_response` has higher priority → double-booking permitted

*Scenario 2*: Only uncertified responders available for hazmat

- Conflict: `fast_response` vs `proper_cert`
- Resolution: Both HIGH priority → $A = \emptyset$ → escalate to external resources

*Scenario 3*: Budget cuts reduce crew below minimum

- Conflict: `adequate_crew` vs resource availability
- Resolution: Systemic violation → operational failure, must fix at planning level

#### Step 6: Implementation

```python
class DispatchSystem:
def assign_responders(self, incident):
candidates = self.available_responders(incident)

# CRITICAL norms (non-negotiable)
safe_candidates = [r for r in candidates if self.is_safe(r, incident)]

# HIGH norms (certification)
certified_candidates = [r for r in safe_candidates 
if self.is_certified(r, incident.type)]

if not certified_candidates:
raise EscalationRequired("No certified responders available")

# MEDIUM norms (crew size)
assignment = self.select_crew(certified_candidates, incident.min_crew)

# LOW norms (no overload), relax if necessary
if not self.check_overload(assignment):
if incident.priority == 'CRITICAL':
log_warning("Double-booking permitted due to critical incident")
else:
assignment = self.rebalance_or_wait(assignment, incident)

return assignment
```

#### Step 7: Verification

*Test normal operations*:
```python
def test_normal_dispatch():
system = DispatchSystem(norms, priorities)
incident = Incident(type='medical', priority='routine')
assignment = system.assign_responders(incident)

assert all(r.is_safe for r in assignment)
assert all(r.certified_for(incident.type) for r in assignment)
assert len(assignment) >= incident.min_crew
assert no_double_booking(assignment)
```

*Test conflict scenario*:
```python
def test_critical_during_rush_hour():
system = DispatchSystem(norms, priorities)
system.assign_all_to_routine_incidents()

critical_incident = Incident(type='cardiac_arrest', priority='CRITICAL')
assignment = system.assign_responders(critical_incident)

# Should permit double-booking
assert len(assignment) > 0
assert all(r.is_safe for r in assignment)
assert all(r.certified_for(critical_incident.type) for r in assignment)
# no_overload may be violated - acceptable given priority
```


### Integration Strategies

#### With Temporal Logic (TLA+, LTL)

```
TLA+ spec defines: all possible behaviours
Our norms define: which behaviours are admissible
Model checker verifies: implementation ⊆ admissible behaviours
```

LTL formulas can be embedded as propositions in deontic operators.
Norms constrain which temporal behaviours are acceptable.

#### With Alloy

Alloy finds instances of relational models:
1. Model domain in Alloy
2. Translate norms to predicates
3. Use Alloy Analyser to check satisfiability
4. Generate test cases from found instances

Admissible worlds = Alloy instances satisfying the admissibility predicate.

#### Runtime Monitoring

- Build enforcement hooks into your system
- Log violations with priority levels
- Trigger escalation procedures
- Maintain audit trail linking violations to norms


### Next Steps

#### For Immediate Use

1. *Identify your domain*: What system are you formalising?
2. *List your norms*: Gather all "must," "must not," "should" statements
3. *Define world structure*: What does a complete execution/state look like?
4. *Formalise incrementally*: Start with 3-5 critical norms, expand from there
5. *Validate with stakeholders*: Confirm formalisation match intent
6. *Choose verification tools*: Model checker, SAT solver, runtime monitor, or custom
7. *Implement and test*: Build, verify, deploy

#### For Deeper Integration

- Temporal embedding with TLA+ or LTL
- Alloy modelling for automated instance-finding
- Runtime monitoring and enforcement
- Traceability linking norms to requirements/regulations
- Change management: version norms alongside code

#### For Theoretical Extensions

- Probabilistic norms for statistical requirements
- Multi-agent settings with overlapping jurisdictions
- Epistemic extensions for knowledge-dependent norms
- Revision operators for norm evolution
- Proof-carrying code with normative certificates


### What This System Provides

This system lives at the boundary between logic and engineering, between philosophy and software.

It won't solve every problem. It won't replace human judgment. It won't make hard decisions easy.

What it *will* do:

- Make normative commitments *explicit*
- Make conflicts *visible* before they become incidents
- Make verification *possible* where it was previously informal
- Make responsibility *traceable* from policy to implementation

If that's what you need, this formalism will serve you well.

Start here: with worlds, admissibility, and the question: *Which futures are we willing to accept?*
