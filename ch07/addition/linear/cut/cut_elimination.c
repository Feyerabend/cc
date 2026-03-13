/*
 * CUT ELIMINATION AS COMPUTATION
 *
 * 
 * This demonstrates the Curry-Howard-Lambek correspondence:
 * 
 *   LOGIC          COMPUTATION      CATEGORY THEORY
 *   -----          -----------      ---------------
 *   Proposition    Type             Object
 *   Proof          Program          Morphism
 *   Normalization  Execution        Composition
 *   Cut            Redex            Identity law
 *   Cut Elim       Reduction        Coherence
 * 
 * CUT ELIMINATION:
 * ----------------
 * A CUT is when you have:
 *   Γ ⊢ A, Δ    Σ, A ⊢ Π
 *   ────────────────────── CUT
 *      Γ, Σ ⊢ Δ, Π
 * 
 * It represents an "intermediary" - A is produced and immediately consumed.
 * 
 * Cut elimination REMOVES the intermediary:
 * - Producer and consumer talk directly
 * - This is COMPUTATION happening
 * - The proof "runs"
 * 
 * EXAMPLE:
 * --------
 * 
 * Before cut elimination:
 *   Producer creates A ⊗ B
 *   Consumer takes A ⊗ B apart
 *   
 * After cut elimination:
 *   Producer's components connect directly to consumer's expectations
 *   No intermediate pair needed
 * 
 * REDUCTION RULES (selection):
 * 
 * TENSOR/PAR cut:
 *   (a ⊗ b) connected to (x ⅋ y) reduces to:
 *   a → x  and  b → y  (two new cuts)
 * 
 * PLUS/WITH cut:
 *   (a ⊕ b) connected to (x & y) reduces to:
 *   Either a → x  or  b → y  (based on ⊕ choice)
 * 
 * BANG/WHYNOT cut:
 *   !a connected to ?x reduces to:
 *   Multiple copies of (a → x)
 * 
 * This program VISUALISES these reductions happening in real-time.
 */

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "pico/stdlib.h"
#include "display.h"
#include "font.h"


// PROOF NET STRUCTURE

typedef enum {
    OP_TENSOR,      // ⊗
    OP_PAR,         // ⅋
    OP_WITH,        // &
    OP_PLUS,        // ⊕
    OP_LOLLIPOP,    // ⊸
    OP_BANG,        // !
    OP_WHYNOT,      // ?
    OP_ATOM         // Atomic formula
} operator_t;

typedef struct pn_node {
    operator_t op;
    char label[8];
    int id;
    
    // Graph structure
    struct pn_node *left;
    struct pn_node *right;
    struct pn_node *dual;  // For cuts
    
    // Visualization
    float x, y;
    float target_x, target_y;  // For animation
    uint16_t color;
    bool marked_for_reduction;
    bool is_cut;
    
    // Metadata
    int depth;
    bool visited;
} pn_node_t;

#define MAX_NODES 128
static pn_node_t nodes[MAX_NODES];
static int node_count = 0;
static int next_id = 0;

pn_node_t* new_node(operator_t op, const char *label) {
    if (node_count >= MAX_NODES) return NULL;
    
    pn_node_t *n = &nodes[node_count++];
    memset(n, 0, sizeof(pn_node_t));
    n->op = op;
    n->id = next_id++;
    strncpy(n->label, label, sizeof(n->label) - 1);
    
    switch (op) {
        case OP_TENSOR: n->color = COLOR_GREEN; break;
        case OP_PAR: n->color = COLOR_CYAN; break;
        case OP_WITH: n->color = COLOR_YELLOW; break;
        case OP_PLUS: n->color = COLOR_MAGENTA; break;
        case OP_LOLLIPOP: n->color = COLOR_RED; break;
        case OP_BANG: n->color = fb_rgb(100, 255, 100); break;
        case OP_WHYNOT: n->color = fb_rgb(100, 255, 255); break;
        default: n->color = COLOR_BLUE; break;
    }
    
    return n;
}

pn_node_t* make_cut(pn_node_t *producer, pn_node_t *consumer) {
    if (!producer || !consumer) return NULL;
    
    producer->dual = consumer;
    consumer->dual = producer;
    producer->is_cut = true;
    consumer->is_cut = true;
    
    return producer;
}


// CUT ELIMINATION RULES

typedef struct {
    pn_node_t *cut_node;
    char description[64];
    bool applied;
} reduction_step_t;

#define MAX_REDUCTIONS 32
static reduction_step_t reduction_queue[MAX_REDUCTIONS];
static int reduction_count = 0;

