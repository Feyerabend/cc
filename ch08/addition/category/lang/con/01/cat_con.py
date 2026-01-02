import threading
import time
from typing import Callable, TypeVar, Generic
from abc import ABC, abstractmethod

A = TypeVar('A')
B = TypeVar('B')

# Category Theory Concept: Functor
# A functor F maps objects and morphisms from category C to category D
# preserving: F(id_A) = id_F(A) and F(g ∘ f) = F(g) ∘ F(f)

class Async(Generic[A], ABC):
    """
    Async[A] represents a computation that will eventually produce a value of type A.
    This is our "container" type - like a category of asynchronous computations.
    """
    
    @abstractmethod
    def run(self) -> A:
        """Execute the async computation and return result"""
        pass
    
    def fmap(self, f: Callable[[A], B]) -> 'Async[B]':
        """
        Functor map: lifts a pure function f: A -> B 
        to work on Async[A] -> Async[B]
        
        This preserves function composition:
        fmap(g . f) = fmap(g) . fmap(f)
        """
        outer_self = self
        
        class MappedAsync(Async[B]):
            def run(self) -> B:
                result = outer_self.run()
                return f(result)
        
        return MappedAsync()


class ConcurrentTask(Async[A]):
    """Concrete implementation using threads"""
    
    def __init__(self, computation: Callable[[], A], delay: float = 0):
        self.computation = computation
        self.delay = delay
        self._result = None
        self._thread = None
    
    def run(self) -> A:
        """Start thread and wait for result"""
        def task():
            if self.delay > 0:
                time.sleep(self.delay)
            self._result = self.computation()
        
        self._thread = threading.Thread(target=task)
        self._thread.start()
        self._thread.join()
        return self._result


# Pure functions (morphisms in our category)
def square(x: int) -> int:
    print(f"  square({x}) = {x*x}")
    return x * x

def add_ten(x: int) -> int:
    print(f"  add_ten({x}) = {x+10}")
    return x + 10

def to_string(x: int) -> str:
    result = f"Result: {x}"
    print(f"  to_string({x}) = '{result}'")
    return result


def demo():
    print("=== Category Theory meets Concurrency ===\n")
    
    # Create async computations (objects in our Async category)
    print("1. Create base async computation:")
    task1 = ConcurrentTask(lambda: 5, delay=0.5)
    
    # Demonstrate functor composition
    print("\n2. Apply functor transformations (fmap):")
    print("   Composing: square ∘ add_ten")
    
    # Method 1: Compose with fmap twice
    print("\n   Method A: fmap(square) . fmap(add_ten)")
    task2 = task1.fmap(add_ten).fmap(square)
    result1 = task2.run()
    print(f"   Final: {result1}")
    
    # Method 2: Compose functions first, then fmap once
    print("\n   Method B: fmap(square . add_ten)")
    task3 = ConcurrentTask(lambda: 5, delay=0.5)
    composed = lambda x: square(add_ten(x))
    task4 = task3.fmap(composed)
    result2 = task4.run()
    print(f"   Final: {result2}")
    
    # Verify functor law: fmap(g . f) = fmap(g) . fmap(f)
    print(f"\n   Results equal? {result1 == result2} ✓")
    
    # Demonstrate concurrent execution with multiple tasks
    print("\n3. Multiple concurrent tasks (parallel functor applications):")
    
    tasks = [
        ConcurrentTask(lambda i=i: i, delay=0.3).fmap(square).fmap(to_string)
        for i in range(1, 4)
    ]
    
    threads = []
    results = [None] * len(tasks)
    
    def run_task(idx, task):
        results[idx] = task.run()
    
    # Start all tasks concurrently
    start = time.time()
    for i, task in enumerate(tasks):
        t = threading.Thread(target=run_task, args=(i, task))
        t.start()
        threads.append(t)
    
    # Wait for all
    for t in threads:
        t.join()
    
    elapsed = time.time() - start
    print(f"\n   Completed {len(tasks)} tasks in {elapsed:.2f}s (concurrent)")
    for r in results:
        print(f"   -> {r}")
    
    print("\n--- Category Theory Concepts ---")
    print("- Objects: Async[A] - computations producing type A")
    print("- Morphisms: A -> B (pure functions)")
    print("- Functor: fmap lifts f: A->B to Async[A]->Async[B]")
    print("- Composition preserved: fmap(g∘f) = fmap(g)∘fmap(f)")
    print("- Concurrency: Multiple functor applications run in parallel")


if __name__ == "__main__":
    demo()
