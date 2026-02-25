/*
 * toynet.c - Network Stack for ToyOS
 *
 * Adds socket-based networking on top of toyos.c, implementing:
 *   - Socket API (socket, bind, listen, accept, connect, send, recv, close)
 *   - TCP state machine (SYN, SYN-ACK, ACK handshake)
 *   - Virtual network interface (loopback-style in-memory)
 *   - Port management and connection table
 *   - Packet queues using existing message queue infrastructure
 *
 * Network Model:
 *   - Single virtual network (all processes on same "LAN")
 *   - IP addresses are just process IDs (simplified)
 *   - Ports are 16-bit integers
 *   - Packets flow through central packet switch
 *
 * Build:   gcc -Wall -o toynet toynet.c
 * Run:     ./toynet
 *
 * Demonstrates:
 *   - How sockets work at the OS level
 *   - TCP connection establishment (3-way handshake)
 *   - Server/client model
 *   - Blocking I/O with wait queues
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

/* CONFIGURATION */

#define MAX_PROCESSES       16
#define MAX_STACK           64
#define MAX_INSTRUCTIONS    1024
#define MAX_LOCKS           16
#define MAX_SEMAPHORES      16
#define MAX_QUEUES          16
#define MAX_WAIT_QUEUE      16
#define MAX_LOCAL_VARS      32
#define MAX_GLOBALS         32
#define NAME_LEN            32

/* NETWORK CONFIGURATION */
#define MAX_SOCKETS         32
#define MAX_CONNECTIONS     16
#define MAX_LISTEN_BACKLOG  8
#define MAX_PACKET_SIZE     256
#define PACKET_QUEUE_SIZE   32

typedef int Value;

/* OPCODES */

typedef enum {
    OP_PUSH,
    OP_POP,
    OP_DUP,
    OP_ADD, OP_SUB, OP_MUL, OP_DIV, OP_MOD,
    OP_LOAD,
    OP_STORE,
    OP_GLOAD,
    OP_GSTORE,
    OP_JUMP,
    OP_JUMP_IF,
    OP_JUMP_IFNOT,
    OP_EQ, OP_LT, OP_GT,
    OP_PRINT,
    OP_PRINT_STR,
    OP_NOP,
    OP_EXIT,
    OP_SYSCALL,
} Opcode;

/* SYSTEM CALLS */

typedef enum {
    SYS_GETPID,
    SYS_SLEEP,
    SYS_GETTIME,
    /* Network syscalls */
    SYS_SOCKET,      /* () -> socket_fd or -1 */
    SYS_BIND,        /* (socket_fd, port) -> 0 or -1 */
    SYS_LISTEN,      /* (socket_fd, backlog) -> 0 or -1 */
    SYS_ACCEPT,      /* (socket_fd) -> client_fd or -1 (blocks) */
    SYS_CONNECT,     /* (socket_fd, dest_pid, dest_port) -> 0 or -1 (blocks) */
    SYS_SEND,        /* (socket_fd, data) -> bytes sent or -1 */
    SYS_RECV,        /* (socket_fd) -> data or -1 (blocks if no data) */
    SYS_CLOSE_SOCK,  /* (socket_fd) -> 0 or -1 */
} Syscall;

/* TCP STATES */

typedef enum {
    TCP_CLOSED,
    TCP_LISTEN,
    TCP_SYN_SENT,
    TCP_SYN_RECEIVED,
    TCP_ESTABLISHED,
    TCP_FIN_WAIT,
    TCP_CLOSE_WAIT,
    TCP_CLOSED_FINAL,
} TcpState;

/* PACKET TYPES */

typedef enum {
    PKT_SYN,
    PKT_SYN_ACK,
    PKT_ACK,
    PKT_DATA,
    PKT_FIN,
} PacketType;

/* NETWORK PACKET */

typedef struct {
    PacketType type;
    int        src_pid;
    int        src_port;
    int        dst_pid;
    int        dst_port;
    int        data;
    int        conn_id;  /* for matching packets to connections */
} Packet;

/* PACKET QUEUE (circular buffer) */

typedef struct {
    Packet packets[PACKET_QUEUE_SIZE];
    int    head, tail, count;
} PacketQueue;

static void packet_queue_init(PacketQueue *pq) {
    pq->head = pq->tail = pq->count = 0;
}

static int packet_queue_is_empty(PacketQueue *pq) {
    return pq->count == 0;
}

static int packet_queue_is_full(PacketQueue *pq) {
    return pq->count == PACKET_QUEUE_SIZE;
}

static void packet_queue_enqueue(PacketQueue *pq, Packet pkt) {
    if (packet_queue_is_full(pq)) {
        return;  /* drop packet if queue full */
    }
    pq->packets[pq->tail] = pkt;
    pq->tail = (pq->tail + 1) % PACKET_QUEUE_SIZE;
    pq->count++;
}

static Packet packet_queue_dequeue(PacketQueue *pq) {
    assert(!packet_queue_is_empty(pq));
    Packet pkt = pq->packets[pq->head];
    pq->head = (pq->head + 1) % PACKET_QUEUE_SIZE;
    pq->count--;
    return pkt;
}

