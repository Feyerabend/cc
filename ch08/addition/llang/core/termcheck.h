#pragma once
#include "term.h"

/* Structural termination checker for let rec / fix.
 *
 * Verifies that all recursive calls in the fix body are on structurally
 * smaller arguments obtained from pattern matching.  Tries each argument
 * position in turn; the first that works is accepted.
 *
 * fix_body : the body of TM_FIX, i.e. the \f. ... term.
 * name     : function name for error messages (may be NULL).
 *
 * Returns 1 if structurally recursive (or has no recursive calls at all),
 * 0 if no decreasing argument can be found.                                */
int term_check_structural(Term *fix_body, const char *name);
