#include "rtos_shell.h"
#include "rtos.h"
#include "pico/stdlib.h"
#include <stdio.h>
#include <string.h>
#include <ctype.h>

/*
 * rtos_shell.c - USB CDC command shell implementation.
 *
 * Input handling:
 *   getchar_timeout_us(0) returns immediately.  If no character is
 *   available it returns PICO_ERROR_TIMEOUT (-1).  This keeps shell_tick()
 *   non-blocking so the calling task can call task_delay(10) between ticks.
 *
 * Output:
 *   All output uses printf / putchar, which route to USB CDC via the
 *   Pico SDK's stdio_usb backend.  If no terminal is connected the calls
 *   return immediately without blocking.
 */

/* ------------------------------------------------------------------ */
/*  Internal state                                                    */
/* ------------------------------------------------------------------ */

static shell_cmd_t cmds[SHELL_CMD_MAX];
static int         num_cmds = 0;
static char        line_buf[SHELL_LINE_MAX];
static int         line_len = 0;

/* ------------------------------------------------------------------ */
/*  Built-in command handlers                                         */
/* ------------------------------------------------------------------ */

static const char * const STATE_NAME[] = {
    "READY", "RUNNING", "BLOCKED", "SUSPEND"
};

/* help - list all registered commands */
static void cmd_help(int argc, char **argv)
{
    (void)argc; (void)argv;
    printf("\r\nAvailable commands:\r\n");
    for (int i = 0; i < num_cmds; i++) {
        printf("  %-12s %s\r\n", cmds[i].name, cmds[i].help);
    }
}

/* tasks - show task name, priority, and current state */
static void cmd_tasks(int argc, char **argv)
{
    (void)argc; (void)argv;
    printf("\r\n  ID  %-10s  PRIO  STATE\r\n", "NAME");
    printf("  --  ----------  ----  -------\r\n");
    for (int i = 0; i < MAX_TASKS; i++) {
        if (tasks[i].name == NULL) break;
        printf("  %2d  %-10s  %4u  %s\r\n",
               i,
               tasks[i].name,
               (unsigned)tasks[i].priority,
               STATE_NAME[tasks[i].state]);
    }
}

/* stats - show CPU%, stack watermark, context-switch count */
static void cmd_stats(int argc, char **argv)
{
    (void)argc; (void)argv;
    rtos_stats_t s;
    rtos_stats_get(&s);

    printf("\r\nUptime: %lu ms\r\n\r\n", (unsigned long)s.uptime_ms);
    printf("  ID  %-10s  CPU%%  SWITCHES   STACK_USED/TOTAL\r\n", "NAME");
    printf("  --  ----------  ----  ---------  ----------------\r\n");
    for (uint8_t i = 0; i < s.num_tasks; i++) {
        const rtos_task_stats_t *t = &s.tasks[i];
        printf("  %2u  %-10s  %3u%%  %9lu  %u / %u words\r\n",
               (unsigned)i,
               t->name,
               (unsigned)t->cpu_percent,
               (unsigned long)t->switch_count,
               (unsigned)t->stack_peak_words,
               (unsigned)t->stack_size_words);
    }
}

/* uptime - milliseconds since boot */
static void cmd_uptime(int argc, char **argv)
{
    (void)argc; (void)argv;
    printf("Uptime: %lu ms\r\n", (unsigned long)tick_count);
}

/* ------------------------------------------------------------------ */
/*  Line dispatch                                                     */
/* ------------------------------------------------------------------ */

static void dispatch(char *line)
{
    /* Tokenise: split on whitespace, stop at SHELL_ARGC_MAX tokens */
    char *argv[SHELL_ARGC_MAX];
    int   argc = 0;
    char *p    = line;

    while (*p != '\0' && argc < SHELL_ARGC_MAX) {
        while (*p == ' ') p++;           /* skip leading / inter-token spaces */
        if (*p == '\0') break;
        argv[argc++] = p;
        while (*p != '\0' && *p != ' ') p++;
        if (*p != '\0') *p++ = '\0';    /* NUL-terminate this token */
    }

    if (argc == 0) return;

    for (int i = 0; i < num_cmds; i++) {
        if (strcmp(argv[0], cmds[i].name) == 0) {
            cmds[i].fn(argc, argv);
            return;
        }
    }
    printf("Unknown command: '%s'  (type 'help')\r\n", argv[0]);
}

/* ------------------------------------------------------------------ */
/*  Public API                                                        */
/* ------------------------------------------------------------------ */

void shell_init(void)
{
    num_cmds = 0;
    line_len = 0;

    /* Register built-in commands - order determines 'help' listing */
    shell_register("help",   "list all commands",              cmd_help);
    shell_register("tasks",  "show task names and states",     cmd_tasks);
    shell_register("stats",  "show CPU%%, stack, switch count", cmd_stats);
    shell_register("uptime", "ms elapsed since boot",          cmd_uptime);
}

bool shell_register(const char *name, const char *help, shell_cmd_fn fn)
{
    if (num_cmds >= SHELL_CMD_MAX) return false;
    cmds[num_cmds].name = name;
    cmds[num_cmds].help = help;
    cmds[num_cmds].fn   = fn;
    num_cmds++;
    return true;
}

void shell_tick(void)
{
    int c = getchar_timeout_us(0);   /* non-blocking: returns immediately */
    if (c == PICO_ERROR_TIMEOUT) return;

    if (c == '\r' || c == '\n') {
        printf("\r\n");
        if (line_len > 0) {
            line_buf[line_len] = '\0';
            dispatch(line_buf);
        }
        line_len = 0;
        printf("> ");
        return;
    }

    if (c == 127 || c == '\b') {         /* DEL / backspace */
        if (line_len > 0) {
            line_len--;
            printf("\b \b");             /* erase character on terminal */
        }
        return;
    }

    if (isprint(c) && line_len < SHELL_LINE_MAX - 1) {
        line_buf[line_len++] = (char)c;
        putchar(c);                      /* echo to terminal */
    }
}
