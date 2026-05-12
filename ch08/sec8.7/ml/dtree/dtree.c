#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <float.h>
#include <string.h>

#define MAX_CLASSES 10
#define MAX_FEATURES 10
#define MIN_SAMPLES_SPLIT 2
#define MAX_DEPTH 10

typedef struct {
    float features[MAX_FEATURES];
    int class;
} DataPoint;

typedef struct Node {
    int is_leaf;
    int class_label;
    float class_probabilities[MAX_CLASSES];
    int split_feature;
    float split_value;
    int samples_count;
    float impurity;
    struct Node *left;
    struct Node *right;
} Node;

typedef struct {
    int num_features;
    int num_classes;
    int max_depth;
    int min_samples_split;
    float min_impurity_decrease;
} TreeConfig;

typedef struct {
    int feature;
    float value;
    float impurity_decrease;
    int left_count;
    int right_count;
} SplitResult;


DataPoint dataset[] = {
    {{2.0, 3.0, 1.5}, 0},
    {{1.5, 2.5, 2.0}, 0},
    {{3.0, 4.0, 1.8}, 0},
    {{2.2, 3.5, 1.6}, 0},
    {{5.0, 2.0, 3.2}, 1},
    {{4.5, 3.0, 2.8}, 1},
    {{6.0, 2.5, 3.5}, 1},
    {{5.5, 1.8, 3.0}, 1},
    {{7.0, 4.0, 4.2}, 2},
    {{6.5, 3.8, 4.0}, 2},
    {{8.0, 4.5, 4.5}, 2}
};


Node* create_leaf(int* class_counts, int total_samples, int num_classes);
Node* create_decision_node(int split_feature, float split_value, Node* left, Node* right);
float calculate_gini_impurity(int* class_counts, int total_samples, int num_classes);
float calculate_entropy(int* class_counts, int total_samples, int num_classes);
void count_classes(DataPoint* data, int n, int* class_counts, int num_classes);
int find_majority_class(int* class_counts, int num_classes);
SplitResult find_best_split(DataPoint* data, int n, TreeConfig* config);
Node* build_tree_recursive(DataPoint* data, int n, int depth, TreeConfig* config);
int predict_class(Node* tree, float* features);
float* predict_probabilities(Node* tree, float* features);
void print_tree(Node* tree, int depth, TreeConfig* config);
void free_tree(Node* tree);
double evaluate_accuracy(Node* tree, DataPoint* test_data, int test_size);



Node* create_leaf(int* class_counts, int total_samples, int num_classes) {
    Node* node = (Node*)malloc(sizeof(Node));
    node->is_leaf = 1;
    node->class_label = find_majority_class(class_counts, num_classes);
    node->samples_count = total_samples;
    node->impurity = calculate_gini_impurity(class_counts, total_samples, num_classes);
    node->left = NULL;
    node->right = NULL;
    
    // Calculate class probabilities
    for (int i = 0; i < num_classes; i++) {
        node->class_probabilities[i] = (float)class_counts[i] / total_samples;
    }
    
    return node;
}

Node* create_decision_node(int split_feature, float split_value, Node* left, Node* right) {
    Node* node = (Node*)malloc(sizeof(Node));
    node->is_leaf = 0;
    node->split_feature = split_feature;
    node->split_value = split_value;
    node->left = left;
    node->right = right;
    node->samples_count = left->samples_count + right->samples_count;
    return node;
}

float calculate_gini_impurity(int* class_counts, int total_samples, int num_classes) {
    if (total_samples == 0) return 0.0;
    
    float impurity = 1.0;
    for (int i = 0; i < num_classes; i++) {
        float prob = (float)class_counts[i] / total_samples;
        impurity -= prob * prob;
    }
    return impurity;
}

float calculate_entropy(int* class_counts, int total_samples, int num_classes) {
    if (total_samples == 0) return 0.0;
    
    float entropy = 0.0;
    for (int i = 0; i < num_classes; i++) {
        if (class_counts[i] > 0) {
            float prob = (float)class_counts[i] / total_samples;
            entropy -= prob * log2(prob);
        }
    }
    return entropy;
}

