"""
GOFAI (Good Old-Fashioned AI) Expert System Example
A simple rule-based animal classification system

Key GOFAI Concepts Demonstrated:
1. Rule-based reasoning
2. Knowledge representation using facts and rules
3. Forward chaining inference
4. Symbolic manipulation (no neural networks or statistics)
"""

class Fact:
    """Represents a piece of knowledge in our system"""
    def __init__(self, **kwargs):
        self.attributes = kwargs
    
    def matches(self, pattern):
        """Check if this fact matches a given pattern"""
        for key, value in pattern.items():
            if key not in self.attributes or self.attributes[key] != value:
                return False
        return True
    
    def __str__(self):
        return f"Fact({', '.join(f'{k}={v}' for k, v in self.attributes.items())})"

class Rule:
    """Represents an if-then rule"""
    def __init__(self, name, conditions, action):
        self.name = name
        self.conditions = conditions  # List of patterns to match
        self.action = action          # Function to execute
    
    def can_fire(self, facts):
        """Check if all conditions are met by available facts"""
        for condition in self.conditions:
            if not any(fact.matches(condition) for fact in facts):
                return False
        return True
    
    def fire(self, facts):
        """Execute the rule's action"""
        print(f"Firing rule: {self.name}")
        return self.action(facts)

class ExpertSystem:
    """Simple forward-chaining expert system"""
    def __init__(self):
        self.facts = []
        self.rules = []
    
    def add_fact(self, **kwargs):
        """Add a new fact to the knowledge base if it doesn't already exist"""
        new_fact = Fact(**kwargs)
        # Check for duplicate facts
        if not any(fact.attributes == new_fact.attributes for fact in self.facts):
            self.facts.append(new_fact)
            print(f"Added: {new_fact}")
            return True
        return False
    
    def add_rule(self, name, conditions, action):
        """Add a new rule to the rule base"""
        rule = Rule(name, conditions, action)
        self.rules.append(rule)
        print(f"Added rule: {name}")
    
    def run(self):
        """Run the inference engine (forward chaining)"""
        print("\nStarting inference engine...")
        print("=" * 50)
        
        iteration = 1
        fired_rules = set()  # Track fired rules to prevent re-firing
        
        while True:
            print(f"\n--- Iteration {iteration} ---")
            new_facts_added = False
            
            for rule in self.rules:
                if rule.name not in fired_rules and rule.can_fire(self.facts):
                    new_facts = rule.fire(self.facts)
                    fired_rules.add(rule.name)  # Mark rule as fired
                    if new_facts:
                        for fact_data in new_facts:
                            if self.add_fact(**fact_data):
                                new_facts_added = True
                                # Allow rules to fire again if new facts are added
                                fired_rules.clear()
            
            if not new_facts_added:
                break  # Exit if no new facts were added
            
            iteration += 1
            if iteration > 10:  # Safety check
                print("Maximum iterations reached!")
                break
        
        print("\nInference complete!")
        self.print_conclusions()
    
    def print_conclusions(self):
        """Print all derived conclusions"""
        print("\nFinal Conclusions:")
        print("-" * 30)
        conclusions = [f for f in self.facts if 'conclusion' in f.attributes]
        if conclusions:
            # Print unique conclusions
            unique_conclusions = {f.attributes['conclusion'] for f in conclusions}
            for conclusion in unique_conclusions:
                print(f". {conclusion}")
        else:
            print("-- No specific conclusions derived")

