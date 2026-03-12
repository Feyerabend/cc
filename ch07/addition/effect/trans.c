
// Software Transactional Memory

typedef struct {
    char* key;
    int value;
} KVPair;

typedef struct {
    KVPair* pairs;
    int count;
    int capacity;
} TransactionLog;

// 

Effect eff_read(char* key, Continuation* k) {
    Effect e = {.tag = EFF_STATE_GET};
    // Store key in continuation context
    return e;
}

Effect eff_write(char* key, int value, Continuation* k) {
    Effect e = {.tag = EFF_STATE_PUT, .data.put.value = value};
    return e;
}

typedef struct {
    TransactionLog log;
    int aborted;
} STMHandler;

void* handle_stm(Effect eff, STMHandler* handler) {
    Effect current = eff;
    handler->log.pairs = malloc(sizeof(KVPair) * 100);
    handler->log.count = 0;
    handler->log.capacity = 100;
    handler->aborted = 0;
    
    while (current.tag != EFF_RETURN && current.tag != EFF_ERROR) {
        switch (current.tag) {
            case EFF_STATE_GET: {
                // Read from log (snapshot isolation)
                printf("[STM] Read operation\n");
                int value = 42; // Simplified
                current = current.continuation->resume(current.continuation, &value);
                break;
            }
            
            case EFF_STATE_PUT: {
                // Write to log (not committed yet)
                printf("[STM] Write to log: %d\n", current.data.put.value);
                if (handler->log.count < handler->log.capacity) {
                    handler->log.pairs[handler->log.count++] = 
                        (KVPair){"key", current.data.put.value};
                }
                current = current.continuation->resume(current.continuation, NULL);
                break;
            }
            
            default:
                break;
        }
    }
    
    if (current.tag == EFF_ERROR) {
        printf("[STM] Transaction aborted, rolling back %d writes\n", 
               handler->log.count);
        handler->aborted = 1;
        free(handler->log.pairs);
        return NULL;
    }
    
    // Commit: apply all writes atomically
    printf("[STM] Committing %d writes\n", handler->log.count);
    for (int i = 0; i < handler->log.count; i++) {
        printf("  - %s = %d\n", handler->log.pairs[i].key, 
               handler->log.pairs[i].value);
    }
    free(handler->log.pairs);
    
    return current.data.return_val;
}


