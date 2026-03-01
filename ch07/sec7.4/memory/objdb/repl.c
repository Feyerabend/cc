/* repl.c  —  interactive shell */

#include "objdb.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>
#include <errno.h>

/* -- colour helpers -- */
#define COL_RESET   "\033[0m"
#define COL_BOLD    "\033[1m"
#define COL_PROMPT  "\033[1;36m"
#define COL_OK      "\033[1;32m"
#define COL_ERR     "\033[1;31m"
#define COL_WARN    "\033[1;33m"
#define COL_DIM     "\033[2m"
#define COL_CMD     "\033[1;34m"

/* -- line buffer: large enough that "normal" use never hits the limit -- */
#define LINE_BUF 4096

/* flush_stdin: discard remainder of an overlong input line.
   Called when fgets filled the buffer without finding '\n'. */
static void flush_stdin(void) {
    int c;
    while ((c = getchar()) != '\n' && c != EOF)
        ;
}

/* trim: strip trailing CR/LF/spaces in-place */
static void trim(char *s) {
    int n = (int)strlen(s);
    while (n > 0 && ((unsigned char)s[n-1] <= ' ')) s[--n] = '\0';
}

/* next_tok: return next whitespace-delimited token from *rest,
   advancing *rest past it.  Returns NULL if nothing left */
static char *next_tok(char **rest) {
    if (!rest || !*rest) return NULL;
    /* skip leading spaces */
    while (**rest == ' ' || **rest == '\t') (*rest)++;
    if (**rest == '\0') return NULL;
    char *start = *rest;
    while (**rest && **rest != ' ' && **rest != '\t') (*rest)++;
    if (**rest != '\0') { **rest = '\0'; (*rest)++; }
    return start;
}

/* rest_of_line: return pointer to first non-space character
   remaining in the buffer, or NULL if nothing left */
static char *rest_of_line(char *p) {
    if (!p) return NULL;
    while (*p == ' ' || *p == '\t') p++;
    return (*p == '\0') ? NULL : p;
}

/* parse_int: strict integer parse — rejects non-numeric input.
   Returns true on success and writes *out */
static bool parse_int(const char *s, int64_t *out) {
    if (!s || *s == '\0') return false;
    char *end;
    errno = 0;
    long long v = strtoll(s, &end, 10);
    /* reject if: no digits consumed, trailing garbage, or overflow */
    if (end == s || *end != '\0' || errno == ERANGE) return false;
    *out = (int64_t)v;
    return true;
}

/* parse_float: strict float parse — rejects non-numeric input. */
static bool parse_float(const char *s, double *out) {
    if (!s || *s == '\0') return false;
    char *end;
    errno = 0;
    double v = strtod(s, &end);
    if (end == s || *end != '\0' || errno == ERANGE) return false;
    *out = v;
    return true;
}

/* validate_key_input: key must be printable, no whitespace,
   within MAX_KEY_LEN.  Gives a user-friendly error on failure */
static bool validate_key_input(const char *key) {
    if (!key || key[0] == '\0') {
        printf(COL_ERR "  error: key cannot be empty\n" COL_RESET);
        return false;
    }
    if (strlen(key) >= MAX_KEY_LEN) {
        printf(COL_ERR "  error: key too long (max %d chars)\n" COL_RESET,
               MAX_KEY_LEN - 1);
        return false;
    }
    for (const char *p = key; *p; p++) {
        if ((unsigned char)*p < 0x20 || *p == ' ' || *p == '\t') {
            printf(COL_ERR
                   "  error: key contains invalid character (0x%02x)\n"
                   COL_RESET, (unsigned char)*p);
            return false;
        }
    }
    return true;
}

/* validate_label_input: labels (frame/checkpoint names) may
   contain spaces but not control characters */
