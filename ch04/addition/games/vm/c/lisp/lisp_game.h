#ifndef LISP_GAME_H
#define LISP_GAME_H

#include "lisp_vm.h"

// Registers the graphics, sprite and button built-ins.
// The display must be initialised with a framebuffer before the game runs.
void lisp_game_init(lisp_vm_t *vm);

// Runs one frame: reads the buttons, calls the button and update
// callbacks, and sends the framebuffer to the display.
// Returns false if a callback raised an error (see lisp_error).
bool lisp_game_frame(lisp_vm_t *vm);

#endif // LISP_GAME_H
