# CSP Language Implementation (Enhanced Hoare-style with Optional Logging)
from dataclasses import dataclass
from typing import Optional, Set, Any, Dict, List, Tuple
from collections import deque, defaultdict
import uuid
import time
from itertools import count

# --- Data Structures for CSP Grammar ---

# Actions
@dataclass
class Send:
    channel: str
    message: Any

@dataclass
class Receive:
    channel: str
    variable: str

@dataclass
class Tau:
    pass

Action = Send | Receive | Tau

# Conditions
@dataclass
class Eq:
    variable: str
    value: Any

@dataclass
class LogicalOp:
    op: str  # "and" or "or"
    cond1: 'Condition'
    cond2: 'Condition'

Condition = Eq | LogicalOp

# Processes
@dataclass
class STOP:
    pass

@dataclass
class SKIP:
    pass

@dataclass
class Prefix:
    action: Action
    process: 'Process'

@dataclass
class Seq:
    p1: 'Process'
    p2: 'Process'

@dataclass
class Choice:
    p1: 'Process'
    p2: 'Process'

@dataclass
class ExtChoice:
    p1: 'Process'
    p2: 'Process'

@dataclass
class Parallel:
    p1: 'Process'
    p2: 'Process'
    channels: Set[str]

@dataclass
class If:
    condition: Condition
    p1: 'Process'
    p2: 'Process'

@dataclass
class Rec:
    var: str
    process: 'Process'

@dataclass
class Var:
    var: str

Process = STOP | SKIP | Prefix | Seq | Choice | ExtChoice | Parallel | If | Rec | Var


class Channel:
    def __init__(self, name: str):
        self.name = name
        self.waiting: List[Tuple[Action, Process, 'CSPInterpreter']] = []

    def try_match(self, action: Action, continuation: Process, interpreter: 'CSPInterpreter') -> Optional[Tuple[Process, bool]]:
        if interpreter.verbose:
            print(f"[Channel {self.name}] Attempting to match action {action}")
        if isinstance(action, Send):
            for i, (waiting_action, waiting_cont, waiting_interpreter) in enumerate(self.waiting):
                if isinstance(waiting_action, Receive):
                    waiting_interpreter.state.set_var(waiting_action.variable, action.message)
                    self.waiting.pop(i)
                    if interpreter.verbose:
                        print(f"[Channel {self.name}] Rendezvous: Sent {action.message} to {waiting_action.variable} in interpreter {waiting_interpreter.id}")
                    return continuation, True
            self.waiting.append((action, continuation, interpreter))
            if interpreter.verbose:
                print(f"[Channel {self.name}] No match for Send, process {interpreter.id} blocked")
            return None, False
        elif isinstance(action, Receive):
            for i, (waiting_action, waiting_cont, waiting_interpreter) in enumerate(self.waiting):
                if isinstance(waiting_action, Send):
                    interpreter.state.set_var(action.variable, waiting_action.message)
                    self.waiting.pop(i)
                    if interpreter.verbose:
                        print(f"[Channel {self.name}] Rendezvous: Received {waiting_action.message} into {action.variable} in interpreter {interpreter.id}")
                    return continuation, True
            self.waiting.append((action, continuation, interpreter))
            if interpreter.verbose:
                print(f"[Channel {self.name}] No match for Receive, process {interpreter.id} blocked")
            return None, False
        if interpreter.verbose:
            print(f"[Channel {self.name}] Tau action, no channel interaction")
        return continuation, True


class State:
    def __init__(self):
        self.variables: Dict[str, Any] = {}
        self.channels: Dict[str, Channel] = {}

    def get_channel(self, name: str) -> Channel:
        if name not in self.channels:
            self.channels[name] = Channel(name)
            print(f"[State] Created channel {name}")
        return self.channels[name]

    def set_var(self, var: str, value: Any):
        print(f"[State] Set variable {var} = {value}")
        self.variables[var] = value

    def get_var(self, var: str) -> Any:
        value = self.variables.get(var)
        print(f"[State] Get variable {var} = {value}")
        return value


