
## Simple Game Arcitecture

This is a very *simplified entity-manager pattern*,
not a true Entity-Component-System.
But what is the difference in more detail? *Entity-Component-System (ECS)*
is a data-oriented architectural pattern that strictly separates:

1. *Entities* - Just unique IDs (often just integers like `entity_id = 42`)
   - No data, no methods, no logic
   - Simply a label to group components together

2. *Components* - Pure data structures (no behaviour)
```
   PositionComponent: { x: 100, y: 50 }
   VelocityComponent: { vx: 5, vy: -2 }
   SpriteComponent: { texture: "player.png", scale: 2 }
   HealthComponent: { current: 80, max: 100 }
```
   - Each entity can have any combination of components
   - Components are stored in efficient arrays grouped by type

3. *Systems* - Pure logic (no data storage)
```
   MovementSystem: operates on entities with Position + Velocity
   RenderSystem: operates on entities with Position + Sprite
   CollisionSystem: operates on entities with Position + Collider
```
   - Systems query for entities that have required components
   - Process matching entities each frame


*Example ECS Flow:*
```
Create entity 123:
  - Add PositionComponent(100, 50)
  - Add VelocityComponent(5, 0)
  - Add SpriteComponent("player.png")

Each frame:
  MovementSystem queries: "all entities with Position + Velocity"
    → Finds entity 123
    → Updates: position.x += velocity.vx * dt
  
  RenderSystem queries: "all entities with Position + Sprite"
    → Finds entity 123
    → Draws sprite at position
```

#### This Simplified Approach vs. True ECS

Here:
- Entities are *classes with inheritance* (Player extends Entity)
- *Data + Logic bundled together* (Player.update() has input handling)
- Entities know how to update/render themselves
- Manager just iterates and calls entity.update()
- Simpler mental model, more intuitive for beginners
- Harder to reuse behavior (inheritance hierarchies get messy)
- Less cache-friendly (objects scattered in memory)
- Difficult to add/remove capabilities at runtime

*True ECS (Data-Oriented Composition):*
- Entities are *just IDs* (no inheritance, no classes)
- *Data separate from logic* (components vs. systems)
- Composition over inheritance (add/remove components freely)
- Extreme performance (cache-friendly contiguous arrays)
- Easy to serialize (components are just data)
- More complex to understand initially
- More boilerplate code
- Harder to debug (data scattered across component arrays)


*Real-World Comparison:*

*Object-Oriented:*
```python
class FlyingEnemy(Enemy):
    def update(self):
        self.fly()
        super().update()

class ShootingEnemy(Enemy):
    def update(self):
        self.shoot()
        super().update()

# Want a flying, shooting enemy? Need FlyingShootingEnemy class!
```

*ECS:*
```python
flying_shooting_enemy = create_entity()
add_component(flying_shooting_enemy, FlightComponent())
add_component(flying_shooting_enemy, WeaponComponent())

# Systems automatically handle any entity with those components
# FlySystem processes anything with FlightComponent
# WeaponSystem processes anything with WeaponComponent
```


#### When to Use Each

*Use This Simplified Approach When:*
- Learning game programming
- Prototyping or game jams
- Small games (< 500 entities)
- Clear entity hierarchies (Player, Enemy, Bullet)
- Development speed > performance

*Upgrade to Full ECS When:*
- 1000+ active entities (crowds, particle systems)
- Need to add/remove capabilities at runtime
- Performance critical (data cache optimization matters)
- Complex entity variations (100+ enemy types)
- Multiplayer (easy serialization of component data)
- Large team (systems can be developed independently)

*Famous ECS Engines:*
Unity DOTS, Bevy (Rust), Amethyst, EnTT (C++), ecs-lib (many languages)


#### The Conceptual Difference

- *OOP thinking:** "What *is* this thing?" → Create class hierarchy
- *ECS thinking:* "What can this thing *do*?" → Add capability components

ECS embraces *composition over inheritance*, making it easier
to create diverse entities from reusable parts, at the cost
of initial complexity.


### CRC cards

*CRC* = *Class-Responsibility-Collaborator*

A simple, low-tech design technique using index cards (or text) to design
object-oriented systems. Created in the late 1980s for teaching OOP concepts.

