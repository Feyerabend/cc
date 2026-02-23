"""
Session Types VM - A minimal implementation of session-typed processes

This VM implements:
- Session types (!, ?, ⊕, &, end)
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


# PROCESSES

class Process(ABC):
    """Base class for processes"""
    @abstractmethod
    def run(self, env: Dict[str, Any]):
        """Execute the process with given environment"""
        pass


@dataclass
class SendProcess(Process):
    """Send a value on a channel"""
    channel_var: str  # Variable name holding channel
    value: Any
    continuation: Process
    
    def run(self, env: Dict[str, Any]):
        channel: ChannelEndpoint = env[self.channel_var]
        
        # Type check
        if not isinstance(channel.session_type, Send):
            raise TypeError(f"Expected Send type, got {channel.session_type}")
        
        expected_type = channel.session_type.value_type
        if not isinstance(self.value, expected_type):
            raise TypeError(f"Expected {expected_type.__name__}, got {type(self.value).__name__}")
        
        # Mark channel as used (linearity)
        channel.mark_used()
        
        # Send message
        channel.send_queue.put(self.value)
        print(f"  → Sent {self.value} on {channel.channel_id}")
        
        # Update channel type to continuation
        channel.session_type = channel.session_type.continuation
        channel.used = False  # Can use continuation
        
        # Run continuation
        if self.continuation:
            self.continuation.run(env)


@dataclass
class ReceiveProcess(Process):
    """Receive a value on a channel"""
    channel_var: str
    bind_var: str  # Variable to bind received value to
    continuation: Process
    
    def run(self, env: Dict[str, Any]):
        channel: ChannelEndpoint = env[self.channel_var]
        
        # Type check
        if not isinstance(channel.session_type, Receive):
            raise TypeError(f"Expected Receive type, got {channel.session_type}")
        
        # Mark channel as used (linearity)
        channel.mark_used()
        
        # Receive message (blocking)
        value = channel.recv_queue.get()
        print(f"  ← Received {value} on {channel.channel_id}")
        
        # Type check received value
        expected_type = channel.session_type.value_type
        if not isinstance(value, expected_type):
            raise TypeError(f"Expected {expected_type.__name__}, got {type(value).__name__}")
        
        # Update channel type to continuation
        channel.session_type = channel.session_type.continuation
        channel.used = False  # Can use continuation
        
        # Bind value and run continuation
        env[self.bind_var] = value
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
