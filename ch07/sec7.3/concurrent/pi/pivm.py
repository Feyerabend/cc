import queue
import threading
import time
import uuid
import copy
import random
from typing import Dict, List, Tuple, Any, Callable, Optional, Set, Union

class Value:
    def __init__(self, value: Any):
        self.value = value
    
    def __repr__(self):
        return f"{self.value}"

class Channel:
    def __init__(self, name: str):
        self.name = name
        self.q = queue.Queue()
        self.closed = False
    
    def send(self, value: Any) -> bool:
        if self.closed:
            return False
        self.q.put(value)
        return True
    
    def receive(self) -> Tuple[Any, bool]:
        if self.closed and self.q.empty():
            return None, False
        return self.q.get(), True
    
    def close(self) -> None:
        self.closed = True
    
    def __repr__(self):
        return f"Channel({self.name})"

class ProcessEnvironment:
    def __init__(self):
        self.variables = {}
        self.pid = str(uuid.uuid4())[:8]
    
    def set(self, name: str, value: Any) -> None:
        self.variables[name] = value
    
    def get(self, name: str) -> Any:
        if name in self.variables:
            return self.variables[name]
        return name
    
    def copy(self):
        new_env = ProcessEnvironment()
        new_env.variables = copy.deepcopy(self.variables)
        return new_env