void count_classes(DataPoint* data, int n, int* class_counts, int num_classes) {
    memset(class_counts, 0, num_classes * sizeof(int));
    for (int i = 0; i < n; i++) {
        if (data[i].class < num_classes) {
            class_counts[data[i].class]++;
        }
    }
}

int find_majority_class(int* class_counts, int num_classes) {
    int max_count = 0;
    int majority_class = 0;
    
    for (int i = 0; i < num_classes; i++) {
        if (class_counts[i] > max_count) {
            max_count = class_counts[i];
            majority_class = i;
        }
    }
    return majority_class;
}

SplitResult find_best_split(DataPoint* data, int n, TreeConfig* config) {
    SplitResult best_split = {-1, 0.0, -FLT_MAX, 0, 0};
    
    int parent_counts[MAX_CLASSES];
    count_classes(data, n, parent_counts, config->num_classes);
    float parent_impurity = calculate_gini_impurity(parent_counts, n, config->num_classes);
    
    // Try each feature
    for (int feature = 0; feature < config->num_features; feature++) {
        // Sort data by current feature
        for (int threshold_idx = 0; threshold_idx < n; threshold_idx++) {
            float threshold = data[threshold_idx].features[feature];
            
            // Count samples in left and right splits
            int left_counts[MAX_CLASSES] = {0};
            int right_counts[MAX_CLASSES] = {0};
            int left_total = 0, right_total = 0;
            
            for (int i = 0; i < n; i++) {
                if (data[i].features[feature] <= threshold) {
                    left_counts[data[i].class]++;
                    left_total++;
                } else {
                    right_counts[data[i].class]++;
                    right_total++;
                }
            }
            
            // Skip if split doesn't separate data
            if (left_total == 0 || right_total == 0) continue;
            
            // Calculate weighted impurity
            float left_impurity = calculate_gini_impurity(left_counts, left_total, config->num_classes);
            float right_impurity = calculate_gini_impurity(right_counts, right_total, config->num_classes);
            float weighted_impurity = (left_total * left_impurity + right_total * right_impurity) / n;
            
            float impurity_decrease = parent_impurity - weighted_impurity;
            
            if (impurity_decrease > best_split.impurity_decrease) {
                best_split.feature = feature;
                best_split.value = threshold;
                best_split.impurity_decrease = impurity_decrease;
                best_split.left_count = left_total;
                best_split.right_count = right_total;
            }
        }
    }
    
    return best_split;
}

Node* build_tree_recursive(DataPoint* data, int n, int depth, TreeConfig* config) {
    int class_counts[MAX_CLASSES];
    count_classes(data, n, class_counts, config->num_classes);
    
    // Check stopping criteria
    if (n < config->min_samples_split || 
        depth >= config->max_depth ||
        calculate_gini_impurity(class_counts, n, config->num_classes) == 0.0) {
        return create_leaf(class_counts, n, config->num_classes);
    }
    
    // Find best split
    SplitResult split = find_best_split(data, n, config);
    
    // If no good split found or minimum impurity decrease not met
    if (split.feature == -1 || split.impurity_decrease < config->min_impurity_decrease) {
        return create_leaf(class_counts, n, config->num_classes);
    }
    
    // Split data
    DataPoint* left_data = (DataPoint*)malloc(split.left_count * sizeof(DataPoint));
    DataPoint* right_data = (DataPoint*)malloc(split.right_count * sizeof(DataPoint));
    
    int left_idx = 0, right_idx = 0;
    for (int i = 0; i < n; i++) {
        if (data[i].features[split.feature] <= split.value) {
            left_data[left_idx++] = data[i];
        } else {
            right_data[right_idx++] = data[i];
        }
    }
    
    // Recursively build subtrees
    Node* left = build_tree_recursive(left_data, split.left_count, depth + 1, config);
    Node* right = build_tree_recursive(right_data, split.right_count, depth + 1, config);
    
    free(left_data);
    free(right_data);
    
    return create_decision_node(split.feature, split.value, left, right);
}

int predict_class(Node* tree, float* features) {
    while (!tree->is_leaf) {
        if (features[tree->split_feature] <= tree->split_value) {
            tree = tree->left;
        } else {
            tree = tree->right;
        }
    }
    return tree->class_label;
}

float* predict_probabilities(Node* tree, float* features) {
    while (!tree->is_leaf) {
        if (features[tree->split_feature] <= tree->split_value) {
            tree = tree->left;
        } else {
            tree = tree->right;
        }
    }
    return tree->class_probabilities;
}