/* SOCKET */

typedef struct {
    int       id;
    int       process_id;
    int       local_port;
    int       remote_pid;
    int       remote_port;
    TcpState  state;
    int       conn_id;        /* connection identifier */
    
    /* For listening sockets */
    int       backlog;
    int       pending_connections[MAX_LISTEN_BACKLOG];
    int       num_pending;
    
    /* Data buffers */
    PacketQueue recv_queue;
    
    /* Waiting processes */
    int       waiting_for_accept;  /* PID of process blocked on accept() */
    int       waiting_for_recv;    /* PID of process blocked on recv() */
    int       waiting_for_connect; /* PID of process blocked on connect() */
} Socket;

/* WAIT QUEUE */

typedef struct {
    int pids[MAX_WAIT_QUEUE];
    int head, tail, count;
} WaitQueue;

/*
static void wait_queue_init(WaitQueue *wq) {
    wq->head = wq->tail = wq->count = 0;
}

static int wait_queue_is_empty(WaitQueue *wq) {
    return wq->count == 0;
}

static void wait_queue_push(WaitQueue *wq, int pid) {
    assert(wq->count < MAX_WAIT_QUEUE);
    wq->pids[wq->tail] = pid;
    wq->tail = (wq->tail + 1) % MAX_WAIT_QUEUE;
    wq->count++;
}

static int wait_queue_pop(WaitQueue *wq) {
    assert(wq->count > 0);
    int pid = wq->pids[wq->head];
    wq->head = (wq->head + 1) % MAX_WAIT_QUEUE;
    wq->count--;
    return pid;
}
*/

/* INSTRUCTION */

typedef struct {
    Opcode op;
    int    iarg;
    char   sarg[NAME_LEN];
} Instr;

/* PROCESS */

typedef enum {
    PS_RUNNING,
    PS_READY,
    PS_WAITING,
    PS_ZOMBIE,
    PS_TERMINATED,
} ProcessState;

typedef struct {
    int  pid;
    int  parent_pid;
    char name[NAME_LEN];
    
    int   pc;
    Value stack[MAX_STACK];
    int   sp;
    
    char  local_var_names[MAX_LOCAL_VARS][NAME_LEN];
    Value local_var_values[MAX_LOCAL_VARS];
    int   num_local_vars;
    
    Instr instructions[MAX_INSTRUCTIONS];
    int   num_instructions;
    
    ProcessState state;
    int          priority;
    int          wait_resource_id;
    int          exit_code;
    int          ticks_to_sleep;
    
    /* Socket file descriptors */
    int socket_fds[MAX_SOCKETS];  /* maps local fd -> socket id */
} Process;

/* GLOBAL VARIABLES */

typedef struct {
    char name[NAME_LEN];
    Value val;
} Global;

/* OPERATING SYSTEM WITH NETWORK STACK */

typedef struct {
    Process      processes[MAX_PROCESSES];
    int          num_processes;
    int          next_pid;
    
    int          run_queue[MAX_PROCESSES];
    int          run_queue_head;
    int          run_queue_tail;
    int          run_queue_count;
    
    Global       globals[MAX_GLOBALS];
    int          num_globals;
    
    /* Network components */
    Socket       sockets[MAX_SOCKETS];
    int          num_sockets;
    int          next_socket_id;
    int          next_conn_id;
    
    PacketQueue  network_queue;  /* central packet switch */
    
    int          current_tick;
    int          debug;
} OS;

/* HELPER FUNCTIONS */

static void push(Process *p, Value val) {
    assert(p->sp < MAX_STACK - 1);
    p->stack[++p->sp] = val;
}

static Value pop(Process *p) {
    assert(p->sp >= 0);
    return p->stack[p->sp--];
}

static void store_local(Process *p, const char *name, Value val) {
    for (int i = 0; i < p->num_local_vars; i++) {
        if (!strcmp(p->local_var_names[i], name)) {
            p->local_var_values[i] = val;
            return;
        }
    }
    assert(p->num_local_vars < MAX_LOCAL_VARS);
    strcpy(p->local_var_names[p->num_local_vars], name);
    p->local_var_values[p->num_local_vars] = val;
    p->num_local_vars++;
}

static Value load_local(Process *p, const char *name) {
    for (int i = 0; i < p->num_local_vars; i++) {
        if (!strcmp(p->local_var_names[i], name)) {
            return p->local_var_values[i];
        }
    }
    return 0;
}

static void store_global(OS *os, const char *name, Value val) {
    for (int i = 0; i < os->num_globals; i++) {
        if (!strcmp(os->globals[i].name, name)) {
            os->globals[i].val = val;
            return;
        }
    }
    assert(os->num_globals < MAX_GLOBALS);
    strcpy(os->globals[os->num_globals].name, name);
    os->globals[os->num_globals].val = val;
    os->num_globals++;
}

/* RUN QUEUE */