void add_reduction(pn_node_t *cut, const char *desc) {
    if (reduction_count >= MAX_REDUCTIONS) return;
    
    reduction_step_t *r = &reduction_queue[reduction_count++];
    r->cut_node = cut;
    strncpy(r->description, desc, sizeof(r->description) - 1);
    r->applied = false;
}

bool can_reduce(pn_node_t *node) {
    if (!node || !node->is_cut || !node->dual) return false;
    
    pn_node_t *producer = node;
    pn_node_t *consumer = node->dual;
    
    // Check if we have a reducible pattern
    
    // TENSOR/PAR reduction
    if (producer->op == OP_TENSOR && consumer->op == OP_PAR) {
        return true;
    }
    
    // PLUS/WITH reduction
    if (producer->op == OP_PLUS && consumer->op == OP_WITH) {
        return true;
    }
    
    // BANG/WHYNOT reduction
    if (producer->op == OP_BANG && consumer->op == OP_WHYNOT) {
        return true;
    }
    
    return false;
}

void reduce_tensor_par(pn_node_t *tensor, pn_node_t *par) {
    // (a ⊗ b) ⋈ (x ⅋ y)  →  (a ⋈ x) ∥ (b ⋈ y)
    // The cut on the compound structure becomes two cuts on components
    
    if (!tensor->left || !tensor->right || !par->left || !par->right) {
        return;
    }
    
    // Create two new cuts
    make_cut(tensor->left, par->left);
    make_cut(tensor->right, par->right);
    
    // Mark originals for deletion
    tensor->marked_for_reduction = true;
    par->marked_for_reduction = true;
    
    printf("REDUCED: Tensor/Par cut -> two component cuts\n");
}

void reduce_plus_with(pn_node_t *plus, pn_node_t *with_node) {
    // (a ⊕ b) ⋈ (x & y)  →  choose left or right
    // The choice in ⊕ determines which branch is taken
    
    // For demo, choose left branch
    if (plus->left && with_node->left) {
        make_cut(plus->left, with_node->left);
    }
    
    plus->marked_for_reduction = true;
    with_node->marked_for_reduction = true;
    
    printf("REDUCED: Plus/With cut -> left branch chosen\n");
}

void reduce_bang_whynot(pn_node_t *bang, pn_node_t *whynot) {
    // !a ⋈ ?x  →  potentially multiple copies of (a ⋈ x)
    // For simplicity, create one copy
    
    if (bang->left && whynot->left) {
        make_cut(bang->left, whynot->left);
    }
    
    bang->marked_for_reduction = true;
    whynot->marked_for_reduction = true;
    
    printf("REDUCED: Bang/Whynot cut -> copied\n");
}

void apply_reduction(pn_node_t *cut) {
    if (!cut || !cut->dual) return;
    
    pn_node_t *producer = cut;
    pn_node_t *consumer = cut->dual;
    
    if (producer->op == OP_TENSOR && consumer->op == OP_PAR) {
        reduce_tensor_par(producer, consumer);
    } else if (producer->op == OP_PLUS && consumer->op == OP_WITH) {
        reduce_plus_with(producer, consumer);
    } else if (producer->op == OP_BANG && consumer->op == OP_WHYNOT) {
        reduce_bang_whynot(producer, consumer);
    }
}

void find_all_reductions(void) {
    reduction_count = 0;
    
    for (int i = 0; i < node_count; i++) {
        pn_node_t *n = &nodes[i];
        if (n->marked_for_reduction) continue;
        
        if (can_reduce(n)) {
            char desc[64];
            snprintf(desc, sizeof(desc), "Cut %d (%s/%s)", 
                     n->id, n->label, n->dual->label);
            add_reduction(n, desc);
        }
    }
}


// EXAMPLE PROOF NETS

pn_node_t* build_tensor_par_example(void) {
    // Build: (A ⊗ B) with a cut to (A⊥ ⅋ B⊥)
    // This demonstrates the most basic reduction
    
    pn_node_t *a = new_node(OP_ATOM, "A");
    pn_node_t *b = new_node(OP_ATOM, "B");
    pn_node_t *tensor = new_node(OP_TENSOR, "⊗");
    tensor->left = a;
    tensor->right = b;
    
    pn_node_t *a_dual = new_node(OP_ATOM, "A⊥");
    pn_node_t *b_dual = new_node(OP_ATOM, "B⊥");
    pn_node_t *par = new_node(OP_PAR, "⅋");
    par->left = a_dual;
    par->right = b_dual;
    
    make_cut(tensor, par);
    
    return tensor;
}