void print_tree(Node* tree, int depth, TreeConfig* config) {
    if (tree == NULL) return;
    
    for (int i = 0; i < depth; i++) printf("  ");
    
    if (tree->is_leaf) {
        printf("Leaf: class=%d, samples=%d, impurity=%.3f\n", 
               tree->class_label, tree->samples_count, tree->impurity);
    } else {
        printf("Split: feature_%d <= %.2f, samples=%d\n", 
               tree->split_feature, tree->split_value, tree->samples_count);
        print_tree(tree->left, depth + 1, config);
        print_tree(tree->right, depth + 1, config);
    }
}

double evaluate_accuracy(Node* tree, DataPoint* test_data, int test_size) {
    int correct = 0;
    for (int i = 0; i < test_size; i++) {
        int prediction = predict_class(tree, test_data[i].features);
        if (prediction == test_data[i].class) {
            correct++;
        }
    }
    return (double)correct / test_size;
}

void free_tree(Node* tree) {
    if (tree == NULL) return;
    if (!tree->is_leaf) {
        free_tree(tree->left);
        free_tree(tree->right);
    }
    free(tree);
}

int main() {
    printf("Decision Tree Classifier\n");
    printf("=================================\n\n");
    
    // Configure the decision tree
    TreeConfig config = {
        .num_features = 3,
        .num_classes = 3,
        .max_depth = 5,
        .min_samples_split = 2,
        .min_impurity_decrease = 0.0
    };
    
    int dataset_size = sizeof(dataset) / sizeof(dataset[0]);
    
    // Build the decision tree
    printf("Building decision tree ..\n");
    Node* tree = build_tree_recursive(dataset, dataset_size, 0, &config);
    
    // Print the tree structure
    printf("\nDecision Tree Structure:\n");
    print_tree(tree, 0, &config);
    
    // Test predictions
    printf("\nTesting predictions:\n");
    DataPoint test_cases[] = {
        {{3.5, 3.5, 2.0}, -1},  // Unknown class for testing
        {{1.0, 2.0, 1.0}, -1},
        {{7.5, 4.2, 4.8}, -1}
    };
    
    for (int i = 0; i < 3; i++) {
        int prediction = predict_class(tree, test_cases[i].features);
        float* probabilities = predict_probabilities(tree, test_cases[i].features);
        
        printf("Test case %d: [%.1f, %.1f, %.1f] -> Class %d\n", 
               i+1, test_cases[i].features[0], test_cases[i].features[1], 
               test_cases[i].features[2], prediction);
        
        printf("  Class probabilities: ");
        for (int j = 0; j < config.num_classes; j++) {
            printf("Class %d: %.3f ", j, probabilities[j]);
        }
        printf("\n");
    }
    
    // Evaluate on training data (for demonstration)
    double accuracy = evaluate_accuracy(tree, dataset, dataset_size);
    printf("\nTraining accuracy: %.2f%%\n", accuracy * 100);
    
    // Clean up
    free_tree(tree);

    return 0;
}