static void enqueue_process(OS *os, int pid) {
    assert(os->run_queue_count < MAX_PROCESSES);
    os->run_queue[os->run_queue_tail] = pid;
    os->run_queue_tail = (os->run_queue_tail + 1) % MAX_PROCESSES;
    os->run_queue_count++;
}

static int dequeue_process(OS *os) {
    assert(os->run_queue_count > 0);
    int pid = os->run_queue[os->run_queue_head];
    os->run_queue_head = (os->run_queue_head + 1) % MAX_PROCESSES;
    os->run_queue_count--;
    return pid;
}

static Process* find_process(OS *os, int pid) {
    for (int i = 0; i < os->num_processes; i++) {
        if (os->processes[i].pid == pid) {
            return &os->processes[i];
        }
    }
    return NULL;
}

/* SOCKET OPERATIONS */

static Socket* find_socket(OS *os, int socket_id) {
    for (int i = 0; i < os->num_sockets; i++) {
        if (os->sockets[i].id == socket_id) {
            return &os->sockets[i];
        }
    }
    return NULL;
}

static Socket* find_listening_socket(OS *os, int port) {
    for (int i = 0; i < os->num_sockets; i++) {
        if (os->sockets[i].state == TCP_LISTEN && 
            os->sockets[i].local_port == port) {
            return &os->sockets[i];
        }
    }
    return NULL;
}

static int allocate_socket_fd(Process *p, int socket_id) {
    for (int fd = 0; fd < MAX_SOCKETS; fd++) {
        if (p->socket_fds[fd] == -1) {
            p->socket_fds[fd] = socket_id;
            return fd;
        }
    }
    return -1;
}

/* PACKET DELIVERY */

static void send_packet(OS *os, Packet pkt) {
    if (os->debug) {
        const char *type_names[] = {"SYN", "SYN-ACK", "ACK", "DATA", "FIN"};
        printf("  [NET] %s: %d:%d -> %d:%d (conn=%d, data=%d)\n",
               type_names[pkt.type],
               pkt.src_pid, pkt.src_port,
               pkt.dst_pid, pkt.dst_port,
               pkt.conn_id, pkt.data);
    }
    packet_queue_enqueue(&os->network_queue, pkt);
}

static void process_network_packets(OS *os) {
    while (!packet_queue_is_empty(&os->network_queue)) {
        Packet pkt = packet_queue_dequeue(&os->network_queue);
        
        /* Find destination socket */
        Socket *dst_sock = NULL;
        
        if (pkt.type == PKT_SYN) {
            /* SYN goes to listening socket on port */
            dst_sock = find_listening_socket(os, pkt.dst_port);
        } else {
            /* Other packets go to established connection */
            for (int i = 0; i < os->num_sockets; i++) {
                Socket *s = &os->sockets[i];
                if (s->conn_id == pkt.conn_id && 
                    s->local_port == pkt.dst_port) {
                    dst_sock = s;
                    break;
                }
            }
        }
        
        if (!dst_sock) {
            if (os->debug) {
                printf("  [NET] Packet dropped - no destination\n");
            }
            continue;
        }
        
        /* Handle packet based on type */
        switch (pkt.type) {
            case PKT_SYN:
                /* Server receives SYN */
                if (dst_sock->state == TCP_LISTEN) {
                    /* Create new socket for this connection */
                    assert(os->num_sockets < MAX_SOCKETS);
                    Socket *new_sock = &os->sockets[os->num_sockets++];
                    new_sock->id = os->next_socket_id++;
                    new_sock->process_id = dst_sock->process_id;
                    new_sock->local_port = dst_sock->local_port;
                    new_sock->remote_pid = pkt.src_pid;
                    new_sock->remote_port = pkt.src_port;
                    new_sock->state = TCP_SYN_RECEIVED;
                    new_sock->conn_id = pkt.conn_id;
                    packet_queue_init(&new_sock->recv_queue);
                    new_sock->waiting_for_accept = -1;
                    new_sock->waiting_for_recv = -1;
                    new_sock->waiting_for_connect = -1;
                    
                    /* Add to listening socket's pending queue */
                    if (dst_sock->num_pending < MAX_LISTEN_BACKLOG) {
                        dst_sock->pending_connections[dst_sock->num_pending++] = new_sock->id;
                    }
                    
                    /* Send SYN-ACK */
                    Packet syn_ack = {
                        .type = PKT_SYN_ACK,
                        .src_pid = new_sock->process_id,
                        .src_port = new_sock->local_port,
                        .dst_pid = pkt.src_pid,
                        .dst_port = pkt.src_port,
                        .conn_id = pkt.conn_id,
                        .data = 0
                    };
                    send_packet(os, syn_ack);
                    
                    /* Wake up accept() if blocked */
                    if (dst_sock->waiting_for_accept > 0) {
                        Process *p = find_process(os, dst_sock->waiting_for_accept);
                        if (p && p->state == PS_WAITING) {
                            /* Replace placeholder return value with actual client fd */
                            int client_fd = allocate_socket_fd(p, new_sock->id);
                            p->stack[p->sp] = client_fd;  /* overwrite the -2 placeholder */
                            
                            p->state = PS_READY;
                            enqueue_process(os, p->pid);
                            dst_sock->waiting_for_accept = -1;
                        }
                    }
                }
                break;
                
            case PKT_SYN_ACK:
                /* Client receives SYN-ACK */
                if (dst_sock->state == TCP_SYN_SENT) {
                    dst_sock->state = TCP_ESTABLISHED;
                    
                    /* Send ACK */
                    Packet ack = {
                        .type = PKT_ACK,
                        .src_pid = dst_sock->process_id,
                        .src_port = dst_sock->local_port,
                        .dst_pid = dst_sock->remote_pid,
                        .dst_port = dst_sock->remote_port,
                        .conn_id = dst_sock->conn_id,
                        .data = 0
                    };
                    send_packet(os, ack);
                    
                    /* Wake up connect() */
                    if (dst_sock->waiting_for_connect > 0) {
                        Process *p = find_process(os, dst_sock->waiting_for_connect);
                        if (p && p->state == PS_WAITING) {
                            p->state = PS_READY;
                            enqueue_process(os, p->pid);
                            dst_sock->waiting_for_connect = -1;
                        }
                    }
                }
                break;
                
            case PKT_ACK:
                /* Server receives ACK - connection established */
                if (dst_sock->state == TCP_SYN_RECEIVED) {
                    dst_sock->state = TCP_ESTABLISHED;
                }
                break;
                
            case PKT_DATA:
                /* Receive data */
                if (dst_sock->state == TCP_ESTABLISHED) {
                    /* Wake up recv() if blocked */
                    if (dst_sock->waiting_for_recv > 0) {
                        Process *p = find_process(os, dst_sock->waiting_for_recv);
                        if (p && p->state == PS_WAITING) {
                            /* Replace placeholder with actual data */
                            p->stack[p->sp] = pkt.data;
                            
                            p->state = PS_READY;
                            enqueue_process(os, p->pid);
                            dst_sock->waiting_for_recv = -1;
                            
                            if (os->debug) {
                                printf("  [RECV] Socket %d delivered data: %d\n", 
                                       dst_sock->id, pkt.data);
                            }
                        }
                    } else {
                        /* No one waiting - queue it */
                        packet_queue_enqueue(&dst_sock->recv_queue, pkt);
                    }
                }
                break;
                
            case PKT_FIN:
                /* Connection close */
                dst_sock->state = TCP_CLOSE_WAIT;
                break;
        }
    }
}