pn_node_t* build_plus_with_example(void) {
    // (A ⊕ B) with cut to (A⊥ & B⊥)
    
    pn_node_t *a = new_node(OP_ATOM, "A");
    pn_node_t *b = new_node(OP_ATOM, "B");
    pn_node_t *plus = new_node(OP_PLUS, "⊕");
    plus->left = a;
    plus->right = b;
    
    pn_node_t *a_dual = new_node(OP_ATOM, "A⊥");
    pn_node_t *b_dual = new_node(OP_ATOM, "B⊥");
    pn_node_t *with_node = new_node(OP_WITH, "&");
    with_node->left = a_dual;
    with_node->right = b_dual;
    
    make_cut(plus, with_node);
    
    return plus;
}


// LAYOUT & VISUALISATION

static uint16_t framebuffer[DISPLAY_WIDTH * DISPLAY_HEIGHT];

void layout_tree(pn_node_t *node, float x, float y, float h_spread, int depth) {
    if (!node || node->visited) return;
    
    node->visited = true;
    node->x = node->target_x = x;
    node->y = node->target_y = y;
    node->depth = depth;
    
    if (node->left) {
        layout_tree(node->left, x - h_spread, y + 35, h_spread * 0.6f, depth + 1);
    }
    if (node->right) {
        layout_tree(node->right, x + h_spread, y + 35, h_spread * 0.6f, depth + 1);
    }
}

void animate_positions(void) {
    // Smooth animation towards target positions
    for (int i = 0; i < node_count; i++) {
        pn_node_t *n = &nodes[i];
        if (n->marked_for_reduction) {
            n->color = fb_rgb(80, 80, 80);  // Dim out
            continue;
        }
        
        float dx = n->target_x - n->x;
        float dy = n->target_y - n->y;
        n->x += dx * 0.1f;
        n->y += dy * 0.1f;
    }
}

void draw_edge(uint16_t *fb, pn_node_t *from, pn_node_t *to, uint16_t color) {
    if (!from || !to) return;
    fb_draw_line_aa(fb, from->x, from->y + 8, to->x, to->y - 8, color);
}

void draw_cut_edge(uint16_t *fb, pn_node_t *n1, pn_node_t *n2) {
    if (!n1 || !n2) return;
    
    // Dashed line for cuts
    float dx = n2->x - n1->x;
    float dy = n2->y - n1->y;
    float len = sqrtf(dx*dx + dy*dy);
    int segments = (int)(len / 10);
    
    for (int i = 0; i < segments; i += 2) {
        float t0 = i / (float)segments;
        float t1 = (i + 1) / (float)segments;
        float x0 = n1->x + t0 * dx;
        float y0 = n1->y + t0 * dy;
        float x1 = n1->x + t1 * dx;
        float y1 = n1->y + t1 * dy;
        fb_draw_line_aa(fb, x0, y0, x1, y1, COLOR_RED);
    }
}

void draw_node(uint16_t *fb, pn_node_t *node) {
    if (!node || node->marked_for_reduction) return;
    
    int x = (int)node->x;
    int y = (int)node->y;
    
    // Draw circle
    fb_draw_circle_aa(fb, x, y, 10, node->color);
    
    // Draw label
    int lx = x - (strlen(node->label) * 4);
    fb_draw_string(fb, lx, y - 4, node->label, node->color, COLOR_BLACK);
    
    // Draw edges
    if (node->left) {
        draw_edge(fb, node, node->left, node->color >> 1);
    }
    if (node->right) {
        draw_edge(fb, node, node->right, node->color >> 1);
    }
    
    // Draw cut edge
    if (node->is_cut && node->dual && node->id < node->dual->id) {
        draw_cut_edge(fb, node, node->dual);
    }
}

void draw_all_nodes(uint16_t *fb) {
    for (int i = 0; i < node_count; i++) {
        draw_node(fb, &nodes[i]);
    }
}

void draw_reduction_info(uint16_t *fb) {
    fb_draw_string(fb, 4, 4, "CUT ELIMINATION", COLOR_WHITE, COLOR_BLACK);
    
    char info[64];
    snprintf(info, sizeof(info), "Nodes: %d  Cuts: %d  Reducible: %d",
             node_count, 
             0,  // TODO: count cuts
             reduction_count);
    fb_draw_string(fb, 4, 16, info, COLOR_CYAN, COLOR_BLACK);
    
    if (reduction_count > 0) {
        fb_draw_string(fb, 4, 28, "Next reduction:", COLOR_YELLOW, COLOR_BLACK);
        fb_draw_string(fb, 4, 40, reduction_queue[0].description, 
                      COLOR_GREEN, COLOR_BLACK);
    } else {
        fb_draw_string(fb, 4, 28, "NORMAL FORM REACHED", COLOR_GREEN, COLOR_BLACK);
    }
}

