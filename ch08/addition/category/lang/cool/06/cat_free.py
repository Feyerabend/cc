"""
Categorical Object-Oriented Language (COOL) with Free Monads
=============================================================
An OOP language where:
- Free monads give you monads "for free" from any functor
- Separate program structure from interpretation
- Build composable DSLs (Domain Specific Languages)
- Multiple interpreters for same program
- Coproduct of functors (extensible effects)
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Set, Tuple, Optional, TypeVar, Generic, Union
from dataclasses import dataclass, field
from collections import defaultdict



# CATEGORY THEORY FOUNDATIONS


class CategoryObject(ABC):
    """Object in a category"""
    @abstractmethod
    def name(self) -> str:
        pass



# TYPE SYSTEM


class Type(CategoryObject):
    """Types are objects in the category"""
    def __init__(self, name: str):
        self._name = name
    
    def name(self) -> str:
        return self._name
    
    def __str__(self):
        return self._name



# RUNTIME VALUES


@dataclass
class Value(ABC):
    """Base runtime value"""
    pass


@dataclass
class IntValue(Value):
    value: int
    def __str__(self): return str(self.value)


@dataclass
class StringValue(Value):
    value: str
    def __str__(self): return f'"{self.value}"'


@dataclass
class BoolValue(Value):
    value: bool
    def __str__(self): return str(self.value).lower()


@dataclass
class UnitValue(Value):
    def __str__(self): return "()"


@dataclass
class ListValue(Value):
    elements: List[Value]
    def __str__(self):
        items = ", ".join(str(e) for e in self.elements)
        return f"[{items}]"



# FREE MONAD DEFINITION


class Free(ABC):
    """Free monad: Free F A
    
    The free monad over a functor F:
      Free F A = Pure A | Free (F (Free F A))
    
    This is the initial algebra giving us monadic structure for free!
    """
    
    @abstractmethod
    def bind(self, f: Callable[[Value], 'Free']) -> 'Free':
        """Monadic bind for free monad"""
        pass
    
    @abstractmethod
    def fmap(self, f: Callable[[Value], Value]) -> 'Free':
        """Functor map"""
        pass
    
    @abstractmethod
    def interpret(self, interpreter: 'Interpreter') -> Value:
        """Interpret the free monad using given interpreter"""
        pass


@dataclass
class Pure(Free):
    """Pure value: Pure A
    
    The 'return' of the monad - wraps a pure value.
    """
    value: Value
    
    def bind(self, f: Callable[[Value], Free]) -> Free:
        """Pure a >>= f = f a"""
        return f(self.value)
    
    def fmap(self, f: Callable[[Value], Value]) -> Free:
        """fmap f (Pure a) = Pure (f a)"""
        return Pure(f(self.value))
    
    def interpret(self, interpreter: 'Interpreter') -> Value:
        """Interpreting Pure just returns the value"""
        return self.value
    
    def __str__(self):
        return f"Pure({self.value})"


@dataclass
class Impure(Free):
    """Impure computation: Free (F (Free F A))
    
    Wraps a functor F containing the next computation.
    This represents one "layer" of effects.
    """
    functor: 'FunctorF'
    
    def bind(self, f: Callable[[Value], Free]) -> Free:
        """Impure fa >>= f = Impure (fmap (>>= f) fa)"""
        # Push bind deeper into the structure
        return Impure(self.functor.fmap_free(lambda free: free.bind(f)))
    
    def fmap(self, f: Callable[[Value], Value]) -> Free:
        """fmap f (Impure fa) = Impure (fmap (fmap f) fa)"""
        return Impure(self.functor.fmap_free(lambda free: free.fmap(f)))
    
    def interpret(self, interpreter: 'Interpreter') -> Value:
        """Interpret using the interpreter's algebra"""
        return interpreter.run(self.functor)
    
    def __str__(self):
        return f"Impure({self.functor})"



# FUNCTOR F (for Free F)


