# call by value (primitives)
def modify_value(x):
    x = 999

def demo_by_value():
    num = 42
    modify_value(num)
    print(f"By Value: {num} (unchanged)")

# call by sharing (objects)
class Object:
    def __init__(self, value):
        self.value = value

def modify_object(obj):
    obj.value = 999  # Changes the original

def reassign_object(obj):
    obj = Object(999)  # Does NOT change the original

def demo_by_sharing():
    obj1 = Object(42)
    modify_object(obj1)
    print(f"By Sharing (modify): {obj1.value} (changed)")
    
    obj2 = Object(42)
    reassign_object(obj2)
    print(f"By Sharing (reassign): {obj2.value} (unchanged)")


demo_by_value()
demo_by_sharing()

# Note: Python has no true "call by reference"
# But you can simulate it with mutable containers:
def modify_via_list(lst):
    lst[0] = 999

def demo_simulated_reference():
    wrapper = [42]
    modify_via_list(wrapper)
    print(f"Simulated Reference: {wrapper[0]} (changed)")

demo_simulated_reference()
