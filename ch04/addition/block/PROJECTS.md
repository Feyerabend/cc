
## Blockchain Project Ideas

This document contains project suggestions based on the blockchain
concepts you've learned. Half focus on programming and technical
implementation, while half explore the social, ethical, and societal
impacts of blockchain technology.


### Programming Projects


#### 1. Voting System Prototype

*Goal*: Extend `block.py` to create a simple electronic voting system.

*Your tasks*:
- Modify the Block class to store votes (voter ID, candidate choice, timestamp)
- Implement vote verification to prevent double-voting
- Add a function to tally results by traversing the chain
- Test tampering: try to change a vote in an earlier block and observe what happens

*Questions to consider*:
- How does the hash chain prevent vote manipulation?
- What happens if two nodes add votes at the same time?
- How would you make voter IDs anonymous while preventing double-voting?


#### 2. Supply Chain Tracker

*Goal*: Create a blockchain that tracks a product's journey from manufacturer to consumer.

*Your tasks*:
- Design block payloads to represent supply chain events (manufactured, shipped, inspected, delivered)
- Add timestamps and location data to each block
- Implement a query function to trace a product's complete history
- Add multiple participants (manufacturer, shipper, retailer) with different roles

*Questions to consider*:
- How does blockchain provide transparency in the supply chain?
- What information should be public vs private?
- How would you handle product recalls using this system?


#### 3. Digital Asset Registry

*Goal*: Build a system to register and transfer ownership of digital assets
(certificates, licenses, property deeds).

*Your tasks*:
- Create blocks that represent ownership transfers
- Implement a function to verify current ownership of an asset
- Add support for multi-signature transfers (requiring multiple parties to approve)
- Build a simple query interface to look up asset history

*Questions to consider*:
- How does this compare to traditional registries (land titles, car ownership)?
- What happens if someone loses their private key?
- Could this system work for physical assets? Why or why not?


#### 4. Consensus Algorithm Comparison

*Goal*: Implement and compare different consensus mechanisms.

*Your tasks*:
- Implement a simple Proof of Work system (find hash with leading zeros)
- Implement a Proof of Stake simulation (validators chosen by stake amount)
- Create a PBFT-style voting mechanism for your blockchain
- Measure and compare: speed, energy use, security under different attack scenarios

*Questions to consider*:
- Which consensus mechanism is most efficient? Most secure?
- How do these mechanisms handle malicious nodes?
- What trade-offs exist between speed and security?


#### 5. Smart Contract Simulator

*Goal*: Add programmable logic to your blockchain.

*Your tasks*:
- Design a simple smart contract language (even just if/then rules)
- Create contracts for common scenarios (escrow, recurring payments, conditional transfers)
- Implement a contract execution engine that runs when blocks are added
- Add state management so contracts can maintain data across blocks

*Questions to consider*:
- What kinds of agreements can be automated with smart contracts?
- What happens when there's a bug in a contract?
- How do you handle real-world data (like weather or prices) in a contract?


#### 6. Multi-Chain Federation

*Goal*: Connect multiple blockchain instances and enable cross-chain communication.

*Your tasks*:
- Run multiple instances of `block.py` on different Picos or simulated nodes
- Implement a bridge that can verify blocks from one chain on another
- Create cross-chain asset transfers or message passing
- Handle synchronization when chains operate at different speeds

*Questions to consider*:
- Why would you want multiple chains instead of one?
- How do you trust information from another chain?
- What security risks exist at chain boundaries?


#### 7. Privacy-Preserving Blockchain

*Goal*: Add privacy features while maintaining verifiability.

*Your tasks*:
- Implement zero-knowledge proofs (start simple: prove you know a number without revealing it)
- Create private transactions where amount and parties are hidden but validity is verifiable
- Add selective disclosure (prove properties about data without revealing the data)
- Compare privacy vs transparency trade-offs

*Questions to consider*:
- When is privacy essential in blockchain applications?
- How do you balance privacy with auditability?
- Can you have complete privacy and still prevent fraud?



### Social Impact Projects


#### 8. Blockchain and Energy Consumption

*Goal*: Research and analyze the environmental impact of blockchain technology.

*Your tasks*:
- Calculate the energy consumption of your `block.py` implementation
- Research the energy use of Bitcoin, Ethereum, and newer Proof of Stake networks
- Compare blockchain energy use to traditional systems (banks, data centers, payment processors)
- Propose and evaluate alternative consensus mechanisms for sustainability

*Questions to explore*:
- Is blockchain's energy use justified by its benefits?
- Who should be responsible for blockchain's environmental impact?
- How might future regulations address cryptocurrency energy consumption?
- What innovations could make blockchain more sustainable?


#### 9. Financial Inclusion and Cryptocurrency

*Goal*: Investigate how blockchain affects access to financial services.

*Your tasks*:
- Research regions with limited banking infrastructure and high cryptocurrency adoption
- Interview or survey people about their experiences with digital currencies
- Analyze barriers to entry (internet access, technical literacy, device ownership)
- Examine cases where cryptocurrency helped or harmed financially excluded populations

*Questions to explore*:
- Can cryptocurrency really "bank the unbanked"? What evidence exists?
- What happens when people in unstable economies rely on volatile cryptocurrencies?
- How do transaction fees affect people with limited resources?
- What alternatives to blockchain might better serve financial inclusion?


