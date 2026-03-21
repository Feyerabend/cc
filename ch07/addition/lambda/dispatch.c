/*
 * dispatch.c — bridge between the HTTP layer and the Forth interpreter
 *
 * dispatch_eval() is the single entry point called by net.c for every
 * POST /eval request.  It is deliberately stateless: forth_init() is
 * called on every invocation so no word defined in one request leaks
 * into the next.
 */

#include "dispatch.h"
#include "forth.h"
#include "sandbox.h"
#include <string.h>

/* ------------------------------------------------------------------ */
/*  Output callback                                                    */
/* ------------------------------------------------------------------ */

/* Appended to by the output_cb below; pointer is valid only during
 * dispatch_eval() and must not be used after it returns. */
static dispatch_result_t *active_result = NULL;

static void output_cb(const char *s, int len)
{
    if (!active_result || len <= 0) return;

    int remaining = DISPATCH_BUF_SIZE - 1 - active_result->len;
    if (remaining <= 0) return;

    int copy = len < remaining ? len : remaining;
    memcpy(active_result->buf + active_result->len, s, copy);
    active_result->len += copy;
    /* buf is NUL-terminated after dispatch_eval() returns */
}

/* ------------------------------------------------------------------ */
/*  Public API                                                         */
/* ------------------------------------------------------------------ */

void dispatch_eval(const char *src, dispatch_result_t *out)
{
    /* Initialise result buffer */
    out->len = 0;
    out->ok  = false;
    out->buf[0] = '\0';

    /* Fresh interpreter on every call — this is what makes it stateless */
    forth_init();

    /* Restrict to the safe word set */
    sandbox_install();

    /* Wire output into out->buf via the callback */
    active_result = out;
    forth_set_output_fn(output_cb);

    /* Run */
    forth_eval_string(src);

    /* Detach callback before touching out again */
    active_result = NULL;

    /* NUL-terminate */
    out->buf[out->len] = '\0';

    out->ok = !forth_had_error();
}
