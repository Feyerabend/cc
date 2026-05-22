#pragma once
#include "term.h"

/*
 * Surface grammar (similar to the Python parser):
 *
 *   expr     ::= lam | pi | app_expr
 *   lam      ::= ('λ' | '\') ident+ '.' expr
 *   pi       ::= 'Π' '(' ident ':' expr ')' '.' expr
 *   app_expr ::= atom+                        (left-assoc)
 *   atom     ::= ident | '(' expr ')' | 'Type' ['_' digit+]
 *
 * Named variables are resolved to de Bruijn indices during parsing.
 * Returns NULL and prints an error on parse failure.
 */

Term *parse(Arena *a, const char *src);
