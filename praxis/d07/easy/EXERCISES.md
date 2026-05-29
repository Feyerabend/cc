## Exercises

### Advanced Programming: Concurrency, Types, and Correctness

#### Concurrency

1. *What is the difference between concurrency and parallelism?*
   - Can a single-core machine be concurrent? Can it be parallel? Give examples of each.

2. *What is a race condition? Give a concrete example.*
   - Why is a race condition hard to reproduce reliably? What makes it dangerous?

3. *What is a mutex? What does it guarantee?*
   - What is the cost of acquiring a mutex? What happens if a mutex is held and never released?

4. *What is a deadlock? Describe the four conditions that must all hold for one to occur.*
   - Give a concrete example involving two threads and two locks.

5. *What is a semaphore? How does it differ from a mutex?*
   - Give an example of a problem that is better solved with a semaphore than a mutex.

6. *What is a condition variable? When would you use one?*
   - Describe the producer-consumer problem. How does a condition variable help solve it?

7. *What is an atomic operation? Why are some operations not atomic even though they look like one line?*
   - Give an example of a non-atomic increment in C. What is the fix?

8. *What is a memory barrier? Why is it needed on modern hardware?*
   - What does "happens-before" mean in a memory model?

9. *What is the actor model of concurrency? How does it differ from shared-memory concurrency?*
   - What problem does message passing solve that locks cannot?

10. *What is a coroutine? How does it differ from a thread?*
    - What is cooperative multitasking? What is its advantage over preemptive multitasking?


#### Functional Programming

1. *What is a pure function? What two properties must it have?*
   - Why are pure functions easier to test than impure ones?

2. *What is referential transparency?*
   - If a function is referentially transparent, what can you do with it that you cannot do
     with an impure function?

3. *What is a closure? What does it "close over"?*
   - Give an example of a closure in Python or JavaScript. What state does it capture?

4. *What is a higher-order function?*
   - Give three examples. What makes higher-order functions composable?

5. *What is a monad? Describe it in one sentence without using the word "monad".*
   - What problem does the Maybe monad solve? What problem does the IO monad solve?

6. *What is lazy evaluation? How does it differ from eager evaluation?*
   - What is an infinite list? Under what evaluation strategy can you define one?

7. *What is immutability, and why does it simplify concurrent programming?*
   - What is a persistent data structure? How can you "modify" an immutable structure?

8. *What is a functor? What operation must it support?*
   - Give an example of a functor in a language you know.


#### Advanced Type Systems

1. *What is parametric polymorphism? Give an example.*
   - How does a generic function differ from an overloaded function?

2. *What is a type class (or trait)? What problem does it solve?*
   - Give an example of a type class. What does implementing it promise?

3. *What is a dependent type?*
   - Give an example of a type that depends on a value. What can dependent types prevent?

4. *What is substructural typing? What does "linear" mean in this context?*
   - What does a linear type system prevent that a regular type system does not?

5. *What is a session type? What does it specify?*
   - Give an example of a session type for a simple client-server interaction.

6. *What is the Curry-Howard correspondence?*
   - What does a type correspond to? What does a program correspond to?
     What does type-checking correspond to?

7. *What is a phantom type? What problem does it solve without any runtime cost?*
   - Give an example where a phantom type prevents a logical error.


#### Distributed Systems

1. *What is a consensus protocol? Why is consensus hard in a distributed system?*
   - What is the FLP impossibility result? What does it say cannot be done?

2. *What is the CAP theorem?*
   - What are the three properties? Which two can you guarantee simultaneously?

3. *What is Raft? What problem does it solve?*
   - What are the three roles a Raft node can have?

4. *What is a leader election? Why must a distributed system agree on exactly one leader?*
   - What happens if two nodes both believe they are the leader?

5. *What is log replication in Raft?*
   - What does the leader do after it receives a write request?
   - What is a "committed" entry?

6. *What is a network partition? How does Raft respond to one?*
   - Which guarantee does Raft maintain during a partition: availability or consistency?
