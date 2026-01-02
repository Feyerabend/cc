import threading
import time
from typing import Callable, TypeVar, Generic
from abc import ABC, abstractmethod

A = TypeVar('A')
B = TypeVar('B')

# Category Theory: Monad
# A monad M is a functor with two additional operations:
# 1. unit (return): A -> M[A]  (lifts a value into the monad)
# 2. bind (>>=): M[A] -> (A -> M[B]) -> M[B]  (sequences operations)
#
# Monad Laws:
# - Left identity:  unit(a).bind(f) = f(a)
# - Right identity: m.bind(unit) = m
# - Associativity:  m.bind(f).bind(g) = m.bind(lambda x: f(x).bind(g))

class Async(Generic[A], ABC):
    """
    Async[A] is both a Functor and a Monad.
    It represents a computation that will eventually produce a value of type A.
    """
    
    @abstractmethod
    def run(self) -> A:
        """Execute and return result"""
        pass
    
    def fmap(self, f: Callable[[A], B]) -> 'Async[B]':
        """Functor map: (A -> B) -> Async[A] -> Async[B]"""
        return self.bind(lambda x: Async.unit(f(x)))
    
    def bind(self, f: Callable[[A], 'Async[B]']) -> 'Async[B]':
        """
        Monadic bind (>>=): sequences dependent computations
        The function f receives the result of self and returns a new Async computation
        """
        outer_self = self
        
        class BoundAsync(Async[B]):
            def run(self) -> B:
                # First run outer computation
                result = outer_self.run()
                # Then apply f to get next computation and run it
                next_computation = f(result)
                return next_computation.run()
        
        return BoundAsync()
    
    @staticmethod
    def unit(value: A) -> 'Async[A]':
        """
        Monadic unit (return): lifts a pure value into Async context
        Also called 'pure' or 'return' in different languages
        """
        class PureAsync(Async[A]):
            def run(self) -> A:
                return value
        
        return PureAsync()


class ConcurrentTask(Async[A]):
    """Async implementation using threads"""
    
    def __init__(self, computation: Callable[[], A], delay: float = 0, name: str = ""):
        self.computation = computation
        self.delay = delay
        self.name = name
    
    def run(self) -> A:
        """Execute in thread"""
        result = None
        
        def task():
            nonlocal result
            if self.name:
                print(f"  [{self.name}] Starting... (delay={self.delay}s)")
            if self.delay > 0:
                time.sleep(self.delay)
            result = self.computation()
            if self.name:
                print(f"  [{self.name}] Completed -> {result}")
        
        thread = threading.Thread(target=task)
        thread.start()
        thread.join()
        return result


def demo_monad_laws():
    """Verify the three monad laws"""
    print("-- Verifying Monad Laws --\n")
    
    # Left identity: unit(a).bind(f) = f(a)
    print("1. Left Identity: unit(a).bind(f) = f(a)")
    f = lambda x: ConcurrentTask(lambda: x * 2, delay=0.1)
    
    left = Async.unit(5).bind(f).run()
    right = f(5).run()
    print(f"   unit(5).bind(f) = {left}")
    print(f"   f(5) = {right}")
    print(f"   Equal? {left == right} ✓\n")
    
    # Right identity: m.bind(unit) = m
    print("2. Right Identity: m.bind(unit) = m")
    m = ConcurrentTask(lambda: 42, delay=0.1)
    
    left = m.bind(Async.unit).run()
    right = m.run()
    print(f"   m.bind(unit) = {left}")
    print(f"   m = {right}")
    print(f"   Equal? {left == right} ✓\n")
    
    # Associativity: m.bind(f).bind(g) = m.bind(lambda x: f(x).bind(g))
    print("3. Associativity: m.bind(f).bind(g) = m.bind(λx.f(x).bind(g))")
    f = lambda x: ConcurrentTask(lambda: x + 10, delay=0.1)
    g = lambda x: ConcurrentTask(lambda: x * 2, delay=0.1)
    m = ConcurrentTask(lambda: 5, delay=0.1)
    
    left = m.bind(f).bind(g).run()
    right = m.bind(lambda x: f(x).bind(g)).run()
    print(f"   m.bind(f).bind(g) = {left}")
    print(f"   m.bind(λx.f(x).bind(g)) = {right}")
    print(f"   Equal? {left == right} ✓\n")


