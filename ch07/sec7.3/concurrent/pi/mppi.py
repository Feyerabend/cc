import multiprocessing as mp
import time
import uuid
import random
import os
from typing import Dict, List, Tuple, Any, Callable, Optional, Set, Union
from multiprocessing import Process as MPProcess

class Value:
    def __init__(self, value: Any):
        self.value = value
    
    def __repr__(self):
        return f"{self.value}"

class Channel:
    def __init__(self, name: str, manager):
        self.name = name
        self.q = manager.Queue()
        self.closed = manager.Value('b', False)
        self.lock = manager.Lock()
    
    def send(self, value: Any) -> bool:
        with self.lock:
            if self.closed.value:
                return False
            self.q.put(value)
            return True
    
    def receive(self) -> Tuple[Any, bool]:
        with self.lock:
            if self.closed.value and self.q.empty():
                return None, False
        return self.q.get(), True
    
    def close(self) -> None:
        with self.lock:
            self.closed.value = True
    
    def __repr__(self):
        return f"Channel({self.name})"

class ProcessEnvironment:
    def __init__(self, manager):
        self.variables = manager.dict()
        self.pid = str(uuid.uuid4())[:8]
    
    def set(self, name: str, value: Any) -> None:
        self.variables[name] = value
    
    def get(self, name: str) -> Any:
        if name in self.variables:
            return self.variables[name]
        return name
    
    def copy(self, manager):
        new_env = ProcessEnvironment(manager)
        for k, v in self.variables.items():
            new_env.variables[k] = v
        return new_env

class Process:
    def __init__(self, name: str, steps: List[Tuple], env: ProcessEnvironment, print_lock):
        self.name = name
        self.steps = steps
        self.env = env
        self.terminated = mp.Manager().Value('b', False)
        self.waiting = mp.Manager().Value('b', False)
        self.waiting_on = None
        self.print_lock = print_lock
    
    def safe_print(self, message):
        with self.print_lock:
            print(message)
    
    def run(self, channels_proxy, registry_proxy):
        step_index = 0
        
        while step_index < len(self.steps) and not self.terminated.value:
            op, args = self.steps[step_index]
            self.safe_print(f"{self.name}[{self.env.pid}] ({os.getpid()}) executing step {step_index}: {op} {args}")
            
            if op == 'send':
                ch_name, val_expr = args
                ch_resolved = self.resolve_value(ch_name)
                val_resolved = self.resolve_value(val_expr)
                
                if ch_resolved in channels_proxy:
                    if channels_proxy[ch_resolved].send(val_resolved):
                        self.safe_print(f"{self.name}[{self.env.pid}] ({os.getpid()}) sends {val_resolved} on {ch_resolved}")
                    else:
                        self.safe_print(f"{self.name}[{self.env.pid}] ({os.getpid()}) failed to send on closed channel {ch_resolved}")
                else:
                    self.safe_print(f"{self.name}[{self.env.pid}] ({os.getpid()}) error: channel {ch_resolved} not found")
                    
                step_index += 1
                
            elif op == 'receive':
                ch_name, var = args
                ch_resolved = self.resolve_value(ch_name)
                
                if ch_resolved in channels_proxy:
                    val, success = channels_proxy[ch_resolved].receive()
                    if success:
                        self.env.set(var, val)
                        self.safe_print(f"{self.name}[{self.env.pid}] ({os.getpid()}) receives {val} from {ch_resolved} as {var}")
                    else:
                        self.safe_print(f"{self.name}[{self.env.pid}] ({os.getpid()}) failed to receive from closed channel {ch_resolved}")
                else:
                    self.safe_print(f"{self.name}[{self.env.pid}] ({os.getpid()}) error: channel {ch_resolved} not found")
                    
                step_index += 1
                
            elif op == 'new_channel':
                ch_name = args
                ch_id = f"{ch_name}_{uuid.uuid4().hex[:6]}"
                channels_proxy[ch_id] = Channel(ch_id, mp.Manager())
                self.env.set(ch_name, ch_id)
                self.safe_print(f"{self.name}[{self.env.pid}] ({os.getpid()}) creates new channel {ch_id}")
                step_index += 1
                
            elif op == 'close':
                ch_name = args
                ch_resolved = self.resolve_value(ch_name)
                
                if ch_resolved in channels_proxy:
                    channels_proxy[ch_resolved].close()
                    self.safe_print(f"{self.name}[{self.env.pid}] ({os.getpid()}) closes channel {ch_resolved}")
                else:
                    self.safe_print(f"{self.name}[{self.env.pid}] ({os.getpid()}) error: cannot close non-existent channel {ch_resolved}")
                    
                step_index += 1
                
            elif op == 'spawn':
                proc_name, proc_steps = args
                new_env = self.env.copy(mp.Manager())
                new_proc = Process(proc_name, proc_steps, new_env, self.print_lock)
                registry_proxy[new_proc.env.pid] = True
                
                process = MPProcess(target=new_proc.run, args=(channels_proxy, registry_proxy))
                process.daemon = True
                process.start()
                
                self.safe_print(f"{self.name}[{self.env.pid}] ({os.getpid()}) spawns {proc_name}[{new_proc.env.pid}]")
                step_index += 1
                
            elif op == 'stop':
                self.safe_print(f"{self.name}[{self.env.pid}] ({os.getpid()}) halts.")
                self.terminated.value = True
                if self.env.pid in registry_proxy:
                    del registry_proxy[self.env.pid]
                break  # Explicitly break to ensure loop exits
                
            elif op == 'log':
                message = self.resolve_value(args)
                self.safe_print(f"{self.name}[{self.env.pid}] ({os.getpid()}) log: {message}")
                step_index += 1
                
            time.sleep(0.5)
        
        self.safe_print(f"{self.name}[{self.env.pid}] ({os.getpid()}) exiting run loop")
    
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
    mp.set_start_method('spawn', force=True)
    manager = mp.Manager()
    channels_proxy = manager.dict()
    registry_proxy = manager.dict()
    print_lock = manager.Lock()
    
    for p in processes:
        for op, args in p.steps:
            if op in ['send', 'receive']:
                ch = args[0]
                if isinstance(ch, str) and ch not in channels_proxy:
                    channels_proxy[ch] = Channel(ch, manager)
        
        registry_proxy[p.env.pid] = True
    
    processes_mp = []
    for p in processes:
        process = MPProcess(target=p.run, args=(channels_proxy, registry_proxy))
        process.daemon = True
        processes_mp.append(process)
        process.start()
    
    # Wait for all processes to complete with a timeout
    for p in processes_mp:
        p.join(timeout=5.0)  # Add timeout to prevent infinite hang
        if p.is_alive():
            print(f"Process {p.pid} did not terminate, forcing termination")
            p.terminate()
    
    # Clean up manager
    manager.shutdown()

def example_system():
    manager = mp.Manager()
    print_lock = manager.Lock()
    
    P = Process("P", [
        ('send', ('a', 42)),
        ('stop', ())
    ], ProcessEnvironment(manager), print_lock)
    
    Q = Process("Q", [
        ('receive', ('a', 'x')),
        ('log', ('var', 'x')),
        ('stop', ())
    ], ProcessEnvironment(manager), print_lock)
    
    run_vm([P, Q])

if __name__ == "__main__":
    print("=== Basic Example ===")
    example_system()