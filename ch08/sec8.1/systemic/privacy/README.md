
## Privacy

*This entry is an open exploration. A starting framework is provided below, but you are
expected to investigate, extend, and form your own understanding.*

Privacy in computing is the property that individuals retain control over information about
themselves: what is collected, by whom, for how long, for what purpose, and with whom it is
shared. It is related to security--and the two are often conflated--but they are distinct.

- *Security* asks: can unauthorised parties access this data?
- *Privacy* asks: should authorised parties have this data in the first place?

A system can be completely secure--all access is authorised, all data is encrypted in transit
and at rest--while being profoundly privacy-violating. A bank that securely stores and legitimately
uses your transaction history to build a detailed behavioural profile and sells it to advertisers
has not suffered a security breach. It has violated privacy.

Privacy is both a technical concern and a social one. It intersects with law, ethics, and the
political question of power: who controls information about people, and what can they do with it?


### Starting Points for Exploration

*Data minimisation:*

The simplest privacy principle is to not collect data you do not need. A system that never
stores a user's precise location cannot leak it. A system that deletes logs after 24 hours
cannot expose two-year-old behaviour to a subpoena. What does your system actually need?
What does it collect that it does not need?

*The right to be forgotten:*

GDPR (General Data Protection Regulation) and similar laws give users the right to request
deletion of their personal data. What does this mean technically? If a user's data is in
a database, in backups, in analytics aggregates, in logs, in a recommendation model trained
on their behaviour--what must be deleted? What is even possible to delete?

*Anonymisation and re-identification:*

Data that has been anonymised (names removed, identifiers replaced) often turns out not to
be anonymous. A famous study found that 87% of Americans could be uniquely identified by
only three data points: ZIP code, date of birth, and sex. Movie ratings anonymised by
Netflix were re-identified by cross-referencing with public IMDB reviews. What does true
anonymisation require? Is it achievable?

*Privacy vs. functionality:*

Many useful features require data. A maps application cannot give you personalised commute
times without knowing where you live and work. A recommendation system cannot suggest
relevant content without tracking what you have viewed. What are the legitimate trade-offs?
Who should make them? The system designer, the user, the regulator?

*Differential privacy:*

A mathematical framework that allows statistics about a population to be computed and
published without revealing information about individuals. The idea: add carefully calibrated
random noise to query results so that no individual's data has a significant influence on
the output. Apple and Google use it to collect aggregate usage statistics. What does it
buy? What does it cost?

*Encryption as a privacy tool:*

Encryption protects data from unauthorised access (security), but also from authorised access
by parties who should not have it. End-to-end encryption in messaging means that the
messaging provider cannot read messages even if compelled to. What are the privacy implications
of a system where the provider has no access to user data? What are the security implications?


### Questions to Answer

1. What is the difference between privacy, confidentiality, and anonymity?
2. What technical mechanisms can a system use to protect user privacy?
3. What are the limits of technical privacy protection? Where does law and policy take over?
4. Privacy and security are often in tension with safety and security (e.g., surveillance for
   crime prevention). How should those tensions be navigated? Who should decide?
5. Find a real system you use daily. What data does it collect about you? What is it used for?
   What would you change if you could?
6. What is the privacy cost of "free" services? Is there a privacy-preserving alternative model?

This is not a purely technical question. Write answers that engage with both the engineering
and the ethics. Discuss them with your peers.