class FunctorF(ABC):
    """Base functor for Free monad
    
    This is the F in Free F A.
    Different DSLs define different functors.
    """
    
    @abstractmethod
    def fmap_free(self, f: Callable[[Free], Free]) -> 'FunctorF':
        """Map over the Free computations inside"""
        pass
    
    @abstractmethod
    def run_step(self, interpreter: 'Interpreter') -> Free:
        """Execute one step and return next computation"""
        pass



# INTERPRETER (F-Algebra)


class Interpreter(ABC):
    """Interpreter for a functor F
    
    This is an F-algebra: F A -> A
    Maps functor operations to actual effects.
    """
    
    @abstractmethod
    def run(self, functor: FunctorF) -> Value:
        """Interpret a functor operation"""
        pass



# DSL 1: CONSOLE I/O


@dataclass
class ConsoleF(FunctorF):
    """Console I/O functor - base operations"""
    pass


@dataclass
class PrintLine(ConsoleF):
    """Print string and continue"""
    message: str
    next_computation: Free
    
    def fmap_free(self, f: Callable[[Free], Free]) -> ConsoleF:
        return PrintLine(self.message, f(self.next_computation))
    
    def run_step(self, interpreter: Interpreter) -> Free:
        return self.next_computation
    
    def __str__(self):
        return f"PrintLine({self.message})"


@dataclass
class ReadLine(ConsoleF):
    """Read string and continue with result"""
    continuation: Callable[[str], Free]
    
    def fmap_free(self, f: Callable[[Free], Free]) -> ConsoleF:
        return ReadLine(lambda s: f(self.continuation(s)))
    
    def run_step(self, interpreter: Interpreter) -> Free:
        # Interpreter will provide the input
        return Pure(UnitValue())  # Placeholder
    
    def __str__(self):
        return "ReadLine(<continuation>)"


# Console DSL helper functions
def print_line(msg: str) -> Free:
    """Smart constructor: print a line"""
    return Impure(PrintLine(msg, Pure(UnitValue())))


def read_line() -> Free:
    """Smart constructor: read a line"""
    return Impure(ReadLine(lambda s: Pure(StringValue(s))))


# Console Interpreter
class ConsoleInterpreter(Interpreter):
    """Interprets console operations with actual I/O"""
    
    def __init__(self):
        self.output_log = []
        self.input_queue = []
    
    def add_input(self, s: str):
        """Add simulated input"""
        self.input_queue.append(s)
    
    def run(self, functor: FunctorF) -> Value:
        """Run console operation"""
        if isinstance(functor, PrintLine):
            self.output_log.append(functor.message)
            print(f"  [Console] {functor.message}")
            return functor.next_computation.interpret(self)
        
        elif isinstance(functor, ReadLine):
            if self.input_queue:
                input_val = self.input_queue.pop(0)
                print(f"  [Console] < {input_val}")
                next_free = functor.continuation(input_val)
                return next_free.interpret(self)
            else:
                print(f"  [Console] < (no input)")
                next_free = functor.continuation("")
                return next_free.interpret(self)
        
        raise RuntimeError(f"Unknown console operation: {functor}")


# Console Logger Interpreter (different interpretation!)
class ConsoleLoggerInterpreter(Interpreter):
    """Interprets console operations as pure logging (no actual I/O)"""
    
    def __init__(self):
        self.log = []
    
    def run(self, functor: FunctorF) -> Value:
        """Log operations without executing"""
        if isinstance(functor, PrintLine):
            self.log.append(f"PRINT: {functor.message}")
            return functor.next_computation.interpret(self)
        
        elif isinstance(functor, ReadLine):
            self.log.append("READ: <input>")
            # Provide dummy input
            next_free = functor.continuation("dummy")
            return next_free.interpret(self)
        
        raise RuntimeError(f"Unknown console operation: {functor}")



# DSL 2: KEY-VALUE STORE


@dataclass
class KVStoreF(FunctorF):
    """Key-Value store functor"""
    pass


@dataclass
class Get(KVStoreF):
    """Get value for key"""
    key: str
    continuation: Callable[[Optional[Value]], Free]
    
    def fmap_free(self, f: Callable[[Free], Free]) -> KVStoreF:
        return Get(self.key, lambda v: f(self.continuation(v)))
    
    def run_step(self, interpreter: Interpreter) -> Free:
        return Pure(UnitValue())
    
    def __str__(self):
        return f"Get({self.key})"


