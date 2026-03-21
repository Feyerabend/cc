#ifndef SANDBOX_H
#define SANDBOX_H

/*
 * sandbox.h — word whitelist for pico-lambda
 *
 * sandbox_install() must be called after forth_init() and before
 * forth_eval_string().  It hides every word not on the whitelist so
 * that untrusted HTTP input cannot access memory primitives or
 * meta-programming words that could crash or escape the interpreter.
 */

void sandbox_install(void);

#endif /* SANDBOX_H */
