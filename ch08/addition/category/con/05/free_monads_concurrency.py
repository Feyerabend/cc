import threading
import time
from typing import Callable, TypeVar, Generic, Union
from abc import ABC, abstractmethod
from dataclasses import dataclass

A = TypeVar('A')
B = TypeVar('B')

# FREE MONADS
# Idea: Separate program DESCRIPTION from EXECUTION
#
# 1. Define operations as data (an AST)
# 2. Build programs by composing operations
# 3. Choose interpreter later (sync/async/parallel/mock/test)
#
# Free[F, A] = Pure(A) | Free(F[Free[F, A]])
#
# This is "free" because it's the "free monad" over functor F,
# meaning it has no additional constraints beyond being a monad.

# STEP 1: Define Operation Language (DSL)

class FileOp(ABC):
    """Base class for file operations - our functor F"""
    pass

@dataclass
class ReadFile(FileOp):
    """Operation: read file"""
    path: str
    next: Callable[[str], 'Free[FileOp, A]']

@dataclass
class WriteFile(FileOp):
    """Operation: write file"""
    path: str
    content: str
    next: Callable[[None], 'Free[FileOp, A]']

@dataclass
class DeleteFile(FileOp):
    """Operation: delete file"""
    path: str
    next: Callable[[None], 'Free[FileOp, A]']

@dataclass
class Sleep(FileOp):
    """Operation: sleep (for simulating delays)"""
    duration: float
    next: Callable[[None], 'Free[FileOp, A]']


# STEP 2: Free Monad Structure

class Free(Generic[A], ABC):
    """
    Free Monad over FileOp functor
    
    Free[A] = Pure(A)               -- finished with value A
            | Suspend(FileOp)       -- suspended operation
    """
    
    @abstractmethod
    def fold(self, pure_fn: Callable[[A], B], 
             suspend_fn: Callable[[FileOp], B]) -> B:
        """Fold/pattern match on the structure"""
        pass
    
    def bind(self, f: Callable[[A], 'Free[B]']) -> 'Free[B]':
        """Monadic bind - sequences operations"""
        def pure_case(a: A) -> 'Free[B]':
            return f(a)
        
        def suspend_case(op: FileOp) -> 'Free[B]':
            # Continue with modified next continuation
            if isinstance(op, ReadFile):
                return Suspend(ReadFile(op.path, lambda content: op.next(content).bind(f)))
            elif isinstance(op, WriteFile):
                return Suspend(WriteFile(op.path, op.content, lambda _: op.next(None).bind(f)))
            elif isinstance(op, DeleteFile):
                return Suspend(DeleteFile(op.path, lambda _: op.next(None).bind(f)))
            elif isinstance(op, Sleep):
                return Suspend(Sleep(op.duration, lambda _: op.next(None).bind(f)))
            else:
                raise TypeError(f"Unknown operation: {type(op)}")
        
        return self.fold(pure_case, suspend_case)
    
    def fmap(self, f: Callable[[A], B]) -> 'Free[B]':
        """Functor map"""
        return self.bind(lambda a: Pure(f(a)))


@dataclass
class Pure(Free[A]):
    """Terminal value - computation finished"""
    value: A
    
    def fold(self, pure_fn: Callable[[A], B], 
             suspend_fn: Callable[[FileOp], B]) -> B:
        return pure_fn(self.value)


@dataclass
class Suspend(Free[A]):
    """Suspended operation - computation continues"""
    op: FileOp
    
    def fold(self, pure_fn: Callable[[A], B], 
             suspend_fn: Callable[[FileOp], B]) -> B:
        return suspend_fn(self.op)


# STEP 3: Smart Constructors (DSL)

def read_file(path: str) -> Free[str]:
    """DSL: read file operation"""
    return Suspend(ReadFile(path, lambda content: Pure(content)))

def write_file(path: str, content: str) -> Free[None]:
    """DSL: write file operation"""
    return Suspend(WriteFile(path, content, lambda _: Pure(None)))

def delete_file(path: str) -> Free[None]:
    """DSL: delete file operation"""
    return Suspend(DeleteFile(path, lambda _: Pure(None)))

def sleep(duration: float) -> Free[None]:
    """DSL: sleep operation"""
    return Suspend(Sleep(duration, lambda _: Pure(None)))

