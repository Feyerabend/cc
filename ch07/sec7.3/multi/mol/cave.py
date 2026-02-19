# This is a simple text-based adventure game implemented in Python.
# You can compare this to the same game implemented in a functional style: cave.mol.
# The game consists of a player navigating through rooms, picking up items,
# and using them to achieve victory.

def digit_char(d):
    return "0123456789"[d]

def to_str(n):
    if n == 0:  return "0"
    if n < 0:   return "-" + to_str(-n)
    digits = []
    m = n
    while m:
        digits = [m % 10] + digits
        m //= 10
    result = ""
    for d in digits:
        result += digit_char(d)
    return result

def elem(x, lst):
    for item in lst:
        if item == x:
            return True
    return False

def find_item(name, lst):
    for item in lst:
        if item["name"] == name:
            return item
    return None

def remove_item(name, lst):
    return [item for item in lst if item["name"] != name]

def add_item(item, lst):
    if elem(item["name"], [i["name"] for i in lst]):
        return lst
    return [item] + lst

def foldl(fn, acc, lst):
    for x in lst:
        acc = fn(acc, x)
    return acc

def reverse(lst, acc):
    for item in lst:
        acc = [item] + acc
    return acc

# room

def get_room(dir, connections):
    for c in connections:
        if c["dir"] == dir:
            return c["room"]
    raise Exception("Invalid direction")

class Room:
    def __init__(self, desc, exits):
        self.desc        = desc
        self.exits       = exits
        self.items       = []
        self.events      = None
        self.connections = []

    def describe(self, player):
        desc = self.desc + "\n"
        if self.items:
            items_str = "Items here: " + self.items[0]["name"] + \
                        foldl(lambda a, b: a + ", " + b["name"], "", self.items[1:]) + "\n"
        else:
            items_str = ""
        event_msg = self.events(player) if self.events else ""
        exits_str = "Exits: " + foldl(lambda a, b: a + " " + b, "", self.exits) + "\n"
        player.add_output(desc + items_str + event_msg + exits_str)

    def add_item(self, item):
        self.items = [item] + self.items

    def remove_item(self, item_name):
        self.items = [i for i in self.items if i["name"] != item_name]

# item

def make_item(name, effect):
    def use(self, player):
        player.add_output("Used " + self["name"] + ": " + self["effect"] + "\n")
    return {"name": name, "effect": effect, "use": use}

# player

class Player:
    def __init__(self, start_room):
        self.room      = start_room
        self.health    = 10
        self.inventory = []
        self.output    = []

    def add_output(self, s):
        self.output = [s] + self.output

    def move(self, dir):
        if not elem(dir, self.room.exits):
            self.add_output("Can't go " + dir + "!\n")
            return self.room
        new_room = get_room(dir, self.room.connections)
        self.room = new_room
        return new_room

    def pickup(self, item_name):
        item = find_item(item_name, self.room.items)
        if item is None:
            self.add_output("No such item!\n")
            return
        self.room.remove_item(item_name)
        self.inventory = [item] + self.inventory
        self.add_output("Picked up " + item_name + "\n")

    def use_item(self, item_name):
        item = find_item(item_name, self.inventory)
        if item is None:
            self.add_output("No such item in inventory!\n")
            return
        item["use"](item, self)
        self.inventory = remove_item(item_name, self.inventory)

    def status(self):
        if self.inventory:
            inv_str = self.inventory[0]["name"] + \
                      foldl(lambda a, b: a + ", " + b["name"], "", self.inventory[1:])
        else:
            inv_str = ""
        s = "Health: " + to_str(self.health) + ", Inventory: " + inv_str + "\n"
        self.add_output(s)

# world setup

entrance  = Room("Entrance hall. Dimly lit.",              ["north", "east"])
hallway   = Room("Long hallway. Echoes abound.",           ["south", "west", "north"])
treasure  = Room("Treasure room. Gold shines.",            ["east"])
monster   = Room("Monster's lair. Growls echo.",           ["west"])
exit_room = Room("Exit chamber. Freedom awaits, but locked.", ["south"])

entrance.connections  = [{"dir": "north", "room": hallway},   {"dir": "east",  "room": monster}]
hallway.connections   = [{"dir": "south", "room": entrance},  {"dir": "west",  "room": treasure}, {"dir": "north", "room": exit_room}]
treasure.connections  = [{"dir": "east",  "room": hallway}]
monster.connections   = [{"dir": "west",  "room": entrance}]
exit_room.connections = [{"dir": "south", "room": hallway}]

torch  = make_item("torch",  "lights the darkness -- you feel braver")
key    = make_item("key",    "a heavy iron key -- perhaps it opens something")
potion = make_item("potion", "restores 5 health points -- you feel refreshed")
sword  = make_item("sword",  "a rusty but sharp blade -- ready to fight")
gold   = make_item("gold",   "a glittering coin -- wealth beyond measure")

entrance.add_item(torch)
entrance.add_item(potion)
treasure.add_item(key)
treasure.add_item(gold)
monster.add_item(sword)

monster.events   = lambda player: "A fearsome troll blocks your path and eyes your belongings!\n"
exit_room.events = lambda player: (
    "The key glows -- the lock clicks open. VICTORY IS YOURS!\n"
    if find_item("key", player.inventory) is not None
    else "The door is sealed tight. You need a key..\n"
)

# helpers

player    = Player(entrance)
separator = "-----------------------------------\n"

def print_output(p):
    lines = reverse(p.output, [])
    p.output = []
    for s in lines:
        print(s, end="")

# story

print("\n-- A CAVE ADVENTURE --\n")
print(separator, end="")

print("** You wake in the entrance hall **")
player.room.describe(player)
print_output(player)

print(separator, end="")
print(">> pick up torch")
player.pickup("torch")
print_output(player)

print(">> pick up potion")
player.pickup("potion")
print_output(player)

player.status()
print_output(player)

print(separator, end="")
print(">> go east (to monster's lair)")
player.move("east")
player.room.describe(player)
print_output(player)

print(">> pick up sword")
player.pickup("sword")
print_output(player)

print(">> use torch")
player.use_item("torch")
print_output(player)

print(separator, end="")
print(">> go west (back to entrance)")
player.move("west")
player.room.describe(player)
print_output(player)

print(">> go north (to hallway)")
player.move("north")
player.room.describe(player)
print_output(player)

print(">> go west (to treasure room)")
player.move("west")
player.room.describe(player)
print_output(player)

print(">> pick up key")
player.pickup("key")
print_output(player)

print(">> pick up gold")
player.pickup("gold")
print_output(player)

player.status()
print_output(player)

print(separator, end="")
print(">> go east then north to exit chamber")
player.move("east")
player.move("north")
player.room.describe(player)
print_output(player)

print(">> use potion")
player.use_item("potion")
print_output(player)

print(separator, end="")
print("** FINAL STATUS **")
player.status()
print_output(player)