/* INSTRUCTION CONSTRUCTORS */

static Instr instr_push(int val) {
    Instr i = {OP_PUSH, val, ""};
    return i;
}

static Instr instr_pop(void) {
    Instr i = {OP_POP, 0, ""};
    return i;
}

static Instr instr_add(void) {
    Instr i = {OP_ADD, 0, ""};
    return i;
}

/*
static Instr instr_sub(void) {
    Instr i = {OP_SUB, 0, ""};
    return i;
}
*/

static Instr instr_load(const char *name) {
    Instr i = {OP_LOAD, 0, ""};
    strncpy(i.sarg, name, NAME_LEN - 1);
    return i;
}

static Instr instr_store(const char *name) {
    Instr i = {OP_STORE, 0, ""};
    strncpy(i.sarg, name, NAME_LEN - 1);
    return i;
}

/*
static Instr instr_global_store(const char *name) {
    Instr i = {OP_GSTORE, 0, ""};
    strncpy(i.sarg, name, NAME_LEN - 1);
    return i;
}
*/

static Instr instr_jump(int addr) {
    Instr i = {OP_JUMP, addr, ""};
    return i;
}

static Instr instr_jump_ifnot(int addr) {
    Instr i = {OP_JUMP_IFNOT, addr, ""};
    return i;
}

/*
static Instr instr_eq(void) {
    Instr i = {OP_EQ, 0, ""};
    return i;
}
*/

static Instr instr_lt(void) {
    Instr i = {OP_LT, 0, ""};
    return i;
}

static Instr instr_print(void) {
    Instr i = {OP_PRINT, 0, ""};
    return i;
}

static Instr instr_print_str(const char *str) {
    Instr i = {OP_PRINT_STR, 0, ""};
    strncpy(i.sarg, str, NAME_LEN - 1);
    return i;
}

static Instr instr_exit(void) {
    Instr i = {OP_EXIT, 0, ""};
    return i;
}

static Instr instr_syscall(int syscall_num) {
    Instr i = {OP_SYSCALL, syscall_num, ""};
    return i;
}

/* SYSTEM CALLS */

static void syscall_getpid(OS *os, Process *p) {
    (void)os;
    push(p, p->pid);
}

