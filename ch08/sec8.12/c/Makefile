CC = gcc
CFLAGS = -Wall -Wextra -std=c99 -O2 -g -Isrc
LDFLAGS = -lm

SRC_CORE = src/core/property_test.c
SRC_TYPES = src/types/types.c
SRC_STRATEGIES = src/strategies/integer_strategy.c \
                 src/strategies/list_strategy.c \
                 src/strategies/tuple_strategy.c \
                 src/strategies/string_strategy.c \
                 src/strategies/oneof_strategy.c \
                 src/strategies/bst_strategy.c \
                 src/strategies/stateful_strategy.c

SRC_ALL = $(SRC_CORE) $(SRC_TYPES) $(SRC_STRATEGIES)
OBJ_ALL = $(SRC_ALL:.c=.o)

LIB_TARGET = build/libproperty_test.a

EXAMPLES = examples/01_algebraic_properties \
           examples/02_sorting_properties \
           examples/03_compositional_generation \
           examples/04_string_properties \
           examples/05_bst_properties \
           examples/06_kv_store_properties \
           examples/07_stack_properties \
           examples/08_serialization_properties \
           examples/09_encryption_properties \
           examples/10_avl_tree_properties \
           examples/11_metamorphic_testing \
           examples/12_model_based_testing \
           examples/13_oracle_based_testing

all: $(LIB_TARGET) $(EXAMPLES)

$(LIB_TARGET): $(OBJ_ALL)
	@mkdir -p build
	ar rcs $@ $^
	@echo "Built library: $(LIB_TARGET)"

examples/01_algebraic_properties: examples/01_algebraic_properties.o $(LIB_TARGET)
	$(CC) $(CFLAGS) -o $@ $< -Lbuild -lproperty_test $(LDFLAGS)

examples/02_sorting_properties: examples/02_sorting_properties.o $(LIB_TARGET)
	$(CC) $(CFLAGS) -o $@ $< -Lbuild -lproperty_test $(LDFLAGS)

examples/03_compositional_generation: examples/03_compositional_generation.o $(LIB_TARGET)
	$(CC) $(CFLAGS) -o $@ $< -Lbuild -lproperty_test $(LDFLAGS)

examples/04_string_properties: examples/04_string_properties.o $(LIB_TARGET)
	$(CC) $(CFLAGS) -o $@ $< -Lbuild -lproperty_test $(LDFLAGS)

examples/05_bst_properties: examples/05_bst_properties.o $(LIB_TARGET)
	$(CC) $(CFLAGS) -o $@ $< -Lbuild -lproperty_test $(LDFLAGS)

examples/06_kv_store_properties: examples/06_kv_store_properties.o $(LIB_TARGET)
	$(CC) $(CFLAGS) -o $@ $< -Lbuild -lproperty_test $(LDFLAGS)

examples/07_stack_properties: examples/07_stack_properties.o $(LIB_TARGET)
	$(CC) $(CFLAGS) -o $@ $< -Lbuild -lproperty_test $(LDFLAGS)

examples/08_serialization_properties: examples/08_serialization_properties.o $(LIB_TARGET)
	$(CC) $(CFLAGS) -o $@ $< -Lbuild -lproperty_test $(LDFLAGS)

examples/09_encryption_properties: examples/09_encryption_properties.o $(LIB_TARGET)
	$(CC) $(CFLAGS) -o $@ $< -Lbuild -lproperty_test $(LDFLAGS)

examples/10_avl_tree_properties: examples/10_avl_tree_properties.o $(LIB_TARGET)
	$(CC) $(CFLAGS) -o $@ $< -Lbuild -lproperty_test $(LDFLAGS)

examples/11_metamorphic_testing: examples/11_metamorphic_testing.o $(LIB_TARGET)
	$(CC) $(CFLAGS) -o $@ $< -Lbuild -lproperty_test $(LDFLAGS)

examples/12_model_based_testing: examples/12_model_based_testing.o $(LIB_TARGET)
	$(CC) $(CFLAGS) -o $@ $< -Lbuild -lproperty_test $(LDFLAGS)

examples/13_oracle_based_testing: examples/13_oracle_based_testing.o $(LIB_TARGET)
	$(CC) $(CFLAGS) -o $@ $< -Lbuild -lproperty_test $(LDFLAGS)

%.o: %.c
	$(CC) $(CFLAGS) -c $< -o $@

clean:
	rm -f $(OBJ_ALL) examples/*.o $(EXAMPLES) $(LIB_TARGET)
	rm -rf build
	@echo "Cleaned all build artifacts"

test: $(EXAMPLES)
	@echo "----------------------------------------"
	@echo "Running Example 1: Algebraic Properties"
	@echo "----------------------------------------"
	@./examples/01_algebraic_properties
	@echo ""
	@echo "--------------------------------------"
	@echo "Running Example 2: Sorting Properties"
	@echo "--------------------------------------"
	@./examples/02_sorting_properties
	@echo ""
	@echo "--------------------------------------------="
	@echo "Running Example 3: Compositional Generation"
	@echo "--------------------------------------------="
	@./examples/03_compositional_generation
	@echo ""
	@echo "--------------------------------------"
	@echo "Running Example 4: String Properties"
	@echo "--------------------------------------"
	@./examples/04_string_properties
	@echo ""
	@echo "--------------------------------------------"
	@echo "Running Example 5: Binary Search Tree (BST)"
	@echo "--------------------------------------------"
	@./examples/05_bst_properties
	@echo ""
	@echo "----------------------------------------------="
	@echo "Running Example 6: Key-Value Store (Dependent)"
	@echo "----------------------------------------------="
	@./examples/06_kv_store_properties
	@echo ""
	@echo "------------------------------------------"
	@echo "Running Example 7: Stack (Stateful)"
	@echo "------------------------------------------"
	@./examples/07_stack_properties
	@echo ""
	@echo "--------------------------------------------"
	@echo "Running Example 8: Serialization Round-Trip"
	@echo "--------------------------------------------"
	@./examples/08_serialization_properties
	@echo ""
	@echo "------------------------------------------"
	@echo "Running Example 9: Encryption Properties"
	@echo "------------------------------------------"
	@./examples/09_encryption_properties
	@echo ""
	@echo "----------------------------------------"
	@echo "Running Example 10: AVL Tree Balance"
	@echo "----------------------------------------"
	@./examples/10_avl_tree_properties
	@echo ""
	@echo "------------------------------------------"
	@echo "Running Example 11: Metamorphic Testing"
	@echo "------------------------------------------"
	@./examples/11_metamorphic_testing
	@echo ""
	@echo "--------------------------------------------"
	@echo "Running Example 12: Model-Based Testing"
	@echo "--------------------------------------------"
	@./examples/12_model_based_testing
	@echo ""
	@echo "------------------------------------------="
	@echo "Running Example 13: Oracle-Based Testing"
	@echo "------------------------------------------="
	@./examples/13_oracle_based_testing

structure:
	@echo "Project Structure:"
	@echo "------------------"
	@echo "src/"
	@echo "  core/         - Core testing framework"
	@echo "  strategies/   - Strategy implementations"
	@echo "  types/        - Shared data structures"
	@echo "examples/       - Numbered example programs"
	@echo "build/          - Build artifacts"
	@echo "docs/           - Documentation"
	@echo ""
	@echo "Current components:"
	@echo "  Core:       property_test"
	@echo "  Types:      IntList, String, Tuple2, Tuple3"
	@echo "  Strategies: Integer, List, Tuple, String, OneOf, BST, Stateful"
	@echo "  Examples:   13 working examples"

.PHONY: all clean test structure
