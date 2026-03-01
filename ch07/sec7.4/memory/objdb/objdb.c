/* objdb.c the Object Database implementation */

#include "objdb.h"
#include <stdio.h>
#include <string.h>
#include <stdlib.h>

/* Internal: safe string copy — always NUL-terminates dst.
   Returns false if src was truncated. */
static bool safe_copy(char *dst, const char *src, size_t dst_size) {
    if (!dst || !src || dst_size == 0) return false;
    size_t n = strlen(src);
    bool truncated = (n >= dst_size);
    if (truncated) n = dst_size - 1;
    memcpy(dst, src, n);
    dst[n] = '\0';
    return !truncated;
}

/* Internal: validate a key string.
   Must be non-empty, within MAX_KEY_LEN, printable, no spaces. */
static bool valid_key(const char *key) {
    if (!key || key[0] == '\0') return false;
    size_t len = 0;
    for (const char *p = key; *p; p++, len++) {
        if (len >= MAX_KEY_LEN - 1) return false;   /* too long */
        if ((unsigned char)*p < 0x20) return false; /* control characters */
        if (*p == ' ' || *p == '\t') return false;  /* no whitespace */
    }
    return true;
}

/* Internal: validate a label (frame / checkpoint name).
   Same rules as key but slightly more permissive — allows
   spaces inside the label so users can write e.g. readable names */
static bool valid_label(const char *label) {
    if (!label || label[0] == '\0') return false;
    size_t len = 0;
    for (const char *p = label; *p; p++, len++) {
        if (len >= MAX_KEY_LEN - 1) return false;
        if ((unsigned char)*p < 0x20) return false; /* no control chars */
    }
    return true;
}

/* Slot helpers */
static int find_slot(ObjDB *db, const char *key) {
    for (int i = 0; i < MAX_OBJECTS; i++)
        if (db->objects[i].exists &&
            strncmp(db->objects[i].key, key, MAX_KEY_LEN) == 0)
            return i;
    return -1;
}

static int alloc_slot(ObjDB *db, const char *key) {
    int s = find_slot(db, key);
    if (s >= 0) return s;               /* reuse existing key */
    for (int i = 0; i < MAX_OBJECTS; i++)
        if (!db->objects[i].exists) return i;
    return -1;                          /* store full */
}

/* Record a before-snapshot into the current frame's undo log.
   Called BEFORE any mutation so we can restore on rollback.
   For brand-new slots the "before" state is a zeroed Object
   with exists=false -- that is the correct undo target.       */
static bool record_undo(ObjDB *db, int slot) {
    if (db->frame_top < 0) return true; /* no frame -- nothing to undo */
    Frame *f = &db->frames[db->frame_top];
    if (f->undo_count >= MAX_UNDO_OPS) {
        fprintf(stderr, "[objdb] undo log full in frame '%s'\n", f->label);
        return false;
    }
    /* Only record the FIRST touch of a slot per frame -- later writes
       within the same frame would clobber the snapshot we want. */
    for (int i = 0; i < f->undo_count; i++)
        if (f->undo[i].slot == slot) return true; /* already captured */

    UndoEntry *e = &f->undo[f->undo_count];
    e->slot = slot;
    /* Copy current state -- if this is a fresh slot it will be zeroed
       (exists=false) which is exactly what rollback needs. */
    e->before = db->objects[slot];
    /* Guarantee the key in the snapshot is NUL-terminated */
    e->before.key[MAX_KEY_LEN - 1] = '\0';
    f->undo_count++;
    return true;
}

/* Lifecycle */
void db_init(ObjDB *db) {
    if (!db) return;
    memset(db, 0, sizeof(ObjDB));
    db->frame_top = -1;
}

/* Frame stack */
bool db_push_frame(ObjDB *db, const char *label) {
    if (!db) return false;
    if (!valid_label(label)) {
        fprintf(stderr, "[objdb] invalid frame label\n");
        return false;
    }
    if (db->frame_top + 1 >= MAX_FRAMES) {
        fprintf(stderr, "[objdb] frame stack full (max %d)\n", MAX_FRAMES);
        return false;
    }
    db->frame_top++;
    Frame *f = &db->frames[db->frame_top];
    memset(f, 0, sizeof(Frame));
    safe_copy(f->label, label, MAX_KEY_LEN);
    f->is_checkpoint = false;
    printf("[frame] push '%s'  (depth=%d)\n", f->label, db->frame_top);
    return true;
}