static void syscall_socket(OS *os, Process *p) {
    assert(os->num_sockets < MAX_SOCKETS);
    
    Socket *sock = &os->sockets[os->num_sockets++];
    sock->id = os->next_socket_id++;
    sock->process_id = p->pid;
    sock->local_port = -1;
    sock->remote_pid = -1;
    sock->remote_port = -1;
    sock->state = TCP_CLOSED;
    sock->conn_id = -1;
    sock->backlog = 0;
    sock->num_pending = 0;
    packet_queue_init(&sock->recv_queue);
    sock->waiting_for_accept = -1;
    sock->waiting_for_recv = -1;
    sock->waiting_for_connect = -1;
    
    int fd = allocate_socket_fd(p, sock->id);
    
    if (os->debug) {
        printf("  [SOCKET] Process %d created socket %d (fd=%d)\n", 
               p->pid, sock->id, fd);
    }
    
    push(p, fd);
}

static void syscall_bind(OS *os, Process *p) {
    int port = pop(p);
    int fd = pop(p);
    
    if (fd < 0 || fd >= MAX_SOCKETS || p->socket_fds[fd] == -1) {
        push(p, -1);
        return;
    }
    
    Socket *sock = find_socket(os, p->socket_fds[fd]);
    if (!sock) {
        push(p, -1);
        return;
    }
    
    sock->local_port = port;
    
    if (os->debug) {
        printf("  [BIND] Socket %d bound to port %d\n", sock->id, port);
    }
    
    push(p, 0);
}

static void syscall_listen(OS *os, Process *p) {
    int backlog = pop(p);
    int fd = pop(p);
    
    if (fd < 0 || fd >= MAX_SOCKETS || p->socket_fds[fd] == -1) {
        push(p, -1);
        return;
    }
    
    Socket *sock = find_socket(os, p->socket_fds[fd]);
    if (!sock) {
        push(p, -1);
        return;
    }
    
    sock->state = TCP_LISTEN;
    sock->backlog = backlog;
    
    if (os->debug) {
        printf("  [LISTEN] Socket %d listening on port %d\n", 
               sock->id, sock->local_port);
    }
    
    push(p, 0);
}

static void syscall_accept(OS *os, Process *p) {
    int fd = pop(p);
    
    if (fd < 0 || fd >= MAX_SOCKETS || p->socket_fds[fd] == -1) {
        push(p, -1);
        return;
    }
    
    Socket *sock = find_socket(os, p->socket_fds[fd]);
    if (!sock || sock->state != TCP_LISTEN) {
        push(p, -1);
        return;
    }
    
    /* Check if there are pending connections */
    if (sock->num_pending > 0) {
        /* Accept the first pending connection */
        int conn_socket_id = sock->pending_connections[0];
        
        /* Remove from pending queue */
        for (int i = 0; i < sock->num_pending - 1; i++) {
            sock->pending_connections[i] = sock->pending_connections[i + 1];
        }
        sock->num_pending--;
        
        /* Allocate fd for the new connection socket */
        int client_fd = allocate_socket_fd(p, conn_socket_id);
        
        if (os->debug) {
            printf("  [ACCEPT] Socket %d accepted connection (client_fd=%d)\n",
                   sock->id, client_fd);
        }
        
        push(p, client_fd);

    } else {
        /* Block until a connection arrives */
        /* Push placeholder - will be overwritten when connection accepted */
        push(p, -2);  /* temporary marker */
        sock->waiting_for_accept = p->pid;
        p->state = PS_WAITING;
        
        if (os->debug) {
            printf("  [ACCEPT] Process %d blocked waiting for connection\n", p->pid);
        }
    }
}

static void syscall_connect(OS *os, Process *p) {
    int dst_port = pop(p);
    int dst_pid = pop(p);
    int fd = pop(p);
    
    if (fd < 0 || fd >= MAX_SOCKETS || p->socket_fds[fd] == -1) {
        push(p, -1);
        return;
    }
    
    Socket *sock = find_socket(os, p->socket_fds[fd]);
    if (!sock) {
        push(p, -1);
        return;
    }
    
    /* Set up connection */
    sock->remote_pid = dst_pid;
    sock->remote_port = dst_port;
    sock->state = TCP_SYN_SENT;
    sock->conn_id = os->next_conn_id++;
    
    /* Send SYN packet */
    Packet syn = {
        .type = PKT_SYN,
        .src_pid = p->pid,
        .src_port = sock->local_port,
        .dst_pid = dst_pid,
        .dst_port = dst_port,
        .conn_id = sock->conn_id,
        .data = 0
    };
    send_packet(os, syn);
    
    /* Block until connection established */
    /* Push return value now - will be there when we resume */
    push(p, 0);
    
    sock->waiting_for_connect = p->pid;
    p->state = PS_WAITING;
    
    if (os->debug) {
        printf("  [CONNECT] Socket %d connecting to %d:%d\n",
               sock->id, dst_pid, dst_port);
    }
}

