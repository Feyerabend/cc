/* main.c  —  demonstration of the object database
   Shows: Frame Stack, Checkpoints, Backtracking, State Machine */

#include "objdb.h"
#include <stdio.h>
#include <stdlib.h>

static void separator(const char *title) {
    printf("\n---------------------\n");
    printf("  %s\n", title);
    printf("---------------------\n");
}

int main(void) {
    ObjDB *db = calloc(1, sizeof(ObjDB));
    if (!db) { fprintf(stderr, "OOM\n"); return 1; }
    db_init(db);

    separator("1. Baseline data — no frame, changes are permanent");
    db_set_string(db, "user:alice",  "Alice Andersson");
    db_set_string(db, "user:bob",    "Bob Bergstrom");
    db_set_int   (db, "score:alice", 1200);
    db_set_int   (db, "score:bob",   850);
    db_set_float (db, "ratio:alice", 0.87);
    db_dump(db);

    separator("2. Frame — commit path");
    db_push_frame(db, "update_scores");
        db_set_int(db, "score:alice", 1350);
        db_set_int(db, "score:carol", 500);
    db_commit_frame(db);
    db_dump(db);

    separator("3. Frame — rollback path (bad batch update)");
    db_push_frame(db, "bad_batch");
        db_set_int   (db, "score:alice", 9999);
        db_set_string(db, "user:bob",    "DELETED");
        db_delete    (db, "ratio:alice");
        printf("\n  State mid-frame (before rollback):\n");
        db_dump(db);
    db_rollback_frame(db);
    printf("  State after rollback:\n");
    db_dump(db);

    separator("4. Checkpoint — backtrack to named save point");
    db_push_frame(db, "outer_tx");
        db_set_string(db, "config:mode", "production");
        db_checkpoint(db, "before_risky_ops");
            db_push_frame(db, "risky_insert");
                db_set_int   (db, "score:dave", 300);
                db_set_float (db, "ratio:dave", 0.55);
                db_set_string(db, "user:dave",  "Dave Dahl");
            db_commit_frame(db);
            db_push_frame(db, "even_riskier");
                db_set_int(db, "score:alice", 0);
            /* note: not committing this frame */
        db_dump_frames(db);
        db_backtrack_to(db, "before_risky_ops");
    db_commit_frame(db);
    printf("  State after backtrack + outer commit:\n");
    db_dump(db);

    separator("5. Query state machine — integers only");
    Query q = db_query_new(db);
    db_query_filter_type(&q, OBJ_INT);
    db_query_run(db, &q);
    db_query_print(db, &q);

    separator("6. Query state machine — all objects");
    Query q2 = db_query_new(db);
    db_query_run(db, &q2);
    db_query_print(db, &q2);

    separator("7. Multiple checkpoints — layered backtracking");
    db_checkpoint(db, "start");
        db_set_int(db, "counter", 1);
        db_checkpoint(db, "mid");
            db_set_int(db, "counter", 2);
            db_set_int(db, "counter", 3);
        db_backtrack_to(db, "start");

    printf("  counter after backtrack to 'start': ");
    Object *counter = db_get(db, "counter");
    if (!counter) printf("does not exist (correctly erased!)\n\n");
    else          printf("%lld\n\n", (long long)counter->val.i);

    printf("Done.\n");
    free(db);
    return 0;
}
