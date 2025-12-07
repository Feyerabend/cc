
## Time Travel Debugging (TTD)

*Time Travel Debugging* is a debugging technique that allows developers
to move back and forth through the execution history of a program.
Unlike traditional debuggers, which only allow you to step through
code in a forward direction, TTD enables the following:

1. *Historical inspection*: Developers can examine the program state at any point
in its execution history. This is incredibly useful for diagnosing issues that are
difficult to reproduce. It allows you to see exactly what was happening in the
program when a bug occurred.

2. *State rewind*: By rewinding to a previous state, developers can re-execute code
to observe the effects of certain changes or to identify where things went wrong.
This is particularly beneficial for understanding complex interactions within the code.

3. *Reproducing bugs*: TTD helps in reproducing bugs by allowing you to traverse
the program's execution path. You can go back to the moment the bug occurred and
step through the execution again, making it easier to isolate the problem.

4. *Enhanced debugging*: It simplifies debugging by allowing developers to review not
just the current state, but also the sequence of operations that led to that state.
This can provide valuable insights that are often lost in traditional debugging.


Usually you would use professional tools, however to be aquainted with some ideas
of how TTD could work, we study a simple samples integrated with a virtual machine
(VM). In the context of the example involving the VM with snapshot and
rewind capabilities, TTD can be applied in the following ways:

1. *Snapshots as Time Markers*: Each time a snapshot is taken in the VM, it serves as
a time marker. This snapshot represents a specific point in the execution where the
state of the object is saved. For instance, after various operations (like addition
or subtraction), a snapshot captures the exact values of all fields at that moment.

2. *Rewind*: The ability to rewind to a previous snapshot allows for time travel through
the state of the object. If a developer notices an issue after several operations, they
can rewind to the last snapshot to inspect the state before those operations were applied.
This makes it easier to diagnose what changes led to the current problematic state.

3. *Interactive debugging*: When debugging using TTD in the VM, developers can execute
the VM instructions step-by-step after rewinding to see how each instruction affects
the state. If an unexpected behavior is observed after a certain operation, they can
rewind to right before that operation to analyze the inputs and conditions that led
to the issue.

4. *Testing*: In a testing context, TTD allows developers to create robust test cases
that can validate the correctness of the VM's behavior over time. For example, tests
can ensure that after a series of operations followed by a rewind, the object reflects
the state of the last snapshot taken before the operations. This reinforces confidence
that the state management and rewind functionalities work as intended.


### Example 1

- *Easier bug detection*: By employing TTD, developers can easily identify *when* and
  *why* a state changed in an unexpected way, which simplifies the debugging process.

- *Validation of complex interactions*: It allows developers to validate that multiple
  interactions within the VM produce the expected results over time, especially as changes
  accumulate.

- *Improved code reliability*: With a focus on ensuring that the state is accurately
  saved and restored, the overall reliability of the VM can be enhanced. This is crucial
  when dealing with complex applications where maintaining consistent state is vital.


```c
int main() {

    // "fields"
    Field fields[2] = {
        {"field1", TYPE_FLOAT, .value.float_value = 10.0f},
        {"field2", TYPE_INT, .value.int_value = 20}
    };

    Object *obj = create_object("ExampleObject", fields, 2);

    printf("Initial state of object:\n");
    print_fields(obj);

    // "methods"
    VMInstruction method[8];
    method[0] = (VMInstruction){ADD, 0, 5.0f};    // Add 5 to field1
    method[1] = (VMInstruction){PRINT, 0, 0};     // Print state
    method[2] = (VMInstruction){SUB, 1, 10};      // Subtract 10 from field2
    method[3] = (VMInstruction){PRINT, 0, 0};     // Print state
    method[4] = (VMInstruction){MUL, 0, 2.0f};    // Multiply field1 by 2
    method[5] = (VMInstruction){PRINT, 0, 0};     // Print state
    method[6] = (VMInstruction){DIV, 1, 2};       // Divide field2 by 2
    method[7] = (VMInstruction){HALT, 0, 0};      // Halt VM

    // create VM
    VirtualMachine vm = {method, 8, 0};  // 8 instructions

    // take snapshots at various places
    Snapshot *snapshot1 = create_snapshot(&vm, obj);  // after first add
    run_vm(&vm, obj);  // run until halt

    // first rewind
    printf("\n--- Rewind to Snapshot 1 ---\n");
    load_snapshot(&vm, obj, snapshot1);
    print_fields(obj);  // state after rewinding to snapshot 1

    // snapshot after the first rewind
    Snapshot *snapshot2 = create_snapshot(&vm, obj);

    // run again to see another state
    run_vm(&vm, obj);  // run until halt again

    // second rewind
    printf("\n--- Rewind to Snapshot 2 ---\n");
    load_snapshot(&vm, obj, snapshot2);
    print_fields(obj);  // state after rewinding to snapshot 2

    // clean up
    free_snapshot(snapshot1);
    free_snapshot(snapshot2);
    free_object(obj);

    return 0;
}
```