def pure(value: A) -> Free[A]:
    """DSL: pure value"""
    return Pure(value)


# STEP 4: Interpreters

class Interpreter(ABC):
    """Base interpreter interface"""
    
    @abstractmethod
    def run(self, program: Free[A]) -> A:
        """Execute the free monad program"""
        pass


class SyncInterpreter(Interpreter):
    """Synchronous interpreter - runs operations immediately"""
    
    def __init__(self, filesystem: dict):
        self.filesystem = filesystem
    
    def run(self, program: Free[A]) -> A:
        """Execute synchronously"""
        def pure_case(a):
            return a
        
        def suspend_case(op):
            if isinstance(op, ReadFile):
                print(f"  [Sync] Reading '{op.path}'")
                content = self.filesystem.get(op.path, "")
                return self.run(op.next(content))
            
            elif isinstance(op, WriteFile):
                print(f"  [Sync] Writing to '{op.path}'")
                self.filesystem[op.path] = op.content
                return self.run(op.next(None))
            
            elif isinstance(op, DeleteFile):
                print(f"  [Sync] Deleting '{op.path}'")
                self.filesystem.pop(op.path, None)
                return self.run(op.next(None))
            
            elif isinstance(op, Sleep):
                print(f"  [Sync] Sleeping {op.duration}s")
                time.sleep(op.duration)
                return self.run(op.next(None))
            
            else:
                raise TypeError(f"Unknown operation: {type(op)}")
        
        return program.fold(pure_case, suspend_case)


class AsyncInterpreter(Interpreter):
    """Asynchronous interpreter - runs operations in threads"""
    
    def __init__(self, filesystem: dict):
        self.filesystem = filesystem
        self.lock = threading.Lock()
    
    def run(self, program: Free[A]) -> A:
        """Execute asynchronously (each operation in thread)"""
        def pure_case(a):
            return a
        
        def suspend_case(op):
            result = None
            
            def execute():
                nonlocal result
                if isinstance(op, ReadFile):
                    print(f"  [Async] Reading '{op.path}' (thread)")
                    with self.lock:
                        content = self.filesystem.get(op.path, "")
                    result = self.run(op.next(content))
                
                elif isinstance(op, WriteFile):
                    print(f"  [Async] Writing to '{op.path}' (thread)")
                    with self.lock:
                        self.filesystem[op.path] = op.content
                    result = self.run(op.next(None))
                
                elif isinstance(op, DeleteFile):
                    print(f"  [Async] Deleting '{op.path}' (thread)")
                    with self.lock:
                        self.filesystem.pop(op.path, None)
                    result = self.run(op.next(None))
                
                elif isinstance(op, Sleep):
                    print(f"  [Async] Sleeping {op.duration}s (thread)")
                    time.sleep(op.duration)
                    result = self.run(op.next(None))
                
                else:
                    raise TypeError(f"Unknown operation: {type(op)}")
            
            thread = threading.Thread(target=execute)
            thread.start()
            thread.join()
            return result
        
        return program.fold(pure_case, suspend_case)


class MockInterpreter(Interpreter):
    """Mock interpreter - for testing without side effects"""
    
    def __init__(self):
        self.operations_log = []
    
    def run(self, program: Free[A]) -> A:
        """Execute in mock mode - just log operations"""
        def pure_case(a):
            return a
        
        def suspend_case(op):
            if isinstance(op, ReadFile):
                self.operations_log.append(f"READ {op.path}")
                return self.run(op.next(f"mock_content_of_{op.path}"))
            
            elif isinstance(op, WriteFile):
                self.operations_log.append(f"WRITE {op.path}: {op.content[:20]}...")
                return self.run(op.next(None))
            
            elif isinstance(op, DeleteFile):
                self.operations_log.append(f"DELETE {op.path}")
                return self.run(op.next(None))
            
            elif isinstance(op, Sleep):
                self.operations_log.append(f"SLEEP {op.duration}s")
                return self.run(op.next(None))
            
            else:
                raise TypeError(f"Unknown operation: {type(op)}")
        
        return program.fold(pure_case, suspend_case)