*Each card contains:*
- *Class name* (top)
- *Responsibilities* (left) - What this class does/knows
- *Collaborators* (right) - Which other classes it works with


#### Example CRC Card

```
┌─────────────────────────────────────┐
│ PLAYER                              │
├──────────────────────┬──────────────┤
│ Responsibilities:    │ Collaborates:│
│ - Store position     │ - Entity     │
│ - Process input      │ - Input      │
│ - Move character     │ - Renderer   │
│ - Render sprite      │              │
└──────────────────────┴──────────────┘
```

#### Why Use CRC Cards?

- Forces you to think about single responsibilities
- Makes collaboration/dependencies visible
- Easy to reorganize (just move cards around)
- Great for team design sessions
- No tools needed - just cards and markers

*When to use:*
- Early design phase (before coding)
- Explaining architecture to others
- Refactoring complex systems
- Teaching OOP concepts


#### The CRC Process

1. *Brainstorm classes* - What objects exist in your system?
2. *Identify responsibilities* - What should each class do? (Keep it focused!)
3. *Find collaborators* - Which classes need to talk to each other?
4. *Role-play scenarios* - Walk through use cases, passing cards between team members
5. *Refine* - Too many responsibilities? Split the class. Too many collaborators? Simplify.


#### CRC Guidelines

*Good Responsibilities:*
- Action-oriented verbs: "Calculate", "Store", "Render", "Update"
- Keep it to 3-5 responsibilities per class
- If you can't fit on a card, class is too complex

*Bad Responsibilities:*
- Vague: "Handle stuff", "Manage things"
- Too many: 10+ responsibilities = needs splitting
- Too detailed: Implementation details don't go on cards

*Collaborator Tips:*
- 0-2 collaborators = well-encapsulated
- 5+ collaborators = probably doing too much
- Circular dependencies = design smell


#### CRC here

The cards at the top use a simplified CRC format:
```
║ CLASS NAME
║ Responsibilities:
║  - Bullet points of what it does
║ Collaborates: Class1, Class2, Class3
```

This shows the architecture at a glance before diving into implementation.
(See below in more detail.)


#### Beyond CRC: What's Next?

CRC cards are *design tools*, not implementation guides. After CRC
when constructing larger programs than this game:
1. *Class diagrams* (UML) - Add methods, attributes, relationships
2. *Sequence diagrams* - Show how objects interact over time
3. *Code* - Implement the design

Think of CRC as the napkin sketch before the blueprint.


#### Core CRC here

```
║ ENTITY MANAGER
║ Responsibilities:
║  - Lifecycle: create, destroy, store all entities
║  - Update all entities each frame
║  - Query/lookup entities by type or ID
║ Collaborates: Entity, Player, Sprite, Enemy


║ ENTITY (Base)
║ Responsibilities:
║  - ID, position, velocity, active state
║  - update(dt): apply velocity → position (movement physics)
║  - render(): interface for drawing
║ Collaborates: EntityManager, subclasses (Player/Sprite)


║ PLAYER / SPRITE / ENEMY : Entity
║ Player:
║  - Process input → set velocity → call super.update()
║  - Render player sprite/shape
║  - Collaborates: InputHandler
║ Sprite (static):
║  - No movement (velocity = 0)
║  - Just renders visual
║ Enemy (AI):
║  - AI logic → set velocity → call super.update()
║  - Bounce/patrol behavior
```

### Support Systems (2 Cards)

```
║ INPUT HANDLER
║ - Poll keyboard/mouse, store key states
║ - Provide input queries to Player
║ Collaborates: Player, GameLoop


║ RENDERER
║ - Clear screen, draw all entities, present frame
║ - Query EntityManager for drawable entities
║ Collaborates: EntityManager, Entity
```



#### Movement Location: *Entity Base Class*

```
Entity stores:     position, velocity
Entity.update():   position += velocity * dt

Subclasses set:    velocity (based on input/AI)
Subclasses call:   super.update() to apply movement
```

#### Flow
```
GameLoop
   |
   ├─- InputHandler ──-- Player.update()
   │                       |
   ├─- EntityManager ──- [Entity.update() for all]
   │                       |
   └─- Renderer ──────-- [Entity.render() for all]
```

#### Memory Management

