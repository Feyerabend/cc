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

/*
 * Parse and register a data declaration.  src is the text AFTER the "data"
 * keyword, already preprocessed (fn→\, Pi→Π, ->→→).
 *
 * Grammar (data declarations, no value indices):
 *   IDENT ['(' IDENT ':' type [',' ...]* ')'] 'where'
 *   (IDENT ':' type [';'])*
 *
 * On success registers the family + type constructor + each constructor as
 * globals in the permanent arena and returns the fam_idx.  Returns -1 on
 * failure (error already printed).
 */
int parse_data(const char *src);
