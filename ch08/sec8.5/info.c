#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>

#define MAX_SYMS  256
#define MAX_NODES (MAX_SYMS * 2)
#define MAX_CODE  (MAX_SYMS + 1)

/* ---- Tree node pool ---------------------------------------------------- */

typedef struct {
    int   sym;         /* ASCII value, or -1 for internal nodes */
    long  freq;
    int   left, right; /* indices into pool[], -1 if leaf      */
} Node;

static Node pool[MAX_NODES];
static int  pool_top;

static int node_new(int sym, long freq, int left, int right) {
    int i = pool_top++;
    pool[i] = (Node){ sym, freq, left, right };
    return i;
}

/* ---- Min-heap of pool indices, keyed by freq --------------------------- */

static int  heap[MAX_NODES];
static int  heap_sz;

static void heap_push(int idx) {
    int i = heap_sz++;
    heap[i] = idx;
    while (i > 0) {
        int p = (i - 1) / 2;
        if (pool[heap[p]].freq <= pool[heap[i]].freq) break;
        int t = heap[p]; heap[p] = heap[i]; heap[i] = t;
        i = p;
    }
}

static int heap_pop(void) {
    int top  = heap[0];
    heap[0]  = heap[--heap_sz];
    for (int i = 0;;) {
        int l = 2*i+1, r = 2*i+2, m = i;
        if (l < heap_sz && pool[heap[l]].freq < pool[heap[m]].freq) m = l;
        if (r < heap_sz && pool[heap[r]].freq < pool[heap[m]].freq) m = r;
        if (m == i) break;
        int t = heap[i]; heap[i] = heap[m]; heap[m] = t;
        i = m;
    }
    return top;
}

/* ---- Code table -------------------------------------------------------- */

static char codes[MAX_SYMS][MAX_CODE];
static int  code_len[MAX_SYMS];

static void gen_codes(int node, char *buf, int depth) {
    if (pool[node].sym != -1) {
        buf[depth] = '\0';
        strncpy(codes[pool[node].sym], buf, MAX_CODE - 1);
        code_len[pool[node].sym] = depth ? depth : 1;
        if (!depth) { codes[pool[node].sym][0] = '0'; codes[pool[node].sym][1] = '\0'; }
        return;
    }
    buf[depth] = '0'; gen_codes(pool[node].left,  buf, depth + 1);
    buf[depth] = '1'; gen_codes(pool[node].right, buf, depth + 1);
}

/* ---- Entropy ----------------------------------------------------------- */

static double entropy(const char *text, int n) {
    long freq[MAX_SYMS] = {0};
    for (int i = 0; i < n; i++) freq[(unsigned char)text[i]]++;
    double h = 0.0;
    for (int i = 0; i < MAX_SYMS; i++) {
        if (!freq[i]) continue;
        double p = (double)freq[i] / n;
        h -= p * log2(p);
    }
    return h;
}

/* ---- Report ------------------------------------------------------------ */

static void report(const char *text) {
    int n = (int)strlen(text);
    long freq[MAX_SYMS] = {0};
    for (int i = 0; i < n; i++) freq[(unsigned char)text[i]]++;

    pool_top = 0; heap_sz = 0;
    memset(code_len, 0, sizeof code_len);

    for (int i = 0; i < MAX_SYMS; i++)
        if (freq[i]) heap_push(node_new(i, freq[i], -1, -1));

    while (heap_sz > 1) {
        int a = heap_pop(), b = heap_pop();
        heap_push(node_new(-1, pool[a].freq + pool[b].freq, a, b));
    }
    int root = heap[0];
    char buf[MAX_CODE];
    gen_codes(root, buf, 0);

    long total_bits = 0;
    for (int i = 0; i < MAX_SYMS; i++) total_bits += freq[i] * code_len[i];

    double h   = entropy(text, n);
    double avg = (double)total_bits / n;

    if (n > 25)
        printf("Text:          \"%.*s...\" (%d chars)\n", 22, text, n);
    else
        printf("Text:          \"%s\"\n", text);

    printf("  Entropy:     %.4f bits/symbol  (theoretical minimum)\n", h);
    printf("  Avg code:    %.4f bits/symbol  (Huffman actual)\n",      avg);
    printf("  Gap:         %.4f bits/symbol  (redundancy)\n",          avg - h);
    printf("  Original:    %d bits (8-bit ASCII)\n",                   n * 8);
    printf("  Compressed:  %ld bits\n",                                total_bits);
    printf("  Ratio:       %.1f%%\n",                        100.0 * total_bits / (n * 8));
    printf("  Codes:      ");
    for (int i = 0; i < MAX_SYMS; i++) {
        if (!freq[i]) continue;
        if (i == ' ') printf("  SPC=%s", codes[i]);
        else          printf("  %c=%s",  i, codes[i]);
    }
    printf("\n\n");
}

int main(void) {
    report("aaabbc");
    report("hello");
    report("hello world");
    report("aaaaaa");
    report("abcdefgh");
    report("the quick brown fox jumps over the lazy dog");
    return 0;
}
