#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "effects.h"



typedef struct {
    char* key;
    int value;
} KVPair;



typedef struct {
    KVPair* pairs;
    int count;
    int capacity;
} TransactionLog;



typedef struct {
    int step;
} TxContext;



/* -----------------------------
   Effect constructors
----------------------------- */

Effect eff_read(char* key, Continuation* k)
{
    Effect e = {
        .tag = EFF_STATE_GET,
        .data.get.key = key,
        .continuation = k
    };
    return e;
}



Effect eff_write(char* key, int value, Continuation* k)
{
    Effect e = {
        .tag = EFF_STATE_PUT,
        .data.put.key = key,
        .data.put.value = value,
        .continuation = k
    };
    return e;
}



/* -----------------------------
   Transaction program
----------------------------- */

Effect tx_resume(Continuation* k, void* value)
{
    TxContext* ctx = k->context;

    switch(ctx->step)
    {

        case 0:
            ctx->step = 1;
            return eff_write("x",10,k);

        case 1:
            ctx->step = 2;
            return eff_write("y",20,k);

        case 2:
            ctx->step = 3;
            return eff_read("x",k);

        case 3:
        {
            int read_value = *(int*)value;

            printf("Program read x = %d\n",read_value);

            int* result = malloc(sizeof(int));
            *result = read_value;

            return eff_return(result);
        }

        default:
            return eff_error("invalid step");
    }
}



/* -----------------------------
   STM Handler
----------------------------- */

typedef struct {
    TransactionLog log;
    int aborted;
} STMHandler;



int lookup(TransactionLog* log, char* key)
{
    for(int i=log->count-1;i>=0;i--)
        if(strcmp(log->pairs[i].key,key)==0)
            return log->pairs[i].value;

    return 0;
}



void* handle_stm(Effect eff, STMHandler* handler)
{
    Effect current = eff;

    handler->log.capacity = 100;
    handler->log.count = 0;
    handler->log.pairs = malloc(sizeof(KVPair)*handler->log.capacity);

    handler->aborted = 0;

    while(current.tag != EFF_RETURN && current.tag != EFF_ERROR)
    {

        switch(current.tag)
        {

            case EFF_STATE_GET:
            {
                char* key = current.data.get.key;

                int value = lookup(&handler->log,key);

                printf("[STM] read %s -> %d\n",key,value);

                current =
                    current.continuation->resume(
                        current.continuation,
                        &value
                    );

                break;
            }


            case EFF_STATE_PUT:
            {
                char* key = current.data.put.key;
                int value = current.data.put.value;

                printf("[STM] log write %s = %d\n",key,value);

                if(handler->log.count < handler->log.capacity)
                {
                    handler->log.pairs[handler->log.count++] =
                        (KVPair){key,value};
                }

                current =
                    current.continuation->resume(
                        current.continuation,
                        NULL
                    );

                break;
            }


            default:
                printf("Unknown effect\n");
                exit(1);
        }
    }


    if(current.tag == EFF_ERROR)
    {
        printf("[STM] aborting transaction\n");

        handler->aborted = 1;

        free(handler->log.pairs);

        return NULL;
    }


    printf("[STM] commit %d writes\n",handler->log.count);

    for(int i=0;i<handler->log.count;i++)
    {
        printf("  %s = %d\n",
            handler->log.pairs[i].key,
            handler->log.pairs[i].value);
    }

    void* result = current.data.return_val;

    free(handler->log.pairs);

    return result;
}



/* -----------------------------
   main
----------------------------- */

int main()
{
    STMHandler handler;

    TxContext* ctx = malloc(sizeof(TxContext));
    ctx->step = 0;

    Continuation k = {
        .resume = tx_resume,
        .context = ctx,
        .parent = NULL
    };

    Effect eff = k.resume(&k,NULL);

    int* result = handle_stm(eff,&handler);

    if(result)
    {
        printf("Transaction returned %d\n",*result);
        free(result);
    }

    free(ctx);

    return 0;
}