class OptimizingInterpreter(Interpreter):
    """Optimising interpreter - parallelises independent operations"""
    
    def __init__(self, filesystem: dict):
        self.filesystem = filesystem
        self.lock = threading.Lock()
    
    def run(self, program: Free[A]) -> A:
        """
        Execute with optimisation: detect independent operations
        and run them in parallel
        """
        # Collect independent operations
        ops_batch = self._collect_independent_ops(program)
        
        if len(ops_batch) > 1:
            print(f"  [Optimising] Found {len(ops_batch)} independent ops, parallelising!")
            return self._run_parallel(ops_batch)
        else:
            return self._run_sequential(program)
    
    def _collect_independent_ops(self, program: Free[A]) -> list:
        """Simple heuristic: collect consecutive reads"""
        # In real implementation, would do dependency analysis
        # For demo, just return single op
        return [program]
    
    def _run_sequential(self, program: Free[A]) -> A:
        def pure_case(a):
            return a
        
        def suspend_case(op):
            if isinstance(op, ReadFile):
                print(f"  [Optimising] Reading '{op.path}'")
                with self.lock:
                    content = self.filesystem.get(op.path, "")
                return self._run_sequential(op.next(content))
            
            elif isinstance(op, WriteFile):
                print(f"  [Optimising] Writing to '{op.path}'")
                with self.lock:
                    self.filesystem[op.path] = op.content
                return self._run_sequential(op.next(None))
            
            elif isinstance(op, DeleteFile):
                print(f"  [Optimising] Deleting '{op.path}'")
                with self.lock:
                    self.filesystem.pop(op.path, None)
                return self._run_sequential(op.next(None))
            
            elif isinstance(op, Sleep):
                time.sleep(op.duration)
                return self._run_sequential(op.next(None))
            
            else:
                raise TypeError(f"Unknown operation: {type(op)}")
        
        return program.fold(pure_case, suspend_case)
    
    def _run_parallel(self, programs: list) -> A:
        # Simplified - would actually parallelize
        return self._run_sequential(programs[0])


# STEP 5: Example Programs

def backup_program() -> Free[str]:
    """
    Program: backup a file
    Note: This is just DESCRIPTION, not execution!
    """
    return (
        read_file("data.txt")
        .bind(lambda content:
            write_file("backup.txt", content)
            .bind(lambda _:
                pure(f"Backed up {len(content)} bytes")
            )
        )
    )


def process_pipeline() -> Free[str]:
    """Program: read -> process -> write"""
    return (
        read_file("input.txt")
        .bind(lambda content:
            write_file("output.txt", content.upper())
            .bind(lambda _:
                pure(f"Processed: {content[:20]}...")
            )
        )
    )


def slow_operation() -> Free[str]:
    """Program with delays"""
    return (
        sleep(0.3)
        .bind(lambda _:
            read_file("data.txt")
            .bind(lambda content:
                sleep(0.3)
                .bind(lambda _:
                    pure(content)
                )
            )
        )
    )


# DEMONSTRATIONS

def demo_basic_interpretation():
    """Show same program, different interpreters"""
    print("--- Same Program, Different Interpreters ---\n")
    
    # Build the program (just description!)
    program = backup_program()
    print("Program built (not executed yet!)\n")
    
    # Interpreter 1: Synchronous
    print("1. Synchronous Interpreter:")
    fs_sync = {"data.txt": "Hello, World!"}
    interp_sync = SyncInterpreter(fs_sync)
    result = interp_sync.run(program)
    print(f"   Result: {result}\n")
    
    # Interpreter 2: Mock (for testing)
    print("2. Mock Interpreter (for testing):")
    interp_mock = MockInterpreter()
    result = interp_mock.run(program)
    print(f"   Result: {result}")
    print(f"   Operations logged: {interp_mock.operations_log}\n")


