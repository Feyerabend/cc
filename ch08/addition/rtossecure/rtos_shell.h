#ifndef RTOS_SHELL_H
#define RTOS_SHELL_H

#include <stdbool.h>

/*
 * rtos_shell.h - Minimal line-oriented command shell over USB CDC.
 *
 * Architecture:
 *   shell_tick() reads one character at a time from stdin (non-blocking),
 *   echoes it to the terminal, accumulates input into a line buffer, and
 *   dispatches the line to a matching registered command handler on '\n'.
 *
 *   It is designed to run from a low-priority RTOS task:
 *
 *     void shell_task(void *p) {
 *         (void)p;
 *         task_delay(1500);                   // wait for USB CDC to connect
 *         printf("\r\n> ");
 *         while (1) { shell_tick(); task_delay(10); }
 *     }
 *
 * Built-in commands (registered by shell_init):
 *   help   - list all registered commands with their descriptions
 *   tasks  - print task name, priority, and current state
 *   stats  - print CPU%, stack high-watermark, and switch count per task
 *   uptime - print milliseconds elapsed since boot
 */

#define SHELL_LINE_MAX  80    /* maximum input line length in characters */
#define SHELL_ARGC_MAX   8    /* maximum number of tokens per line       */
#define SHELL_CMD_MAX   16    /* maximum number of registered commands   */

/* Callback invoked when a matching command line is received */
typedef void (*shell_cmd_fn)(int argc, char **argv);

typedef struct {
    const char   *name; /* command keyword (matched against argv[0]) */
    const char   *help; /* one-line description shown by 'help'      */
    shell_cmd_fn  fn;   /* handler invoked on match                  */
} shell_cmd_t;

/*
 * Initialise the shell and register the built-in commands.
 * Call once before rtos_start().
 */
void shell_init(void);

/*
 * Register a user command.
 * Returns false if SHELL_CMD_MAX registered commands are already stored.
 */
bool shell_register(const char *name, const char *help, shell_cmd_fn fn);

/*
 * Process up to one input character per call.
 * Call from a task loop - blocking is not required (uses getchar_timeout_us(0)).
 */
void shell_tick(void);

#endif /* RTOS_SHELL_H */