static bool validate_label_input(const char *label) {
    if (!label || label[0] == '\0') {
        printf(COL_ERR "  error: name cannot be empty\n" COL_RESET);
        return false;
    }
    if (strlen(label) >= MAX_KEY_LEN) {
        printf(COL_ERR "  error: name too long (max %d chars)\n" COL_RESET,
               MAX_KEY_LEN - 1);
        return false;
    }
    for (const char *p = label; *p; p++) {
        if ((unsigned char)*p < 0x20) {
            printf(COL_ERR
                   "  error: name contains control character (0x%02x)\n"
                   COL_RESET, (unsigned char)*p);
            return false;
        }
    }
    return true;
}


static void print_help(void) {
    printf(COL_BOLD "\n  objdb interactive shell\n" COL_RESET);
    printf(COL_DIM  "  --------------------------------------------\n" COL_RESET);
    printf("  " COL_CMD "set" COL_RESET "  <key> int   <n>   " COL_DIM "— store integer\n"   COL_RESET);
    printf("  " COL_CMD "set" COL_RESET "  <key> float <n>   " COL_DIM "— store float\n"     COL_RESET);
    printf("  " COL_CMD "set" COL_RESET "  <key> str   <...> " COL_DIM "— store string\n"    COL_RESET);
    printf("  " COL_CMD "get" COL_RESET "  <key>             " COL_DIM "— read one object\n"  COL_RESET);
    printf("  " COL_CMD "del" COL_RESET "  <key>             " COL_DIM "— delete object\n"    COL_RESET);
    printf("  " COL_CMD "dump" COL_RESET "                   " COL_DIM "— print all objects\n" COL_RESET);
    printf("  " COL_CMD "query" COL_RESET " [int|float|str]  " COL_DIM "— query with optional type filter\n" COL_RESET);
    printf(COL_DIM  "  --------------------------------------------\n" COL_RESET);
    printf("  " COL_CMD "frame push" COL_RESET " <label>     " COL_DIM "— open a transaction frame\n"   COL_RESET);
    printf("  " COL_CMD "frame commit" COL_RESET "           " COL_DIM "— commit current frame\n"        COL_RESET);
    printf("  " COL_CMD "frame rollback" COL_RESET "         " COL_DIM "— undo current frame\n"          COL_RESET);
    printf("  " COL_CMD "frame list" COL_RESET "             " COL_DIM "— show frame stack\n"            COL_RESET);
    printf(COL_DIM  "  --------------------------------------------\n" COL_RESET);
    printf("  " COL_CMD "checkpoint" COL_RESET " <name>      " COL_DIM "— set a named save point\n"     COL_RESET);
    printf("  " COL_CMD "backtrack"  COL_RESET "  <name>     " COL_DIM "— rewind to named checkpoint\n" COL_RESET);
    printf(COL_DIM  "  --------------------------------------------\n" COL_RESET);
    printf("  " COL_CMD "help" COL_RESET "                   " COL_DIM "— this message\n"    COL_RESET);
    printf("  " COL_CMD "quit" COL_RESET "                   " COL_DIM "— exit\n\n"          COL_RESET);
}


static void print_object(Object *o) {
    if (!o) return;
    printf("  " COL_OK "%-22s" COL_RESET, o->key);
    switch (o->type) {
    case OBJ_INT:    printf("= %lld",   (long long)o->val.i); break;
    case OBJ_FLOAT:  printf("= %g",     o->val.f);            break;
    case OBJ_STRING: printf("= \"%s\"", o->val.s);            break;
    default:         printf("= <null>");                       break;
    }
    const char *tn;
    switch (o->type) {
    case OBJ_INT:    tn = "int";   break;
    case OBJ_FLOAT:  tn = "float"; break;
    case OBJ_STRING: tn = "str";   break;
    default:         tn = "null";  break;
    }
    printf(COL_DIM "  (%s, v%u)\n" COL_RESET, tn, o->version);
}

