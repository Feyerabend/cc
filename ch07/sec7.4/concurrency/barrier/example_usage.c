#include <stdio.h>
#include <stdlib.h>
#include <pthread.h>
#include <unistd.h>

#include "atomic.h"
#include "arena_threadsafe.h"

/*
 * Practical Example: Multi-threaded Token Parser
 * 
 * This example demonstrates how memory barriers enable safe multi-threaded
 * processing in a compiler scenario. Multiple threads parse different sections
 * of input and allocate tokens from a shared arena.
 */

#define NUM_PARSER_THREADS 4
#define TOKENS_PER_SECTION 5000

/* Simulated token */
typedef struct {
    int type;
    char *value;
    int line;
    int column;
} Token;

/* Parser thread data */
typedef struct {
    int thread_id;
    ThreadSafeArena *arena;
    atomic_size_t *total_tokens;
    int start_line;
    int end_line;
} ParserThread;

/* Simulated token types */
enum {
    TOK_IDENT,
    TOK_NUMBER,
    TOK_OPERATOR,
    TOK_KEYWORD,
    TOK_PUNCT
};

const char *token_names[] = {
    "IDENT", "NUMBER", "OPERATOR", "KEYWORD", "PUNCT"
};

/* Simulate parsing a section of code */
void* parser_worker(void *arg) {
    ParserThread *pt = (ParserThread*)arg;
    
    printf("Thread %d: Parsing lines %d-%d\n", 
           pt->thread_id, pt->start_line, pt->end_line);
    
    int tokens_parsed = 0;
    
    for (int line = pt->start_line; line < pt->end_line; line++) {
        for (int col = 0; col < 10; col++) {
            // Allocate token structure from shared arena
            Token *tok = ts_arena_alloc(pt->arena, sizeof(Token));
            if (!tok) {
                fprintf(stderr, "Thread %d: Allocation failed!\n", pt->thread_id);
                return NULL;
            }
            
            // Simulate token data
            tok->type = (line + col) % 5;
            tok->line = line;
            tok->column = col;
            
            // Allocate and set token value
            char buffer[64];
            snprintf(buffer, sizeof(buffer), "token_%d_%d", line, col);
            tok->value = ts_arena_strdup(pt->arena, buffer);
            
            tokens_parsed++;
            
            // Atomically update total count
            atomic_fetch_add_size(pt->total_tokens, 1, memory_order_relaxed);
        }
    }
    
    printf("Thread %d: Parsed %d tokens\n", pt->thread_id, tokens_parsed);
    return NULL;
}

/* Example 1: Multi-threaded parsing */
void example_multithreaded_parsing(void) {
    printf("\n=== Example 1: Multi-threaded Token Parsing ===\n");
    
    // Create shared arena with memory barriers
    ThreadSafeArena *arena = ts_arena_create(16384);
    if (!arena) {
        fprintf(stderr, "Failed to create arena\n");
        return;
    }
    
    // Shared counter for total tokens
    atomic_size_t total_tokens;
    atomic_store_explicit(&total_tokens, 0, memory_order_relaxed);
    
    pthread_t threads[NUM_PARSER_THREADS];
    ParserThread thread_data[NUM_PARSER_THREADS];
    
    // Divide work among threads
    int lines_per_thread = TOKENS_PER_SECTION / NUM_PARSER_THREADS;
    
    // Start parser threads
    for (int i = 0; i < NUM_PARSER_THREADS; i++) {
        thread_data[i].thread_id = i;
        thread_data[i].arena = arena;
        thread_data[i].total_tokens = &total_tokens;
        thread_data[i].start_line = i * lines_per_thread;
        thread_data[i].end_line = (i + 1) * lines_per_thread;
        
        pthread_create(&threads[i], NULL, parser_worker, &thread_data[i]);
    }
    
    // Wait for completion
    for (int i = 0; i < NUM_PARSER_THREADS; i++) {
        pthread_join(threads[i], NULL);
    }
    
    // Read final count (acquire barrier ensures we see all writes)
    size_t final_count = atomic_load_explicit(&total_tokens, memory_order_acquire);
    
    printf("\nResults:\n");
    printf("  Total tokens parsed: %zu\n", final_count);
    printf("  Arena allocated: %zu bytes in %zu blocks\n",
           ts_arena_total_allocated(arena), ts_arena_total_blocks(arena));
    
    ts_arena_destroy(arena);
}

/* Example 2: Producer-Consumer with memory barriers */
typedef struct {
    Token **buffer;
    size_t capacity;
    atomic_size_t write_pos;
    atomic_size_t read_pos;
    atomic_bool shutdown;
} TokenQueue;

void tokenqueue_init(TokenQueue *q, size_t capacity) {
    q->buffer = calloc(capacity, sizeof(Token*));
    q->capacity = capacity;
    atomic_store_explicit(&q->write_pos, 0, memory_order_relaxed);
    atomic_store_explicit(&q->read_pos, 0, memory_order_relaxed);
    atomic_store_explicit(&q->shutdown, false, memory_order_relaxed);
}