# Define our animal classification rules
def create_animal_expert():
    """Create an expert system for animal classification"""
    system = ExpertSystem()
    
    # Rule 1: If it has feathers, it's a bird
    def feather_rule(facts):
        return [{'type': 'bird', 'conclusion': 'This animal is a bird (has feathers)'}]
    
    system.add_rule(
        "Feather Rule",
        [{'has': 'feathers'}],
        feather_rule
    )
    
    # Rule 2: If it's a bird, it can probably fly
    def flight_rule(facts):
        return [{'ability': 'flight', 'conclusion': 'This animal can probably fly'}]
    
    system.add_rule(
        "Flight Rule", 
        [{'type': 'bird'}],
        flight_rule
    )
    
    # Rule 3: If it has gills and fins, it's a fish
    def fish_rule(facts):
        return [{'type': 'fish', 'conclusion': 'This animal is a fish (has gills and fins)'}]
    
    system.add_rule(
        "Fish Rule",
        [{'has': 'gills'}, {'has': 'fins'}],
        fish_rule
    )
    
    # Rule 4: If it's a fish, it swims
    def swim_rule(facts):
        return [{'ability': 'swimming', 'conclusion': 'This animal swims in water'}]
    
    system.add_rule(
        "Swimming Rule",
        [{'type': 'fish'}],
        swim_rule
    )
    
    # Rule 5: If it has fur and four legs, it's probably a mammal
    def mammal_rule(facts):
        return [{'type': 'mammal', 'conclusion': 'This animal is likely a mammal'}]
    
    system.add_rule(
        "Mammal Rule",
        [{'has': 'fur'}, {'legs': 4}],
        mammal_rule
    )
    
    return system

# Example usage and demonstrations
def demo_bird():
    print("1: Classifying a Robin")
    print("=" * 40)
    
    system = create_animal_expert()
    
    # Add facts about a robin
    system.add_fact(animal='robin', has='feathers')
    system.add_fact(animal='robin', has='beak')
    system.add_fact(animal='robin', legs=2)
    
    system.run()

def demo_fish():
    print("\n\n2: Classifying a Goldfish")
    print("=" * 40)
    
    system = create_animal_expert()
    
    # Add facts about a goldfish
    system.add_fact(animal='goldfish', has='gills')
    system.add_fact(animal='goldfish', has='fins')
    system.add_fact(animal='goldfish', has='scales')
    
    system.run()

def demo_mammal():
    print("\n\n3: Classifying a Dog")
    print("=" * 40)
    
    system = create_animal_expert()
    
    # Add facts about a dog
    system.add_fact(animal='dog', has='fur')
    system.add_fact(animal='dog', legs=4)
    system.add_fact(animal='dog', has='tail')
    
    system.run()

def interactive_demo():
    """Let students input their own animal characteristics"""
    print("\n\nDEMO: Classify Your Own Animal!")
    print("=" * 50)
    
    system = create_animal_expert()
    
    animal_name = input("What animal are you thinking of? ")
    
    print(f"\nTell me about the {animal_name}:")
    print("Type characteristics one by one (press Enter with empty line to finish)")
    print("Examples: 'has feathers', 'has fur', 'has gills', 'has fins', 'legs 4'")
    
    while True:
        characteristic = input("Characteristic: ").strip()
        if not characteristic:
            break
        
        if characteristic.startswith('has '):
            feature = characteristic[4:]  # Remove 'has '
            system.add_fact(animal=animal_name, has=feature)
        elif characteristic.startswith('legs '):
            num_legs = int(characteristic[5:])  # Remove 'legs '
            system.add_fact(animal=animal_name, legs=num_legs)
        else:
            print("Format not recognized. Use 'has [feature]' or 'legs [number]'")
    
    system.run()

if __name__ == "__main__":
    print("GOFAI Expert System Demonstration")
    print("=" * 50)
    print("This demonstrates classical AI techniques:")
    print("- Symbolic reasoning (no neural networks)")
    print("- Rule-based inference")
    print("- Forward chaining")
    print("- Knowledge representation with facts and rules")
    
    # Run demonstrations
    demo_bird()
    demo_fish() 
    demo_mammal()
    
    # Interactive session
    print("\n" + "="*60)
    try_interactive = input("\nWould you like to try the interactive demo? (y/n): ")
    if try_interactive.lower().startswith('y'):
        interactive_demo()
    
    print("\nGOFAI Takeaways:")
    print("- Knowledge is explicitly represented as facts and rules")
    print("- Reasoning follows logical, traceable steps")
    print("- No learning from data--all knowledge is programmed")
    print("- Transparent decision-making process")
    print("- Works well for domains with clear, logical rules")


