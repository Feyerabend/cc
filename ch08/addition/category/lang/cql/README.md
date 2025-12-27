
## Categorical Query Language

This file defines "Categorical Query Language" (CQL), a tiny in-memory relational database
query engine in Python.
- Schemas and typed tables.
- Rows as dictionaries with validation.
- A set of query operations (Select, Where, Map, Join, Union, GroupBy, OrderBy, Limit).
- A fluent *QueryBuilder* for chaining operations (e.g., `.select(...).where(...).join(...)`).
- Query composition via the `>>` operator.
The demo creates sample Employee and Department tables and runs several queries,
from simple projections to complex joins with aggregations.

### *Context in Category Theory*

This one engages more directly with applied category theory in databases:
- *Tables/schemas* are treated as *objects* in a category.
- *Queries* are explicitly modeled as *functors* (they map tables to tables while preserving structure).
- *Query composition* uses functorial composition (`self >> other`).
- *Joins* are described as *pullbacks* (the universal construction capturing matching rows).
- *Unions* as *coproducts* (disjoint union of rows).
- *Aggregations/GroupBy* as *natural transformations* (transforming between functors in a structure-preserving way).
- Projections and selections align with categorical projections and subobjects.

This mirrors real research in *categorical database theory* (e.g., David Spivak, Bob Rosebrugh, and others),
where relational algebra operations are reinterpreted using limits, colimits, functors, and natural transformations.
Both files shows how category theory concepts can inspire cleaner, more compositional designs in programming
languages and data querying systems.