- *EntityManager* owns all entities
- Array/vector storage for cache efficiency
- `createEntity()` / `destroyEntity()` for lifecycle
- Optional: object pooling for reuse



### Implementation Pattern (Pseudocode)

```pseudocode
class Entity:
    position, velocity, id, active
    update(dt):
        position += velocity * dt

class Player extends Entity:
    update(dt, input):
        if input.left: velocity.x = -speed
        super.update(dt)

class EntityManager:
    entities = []
    
    createEntity(type, args):
        entity = new type(args)
        entities.add(entity)
        return entity
    
    update(dt, input):
        for entity in entities:
            entity.update(dt, input)

class Game:
    entityManager = new EntityManager()
    inputHandler = new InputHandler()
    renderer = new Renderer()
    
    loop():
        input = inputHandler.poll()
        entityManager.update(dt, input)
        renderer.render(entityManager)
```


### Entity-Component System Explained

game architecture pattern:
- *Entity*: Game objects (players, enemies, bullets)
- *EntityManager*: Container that handles all entities
- *Game*: Main loop that coordinates everything


```
Game Loop:
1. Get input (keyboard/mouse)
2. Update all entities (move, check collisions)
3. Render everything to screen
```

*Entity* = Data + Behavior
- Stores position, velocity, ID
- Updates itself each frame

*Player* = Special Entity
- Responds to input (arrow keys, etc.)
- Calls parent Entity's update for movement

*EntityManager* = Collection Manager
- Factory: Creates new entities
- Updates all entities each frame
- Central registry



__Good:__
- Games with many similar objects
- When you need centralized entity management
- Simple to medium complexity games

__Not ideal:__
- Very large-scale games (needs optimisation)
- Projects requiring maximum flexibility


### Project Ideas for Extension

#### 1. Add More Entity Types
```javascript
class Enemy extends Entity:
    update(dt):
        // AI logic here
        position.x += sin(time) * speed
        super.update(dt)

class Bullet extends Entity:
    lifespan = 3.0
    update(dt):
        lifespan -= dt
        if lifespan <= 0:
            active = false
        super.update(dt)
```

#### 2. Add Components (Composition over Inheritance)
```javascript
class Entity:
    components = []
    addComponent(component)
    update(dt):
        for component in components:
            component.update(dt)

// Now mix and match:
player.addComponent(new InputComponent())
player.addComponent(new PhysicsComponent())
player.addComponent(new SpriteComponent())
```

#### 3. Add Systems
```javascript
class CollisionSystem:
    checkCollisions(entities)

class RenderSystem:
    render(entities)

// In Game loop:
collisionSystem.check(entityManager.entities)
renderSystem.render(entityManager.entities)
```

#### 4. Object Pooling (Performance)
```javascript
class EntityManager:
    pool = []
    
    getEntity(type):
        entity = pool.findInactive()
        if entity:
            entity.active = true
            return entity
        return createEntity(type)
    
    releaseEntity(entity):
        entity.active = false
        // Reuse later
```

#### 5. Event System
```javascript
class EventBus:
    listeners = {}
    
    emit(event, data)
    on(event, callback)

// Usage:
eventBus.on("collision", handleCollision)
eventBus.emit("collision", {entity1, entity2})
```


### Project Plan 1: Implement the Basic Simplified Entity-Manager Game

This project focuses on building a minimal viable game using the simplified
entity-manager pattern described in the text. It's ideal for beginners learning
game programming, as it emphasises a simple OOP approach with inheritance.
The goal is to create a basic 2D game loop where a player can move around,
with static sprites (like background elements) and perhaps one enemy type.


#### Objectives
- Understand and implement the core classes: Entity (base), Player, Sprite,
  Enemy, EntityManager, InputHandler, Renderer, and Game.
- Demonstrate the game loop: Input → Update → Render.
- Keep it simple: <500 lines of code, no advanced features.

#### Steps
1. *Setup Environment*:
   - Choose a framework: MicroPython for easy input and rendering, and
     HTML5 Canvas (JavaScript) for web-based prototyping, if necessary.

