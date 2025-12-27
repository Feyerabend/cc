import threading
import time
from typing import Callable, TypeVar, Generic, List
from abc import ABC, abstractmethod
from queue import Queue

A = TypeVar('A')
B = TypeVar('B')

# Natural Transformation: η : F ⇒ G
# A natural transformation is a mapping between functors that preserves structure.
# For all morphisms f: A -> B, this diagram commutes:
#
#    F(A) --F(f)--> F(B)
#     |              |
#    η_A            η_B
#     |              |
#     v              v
#    G(A) --G(f)--> G(B)
#
# This means: η_B . F(f) = G(f) . η_A
# (Transform then map = Map then transform)

class Functor(Generic[A], ABC):
    """Base functor interface"""
    
    @abstractmethod
    def fmap(self, f: Callable[[A], B]) -> 'Functor[B]':
        pass
    
    @abstractmethod
    def run(self) -> A:
        pass


class Sync(Functor[A]):
    """Synchronous computation functor - executes immediately"""
    
    def __init__(self, computation: Callable[[], A], name: str = ""):
        self.computation = computation
        self.name = name
    
    def fmap(self, f: Callable[[A], B]) -> 'Sync[B]':
        outer = self
        return Sync(
            lambda: f(outer.computation()),
            name=f"{self.name}->mapped"
        )
    
    def run(self) -> A:
        if self.name:
            print(f"  [Sync:{self.name}] Executing immediately")
        return self.computation()


class Async(Functor[A]):
    """Asynchronous computation functor - executes in thread"""
    
    def __init__(self, computation: Callable[[], A], delay: float = 0, name: str = ""):
        self.computation = computation
        self.delay = delay
        self.name = name
    
    def fmap(self, f: Callable[[A], B]) -> 'Async[B]':
        outer = self
        return Async(
            lambda: f(outer.computation()),
            delay=self.delay,
            name=f"{self.name}->mapped"
        )
    
    def run(self) -> A:
        result = None
        
        def task():
            nonlocal result
            if self.name:
                print(f"  [Async:{self.name}] Starting in thread...")
            time.sleep(self.delay)
            result = self.computation()
        
        thread = threading.Thread(target=task)
        thread.start()
        thread.join()
        return result


class Lazy(Functor[A]):
    """Lazy computation functor - defers execution until forced"""
    
    def __init__(self, computation: Callable[[], A], name: str = ""):
        self.computation = computation
        self.name = name
        self._cached = None
        self._evaluated = False
    
    def fmap(self, f: Callable[[A], B]) -> 'Lazy[B]':
        outer = self
        return Lazy(
            lambda: f(outer.force()),
            name=f"{self.name}->mapped"
        )
    
    def force(self) -> A:
        """Force evaluation and cache result"""
        if not self._evaluated:
            if self.name:
                print(f"  [Lazy:{self.name}] Evaluating (first time)")
            self._cached = self.computation()
            self._evaluated = True
        else:
            if self.name:
                print(f"  [Lazy:{self.name}] Returning cached")
        return self._cached
    
    def run(self) -> A:
        return self.force()


class Parallel(Functor[A]):
    """Parallel computation functor - executes multiple tasks concurrently"""
    
    def __init__(self, computations: List[Callable[[], A]], name: str = ""):
        self.computations = computations
        self.name = name
    
    def fmap(self, f: Callable[[A], B]) -> 'Parallel[B]':
        return Parallel(
            [lambda comp=c: f(comp()) for c in self.computations],
            name=f"{self.name}->mapped"
        )
    
    def run(self) -> List[A]:
        if self.name:
            print(f"  [Parallel:{self.name}] Starting {len(self.computations)} tasks")
        
        results = [None] * len(self.computations)
        threads = []
        
        def worker(idx, comp):
            results[idx] = comp()
        
        start = time.time()
        for i, comp in enumerate(self.computations):
            t = threading.Thread(target=worker, args=(i, comp))
            t.start()
            threads.append(t)
        
        for t in threads:
            t.join()
        
        elapsed = time.time() - start
        if self.name:
            print(f"  [Parallel:{self.name}] Completed in {elapsed:.2f}s")
        
        return results