#### 10. Decentralisation vs Power Concentration

*Goal*: Examine whether blockchain actually decentralizes power or creates new concentrations.

*Your tasks*:
- Research mining pool concentration in Bitcoin (who controls majority hash power?)
- Analyze wealth distribution in major cryptocurrencies
- Investigate who controls development of major blockchain protocols
- Map the actual infrastructure: where are nodes located? Who owns the servers?

*Questions to explore*:
- Is blockchain truly decentralized in practice?
- Have new power structures emerged (mining cartels, large holders, core developers)?
- Does "code is law" give too much power to programmers?
- What happens when a small group controls a "decentralized" system?


#### 11. Blockchain in Democratic Processes

*Goal*: Critically evaluate blockchain-based voting and governance systems.

*Your tasks*:
- Research real-world blockchain voting pilots (Estonia, West Virginia, others)
- Analyze attacks on voting systems: coercion, vote buying, technical exploits
- Interview election officials or security experts about concerns
- Design a threat model for blockchain voting in your local context

*Questions to explore*:
- Does blockchain solve real problems in current voting systems?
- What new vulnerabilities does electronic voting introduce?
- How do you ensure accessibility for all voters (elderly, disabled, poor)?
- Is the transparency of blockchain compatible with ballot secrecy?
- Who audits the code? Who trusts the auditors?


#### 12. Blockchain and Labor Rights

*Goal*: Investigate how blockchain and Web3 technologies affect workers.

*Your tasks*:
- Research NFT creators: ownership rights, platform power, income stability
- Examine "play-to-earn" games: who profits? What are working conditions?
- Analyze DAOs (Decentralized Autonomous Organizations): worker protections, dispute resolution
- Compare traditional employment protections with blockchain-based work

*Questions to explore*:
- Do smart contracts empower workers or remove protections?
- Who benefits most from "decentralized" platforms?
- How do you resolve disputes when "code is law"?
- What happens to labor rights when work is mediated by immutable contracts?


#### 13. Speculation, Scams, and Vulnerable Populations

*Goal*: Examine how cryptocurrency affects at-risk groups.

*Your tasks*:
- Document common cryptocurrency scams targeting specific communities
- Research pump-and-dump schemes, rug pulls, and Ponzi structures
- Analyze the psychology of FOMO (fear of missing out) in crypto marketing
- Interview victims of cryptocurrency scams or financial counselors who help them

*Questions to explore*:
- Why are some communities disproportionately targeted by crypto scams?
- How does "get rich quick" messaging harm people?
- What responsibility do platforms, influencers, and developers have?
- Should governments regulate cryptocurrency? How?


#### 14. Digital Identity and Surveillance

*Goal*: Explore blockchain's role in identity systems and privacy.

*Your tasks*:
- Research blockchain-based identity proposals (self-sovereign identity, digital credentials)
- Analyze the trade-off between identity verification and privacy
- Investigate surveillance risks: permanent records, data correlation, social graphs
- Compare blockchain identity to current systems (passports, social security numbers)

*Questions to explore*:
- Do you want your identity permanently recorded on a blockchain?
- Who controls your identity data in different systems?
- How might governments or corporations use blockchain identity for surveillance?
- What happens if your identity is stolen or compromised on a blockchain?
- Can blockchain provide privacy and accountability simultaneously?


#### 15. Cultural Heritage and NFTs

*Goal*: Critically examine NFTs' impact on art, culture, and indigenous communities.

*Your tasks*:
- Research cases of cultural appropriation through NFTs
- Analyze who profits when traditional art or artifacts are tokenized
- Interview artists about NFT platforms: benefits, exploitation, power dynamics
- Examine environmental justice: communities harmed by mining for "digital art"

*Questions to explore*:
- Who has the right to tokenize cultural artifacts or practices?
- Do NFTs help or harm artists financially?
- What is lost when culture becomes tradeable tokens?
- How do indigenous communities view blockchain and NFTs?




### Combining Technical and Social Analysis

The most impactful projects combine both dimensions. For any programming project, ask:
- *Who benefits?* Who is excluded?
- *What power structures* does this create or reinforce?
- *What could go wrong?* How might this be misused?
- *Who decides?* Who writes the code, sets the rules, controls access?

For any social impact project, consider:
- *What technical constraints* shape these outcomes?
- *Could the code be different?* What alternatives exist?
- *How does implementation matter?* Same idea, different results based on design choices.


### Reflection Questions for All Projects

Regardless of which project you choose, consider:

1. *Immutability*: Is permanence always good? What if you need to correct mistakes,
   remove harmful content, or comply with privacy laws like GDPR's "right to be forgotten"?

2. *Accessibility*: Who can participate? What barriers exist (cost, technical knowledge,
   internet access, language, disability)?

3. *Governance*: How are decisions made? Who can propose changes? How are disputes resolved?

4. *Accountability*: When things go wrong, who is responsible? Can you sue a smart contract? A DAO?

5. *Sustainability*: Beyond energy use, is this system sustainable socially, economically, and ethically?


### Getting Started

1. Choose a project that genuinely interests you
2. Start small: build a minimal version or research a specific case
3. Talk to real people affected by these technologies
4. Be critical: question assumptions, including your own
5. Document what you learn: code, research findings, interviews, reflections
6. Share your work and invite feedback