static void syscall_send(OS *os, Process *p) {
    int data = pop(p);
    int fd = pop(p);
    
    if (fd < 0 || fd >= MAX_SOCKETS || p->socket_fds[fd] == -1) {
        push(p, -1);
        return;
    }
    
    Socket *sock = find_socket(os, p->socket_fds[fd]);
    if (!sock || sock->state != TCP_ESTABLISHED) {
        push(p, -1);
        return;
    }
    
    /* Send data packet */
    Packet pkt = {
        .type = PKT_DATA,
        .src_pid = sock->process_id,
        .src_port = sock->local_port,
        .dst_pid = sock->remote_pid,
        .dst_port = sock->remote_port,
        .conn_id = sock->conn_id,
        .data = data
    };
    send_packet(os, pkt);
    
    if (os->debug) {
        printf("  [SEND] Socket %d sent data: %d\n", sock->id, data);
    }
    
    push(p, 1);  /* bytes sent */
}

static void syscall_recv(OS *os, Process *p) {
    int fd = pop(p);
    
    if (fd < 0 || fd >= MAX_SOCKETS || p->socket_fds[fd] == -1) {
        push(p, -1);
        return;
    }
    
    Socket *sock = find_socket(os, p->socket_fds[fd]);
    if (!sock || sock->state != TCP_ESTABLISHED) {
        push(p, -1);
        return;
    }
    
    /* Check if data available */
    if (!packet_queue_is_empty(&sock->recv_queue)) {
        Packet pkt = packet_queue_dequeue(&sock->recv_queue);
        
        if (os->debug) {
            printf("  [RECV] Socket %d received data: %d\n", sock->id, pkt.data);
        }
        
        push(p, pkt.data);
    } else {
        /* Block until data arrives */
        push(p, -2);  /* placeholder */
        sock->waiting_for_recv = p->pid;
        p->state = PS_WAITING;
        
        if (os->debug) {
            printf("  [RECV] Process %d blocked waiting for data\n", p->pid);
        }
    }
}

static void syscall_close_sock(OS *os, Process *p) {
    int fd = pop(p);
    
    if (fd < 0 || fd >= MAX_SOCKETS || p->socket_fds[fd] == -1) {
        push(p, -1);
        return;
    }
    
    Socket *sock = find_socket(os, p->socket_fds[fd]);
    if (sock) {
        sock->state = TCP_CLOSED_FINAL;
        if (os->debug) {
            printf("  [CLOSE] Socket %d closed\n", sock->id);
        }
    }
    
    p->socket_fds[fd] = -1;
    push(p, 0);
}

static void syscall_sleep(OS *os, Process *p) {
    int ticks = pop(p);
    p->ticks_to_sleep = ticks;
    p->state = PS_WAITING;
    
    if (os->debug) {
        printf("  [SLEEP] Process %d sleeping for %d ticks\n", p->pid, ticks);
    }
}

static void syscall_gettime(OS *os, Process *p) {
    push(p, os->current_tick);
}

/* EXECUTE INSTRUCTION */

static int execute_instruction(OS *os, Process *p) {
    if (p->pc >= p->num_instructions) {
        return 0;
    }
    
    Instr instr = p->instructions[p->pc];
    p->pc++;
    
    switch (instr.op) {
        case OP_PUSH:
            push(p, instr.iarg);
            break;
        case OP_POP:
            pop(p);
            break;
        case OP_ADD: {
            Value b = pop(p);
            Value a = pop(p);
            push(p, a + b);
            break;
        }
        case OP_SUB: {
            Value b = pop(p);
            Value a = pop(p);
            push(p, a - b);
            break;
        }
        case OP_LOAD:
            push(p, load_local(p, instr.sarg));
            break;
        case OP_STORE:
            store_local(p, instr.sarg, pop(p));
            break;
        case OP_GSTORE:
            store_global(os, instr.sarg, pop(p));
            break;
        case OP_JUMP:
            p->pc = instr.iarg;
            break;
        case OP_JUMP_IFNOT:
            if (!pop(p)) {
                p->pc = instr.iarg;
            }
            break;
        case OP_EQ: {
            Value b = pop(p);
            Value a = pop(p);
            push(p, a == b);
            break;
        }
        case OP_LT: {
            Value b = pop(p);
            Value a = pop(p);
            push(p, a < b);
            break;
        }
        case OP_PRINT:
            printf("%d\n", pop(p));
            break;
        case OP_PRINT_STR:
            printf("%s\n", instr.sarg);
            break;
        case OP_EXIT:
            return 0;
        case OP_SYSCALL:
            switch (instr.iarg) {
                case SYS_GETPID:
                    syscall_getpid(os, p);
                    break;
                case SYS_SOCKET:
                    syscall_socket(os, p);
                    break;
                case SYS_BIND:
                    syscall_bind(os, p);
                    break;
                case SYS_LISTEN:
                    syscall_listen(os, p);
                    break;
                case SYS_ACCEPT:
                    syscall_accept(os, p);
                    return 1;  /* may have blocked */
                case SYS_CONNECT:
                    syscall_connect(os, p);
                    return 1;  /* blocks */
                case SYS_SEND:
                    syscall_send(os, p);
                    break;
                case SYS_RECV:
                    syscall_recv(os, p);
                    return 1;  /* may have blocked */
                case SYS_CLOSE_SOCK:
                    syscall_close_sock(os, p);
                    break;
                case SYS_SLEEP:
                    syscall_sleep(os, p);
                    return 1;
                case SYS_GETTIME:
                    syscall_gettime(os, p);
                    break;
                default:
                    fprintf(stderr, "ERROR: unknown syscall %d\n", instr.iarg);
            }
            break;
        default:
            fprintf(stderr, "ERROR: unknown opcode %d\n", instr.op);
            return 0;
    }
    
    return 1;
}

