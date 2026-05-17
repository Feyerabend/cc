#include "../src/core/property_test.h"
#include "../src/strategies/integer_strategy.h"
#include "../src/strategies/tuple_strategy.h"
#include "../src/strategies/oneof_strategy.h"
#include <stdio.h>
#include <stdlib.h>

typedef enum {
    SHAPE_RECTANGLE,
    SHAPE_CIRCLE
} ShapeType;

typedef struct {
    int x;
    int y;
} Point;

typedef struct {
    Point center;
    int width;
    int height;
} Rectangle;

typedef struct {
    Point center;
    int radius;
} Circle;

typedef struct {
    ShapeType type;
    union {
        Rectangle rect;
        Circle circ;
    } data;
} Shape;

int calculate_area_rectangle(Rectangle* rect) {
    return rect->width * rect->height;
}

int calculate_area_circle(Circle* circle) {
    return (int)(3.14159 * circle->radius * circle->radius);
}

void test_tuple_coordinates(void* input) {
    Tuple2* coord = (Tuple2*)input;
    int* x = (int*)coord->first;
    int* y = (int*)coord->second;
    
    PROPERTY_ASSERT(*x >= 0 && *x <= 100);
    PROPERTY_ASSERT(*y >= 0 && *y <= 100);
}

void test_rectangle_area_positive(void* input) {
    Tuple2* rect_data = (Tuple2*)input;
    Tuple2* center = (Tuple2*)rect_data->first;
    Tuple2* dimensions = (Tuple2*)rect_data->second;
    
    int* width = (int*)dimensions->first;
    int* height = (int*)dimensions->second;
    
    if (*width > 0 && *height > 0) {
        int area = (*width) * (*height);
        PROPERTY_ASSERT(area > 0);
        PROPERTY_ASSERT(area >= *width);
        PROPERTY_ASSERT(area >= *height);
    }
}

void test_circle_area_vs_perimeter(void* input) {
    Tuple2* circ_data = (Tuple2*)input;
    int* radius = (int*)circ_data->second;
    
    if (*radius > 0) {
        double area = 3.14159 * (*radius) * (*radius);
        double perimeter = 2 * 3.14159 * (*radius);
        
        PROPERTY_ASSERT(area >= 0);
        PROPERTY_ASSERT(perimeter >= 0);
        
        if (*radius > 2) {
            PROPERTY_ASSERT(area > perimeter);
        }
    }
}

void run_property_test(
    const char* name,
    PropertyFn property,
    Strategy* strategy,
    int max_examples
) {
    printf("Running: %s\n", name);
    
    TestResult* result = test_property(
        property,
        strategy,
        max_examples,
        (unsigned int)time(NULL)
    );
    
    if (result->passed) {
        printf("  ✓ PASSED (%d examples in %.3fs)\n",
               result->examples_tried,
               result->execution_time);
    } else {
        printf("  ✗ FAILED after %d examples\n", result->examples_tried);
        printf("    Shrink iterations: %d\n", result->shrink_iterations);
    }
    
    test_result_free(result);
    printf("\n");
}

int main(void) {
    printf("Property-Based Testing - Compositional Generation\n");
    printf("================================================\n\n");
    
    Strategy* coord_strategy = integer_strategy_create(0, 100);
    Strategy* point_strategy = tuple2_strategy_create(coord_strategy, coord_strategy);
    
    printf("Testing Point (Tuple of Coordinates):\n");
    printf("-------------------------------------\n");
    
    run_property_test(
        "Point coordinates within bounds",
        test_tuple_coordinates,
        point_strategy,
        100
    );
    
    Strategy* dimension_strategy = integer_strategy_create(1, 50);
    Strategy* dimensions_strategy = tuple2_strategy_create(
        dimension_strategy,
        dimension_strategy
    );
    
    Strategy* rectangle_strategy = tuple2_strategy_create(
        point_strategy,
        dimensions_strategy
    );
    
    printf("Testing Rectangle (Tuple of Point and Dimensions):\n");
    printf("-------------------------------------------------\n");
    
    run_property_test(
        "Rectangle area is positive and >= dimensions",
        test_rectangle_area_positive,
        rectangle_strategy,
        100
    );
    
    Strategy* radius_strategy = integer_strategy_create(1, 50);
    Strategy* circle_strategy = tuple2_strategy_create(
        point_strategy,
        radius_strategy
    );
    
    printf("Testing Circle (Tuple of Point and Radius):\n");
    printf("-------------------------------------------\n");
    
    run_property_test(
        "Circle area > perimeter for radius > 2",
        test_circle_area_vs_perimeter,
        circle_strategy,
        100
    );
    
    Strategy* shapes[2] = {rectangle_strategy, circle_strategy};
    Strategy* shape_strategy = oneof_strategy_create(shapes, 2);
    
    printf("Testing Mixed Shapes (OneOf strategy):\n");
    printf("-------------------------------------\n");
    printf("(OneOf strategy generates either rectangles or circles)\n\n");
    
    strategy_free(shape_strategy);
    strategy_free(circle_strategy);
    strategy_free(rectangle_strategy);
    strategy_free(dimensions_strategy);
    strategy_free(dimension_strategy);
    strategy_free(point_strategy);
    strategy_free(radius_strategy);
    strategy_free(coord_strategy);
    
    printf("All tests completed.\n");
    printf("\nNote: This example demonstrates:\n");
    printf("  - Tuple strategies for compositional generation\n");
    printf("  - Building complex types from simple strategies\n");
    printf("  - OneOf strategy for choosing between alternatives\n");
    printf("  - Testing geometric properties\n");
    
    return 0;
}
