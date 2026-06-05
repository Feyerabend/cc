/*
 * linked_list.c -- Separation Logic: Linked List Operations
 *
 * In Separation Logic, a singly-linked list at pointer x containing
 * logical sequence α is defined recursively:
 *
 *   list(x, [])    ≝  x = NULL  ∧  emp
 *   list(x, v::vs) ≝  ∃y.  x ↦ (v, y)  *  list(y, vs)
 *
 * The separating conjunction (*) forces every node to occupy a
 * distinct address -- no aliasing, no cycles, by construction.
 *
 * We cannot run a separation logic proof checker here, but we can:
 *   (a) make the spatial invariants explicit as runtime assertions, and
 *   (b) trace the loop invariant from §11.4 through the
 *       in-place reversal step by step.
 *
 * Compile:  gcc -Wall -std=c11 -o linked_list linked_list.c
 */

#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <stdbool.h>

typedef struct Node {
    int value;
    struct Node *next;
} Node;


/* Structural checks -- approximating separation logic properties */

/*
 * Returns true iff no two nodes in the list share an address.
 *
 * This approximates the (*) requirement: in  x ↦ _ * y ↦ _,
 * disjoint union ⊎ forces x ≠ y.  A list whose nodes alias would
 * require the same address to appear in two disjoint heap parts,
 * which is impossible under (*).
 */
static bool all_nodes_distinct(Node *head)
{
    Node *seen[1024];
    int count = 0;
    for (Node *p = head; p != NULL; p = p->next) {
        for (int i = 0; i < count; i++)
            if (seen[i] == p) return false;
        assert(count < 1024);
        seen[count++] = p;
    }
    return true;
}

/*
 * Returns true iff the list has no cycle (Floyd's tortoise and hare).
 *
 * A well-formed list(x, α) is always acyclic.  A cycle would mean
 * some node n appears in two disjoint parts of the heap -- impossible
 * because disjoint union requires disjoint domains.
 */
static bool no_cycle(Node *head)
{
    Node *slow = head, *fast = head;
    while (fast != NULL && fast->next != NULL) {
        slow = slow->next;
        fast = fast->next->next;
        if (slow == fast) return false;
    }
    return true;
}

/*
 * Returns true iff the list represents arr[0..n-1].
 * Corresponds to checking that list(head, α) holds with α = arr.
 */
static bool matches_sequence(Node *head, int arr[], int n)
{
    Node *p = head;
    for (int i = 0; i < n; i++) {
        if (p == NULL || p->value != arr[i]) return false;
        p = p->next;
    }
    return p == NULL;
}

/* Verify all three separation logic properties at once. */
static void assert_valid_list(Node *head, int arr[], int n,
                              const char *label)
{
    assert(no_cycle(head));
    assert(all_nodes_distinct(head));
    assert(matches_sequence(head, arr, n));
    printf("  [%s] list is well-formed\n", label);
}


/* List construction and destruction */

/*
 * Allocate a list from arr[0..n-1].
 * Pre:  n >= 0
 * Post: list(result, arr[0..n-1])   (nodes freshly allocated, all distinct)
 */
static Node *list_from_array(int arr[], int n)
{
    Node *head = NULL;
    for (int i = n - 1; i >= 0; i--) {
        Node *node = malloc(sizeof(Node));
        assert(node != NULL);
        node->value = arr[i];
        node->next  = head;
        head = node;
    }
    return head;
}

/* Free all nodes; approximates restoring to emp. */
static void list_free(Node *head)
{
    while (head != NULL) {
        Node *next = head->next;
        free(head);
        head = next;
    }
}

static void list_print(Node *head)
{
    printf("[");
    for (Node *p = head; p != NULL; p = p->next)
        printf("%d%s", p->value, p->next ? ", " : "");
    printf("]");
}

/*
 * Assert that lists a and b share no node addresses.
 * This approximates: a and b occupy disjoint parts of the heap,
 * i.e. their heap portions satisfy list(a,_) * list(b,_).
 */
static void assert_disjoint(Node *a, Node *b)
{
    for (Node *pa = a; pa != NULL; pa = pa->next)
        for (Node *pb = b; pb != NULL; pb = pb->next)
            assert(pa != pb && "lists share a node -- spatial disjointness violated");
}


/* In-place list reversal (§11.4 — Separation Logic and Heap Isolation) */

/*
 * Reverses the list at x in place.
 *
 * Pre:  list(x, α)
 * Post: list(result, reverse(α))
 *
 * Loop invariant:
 *   ∃α₁ α₂.  list(x, α₁)  *  list(y, α₂)
 *           ∧  reverse(α) = reverse(α₁) ++ α₂
 *
 * The (*) in the invariant ensures the two partial lists never share
 * a node, which is what allows us to safely redirect x->next to y.
 *
 * Entry:  α₁ = α,  α₂ = []
 * Exit:   α₁ = [],  α₂ = reverse(α)
 */
