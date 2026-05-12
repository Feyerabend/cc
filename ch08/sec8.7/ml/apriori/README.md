
## Apriori and FP-Growth

The Apriori algorithm and FP-Growth are the two foundational methods for discovering frequent
itemsets in a transaction database--for example, finding which products are commonly bought
together. Both exploit the same downward-closure property: if an itemset is frequent, every
one of its subsets must also be frequent. They differ in how they use this property.

The Apriori algorithm works by generating candidate itemsets level by level. At level k it
produces all size-k candidates from the size-(k-1) frequent itemsets, scans the database to
count their support, and prunes those below the minimum support threshold. This is simple to
implement but requires many database scans and can generate a very large number of candidates.

FP-Growth avoids candidate generation entirely. It compresses the transaction database into a
prefix tree (FP-tree) in just two scans, then mines frequent itemsets recursively by dividing
the problem into smaller sub-problems on conditional pattern bases. This makes it significantly
faster on large, dense datasets.


### Apriori

#### Mathematics

Let:
- $I = \{ i_1, i_2, \dots, i_n \}$ be the set of all items.
- $D = \{ T_1, T_2, \dots, T_m \}$ be the set of transactions, where each $T_i \subseteq I$.
- An itemset $X \subseteq I$ is frequent if its support exceeds a user-defined threshold.

Support of itemset $X$:
```math
\text{support}(X) = \frac{|\{ T \in D \mid X \subseteq T \}|}{|D|}
```

Confidence of the association rule $X \Rightarrow Y$:
```math
\text{confidence}(X \Rightarrow Y) = \frac{\text{support}(X \cup Y)}{\text{support}(X)}
```

Time complexity (approximate, over all levels):
```math
\mathcal{O}\left(\sum_{k=1}^{K} |C_k| \cdot N \cdot k \right)
```
where $C_k$ is the set of candidates at level $k$ and $N$ is the number of transactions.
Candidate count is exponential in the worst case: $\sum_{k=1}^{m} \binom{m}{k} = 2^m - 1$.

#### Algorithm

1. Generate all 1-itemsets and count their support.
2. Prune those below *minSupport*.
3. Join the surviving (k-1)-itemsets to produce k-itemsets; prune candidates that have an
   infrequent subset (Apriori principle).
4. Scan the database to count support for the remaining candidates.
5. Repeat from step 3 until no new frequent itemsets are found.


### FP-Growth

#### Tree Construction

FP-Growth compresses the database into an FP-tree in two passes:
- *Pass 1:* Count the support of every item; discard infrequent ones.
- *Pass 2:* Insert each transaction (retaining only frequent items, sorted by descending
  support) into a prefix tree. Shared prefixes are merged, keeping node counts.

Mining then proceeds recursively: for each frequent item $i$, the conditional pattern base
(all paths ending at $i$) forms a sub-database from which a smaller FP-tree is built and
mined.

#### Comparison

| Aspect                  | Apriori                              | FP-Growth                            |
|-------------------------|--------------------------------------|--------------------------------------|
| Strategy                | Generate-and-test                    | Divide-and-conquer                   |
| Candidate generation    | Explicit                             | None                                 |
| Database scans          | $\geq k$ (one per level)             | 2                                    |
| Memory                  | High (stores all $C_k$)              | Low (compact prefix tree)            |
| Sparse data             | Acceptable                           | Excellent                            |
| Dense data              | Slow (many candidates)               | Much faster                          |


### Samples


*Sample 1: Market Basket Analysis*

* *Data:* Supermarket receipts -- each transaction is a set of products purchased together.
* *Threshold:* minSupport = 0.3, minConfidence = 0.6.
* *Scenario:* A retailer mines frequent itemsets to discover that bread and butter appear
  together in 40% of transactions. The rule "bread → butter" with 75% confidence can be
  used to place items near each other or to design promotions.

*Sample 2: Web Clickstream Analysis*

* *Data:* Web server logs -- each transaction is the set of pages visited in one session.
* *Threshold:* minSupport = 0.05 (5% of sessions).
* *Scenario:* An e-commerce site identifies page sequences that frequently co-occur. This
  informs navigation redesign and surfaces related-content recommendations.

*Sample 3: Medical Co-morbidity Discovery*

* *Data:* Patient records -- each transaction is the set of diagnoses for one patient.
* *Threshold:* minSupport = 0.1.
* *Scenario:* Researchers mine the records to find groups of conditions that co-occur more
  often than expected, which may suggest shared risk factors or guide screening protocols.