bool db_commit_frame(ObjDB *db) {
    if (!db) return false;
    if (db->frame_top < 0) {
        fprintf(stderr, "[objdb] no frame to commit\n"); return false;
    }
    Frame *f = &db->frames[db->frame_top];
    printf("[frame] commit '%s'  (%d mutation(s) made permanent)\n",
           f->label, f->undo_count);
    /* Discard undo log -- changes are now permanent. Zero the frame
       so stale pointers inside can't be accidentally reused. */
    memset(f, 0, sizeof(Frame));
    db->frame_top--;
    return true;
}

bool db_rollback_frame(ObjDB *db) {
    if (!db) return false;
    if (db->frame_top < 0) {
        fprintf(stderr, "[objdb] no frame to roll back\n"); return false;
    }
    Frame *f = &db->frames[db->frame_top];
    printf("[frame] rollback '%s'  (undoing %d mutation(s))\n",
           f->label, f->undo_count);
    /* Apply undo log in reverse -- last write undone first. */
    for (int i = f->undo_count - 1; i >= 0; i--) {
        int s = f->undo[i].slot;
        /* Bounds-check the slot index before writing */
        if (s < 0 || s >= MAX_OBJECTS) {
            fprintf(stderr, "[objdb] corrupt undo entry slot %d — skipped\n", s);
            continue;
        }
        db->objects[s] = f->undo[i].before;
    }
    memset(f, 0, sizeof(Frame));
    db->frame_top--;
    return true;
}

/* Checkpoints */
bool db_checkpoint(ObjDB *db, const char *name) {
    if (!db) return false;
    if (!valid_label(name)) {
        fprintf(stderr, "[objdb] invalid checkpoint name\n"); return false;
    }
    /* Guard both limits before touching anything */
    if (db->frame_top + 1 >= MAX_FRAMES) {
        fprintf(stderr, "[objdb] frame stack full — cannot set checkpoint\n");
        return false;
    }
    if (db->checkpoint_count >= MAX_CHECKPOINTS) {
        fprintf(stderr, "[objdb] checkpoint table full (max %d)\n",
                MAX_CHECKPOINTS);
        return false;
    }
    /* Check for duplicate checkpoint name */
    for (int i = 0; i < db->checkpoint_count; i++) {
        if (strncmp(db->checkpoints[i].name, name, MAX_KEY_LEN) == 0) {
            fprintf(stderr, "[objdb] checkpoint '%s' already exists\n", name);
            return false;
        }
    }

    if (!db_push_frame(db, name)) return false;   /* push -- can't fail now */
    db->frames[db->frame_top].is_checkpoint = true;

    int ci = db->checkpoint_count++;
    safe_copy(db->checkpoints[ci].name, name, MAX_KEY_LEN);
    db->checkpoints[ci].frame_idx = db->frame_top;
    printf("[checkpoint] '%s' set at frame depth %d\n", name, db->frame_top);
    return true;
}

bool db_backtrack_to(ObjDB *db, const char *name) {
    if (!db || !name) return false;

    /* Find checkpoint in index */
    int ci = -1;
    for (int i = 0; i < db->checkpoint_count; i++)
        if (strncmp(db->checkpoints[i].name, name, MAX_KEY_LEN) == 0) {
            ci = i; break;
        }
    if (ci < 0) {
        fprintf(stderr, "[objdb] unknown checkpoint '%s'\n", name);
        return false;
    }

    int target_depth = db->checkpoints[ci].frame_idx;
    if (target_depth > db->frame_top) {
        fprintf(stderr,
                "[objdb] checkpoint '%s' depth %d is above current top %d\n",
                name, target_depth, db->frame_top);
        return false;
    }

    printf("[backtrack] rewinding to checkpoint '%s' (frame %d → %d)\n",
           name, db->frame_top, target_depth);

    /* Roll back frames from top down to and including the checkpoint */
    while (db->frame_top >= target_depth)
        db_rollback_frame(db);

    /* Remove this checkpoint from the index.
       Any checkpoints whose frame_idx was above target_depth are now
       stale -- warn about and remove them too. */
    for (int i = db->checkpoint_count - 1; i >= 0; i--) {
        if (db->checkpoints[i].frame_idx >= target_depth) {
            if (i != ci)
                fprintf(stderr,
                    "[objdb] warning: checkpoint '%s' was inside rolled-back "
                    "region and has been removed\n",
                    db->checkpoints[i].name);
            /* Swap with last entry to remove */
            db->checkpoints[i] = db->checkpoints[--db->checkpoint_count];
        }
    }
    return true;
}

