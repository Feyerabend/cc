// Runs the Lisp game VM on a PC.
//
//   lisp_host                  interactive prompt
//   lisp_host game.lisp ...    run a game without the hardware
//
// Options for running a game:
//   -f N        run N frames (default 300)
//   -p B@F      press button B (a, b, x or y) at frame F
//   -p B@F-G    hold button B from frame F to frame G
//   -o FILE     save the last frame as a PPM image
//   -q          print only errors and the summary

#include "../lisp_vm.h"
#include "../lisp_game.h"
#include "display_host.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_PRESSES 64

typedef struct {
    button_t button;
    int from;
    int to;
} press_t;

static lisp_vm_t vm;

static char *read_file(const char *path) {
    FILE *f = fopen(path, "rb");
    if (f == NULL) return NULL;
    fseek(f, 0, SEEK_END);
    long size = ftell(f);
    fseek(f, 0, SEEK_SET);
    char *buf = malloc((size_t) size + 1);
    if (buf != NULL) {
        size_t n = fread(buf, 1, (size_t) size, f);
        buf[n] = '\0';
    }
    fclose(f);
    return buf;
}

static bool parse_press(const char *s, press_t *p) {
    const char *names = "abxy";
    const char *found = (*s != '\0') ? strchr(names, *s) : NULL;
    if (found == NULL || s[1] != '@') return false;
    p->button = (button_t) (found - names);
    char *end;
    p->from = (int) strtol(s + 2, &end, 10);
    p->to = p->from;
    if (*end == '-') p->to = (int) strtol(end + 1, &end, 10);
    return *end == '\0' && p->from >= 0 && p->to >= p->from;
}

// True when every ( has its ), ignoring strings and comments
static bool balanced(const char *s) {
    int depth = 0;
    bool in_string = false;
    for (; *s; s++) {
        if (in_string) {
            if (*s == '\\' && s[1]) s++;
            else if (*s == '"') in_string = false;
        } else if (*s == '"') {
            in_string = true;
        } else if (*s == ';') {
            while (*s && *s != '\n') s++;
            if (!*s) break;
        } else if (*s == '(') {
            depth++;
        } else if (*s == ')') {
            depth--;
        }
    }
    return depth <= 0 && !in_string;
}

static int repl(void) {
    char input[4096];
    size_t len = 0;
    printf("Lisp game VM. Ctrl-D to quit.\n");

    for (;;) {
        printf(len == 0 ? "> " : "  ");
        fflush(stdout);
        if (fgets(input + len, (int) (sizeof(input) - len), stdin) == NULL) break;
        len = strlen(input);
        if (!balanced(input) && len < sizeof(input) - 1) continue;

        lisp_value_t *result = lisp_run(&vm, input);
        if (result == NULL) {
            printf("Error: %s\n", lisp_error(&vm));
        } else {
            lisp_print(result);
            printf("\n");
        }
        len = 0;
    }
    printf("\n");
    return 0;
}

int main(int argc, char **argv) {
    const char *file = NULL;
    const char *image = NULL;
    int frames = 300;
    bool quiet = false;
    press_t presses[MAX_PRESSES];
    int press_count = 0;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "-f") == 0 && i + 1 < argc) {
            frames = atoi(argv[++i]);
        } else if (strcmp(argv[i], "-o") == 0 && i + 1 < argc) {
            image = argv[++i];
        } else if (strcmp(argv[i], "-q") == 0) {
            quiet = true;
        } else if (strcmp(argv[i], "-p") == 0 && i + 1 < argc && press_count < MAX_PRESSES) {
            if (!parse_press(argv[++i], &presses[press_count++])) {
                fprintf(stderr, "Bad button press: %s (use for example x@10 or x@10-20)\n", argv[i]);
                return 2;
            }
        } else if (argv[i][0] != '-' && file == NULL) {
            file = argv[i];
        } else {
            fprintf(stderr, "usage: %s [game.lisp [-f frames] [-p button@frame[-frame]] [-o image.ppm] [-q]]\n", argv[0]);
            return 2;
        }
    }

    disp_init(NULL);
    disp_framebuffer_alloc();
    buttons_init();
    lisp_init(&vm);
    lisp_game_init(&vm);

    if (file == NULL) return repl();

    char *source = read_file(file);
    if (source == NULL) {
        fprintf(stderr, "Cannot read %s\n", file);
        return 2;
    }

    if (quiet) {
        // Silence (print ...) in the game, but keep our own summary
        fflush(stdout);
        if (freopen("/dev/null", "w", stdout) == NULL) quiet = false;
    }

    int status = 0;
    int frame = 0;
    if (lisp_run(&vm, source) == NULL) {
        fprintf(stderr, "Error while loading %s: %s\n", file, lisp_error(&vm));
        status = 1;
    } else {
        for (frame = 0; frame < frames && vm.running; frame++) {
            for (int b = 0; b < BUTTON_COUNT; b++) {
                bool down = false;
                for (int i = 0; i < press_count; i++) {
                    if (presses[i].button == (button_t) b && frame >= presses[i].from && frame <= presses[i].to) {
                        down = true;
                    }
                }
                host_set_button((button_t) b, down);
            }
            if (!lisp_game_frame(&vm)) {
                fprintf(stderr, "Error in frame %d: %s\n", frame, lisp_error(&vm));
                status = 1;
                break;
            }
        }
    }

    if (image != NULL && !host_save_ppm(image)) {
        fprintf(stderr, "Cannot write %s\n", image);
        status = 2;
    }

    fprintf(stderr, "%s: %d frames, %u collections, %u of %d cells in use, screen %08x\n",
            file, frame, (unsigned) vm.gc_count, (unsigned) vm.cells_used, LISP_HEAP_SIZE,
            (unsigned) host_screen_hash());
    free(source);
    return status;
}