@dataclass
class Put(KVStoreF):
    """Put value for key"""
    key: str
    value: Value
    next_computation: Free
    
    def fmap_free(self, f: Callable[[Free], Free]) -> KVStoreF:
        return Put(self.key, self.value, f(self.next_computation))
    
    def run_step(self, interpreter: Interpreter) -> Free:
        return self.next_computation
    
    def __str__(self):
        return f"Put({self.key}, {self.value})"


@dataclass
class Delete(KVStoreF):
    """Delete key"""
    key: str
    next_computation: Free
    
    def fmap_free(self, f: Callable[[Free], Free]) -> KVStoreF:
        return Delete(self.key, f(self.next_computation))
    
    def run_step(self, interpreter: Interpreter) -> Free:
        return self.next_computation
    
    def __str__(self):
        return f"Delete({self.key})"


# KV Store DSL helper functions
def get(key: str) -> Free:
    """Smart constructor: get value"""
    return Impure(Get(key, lambda v: Pure(v if v else UnitValue())))


def put(key: str, value: Value) -> Free:
    """Smart constructor: put value"""
    return Impure(Put(key, value, Pure(UnitValue())))


def delete(key: str) -> Free:
    """Smart constructor: delete key"""
    return Impure(Delete(key, Pure(UnitValue())))


# KV Store Interpreter
class KVStoreInterpreter(Interpreter):
    """Interprets KV operations with in-memory dict"""
    
    def __init__(self):
        self.store: Dict[str, Value] = {}
    
    def run(self, functor: FunctorF) -> Value:
        """Run KV operation"""
        if isinstance(functor, Get):
            val = self.store.get(functor.key)
            print(f"  [KVStore] GET {functor.key} = {val}")
            next_free = functor.continuation(val)
            return next_free.interpret(self)
        
        elif isinstance(functor, Put):
            self.store[functor.key] = functor.value
            print(f"  [KVStore] PUT {functor.key} = {functor.value}")
            return functor.next_computation.interpret(self)
        
        elif isinstance(functor, Delete):
            if functor.key in self.store:
                del self.store[functor.key]
            print(f"  [KVStore] DELETE {functor.key}")
            return functor.next_computation.interpret(self)
        
        raise RuntimeError(f"Unknown KV operation: {functor}")



# DSL 3: TELEMETRY (Logging/Metrics)


@dataclass
class TelemetryF(FunctorF):
    """Telemetry functor"""
    pass


@dataclass
class Log(TelemetryF):
    """Log a message"""
    level: str  # INFO, WARN, ERROR
    message: str
    next_computation: Free
    
    def fmap_free(self, f: Callable[[Free], Free]) -> TelemetryF:
        return Log(self.level, self.message, f(self.next_computation))
    
    def run_step(self, interpreter: Interpreter) -> Free:
        return self.next_computation
    
    def __str__(self):
        return f"Log[{self.level}]({self.message})"


@dataclass
class Metric(TelemetryF):
    """Record a metric"""
    name: str
    value: float
    next_computation: Free
    
    def fmap_free(self, f: Callable[[Free], Free]) -> TelemetryF:
        return Metric(self.name, self.value, f(self.next_computation))
    
    def run_step(self, interpreter: Interpreter) -> Free:
        return self.next_computation
    
    def __str__(self):
        return f"Metric({self.name}={self.value})"


# Telemetry DSL helpers
def log_info(msg: str) -> Free:
    return Impure(Log("INFO", msg, Pure(UnitValue())))


def log_error(msg: str) -> Free:
    return Impure(Log("ERROR", msg, Pure(UnitValue())))


def record_metric(name: str, value: float) -> Free:
    return Impure(Metric(name, value, Pure(UnitValue())))