/*  Object mutations */
static bool prepare_write(ObjDB *db, const char *key, int *slot_out) {
    if (!db || !slot_out) return false;
    if (!valid_key(key)) {
        fprintf(stderr, "[objdb] invalid key\n"); return false;
    }
    int slot = alloc_slot(db, key);
    if (slot < 0) { fprintf(stderr, "[objdb] object store full\n"); return false; }
    if (!record_undo(db, slot)) return false;
    *slot_out = slot;
    return true;
}

bool db_set_int(ObjDB *db, const char *key, int64_t value) {
    int slot;
    if (!prepare_write(db, key, &slot)) return false;
    Object *o = &db->objects[slot];
    safe_copy(o->key, key, MAX_KEY_LEN);
    o->type   = OBJ_INT;
    o->val.i  = value;
    o->exists = true;
    o->version++;
    return true;
}

bool db_set_float(ObjDB *db, const char *key, double value) {
    int slot;
    if (!prepare_write(db, key, &slot)) return false;
    Object *o = &db->objects[slot];
    safe_copy(o->key, key, MAX_KEY_LEN);
    o->type   = OBJ_FLOAT;
    o->val.f  = value;
    o->exists = true;
    o->version++;
    return true;
}

bool db_set_string(ObjDB *db, const char *key, const char *value) {
    if (!value) { fprintf(stderr, "[objdb] null string value\n"); return false; }
    int slot;
    if (!prepare_write(db, key, &slot)) return false;
    Object *o = &db->objects[slot];
    safe_copy(o->key,   key,   MAX_KEY_LEN);
    if (!safe_copy(o->val.s, value, MAX_STR_LEN))
        fprintf(stderr, "[objdb] warning: string value truncated to %d chars\n",
                MAX_STR_LEN - 1);
    o->type   = OBJ_STRING;
    o->exists = true;
    o->version++;
    return true;
}

bool db_delete(ObjDB *db, const char *key) {
    if (!db) return false;
    if (!valid_key(key)) { fprintf(stderr, "[objdb] invalid key\n"); return false; }
    int slot = find_slot(db, key);
    if (slot < 0) return false;
    if (!record_undo(db, slot)) return false;
    db->objects[slot].exists = false;
    return true;
}

Object *db_get(ObjDB *db, const char *key) {
    if (!db || !valid_key(key)) return NULL;
    int slot = find_slot(db, key);
    return slot >= 0 ? &db->objects[slot] : NULL;
}

/* Query state machine */
Query db_query_new(ObjDB *db) {
    (void)db;
    Query q;
    memset(&q, 0, sizeof(q));
    q.state           = QS_IDLE;
    q.has_type_filter = false;
    q.cursor          = 0;
    q.result_count    = 0;
    return q;
}

void db_query_filter_type(Query *q, ObjType type) {
    if (!q) return;
    q->has_type_filter = true;
    q->predicate_type  = type;
}

/* Drive the state machine until QS_DONE or QS_ERROR.
   Transitions:  IDLE → SCAN → FILTER → PROJECT → DONE
   Each state does its work then sets the next state. */