void draw_legend(uint16_t *fb) {
    int x = DISPLAY_WIDTH - 70;
    int y = DISPLAY_HEIGHT - 80;
    
    fb_draw_char(fb, x, y, 139, COLOR_GREEN, COLOR_BLACK);  // tensor
    fb_draw_string(fb, x+10, y, "Tensor", COLOR_GREEN, COLOR_BLACK);
    
    fb_draw_string(fb, x, y+12, "P", COLOR_CYAN, COLOR_BLACK);  // par
    fb_draw_string(fb, x+10, y+12, "Par", COLOR_CYAN, COLOR_BLACK);
    
    fb_draw_string(fb, x, y+24, "&", COLOR_YELLOW, COLOR_BLACK);
    fb_draw_string(fb, x+10, y+24, "With", COLOR_YELLOW, COLOR_BLACK);
    
    fb_draw_string(fb, x, y+36, "+", COLOR_MAGENTA, COLOR_BLACK);
    fb_draw_string(fb, x+10, y+36, "Plus", COLOR_MAGENTA, COLOR_BLACK);
    
    fb_draw_line_aa(fb, x, y+50, x+30, y+50, COLOR_RED);
    fb_draw_string(fb, x+10, y+48, "Cut", COLOR_RED, COLOR_BLACK);
}


// DEMO

static int demo_phase = 0;
static pn_node_t *root = NULL;

void init_demo(void) {
    node_count = 0;
    next_id = 0;
    reduction_count = 0;
    
    // Build initial proof net with cuts
    root = build_tensor_par_example();
    
    // Reset visited flags and layout
    for (int i = 0; i < node_count; i++) {
        nodes[i].visited = false;
    }
    
    if (root) {
        layout_tree(root, DISPLAY_WIDTH / 2, 60, 60, 0);
        if (root->dual) {
            layout_tree(root->dual, DISPLAY_WIDTH / 2, 150, 60, 0);
        }
    }

    find_all_reductions();
}

void update_demo(void) {
    static uint32_t last_step = 0;
    uint32_t now = to_ms_since_boot(get_absolute_time());
    
    if (now - last_step < 2000) return;
    last_step = now;
    
    if (reduction_count > 0) {
        // Apply next reduction
        reduction_step_t *r = &reduction_queue[0];
        if (!r->applied) {
            apply_reduction(r->cut_node);
            r->applied = true;
            
            // Re-layout
            for (int i = 0; i < node_count; i++) {
                nodes[i].visited = false;
            }
            if (root) {
                layout_tree(root, DISPLAY_WIDTH / 2, 60, 60, 0);
                if (root->dual) {
                    layout_tree(root->dual, DISPLAY_WIDTH / 2, 150, 60, 0);
                }
            }

            // Find new reductions
            find_all_reductions();
        }
    } else {
        // No more reductions - cycle to next example
        demo_phase++;
        if (demo_phase >= 2) demo_phase = 0;
        
        node_count = 0;
        next_id = 0;
        
        if (demo_phase == 0) {
            root = build_tensor_par_example();
        } else {
            root = build_plus_with_example();
        }
        
        for (int i = 0; i < node_count; i++) {
            nodes[i].visited = false;
        }
        if (root) {
            layout_tree(root, DISPLAY_WIDTH / 2, 60, 60, 0);
            if (root->dual) {
                layout_tree(root->dual, DISPLAY_WIDTH / 2, 150, 60, 0);
            }
        }

        find_all_reductions();
    }
}

void render(void) {
    fb_clear(framebuffer, COLOR_BLACK);
    
    draw_reduction_info(framebuffer);
    draw_all_nodes(framebuffer);
    draw_legend(framebuffer);
    
    display_blit_full(framebuffer);
}

int main(void) {
    stdio_init_all();
    
    if (display_pack_init() != DISPLAY_OK) {
        printf("Display init failed!\n");
        return 1;
    }
    
    display_set_backlight(true);
    
    printf("\nCUT ELIMINATION VISUALISER\n");
    printf("Watching proof normalization as computation\n");
    printf("Cuts represent intermediate values\n");
    printf("Elimination removes them - program runs!\n");
    printf("---------------------------------------\n\n");

    init_demo();
    
    while (true) {
        animate_positions();
        update_demo();
        render();
        sleep_ms(16);
    }
    
    return 0;
}
