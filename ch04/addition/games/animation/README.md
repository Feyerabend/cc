
## Display Pico Animation Engine – Architecture and Design Plan

__Project:__ This doc describes the architecture and design of a small, distributed
graphics and animation system based on two Raspberry Pi Pico boards.
The system is intentionally split into two clearly defined roles.

One *Raspberry Pi Pico 2* is dedicated to driving a display, for example the
Pimoroni DisplayPack 2.0. This Pico is responsible for all real-time,
time-critical tasks such as rendering graphics, running the animation engine,
updating object positions, and detecting collisions. It acts as a deterministic
simulation and rendering node.

The second board is a *Raspberry Pi Pico 2W*. This Pico provides connectivity
to the outside world and serves as the high-level controller. It can communicate
with other Picos, computers, or network services, and is responsible for
decision-making, orchestration, and external control of the system.

The two Picos are connected by a direct wired link using UART. Over this link,
the Pico 2W sends commands that modify the state of the animation world, while
the display Pico sends back events such as collisions, boundary violations,
or other simulation results. Timing, animation, and rendering are never driven
by UART traffic; UART is used strictly for exchanging state changes and events.

This separation of responsibilities creates a clean and robust architecture:
- The display Pico behaves like a small, self-contained game or animation engine.
- The Pico 2W behaves like a controller and communication hub.

By keeping real-time animation and rendering independent from external communication,
the system remains smooth, deterministic, and easy to extend.

* Target: Raspberry Pi Pico 2
* Role: Deterministic rendering + animation + collision node
* Communication: UART0 with Pico 2W

The Pico 2W acts as:
- High-level controller
- Network interface
- Game logic / orchestration
- External commands source

The display Pico acts as:
- Real-time simulation engine
- Animation engine
- Collision engine
- Renderer
- Event emitter

No timing or animation logic is ever driven by UART. UART only modifies state.


### 1. High-Level Data Flow

* UART RX –> Command Parser –> World State
* World State –> Animation Tick –> Collision System –> Event Queue –> UART TX
* World State –> Renderer –> Display

Everything revolves around the *World State*.



### 2. Core Subsystems

```
/drivers
	display.c
	uart.c
	timer.c

/engine
	world.c
	entity.c
	animation.c
	collision.c
	behavior.c
	events.c

/protocol
	parser.c
	serializer.c
```


### 3. World Model

The world is a list of entities.

```c
#define MAX_ENTITIES 32

typedef struct {
    int id;
    int x, y;
    int vx, vy;
    int width, height;
    uint8_t behavior;
    bool active;
} Entity;

typedef struct {
    Entity entities[MAX_ENTITIES];
    uint32_t tick;
} World;
```


### 4. Animation Engine

Runs at fixed frequency (e.g. 60 Hz).
```c
void animation_tick(World *w) {
    w->tick++;

    apply_behaviors(w);
    move_entities(w);
    detect_collisions(w);
}

Movement:

void move_entities(World *w) {
    for (int i = 0; i < MAX_ENTITIES; i++) {
        Entity *e = &w->entities[i];
        if (!e->active) continue;
        e->x += e->vx;
        e->y += e->vy;
    }
}
```



### 5. Behaviour System

Behaviour is a bitmask.
```c
#define BEHAVIOR_MOVE     0x01
#define BEHAVIOR_BOUNCE   0x02
#define BEHAVIOR_WRAP     0x04
#define BEHAVIOR_EXPIRE   0x08

void apply_behaviors(World *w) {
    for (each entity e) {
        if (e->behavior & BEHAVIOR_BOUNCE) bounce(e);
        if (e->behavior & BEHAVIOR_WRAP) wrap(e);
    }
}
```



### 6. Collision Engine

Simple AABB collision.
```c
bool collide(Entity *a, Entity *b) {
    return !(a->x + a->width  < b->x ||
             a->x > b->x + b->width ||
             a->y + a->height < b->y ||
             a->y > b->y + b->height);
}
```
On collision:
```c
EVENT COLLISION <id1> <id2>
```
Sent via UART.



### 7. Rendering

Renderer draws current world state:
```c
void render(World *w) {
    clear_screen();
    for (each entity e)
        draw_sprite(e);
    swap_buffers();
}
```
Renderer never modifies world state.



### 8. UART Protocol

Command Format (ASCII for simplicity):
```
CMD <COMMAND> <ARGS>\n
```
Examples:
```
CMD CREATE 3 10 20 16 16
CMD SET_VEL 3 2 -1
CMD SET_BEHAVIOR 3 BOUNCE
CMD STOP 3
CMD DELETE 3
```
Which map to:
```
CREATE -> create_entity(id, x, y, w, h)
SET_VEL -> entities[id].vx = vx; entities[id].vy = vy;
```
Event Format:
```
EVENT <TYPE> <ARGS>\n
```
Examples:
```
EVENT COLLISION 3 7
EVENT OUT_OF_BOUNDS 4
```



### 9. Event Queue

Events generated during tick are buffered and flushed after the tick.
```c
typedef struct {
    char text[64];
} Event;

Event event_queue[16];
```



### 10. Main Loop
```c
while (1) {
    uart_poll();
    if (timer_tick_elapsed()) {
        animation_tick(&world);
        render(&world);
        flush_events();
    }
}
```
UART never blocks animation.



### 11. Expansion Paths

Once this exists, adding features is trivial:
- Sprite animation frames:
```c
frame = (tick / 4) % frame_count;
```
- Z-order:
```c
int z;
sort before render;
```
- Physics:
```
gravity
acceleration
mass
```
- Scripts:
```
CMD RUN_SCRIPT intro.anim
```



### 12. Mental Model

The display Pico is a tiny deterministic game engine.

The Pico 2W is:
- Director
- Network bridge
- AI / logic

The Pico 2 is:
- Renderer
- Animator
- Physics simulator

They communicate only through:
```
Commands in
Events out
```
This separation is what will make your system stable, debuggable, and extensible.
