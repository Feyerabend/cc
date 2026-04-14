/*
 * conn.c - State Machine pattern in C
 *
 * A minimal connection lifecycle demonstrating the function pointer
 * table approach to state machines.
 *
 * States:  IDLE -> CONNECTING -> CONNECTED -> CLOSING -> CLOSED
 * Events:  connect, ready, data, close, error
 *
 * Build:  cc -std=c11 -Wall -Wextra -o conn conn.c
 */

#include <stdio.h>

/*
 *  State and event enumerations
 */

typedef enum {
    ST_IDLE,
    ST_CONNECTING,
    ST_CONNECTED,
    ST_CLOSING,
    ST_CLOSED,
    NUM_STATES
} State;

typedef enum {
    EV_CONNECT,   /* caller requests connection        */
    EV_READY,     /* remote acknowledged               */
    EV_DATA,      /* data arrived                      */
    EV_CLOSE,     /* caller requests graceful shutdown */
    EV_ERROR,     /* unrecoverable fault               */
    NUM_EVENTS
} Event;

static const char *state_name[] = {
    "IDLE", "CONNECTING", "CONNECTED", "CLOSING", "CLOSED"
};

static const char *event_name[] = {
    "connect", "ready", "data", "close", "error"
};


/*
 * Connection context - passed to every handler
 */

typedef struct {
    int bytes_received;
    int error_count;
} Conn;


/*
 * Handler type: receives context, returns next state
 */

typedef State (*Handler)(Conn *);


/* 
 * Concrete handlers - one per meaningful (state, event) pair
 */

static State on_idle_connect(Conn *c) {
    (void)c;
    printf("  opening socket, sending SYN\n");
    return ST_CONNECTING;
}

static State on_connecting_ready(Conn *c) {
    (void)c;
    printf("  SYN-ACK received - connection established\n");
    return ST_CONNECTED;
}

static State on_connecting_error(Conn *c) {
    c->error_count++;
    printf("  handshake failed (errors: %d)\n", c->error_count);
    return ST_CLOSED;
}

static State on_connected_data(Conn *c) {
    c->bytes_received += 64;
    printf("  received 64 bytes (%d total)\n", c->bytes_received);
    return ST_CONNECTED;
}

static State on_connected_close(Conn *c) {
    (void)c;
    printf("  sending FIN, draining\n");
    return ST_CLOSING;
}

static State on_connected_error(Conn *c) {
    c->error_count++;
    printf("  connection reset (errors: %d) - forcing close\n", c->error_count);
    return ST_CLOSING;
}

static State on_closing_ready(Conn *c) {
    (void)c;
    printf("  FIN-ACK received - connection closed\n");
    return ST_CLOSED;
}

static State on_closing_error(Conn *c) {
    c->error_count++;
    printf("  error during close (errors: %d) - abandoning\n", c->error_count);
    return ST_CLOSED;
}


/*
 * Transition table: table[state][event]
 *
 * NULL means the event is not valid in that state.
 * The dispatch function handles NULL without touching the handlers.
 */

static const Handler table[NUM_STATES][NUM_EVENTS] = {
/*                  connect          ready                  data                 close                error              */
/* IDLE        */ { on_idle_connect, NULL,                  NULL,                NULL,                NULL                },
/* CONNECTING  */ { NULL,            on_connecting_ready,   NULL,                NULL,                on_connecting_error },
/* CONNECTED   */ { NULL,            NULL,                  on_connected_data,   on_connected_close,  on_connected_error  },
/* CLOSING     */ { NULL,            on_closing_ready,      NULL,                NULL,                on_closing_error    },
/* CLOSED      */ { NULL,            NULL,                  NULL,                NULL,                NULL                },
};


/*
 * Dispatch - the only function that knows about the table
 */

static State dispatch(State current, Event ev, Conn *conn) {
    Handler h = table[current][ev];
    if (h == NULL) {
        printf("  [ignored] event '%s' is not valid in state %s\n",
               event_name[ev], state_name[current]);
        return current;
    }
    return h(conn);
}


/*
 * Scenario runner
 */

static void run(const char *label, const Event *events, int n) {
    printf("\n=== %s ===\n", label);
    Conn conn = { .bytes_received = 0, .error_count = 0 };
    State s = ST_IDLE;

    for (int i = 0; i < n; i++) {
        printf("[%s] + %s\n", state_name[s], event_name[events[i]]);
        s = dispatch(s, events[i], &conn);
    }
    printf("[%s] done\n", state_name[s]);
}

int main(void) {
    /* Happy path */
    {
        const Event seq[] = {
            EV_CONNECT, EV_READY, EV_DATA, EV_DATA, EV_CLOSE, EV_READY
        };
        run("happy path", seq, 6);
    }

    /* Error mid-connection */
    {
        const Event seq[] = {
            EV_CONNECT, EV_READY, EV_DATA, EV_ERROR, EV_READY
        };
        run("error mid-connection", seq, 5);
    }

    /* Illegal event - data before connected */
    {
        const Event seq[] = {
            EV_CONNECT, EV_DATA
        };
        run("illegal event", seq, 2);
    }

    /* Handshake failure */
    {
        const Event seq[] = {
            EV_CONNECT, EV_ERROR
        };
        run("handshake failure", seq, 2);
    }

    return 0;
}
