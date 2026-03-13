/*
 * ADVANCED LINEAR LOGIC: TENSOR PRODUCTS & PROOF NETS
 *
 * 
 * This demonstrates:
 * 1. TENSOR PRODUCT (A ⊗ B) - parallel composition of resources
 * 2. PROOF NETS - graphical representation of linear logic proofs
 * 3. SESSION TYPE CHOREOGRAPHY - multiple concurrent protocols
 * 4. CUT ELIMINATION - proof normalization as computation
 * 
 * TENSOR vs WITH vs PLUS:
 * -----------------------
 * A ⊗ B (TENSOR):  "I have both A and B available simultaneously"
 *                  Both resources exist in parallel
 *                  Must be consumed together
 * 
 * A & B (WITH):    "I can give you A or B, you pick"
 *                  Environment chooses which
 *                  The unchosen one disappears
 * 
 * A ⊕ B (PLUS):    "I give you A or B, I pick"
 *                  System chooses which
 *                  Cannot backtrack
 * 
 * PROOF NETS:
 * -----------
 * Proof nets are graphs where:
 * - Formulas are vertices
 * - Connectives are edges with specific wiring rules
 * - Cuts represent communication channels
 * - Cut elimination is graph rewriting
 * 
 * Example proof net for (A ⊗ B) ⊸ (B ⊗ A):
 * 
 *     A────⊗────┐
 *     │         │
 *     │    B────┘
 *     │         
 *     └────⊗────B
 *          │    
 *     A────┘
 * 
 * SESSION TYPES:
 * --------------
 * We implement a PARALLEL VENDOR protocol:
 * 
 *   VendorA: !Coin ⊸ Apple
 *   VendorB: !Coin ⊸ Banana
 *   Parallel: (VendorA ⊗ VendorB)
 * 
 * This is a tensor product of two independent sessions running in parallel.
 * Each vendor operates independently but both must complete.
 * 
 * CUT ELIMINATION:
 * ----------------
 * When we connect a producer (A) to a consumer (A⊥), we get a CUT.
 * Cut elimination removes this intermediary, directly connecting them.
 * This is the computational content of the proof!
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "pico/stdlib.h"
#include "display.h"
#include "font.h"


// PROOF NET REPRESENTATION

typedef enum {
    NODE_FORMULA,      // Leaf: actual formula (A, B, etc.)
    NODE_TENSOR,       // ⊗
    NODE_PAR,          // ⅋
    NODE_WITH,         // &
    NODE_PLUS,         // ⊕
    NODE_LOLLIPOP,     // ⊸
    NODE_BANG,         // !
    NODE_WHYNOT,       // ?
    NODE_CUT           // Communication channel
} node_type_t;

typedef struct proof_node {
    node_type_t type;
    char label[16];
    int x, y;                          // Screen position
    struct proof_node *left, *right;   // Children
    struct proof_node *dual;           // For cuts: points to dual node
    bool highlighted;
    uint16_t color;
} proof_node_t;

#define MAX_PROOF_NODES 64
static proof_node_t proof_nodes[MAX_PROOF_NODES];
static int proof_node_count = 0;

proof_node_t* create_proof_node(node_type_t type, const char *label) {
    if (proof_node_count >= MAX_PROOF_NODES) return NULL;
    
    proof_node_t *node = &proof_nodes[proof_node_count++];
    memset(node, 0, sizeof(proof_node_t));
    node->type = type;
    strncpy(node->label, label, sizeof(node->label) - 1);
    
    switch (type) {
        case NODE_TENSOR:    node->color = COLOR_GREEN; break;
        case NODE_PAR:       node->color = COLOR_CYAN; break;
        case NODE_WITH:      node->color = COLOR_YELLOW; break;
        case NODE_PLUS:      node->color = COLOR_MAGENTA; break;
        case NODE_LOLLIPOP:  node->color = COLOR_RED; break;
        case NODE_CUT:       node->color = COLOR_WHITE; break;
        default:             node->color = COLOR_BLUE; break;
    }
    
    return node;
}


// CONCURRENT SESSION TYPES

typedef enum {
    VENDOR_IDLE,
    VENDOR_AWAITING_COIN,
    VENDOR_COIN_RECEIVED,
    VENDOR_DELIVERING_ITEM,
    VENDOR_COMPLETE,
    VENDOR_ERROR
} vendor_state_t;

typedef struct {
    char name[16];
    char item[16];
    vendor_state_t state;
    int coin_resource_idx;
    int item_resource_idx;
    int x, y;  // Screen position for visualization
    uint16_t color;
} vendor_t;

#define MAX_VENDORS 4
static vendor_t vendors[MAX_VENDORS];
static int vendor_count = 0;

typedef struct {
    int vendor_a_idx;  // First vendor in tensor
    int vendor_b_idx;  // Second vendor in tensor
    bool both_complete;
} tensor_session_t;

static tensor_session_t tensor_sessions[4];
static int tensor_session_count = 0;


// RESOURCE SYSTEM (from previous example, extended)

typedef enum {
    MULTIPLICITY_LINEAR,
    MULTIPLICITY_AFFINE,
    MULTIPLICITY_UNLIMITED
} multiplicity_t;

typedef struct {
    char name[16];
    multiplicity_t mult;
    int uses_remaining;
    bool consumed;
    int owner_vendor_idx;  // Which vendor owns this
    uint16_t color;
    int x, y;
} resource_t;

#define MAX_RESOURCES 64
static resource_t resources[MAX_RESOURCES];
static int resource_count = 0;

int create_resource(const char *name, multiplicity_t mult, int vendor_idx) {
    if (resource_count >= MAX_RESOURCES) return -1;
    
    resource_t *r = &resources[resource_count];
    strncpy(r->name, name, sizeof(r->name) - 1);
    r->mult = mult;
    r->consumed = false;
    r->owner_vendor_idx = vendor_idx;
    
    switch (mult) {
        case MULTIPLICITY_LINEAR:
            r->uses_remaining = 1;
            r->color = COLOR_RED;
            break;
        case MULTIPLICITY_AFFINE:
            r->uses_remaining = 1;
            r->color = COLOR_YELLOW;
            break;
        case MULTIPLICITY_UNLIMITED:
            r->uses_remaining = -1;
            r->color = COLOR_GREEN;
            break;
    }
    
    return resource_count++;
}

bool consume_resource(int idx) {
    if (idx < 0 || idx >= resource_count) return false;
    
    resource_t *r = &resources[idx];
    
    if (r->consumed && r->mult == MULTIPLICITY_LINEAR) {
        return false; // Type error!
    }
    
    if (r->uses_remaining > 0) {
        r->uses_remaining--;
    }
    
    r->consumed = true;
    return true;
}


// VENDOR (SESSION PARTICIPANT)

int create_vendor(const char *name, const char *item, int x, int y, uint16_t color) {
    if (vendor_count >= MAX_VENDORS) return -1;
    
    vendor_t *v = &vendors[vendor_count];
    strncpy(v->name, name, sizeof(v->name) - 1);
    strncpy(v->item, item, sizeof(v->item) - 1);
    v->state = VENDOR_IDLE;
    v->x = x;
    v->y = y;
    v->color = color;
    v->coin_resource_idx = -1;
    v->item_resource_idx = -1;
    
    return vendor_count++;
}

void vendor_start(int idx) {
    if (idx < 0 || idx >= vendor_count) return;
    vendors[idx].state = VENDOR_AWAITING_COIN;
}

void vendor_receive_coin(int vendor_idx, int coin_idx) {
    if (vendor_idx < 0 || vendor_idx >= vendor_count) return;
    
    vendor_t *v = &vendors[vendor_idx];
    if (v->state != VENDOR_AWAITING_COIN) return;
    
    v->coin_resource_idx = coin_idx;
    v->state = VENDOR_COIN_RECEIVED;
}

void vendor_deliver_item(int vendor_idx) {
    if (vendor_idx < 0 || vendor_idx >= vendor_count) return;
    
    vendor_t *v = &vendors[vendor_idx];
    if (v->state != VENDOR_COIN_RECEIVED) return;
    
    // Consume the coin
    if (!consume_resource(v->coin_resource_idx)) {
        v->state = VENDOR_ERROR;
        return;
    }
    
    // Create the item (LINEAR resource)
    int item_idx = create_resource(v->item, MULTIPLICITY_LINEAR, vendor_idx);
    v->item_resource_idx = item_idx;
    v->state = VENDOR_DELIVERING_ITEM;
}

void vendor_complete(int vendor_idx) {
    if (vendor_idx < 0 || vendor_idx >= vendor_count) return;
    vendors[vendor_idx].state = VENDOR_COMPLETE;
}


// TENSOR SESSION (A ⊗ B)

int create_tensor_session(int vendor_a_idx, int vendor_b_idx) {
    if (tensor_session_count >= 4) return -1;
    
    tensor_session_t *ts = &tensor_sessions[tensor_session_count];
    ts->vendor_a_idx = vendor_a_idx;
    ts->vendor_b_idx = vendor_b_idx;
    ts->both_complete = false;
    
    return tensor_session_count++;
}

void update_tensor_session(int ts_idx) {
    if (ts_idx < 0 || ts_idx >= tensor_session_count) return;
    
    tensor_session_t *ts = &tensor_sessions[ts_idx];
    vendor_t *va = &vendors[ts->vendor_a_idx];
    vendor_t *vb = &vendors[ts->vendor_b_idx];
    
    // Tensor requires BOTH vendors to complete
    if (va->state == VENDOR_COMPLETE && vb->state == VENDOR_COMPLETE) {
        ts->both_complete = true;
    }
}


// PROOF NET VISUALS

void layout_proof_tree(proof_node_t *node, int x, int y, int h_spacing) {
    if (!node) return;
    
    node->x = x;
    node->y = y;
    
    if (node->left && node->right) {
        // Binary node: lay out children
        layout_proof_tree(node->left, x - h_spacing, y + 40, h_spacing / 2);
        layout_proof_tree(node->right, x + h_spacing, y + 40, h_spacing / 2);
    } else if (node->left) {
        // Unary node
        layout_proof_tree(node->left, x, y + 40, h_spacing);
    }
}

void draw_proof_net_edge(uint16_t *fb, int x1, int y1, int x2, int y2, uint16_t color) {
    fb_draw_line_aa(fb, x1, y1, x2, y2, color);
}

void draw_proof_net_node(uint16_t *fb, proof_node_t *node) {
    if (!node) return;
    
    uint16_t color = node->highlighted ? COLOR_WHITE : node->color;
    
    // Draw node circle
    fb_draw_circle_aa(fb, node->x, node->y, 12, color);
    
    // Draw label
    int label_x = node->x - (strlen(node->label) * 4);
    fb_draw_string(fb, label_x, node->y - 4, node->label, color, COLOR_BLACK);
    
    // Draw edges to children
    if (node->left) {
        draw_proof_net_edge(fb, node->x, node->y + 12, 
                           node->left->x, node->left->y - 12, color);
        draw_proof_net_node(fb, node->left);
    }
    if (node->right) {
        draw_proof_net_edge(fb, node->x, node->y + 12,
                           node->right->x, node->right->y - 12, color);
        draw_proof_net_node(fb, node->right);
    }
    
    // Draw cut edge if present
    if (node->type == NODE_CUT && node->dual) {
        // Draw dashed line to dual
        for (int i = 0; i < 5; i++) {
            float t0 = i / 5.0f;
            float t1 = (i + 0.5f) / 5.0f;
            float x0 = node->x + t0 * (node->dual->x - node->x);
            float y0 = node->y + t0 * (node->dual->y - node->y);
            float x1 = node->x + t1 * (node->dual->x - node->x);
            float y1 = node->y + t1 * (node->dual->y - node->y);
            fb_draw_line_aa(fb, x0, y0, x1, y1, COLOR_RED);
        }
    }
}


// BUILD EXAMPLE PROOF NET

proof_node_t* build_tensor_proof_net(void) {
    // Build proof for: (A ⊗ B) ⊸ (B ⊗ A)
    // This proves commutativity of tensor
    
    proof_node_t *a1 = create_proof_node(NODE_FORMULA, "A");
    proof_node_t *b1 = create_proof_node(NODE_FORMULA, "B");
    proof_node_t *tensor1 = create_proof_node(NODE_TENSOR, "⊗");
    tensor1->left = a1;
    tensor1->right = b1;
    
    proof_node_t *b2 = create_proof_node(NODE_FORMULA, "B");
    proof_node_t *a2 = create_proof_node(NODE_FORMULA, "A");
    proof_node_t *tensor2 = create_proof_node(NODE_TENSOR, "⊗");
    tensor2->left = b2;
    tensor2->right = a2;
    
    proof_node_t *lollipop = create_proof_node(NODE_LOLLIPOP, "⊸");
    lollipop->left = tensor1;
    lollipop->right = tensor2;
    
    // Create cuts (communication channels)
    proof_node_t *cut_a = create_proof_node(NODE_CUT, "cut");
    proof_node_t *cut_b = create_proof_node(NODE_CUT, "cut");
    cut_a->dual = a2;
    a2->dual = cut_a;
    cut_b->dual = b2;
    b2->dual = cut_b;
    
    return lollipop;
}

// VISUALISATION

static uint16_t framebuffer[DISPLAY_WIDTH * DISPLAY_HEIGHT];
static proof_node_t *main_proof_net = NULL;

void draw_vendor(uint16_t *fb, int idx) {
    if (idx < 0 || idx >= vendor_count) return;
    
    vendor_t *v = &vendors[idx];
    
    // Draw vendor box
    fb_fill_rect(fb, v->x, v->y, 80, 50, v->color >> 2);
    fb_fill_rect(fb, v->x+2, v->y+2, 76, 46, COLOR_BLACK);
    
    // Draw vendor name
    fb_draw_string(fb, v->x+4, v->y+4, v->name, v->color, COLOR_BLACK);
    
    // Draw state
    const char *state_names[] = {"IDLE", "AWAIT", "RECV", "DLVR", "DONE", "ERR"};
    fb_draw_string(fb, v->x+4, v->y+16, state_names[v->state], 
                   COLOR_CYAN, COLOR_BLACK);
    
    // Draw item
    fb_draw_string(fb, v->x+4, v->y+28, v->item, COLOR_YELLOW, COLOR_BLACK);
    
    // Draw session type below
    char session[32];
    snprintf(session, sizeof(session), "!$ %c %s", 140, v->item); // lollipop
    fb_draw_string(fb, v->x+4, v->y+40, session, COLOR_GREEN, COLOR_BLACK);
}

void draw_tensor_indicator(uint16_t *fb, int ts_idx) {
    if (ts_idx < 0 || ts_idx >= tensor_session_count) return;
    
    tensor_session_t *ts = &tensor_sessions[ts_idx];
    vendor_t *va = &vendors[ts->vendor_a_idx];
    vendor_t *vb = &vendors[ts->vendor_b_idx];
    
    // Draw tensor symbol between vendors
    int mid_x = (va->x + vb->x + 80) / 2;
    int mid_y = va->y + 25;  // vertical center of the 50px-high boxes

    fb_draw_char(fb, mid_x - 4, mid_y - 4, 139, COLOR_GREEN, COLOR_BLACK); // cross/tensor

    // Draw completion status — "DONE" is 24px wide, fits the 40px gap
    if (ts->both_complete) {
        fb_draw_string(fb, mid_x - 12, mid_y + 8, "DONE",
                      COLOR_GREEN, COLOR_BLACK);
    }
}

void draw_header(uint16_t *fb) {
    fb_draw_string(fb, 4, 4, "TENSOR PRODUCT (A", COLOR_WHITE, COLOR_BLACK);
    fb_draw_char(fb, 124, 4, 139, COLOR_GREEN, COLOR_BLACK); // tensor symbol
    fb_draw_string(fb, 132, 4, "B)", COLOR_WHITE, COLOR_BLACK);
    
    fb_draw_string(fb, 4, 16, "Parallel Sessions:", COLOR_CYAN, COLOR_BLACK);
}


// GAME LOOP

static int demo_state = 0;

void init_demo(void) {
    // Create two vendors in parallel (tensor composition)
    int vendor_a = create_vendor("VendorA", "Apple", 20, 60, COLOR_RED);
    int vendor_b = create_vendor("VendorB", "Banana", 140, 60, COLOR_YELLOW);
    
    // Create tensor session
    create_tensor_session(vendor_a, vendor_b);
    
    // Start both vendors (parallel composition)
    vendor_start(vendor_a);
    vendor_start(vendor_b);
    
    // Build proof net visualization
    main_proof_net = build_tensor_proof_net();
    if (main_proof_net) {
        layout_proof_tree(main_proof_net, DISPLAY_WIDTH/2, 140, 60);
    }
}

void update_demo(void) {
    static uint32_t last_update = 0;
    uint32_t now = to_ms_since_boot(get_absolute_time());
    
    if (now - last_update < 2000) return;
    last_update = now;
    
    // Automated demo progression
    switch (demo_state) {
        case 0:
            // Provide coins to both vendors (parallel action!)
            {
                int coin_a = create_resource("Coin", MULTIPLICITY_UNLIMITED, 0);
                int coin_b = create_resource("Coin", MULTIPLICITY_UNLIMITED, 1);
                vendor_receive_coin(0, coin_a);
                vendor_receive_coin(1, coin_b);
                demo_state++;
            }
            break;
            
        case 1:
            // Vendor A delivers
            vendor_deliver_item(0);
            demo_state++;
            break;
            
        case 2:
            // Vendor B delivers (parallel completion)
            vendor_deliver_item(1);
            demo_state++;
            break;
            
        case 3:
            // Mark both complete
            vendor_complete(0);
            vendor_complete(1);
            update_tensor_session(0);
            demo_state++;
            break;
            
        case 4:
            // Highlight proof net nodes to show cut elimination
            if (main_proof_net && main_proof_net->left) {
                main_proof_net->left->highlighted = true;
            }
            demo_state++;
            break;
            
        default:
            // Reset
            proof_node_count = 0;
            resource_count = 0;
            vendor_count = 0;
            tensor_session_count = 0;
            demo_state = 0;
            init_demo();
            break;
    }
}

void render(void) {
    fb_clear(framebuffer, COLOR_BLACK);
    
    draw_header(framebuffer);
    
    // Draw vendors
    for (int i = 0; i < vendor_count; i++) {
        draw_vendor(framebuffer, i);
    }
    
    // Draw tensor indicators
    for (int i = 0; i < tensor_session_count; i++) {
        draw_tensor_indicator(framebuffer, i);
    }
    
    // Draw proof net
    if (main_proof_net) {
        draw_proof_net_node(framebuffer, main_proof_net);
    }
    
    display_blit_full(framebuffer);
}


//

int main(void) {
    stdio_init_all();
    
    if (display_pack_init() != DISPLAY_OK) {
        printf("Display init failed!\n");
        return 1;
    }
    
    if (buttons_init() != DISPLAY_OK) {
        printf("Buttons init failed!\n");
        return 1;
    }
    
    display_set_backlight(true);
    
    printf("\nTENSOR PRODUCT & PROOF NETS\n");
    printf("Demonstrating A ⊗ B: parallel composition\n");
    printf("Two vendors operate simultaneously\n");
    printf("Both must complete for tensor to succeed\n");
    printf("----------------------------------------\n\n");
    
    init_demo();
    
    while (true) {
        update_demo();
        render();
        sleep_ms(16);
    }
    
    return 0;
}