class Process:
    def __init__(self, name: str, steps: List[Tuple], env: Optional[ProcessEnvironment] = None):
        self.name = name
        self.steps = steps
        self.env = env or ProcessEnvironment()
        self.terminated = False
        self.waiting = False
        self.waiting_on = None
    
    def run(self, channels: Dict[str, Channel], process_registry: Dict[str, 'Process']) -> None:
        step_index = 0
        
        while step_index < len(self.steps) and not self.terminated:
            op, args = self.steps[step_index]
            
            if op == 'send':
                ch_name, val_expr = args
                ch_resolved = self.resolve_value(ch_name)
                val_resolved = self.resolve_value(val_expr)
                
                if ch_resolved in channels:
                    if channels[ch_resolved].send(val_resolved):
                        print(f"{self.name}[{self.env.pid}] sends {val_resolved} on {ch_resolved}")
                    else:
                        print(f"{self.name}[{self.env.pid}] failed to send on closed channel {ch_resolved}")
                else:
                    print(f"{self.name}[{self.env.pid}] error: channel {ch_resolved} not found")
                    
                step_index += 1
                
            elif op == 'receive':
                ch_name, var = args
                ch_resolved = self.resolve_value(ch_name)
                
                if ch_resolved in channels:
                    val, success = channels[ch_resolved].receive()
                    if success:
                        self.env.set(var, val)
                        print(f"{self.name}[{self.env.pid}] receives {val} from {ch_resolved} as {var}")
                    else:
                        print(f"{self.name}[{self.env.pid}] failed to receive from closed channel {ch_resolved}")
                else:
                    print(f"{self.name}[{self.env.pid}] error: channel {ch_resolved} not found")
                    
                step_index += 1
                
            elif op == 'new_channel':
                ch_name = args
                ch_id = f"{ch_name}_{uuid.uuid4().hex[:6]}"
                channels[ch_id] = Channel(ch_id)
                self.env.set(ch_name, ch_id)
                print(f"{self.name}[{self.env.pid}] creates new channel {ch_id}")
                step_index += 1
                
            elif op == 'close':
                ch_name = args
                ch_resolved = self.resolve_value(ch_name)
                
                if ch_resolved in channels:
                    channels[ch_resolved].close()
                    print(f"{self.name}[{self.env.pid}] closes channel {ch_resolved}")
                else:
                    print(f"{self.name}[{self.env.pid}] error: cannot close non-existent channel {ch_resolved}")
                    
                step_index += 1
                
            elif op == 'spawn':
                proc_name, proc_steps = args
                new_proc = Process(proc_name, proc_steps, self.env.copy())
                process_registry[new_proc.env.pid] = new_proc
                
                thread = threading.Thread(target=new_proc.run, args=(channels, process_registry))
                thread.daemon = True
                thread.start()
                
                print(f"{self.name}[{self.env.pid}] spawns {proc_name}[{new_proc.env.pid}]")
                step_index += 1
                
            elif op == 'select':
                options = args
                valid_options = []
                
                for i, (condition, next_steps) in enumerate(options):
                    cond_op, cond_args = condition
                    
                    if cond_op == 'receive_ready':
                        ch_name = cond_args
                        ch_resolved = self.resolve_value(ch_name)
                        
                        if ch_resolved in channels and not channels[ch_resolved].q.empty():
                            valid_options.append((i, next_steps))
                    
                    elif cond_op == 'default':
                        valid_options.append((i, next_steps))
                
                if valid_options:
                    choice_idx, next_steps = random.choice(valid_options)
                    print(f"{self.name}[{self.env.pid}] selects option {choice_idx}")
                    
                    for ns in next_steps:
                        self.steps.insert(step_index + 1, ns)
                        
                step_index += 1
                
            elif op == 'set':
                var, expr = args
                val = self.resolve_value(expr)
                self.env.set(var, val)
                print(f"{self.name}[{self.env.pid}] sets {var} = {val}")
                step_index += 1
                
            elif op == 'log':
                message = self.resolve_value(args)
                print(f"{self.name}[{self.env.pid}] log: {message}")
                step_index += 1
                
            elif op == 'if':
                condition, true_steps, false_steps = args
                
                if self.evaluate_condition(condition):
                    print(f"{self.name}[{self.env.pid}] condition true, taking true branch")
                    for step in reversed(true_steps):
                        self.steps.insert(step_index + 1, step)
                else:
                    print(f"{self.name}[{self.env.pid}] condition false, taking false branch")
                    for step in reversed(false_steps):
                        self.steps.insert(step_index + 1, step)
                        
                step_index += 1
                
            elif op == 'replicate':
                proc_name, proc_steps = args
                
                def spawn_replica():
                    new_proc = Process(proc_name, copy.deepcopy(proc_steps), self.env.copy())
                    process_registry[new_proc.env.pid] = new_proc
                    
                    thread = threading.Thread(target=new_proc.run, args=(channels, process_registry))
                    thread.daemon = True
                    thread.start()
                    
                    print(f"{self.name}[{self.env.pid}] replicates {proc_name}[{new_proc.env.pid}]")
                    
                    spawn_replica()
                
                spawn_replica()
                step_index += 1
                
            elif op == 'stop':
                print(f"{self.name}[{self.env.pid}] halts.")
                self.terminated = True
                del process_registry[self.env.pid]
                return
                
            time.sleep(0.5)
    
    def resolve_value(self, expr):
        if isinstance(expr, tuple) and len(expr) >= 1:
            op = expr[0]
            
            if op == 'var':
                return self.env.get(expr[1])
            elif op == 'add':
                return self.resolve_value(expr[1]) + self.resolve_value(expr[2])
            elif op == 'sub':
                return self.resolve_value(expr[1]) - self.resolve_value(expr[2])
            elif op == 'mul':
                return self.resolve_value(expr[1]) * self.resolve_value(expr[2])
            elif op == 'div':
                return self.resolve_value(expr[1]) / self.resolve_value(expr[2])
            elif op == 'eq':
                return self.resolve_value(expr[1]) == self.resolve_value(expr[2])
            elif op == 'ne':
                return self.resolve_value(expr[1]) != self.resolve_value(expr[2])
            elif op == 'lt':
                return self.resolve_value(expr[1]) < self.resolve_value(expr[2])
            elif op == 'le':
                return self.resolve_value(expr[1]) <= self.resolve_value(expr[2])
            elif op == 'gt':
                return self.resolve_value(expr[1]) > self.resolve_value(expr[2])
            elif op == 'ge':
                return self.resolve_value(expr[1]) >= self.resolve_value(expr[2])
            elif op == 'and':
                return self.resolve_value(expr[1]) and self.resolve_value(expr[2])
            elif op == 'or':
                return self.resolve_value(expr[1]) or self.resolve_value(expr[2])
            elif op == 'not':
                return not self.resolve_value(expr[1])
            elif op == 'list':
                return [self.resolve_value(x) for x in expr[1:]]
            elif op == 'dict':
                result = {}
                for k, v in expr[1:]:
                    result[self.resolve_value(k)] = self.resolve_value(v)
                return result
        
        return expr
    
    def evaluate_condition(self, condition):
        return self.resolve_value(condition)