def evaluate_condition(cond: Condition, state: State, verbose: bool) -> bool:
    if verbose:
        print(f"[Condition] Evaluating {cond}")
    if isinstance(cond, Eq):
        result = state.get_var(cond.variable) == cond.value
        if verbose:
            print(f"[Condition] Eq({cond.variable}, {cond.value}) = {result}")
        return result
    elif isinstance(cond, LogicalOp):
        left = evaluate_condition(cond.cond1, state, verbose)
        right = evaluate_condition(cond.cond2, state, verbose)
        result = (left and right) if cond.op == "and" else (left or right)
        if verbose:
            print(f"[Condition] {cond.op}({left}, {right}) = {result}")
        return result
    raise ValueError(f"Unknown condition: {cond}")


class CSPInterpreter:
    def __init__(self, env: Optional[Dict[str, Process]] = None, verbose: bool = False):
        self.state = State()
        self.env = env if env is not None else {}
        self.scheduler = deque()
        self.id = str(uuid.uuid4())[:8]
        self.verbose = verbose
        self.dependency_graph: Dict[str, Set[str]] = defaultdict(set)
        if self.verbose:
            print(f"[Interpreter {self.id}] Initialized")

    def step(self, process: Process) -> Optional[Process]:
        if self.verbose:
            print(f"[Interpreter {self.id}] Stepping process: {process}")
        if isinstance(process, STOP):
            if self.verbose:
                print(f"[Interpreter {self.id}] Process stopped")
            return None
        elif isinstance(process, SKIP):
            if self.verbose:
                print(f"[Interpreter {self.id}] Process skipped")
            return None
        elif isinstance(process, Prefix):
            cont, executed = self.execute_action(process.action, process.process)
            if executed:
                if self.verbose:
                    print(f"[Interpreter {self.id}] Prefix action executed, continuing to {cont}")
                return cont
            if self.verbose:
                print(f"[Interpreter {self.id}] Prefix action blocked, staying at {process}")
            return process
        elif isinstance(process, Seq):
            if isinstance(process.p1, (STOP, SKIP)):
                if self.verbose:
                    print(f"[Interpreter {self.id}] Seq: First process terminated, moving to {process.p2}")
                return process.p2
            next_p1 = self.step(process.p1)
            if next_p1 is None:
                if self.verbose:
                    print(f"[Interpreter {self.id}] Seq: First process done, moving to {process.p2}")
                return process.p2
            if self.verbose:
                print(f"[Interpreter {self.id}] Seq: Continuing with {next_p1}")
            return Seq(next_p1, process.p2)
        elif isinstance(process, Choice):
            import random
            chosen = random.choice([process.p1, process.p2])
            if self.verbose:
                print(f"[Interpreter {self.id}] Non-deterministic choice: picked {chosen}")
            return chosen
        elif isinstance(process, ExtChoice):
            if self.verbose:
                print(f"[Interpreter {self.id}] External choice: picking p1 (mock)")
            return process.p1
        elif isinstance(process, Parallel):
            if self.verbose:
                print(f"[Interpreter {self.id}] Parallel: Scheduling processes on channels {process.channels}")
            for chan in process.channels:
                self.state.get_channel(chan)
            interp1 = CSPInterpreter(self.env, self.verbose)
            interp2 = CSPInterpreter(self.env, self.verbose)
            self.scheduler.append((process.p1, interp1, process.channels))
            self.scheduler.append((process.p2, interp2, process.channels))
            return None
        elif isinstance(process, If):
            if self.verbose:
                print(f"[Interpreter {self.id}] If: Evaluating condition")
            if evaluate_condition(process.condition, self.state, self.verbose):
                if self.verbose:
                    print(f"[Interpreter {self.id}] If: Condition true, picking {process.p1}")
                return process.p1
            if self.verbose:
                print(f"[Interpreter {self.id}] If: Condition false, picking {process.p2}")
            return process.p2
        elif isinstance(process, Rec):
            if self.verbose:
                print(f"[Interpreter {self.id}] Rec: Binding {process.var} to {process.process}")
            self.env[process.var] = process.process
            return process.process
        elif isinstance(process, Var):
            if process.var in self.env:
                if self.verbose:
                    print(f"[Interpreter {self.id}] Var: Unfolding {process.var} to {self.env[process.var]}")
                return self.env[process.var]
            if self.verbose:
                print(f"[Interpreter {self.id}] Unbound recursive variable {process.var}")
            return STOP()
        raise ValueError(f"Unknown process: {process}")

    def execute_action(self, action: Action, continuation: Process) -> Tuple[Optional[Process], bool]:
        if self.verbose:
            print(f"[Interpreter {self.id}] Executing action: {action}")
        if isinstance(action, Send) or isinstance(action, Receive):
            channel = self.state.get_channel(action.channel)
            cont, executed = channel.try_match(action, continuation, self)
            if not executed:
                if self.verbose:
                    print(f"[Interpreter {self.id}] Action blocked, updating dependencies")
                for _, _, other_interp in channel.waiting:
                    if other_interp.id != self.id:
                        self.dependency_graph[self.id].add(other_interp.id)
                        if self.verbose:
                            print(f"[Interpreter {self.id}] Added dependency: {self.id} -> {other_interp.id}")
            else:
                self.dependency_graph[self.id].clear()
                if self.verbose:
                    print(f"[Interpreter {self.id}] Action executed, cleared dependencies")
            return cont, executed
        elif isinstance(action, Tau):
            if self.verbose:
                print(f"[Interpreter {self.id}] Silent action (tau)")
            return continuation, True
        raise ValueError(f"Unknown action: {action}")

    def detect_deadlock(self) -> bool:
        if self.verbose:
            print(f"[Interpreter {self.id}] Checking for deadlock")
        if not self.scheduler:
            if self.verbose:
                print(f"[Interpreter {self.id}] No scheduled processes, no deadlock")
            return False

        all_blocked = True
        for process, _, _ in self.scheduler:
            if not isinstance(process, Prefix) or not isinstance(process.action, (Send, Receive)):
                all_blocked = False
                if self.verbose:
                    print(f"[Interpreter {self.id}] Found non-blocked process: {process}")
                break

        if not all_blocked:
            if self.verbose:
                print(f"[Interpreter {self.id}] Not all processes blocked, no deadlock")
            return False

        visited = set()
        rec_stack = set()

        def dfs(node: str) -> bool:
            visited.add(node)
            rec_stack.add(node)
            for neighbor in self.dependency_graph[node]:
                if self.verbose:
                    print(f"[Interpreter {self.id}] DFS: Checking {node} -> {neighbor}")
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    if self.verbose:
                        print(f"[Interpreter {self.id}] Cycle detected: {node} -> {neighbor}")
                    return True
            rec_stack.remove(node)
            return False

        for process, interp, _ in self.scheduler:
            if interp.id not in visited:
                if dfs(interp.id):
                    if self.verbose:
                        print(f"[Interpreter {self.id}] Deadlock detected: Cycle in dependency graph")
                    return True

        for channel in self.state.channels.values():
            sends = [a for a, _, _ in channel.waiting if isinstance(a, Send)]
            receives = [a for a, _, _ in channel.waiting if isinstance(a, Receive)]
            if sends and receives:
                if self.verbose:
                    print(f"[Interpreter {self.id}] Found matching Send/Receive on {channel.name}, no deadlock")
                return False

        if any(channel.waiting for channel in self.state.channels.values()):
            if self.verbose:
                print(f"[Interpreter {self.id}] Deadlock detected: All processes blocked with no matching actions")
            return True
        return False

    def run_scheduler(self, max_steps: int = 100, time_limit: float = float('inf')) -> bool:
        start_time = time.time()
        steps = 0
        if self.verbose:
            print(f"[Interpreter {self.id}] Starting scheduler with {len(self.scheduler)} processes")
        while self.scheduler and steps < max_steps and (time.time() - start_time) < time_limit:
            if self.detect_deadlock():
                return False
            process, interp, sync_channels = self.scheduler.popleft()
            if self.verbose:
                print(f"[Interpreter {self.id}] Scheduling process {process} in interpreter {interp.id}")
            next_process = interp.step(process)
            if next_process is not None:
                if isinstance(next_process, Prefix) and isinstance(next_process.action, (Send, Receive)):
                    if next_process.action.channel in sync_channels:
                        _, executed = interp.execute_action(next_process.action, next_process.process)
                        if not executed:
                            self.scheduler.append((next_process, interp, sync_channels))
                            if self.verbose:
                                print(f"[Interpreter {self.id}] Process blocked on sync channel, requeued")
                            continue
                self.scheduler.append((next_process, interp, sync_channels))
                if self.verbose:
                    print(f"[Interpreter {self.id}] Process continued, requeued")
            else:
                if self.verbose:
                    print(f"[Interpreter {self.id}] Process terminated")
            steps += 1
        if (time.time() - start_time) >= time_limit:
            if self.verbose:
                print(f"[Interpreter {self.id}] Execution halted: Time limit exceeded")
            return False
        if steps >= max_steps:
            if self.verbose:
                print(f"[Interpreter {self.id}] Max steps reached")
            return False
        if self.verbose:
            print(f"[Interpreter {self.id}] Scheduler completed")
        return True

    def run(self, process: Process, max_steps: int = 100, time_limit: float = float('inf')) -> bool:
        start_time = time.time()
        current = process
        steps = 0
        if self.verbose:
            print(f"[Interpreter {self.id}] Starting execution of {process}")
        while current is not None and steps < max_steps and (time.time() - start_time) < time_limit:
            current = self.step(current)
            steps += 1
            if self.scheduler:
                if self.verbose:
                    print(f"[Interpreter {self.id}] Switching to scheduler for parallel processes")
                if not self.run_scheduler(max_steps - steps, time_limit - (time.time() - start_time)):
                    return False
                break
        if (time.time() - start_time) >= time_limit:
            if self.verbose:
                print(f"[Interpreter {self.id}] Execution halted: Time limit exceeded")
            return False
        if steps >= max_steps:
            if self.verbose:
                print(f"[Interpreter {self.id}] Max steps reached")
            return False
        if self.verbose:
            print(f"[Interpreter {self.id}] Execution completed")
        return True