2. *Implement Core Classes (Based on Pseudocode and CRC Cards)*:
   - *Entity (Base)*: Include position, velocity, ID, active state.
     Implement `update(dt)` for basic movement (position += velocity * dt).
   - *Player (extends Entity)*: Add input handling to set velocity (e.g.,
     arrow keys for movement). Call super.update(dt).
   - *Sprite (extends Entity)*: Static visual entity with velocity=0.
     Implement `render()` to draw an image or shape.
   - *Enemy (extends Entity)*: Basic AI to set velocity (e.g., patrol
     left/right). Call super.update(dt).
   - *EntityManager*: Store entities in a list. Methods: createEntity(type, args),
     destroyEntity(id), update(dt, input) to loop over entities.
   - *InputHandler*: Poll for key states (e.g., up/down/left/right).
   - *Renderer*: Clear screen, call entity.render() for all active entities,
     present frame.
   - *Game*: Initialize manager, input, renderer. Run loop() with a fixed
     timestep (e.g., 60 FPS).

3. *Build the Game Loop*:
   - In Game.loop(): Poll input -> EntityManager.update(dt, input) ->
     Renderer.render(entityManager).
   - Add a main scene: Create a player, a few sprites (e.g., walls), and one enemy.

4. *Testing and Features*:
   - Test movement: Player responds to keys, enemy patrols.
   - Add basic collision: In Entity.update(), check if position overlaps with
     other entities (simple bounding box).
   - Run the game: Player moves around a screen with static elements and
     a moving enemy.

5. *Timeline and Milestones*:
   - Day 1: Setup and implement Entity base + subclasses.
   - Day 2: EntityManager and Game loop.
   - Day 3: InputHandler, Renderer, basic testing.
   - Total: 3-5 days for a beginner.

6. *Extensions (If Time Allows)*:
   - Add health to entities (inspired by HealthComponent example).
   - Make it a simple "dodge the enemy" game.



### Project Plan 2: Extend to a Component-Based System (Hybrid Approach)

Building on the simplified pattern, this project transitions toward a more
flexible composition model by adding components, as suggested in the "Project Ideas for Extension"
section above. This bridges the gap between the OOP entity-manager and a full
ECS, allowing runtime addition/removal of behaviors without deep inheritance hierarchies.

#### Objectives
- Refactor the basic system to use components for modularity.
- Demonstrate composition: Mix and match behaviours like input, physics, 
  and rendering on any entity.
- Suitable for intermediate developers prototyping varied entity types.

#### Steps
1. *Start from Basic Implementation*:
   - Use Project Plan 1 as a base, or implement it first if needed.

2. *Add Components (Inspired by Extension Idea #2)*:
   - Create a Component base class with update(dt) and render() methods.
   - Examples:
     - InputComponent: Handles key presses to set velocity.
     - PhysicsComponent: Applies velocity to position.
     - SpriteComponent: Draws the entity.
     - AIComponent: Sets velocity based on patrol logic.
   - Modify Entity: Add a list of components. In Entity.update(dt):
     Loop over components and call their update(dt). Same for render().

3. *Refactor Subclasses*:
   - Remove inheritance for Player/Enemy/Sprite. Instead, create plain
     Entities and add components dynamically.
     - Player: addComponent(new InputComponent()),
       addComponent(new PhysicsComponent()), addComponent(new SpriteComponent("player.png")).
     - Enemy: addComponent(new AIComponent()), addComponent(new PhysicsComponent()).
     - Sprite: addComponent(new SpriteComponent("static.png")) (no physics).

4. *Update EntityManager and Game Loop*:
   - EntityManager.createEntity() now returns a plain Entity; user adds components manually.
   - In update(dt, input): Pass input to entities; entities delegate to components
     (e.g., InputComponent uses the input).

5. *Add Features*:
   - Runtime changes: e.g., Add a WeaponComponent to player mid-game for shooting.
   - Basic event system (from Extension Idea #5): Simple EventBus for "collision" events.

6. *Testing and Features*:
   - Test: Create a flying-shooting enemy by adding FlightComponent + WeaponComponent
     (as in the ECS example).
   - Game idea: A shooter where entities gain/lose abilities (e.g., power-ups add components).

7. *Timeline and Milestones*:
   - Day 1-2: Refactor Entity to support components.
   - Day 3: Implement 3-4 component types and refactor subclasses.
   - Day 4: Enhance game loop and test dynamic additions.
   - Total: 4-7 days.


![Game](./../../../../assets/image/projects/pygame.png)