def demo_sequential_pipeline():
    """Show monad for sequencing dependent async operations"""
    print("-- Sequential Pipeline (each depends on previous) --\n")
    
    # Simulate: fetch user -> fetch posts -> count words
    def fetch_user(user_id: int) -> Async[str]:
        return ConcurrentTask(
            lambda: f"User_{user_id}",
            delay=0.3,
            name=f"FetchUser({user_id})"
        )
    
    def fetch_posts(username: str) -> Async[list]:
        return ConcurrentTask(
            lambda: [f"{username}_post1", f"{username}_post2", f"{username}_post3"],
            delay=0.4,
            name=f"FetchPosts({username})"
        )
    
    def count_words(posts: list) -> Async[int]:
        return ConcurrentTask(
            lambda: len(posts) * 15,  # simulate word count
            delay=0.2,
            name=f"CountWords({len(posts)} posts)"
        )
    
    # Chain operations with bind - each waits for previous
    print("Building pipeline: fetch_user >>= fetch_posts >>= count_words\n")
    
    start = time.time()
    result = (fetch_user(123)
              .bind(fetch_posts)
              .bind(count_words)
              .run())
    elapsed = time.time() - start
    
    print(f"\nTotal words: {result}")
    print(f"Sequential time: {elapsed:.2f}s (≈0.3+0.4+0.2 = 0.9s)")


def demo_parallel_vs_sequential():
    """Compare independent vs dependent computations"""
    print("\n-- Parallel vs Sequential --\n")
    
    # Independent computations - can run in parallel
    print("1. Independent computations (parallel with threads):")
    
    tasks = [
        ConcurrentTask(lambda i=i: i**2, delay=0.3, name=f"Task{i}")
        for i in range(1, 4)
    ]
    
    results = []
    threads = []
    start = time.time()
    
    def runner(task):
        results.append(task.run())
    
    for task in tasks:
        t = threading.Thread(target=runner, args=(task,))
        t.start()
        threads.append(t)
    
    for t in threads:
        t.join()
    
    elapsed = time.time() - start
    print(f"   Results: {results}")
    print(f"   Time: {elapsed:.2f}s (parallel, ~0.3s)\n")
    
    # Dependent computations - must be sequential
    print("2. Dependent computations (sequential with bind):")
    
    start = time.time()
    result = (ConcurrentTask(lambda: 1, delay=0.3, name="Step1")
              .bind(lambda x: ConcurrentTask(lambda: x + 1, delay=0.3, name="Step2"))
              .bind(lambda x: ConcurrentTask(lambda: x * 2, delay=0.3, name="Step3"))
              .run())
    elapsed = time.time() - start
    
    print(f"   Result: {result}")
    print(f"   Time: {elapsed:.2f}s (sequential, ~0.9s)")


def demo_error_handling():
    """Show how monads can handle errors in pipelines"""
    print("\n-- Monad Pattern for Error Handling --\n")
    
    # Simulate operations that might fail
    def risky_operation(x: int) -> Async[int]:
        if x < 0:
            print(f"  [Warning] Clamping negative value {x} to 0")
            return Async.unit(0)
        return ConcurrentTask(lambda: x * 2, delay=0.1, name=f"Process({x})")
    
    values = [5, -3, 10]
    
    for val in values:
        result = (Async.unit(val)
                  .bind(risky_operation)
                  .bind(lambda x: Async.unit(x + 100))
                  .run())
        print(f"  Input {val} -> Output {result}")


def main():
    print("--- Category Theory: Monads for Async Sequencing ---\n")
    
    demo_monad_laws()
    demo_sequential_pipeline()
    demo_parallel_vs_sequential()
    demo_error_handling()

    print("\n-- Concepts --")
    print("- Functor: transforms values (independent operations)")
    print("- Monad: sequences computations (dependent operations)")
    print("- unit/return: lifts pure values into async context")
    print("- bind (>>=): chains operations where each depends on previous")
    print("- Laws ensure predictable composition and refactoring")


if __name__ == "__main__":
    main()