# Example: Demonstrates various CSP processes with verbose logging
if __name__ == "__main__":

    # Producer: Sends a fixed message that matches consumer's condition
    # Uses Rec for looping, Prefix for sending, and Tau for pacing
    producer = Rec(
        "P",
        Seq(
            Prefix(
                Send("data_channel", {"id": 2, "value": "item", "data": [1, 2, 3]}),
                SKIP()
            ),
            Seq(
                Prefix(Tau(), Var("P")),  # Silent action before looping
                STOP()
            )
        )
    )

    # Consumer: Receives messages, uses If to check conditions, and stops after id=2
    # Demonstrates Seq, If, and Rec
    consumer = Rec(
        "C",
        Seq(
            Prefix(Receive("data_channel", "msg"), SKIP()),
            If(
                Eq("msg", {"id": 2, "value": "item", "data": [1, 2, 3]}),
                STOP(),
                Var("C")
            )
        )
    )

    # Monitor: Makes choices between sending status or skipping
    # Uses Choice and ExtChoice to demonstrate decision points
    monitor = Rec(
        "M",
        Choice(
            Prefix(Send("status_channel", "active"), Var("M")),
            ExtChoice(
                Prefix(Tau(), Var("M")),
                SKIP()
            )
        )
    )

    # Deadlocker: Receives on data_channel without condition
    # Demonstrates a process that can receive unmatched messages
    deadlocker = Prefix(Receive("data_channel", "dummy"), STOP())

    # Main process: Combines all processes in parallel with synchronized channels
    main_process = Parallel(
        producer,
        Parallel(
            consumer,
            Parallel(
                monitor,
                deadlocker,
                {"data_channel", "status_channel"}
            ),
            {"data_channel", "status_channel"}
        ),
        {"data_channel"}
    )

    interpreter = CSPInterpreter(verbose=True)
    print("Test CSP example with verbose logging:")
    interpreter.run(main_process, max_steps=50, time_limit=5.0)



