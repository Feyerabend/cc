#ifndef FORTH_H
#define FORTH_H

#include <stdbool.h>
#include <stdint.h>

/*
 * forth.h — minimal token-threaded Forth for pico-lambda
 *
 * Vocabulary: arithmetic, stack ops, comparisons, logic, control flow,
 * output, string literals, word definitions, constants, variables.
 *
 * No float stack, no RTOS words, no VGA, no filesystem.
 */

/* Re-initialise the interpreter to a clean, stateless state.
 * Call this before each HTTP request so requests cannot affect each other. */
void forth_init(void);

/* Evaluate a NUL-terminated Forth source string.
 * May span multiple lines; each line is processed in order. */
void forth_eval_string(const char *src);

/* Redirect all Forth output (. .S EMIT CR ." ...) to fn.
 * Must be called after forth_init() and before forth_eval_string().
 * If not set, output is silently discarded. */
void forth_set_output_fn(void (*fn)(const char *s, int len));

/* Hide every word whose name is NOT in the allowed[] array.
 * Must be called after forth_init() and before forth_eval_string().
 * Internal executor tokens (names starting with '(') are never hidden. */
void forth_restrict_to(const char **allowed, int count);

/* Returns true if the last forth_eval_string() encountered any error
 * (unknown word, stack underflow/overflow, execution step limit). */
bool forth_had_error(void);

#endif /* FORTH_H */