def run_vm(processes):
    channels = {}
    process_registry = {}
    
    for p in processes:
        for op, args in p.steps:
            if op in ['send', 'receive']:
                ch = args[0]
                if isinstance(ch, str) and ch not in channels:
                    channels[ch] = Channel(ch)
        
        process_registry[p.env.pid] = p
    
    threads = []
    for p in processes:
        thread = threading.Thread(target=p.run, args=(channels, process_registry))
        thread.daemon = True
        threads.append(thread)
        thread.start()
    
    for t in threads:
        t.join()

def example_system():
    P = Process("P", [
        ('send', ('a', 42)),
        ('stop', ())
    ])
    
    Q = Process("Q", [
        ('receive', ('a', 'x')),
        ('log', ('var', 'x')),
        ('stop', ())
    ])
    
    run_vm([P, Q])

def example_advanced_system():
    Server = Process("Server", [
        ('receive', ('reply_ch', 'reply')),  # Receive the reply channel from Coordinator
        ('log', "Server waiting for requests"),
        ('receive', ('request', 'client_msg')),
        ('log', ('var', 'client_msg')),
        ('send', (('var', 'reply'), ('add', ('var', 'client_msg'), 100))),
        ('stop', ())
    ])
    
    Client = Process("Client", [
        ('receive', ('reply_ch', 'server_reply_ch')),
        ('send', ('request', 42)),
        ('receive', (('var', 'server_reply_ch'), 'response')),
        ('log', ('var', 'response')),
        ('stop', ())
    ])
    
    Coordinator = Process("Coordinator", [
        ('new_channel', 'request'),
        ('new_channel', 'reply_ch'),
        ('new_channel', 'reply'),
        ('spawn', ('ServerProcess', [
            ('send', ('reply_ch', ('var', 'reply'))),  # Send reply channel to Server
            ('stop', ())
        ])),
        ('send', ('reply_ch', ('var', 'reply'))),  # Send reply channel to Client
        ('stop', ())
    ])
    
    run_vm([Server, Client, Coordinator])


def example_replication():
    RequestHandler = Process("RequestHandler", [
        ('new_channel', 'requests'),
        ('new_channel', 'response_ch'),
        ('new_channel', 'handler1_req'),
        ('new_channel', 'handler2_req'),
        ('new_channel', 'handler3_req'),
        ('spawn', ("Handler1", [
            ('receive', ('handler1_req', 'req')),
            ('log', ('var', 'req')),
            ('send', ('response_ch', ('add', ('var', 'req'), 1))),
            ('stop', ())
        ])),
        ('spawn', ("Handler2", [
            ('receive', ('handler2_req', 'req')),
            ('log', ('var', 'req')),
            ('send', ('response_ch', ('add', ('var', 'req'), 1))),
            ('stop', ())
        ])),
        ('spawn', ("Handler3", [
            ('receive', ('handler3_req', 'req')),
            ('log', ('var', 'req')),
            ('send', ('response_ch', ('add', ('var', 'req'), 1))),
            ('stop', ())
        ])),
        ('receive', ('requests', 'req1')),
        ('send', ('handler1_req', ('var', 'req1'))),
        ('receive', ('requests', 'req2')),
        ('send', ('handler2_req', ('var', 'req2'))),
        ('receive', ('requests', 'req3')),
        ('send', ('handler3_req', ('var', 'req3'))),
        ('stop', ())
    ])
    
    Client = Process("Client", [
        ('send', ('requests', 1)),
        ('send', ('requests', 2)),
        ('send', ('requests', 3)),
        ('close', 'requests'),
        ('receive', ('response_ch', 'resp1')),
        ('log', ('var', 'resp1')),
        ('receive', ('response_ch', 'resp2')),
        ('log', ('var', 'resp2')),
        ('receive', ('response_ch', 'resp3')),
        ('log', ('var', 'resp3')),
        ('close', 'response_ch'),
        ('stop', ())
    ])
    
    run_vm([RequestHandler, Client])


if __name__ == "__main__":
    print("=== Basic Example ===")
    example_system()
    
    print("\n=== Advanced Example ===")
    example_advanced_system()
    
    print("\n=== Replication Example ===")
    example_replication()
