#ifndef OBJDB_H
#define OBJDB_H

#include <stdint.h>
#include <stdbool.h>

/* 
   OBJECT DATABASE  —  objdb.h
   Concepts demonstrated:
     • State Machine   — drives query/transaction lifecycle
     • Frame Stack     — tracks mutations per operation scope
     • Checkpoints     — named snapshots for targeted rollback
     • Backtracking    — unwinds frames to restore prior state
*/

#define MAX_OBJECTS     256
#define MAX_KEY_LEN      64
#define MAX_STR_LEN     128
#define MAX_FRAMES      128
#define MAX_CHECKPOINTS  16
#define MAX_UNDO_OPS    512

/* Object store */
typedef enum {
    OBJ_INT,
    OBJ_FLOAT,
    OBJ_STRING,
    OBJ_NULL
} ObjType;

typedef struct {
    char     key[MAX_KEY_LEN];
    ObjType  type;
    union {
        int64_t  i;
        double   f;
        char     s[MAX_STR_LEN];
    } val;
    bool     exists;        /* tombstone flag */
    uint32_t version;       /* increments on every write */
} Object;

/* Undo log entry — what a frame records when it mutates an object */
typedef struct {
    int    slot;            /* index into db->objects[]   */
    Object before;          /* full snapshot before change */
} UndoEntry;

/* Frame  — one scope of work (transaction, sub-query, etc.) */
typedef struct {
    char       label[MAX_KEY_LEN];
    bool       is_checkpoint;   /* named save-point?        */
    UndoEntry  undo[MAX_UNDO_OPS];
    int        undo_count;
} Frame;

/* Query state machine states */
typedef enum {
    QS_IDLE,        /* no query running              */
    QS_SCAN,        /* iterating over all objects    */
    QS_FILTER,      /* applying predicate            */
    QS_PROJECT,     /* formatting matching results   */
    QS_DONE,        /* finished — results ready      */
    QS_ERROR        /* something went wrong          */
} QueryState;

/* Query descriptor */
typedef struct {
    QueryState state;
    char       predicate_key[MAX_KEY_LEN];  /* filter: key must match */
    ObjType    predicate_type;              /* filter: type must match */
    bool       has_type_filter;
    /* result buffer */
    int        results[MAX_OBJECTS];
    int        result_count;
    int        cursor;          /* current scan position   */
} Query;

/* The database itself */
typedef struct {
    Object  objects[MAX_OBJECTS];
    int     object_count;

    /* frame stack */
    Frame   frames[MAX_FRAMES];
    int     frame_top;          /* -1 = empty              */

    /* quick checkpoint index: name → frame index           */
    struct { char name[MAX_KEY_LEN]; int frame_idx; }
            checkpoints[MAX_CHECKPOINTS];
    int     checkpoint_count;
} ObjDB;


/* API */

/* lifecycle */
void    db_init(ObjDB *db);

/* frame / checkpoint / backtrack */
bool    db_push_frame(ObjDB *db, const char *label);
bool    db_commit_frame(ObjDB *db);          /* discard undo log, pop */
bool    db_rollback_frame(ObjDB *db);        /* undo all ops, pop     */
bool    db_checkpoint(ObjDB *db, const char *name); /* named save-point */
bool    db_backtrack_to(ObjDB *db, const char *checkpoint_name);

/* object mutations (record undo entries into current frame) */
bool    db_set_int(ObjDB *db, const char *key, int64_t value);
bool    db_set_float(ObjDB *db, const char *key, double value);
bool    db_set_string(ObjDB *db, const char *key, const char *value);
bool    db_delete(ObjDB *db, const char *key);

/* reads (no frame interaction) */
Object *db_get(ObjDB *db, const char *key);

/* query state machine */
Query   db_query_new(ObjDB *db);
void    db_query_filter_type(Query *q, ObjType type);
void    db_query_run(ObjDB *db, Query *q);  /* drives state machine  */
void    db_query_print(ObjDB *db, Query *q);

/* diagnostics */
void    db_dump(ObjDB *db);
void    db_dump_frames(ObjDB *db);

#endif /* OBJDB_H */