# NATURAL TRANSFORMATIONS

def sync_to_async(sync_comp: Sync[A], delay: float = 0) -> Async[A]:
    """
    Natural transformation: Sync ⇒ Async
    Converts synchronous computation to asynchronous
    """
    return Async(sync_comp.computation, delay=delay, name=f"async({sync_comp.name})")


def async_to_sync(async_comp: Async[A]) -> Sync[A]:
    """
    Natural transformation: Async ⇒ Sync
    Forces async computation to run synchronously (blocks)
    """
    return Sync(async_comp.run, name=f"sync({async_comp.name})")


def sync_to_lazy(sync_comp: Sync[A]) -> Lazy[A]:
    """
    Natural transformation: Sync ⇒ Lazy
    Defers synchronous computation until forced
    """
    return Lazy(sync_comp.computation, name=f"lazy({sync_comp.name})")


def lazy_to_sync(lazy_comp: Lazy[A]) -> Sync[A]:
    """
    Natural transformation: Lazy ⇒ Sync
    Forces lazy computation immediately
    """
    return Sync(lazy_comp.force, name=f"sync({lazy_comp.name})")


def list_to_parallel(sync_list: List[Sync[A]]) -> Parallel[A]:
    """
    Natural transformation: List[Sync] ⇒ Parallel
    Converts list of sync computations to parallel execution
    """
    return Parallel(
        [s.computation for s in sync_list],
        name="parallel_batch"
    )


# DEMONSTRATIONS

def demo_naturality_law():
    """
    Verify naturality condition: η_B . F(f) = G(f) . η_A
    (Transform then map = Map then transform)
    """
    print("--- Verifying Naturality Law ---\n")
    print("Law: transform(F(x).map(f)) = transform(F(x)).map(f)")
    print("     (transform after map)   (map after transform)\n")
    
    f = lambda x: x * 2
    
    # Create a sync computation
    sync_comp = Sync(lambda: 5, name="base")
    
    # Path 1: Map first, then transform
    path1 = sync_to_async(sync_comp.fmap(f), delay=0.1)
    result1 = path1.run()
    print(f"Path 1 (map then transform): {result1}")
    
    # Path 2: Transform first, then map
    path2 = sync_to_async(sync_comp, delay=0.1).fmap(f)
    result2 = path2.run()
    print(f"Path 2 (transform then map): {result2}")
    
    print(f"\nResults equal? {result1 == result2} ✓")
    print("Naturality preserved! Order doesn't matter.\n")


def demo_execution_strategies():
    """Show different execution strategies via natural transformations"""
    print("--- Execution Strategy Transformations ---\n")
    
    # Start with sync computation
    print("1. Base: Synchronous computation")
    sync = Sync(lambda: 42, name="compute_42")
    result = sync.run()
    print(f"   Result: {result}\n")
    
    # Transform to async
    print("2. Transform to Async (runs in thread)")
    async_version = sync_to_async(sync, delay=0.3)
    start = time.time()
    result = async_version.run()
    elapsed = time.time() - start
    print(f"   Result: {result} (took {elapsed:.2f}s)\n")
    
    # Transform to lazy
    print("3. Transform to Lazy (deferred evaluation)")
    lazy_version = sync_to_lazy(Sync(lambda: 100, name="expensive_calc"))
    print("   Created lazy computation (not yet evaluated)")
    print("   Forcing evaluation...")
    result1 = lazy_version.run()
    print(f"   First call: {result1}")
    result2 = lazy_version.run()
    print(f"   Second call: {result2} (cached!)\n")