Explanation:

1. *Initial setup*: We create an object and define the VM instructions.
2. *First snapshot*: We take a snapshot after the initial state of the VM.
3. *Run VM*: The VM runs through all the instructions, modifying the object.
4. *First rewind*: We rewind to the first snapshot and print the object's state.
5. *Second snapshot*: After the first rewind, we take another snapshot.
6. *Second run*: We run the VM again to change the object's state further.
7. *Second rewind*: We rewind to the second snapshot and print the object's state again.
8. *Clean up*: We free the memory used by the snapshots and the object.

This structure allows for demonstration of the snapshots and rewinds at two
different points in the program, making it easier to understand how the object
state changes over time.



### Example 2

In the provided "Lisp" interpreter, the snapshot mechanism is implemented within the
`Environment` class through two key methods `snapshot()` and `restore(snapshot)`.

1. The `snapshot()` method captures current state of the environment, which includes:

	- *Variable bindings*: A copy of all variable names and their current values stored
    in the bindings dictionary.

	- *Function definitions*: A copy of all user-defined functions stored in the functions
    dictionary.

	- This method allows the interpreter to save its current execution context, enabling
    it to "rewind" to this point later on.

2. The `restore(snapshot)` method takes a snapshot and sets the environment's state back
   to that captured point.

	- The current bindings and functions are replaced with the copies stored in the snapshot.

	- All user-defined variables and functions created after the snapshot are effectively
    removed from the environment.

	- This method is essential for debugging purposes, allowing developers to revert to
    a known good state of the interpreter when an error occurs or unexpected behavior
    is encountered.


#### Context of snapshots

Looking at this from another way: in programming and software development, the ability
to take snapshots of the application state is particularly useful in various scenarios.

- *Debugging*: When testing a program, developers may want to pause execution at certain
  points, analyze the state of the application, and revert back if needed. This can be
  especially beneficial when dealing with complex systems where issues may arise due to
  state changes over time.

- *State management*: In applications with complex state interactions, being able to
  snapshot and restore states allows for better control over how the application behaves
  during different operations. This is critical in systems that rely on transactional
  integrity or rollback capabilities.

- *Time-Travel Debugging (TTD)*: TTD is thus a technique that enables developers to step
  backward in execution, inspecting the state of the program at different times. This can
  simplify debugging by allowing users to explore the history of function calls and variable
  changes.


__Benefits__

1. *Error recovery*: By providing a mechanism to revert to a prior state,
   snapshots allow developers to recover from errors or bugs that occur due
   to incorrect function calls or unexpected behavior.

2. *State visualization*: Snapshots can help in visualizing how the state
   of the environment changes over time, providing insights into how variables
   and functions are manipulated during execution.

3. *Testing and validation*: Snapshots can be used to test specific scenarios
   and validate the state of the application at various checkpoints. This
   ensures that the environment behaves as expected under different conditions.

4. *Improving development efficiency*: With the ability to quickly revert to
   previous states, developers can experiment more freely, knowing they can
   easily backtrack if something goes wrong.


#### Conclusion

In general *Time Travel Debugging* offers a powerful paradigm for debugging that
enhances the developer's ability to trace and diagnose issues effectively. When
integrated into a VM, TTD facilitates a clear and structured approach to managing
state changes and ensures that developers can navigate the complexities of object
states throughout the execution of code.

The snapshot mechanism implemented in the "Lisp" interpreter serves as a 
tool for managing the state of the interpreter during execution. It enhances
debugging capabilities, aids in error recovery, and provides a way to explore
the behavior of the program at different points in time. By incorporating snapshot
functionality, the interpreter becomes more resilient, user-friendly, and easier
to debug, ultimately leading to a more robust development experience.