# Telemetry Interpreter
class TelemetryInterpreter(Interpreter):
    """Interprets telemetry operations"""
    
    def __init__(self):
        self.logs = []
        self.metrics = {}
    
    def run(self, functor: FunctorF) -> Value:
        if isinstance(functor, Log):
            self.logs.append(f"[{functor.level}] {functor.message}")
            print(f"  [Telemetry] {functor.level}: {functor.message}")
            return functor.next_computation.interpret(self)
        
        elif isinstance(functor, Metric):
            self.metrics[functor.name] = functor.value
            print(f"  [Telemetry] Metric {functor.name} = {functor.value}")
            return functor.next_computation.interpret(self)
        
        raise RuntimeError(f"Unknown telemetry operation: {functor}")



# COPRODUCT OF FUNCTORS (Extensible Effects)


@dataclass
class Coproduct(FunctorF):
    """Coproduct of two functors: F + G
    
    This allows combining multiple DSLs!
    """
    left: Optional[FunctorF] = None
    right: Optional[FunctorF] = None
    
    def fmap_free(self, f: Callable[[Free], Free]) -> 'Coproduct':
        if self.left:
            return Coproduct(left=self.left.fmap_free(f))
        elif self.right:
            return Coproduct(right=self.right.fmap_free(f))
        raise RuntimeError("Empty coproduct")
    
    def run_step(self, interpreter: Interpreter) -> Free:
        if self.left:
            return self.left.run_step(interpreter)
        elif self.right:
            return self.right.run_step(interpreter)
        raise RuntimeError("Empty coproduct")
    
    def __str__(self):
        if self.left:
            return f"Left({self.left})"
        elif self.right:
            return f"Right({self.right})"
        return "EmptyCoproduct"


def inject_left(f: FunctorF) -> Coproduct:
    """Inject into left side of coproduct"""
    return Coproduct(left=f)


def inject_right(f: FunctorF) -> Coproduct:
    """Inject into right side of coproduct"""
    return Coproduct(right=f)


# Coproduct Interpreter
class CoproductInterpreter(Interpreter):
    """Interprets coproduct by delegating to sub-interpreters"""
    
    def __init__(self, left_interp: Interpreter, right_interp: Interpreter):
        self.left_interp = left_interp
        self.right_interp = right_interp
    
    def run(self, functor: FunctorF) -> Value:
        if isinstance(functor, Coproduct):
            if functor.left:
                return self.left_interp.run(functor.left)
            elif functor.right:
                return self.right_interp.run(functor.right)
        
        raise RuntimeError(f"Cannot interpret: {functor}")



# PROGRAM COMBINATORS


def sequence_free(programs: List[Free]) -> Free:
    """Sequence a list of Free programs"""
    if not programs:
        return Pure(UnitValue())
    
    first = programs[0]
    rest = programs[1:]
    
    if not rest:
        return first
    
    # first >>= λ_. sequence rest
    return first.bind(lambda _: sequence_free(rest))


def replicate_free(n: int, program: Free) -> Free:
    """Repeat a program n times"""
    programs = [program for _ in range(n)]
    return sequence_free(programs)



# DEMONSTRATION