def demo_monadic_composition():
    """Show how free monads compose with bind"""
    print("--- Monadic Composition ---\n")
    
    # Build complex program by composing
    def duplicate_file(src: str, dst: str) -> Free[str]:
        return (
            read_file(src)
            .bind(lambda content:
                write_file(dst, content)
                .bind(lambda _:
                    pure(f"Duplicated {src} to {dst}")
                )
            )
        )
    
    def cleanup(path: str) -> Free[str]:
        return (
            delete_file(path)
            .bind(lambda _:
                pure(f"Cleaned up {path}")
            )
        )
    
    # Compose operations
    program = (
        duplicate_file("source.txt", "copy1.txt")
        .bind(lambda msg1:
            duplicate_file("source.txt", "copy2.txt")
            .bind(lambda msg2:
                cleanup("source.txt")
                .bind(lambda msg3:
                    pure(f"{msg1}, {msg2}, {msg3}")
                )
            )
        )
    )
    
    print("Composed program: duplicate twice, then cleanup\n")
    
    fs = {"source.txt": "Important data"}
    interp = SyncInterpreter(fs)
    result = interp.run(program)
    print(f"\nResult: {result}")
    print(f"Filesystem: {fs}\n")


def demo_interpreter_switching():
    """Show power: switch interpreters without changing program"""
    print("--- Interpreter Switching (Same Program!) ---\n")
    
    program = process_pipeline()
    
    print("Program: read input.txt -> uppercase -> write output.txt\n")
    
    # Test with mock first
    print("1. Test with Mock Interpreter:")
    mock = MockInterpreter()
    result = mock.run(program)
    print(f"   Operations: {mock.operations_log}")
    print(f"   Would produce: {result}\n")
    
    # Then run with real interpreter
    print("2. Run with Real Sync Interpreter:")
    fs = {"input.txt": "hello world"}
    interp = SyncInterpreter(fs)
    result = interp.run(program)
    print(f"   Result: {result}")
    print(f"   Filesystem: {fs}\n")


def demo_performance_comparison():
    """Compare sync vs async interpreters"""
    print("--- Performance: Sync vs Async Interpreters ---\n")
    
    program = slow_operation()
    
    # Sync
    print("1. Synchronous Interpreter:")
    fs1 = {"data.txt": "test data"}
    interp1 = SyncInterpreter(fs1)
    start = time.time()
    result1 = interp1.run(program)
    elapsed1 = time.time() - start
    print(f"   Time: {elapsed1:.2f}s\n")
    
    # Async
    print("2. Asynchronous Interpreter:")
    fs2 = {"data.txt": "test data"}
    interp2 = AsyncInterpreter(fs2)
    start = time.time()
    result2 = interp2.run(program)
    elapsed2 = time.time() - start
    print(f"   Time: {elapsed2:.2f}s\n")


def demo_real_world_etl():
    """Realistic ETL pipeline with free monad"""
    print("-- Real-World: ETL Pipeline --\n")
    
    def etl_pipeline() -> Free[dict]:
        """Extract -> Transform -> Load"""
        return (
            read_file("raw_data.csv")
            .bind(lambda raw:
                # Transform
                write_file("processed.csv", raw.upper())
                .bind(lambda _:
                    # Load
                    read_file("processed.csv")
                    .bind(lambda processed:
                        pure({
                            "raw_size": len(raw),
                            "processed_size": len(processed),
                            "status": "success"
                        })
                    )
                )
            )
        )
    
    program = etl_pipeline()
    
    print("ETL Pipeline: Extract -> Transform -> Load\n")
    
    # Run with real interpreter
    fs = {"raw_data.csv": "name,age\nalice,30\nbob,25"}
    interp = SyncInterpreter(fs)
    result = interp.run(program)
    
    print(f"\nResult: {result}")
    print(f"Final filesystem: {fs}\n")


def main():    
    demo_basic_interpretation()
    demo_monadic_composition()
    demo_interpreter_switching()
    demo_performance_comparison()
    demo_real_world_etl()
    
    print("\n-- Insights: Free Monads --")
    print("- Separate DESCRIPTION (program) from EXECUTION (interpreter)")
    print("- Programs are just data structures (ASTs)")
    print("- Same program → multiple interpreters (sync/async/mock/optimize)")
    print("- Perfect for testing: swap real I/O with mock")
    print("- Enables optimization: analyze AST before execution")
    print("- Used in: Cats Effect, ZIO, Polysemy, Fused-Effects")
    print()
    
    print("Functor:         Transform values independently")
    print("Applicative:     Combine independent operations (parallel)")
    print("Monad:           Sequence dependent operations")
    print("Natural Trans:   Convert between execution strategies")
    print("Free Monad:      Separate description from execution")


if __name__ == "__main__":
    main()