def demo_parallel_transformation():
    """Transform sequential tasks to parallel execution"""
    print("--- Sequential → Parallel Transformation ---\n")
    
    # Create sequential sync tasks
    tasks = [
        Sync(lambda i=i: i**2, name=f"square_{i}")
        for i in range(1, 5)
    ]
    
    print("1. Sequential execution:")
    start = time.time()
    seq_results = [t.run() for t in tasks]
    seq_time = time.time() - start
    print(f"   Results: {seq_results}")
    print(f"   Time: {seq_time:.3f}s\n")
    
    print("2. Parallel execution (via natural transformation):")
    # Add delays to see parallel benefit
    delayed_tasks = [
        Sync(lambda i=i: (time.sleep(0.2), i**2)[1], name=f"square_{i}")
        for i in range(1, 5)
    ]
    
    parallel = list_to_parallel(delayed_tasks)
    start = time.time()
    par_results = parallel.run()
    par_time = time.time() - start
    print(f"   Results: {par_results}")
    print(f"   Time: {par_time:.2f}s (parallel speedup!)\n")


def demo_composition():
    """Compose natural transformations"""
    print("--- Composing Natural Transformations ---\n")
    print("Chain: Sync → Lazy → Sync → Async\n")
    
    # Start with sync
    comp = Sync(lambda: 7, name="start")
    print(f"1. Sync: {comp.run()}")
    
    # Sync → Lazy
    comp = sync_to_lazy(comp)
    print(f"2. After Sync→Lazy: {comp.run()}")
    
    # Lazy → Sync
    comp = lazy_to_sync(comp)
    print(f"3. After Lazy→Sync: {comp.run()}")
    
    # Sync → Async
    comp = sync_to_async(comp, delay=0.2)
    print(f"4. After Sync→Async: {comp.run()}")
    
    print("\nEach transformation changes execution model while preserving value!")


def demo_real_world_pipeline():
    """Realistic example: data processing with different strategies"""
    print("\n--- Real-World Pipeline Example ---\n")
    print("Scenario: Process user data with different execution strategies\n")
    
    # Simulate data fetching and processing
    def fetch_data(user_id):
        time.sleep(0.2)  # simulate I/O
        return {"id": user_id, "score": user_id * 10}
    
    def process_data(data):
        time.sleep(0.1)  # simulate processing
        return data["score"] * 2
    
    user_ids = [1, 2, 3, 4, 5]
    
    # Strategy 1: Sequential sync
    print("Strategy 1: Sequential Sync")
    sync_tasks = [Sync(lambda uid=uid: fetch_data(uid), name=f"user_{uid}") 
                  for uid in user_ids]
    start = time.time()
    sync_results = [process_data(t.run()) for t in sync_tasks]
    print(f"  Results: {sync_results}")
    print(f"  Time: {time.time() - start:.2f}s\n")
    
    # Strategy 2: Parallel (transform sequential to parallel)
    print("Strategy 2: Parallel (via natural transformation)")
    sync_tasks = [Sync(lambda uid=uid: fetch_data(uid), name=f"user_{uid}") 
                  for uid in user_ids]
    parallel_fetch = list_to_parallel(sync_tasks)
    start = time.time()
    fetched = parallel_fetch.run()
    parallel_results = [process_data(d) for d in fetched]
    print(f"  Results: {parallel_results}")
    print(f"  Time: {time.time() - start:.2f}s (faster!)\n")


def main():
    demo_naturality_law()
    demo_execution_strategies()
    demo_parallel_transformation()
    demo_composition()
    demo_real_world_pipeline()
    
    print("\n-- Concepts --")
    print("- Natural Transformation: morphism between functors (η: F ⇒ G)")
    print("- Preserves structure: transform then map = map then transform")
    print("- Enables switching execution strategies (sync/async/lazy/parallel)")
    print("- Composable: can chain transformations (Sync→Lazy→Async)")
    print("- Practical: optimize performance by changing execution model")
    print("\n-- The Complete Picture --")
    print("Functor:  independent transformations (map)")
    print("Monad:    dependent sequencing (bind)")
    print("Natural:  strategy conversion (between functors)")


if __name__ == "__main__":
    main()
