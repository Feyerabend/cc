class Animal:
    def speak(self): return "Generic sound"
class Dog(Animal):
    def speak(self): return "Woof"
class Cat(Animal):
    def speak(self): return "Meow"
animals = [Dog(), Cat()]
for animal in animals:
    print(animal.speak())  # Woof, Meow

# This is an example of polymorphism in Python.
# The `speak` method is defined in the base class
# `Animal` and overridden in the derived classes
# `Dog` and `Cat`.
# When we call `speak` on an instance of `Dog` or `Cat`,
# the appropriate method is called based on the
# actual object type, not the reference type.
# This allows us to write code that can work with
# different types of objects in a uniform way.

