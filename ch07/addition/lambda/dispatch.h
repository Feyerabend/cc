#ifndef DISPATCH_H
#define DISPATCH_H

#include <stdbool.h>

#define DISPATCH_BUF_SIZE 2048

typedef struct {
    char buf[DISPATCH_BUF_SIZE];
    int  len;
    bool ok;
} dispatch_result_t;

/* Evaluate Forth source src, capture output into out->buf, set out->ok. */
void dispatch_eval(const char *src, dispatch_result_t *out);

#endif /* DISPATCH_H */
