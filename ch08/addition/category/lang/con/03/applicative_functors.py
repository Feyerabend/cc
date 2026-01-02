import threading
import time
from typing import Callable, TypeVar, Generic, List
from abc import ABC, abstractmethod

A = TypeVar('A')
B = TypeVar('B')
C = TypeVar('C')
D = TypeVar('D')

# Applicative Functor: sits between Functor and Monad
#
# Hierarchy:
#   Functor     <: has fmap
#   Applicative <: has fmap + pure + ap (or <*>)
#   Monad       <: has fmap + pure + ap + bind
#
# Key insight: Applicative allows independent computations to be composed
# in parallel, while Monad forces sequential dependencies.
#
# Operations:
#   pure: A -> F[A]                    (lift value)
#   ap (<*>): F[A -> B] -> F[A] -> F[B] (apply wrapped function)
#
# Laws:
#   Identity:     pure(id) <*> v = v
#   Composition:  pure(∘) <*> u <*> v <*> w = u <*> (v <*> w)
#   Homomorphism: pure(f) <*> pure(x) = pure(f(x))
#   Interchange:  u <*> pure(y) = pure(λf.f(y)) <*> u

class Applicative(Generic[A], ABC):
    """
    Applicative Functor: allows independent parallel composition
    """
    
    @abstractmethod
    def fmap(self, f: Callable[[A], B]) -> 'Applicative[B]':
        """Functor map"""
        pass
    
    @abstractmethod
    def ap(self, ff: 'Applicative[Callable[[A], B]]') -> 'Applicative[B]':
        """
        Apply: F[A -> B] -> F[A] -> F[B]
        The key operation! Applies a wrapped function to wrapped value.
        """
        pass
    
    @staticmethod
    @abstractmethod
    def pure(value: A) -> 'Applicative[A]':
        """Lift a pure value into the applicative context"""
        pass
    
    @abstractmethod
    def run(self) -> A:
        """Execute and return result"""
        pass
    
    # Derived operations
    def map2(self, other: 'Applicative[B]', f: Callable[[A, B], C]) -> 'Applicative[C]':
        """
        Combine two independent computations with a binary function.
        This is where parallelism shines!
        map2(fa, fb, f) can run fa and fb in parallel, then combine.
        """
        # Lift f into applicative: pure(f) : F[A -> B -> C]
        # Then apply twice: pure(f) <*> fa <*> fb
        return other.ap(self.fmap(lambda a: lambda b: f(a, b)))
    
    def map3(self, b: 'Applicative[B]', c: 'Applicative[C]', 
             f: Callable[[A, B, C], D]) -> 'Applicative[D]':
        """Combine three independent computations"""
        return c.ap(b.ap(self.fmap(lambda a: lambda b: lambda c: f(a, b, c))))


class ParAsync(Applicative[A]):
    """
    Asynchronous computation with PARALLEL applicative composition.
    Key: ap() runs both computations in parallel!
    """
    
    def __init__(self, computation: Callable[[], A], delay: float = 0, name: str = ""):
        self.computation = computation
        self.delay = delay
        self.name = name
    
    def fmap(self, f: Callable[[A], B]) -> 'ParAsync[B]':
        outer = self
        return ParAsync(
            lambda: f(outer.computation()),
            delay=self.delay,
            name=f"fmap({self.name})"
        )
    
    def ap(self, ff: 'ParAsync[Callable[[A], B]]') -> 'ParAsync[B]':
        """
        PARALLEL APPLICATION: Both self and ff run concurrently!
        This is the magic of Applicative for concurrency.
        """
        outer_value = self
        outer_func = ff
        
        def parallel_apply():
            result_value = None
            result_func = None
            
            def run_value():
                nonlocal result_value
                if outer_value.name:
                    print(f"  [Parallel] Computing value: {outer_value.name}")
                time.sleep(outer_value.delay)
                result_value = outer_value.computation()
            
            def run_func():
                nonlocal result_func
                if outer_func.name:
                    print(f"  [Parallel] Computing function: {outer_func.name}")
                time.sleep(outer_func.delay)
                result_func = outer_func.computation()
            
            # Run both in parallel!
            t1 = threading.Thread(target=run_value)
            t2 = threading.Thread(target=run_func)
            
            start = time.time()
            t1.start()
            t2.start()
            t1.join()
            t2.join()
            elapsed = time.time() - start
            
            print(f"  [Parallel] Both completed in {elapsed:.2f}s")
            return result_func(result_value)
        
        return ParAsync(parallel_apply, delay=0, name=f"ap({ff.name},{self.name})")
    
    @staticmethod
    def pure(value: A) -> 'ParAsync[A]':
        return ParAsync(lambda: value, delay=0, name=f"pure({value})")
    
    def run(self) -> A:
        if self.name:
            print(f"  [Run] Executing {self.name}")
        time.sleep(self.delay)
        return self.computation()