void db_query_run(ObjDB *db, Query *q) {
    if (!db || !q) return;
    if (q->state == QS_DONE || q->state == QS_ERROR) {
        fprintf(stderr, "[objdb] query already run — create a new one\n");
        return;
    }
    q->state = QS_SCAN;   /* kick off */

    while (q->state != QS_DONE && q->state != QS_ERROR) {
        switch (q->state) {

        /* SCAN: collect all live objects */
        case QS_SCAN:
            q->result_count = 0;
            for (int i = 0; i < MAX_OBJECTS; i++) {
                if (!db->objects[i].exists) continue;
                if (q->result_count < MAX_OBJECTS)
                    q->results[q->result_count++] = i;
            }
            printf("[query:SCAN] found %d live object(s)\n", q->result_count);
            q->state = QS_FILTER;
            break;

        /* FILTER: apply type predicate */
        case QS_FILTER: {
            if (!q->has_type_filter) {
                printf("[query:FILTER] no predicate — keeping all\n");
                q->state = QS_PROJECT;
                break;
            }
            int kept = 0;
            for (int i = 0; i < q->result_count; i++) {
                int s = q->results[i];
                if (s < 0 || s >= MAX_OBJECTS) continue; /* safety */
                if (db->objects[s].type == q->predicate_type)
                    q->results[kept++] = s;
            }
            printf("[query:FILTER] %d → %d after type filter\n",
                   q->result_count, kept);
            q->result_count = kept;
            q->state = QS_PROJECT;
            break;
        }

        /* PROJECT: nothing more to do for a simple projection */
        case QS_PROJECT:
            printf("[query:PROJECT] projecting %d result(s)\n", q->result_count);
            q->state = QS_DONE;
            break;

        default:
            fprintf(stderr, "[objdb] query reached unexpected state %d\n",
                    q->state);
            q->state = QS_ERROR;
            break;
        }
    }
}

void db_query_print(ObjDB *db, Query *q) {
    if (!db || !q) return;
    if (q->state != QS_DONE) {
        printf("[query] not in DONE state -- run query first\n"); return;
    }
    printf("---------------------------------------\n");
    printf("│  Query Results (%d object(s))\n", q->result_count);
    printf("---------------------------------------\n");
    for (int i = 0; i < q->result_count; i++) {
        int s = q->results[i];
        if (s < 0 || s >= MAX_OBJECTS || !db->objects[s].exists) continue;
        Object *o = &db->objects[s];
        switch (o->type) {
        case OBJ_INT:
            printf("│  %-20s = %lld  (int, v%u)\n",
                   o->key, (long long)o->val.i, o->version);
            break;
        case OBJ_FLOAT:
            printf("│  %-20s = %g  (float, v%u)\n",
                   o->key, o->val.f, o->version);
            break;
        case OBJ_STRING:
            printf("│  %-20s = \"%s\"  (str, v%u)\n",
                   o->key, o->val.s, o->version);
            break;
        default:
            printf("│  %-20s = <unknown type %d>\n", o->key, (int)o->type);
            break;
        }
    }
    printf("---------------------------------------\n");
}

/* Diagnostics */
static const char *type_name(ObjType t) {
    switch (t) {
    case OBJ_INT:    return "int";
    case OBJ_FLOAT:  return "float";
    case OBJ_STRING: return "str";
    case OBJ_NULL:   return "null";
    default:         return "???";
    }
}

void db_dump(ObjDB *db) {
    if (!db) return;
    printf("\n** DB DUMP **\n");
    int shown = 0;
    for (int i = 0; i < MAX_OBJECTS; i++) {
        if (!db->objects[i].exists) continue;
        Object *o = &db->objects[i];
        printf("  [%3d] %-20s (%s, v%u) = ",
               i, o->key, type_name(o->type), o->version);
        switch (o->type) {
        case OBJ_INT:    printf("%lld\n",   (long long)o->val.i); break;
        case OBJ_FLOAT:  printf("%g\n",     o->val.f);            break;
        case OBJ_STRING: printf("\"%s\"\n", o->val.s);            break;
        default:         printf("<type %d>\n", (int)o->type);     break;
        }
        shown++;
    }
    if (!shown) printf("  (empty)\n");
    printf("******************\n\n");
}

void db_dump_frames(ObjDB *db) {
    if (!db) return;
    printf("\n*** FRAME STACK (top=%d) ***\n", db->frame_top);
    for (int i = db->frame_top; i >= 0; i--) {
        Frame *f = &db->frames[i];
        printf("  [%d] '%s'%s  — %d undo entr(ies)\n",
               i, f->label,
               f->is_checkpoint ? " [CHECKPOINT]" : "",
               f->undo_count);
    }
    if (db->frame_top < 0) printf("  (empty)\n");
    printf("*******************\n\n");
}