bool tokenqueue_push(TokenQueue *q, Token *tok) {
    size_t write = atomic_load_explicit(&q->write_pos, memory_order_relaxed);
    size_t next_write = (write + 1) % q->capacity;
    size_t read = atomic_load_explicit(&q->read_pos, memory_order_acquire);
    
    if (next_write == read) {
        return false; // Queue full
    }
    
    q->buffer[write] = tok;
    
    // Release barrier ensures token is visible before updating write_pos
    atomic_store_explicit(&q->write_pos, next_write, memory_order_release);
    return true;
}

Token* tokenqueue_pop(TokenQueue *q) {
    size_t read = atomic_load_explicit(&q->read_pos, memory_order_relaxed);
    size_t write = atomic_load_explicit(&q->write_pos, memory_order_acquire);
    
    if (read == write) {
        return NULL; // Queue empty
    }
    
    Token *tok = q->buffer[read];
    
    // Release barrier ensures we're done with the token before updating read_pos
    atomic_store_explicit(&q->read_pos, (read + 1) % q->capacity, 
                          memory_order_release);
    return tok;
}

void* producer_thread(void *arg) {
    ParserThread *pt = (ParserThread*)arg;
    TokenQueue *queue = (TokenQueue*)pt->arena; // Reusing field for queue
    ThreadSafeArena *arena = (ThreadSafeArena*)pt->total_tokens; // Reusing field
    
    printf("Producer %d: Starting\n", pt->thread_id);
    
    for (int i = 0; i < 100; i++) {
        Token *tok = ts_arena_alloc(arena, sizeof(Token));
        tok->type = i % 5;
        tok->line = i;
        tok->column = pt->thread_id;
        
        char buffer[32];
        snprintf(buffer, sizeof(buffer), "tok_%d_%d", pt->thread_id, i);
        tok->value = ts_arena_strdup(arena, buffer);
        
        while (!tokenqueue_push(queue, tok)) {
            usleep(100); // Wait if queue full
        }
    }
    
    printf("Producer %d: Done\n", pt->thread_id);
    return NULL;
}

void* consumer_thread(void *arg) {
    ParserThread *pt = (ParserThread*)arg;
    TokenQueue *queue = (TokenQueue*)pt->arena;
    atomic_size_t *consumed = (atomic_size_t*)pt->total_tokens;
    
    printf("Consumer %d: Starting\n", pt->thread_id);
    
    int count = 0;
    while (true) {
        Token *tok = tokenqueue_pop(queue);
        if (tok) {
            // Process token
            count++;
            atomic_fetch_add_size(consumed, 1, memory_order_relaxed);
        } else {
            // Check if shutdown
            if (atomic_load_explicit((atomic_bool*)&queue->shutdown, 
                                     memory_order_acquire)) {
                break;
            }
            usleep(100);
        }
    }
    
    // Drain remaining tokens
    Token *tok;
    while ((tok = tokenqueue_pop(queue)) != NULL) {
        count++;
        atomic_fetch_add_size(consumed, 1, memory_order_relaxed);
    }
    
    printf("Consumer %d: Consumed %d tokens\n", pt->thread_id, count);
    return NULL;
}

void example_producer_consumer(void) {
    printf("\n=== Example 2: Producer-Consumer with Memory Barriers ===\n");
    
    ThreadSafeArena *arena = ts_arena_create(8192);
    TokenQueue queue;
    tokenqueue_init(&queue, 1024);
    
    atomic_size_t consumed;
    atomic_store_explicit(&consumed, 0, memory_order_relaxed);
    
    pthread_t producers[2], consumers[2];
    ParserThread producer_data[2], consumer_data[2];
    
    // Start producers
    for (int i = 0; i < 2; i++) {
        producer_data[i].thread_id = i;
        producer_data[i].arena = (ThreadSafeArena*)&queue; // Hack for demo
        producer_data[i].total_tokens = (atomic_size_t*)arena;
        pthread_create(&producers[i], NULL, producer_thread, &producer_data[i]);
    }
    
    // Start consumers
    for (int i = 0; i < 2; i++) {
        consumer_data[i].thread_id = i;
        consumer_data[i].arena = (ThreadSafeArena*)&queue;
        consumer_data[i].total_tokens = &consumed;
        pthread_create(&consumers[i], NULL, consumer_thread, &consumer_data[i]);
    }
    
    // Wait for producers
    for (int i = 0; i < 2; i++) {
        pthread_join(producers[i], NULL);
    }
    
    // Signal shutdown
    atomic_store_explicit(&queue.shutdown, true, memory_order_release);
    
    // Wait for consumers
    for (int i = 0; i < 2; i++) {
        pthread_join(consumers[i], NULL);
    }
    
    size_t total = atomic_load_explicit(&consumed, memory_order_acquire);
    
    printf("\nResults:\n");
    printf("  Tokens consumed: %zu (expected: 200)\n", total);
    printf("  Arena allocated: %zu bytes\n", ts_arena_total_allocated(arena));
    
    free(queue.buffer);
    ts_arena_destroy(arena);
}

/* Main */
int main(void) {
    printf("\n\n");
    printf("   --> Memory Barriers -- Practical Examples\n\n");
    
    example_multithreaded_parsing();
    example_producer_consumer();
    
    printf("\n\n");
    printf("   --> Done.\n\n");
    
    return EXIT_SUCCESS;
}