class SeqAsync(Applicative[A]):
    """
    Asynchronous computation with SEQUENTIAL applicative composition.
    For comparison: ap() runs computations one after another.
    """
    
    def __init__(self, computation: Callable[[], A], delay: float = 0, name: str = ""):
        self.computation = computation
        self.delay = delay
        self.name = name
    
    def fmap(self, f: Callable[[A], B]) -> 'SeqAsync[B]':
        outer = self
        return SeqAsync(
            lambda: f(outer.computation()),
            delay=self.delay,
            name=f"fmap({self.name})"
        )
    
    def ap(self, ff: 'SeqAsync[Callable[[A], B]]') -> 'SeqAsync[B]':
        """SEQUENTIAL APPLICATION: ff runs first, then self"""
        outer_value = self
        outer_func = ff
        
        def sequential_apply():
            # Run sequentially
            if outer_func.name:
                print(f"  [Sequential] Computing function: {outer_func.name}")
            time.sleep(outer_func.delay)
            f = outer_func.computation()
            
            if outer_value.name:
                print(f"  [Sequential] Computing value: {outer_value.name}")
            time.sleep(outer_value.delay)
            value = outer_value.computation()
            
            return f(value)
        
        return SeqAsync(sequential_apply, delay=0, name=f"ap({ff.name},{self.name})")
    
    @staticmethod
    def pure(value: A) -> 'SeqAsync[A]':
        return SeqAsync(lambda: value, delay=0, name=f"pure({value})")
    
    def run(self) -> A:
        if self.name:
            print(f"  [Run] Executing {self.name}")
        time.sleep(self.delay)
        return self.computation()




def demo_parallel_vs_sequential():
    """Show the key difference: parallel vs sequential composition"""
    print("-- Applicative: Parallel vs Sequential --\n")
    
    print("Scenario: Fetch user data and fetch posts independently\n")
    
    # Two independent async operations
    fetch_user = ParAsync(lambda: "Alice", delay=0.5, name="fetch_user")
    fetch_posts = ParAsync(lambda: ["post1", "post2"], delay=0.5, name="fetch_posts")
    
    # Combine with a function
    def combine(user, posts):
        return f"{user} has {len(posts)} posts"
    
    print("1. PARALLEL (Applicative):")
    start = time.time()
    result = fetch_user.map2(fetch_posts, combine).run()
    elapsed = time.time() - start
    print(f"   Result: {result}")
    print(f"   Time: {elapsed:.2f}s (both ran in parallel!)\n")
    
    # Same with sequential
    fetch_user_seq = SeqAsync(lambda: "Alice", delay=0.5, name="fetch_user")
    fetch_posts_seq = SeqAsync(lambda: ["post1", "post2"], delay=0.5, name="fetch_posts")
    
    print("2. SEQUENTIAL (for comparison):")
    start = time.time()
    result = fetch_user_seq.map2(fetch_posts_seq, combine).run()
    elapsed = time.time() - start
    print(f"   Result: {result}")
    print(f"   Time: {elapsed:.2f}s (ran one after another)\n")


def demo_applicative_laws():
    """Verify applicative laws"""
    print("-- Verifying Applicative Laws --\n")
    
    # Identity: pure(id) <*> v = v
    print("1. Identity: pure(id) <*> v = v")
    v = ParAsync(lambda: 42, delay=0.1, name="v")
    identity = lambda x: x
    
    left = v.ap(ParAsync.pure(identity)).run()
    right = v.run()
    print(f"   pure(id) <*> v = {left}")
    print(f"   v = {right}")
    print(f"   Equal? {left == right} ✓\n")
    
    # Homomorphism: pure(f) <*> pure(x) = pure(f(x))
    print("2. Homomorphism: pure(f) <*> pure(x) = pure(f(x))")
    f = lambda x: x * 2
    x = 21
    
    left = ParAsync.pure(x).ap(ParAsync.pure(f)).run()
    right = ParAsync.pure(f(x)).run()
    print(f"   pure(f) <*> pure(x) = {left}")
    print(f"   pure(f(x)) = {right}")
    print(f"   Equal? {left == right} ✓\n")


def demo_map2_map3():
    """Show combining multiple independent computations"""
    print("-- Combining Multiple Independent Computations --\n")
    
    print("1. map2: Combine 2 computations")
    a = ParAsync(lambda: 10, delay=0.3, name="compute_a")
    b = ParAsync(lambda: 20, delay=0.3, name="compute_b")
    
    start = time.time()
    result = a.map2(b, lambda x, y: x + y).run()
    elapsed = time.time() - start
    print(f"   Result: {result}")
    print(f"   Time: {elapsed:.2f}s (parallel!)\n")
    
    print("2. map3: Combine 3 computations")
    a = ParAsync(lambda: 5, delay=0.2, name="compute_a")
    b = ParAsync(lambda: 10, delay=0.2, name="compute_b")
    c = ParAsync(lambda: 15, delay=0.2, name="compute_c")
    
    start = time.time()
    result = a.map3(b, c, lambda x, y, z: x + y + z).run()
    elapsed = time.time() - start
    print(f"   Result: {result}")
    print(f"   Time: {elapsed:.2f}s (all 3 in parallel!)\n")