def demo():
    print("=" * 70)
    print("COOL with FREE MONADS")
    print("=" * 70)
    print("Free Monads: The Ultimate Abstraction")
    print("- Get monads 'for free' from any functor")
    print("- Separate DESCRIPTION from INTERPRETATION")
    print("- Build composable DSLs")
    print("- Multiple interpreters for same program")
    print("=" * 70)
    
    # Example 1: Simple Console DSL
    print("\n" + "=" * 70)
    print("Example 1: Console DSL - Free Monad Basics")
    print("=" * 70)
    
    print("Building a program (pure description):")
    
    # Program: print "Hello" then print "World"
    program1 = print_line("Hello").bind(lambda _: print_line("World"))
    
    print(f"  program = {program1}")
    print("\nThis is just a DATA STRUCTURE - not executed yet!")
    
    print("\nNow interpret with ConsoleInterpreter:")
    console_interp = ConsoleInterpreter()
    result = program1.interpret(console_interp)
    print(f"  Result: {result}")
    
    print("\nSame program, different interpreter (Logger):")
    logger_interp = ConsoleLoggerInterpreter()
    result2 = program1.interpret(logger_interp)
    print(f"  Log: {logger_interp.log}")
    
    # Example 2: Interactive Program
    print("\n" + "=" * 70)
    print("Example 2: Interactive Console Program")
    print("=" * 70)
    
    print("Program with input:")
    
    # Ask name, greet
    def greet_program():
        return print_line("What is your name?").bind(lambda _:
            read_line().bind(lambda name_val:
                print_line(f"Hello, {name_val}!") if isinstance(name_val, StringValue)
                else print_line("Hello, stranger!")
            )
        )
    
    program2 = greet_program()
    
    print("\nExecuting with simulated input:")
    console_interp2 = ConsoleInterpreter()
    console_interp2.add_input("Alice")
    result = program2.interpret(console_interp2)
    
    # Example 3: Key-Value Store DSL
    print("\n" + "=" * 70)
    print("Example 3: Key-Value Store DSL")
    print("=" * 70)
    
    print("Building database operations:")
    
    # Program: put user, get user, delete user
    program3 = (
        put("user:1", StringValue("Alice"))
        .bind(lambda _: put("user:2", StringValue("Bob")))
        .bind(lambda _: get("user:1"))
        .bind(lambda val: print_line(f"Found: {val}") if isinstance(val, StringValue) 
              else Pure(UnitValue()))
        .bind(lambda _: delete("user:1"))
        .bind(lambda _: get("user:1"))
    )
    
    print("  put user:1 'Alice'")
    print("  put user:2 'Bob'")
    print("  get user:1")
    print("  delete user:1")
    print("  get user:1")
    
    print("\nInterpreting with KVStoreInterpreter:")
    kv_interp = KVStoreInterpreter()
    
    # Need combined interpreter for Console + KVStore
    class CombinedInterpreter(Interpreter):
        def __init__(self, console, kvstore):
            self.console = console
            self.kvstore = kvstore
        
        def run(self, functor):
            if isinstance(functor, (PrintLine, ReadLine)):
                return self.console.run(functor)
            elif isinstance(functor, (Get, Put, Delete)):
                return self.kvstore.run(functor)
            raise RuntimeError(f"Unknown operation: {functor}")
    
    combined = CombinedInterpreter(ConsoleInterpreter(), kv_interp)
    result = program3.interpret(combined)
    
    print(f"\nFinal store state: {kv_interp.store}")
    
    # Example 4: Telemetry DSL
    print("\n" + "=" * 70)
    print("Example 4: Telemetry/Logging DSL")
    print("=" * 70)
    
    print("Program with logging:")
    
    program4 = (
        log_info("Starting computation")
        .bind(lambda _: record_metric("operations", 1.0))
        .bind(lambda _: log_info("Computation complete"))
        .bind(lambda _: record_metric("operations", 2.0))
        .bind(lambda _: log_error("Something went wrong!"))
    )
    
    print("\nInterpreting:")
    telem_interp = TelemetryInterpreter()
    result = program4.interpret(telem_interp)
    
    print(f"\nCollected logs: {len(telem_interp.logs)}")
    print(f"Metrics: {telem_interp.metrics}")
    
    # Example 5: Composing Programs
    print("\n" + "=" * 70)
    print("Example 5: Composing Free Programs")
    print("=" * 70)
    
    print("Free monad bind allows composition:")
    
    # Define reusable components
    def save_user(name: str) -> Free:
        return (
            log_info(f"Saving user: {name}")
            .bind(lambda _: put(f"user:{name}", StringValue(name)))
            .bind(lambda _: log_info(f"User {name} saved"))
        )
    
    def load_user(name: str) -> Free:
        return (
            log_info(f"Loading user: {name}")
            .bind(lambda _: get(f"user:{name}"))
        )
    
    # Compose them
    workflow = (
        save_user("Alice")
        .bind(lambda _: save_user("Bob"))
        .bind(lambda _: load_user("Alice"))
        .bind(lambda _: load_user("Charlie"))
    )
    
    print("Workflow:")
    print("  save_user('Alice')")
    print("  save_user('Bob')")
    print("  load_user('Alice')")
    print("  load_user('Charlie')")
    
    print("\nExecuting workflow:")
    
    class FullInterpreter(Interpreter):
        def __init__(self):
            self.kv = KVStoreInterpreter()
            self.telem = TelemetryInterpreter()
            self.console = ConsoleInterpreter()
        
        def run(self, functor):
            if isinstance(functor, (Get, Put, Delete)):
                return self.kv.run(functor)
            elif isinstance(functor, (Log, Metric)):
                return self.telem.run(functor)
            elif isinstance(functor, (PrintLine, ReadLine)):
                return self.console.run(functor)
            raise RuntimeError(f"Unknown: {functor}")
    
    full_interp = FullInterpreter()
    result = workflow.interpret(full_interp)
    
    # Example 6: Sequence and Replicate
    print("\n" + "=" * 70)
    print("Example 6: Program Combinators")
    print("=" * 70)
    
    print("Sequence: run list of programs")
    
    programs = [
        print_line("First"),
        print_line("Second"),
        print_line("Third")
    ]
    
    sequenced = sequence_free(programs)
    
    print("\nExecuting sequence:")
    console = ConsoleInterpreter()
    sequenced.interpret(console)
    
    print("\nReplicate: repeat program n times")
    repeated = replicate_free(3, print_line("Repeated!"))
    
    print("\nExecuting replicate(3):")
    console2 = ConsoleInterpreter()
    repeated.interpret(console2)
    
    # Example 7: Multiple Interpretations
    print("\n" + "=" * 70)
    print("Example 7: Same Program, Multiple Interpretations")
    print("=" * 70)
    
    print("The POWER of Free Monads: interpret the same program differently!")
    
    simple_prog = (
        log_info("Starting")
        .bind(lambda _: put("counter", IntValue(0)))
        .bind(lambda _: log_info("Done"))
    )
    
    print("\nInterpretation 1: Real execution")
    real_interp = FullInterpreter()
    simple_prog.interpret(real_interp)
    
    print("\nInterpretation 2: Just count operations")
    
    class CountingInterpreter(Interpreter):
        def __init__(self):
            self.count = 0
        
        def run(self, functor):
            self.count += 1
            if hasattr(functor, 'next_computation'):
                return functor.next_computation.interpret(self)
            elif hasattr(functor, 'continuation'):
                return functor.continuation(None).interpret(self)
            return UnitValue()
    
    counter = CountingInterpreter()
    simple_prog.interpret(counter)
    print(f"  Total operations: {counter.count}")
    
    print("\nInterpretation 3: Dry run (no effects)")
    
    class DryRunInterpreter(Interpreter):
        def __init__(self):
            self.plan = []
        
        def run(self, functor):
            self.plan.append(str(functor))
            if hasattr(functor, 'next_computation'):
                return functor.next_computation.interpret(self)
            elif hasattr(functor, 'continuation'):
                return functor.continuation(None).interpret(self)
            return UnitValue()
    
    dry_run = DryRunInterpreter()
    simple_prog.interpret(dry_run)
    print(f"  Execution plan:")
    for step in dry_run.plan:
        print(f"    - {step}")
    
    # Example 8: Testing with Mock Interpreter
    print("\n" + "=" * 70)
    print("Example 8: Testing with Mock Interpreter")
    print("=" * 70)
    
    print("Free monads make testing EASY - just use mock interpreter!")
    
    def user_workflow(user_id: str) -> Free:
        """Production code using Free monad"""
        return (
            log_info(f"Processing user {user_id}")
            .bind(lambda _: get(f"user:{user_id}"))
            .bind(lambda user: 
                log_info(f"Found user: {user}") if user 
                else log_error(f"User {user_id} not found")
            )
            .bind(lambda _: record_metric("users_processed", 1.0))
        )
    
    print("Production workflow:")
    print("  log_info('Processing user...')")
    print("  get('user:123')")
    print("  log_info('Found user...')")
    print("  record_metric('users_processed', 1.0)")
    
    print("\nTest with mock interpreter:")
    
    class MockInterpreter(Interpreter):
        def __init__(self):
            self.mock_store = {"user:123": StringValue("Test User")}
            self.logs = []
            self.metrics = []
        
        def run(self, functor):
            if isinstance(functor, Log):
                self.logs.append(functor.message)
                return functor.next_computation.interpret(self)
            elif isinstance(functor, Get):
                val = self.mock_store.get(functor.key)
                return functor.continuation(val).interpret(self)
            elif isinstance(functor, Metric):
                self.metrics.append((functor.name, functor.value))
                return functor.next_computation.interpret(self)
            return UnitValue()
    
    mock = MockInterpreter()
    user_workflow("123").interpret(mock)
    
    print(f"\n  Logs: {mock.logs}")
    print(f"  Metrics: {mock.metrics}")
    print("  + Tested without any real I/O!")
    
    # Example 9: Optimization Interpreter
    print("\n" + "=" * 70)
    print("Example 9: Optimization Interpreter")
    print("=" * 70)
    
    print("Different interpreter can OPTIMIZE the program!")
    
    # Program with redundant operations
    redundant = (
        put("x", IntValue(1))
        .bind(lambda _: put("x", IntValue(2)))  # Overwrites!
        .bind(lambda _: put("x", IntValue(3)))  # Overwrites again!
        .bind(lambda _: get("x"))
    )
    
    print("Program:")
    print("  put x=1")
    print("  put x=2")
    print("  put x=3")
    print("  get x")
    
    class OptimizingInterpreter(Interpreter):
        """Optimizes away redundant puts"""
        def __init__(self):
            self.store = {}
            self.ops_executed = 0
        
        def run(self, functor):
            if isinstance(functor, Put):
                # Skip if next operation also puts to same key
                self.store[functor.key] = functor.value
                self.ops_executed += 1
                return functor.next_computation.interpret(self)
            elif isinstance(functor, Get):
                self.ops_executed += 1
                val = self.store.get(functor.key)
                return functor.continuation(val).interpret(self)
            return UnitValue()
    
    print("\nNaive interpreter (executes all):")
    naive = KVStoreInterpreter()
    redundant.interpret(naive)
    print(f"  Store: {naive.store}")
    
    print("\nOptimizing interpreter:")
    opt = OptimizingInterpreter()
    redundant.interpret(opt)
    print(f"  Operations executed: {opt.ops_executed}")
    print(f"  Store: {opt.store}")
    print("  -> Same result, could be more efficient!")
    
    # Example 10: Building Complex DSLs
    print("\n" + "=" * 70)
    print("Example 10: Real-World Example - Web API DSL")
    print("=" * 70)
    
    print("Free monads excel at building domain-specific languages")
    
    # Web API operations
    @dataclass
    class HttpGetF(FunctorF):
        url: str
        continuation: Callable[[str], Free]
        
        def fmap_free(self, f):
            return HttpGetF(self.url, lambda s: f(self.continuation(s)))
        
        def run_step(self, interpreter):
            return Pure(UnitValue())
        
        def __str__(self):
            return f"HttpGet({self.url})"
    
    @dataclass
    class HttpPostF(FunctorF):
        url: str
        data: str
        next_computation: Free
        
        def fmap_free(self, f):
            return HttpPostF(self.url, self.data, f(self.next_computation))
        
        def run_step(self, interpreter):
            return self.next_computation
        
        def __str__(self):
            return f"HttpPost({self.url}, {self.data})"
    
    def http_get(url: str) -> Free:
        return Impure(HttpGetF(url, lambda resp: Pure(StringValue(resp))))
    
    def http_post(url: str, data: str) -> Free:
        return Impure(HttpPostF(url, data, Pure(UnitValue())))
    
    # API workflow
    api_workflow = (
        log_info("Starting API request")
        .bind(lambda _: http_get("/api/users/1"))
        .bind(lambda user: log_info(f"Fetched user: {user}"))
        .bind(lambda _: http_post("/api/analytics", "event=page_view"))
        .bind(lambda _: log_info("Analytics sent"))
    )
    
    print("\nAPI Workflow:")
    print("  log_info('Starting API request')")
    print("  http_get('/api/users/1')")
    print("  log_info('Fetched user: ...')")
    print("  http_post('/api/analytics', 'event=page_view')")
    print("  log_info('Analytics sent')")
    
    print("\nMock API Interpreter (for testing):")
    
    class MockHttpInterpreter(Interpreter):
        def __init__(self):
            self.telem = TelemetryInterpreter()
            self.requests = []
        
        def run(self, functor):
            if isinstance(functor, HttpGetF):
                self.requests.append(f"GET {functor.url}")
                # Return mock data
                mock_response = '{"id": 1, "name": "Alice"}'
                return functor.continuation(mock_response).interpret(self)
            elif isinstance(functor, HttpPostF):
                self.requests.append(f"POST {functor.url}")
                return functor.next_computation.interpret(self)
            elif isinstance(functor, (Log, Metric)):
                return self.telem.run(functor)
            return UnitValue()
    
    mock_http = MockHttpInterpreter()
    api_workflow.interpret(mock_http)
    
    print(f"\n  HTTP Requests made:")
    for req in mock_http.requests:
        print(f"    - {req}")
    print(f"  Logs: {len(mock_http.telem.logs)}")
    print("  + Tested entire workflow without real HTTP!")
    
    # Summary
    print("\n" + "=" * 70)
    print("CATEGORICAL PROPERTIES DEMONSTRATED:")
    print("=" * 70)
    print("+ Free Monad: Free F A = Pure A | Impure (F (Free F A))")
    print("+ Initial Algebra: Gives monad structure 'for free'")
    print("+ Separation of Concerns: Description vs Interpretation")
    print("+ F-Algebra: Interpreter is a functor algebra F A -> A")
    print("+ Multiple Interpreters: Same program, different meanings")
    print("+ Composability: Programs compose via bind")
    print("+ Extensibility: Coproduct of functors for multiple DSLs")
    print("+ Testability: Mock interpreters for pure testing")
    print("+ Optimization: Interpreters can transform/optimize")
    print("+ DSL Building: Natural way to create domain languages")
    print("=" * 70)
    
    print("\nKey Insights:")
    print("- Free monads: structure without commitment")
    print("- Program = data structure (AST)")
    print("- Interpreter = meaning (semantics)")
    print("- One program -> many interpretations")
    
    print("\nThe Free Monad Triangle:")
    print("  Functor F -> Free F -> Monad")
    print("  (base ops) (structure) (composition)")
    
    print("\nPractical Benefits:")
    print("1. TESTING: Mock interpreters, no real I/O")
    print("2. DEBUGGING: Inspect program structure before running")
    print("3. OPTIMIZATION: Transform programs before execution")
    print("4. COMPOSITION: Build complex from simple")
    print("5. FLEXIBILITY: Swap interpreters at runtime")
    
    print("\nCommon Use Cases:")
    print("- Web APIs and HTTP clients")
    print("- Database access layers")
    print("- Game engines (separate logic from rendering)")
    print("- Configuration languages")
    print("- Protocol implementations")
    print("- Workflow engines")
    
    print("\nThe Power:")
    print("  'Free' means we get monadic structure")
    print("  WITHOUT committing to specific implementation!")
    print("  Pure description, delayed execution.")
    
    print("\n" + "=" * 70)
    print("COMPARISON TABLE:")
    print("=" * 70)
    print("| Approach       | Pros                  | Cons                |")
    print("|----------------|------------------------|---------------------|")
    print("| Direct Effects | Simple, fast          | Hard to test/mock   |")
    print("| Monad Stack    | Composable effects    | Fixed at compile    |")
    print("| Free Monad     | Ultimate flexibility  | Some overhead       |")
    print("=" * 70)
    
    print("\nWhen to use Free Monads:")
    print("+ Need multiple interpretations")
    print("+ Testing is critical")
    print("+ Building a DSL")
    print("+ Need to inspect/transform programs")
    print("+ Want maximum flexibility")
    
    print("\nWhen NOT to use Free Monads:")
    print("- Simple, straightforward code")
    print("- Performance is absolutely critical")
    print("- Only one interpretation needed")
    print("- Team unfamiliar with advanced FP")
    
    print("\n" + "=" * 70)
    print("The Free Monad is the ULTIMATE abstraction:")
    print("  'Free' = No commitment")
    print("  'Monad' = Composable structure")
    print("  Result = Pure, flexible, testable code!")
    print("=" * 70)


if __name__ == "__main__":
    demo()
