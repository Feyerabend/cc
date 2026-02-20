// Sample implementation of Huffman coding in C
// A greedy algorithm for data compression
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#define MAX_TREE_HT 100
#define ASCII_SIZE 256

// Huffman tree node
typedef struct Node {
    char data;
    unsigned freq;
    struct Node *left, *right;
} Node;

// Min-heap structure
typedef struct {
    unsigned size;
    unsigned capacity;
    Node **array;
} MinHeap;

// Create new node
Node* newNode(char data, unsigned freq) {
    Node* node = (Node*)malloc(sizeof(Node));
    node->data = data;
    node->freq = freq;
    node->left = node->right = NULL;
    return node;
}

// Create min-heap
MinHeap* createMinHeap(unsigned capacity) {
    MinHeap* heap = (MinHeap*)malloc(sizeof(MinHeap));
    heap->size = 0;
    heap->capacity = capacity;
    heap->array = (Node**)malloc(capacity * sizeof(Node*));
    return heap;
}

// Swap nodes
void swapNode(Node** a, Node** b) {
    Node* t = *a;
    *a = *b;
    *b = t;
}

// Heapify
void minHeapify(MinHeap* heap, int idx) {
    int smallest = idx;
    int left = 2 * idx + 1;
    int right = 2 * idx + 2;

    if (left < heap->size &&
        heap->array[left]->freq < heap->array[smallest]->freq)
        smallest = left;

    if (right < heap->size &&
        heap->array[right]->freq < heap->array[smallest]->freq)
        smallest = right;

    if (smallest != idx) {
        swapNode(&heap->array[smallest], &heap->array[idx]);
        minHeapify(heap, smallest);
    }
}

// Extract min
Node* extractMin(MinHeap* heap) {
    Node* temp = heap->array[0];
    heap->array[0] = heap->array[--heap->size];
    minHeapify(heap, 0);
    return temp;
}

// Insert into heap
void insertMinHeap(MinHeap* heap, Node* node) {
    int i = heap->size++;
    while (i && node->freq < heap->array[(i - 1) / 2]->freq) {
        heap->array[i] = heap->array[(i - 1) / 2];
        i = (i - 1) / 2;
    }
    heap->array[i] = node;
}

// Build min-heap
void buildMinHeap(MinHeap* heap) {
    int n = heap->size - 1;
    for (int i = (n - 1) / 2; i >= 0; i--)
        minHeapify(heap, i);
}

// Check leaf
int isLeaf(Node* node) {
    return !(node->left) && !(node->right);
}

// Create heap from frequency table
MinHeap* buildHeap(char data[], int freq[], int size) {
    MinHeap* heap = createMinHeap(size);
    for (int i = 0; i < size; i++)
        heap->array[i] = newNode(data[i], freq[i]);

    heap->size = size;
    buildMinHeap(heap);
    return heap;
}

// Build Huffman tree
Node* buildHuffmanTree(char data[], int freq[], int size) {
    Node *left, *right, *top;
    MinHeap* heap = buildHeap(data, freq, size);

    while (heap->size > 1) {
        left = extractMin(heap);
        right = extractMin(heap);

        top = newNode('$', left->freq + right->freq);
        top->left = left;
        top->right = right;

        insertMinHeap(heap, top);
    }

    return extractMin(heap);
}

// Print array (code)
void printArr(int arr[], int n) {
    for (int i = 0; i < n; i++)
        printf("%d", arr[i]);
    printf("\n");
}

// Generate codes
void printCodes(Node* root, int arr[], int top) {
    if (root->left) {
        arr[top] = 0;
        printCodes(root->left, arr, top + 1);
    }

    if (root->right) {
        arr[top] = 1;
        printCodes(root->right, arr, top + 1);
    }

    if (isLeaf(root)) {
        printf("'%c': ", root->data);
        printArr(arr, top);
    }
}

// Build frequency table
void buildFrequency(const char* str, int freq[]) {
    for (int i = 0; str[i]; i++)
        freq[(unsigned char)str[i]]++;
}

// Extract symbols with freq > 0
int extractSymbols(int freq[], char data[], int outFreq[]) {
    int size = 0;
    for (int i = 0; i < ASCII_SIZE; i++) {
        if (freq[i] > 0) {
            data[size] = (char)i;
            outFreq[size] = freq[i];
            size++;
        }
    }
    return size;
}

// Main
int main() {
    // const char* text = "huffman coding example";
    const char* text = "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.";

    int freq[ASCII_SIZE] = {0};
    buildFrequency(text, freq);

    char data[ASCII_SIZE];
    int frequencies[ASCII_SIZE];

    int size = extractSymbols(freq, data, frequencies);

    Node* root = buildHuffmanTree(data, frequencies, size);

    int arr[MAX_TREE_HT], top = 0;

    printf("Huffman Codes:\n");
    printCodes(root, arr, top);

    return 0;
}

