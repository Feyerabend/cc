
## Game VM

This is using ncurses i.e. the console. Preliminary testing.


### How it works

Simple opcodes - Each opcode calls a game system:

```
OP_CALL_INPUT - handle player input
OP_CALL_AI - update AI behavior
OP_CALL_MOVE - move an entity
OP_CALL_CLAMP - keep entity on screen
OP_CALL_FLASH - update flash timer
OP_CALL_RENDER - draw everything
OP_HALT - end frame
```

Bytecode program - `build_game_code()` creates a simple program:

```
   INPUT player
   AI entity1, AI entity2, AI entity3
   FLASH entity1, FLASH entity2, FLASH entity3
   MOVE all entities
   CLAMP all entities
   RENDER
   HALT
```

One frame per execution. The VM runs the bytecode once per frame, then halts.
Systems are separate. Easy to add new systems (collision, scoring, etc.).

### Extend

```
Add OP_CALL_COLLISION to check if player hits AI
Add OP_CALL_SCORE to update score
Modify build_game_code() to create different game logic
```

