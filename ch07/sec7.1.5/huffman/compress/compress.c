#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_TREE_HT 256

// Huffman tree node
struct MinHeapNode {
    char data;                // Character
    unsigned freq;            // Frequency
    struct MinHeapNode *left, *right;  // Left and right child
};

// Min heap for priority queue
struct MinHeap {
    unsigned size;            // Current size
    unsigned capacity;        // Max capacity
    struct MinHeapNode **array;  // Array of nodes
};

// Create new node
struct MinHeapNode *newNode(char data, unsigned freq) {
    struct MinHeapNode *temp = (struct MinHeapNode *)malloc(sizeof(struct MinHeapNode));
    temp->left = temp->right = NULL;
    temp->data = data;
    temp->freq = freq;
    return temp;
}

// Create min heap
struct MinHeap *createMinHeap(unsigned capacity) {
    struct MinHeap *minHeap = (struct MinHeap *)malloc(sizeof(struct MinHeap));
    minHeap->size = 0;
    minHeap->capacity = capacity;
    minHeap->array = (struct MinHeapNode **)malloc(minHeap->capacity * sizeof(struct MinHeapNode *));
    return minHeap;
}

// Swap nodes
void swapMinHeapNode(struct MinHeapNode **a, struct MinHeapNode **b) {
    struct MinHeapNode *t = *a;
    *a = *b;
    *b = t;
}

// Heapify
void minHeapify(struct MinHeap *minHeap, int idx) {
    int smallest = idx;
    int left = 2 * idx + 1;
    int right = 2 * idx + 2;

    if (left < minHeap->size && minHeap->array[left]->freq < minHeap->array[smallest]->freq)
        smallest = left;

    if (right < minHeap->size && minHeap->array[right]->freq < minHeap->array[smallest]->freq)
        smallest = right;

    if (smallest != idx) {
        swapMinHeapNode(&minHeap->array[smallest], &minHeap->array[idx]);
        minHeapify(minHeap, smallest);
    }
}

// Check if size is 1
int isSizeOne(struct MinHeap *minHeap) {
    return (minHeap->size == 1);
}

// Extract min
struct MinHeapNode *extractMin(struct MinHeap *minHeap) {
    struct MinHeapNode *temp = minHeap->array[0];
    minHeap->array[0] = minHeap->array[minHeap->size - 1];
    --minHeap->size;
    minHeapify(minHeap, 0);
    return temp;
}

// Insert node
void insertMinHeap(struct MinHeap *minHeap, struct MinHeapNode *minHeapNode) {
    ++minHeap->size;
    int i = minHeap->size - 1;
    while (i && minHeapNode->freq < minHeap->array[(i - 1) / 2]->freq) {
        minHeap->array[i] = minHeap->array[(i - 1) / 2];
        i = (i - 1) / 2;
    }
    minHeap->array[i] = minHeapNode;
}

// Build min heap
void buildMinHeap(struct MinHeap *minHeap) {
    int n = minHeap->size - 1;
    int i;
    for (i = (n - 1) / 2; i >= 0; --i)
        minHeapify(minHeap, i);
}

// Check if leaf
int isLeaf(struct MinHeapNode *root) {
    return !(root->left) && !(root->right);
}

// Create and build min heap from frequency
struct MinHeap *createAndBuildMinHeap(char data[], unsigned freq[], int size) {
    struct MinHeap *minHeap = createMinHeap(size);
    for (int i = 0; i < size; ++i)
        minHeap->array[i] = newNode(data[i], freq[i]);
    minHeap->size = size;
    buildMinHeap(minHeap);
    return minHeap;
}

// Build Huffman tree
struct MinHeapNode *buildHuffmanTree(char data[], unsigned freq[], int size) {
    if (size == 0) return NULL; // Empty file
    struct MinHeapNode *left, *right, *top;
    struct MinHeap *minHeap = createAndBuildMinHeap(data, freq, size);
    while (!isSizeOne(minHeap)) {
        left = extractMin(minHeap);
        right = extractMin(minHeap);
        top = newNode('$', left->freq + right->freq);
        top->left = left;
        top->right = right;
        insertMinHeap(minHeap, top);
    }
    return extractMin(minHeap);
}

// Codes array
char codes[256][MAX_TREE_HT];

// Generate codes recursive
void generateCodes(struct MinHeapNode *root, char str[], int top) {
    if (root->left) {
        str[top] = '0';
        generateCodes(root->left, str, top + 1);
    }
    if (root->right) {
        str[top] = '1';
        generateCodes(root->right, str, top + 1);
    }
    if (isLeaf(root)) {
        str[top] = '\0';
        strcpy(codes[(unsigned char)root->data], str);
    }
}

// Compress the file
void compress(FILE *in, FILE *out, unsigned freq[]) {
    char data[256];
    unsigned freq_copy[256];
    int size = 0;
    unsigned total_chars = 0;
    for (int i = 0; i < 256; i++) {
        if (freq[i]) {
            data[size] = i;
            freq_copy[size] = freq[i];
            size++;
            total_chars += freq[i];
        }
    }
    if (total_chars == 0) return; // Empty file

    struct MinHeapNode *root = buildHuffmanTree(data, freq_copy, size);

    char str[MAX_TREE_HT];
    generateCodes(root, str, 0);

    // Write frequency header
    fwrite(freq, sizeof(unsigned), 256, out);

    // Write encoded data
    char ch;
    unsigned char byte = 0;
    int bit_count = 0;
    fseek(in, 0, SEEK_SET);
    while ((ch = fgetc(in)) != EOF) {
        char *code = codes[(unsigned char)ch];
        for (int i = 0; code[i]; i++) {
            byte = (byte << 1) | (code[i] - '0');
            bit_count++;
            if (bit_count == 8) {
                fputc(byte, out);
                byte = 0;
                bit_count = 0;
            }
        }
    }
    // Padding last byte
    int padding = 0;
    if (bit_count > 0) {
        byte <<= (8 - bit_count);
        fputc(byte, out);
        padding = 8 - bit_count;
    }
    fputc(padding, out);
}

int main(int argc, char *argv[]) {
    if (argc != 3) {
        printf("Usage: %s input.txt output.huf\n", argv[0]);
        return 1;
    }

    FILE *in = fopen(argv[1], "r");
    if (!in) {
        printf("Cannot open input file\n");
        return 1;
    }

    FILE *out = fopen(argv[2], "wb");
    if (!out) {
        printf("Cannot open output file\n");
        fclose(in);
        return 1;
    }

    unsigned freq[256] = {0};
    char ch;
    while ((ch = fgetc(in)) != EOF) {
        freq[(unsigned char)ch]++;
    }

    compress(in, out, freq);

    fclose(in);
    fclose(out);
    printf("Compression complete: %s -> %s\n", argv[1], argv[2]);
    return 0;
}