static Node *reverse_list(Node *x)
{
    Node *y = NULL;
    /* Invariant: list(x, α) * list(NULL, []),  reverse(α) = reverse(α) ++ [] */

    while (x != NULL) {
        /*
         * State:  list(x, v::α₁)  *  list(y, α₂)
         *         reverse(α) = reverse(v::α₁) ++ α₂
         */
        Node *t = x->next;   /* save tail; t heads list(t, α₁) */

        /*
         * State:  x ↦ (v, t)  *  list(t, α₁)  *  list(y, α₂)
         */
        x->next = y;         /* reverse the pointer */

        /*
         * State:  x ↦ (v, y)  *  list(t, α₁)  *  list(y, α₂)
         *       = list(x, v::α₂)  *  list(t, α₁)    [fold definition]
         */
        y = x;
        x = t;

        /*
         * State:  list(x, α₁)  *  list(y, v::α₂)
         * Invariant holds: reverse(α) = reverse(α₁) ++ (v::α₂)
         */
    }

    /* α₁ = [], so reverse(α) = [] ++ α₂ = α₂.  list(y, reverse(α)). */
    return y;
}


/* Demo */

static void demo_reversal(void)
{
    printf("-- In-Place List Reversal (§11.4: Separation Logic) --\n\n");

    int original[] = {1, 2, 3, 4, 5};
    int reversed[] = {5, 4, 3, 2, 1};
    int n = 5;

    Node *list = list_from_array(original, n);

    printf("Pre:  list(x, "); list_print(list); printf(")\n");
    assert_valid_list(list, original, n, "precondition");
    printf("\n");

    /*
     * Trace the loop invariant explicitly at each step.
     * We run the reversal by hand so we can observe the invariant.
     */
    printf("Tracing the loop invariant:\n");
    Node *x = list, *y = NULL;
    int step = 0;

    while (x != NULL) {
        printf("  Step %d:  x = ", step); list_print(x);
        printf("  *  y = ");             list_print(y); printf("\n");

        /* Check: no_cycle and all_nodes_distinct on both partial lists */
        assert(no_cycle(x));
        assert(no_cycle(y));
        assert(all_nodes_distinct(x));
        assert(all_nodes_distinct(y));
        /* Check: x-list and y-list are spatially disjoint */
        assert_disjoint(x, y);

        Node *t = x->next;
        x->next = y;
        y = x;
        x = t;
        step++;
    }

    Node *result = y;
    printf("\nPost: list(result, "); list_print(result); printf(")\n");
    assert_valid_list(result, reversed, n, "postcondition");
    printf("Verified: result = reverse([1,2,3,4,5])\n\n");

    list_free(result);

    /* Verify the same result using reverse_list() directly. */
    Node *list2   = list_from_array(original, n);
    Node *result2 = reverse_list(list2);
    assert(matches_sequence(result2, reversed, n));
    printf("reverse_list() gives same result: verified\n\n");
    list_free(result2);
}

static void demo_frame_rule(void)
{
    printf("-- Frame Rule: Append (§11.4: Separation Logic and Heap Isolation) --\n\n");

    /*
     * The frame rule says that a function touching only list(xs, α₁)
     * leaves any disjoint resource R intact:
     *
     *   {list(xs, α₁)} append(xs, ys) {list(xs, α₁++α₂)}
     *   ——————————————————————————————————————————————————— [Frame]
     *   {list(xs, α₁) * R} append(xs, ys) {list(xs, α₁++α₂) * R}
     *
     * Here R = list(frame, [99,100]).  append walks xs only;
     * it never touches frame, so frame must be unchanged.
     */
    int a1[]         = {1, 2, 3};
    int a2[]         = {4, 5, 6};
    int combined[]   = {1, 2, 3, 4, 5, 6};
    int frame_seq[]  = {99, 100};

    Node *xs    = list_from_array(a1, 3);
    Node *ys    = list_from_array(a2, 3);
    Node *frame = list_from_array(frame_seq, 2);

    printf("xs    = "); list_print(xs);    printf("  (list to extend)\n");
    printf("ys    = "); list_print(ys);    printf("  (suffix to attach)\n");
    printf("frame = "); list_print(frame); printf("  (unrelated bystander)\n\n");

    /* Verify initial spatial disjointness: xs, ys, frame all separate */
    assert_disjoint(xs, frame);
    assert_disjoint(ys, frame);
    assert_disjoint(xs, ys);
    printf("Precondition: xs * ys * frame are spatially disjoint\n\n");

    /* Append: walk to end of xs, link to ys */
    Node *p = xs;
    while (p->next != NULL) p = p->next;
    p->next = ys;

    printf("After append:\n");
    printf("  xs = "); list_print(xs); printf("\n");
    printf("  frame = "); list_print(frame); printf("  (should be unchanged)\n\n");

    assert(matches_sequence(xs,    combined,  6));
    assert(matches_sequence(frame, frame_seq, 2));
    printf("Postcondition:\n");
    printf("  list(xs, [1,2,3,4,5,6]): verified\n");
    printf("  frame unchanged (frame rule holds): verified\n\n");

    list_free(xs);      /* xs now chains into ys; frees both */
    list_free(frame);
}

int main(void)
{
    printf("Separation Logic: Linked List Operations\n");
    printf("----------------------------------------\n\n");

    demo_reversal();
    demo_frame_rule();

    printf("All separation logic properties verified.\n");
    return 0;
}
