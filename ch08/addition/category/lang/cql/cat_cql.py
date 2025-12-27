"""
Categorical Query Language (CQL)
=================================
A database query language built on category theory principles:

- Tables are objects in the category
- Queries are morphisms (functors between categories)
- Joins are pullbacks
- Unions are coproducts (pushouts)
- Aggregations are natural transformations
- Query composition follows functorial laws

This reimagines relational algebra through categorical lenses.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, TypeVar, List, Dict, Set, Tuple
from dataclasses import dataclass, field
from collections import defaultdict
from copy import deepcopy


# ============================================================================
# CATEGORY THEORY FOUNDATIONS
# ============================================================================

T = TypeVar('T')
U = TypeVar('U')

class Functor(ABC):
    """Functor maps between categories"""
    @abstractmethod
    def fmap(self, f: Callable) -> 'Functor':
        pass

class NaturalTransformation(ABC):
    """Natural transformation between functors"""
    @abstractmethod
    def component(self, obj: Any) -> Callable:
        pass


# ============================================================================
# SCHEMA (Category of Types)
# ============================================================================

class SchemaType(ABC):
    """Base type in schema category"""
    @abstractmethod
    def __str__(self):
        pass
    
    @abstractmethod
    def validate(self, value: Any) -> bool:
        pass

class IntType(SchemaType):
    def __str__(self): return "Int"
    def validate(self, value): return isinstance(value, int)

class StrType(SchemaType):
    def __str__(self): return "String"
    def validate(self, value): return isinstance(value, str)

class FloatType(SchemaType):
    def __str__(self): return "Float"
    def validate(self, value): return isinstance(value, (int, float))

class BoolType(SchemaType):
    def __str__(self): return "Bool"
    def validate(self, value): return isinstance(value, bool)

@dataclass
class Schema:
    """Schema defines the structure (object in schema category)"""
    name: str
    columns: Dict[str, SchemaType]
    
    def __str__(self):
        cols = ", ".join(f"{k}: {v}" for k, v in self.columns.items())
        return f"{self.name}({cols})"
    
    def project(self, cols: List[str]) -> 'Schema':
        """Project to subset of columns"""
        return Schema(
            f"{self.name}_proj",
            {k: v for k, v in self.columns.items() if k in cols}
        )
    
    def product(self, other: 'Schema') -> 'Schema':
        """Categorical product (cartesian product of schemas)"""
        new_cols = {}
        for k, v in self.columns.items():
            new_cols[f"{self.name}.{k}"] = v
        for k, v in other.columns.items():
            new_cols[f"{other.name}.{k}"] = v
        return Schema(f"{self.name}_x_{other.name}", new_cols)


# ============================================================================
# TABLES (Instances of Schema)
# ============================================================================

@dataclass
class Row:
    """A row is a morphism from terminal object to schema"""
    data: Dict[str, Any]
    
    def __getitem__(self, key):
        return self.data.get(key)
    
    def __str__(self):
        return f"Row({self.data})"
    
    def project(self, columns: List[str]) -> 'Row':
        """Project row to subset of columns"""
        return Row({k: v for k, v in self.data.items() if k in columns})
    
    def merge(self, other: 'Row') -> 'Row':
        """Merge two rows (for joins)"""
        merged = deepcopy(self.data)
        merged.update(other.data)
        return Row(merged)

@dataclass
class Table:
    """Table is a presheaf (contravariant functor)"""
    schema: Schema
    rows: List[Row] = field(default_factory=list)
    
    def __str__(self):
        return f"Table[{self.schema.name}]({len(self.rows)} rows)"
    
    def insert(self, row_data: Dict[str, Any]):
        """Insert a row"""
        # Validate
        for col, typ in self.schema.columns.items():
            if col not in row_data:
                raise ValueError(f"Missing column: {col}")
            if not typ.validate(row_data[col]):
                raise TypeError(f"Invalid type for {col}")
        self.rows.append(Row(row_data))
    
    def display(self, limit: int = None):
        """Display table contents"""
        print(f"\n{self.schema}")
        print("=" * 70)
        
        if not self.rows:
            print("(empty table)")
            return
        
        # Header
        cols = list(self.schema.columns.keys())
        print(" | ".join(f"{c:15}" for c in cols))
        print("-" * 70)
        
        # Rows
        for i, row in enumerate(self.rows):
            if limit and i >= limit:
                print(f"... ({len(self.rows) - limit} more rows)")
                break
            print(" | ".join(f"{str(row[c]):15}" for c in cols))


# ============================================================================
# QUERY MORPHISMS (Functors between table categories)
# ============================================================================

class Query(ABC):
    """Query is a functor from one table category to another"""
    
    @abstractmethod
    def apply(self, table: Table) -> Table:
        """Apply query transformation"""
        pass
    
    @abstractmethod
    def infer_schema(self, input_schema: Schema) -> Schema:
        """Infer output schema (functor on objects)"""
        pass
    
    def __rshift__(self, other: 'Query') -> 'Query':
        """Compose queries: self >> other (functorial composition)"""
        return ComposedQuery(self, other)


class SelectQuery(Query):
    """SELECT query - projects columns (projection functor)"""
    
    def __init__(self, columns: List[str]):
        self.columns = columns
    
    def infer_schema(self, input_schema: Schema) -> Schema:
        return input_schema.project(self.columns)
    
    def apply(self, table: Table) -> Table:
        new_schema = self.infer_schema(table.schema)
        result = Table(new_schema)
        for row in table.rows:
            result.rows.append(row.project(self.columns))
        return result
    
    def __str__(self):
        return f"SELECT({', '.join(self.columns)})"


class WhereQuery(Query):
    """WHERE query - filters rows (subfunctor)"""
    
    def __init__(self, predicate: Callable[[Row], bool]):
        self.predicate = predicate
    
    def infer_schema(self, input_schema: Schema) -> Schema:
        return input_schema  # Schema unchanged
    
    def apply(self, table: Table) -> Table:
        result = Table(table.schema)
        result.rows = [row for row in table.rows if self.predicate(row)]
        return result
    
    def __str__(self):
        return "WHERE(predicate)"


class MapQuery(Query):
    """MAP query - transforms columns (functor mapping)"""
    
    def __init__(self, transforms: Dict[str, Tuple[str, Callable]]):
        """
        transforms: {new_col: (old_col, function)}
        """
        self.transforms = transforms
    
    def infer_schema(self, input_schema: Schema) -> Schema:
        new_cols = {}
        for new_col, (old_col, _) in self.transforms.items():
            new_cols[new_col] = input_schema.columns.get(old_col, IntType())
        return Schema(f"{input_schema.name}_mapped", new_cols)
    
    def apply(self, table: Table) -> Table:
        new_schema = self.infer_schema(table.schema)
        result = Table(new_schema)
        
        for row in table.rows:
            new_data = {}
            for new_col, (old_col, func) in self.transforms.items():
                new_data[new_col] = func(row[old_col])
            result.rows.append(Row(new_data))
        
        return result
    
    def __str__(self):
        return f"MAP({list(self.transforms.keys())})"


class JoinQuery(Query):
    """JOIN query - categorical pullback"""
    
    def __init__(self, other_table: Table, left_key: str, right_key: str, join_type: str = "inner"):
        self.other_table = other_table
        self.left_key = left_key
        self.right_key = right_key
        self.join_type = join_type
    
    def infer_schema(self, input_schema: Schema) -> Schema:
        return input_schema.product(self.other_table.schema)
    
    def apply(self, table: Table) -> Table:
        new_schema = self.infer_schema(table.schema)
        result = Table(new_schema)
        
        if self.join_type == "inner":
            # Inner join: pullback in category
            for left_row in table.rows:
                for right_row in self.other_table.rows:
                    if left_row[self.left_key] == right_row[self.right_key]:
                        # Merge rows with qualified names
                        merged_data = {}
                        for k, v in left_row.data.items():
                            merged_data[f"{table.schema.name}.{k}"] = v
                        for k, v in right_row.data.items():
                            merged_data[f"{self.other_table.schema.name}.{k}"] = v
                        result.rows.append(Row(merged_data))
        
        elif self.join_type == "left":
            # Left outer join
            for left_row in table.rows:
                matched = False
                for right_row in self.other_table.rows:
                    if left_row[self.left_key] == right_row[self.right_key]:
                        merged_data = {}
                        for k, v in left_row.data.items():
                            merged_data[f"{table.schema.name}.{k}"] = v
                        for k, v in right_row.data.items():
                            merged_data[f"{self.other_table.schema.name}.{k}"] = v
                        result.rows.append(Row(merged_data))
                        matched = True
                
                if not matched:
                    # Add left row with nulls for right
                    merged_data = {}
                    for k, v in left_row.data.items():
                        merged_data[f"{table.schema.name}.{k}"] = v
                    for k in self.other_table.schema.columns:
                        merged_data[f"{self.other_table.schema.name}.{k}"] = None
                    result.rows.append(Row(merged_data))
        
        return result
    
    def __str__(self):
        return f"JOIN({self.left_key}={self.right_key})"


class UnionQuery(Query):
    """UNION query - categorical coproduct (pushout)"""
    
    def __init__(self, other_table: Table):
        self.other_table = other_table
    
    def infer_schema(self, input_schema: Schema) -> Schema:
        # Union requires same schema
        return input_schema
    
    def apply(self, table: Table) -> Table:
        if table.schema.columns != self.other_table.schema.columns:
            raise ValueError("UNION requires compatible schemas")
        
        result = Table(table.schema)
        result.rows = table.rows + self.other_table.rows
        return result
    
    def __str__(self):
        return "UNION"


class GroupByQuery(Query):
    """GROUP BY query - natural transformation (aggregation)"""
    
    def __init__(self, group_cols: List[str], agg_funcs: Dict[str, Tuple[str, Callable]]):
        """
        group_cols: columns to group by
        agg_funcs: {result_col: (source_col, aggregation_function)}
        """
        self.group_cols = group_cols
        self.agg_funcs = agg_funcs
    
    def infer_schema(self, input_schema: Schema) -> Schema:
        new_cols = {}
        for col in self.group_cols:
            new_cols[col] = input_schema.columns[col]
        for result_col, (source_col, _) in self.agg_funcs.items():
            # Assume aggregation results are same type (simplified)
            new_cols[result_col] = input_schema.columns.get(source_col, IntType())
        return Schema(f"{input_schema.name}_grouped", new_cols)
    
    def apply(self, table: Table) -> Table:
        new_schema = self.infer_schema(table.schema)
        result = Table(new_schema)
        
        # Group rows
        groups = defaultdict(list)
        for row in table.rows:
            key = tuple(row[col] for col in self.group_cols)
            groups[key].append(row)
        
        # Apply aggregations
        for key, group_rows in groups.items():
            new_data = {}
            # Add group key columns
            for i, col in enumerate(self.group_cols):
                new_data[col] = key[i]
            
            # Apply aggregation functions
            for result_col, (source_col, agg_func) in self.agg_funcs.items():
                values = [row[source_col] for row in group_rows]
                new_data[result_col] = agg_func(values)
            
            result.rows.append(Row(new_data))
        
        return result
    
    def __str__(self):
        return f"GROUP_BY({', '.join(self.group_cols)})"


class OrderByQuery(Query):
    """ORDER BY query - endofunctor with ordering"""
    
    def __init__(self, column: str, ascending: bool = True):
        self.column = column
        self.ascending = ascending
    
    def infer_schema(self, input_schema: Schema) -> Schema:
        return input_schema  # Schema unchanged
    
    def apply(self, table: Table) -> Table:
        result = Table(table.schema)
        # Handle None values in sorting
        result.rows = sorted(
            table.rows,
            key=lambda row: (row[self.column] is None, row[self.column] or 0),
            reverse=not self.ascending
        )
        return result
    
    def __str__(self):
        direction = "ASC" if self.ascending else "DESC"
        return f"ORDER_BY({self.column} {direction})"


class LimitQuery(Query):
    """LIMIT query - truncation functor"""
    
    def __init__(self, n: int):
        self.n = n
    
    def infer_schema(self, input_schema: Schema) -> Schema:
        return input_schema  # Schema unchanged
    
    def apply(self, table: Table) -> Table:
        result = Table(table.schema)
        result.rows = table.rows[:self.n]
        return result
    
    def __str__(self):
        return f"LIMIT({self.n})"


class ComposedQuery(Query):
    """Composition of queries (functorial composition)"""
    
    def __init__(self, first: Query, second: Query):
        self.first = first
        self.second = second
    
    def infer_schema(self, input_schema: Schema) -> Schema:
        intermediate = self.first.infer_schema(input_schema)
        return self.second.infer_schema(intermediate)
    
    def apply(self, table: Table) -> Table:
        intermediate = self.first.apply(table)
        return self.second.apply(intermediate)
    
    def __str__(self):
        return f"({self.first} >> {self.second})"


# ============================================================================
# QUERY BUILDER (Fluent Interface)
# ============================================================================

class QueryBuilder:
    """Fluent interface for building categorical queries"""
    
    def __init__(self, table: Table):
        self.table = table
        self.query = None
    
    def select(self, *columns: str) -> 'QueryBuilder':
        """Project columns"""
        q = SelectQuery(list(columns))
        self.query = q if self.query is None else self.query >> q
        return self
    
    def where(self, predicate: Callable[[Row], bool]) -> 'QueryBuilder':
        """Filter rows"""
        q = WhereQuery(predicate)
        self.query = q if self.query is None else self.query >> q
        return self
    
    def map(self, **transforms) -> 'QueryBuilder':
        """Transform columns: new_col=(old_col, func)"""
        trans_dict = {k: v for k, v in transforms.items()}
        q = MapQuery(trans_dict)
        self.query = q if self.query is None else self.query >> q
        return self
    
    def join(self, other_table: Table, left_key: str, right_key: str, how: str = "inner") -> 'QueryBuilder':
        """Join with another table"""
        q = JoinQuery(other_table, left_key, right_key, how)
        self.query = q if self.query is None else self.query >> q
        return self
    
    def union(self, other_table: Table) -> 'QueryBuilder':
        """Union with another table"""
        q = UnionQuery(other_table)
        self.query = q if self.query is None else self.query >> q
        return self
    
    def group_by(self, *columns: str, **aggregations) -> 'QueryBuilder':
        """Group by columns with aggregations"""
        q = GroupByQuery(list(columns), aggregations)
        self.query = q if self.query is None else self.query >> q
        return self
    
    def order_by(self, column: str, ascending: bool = True) -> 'QueryBuilder':
        """Order by column"""
        q = OrderByQuery(column, ascending)
        self.query = q if self.query is None else self.query >> q
        return self
    
    def limit(self, n: int) -> 'QueryBuilder':
        """Limit results"""
        q = LimitQuery(n)
        self.query = q if self.query is None else self.query >> q
        return self
    
    def execute(self) -> Table:
        """Execute the query"""
        if self.query is None:
            return self.table
        return self.query.apply(self.table)
    
    def explain(self):
        """Explain query plan"""
        print(f"\nQuery Plan:")
        print(f"  {self.query if self.query else 'Identity'}")


# ============================================================================
# DEMONSTRATION
# ============================================================================

def demo():
    print("=" * 70)
    print("CATEGORICAL QUERY LANGUAGE (CQL)")
    print("=" * 70)
    print("A database query language built on category theory")
    print("- Tables are objects")
    print("- Queries are functors")
    print("- Joins are pullbacks")
    print("- Unions are coproducts")
    print("- Aggregations are natural transformations")
    print("=" * 70)
    
    # Create schemas
    employee_schema = Schema("Employee", {
        "id": IntType(),
        "name": StrType(),
        "dept_id": IntType(),
        "salary": IntType()
    })
    
    dept_schema = Schema("Department", {
        "id": IntType(),
        "name": StrType(),
        "budget": IntType()
    })

    # Create tables
    employees = Table(employee_schema)
    employees.insert({"id": 1, "name": "Alice", "dept_id": 10, "salary": 70000})
    employees.insert({"id": 2, "name": "Bob", "dept_id": 20, "salary": 80000})
    employees.insert({"id": 3, "name": "Charlie", "dept_id": 10, "salary": 75000})
    employees.insert({"id": 4, "name": "Diana", "dept_id": 30, "salary": 90000})
    employees.insert({"id": 5, "name": "Eve", "dept_id": 20, "salary": 85000})
    
    departments = Table(dept_schema)
    departments.insert({"id": 10, "name": "Engineering", "budget": 500000})
    departments.insert({"id": 20, "name": "Sales", "budget": 300000})
    departments.insert({"id": 30, "name": "Marketing", "budget": 200000})
    
    print("\nOriginal Tables")
    employees.display()
    departments.display()
    
    # Example 1: Simple projection (SELECT)
    print("\n" + "-" * 70)
    print("Example 1: Projection (SELECT name, salary)")
    print("-" * 70)
    
    result1 = QueryBuilder(employees).select("name", "salary").execute()
    result1.display()
    
    # Example 2: Filter (WHERE)
    print("\n" + "-" * 70)
    print("Example 2: Filter (WHERE salary > 75000)")
    print("-" * 70)
    
    result2 = (QueryBuilder(employees)
               .where(lambda row: row["salary"] > 75000)
               .select("name", "salary")
               .execute())
    result2.display()
    
    # Example 3: Map (transform columns)
    print("\n" + "-" * 70)
    print("Example 3: Transform (salary in thousands)")
    print("-" * 70)
    
    result3 = (QueryBuilder(employees)
               .select("name", "salary")
               .map(salary_k=("salary", lambda x: x // 1000))
               .execute())
    result3.display()
    
    # Example 4: Join (categorical pullback)
    print("\n" + "-" * 70)
    print("Example 4: JOIN (Employee ⋈ Department)")
    print("-" * 70)
    
    result4 = (QueryBuilder(employees)
               .join(departments, "dept_id", "id")
               .select("Employee.name", "Department.name", "Employee.salary")
               .execute())
    result4.display()
    
    # Example 5: Group By (natural transformation)
    print("\n" + "-" * 70)
    print("Example 5: GROUP BY dept_id (aggregation)")
    print("-" * 70)
    
    result5 = (QueryBuilder(employees)
               .group_by("dept_id",
                        avg_salary=("salary", lambda vals: sum(vals) // len(vals)),
                        count=("id", lambda vals: len(vals)))
               .execute())
    result5.display()
    
    # Example 6: Complex query (composition of functors)
    print("\n" + "-" * 70)
    print("Example 6: Complex Query (composition)")
    print("High-earning employees by department")
    print("-" * 70)
    
    result6 = (QueryBuilder(employees)
               .where(lambda row: row["salary"] > 75000)
               .join(departments, "dept_id", "id")
               .select("Department.name", "Employee.name", "Employee.salary")
               .order_by("Employee.salary", ascending=False)
               .execute())
    result6.display()
    
    # Example 7: Aggregation with join
    print("\n" + "-" * 70)
    print("Example 7: Department statistics")
    print("-" * 70)
    
    result7 = (QueryBuilder(employees)
               .group_by("dept_id",
                        total_salary=("salary", sum),
                        avg_salary=("salary", lambda vals: sum(vals) // len(vals)),
                        count=("id", len))
               .join(departments, "dept_id", "id")
               .select("Department.name", "total_salary", "avg_salary", "count")
               .order_by("total_salary", ascending=False)
               .execute())
    result7.display()
    
    print("\n" + "-" * 70)
    print("All examples demonstrate categorical properties:")
    print("- Functoriality (structure preservation)")
    print("- Composition (query pipelining)")
    print("- Universal properties (joins as pullbacks)")
    print("-" * 70)

if __name__ == "__main__":
    demo()