/* OS INIT */

static void os_init(OS *os, int debug) {
    memset(os, 0, sizeof(OS));
    os->next_pid = 1;
    os->next_socket_id = 1;
    os->next_conn_id = 1000;
    os->debug = debug;
    os->current_tick = 0;
    packet_queue_init(&os->network_queue);
    
    for (int i = 0; i < MAX_PROCESSES; i++) {
        for (int fd = 0; fd < MAX_SOCKETS; fd++) {
            os->processes[i].socket_fds[fd] = -1;
        }
    }
}

/* PROCESS CREATION */

static int create_process(OS *os, const char *name, Instr *instructions,
                         int num_instructions, int priority, int parent_pid) {
    assert(os->num_processes < MAX_PROCESSES);
    
    int pid = os->next_pid++;
    Process *p = &os->processes[os->num_processes++];
    
    p->pid = pid;
    p->parent_pid = parent_pid;
    strncpy(p->name, name, NAME_LEN - 1);
    p->pc = 0;
    p->sp = -1;
    p->num_local_vars = 0;
    p->state = PS_READY;
    p->priority = priority;
    p->wait_resource_id = -1;
    p->exit_code = 0;
    p->ticks_to_sleep = 0;
    
    assert(num_instructions < MAX_INSTRUCTIONS);
    memcpy(p->instructions, instructions, num_instructions * sizeof(Instr));
    p->num_instructions = num_instructions;
    
    for (int fd = 0; fd < MAX_SOCKETS; fd++) {
        p->socket_fds[fd] = -1;
    }
    
    enqueue_process(os, pid);
    
    if (os->debug) {
        printf("  [OS] Created process %d (%s)\n", pid, name);
    }
    
    return pid;
}

/* SCHEDULER */

static void run(OS *os, int max_steps) {
    int steps = 0;
    
    while (steps < max_steps) {
        os->current_tick++;
        
        /* Process network packets */
        process_network_packets(os);
        
        /* Wake up sleeping processes */
        for (int i = 0; i < os->num_processes; i++) {
            Process *p = &os->processes[i];
            if (p->state == PS_WAITING && p->ticks_to_sleep > 0) {
                p->ticks_to_sleep--;
                if (p->ticks_to_sleep == 0) {
                    p->state = PS_READY;
                    enqueue_process(os, p->pid);
                }
            }
        }
        
        /* Check if we have any work to do */
        if (os->run_queue_count == 0) {
            /* Check if all processes are terminated */
            int any_active = 0;
            for (int i = 0; i < os->num_processes; i++) {
                if (os->processes[i].state != PS_ZOMBIE && 
                    os->processes[i].state != PS_TERMINATED) {
                    any_active = 1;
                    break;
                }
            }
            if (!any_active) {
                break;  /* all processes done */
            }
            /* Processes are waiting - continue to process packets */
            continue;
        }
        
        int pid = dequeue_process(os);
        Process *current = find_process(os, pid);
        
        if (!current || current->state != PS_READY) {
            continue;
        }
        
        current->state = PS_RUNNING;
        
        int continue_running = execute_instruction(os, current);
        
        steps++;
        
        if (!continue_running || current->pc >= current->num_instructions) {
            current->state = PS_ZOMBIE;
            if (os->debug) {
                printf("  [EXIT] Process %d terminated\n", pid);
            }
        } else if (current->state == PS_RUNNING) {
            current->state = PS_READY;
            enqueue_process(os, pid);
        }
    }
}

/* DEMO: HTTP-LIKE REQUEST/RESPONSE */