/*
// Iris flower classification dataset
// Features: sepal_length, sepal_width, petal_length
// Classes: 0=Setosa, 1=Versicolor, 2=Virginica

DataPoint iris_dataset[] = {
    // Setosa (typically smaller petals)
    {{5.1, 3.5, 1.4}, 0}, {{4.9, 3.0, 1.4}, 0}, {{4.7, 3.2, 1.3}, 0},
    {{4.6, 3.1, 1.5}, 0}, {{5.0, 3.6, 1.4}, 0}, {{5.4, 3.9, 1.7}, 0},
    
    // Versicolor (medium-sized petals)
    {{7.0, 3.2, 4.7}, 1}, {{6.4, 3.2, 4.5}, 1}, {{6.9, 3.1, 4.9}, 1},
    {{5.5, 2.3, 4.0}, 1}, {{6.5, 2.8, 4.6}, 1}, {{5.7, 2.8, 4.5}, 1},
    
    // Virginica (largest petals)
    {{6.3, 3.3, 6.0}, 2}, {{5.8, 2.7, 5.1}, 2}, {{7.1, 3.0, 5.9}, 2},
    {{6.3, 2.9, 5.6}, 2}, {{6.5, 3.0, 5.8}, 2}, {{7.6, 3.0, 6.6}, 2}
};

DataPoint iris_test_cases[] = {
    {{5.0, 3.4, 1.6}, -1},  // Should be Setosa (small petal)
    {{6.2, 2.8, 4.8}, -1},  // Should be Versicolor (medium petal)
    {{7.2, 3.2, 6.0}, -1},  // Should be Virginica (large petal)
    {{4.8, 3.0, 1.2}, -1},  // Edge case: very small -> Setosa
    {{6.8, 3.0, 5.5}, -1}   // Edge case: large -> Virginica
};

const char* iris_feature_names[] = {"Sepal Length", "Sepal Width", "Petal Length"};
const char* iris_class_names[] = {"Setosa", "Versicolor", "Virginica"};



// Medical risk assesment dataset
// Features: age, systolic_bp, cholesterol
// Classes: 0=Low Risk, 1=Medium Risk, 2=High Risk

DataPoint medical_dataset[] = {
    // Low Risk (young, good vitals)
    {{25, 110, 170}, 0}, {{28, 115, 165}, 0}, {{32, 120, 180}, 0},
    {{35, 118, 175}, 0}, {{30, 112, 160}, 0}, {{33, 125, 185}, 0},
    
    // Medium Risk (middle-aged or some elevated vitals)
    {{45, 135, 210}, 1}, {{42, 140, 220}, 1}, {{48, 138, 215}, 1},
    {{50, 142, 225}, 1}, {{38, 145, 200}, 1}, {{44, 148, 235}, 1},
    
    // High Risk (older with high vitals)
    {{65, 160, 280}, 2}, {{62, 165, 275}, 2}, {{70, 170, 290}, 2},
    {{68, 175, 285}, 2}, {{72, 168, 295}, 2}, {{66, 172, 300}, 2}
};

DataPoint medical_test_cases[] = {
    {{27, 118, 172}, -1},  // Young, good vitals -> Low Risk
    {{46, 141, 218}, -1},  // Middle-aged, elevated -> Medium Risk  
    {{67, 167, 287}, -1},  // Older, high vitals -> High Risk
    {{55, 128, 195}, -1},  // Borderline case
    {{75, 180, 310}, -1}   // Very high risk case
};

const char* medical_feature_names[] = {"Age", "Systolic BP", "Cholesterol"};
const char* medical_class_names[] = {"Low Risk", "Medium Risk", "High Risk"};



// Student performance prediction dataset
// Features: study_hours_per_week, previous_gpa, attendance_percentage
// Classes: 0=Poor (F), 1=Average (C), 2=Good (A)

DataPoint student_dataset[] = {
    // Poor Performance (low effort)
    {{5, 2.0, 60}, 0}, {{8, 2.2, 65}, 0}, {{6, 1.8, 55}, 0},
    {{10, 2.4, 70}, 0}, {{7, 2.1, 62}, 0}, {{9, 2.3, 68}, 0},
    
    // Average Performance (moderate effort)
    {{15, 2.8, 80}, 1}, {{18, 3.0, 85}, 1}, {{16, 2.9, 82}, 1},
    {{20, 3.2, 88}, 1}, {{17, 3.1, 83}, 1}, {{19, 2.7, 86}, 1},
    
    // Good Performance (high effort)
    {{25, 3.7, 95}, 2}, {{28, 3.8, 96}, 2}, {{30, 3.9, 98}, 2},
    {{26, 3.6, 94}, 2}, {{32, 4.0, 97}, 2}, {{29, 3.8, 93}, 2}
};

DataPoint student_test_cases[] = {
    {{12, 2.5, 72}, -1},   // Low-moderate effort -> likely Poor/Average
    {{22, 3.4, 90}, -1},   // Good effort -> likely Good
    {{6, 1.9, 58}, -1},    // Very low effort -> Poor
    {{35, 3.9, 99}, -1},   // Exceptional effort -> Good
    {{14, 2.6, 75}, -1}    // Borderline case
};

const char* student_feature_names[] = {"Study Hours/Week", "Previous GPA", "Attendance %"};
const char* student_class_names[] = {"Poor (F)", "Average (C)", "Good (A)"};
*/
