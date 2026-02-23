"""
Session Types VM - A minimal implementation of session-typed processes

This VM implements:
- Session types (!, ?, ⊕, &, end)
- Channel mobility: sending/receiving channel endpoints as values (!S.T, ?S.T)
- Recursive session types (μX.S) for servers and loops
- Linear channel usage checking
- Dual channel endpoints
- Process execution with communication
- Type checking for protocols
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Set
from enum import Enum
from queue import Queue
import threading
from abc import ABC, abstractmethod



# SESSION TYPES

class SessionType(ABC):
    """Base class for session types"""
    @abstractmethod
    def dual(self) -> 'SessionType':
        """Return the dual session type"""
        pass
    
    @abstractmethod
    def __str__(self) -> str:
        pass


@dataclass
class Send(SessionType):
    """!T.S - Send a value of type T, then continue with S"""
    value_type: type
    continuation: SessionType
    
    def dual(self) -> SessionType:
        return Receive(self.value_type, self.continuation.dual())
    
    def __str__(self) -> str:
        return f"!{self.value_type.__name__}.{self.continuation}"


@dataclass
class Receive(SessionType):
    """?T.S - Receive a value of type T, then continue with S"""
    value_type: type
    continuation: SessionType
    
    def dual(self) -> SessionType:
        return Send(self.value_type, self.continuation.dual())
    
    def __str__(self) -> str:
        return f"?{self.value_type.__name__}.{self.continuation}"


@dataclass
class Choice(SessionType):
    """⊕{l1: S1, l2: S2, ...} - Offer a choice of branches"""
    branches: Dict[str, SessionType]
    
    def dual(self) -> SessionType:
        return Offer({label: st.dual() for label, st in self.branches.items()})
    
    def __str__(self) -> str:
        branches_str = ", ".join(f"{l}: {s}" for l, s in self.branches.items())
        return f"⊕{{{branches_str}}}"


@dataclass
class Offer(SessionType):
    """&{l1: S1, l2: S2, ...} - Accept a choice from partner"""
    branches: Dict[str, SessionType]
    
    def dual(self) -> SessionType:
        return Choice({label: st.dual() for label, st in self.branches.items()})
    
    def __str__(self) -> str:
        branches_str = ", ".join(f"{l}: {s}" for l, s in self.branches.items())
        return f"&{{{branches_str}}}"


class End(SessionType):
    """End of session"""
    def dual(self) -> SessionType:
        return End()
    
    def __str__(self) -> str:
        return "end"
    
    def __eq__(self, other):
        return isinstance(other, End)
    
    def __hash__(self):
        return hash("end")


@dataclass
class SendChan(SessionType):
    """!S.T  —  Send a channel endpoint with session type S, then continue with T.

    This is the *mobility* constructor. The sent channel's session type (chan_type)
    travels with the endpoint so the receiver knows what protocol to follow.
    Example:  SendChan(?int.end, end)  means "send a channel that will receive an
    int, then this session ends."
    """
    chan_type: SessionType      # session type of the channel being sent
    continuation: SessionType   # what to do after sending it

    def dual(self) -> SessionType:
        # Dual of sending a channel is receiving a channel.
        # The channel's own type is sent as-is--the receiver gets the *same* type
        # description (both sides need to agree on what the delegated channel does).
        return RecvChan(self.chan_type, self.continuation.dual())

    def __str__(self) -> str:
        return f"!({self.chan_type}).{self.continuation}"


@dataclass
class RecvChan(SessionType):
    """?S.T  —  Receive a channel endpoint with session type S, then continue with T."""
    chan_type: SessionType
    continuation: SessionType

    def dual(self) -> SessionType:
        return SendChan(self.chan_type, self.continuation.dual())

    def __str__(self) -> str:
        return f"?({self.chan_type}).{self.continuation}"


@dataclass
class Rec(SessionType):
    """μX.S  —  Recursive session type.

    Allows typing servers and loops. The variable X can appear inside S and
    unfolds to the whole Rec type again.  Example:
        μX. ?int.!int.X   — a server that repeatedly receives and sends an int.
    """
    var: str
    body: SessionType

    def dual(self) -> SessionType:
        return Rec(self.var, self.body.dual())

    def unfold(self) -> SessionType:
        """Replace free occurrences of self.var in body with self."""
        return _subst(self.body, self.var, self)

    def __str__(self) -> str:
        return f"μ{self.var}.{self.body}"


@dataclass
class TypeVar(SessionType):
    """A type variable used inside a Rec body."""
    name: str

    def dual(self) -> SessionType:
        # Duality is pushed through by Rec.dual(); leave var as-is here.
        return TypeVar(self.name)

    def __str__(self) -> str:
        return self.name


def _subst(st: SessionType, var: str, replacement: SessionType) -> SessionType:
    """Substitute TypeVar(var) with replacement inside st (one level deep)."""
    if isinstance(st, TypeVar):
        return replacement if st.name == var else st
    elif isinstance(st, Send):
        return Send(st.value_type, _subst(st.continuation, var, replacement))
    elif isinstance(st, Receive):
        return Receive(st.value_type, _subst(st.continuation, var, replacement))
    elif isinstance(st, SendChan):
        return SendChan(_subst(st.chan_type, var, replacement),
                        _subst(st.continuation, var, replacement))
    elif isinstance(st, RecvChan):
        return RecvChan(_subst(st.chan_type, var, replacement),
                        _subst(st.continuation, var, replacement))
    elif isinstance(st, Choice):
        return Choice({l: _subst(s, var, replacement) for l, s in st.branches.items()})
    elif isinstance(st, Offer):
        return Offer({l: _subst(s, var, replacement) for l, s in st.branches.items()})
    elif isinstance(st, Rec):
        if st.var == var:   # shadowed — don't substitute inside
            return st
        return Rec(st.var, _subst(st.body, var, replacement))
    else:
        return st  # End, unknown leaf


# CHANNELS

@dataclass
class ChannelEndpoint:
    """One end of a channel with a session type"""
    channel_id: str
    session_type: SessionType
    send_queue: Queue  # Queue this endpoint sends to
    recv_queue: Queue  # Queue this endpoint receives from
    used: bool = False  # For linearity checking
    
    def mark_used(self):
        """Mark this endpoint as used (for linearity)"""
        if self.used:
            raise RuntimeError(f"Channel {self.channel_id} used more than once! (Linearity violation)")
        self.used = True


class ChannelManager:
    """Manages channel creation and tracks linearity"""
    def __init__(self):
        self.channels: Dict[str, tuple[ChannelEndpoint, ChannelEndpoint]] = {}
        self.next_id = 0
        self.lock = threading.Lock()
    
    def create_channel(self, session_type: SessionType) -> tuple[ChannelEndpoint, ChannelEndpoint]:
        """Create a pair of dual channel endpoints"""
        with self.lock:
            channel_id = f"ch_{self.next_id}"
            self.next_id += 1
            
            # Two queues: A->B and B->A
            queue_a_to_b = Queue()
            queue_b_to_a = Queue()
            
            # Create dual endpoints with crossed queues
            # Endpoint A sends to queue_a_to_b, receives from queue_b_to_a
            # Endpoint B sends to queue_b_to_a, receives from queue_a_to_b
            endpoint1 = ChannelEndpoint(channel_id + "_A", session_type, queue_a_to_b, queue_b_to_a)
            endpoint2 = ChannelEndpoint(channel_id + "_B", session_type.dual(), queue_b_to_a, queue_a_to_b)
            
            self.channels[channel_id] = (endpoint1, endpoint2)
            
            print(f"✓ Created channel {channel_id}")
            print(f"  Endpoint A: {session_type}")
            print(f"  Endpoint B: {session_type.dual()}")
            
            return endpoint1, endpoint2
    
    def check_linearity(self):
        """Check that all channels have been used exactly once"""
        violations = []
        for ch_id, (ep1, ep2) in self.channels.items():
            if not ep1.used:
                violations.append(f"Channel {ep1.channel_id} never used")
            if not ep2.used:
                violations.append(f"Channel {ep2.channel_id} never used")
        
        if violations:
            raise RuntimeError("Linearity violations:\n" + "\n".join(violations))


# HELPERS FOR MOBILITY & RECURSIVE TYPES

def _unfold_if_rec(st: SessionType) -> SessionType:
    """If st is a Rec type, unfold it one level. Otherwise return as-is."""
    if isinstance(st, Rec):
        return st.unfold()
    return st


def _session_types_equal(a: SessionType, b: SessionType) -> bool:
    """Structural equality check for session types, handling Rec unfolding."""
    # Unfold one level of recursion before comparing
    a = _unfold_if_rec(a)
    b = _unfold_if_rec(b)

    if type(a) != type(b):
        return False
    if isinstance(a, End):
        return True
    if isinstance(a, (Send, Receive)):
        return a.value_type == b.value_type and _session_types_equal(a.continuation, b.continuation)
    if isinstance(a, (SendChan, RecvChan)):
        return (_session_types_equal(a.chan_type, b.chan_type) and
                _session_types_equal(a.continuation, b.continuation))
    if isinstance(a, (Choice, Offer)):
        return (set(a.branches.keys()) == set(b.branches.keys()) and
                all(_session_types_equal(a.branches[l], b.branches[l]) for l in a.branches))
    if isinstance(a, Rec):
        # Same variable and structurally equal bodies
        return a.var == b.var and _session_types_equal(a.body, b.body)
    if isinstance(a, TypeVar):
        return a.name == b.name
    return False


# PROCESSES

class Process(ABC):
    """Base class for processes"""
    @abstractmethod
    def run(self, env: Dict[str, Any]):
        """Execute the process with given environment"""
        pass


@dataclass
class SendProcess(Process):
    """Send a value (or channel endpoint) on a channel.

    When the channel's session type is Send(T, S): sends a plain value of type T.
    When the channel's session type is SendChan(S', S): sends a channel endpoint
    whose remaining session type must match S'.  This is *channel mobility* —
    the endpoint leaves the sender's scope (lineariy: it is removed from env).
    """
    channel_var: str   # variable holding the *carrier* channel
    value: Any         # literal value  OR  variable name (str) of endpoint to delegate
    continuation: Process

    def run(self, env: Dict[str, Any]):
        channel: ChannelEndpoint = env[self.channel_var]

        # Unfold recursive types transparently
        st = _unfold_if_rec(channel.session_type)

        if isinstance(st, SendChan):
            # MOBILITY PATH 
            # Resolve the endpoint to send (must be a variable name)
            if not isinstance(self.value, str) or self.value not in env:
                raise ValueError(f"SendChan: expected a variable name in env, got {self.value!r}")

            delegated: ChannelEndpoint = env[self.value]
            if not isinstance(delegated, ChannelEndpoint):
                raise TypeError(f"SendChan: variable '{self.value}' is not a ChannelEndpoint")

            # Check the delegated endpoint's session type matches what the type says
            if not _session_types_equal(delegated.session_type, st.chan_type):
                raise TypeError(
                    f"SendChan type mismatch: expected {st.chan_type}, "
                    f"got {delegated.session_type} on {delegated.channel_id}"
                )

            # Linearity: remove the delegated endpoint from *this* process's scope
            del env[self.value]

            # Mark carrier as used, send the endpoint object itself
            channel.mark_used()
            channel.send_queue.put(delegated)
            print(f"  → Delegated channel {delegated.channel_id} "
                  f"(type: {delegated.session_type}) via {channel.channel_id}")

            channel.session_type = st.continuation
            channel.used = False

        elif isinstance(st, Send):
            # PLAIN VALUE PATH
            val = env[self.value] if isinstance(self.value, str) and self.value in env else self.value
            expected_type = st.value_type
            if not isinstance(val, expected_type):
                raise TypeError(f"Expected {expected_type.__name__}, got {type(val).__name__}")

            channel.mark_used()
            channel.send_queue.put(val)
            print(f"  → Sent {val} on {channel.channel_id}")

            channel.session_type = st.continuation
            channel.used = False

        else:
            raise TypeError(f"SendProcess: expected Send or SendChan type, got {channel.session_type}")

        if self.continuation:
            self.continuation.run(env)


@dataclass
class ReceiveProcess(Process):
    """Receive a value (or channel endpoint) on a channel.

    When the channel's session type is Receive(T, S): binds a plain value.
    When the channel's session type is RecvChan(S', S): binds a received
    ChannelEndpoint into env[bind_var].  The received endpoint's session type
    is checked against S' and can then be used by the continuation.
    """
    channel_var: str
    bind_var: str
    continuation: Process

    def run(self, env: Dict[str, Any]):
        channel: ChannelEndpoint = env[self.channel_var]

        # Unfold recursive types transparently
        st = _unfold_if_rec(channel.session_type)

        if isinstance(st, RecvChan):
            # MOBILITY PATH
            channel.mark_used()

            # Block until the delegated endpoint arrives
            delegated: ChannelEndpoint = channel.recv_queue.get()
            if not isinstance(delegated, ChannelEndpoint):
                raise TypeError(f"RecvChan: expected a ChannelEndpoint, got {type(delegated)}")

            # Verify the received endpoint matches the promised type
            if not _session_types_equal(delegated.session_type, st.chan_type):
                raise TypeError(
                    f"RecvChan type mismatch: expected {st.chan_type}, "
                    f"got {delegated.session_type} on {delegated.channel_id}"
                )

            print(f"  ← Received channel {delegated.channel_id} "
                  f"(type: {delegated.session_type}) via {channel.channel_id}")

            channel.session_type = st.continuation
            channel.used = False

            # Bring the delegated endpoint into scope
            env[self.bind_var] = delegated

        elif isinstance(st, Receive):
            # PLAIN VALUE PATH
            channel.mark_used()
            value = channel.recv_queue.get()
            print(f"  ← Received {value} on {channel.channel_id}")

            expected_type = st.value_type
            if not isinstance(value, expected_type):
                raise TypeError(f"Expected {expected_type.__name__}, got {type(value).__name__}")

            channel.session_type = st.continuation
            channel.used = False
            env[self.bind_var] = value

        else:
            raise TypeError(f"ReceiveProcess: expected Receive or RecvChan type, got {channel.session_type}")

        if self.continuation:
            self.continuation.run(env)


@dataclass
class SelectProcess(Process):
    """Send a choice label and continue with that branch"""
    channel_var: str
    label: str
    continuation: Process
    
    def run(self, env: Dict[str, Any]):
        channel: ChannelEndpoint = env[self.channel_var]
        
        # Type check
        if not isinstance(channel.session_type, Choice):
            raise TypeError(f"Expected Choice type, got {channel.session_type}")
        
        if self.label not in channel.session_type.branches:
            raise ValueError(f"Label '{self.label}' not in {list(channel.session_type.branches.keys())}")
        
        # Mark channel as used (linearity)
        channel.mark_used()
        
        # Send choice label
        channel.send_queue.put(self.label)
        print(f"  ⊕ Selected '{self.label}' on {channel.channel_id}")
        
        # Update channel type to selected branch
        channel.session_type = channel.session_type.branches[self.label]
        channel.used = False  # Can use continuation
        
        # Run continuation
        if self.continuation:
            self.continuation.run(env)


@dataclass
class OfferProcess(Process):
    """Receive a choice label and branch accordingly"""
    channel_var: str
    branches: Dict[str, Process]  # label -> process
    
    def run(self, env: Dict[str, Any]):
        channel: ChannelEndpoint = env[self.channel_var]
        
        # Type check
        if not isinstance(channel.session_type, Offer):
            raise TypeError(f"Expected Offer type, got {channel.session_type}")
        
        if set(self.branches.keys()) != set(channel.session_type.branches.keys()):
            raise ValueError(f"Branch labels don't match: {self.branches.keys()} vs {channel.session_type.branches.keys()}")
        
        # Mark channel as used (linearity)
        channel.mark_used()
        
        # Receive choice label
        label = channel.recv_queue.get()
        print(f"  & Received choice '{label}' on {channel.channel_id}")
        
        # Update channel type to selected branch
        channel.session_type = channel.session_type.branches[label]
        channel.used = False  # Can use continuation
        
        # Run selected branch
        self.branches[label].run(env)


@dataclass
class CloseProcess(Process):
    """Close a channel (must be at End type)"""
    channel_var: str
    
    def run(self, env: Dict[str, Any]):
        channel: ChannelEndpoint = env[self.channel_var]
        
        # Type check
        if not isinstance(channel.session_type, End):
            raise TypeError(f"Cannot close channel, expected End but got {channel.session_type}")
        
        # Mark channel as used (linearity)
        channel.mark_used()
        
        print(f"  ✓ Closed {channel.channel_id}")


@dataclass
class ParallelProcess(Process):
    """Run two processes in parallel"""
    proc1: Process
    proc2: Process
    
    def run(self, env: Dict[str, Any]):
        # Copy environment for each process
        env1 = env.copy()
        env2 = env.copy()
        
        # Run in parallel threads
        t1 = threading.Thread(target=lambda: self.proc1.run(env1))
        t2 = threading.Thread(target=lambda: self.proc2.run(env2))
        
        t1.start()
        t2.start()
        
        t1.join()
        t2.join()



# VM

class SessionTypesVM:
    """Virtual machine for executing session-typed processes"""
    
    def __init__(self):
        self.channel_manager = ChannelManager()
    
    def create_channel(self, session_type: SessionType) -> tuple[ChannelEndpoint, ChannelEndpoint]:
        """Create a new channel with the given session type"""
        return self.channel_manager.create_channel(session_type)
    
    def run(self, process: Process, env: Dict[str, Any] = None):
        """Execute a process"""
        if env is None:
            env = {}
        
        print("\n" + "="*60)
        print("EXECUTING PROCESS")
        print("="*60)
        
        try:
            process.run(env)
            print("\n" + "="*60)
            print("EXECUTION COMPLETE")
            print("="*60)
            
            # Check linearity
            # self.channel_manager.check_linearity()
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            raise


# HELPERS

def End_() -> End:
    """Helper to create End type"""
    return End()

def Send_(value_type: type, continuation: SessionType) -> Send:
    """Helper to create Send type"""
    return Send(value_type, continuation)

def Recv_(value_type: type, continuation: SessionType) -> Receive:
    """Helper to create Receive type"""
    return Receive(value_type, continuation)

def Choice_(branches: Dict[str, SessionType]) -> Choice:
    """Helper to create Choice type"""
    return Choice(branches)

def Offer_(branches: Dict[str, SessionType]) -> Offer:
    """Helper to create Offer type"""
    return Offer(branches)

def SendChan_(chan_type: SessionType, continuation: SessionType) -> SendChan:
    """Helper to create SendChan (mobility send) type"""
    return SendChan(chan_type, continuation)

def RecvChan_(chan_type: SessionType, continuation: SessionType) -> RecvChan:
    """Helper to create RecvChan (mobility receive) type"""
    return RecvChan(chan_type, continuation)

def Rec_(var: str, body: SessionType) -> Rec:
    """Helper to create recursive session type μvar.body"""
    return Rec(var, body)

def Var_(name: str) -> TypeVar:
    """Helper to create a type variable (for use inside Rec bodies)"""
    return TypeVar(name)


if __name__ == "__main__":
    print("session_vm: import this module and see examples.py for usage.")