static void demo_http_server(void) {
    printf("\nDEMO: Simple HTTP-like Server\n\n");
    printf("Server listens on port 80.\n");
    printf("Client connects and sends request number.\n");
    printf("Server responds with request * 10.\n\n");
    
    OS os;
    os_init(&os, 1);
    
    /*
     * SERVER:
     *  0  SYSCALL SYS_SOCKET
     *  1  STORE "server_sock"
     *  2  LOAD "server_sock"
     *  3  PUSH 80              port
     *  4  SYSCALL SYS_BIND
     *  5  POP
     *  6  LOAD "server_sock"
     *  7  PUSH 5               backlog
     *  8  SYSCALL SYS_LISTEN
     *  9  POP
     * 10  PRINT_STR "Server listening on port 80"
     * 
     * Loop:
     * 11  LOAD "server_sock"
     * 12  SYSCALL SYS_ACCEPT   (blocks)
     * 13  STORE "client_sock"
     * 14  PRINT_STR "Client connected"
     * 15  LOAD "client_sock"
     * 16  SYSCALL SYS_RECV     (blocks)
     * 17  STORE "request"
     * 18  LOAD "request"
     * 19  PRINT                print request
     * 20  LOAD "client_sock"
     * 21  LOAD "request"
     * 22  PUSH 10
     * 23  ADD                  response = request * 10
     * 24  SYSCALL SYS_SEND
     * 25  POP
     * 26  LOAD "client_sock"
     * 27  SYSCALL SYS_CLOSE_SOCK
     * 28  POP
     * 29  JMP 11              handle next connection
     * 30  EXIT
     */
    
    Instr server_program[] = {
        instr_syscall(SYS_SOCKET),
        instr_store("server_sock"),
        instr_load("server_sock"),
        instr_push(80),
        instr_syscall(SYS_BIND),
        instr_pop(),
        instr_load("server_sock"),
        instr_push(5),
        instr_syscall(SYS_LISTEN),
        instr_pop(),
        instr_print_str("Server listening on port 80"),
        /* Accept loop */
        instr_load("server_sock"),
        instr_syscall(SYS_ACCEPT),
        instr_store("client_sock"),
        instr_print_str("Client connected"),
        instr_load("client_sock"),
        instr_syscall(SYS_RECV),
        instr_store("request"),
        instr_load("request"),
        instr_print(),
        instr_load("client_sock"),
        instr_load("request"),
        instr_push(10),
        instr_add(),
        instr_syscall(SYS_SEND),
        instr_pop(),
        instr_load("client_sock"),
        instr_syscall(SYS_CLOSE_SOCK),
        instr_pop(),
        instr_jump(11),
        instr_exit(),
    };
    
    /*
     * CLIENT:
     *  0  PUSH 2               sleep to let server start
     *  1  SYSCALL SYS_SLEEP
     *  2  PUSH 0               loop counter
     *  3  STORE "i"
     *  
     * Loop (send 3 requests):
     *  4  LOAD "i"
     *  5  PUSH 3
     *  6  LT
     *  7  JIFNOT 29           exit when i >= 3
     *  
     *  8  SYSCALL SYS_SOCKET
     *  9  STORE "sock"
     * 10  LOAD "sock"
     * 11  PUSH 12345           local port (arbitrary)
     * 12  SYSCALL SYS_BIND
     * 13  POP
     * 14  LOAD "sock"
     * 15  PUSH 1               server PID
     * 16  PUSH 80              server port
     * 17  SYSCALL SYS_CONNECT  (blocks)
     * 18  PRINT_STR "Connected to server"
     * 19  LOAD "sock"
     * 20  LOAD "i"             send request = i
     * 21  SYSCALL SYS_SEND
     * 22  POP
     * 23  LOAD "sock"
     * 24  SYSCALL SYS_RECV     (blocks)
     * 25  PRINT                print response
     * 26  LOAD "sock"
     * 27  SYSCALL SYS_CLOSE_SOCK
     * 28  POP
     * 29  LOAD "i"
     * 30  PUSH 1
     * 31  ADD
     * 32  STORE "i"
     * 33  JMP 4
     * 34  EXIT
     */
    
    Instr client_program[] = {
        instr_push(2),
        instr_syscall(SYS_SLEEP),
        instr_push(0),
        instr_store("i"),
        /* Loop */
        instr_load("i"),
        instr_push(3),
        instr_lt(),
        instr_jump_ifnot(34),
        
        instr_syscall(SYS_SOCKET),
        instr_store("sock"),
        instr_load("sock"),
        instr_push(12345),
        instr_syscall(SYS_BIND),
        instr_pop(),
        instr_load("sock"),
        instr_push(1),  /* server PID */
        instr_push(80),
        instr_syscall(SYS_CONNECT),
        instr_pop(),  /* pop return value from connect */
        instr_print_str("Connected to server"),
        instr_load("sock"),
        instr_load("i"),
        instr_syscall(SYS_SEND),
        instr_pop(),
        instr_load("sock"),
        instr_syscall(SYS_RECV),
        instr_print(),
        instr_load("sock"),
        instr_syscall(SYS_CLOSE_SOCK),
        instr_pop(),
        
        instr_load("i"),
        instr_push(1),
        instr_add(),
        instr_store("i"),
        instr_jump(4),
        instr_exit(),
    };
    
    create_process(&os, "server", server_program, sizeof(server_program) / sizeof(server_program[0]), 0, 0);
    create_process(&os, "client", client_program, sizeof(client_program) / sizeof(client_program[0]), 0, 0);
    
    run(&os, 5000);
    
    printf("\nDemo complete.\n");
}

/* MAIN */

int main(void) {
    printf("\n\n");
    printf("  / toynet.c - Network Stack for ToyOS\n\n");
    printf("    Features:\n");
    printf("    - Socket API (socket, bind, listen, accept...)\n");
    printf("    - TCP state machine (3-way handshake)\n");
    printf("    - Virtual packet switching\n");
    printf("    - Blocking I/O with wait queues\n\n");
    
    demo_http_server();
    
    printf("\n");
    return 0;
}