/* render_prompt: shows active frame path in the prompt */
static void render_prompt(ObjDB *db) {
    printf(COL_PROMPT "objdb" COL_RESET);
    if (db->frame_top < 0) {
        printf(COL_DIM " ∅ " COL_RESET);
    } else {
        for (int i = 0; i <= db->frame_top; i++) {
            printf(COL_DIM "/" COL_RESET);
            printf(db->frames[i].is_checkpoint ? COL_WARN : COL_CMD);
            printf("%s" COL_RESET, db->frames[i].label);
        }
        printf(" ");
    }
    printf("> ");
    fflush(stdout);
}


int main(void) {
    ObjDB *db = calloc(1, sizeof(ObjDB));
    if (!db) { fprintf(stderr, "OOM\n"); return 1; }
    db_init(db);

    printf(COL_BOLD "\n  objdb — object database shell\n" COL_RESET);
    printf(COL_DIM  "  type 'help' for commands, 'quit' to exit\n\n" COL_RESET);

    char line[LINE_BUF];
    while (1) {
        render_prompt(db);

        if (!fgets(line, sizeof(line), stdin)) {
            printf(COL_DIM "\n(EOF)\n" COL_RESET);
            break;
        }

        /* Detect truncated line (no '\n' before buffer end) */
        size_t len = strlen(line);
        if (len == sizeof(line) - 1 && line[len-1] != '\n') {
            printf(COL_ERR
                   "  error: input line too long (max %d chars) — discarded\n"
                   COL_RESET, (int)(sizeof(line) - 2));
            flush_stdin();
            continue;
        }

        trim(line);
        if (line[0] == '\0' || line[0] == '#') continue; /* blank / comment */

        char *p   = line;
        char *cmd = next_tok(&p);
        if (!cmd) continue;

        /* -- quit -- */
        if (strcmp(cmd,"quit")==0 || strcmp(cmd,"exit")==0 || strcmp(cmd,"q")==0) {
            printf(COL_DIM "bye.\n" COL_RESET);
            break;
        }

        /* -- help -- */
        else if (strcmp(cmd,"help")==0 || strcmp(cmd,"?")==0) {
            print_help();
        }

        /* -- dump -- */
        else if (strcmp(cmd,"dump")==0) {
            db_dump(db);
        }

        /* -- get <key> -- */
        else if (strcmp(cmd,"get")==0) {
            char *key = next_tok(&p);
            if (!key) {
                printf(COL_ERR "  usage: get <key>\n" COL_RESET); continue;
            }
            if (!validate_key_input(key)) continue;
            Object *o = db_get(db, key);
            if (!o) printf(COL_WARN "  '%s' not found\n" COL_RESET, key);
            else    print_object(o);
        }

        /* -- del <key> -- */
        else if (strcmp(cmd,"del")==0 || strcmp(cmd,"delete")==0) {
            char *key = next_tok(&p);
            if (!key) {
                printf(COL_ERR "  usage: del <key>\n" COL_RESET); continue;
            }
            if (!validate_key_input(key)) continue;
            if (db_delete(db, key))
                printf(COL_OK "  deleted '%s'\n" COL_RESET, key);
            else
                printf(COL_WARN "  '%s' not found\n" COL_RESET, key);
        }

        /* -- set <key> <type> <value> -- */
        else if (strcmp(cmd,"set")==0) {
            char *key  = next_tok(&p);
            char *type = next_tok(&p);
            char *val  = rest_of_line(p);

            if (!key || !type) {
                printf(COL_ERR "  usage: set <key> int|float|str <value>\n"
                       COL_RESET);
                continue;
            }
            if (!validate_key_input(key)) continue;

            if (strcmp(type,"int")==0) {
                if (!val) {
                    printf(COL_ERR "  error: missing integer value\n" COL_RESET);
                    continue;
                }
                int64_t n;
                if (!parse_int(val, &n)) {
                    printf(COL_ERR "  error: '%s' is not a valid integer\n"
                           COL_RESET, val);
                    continue;
                }
                if (db_set_int(db, key, n))
                    printf(COL_OK "  set %s = %lld\n" COL_RESET, key, (long long)n);
                else
                    printf(COL_ERR "  set failed\n" COL_RESET);

            } else if (strcmp(type,"float")==0) {
                if (!val) {
                    printf(COL_ERR "  error: missing float value\n" COL_RESET);
                    continue;
                }
                double f;
                if (!parse_float(val, &f)) {
                    printf(COL_ERR "  error: '%s' is not a valid number\n"
                           COL_RESET, val);
                    continue;
                }
                if (db_set_float(db, key, f))
                    printf(COL_OK "  set %s = %g\n" COL_RESET, key, f);
                else
                    printf(COL_ERR "  set failed\n" COL_RESET);

            } else if (strcmp(type,"str")==0 || strcmp(type,"string")==0) {
                /* Empty string is valid — store it as-is               */
                const char *s = val ? val : "";
                if (strlen(s) >= MAX_STR_LEN)
                    printf(COL_WARN
                           "  warning: value will be truncated to %d chars\n"
                           COL_RESET, MAX_STR_LEN - 1);
                if (db_set_string(db, key, s))
                    printf(COL_OK "  set %s = \"%s\"\n" COL_RESET, key, s);
                else
                    printf(COL_ERR "  set failed\n" COL_RESET);

            } else {
                printf(COL_ERR "  error: unknown type '%s' — use int, float, str\n"
                       COL_RESET, type);
            }
        }

        /* -- query [type] -- */
        else if (strcmp(cmd,"query")==0) {
            char *tf = next_tok(&p);
            Query q  = db_query_new(db);
            if (tf) {
                if      (strcmp(tf,"int")==0)   db_query_filter_type(&q, OBJ_INT);
                else if (strcmp(tf,"float")==0) db_query_filter_type(&q, OBJ_FLOAT);
                else if (strcmp(tf,"str")==0 ||
                         strcmp(tf,"string")==0) db_query_filter_type(&q, OBJ_STRING);
                else {
                    printf(COL_ERR "  error: unknown type filter '%s' — use int, float, str\n"
                           COL_RESET, tf);
                    continue;
                }
            }
            db_query_run(db, &q);
            db_query_print(db, &q);
        }

        /* -- frame push|commit|rollback|list -- */
        else if (strcmp(cmd,"frame")==0) {
            char *sub = next_tok(&p);
            if (!sub) {
                printf(COL_ERR "  usage: frame push|commit|rollback|list\n"
                       COL_RESET);
                continue;
            }
            if (strcmp(sub,"push")==0) {
                char *label = rest_of_line(p);
                if (!label) {
                    printf(COL_ERR "  usage: frame push <label>\n" COL_RESET);
                    continue;
                }
                if (!validate_label_input(label)) continue;
                db_push_frame(db, label);

            } else if (strcmp(sub,"commit")==0) {
                db_commit_frame(db);

            } else if (strcmp(sub,"rollback")==0) {
                db_rollback_frame(db);

            } else if (strcmp(sub,"list")==0) {
                db_dump_frames(db);

            } else {
                printf(COL_ERR "  error: unknown frame sub-command '%s'\n"
                       COL_RESET, sub);
            }
        }

        /* -- checkpoint <name> -- */
        else if (strcmp(cmd,"checkpoint")==0 || strcmp(cmd,"cp")==0) {
            char *name = rest_of_line(p);
            if (!name) {
                printf(COL_ERR "  usage: checkpoint <name>\n" COL_RESET);
                continue;
            }
            if (!validate_label_input(name)) continue;
            db_checkpoint(db, name);
        }

        /* -- backtrack <name> -- */
        else if (strcmp(cmd,"backtrack")==0 || strcmp(cmd,"bt")==0) {
            char *name = rest_of_line(p);
            if (!name) {
                printf(COL_ERR "  usage: backtrack <name>\n" COL_RESET);
                continue;
            }
            if (!validate_label_input(name)) continue;
            db_backtrack_to(db, name);
        }

        /* -- unknown -- */
        else {
            printf(COL_ERR "  unknown command '%s' — type 'help'\n"
                   COL_RESET, cmd);
        }
    }

    free(db);
    return 0;
}