def demo_real_world_form_validation():
    """Realistic example: parallel form field validation"""
    print("-- Real-World: Parallel Form Validation --\n")
    
    def validate_email(email: str) -> bool:
        """Simulate async email validation (check if exists in DB)"""
        time.sleep(0.3)
        print(f"  ✓ Email '{email}' validated")
        return "@" in email
    
    def validate_username(username: str) -> bool:
        """Simulate async username validation (check if available)"""
        time.sleep(0.3)
        print(f"  ✓ Username '{username}' validated")
        return len(username) >= 3
    
    def validate_password(password: str) -> bool:
        """Simulate async password strength check"""
        time.sleep(0.3)
        print(f"  ✓ Password validated")
        return len(password) >= 8
    
    # Create independent validation tasks
    email_check = ParAsync(
        lambda: validate_email("alice@example.com"),
        delay=0,
        name="email_validation"
    )
    
    username_check = ParAsync(
        lambda: validate_username("alice123"),
        delay=0,
        name="username_validation"
    )
    
    password_check = ParAsync(
        lambda: validate_password("secure_pass_123"),
        delay=0,
        name="password_validation"
    )
    
    # Combine all three in parallel!
    def all_valid(e, u, p):
        return e and u and p
    
    print("Validating form fields in parallel...\n")
    start = time.time()
    result = email_check.map3(username_check, password_check, all_valid).run()
    elapsed = time.time() - start
    
    print(f"\nAll validations passed? {result}")
    print(f"Total time: {elapsed:.2f}s (parallel, not 0.9s sequential!)\n")


def demo_applicative_vs_monad():
    """Show when to use Applicative vs Monad"""
    print("-- Applicative vs Monad: When to Use Each --\n")
    
    print("1. INDEPENDENT operations → Use Applicative (parallel)")
    print("   Example: Fetch user profile and user posts simultaneously\n")
    
    profile = ParAsync(lambda: {"name": "Alice"}, delay=0.3, name="profile")
    posts = ParAsync(lambda: ["post1", "post2"], delay=0.3, name="posts")
    
    start = time.time()
    result = profile.map2(posts, lambda p, ps: f"{p['name']}: {len(ps)} posts").run()
    elapsed = time.time() - start
    print(f"   Result: {result}")
    print(f"   Time: {elapsed:.2f}s (parallel ✓)\n")
    
    print("2. DEPENDENT operations → Must use Monad (sequential)")
    print("   Example: Fetch user, THEN fetch their posts using user ID")
    print("   (Can't parallelize - need user ID first!)")
    print("   This requires bind/flatMap, not Applicative\n")


def demo_traffic_light():
    """Fun example: combining multiple sensor readings"""
    print("-- Example: Traffic Light Control System --\n")
    print("Read 3 sensors in parallel, decide action\n")
    
    def read_motion_sensor():
        time.sleep(0.2)
        return True  # motion detected
    
    def read_light_sensor():
        time.sleep(0.2)
        return 0.3  # 30% brightness (night)
    
    def read_timer():
        time.sleep(0.2)
        return 45  # 45 seconds since last change
    
    motion = ParAsync(read_motion_sensor, delay=0, name="motion_sensor")
    light = ParAsync(read_light_sensor, delay=0, name="light_sensor")
    timer = ParAsync(read_timer, delay=0, name="timer")
    
    def decide(has_motion, brightness, elapsed):
        if has_motion and brightness < 0.5 and elapsed > 30:
            return " Turn Green (motion at night, enough time passed)"
        else:
            return " Stay Red"
    
    start = time.time()
    decision = motion.map3(light, timer, decide).run()
    elapsed = time.time() - start
    
    print(f"Decision: {decision}")
    print(f"Time: {elapsed:.2f}s (all sensors read in parallel!)\n")


def main():    
    demo_parallel_vs_sequential()
    demo_applicative_laws()
    demo_map2_map3()
    demo_real_world_form_validation()
    demo_applicative_vs_monad()
    demo_traffic_light()
    
    print("\n-- Key Insights --")
    print("- Applicative sits between Functor and Monad")
    print("- Key power: compose INDEPENDENT computations in PARALLEL")
    print("- Operations: pure (lift) + ap (<*>) (apply wrapped function)")
    print("- map2, map3: combine 2-3 independent operations efficiently")
    print("- When to use:")
    print("  - Applicative: independent operations (parallel)")
    print("  - Monad: dependent operations (sequential)")
    print("\n-- The Hierarchy --")
    print("Functor:     fmap                    (transform values)")
    print("Applicative: fmap + pure + ap        (parallel composition)")
    print("Monad:       fmap + pure + ap + bind (sequential composition)")


if __name__ == "__main__":
    main()
