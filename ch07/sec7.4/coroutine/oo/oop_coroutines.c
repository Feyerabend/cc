#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <setjmp.h>
#include <stdint.h>


// SECTION 1: Base Coroutine Infrastructure

typedef struct {
    jmp_buf context;
    int state;
    int finished;
} CoroutineBase;

#define CO_YIELD(co) \
    do { \
        (co)->state = __LINE__; \
        if (setjmp((co)->context) == 0) return 1; \
        case __LINE__:; \
    } while(0)

#define CO_BEGIN(co) \
    if ((co)->finished) return 0; \
    if (setjmp((co)->context) == 0) { \
        if ((co)->state != 0) longjmp((co)->context, 1); \
    } \
    switch((co)->state) { case 0:

#define CO_END(co) \
    } \
    (co)->finished = 1; \
    return 0;

#define CO_RESUME(co) \
    (setjmp((co)->context) == 0 ? longjmp((co)->context, 1) : 0)


// SECTION 2: Shape Hierarchy - Demonstrating Inheritance & Polymorphism

// Virtual method table for shapes
typedef struct Shape Shape;

typedef struct {
    double (*area)(Shape* self);
    double (*perimeter)(Shape* self);
    void (*draw)(Shape* self);
    void (*destroy)(Shape* self);
} ShapeVTable;

// Base Shape "class"
struct Shape {
    CoroutineBase coroutine;
    ShapeVTable* vtable;
    char* name;
    double x, y;  // position
};

void shape_base_init(Shape* self, const char* name, double x, double y) {
    self->coroutine.state = 0;
    self->coroutine.finished = 0;
    self->name = strdup(name);
    self->x = x;
    self->y = y;
}

// Circle "class" - inherits from Shape
typedef struct {
    Shape base;
    double radius;
} Circle;

double circle_area(Shape* self) {
    Circle* circle = (Circle*)self;
    return 3.14159 * circle->radius * circle->radius;
}

double circle_perimeter(Shape* self) {
    Circle* circle = (Circle*)self;
    return 2 * 3.14159 * circle->radius;
}

void circle_draw(Shape* self) {
    Circle* circle = (Circle*)self;
    printf("  Drawing circle '%s' at (%.1f, %.1f) with radius %.1f\n",
           self->name, self->x, self->y, circle->radius);
}

void circle_destroy(Shape* self) {
    free(self->name);
    free(self);
}

static ShapeVTable circle_vtable = {
    .area = circle_area,
    .perimeter = circle_perimeter,
    .draw = circle_draw,
    .destroy = circle_destroy
};

Circle* circle_create(const char* name, double x, double y, double radius) {
    Circle* circle = (Circle*)malloc(sizeof(Circle));
    shape_base_init(&circle->base, name, x, y);
    circle->base.vtable = &circle_vtable;
    circle->radius = radius;
    return circle;
}

// Rectangle "class" - inherits from Shape
typedef struct {
    Shape base;
    double width;
    double height;
} Rectangle;

double rectangle_area(Shape* self) {
    Rectangle* rect = (Rectangle*)self;
    return rect->width * rect->height;
}

double rectangle_perimeter(Shape* self) {
    Rectangle* rect = (Rectangle*)self;
    return 2 * (rect->width + rect->height);
}

void rectangle_draw(Shape* self) {
    Rectangle* rect = (Rectangle*)self;
    printf("  Drawing rectangle '%s' at (%.1f, %.1f) with dimensions %.1fx%.1f\n",
           self->name, self->x, self->y, rect->width, rect->height);
}

void rectangle_destroy(Shape* self) {
    free(self->name);
    free(self);
}

static ShapeVTable rectangle_vtable = {
    .area = rectangle_area,
    .perimeter = rectangle_perimeter,
    .draw = rectangle_draw,
    .destroy = rectangle_destroy
};

Rectangle* rectangle_create(const char* name, double x, double y, double width, double height) {
    Rectangle* rect = (Rectangle*)malloc(sizeof(Rectangle));
    shape_base_init(&rect->base, name, x, y);
    rect->base.vtable = &rectangle_vtable;
    rect->width = width;
    rect->height = height;
    return rect;
}


// SECTION 3: Iterator Pattern with Coroutines

typedef struct {
    CoroutineBase coroutine;
    Shape** shapes;
    int count;
    int current;
    Shape* current_shape;
} ShapeIterator;

void shape_iterator_init(ShapeIterator* self, Shape** shapes, int count) {
    self->coroutine.state = 0;
    self->coroutine.finished = 0;
    self->shapes = shapes;
    self->count = count;
    self->current = 0;
    self->current_shape = NULL;
}

// Coroutine-based iterator that yields each shape
int shape_iterator_next(ShapeIterator* self) {
    CO_BEGIN(&self->coroutine);
    
    while (self->current < self->count) {
        self->current_shape = self->shapes[self->current];
        self->current++;
        CO_YIELD(&self->coroutine);
    }
    
    CO_END(&self->coroutine);
}


// SECTION 4: State Machine - Animation Controller

typedef enum {
    ANIM_IDLE,
    ANIM_PLAYING,
    ANIM_PAUSED,
    ANIM_REWINDING,
    ANIM_STOPPED
} AnimationState;

typedef struct {
    CoroutineBase coroutine;
    AnimationState state;
    Shape** shapes;
    int shape_count;
    int current_frame;
    int max_frames;
    double speed;
} AnimationController;

void animation_controller_init(AnimationController* self, Shape** shapes, int count, int max_frames) {
    self->coroutine.state = 0;
    self->coroutine.finished = 0;
    self->state = ANIM_IDLE;
    self->shapes = shapes;
    self->shape_count = count;
    self->current_frame = 0;
    self->max_frames = max_frames;
    self->speed = 1.0;
}

void animation_controller_play(AnimationController* self) {
    self->state = ANIM_PLAYING;
}

void animation_controller_pause(AnimationController* self) {
    self->state = ANIM_PAUSED;
}

void animation_controller_stop(AnimationController* self) {
    self->state = ANIM_STOPPED;
    self->current_frame = 0;
}

// Coroutine that runs the animation state machine
int animation_controller_update(AnimationController* self) {
    CO_BEGIN(&self->coroutine);
    
    while (1) {
        switch (self->state) {
            case ANIM_IDLE:
                printf("  Animation: Idle (frame %d/%d)\n", 
                       self->current_frame, self->max_frames);
                CO_YIELD(&self->coroutine);
                break;
                
            case ANIM_PLAYING:
                if (self->current_frame < self->max_frames) {
                    printf("  Animation: Playing frame %d/%d\n", 
                           self->current_frame, self->max_frames);
                    self->current_frame++;
                    CO_YIELD(&self->coroutine);
                } else {
                    printf("  Animation: Finished!\n");
                    self->state = ANIM_IDLE;
                    CO_YIELD(&self->coroutine);
                }
                break;
                
            case ANIM_PAUSED:
                printf("  Animation: Paused at frame %d/%d\n", 
                       self->current_frame, self->max_frames);
                CO_YIELD(&self->coroutine);
                break;
                
            case ANIM_REWINDING:
                if (self->current_frame > 0) {
                    printf("  Animation: Rewinding to frame %d/%d\n", 
                           self->current_frame, self->max_frames);
                    self->current_frame--;
                    CO_YIELD(&self->coroutine);
                } else {
                    printf("  Animation: Back to start\n");
                    self->state = ANIM_IDLE;
                    CO_YIELD(&self->coroutine);
                }
                break;
                
            case ANIM_STOPPED:
                printf("  Animation: Stopped\n");
                CO_YIELD(&self->coroutine);
                break;
        }
    }
    
    CO_END(&self->coroutine);
}


// SECTION 5: Generator Pattern - Fibonacci Sequence

typedef struct {
    CoroutineBase coroutine;
    int a, b;
    int current;
    int max_count;
    int count;
} FibonacciGenerator;

void fibonacci_init(FibonacciGenerator* self, int max_count) {
    self->coroutine.state = 0;
    self->coroutine.finished = 0;
    self->a = 0;
    self->b = 1;
    self->current = 0;
    self->max_count = max_count;
    self->count = 0;
}

int fibonacci_next(FibonacciGenerator* self) {
    CO_BEGIN(&self->coroutine);
    
    self->current = self->a;
    CO_YIELD(&self->coroutine);
    self->count++;
    
    self->current = self->b;
    CO_YIELD(&self->coroutine);
    self->count++;
    
    while (self->count < self->max_count) {
        int next = self->a + self->b;
        self->a = self->b;
        self->b = next;
        self->current = next;
        self->count++;
        CO_YIELD(&self->coroutine);
    }
    
    CO_END(&self->coroutine);
}


// SECTION 6: Producer-Consumer Pattern

#define BUFFER_SIZE 8

typedef struct {
    CoroutineBase coroutine;
    int buffer[BUFFER_SIZE];
    int count;
    int produce_count;
    int current_value;
} Producer;

void producer_init(Producer* self, int start_value, int produce_count) {
    self->coroutine.state = 0;
    self->coroutine.finished = 0;
    self->count = 0;
    self->produce_count = produce_count;
    self->current_value = start_value;
}

int producer_produce(Producer* self) {
    CO_BEGIN(&self->coroutine);
    
    while (self->count < self->produce_count) {
        printf("  Producer: Generating value %d\n", self->current_value);
        self->buffer[self->count % BUFFER_SIZE] = self->current_value;
        self->count++;
        self->current_value += 10;
        CO_YIELD(&self->coroutine);
    }
    
    printf("  Producer: Finished producing\n");
    
    CO_END(&self->coroutine);
}

typedef struct {
    CoroutineBase coroutine;
    Producer* producer;
    int consumed;
    int current_value;
} Consumer;

void consumer_init(Consumer* self, Producer* producer) {
    self->coroutine.state = 0;
    self->coroutine.finished = 0;
    self->producer = producer;
    self->consumed = 0;
    self->current_value = 0;
}

int consumer_consume(Consumer* self) {
    CO_BEGIN(&self->coroutine);
    
    while (self->consumed < self->producer->count || !self->producer->coroutine.finished) {
        if (self->consumed < self->producer->count) {
            self->current_value = self->producer->buffer[self->consumed % BUFFER_SIZE];
            printf("  Consumer: Consumed value %d\n", self->current_value);
            self->consumed++;
            CO_YIELD(&self->coroutine);
        } else {
            printf("  Consumer: Waiting for data...\n");
            CO_YIELD(&self->coroutine);
        }
    }
    
    printf("  Consumer: Finished consuming\n");
    
    CO_END(&self->coroutine);
}


// SECTION 7: Task Scheduler with Priorities

typedef struct Task Task;

typedef struct {
    void (*execute)(Task* self);
    void (*destroy)(Task* self);
} TaskVTable;

struct Task {
    CoroutineBase coroutine;
    TaskVTable* vtable;
    char* name;
    int priority;
    int work_remaining;
};

void task_base_init(Task* self, const char* name, int priority, int work_remaining) {
    self->coroutine.state = 0;
    self->coroutine.finished = 0;
    self->name = strdup(name);
    self->priority = priority;
    self->work_remaining = work_remaining;
}

// Computation Task
typedef struct {
    Task base;
    int computation_steps;
} ComputationTask;

void computation_task_execute(Task* self) {
    ComputationTask* task = (ComputationTask*)self;
    
    if (task->base.work_remaining > 0) {
        printf("    Task '%s' (priority %d): Computing step %d/%d\n",
               task->base.name, task->base.priority,
               task->computation_steps - task->base.work_remaining + 1,
               task->computation_steps);
        task->base.work_remaining--;
    }
}

void computation_task_destroy(Task* self) {
    free(self->name);
    free(self);
}

static TaskVTable computation_task_vtable = {
    .execute = computation_task_execute,
    .destroy = computation_task_destroy
};

ComputationTask* computation_task_create(const char* name, int priority, int steps) {
    ComputationTask* task = (ComputationTask*)malloc(sizeof(ComputationTask));
    task_base_init(&task->base, name, priority, steps);
    task->base.vtable = &computation_task_vtable;
    task->computation_steps = steps;
    return task;
}

// I/O Task
typedef struct {
    Task base;
    int io_operations;
} IOTask;

void io_task_execute(Task* self) {
    IOTask* task = (IOTask*)self;
    
    if (task->base.work_remaining > 0) {
        printf("    Task '%s' (priority %d): I/O operation %d/%d\n",
               task->base.name, task->base.priority,
               task->io_operations - task->base.work_remaining + 1,
               task->io_operations);
        task->base.work_remaining--;
    }
}

void io_task_destroy(Task* self) {
    free(self->name);
    free(self);
}

static TaskVTable io_task_vtable = {
    .execute = io_task_execute,
    .destroy = io_task_destroy
};

IOTask* io_task_create(const char* name, int priority, int operations) {
    IOTask* task = (IOTask*)malloc(sizeof(IOTask));
    task_base_init(&task->base, name, priority, operations);
    task->base.vtable = &io_task_vtable;
    task->io_operations = operations;
    return task;
}

// Scheduler
#define MAX_TASKS 16

typedef struct {
    Task* tasks[MAX_TASKS];
    int task_count;
} Scheduler;

void scheduler_init(Scheduler* self) {
    self->task_count = 0;
}

void scheduler_add_task(Scheduler* self, Task* task) {
    if (self->task_count < MAX_TASKS) {
        self->tasks[self->task_count++] = task;
    }
}

void scheduler_run(Scheduler* self) {
    int active_tasks = self->task_count;
    
    while (active_tasks > 0) {
        active_tasks = 0;
        
        // Sort tasks by priority (simple bubble sort)
        for (int i = 0; i < self->task_count - 1; i++) {
            for (int j = 0; j < self->task_count - i - 1; j++) {
                if (self->tasks[j]->priority < self->tasks[j + 1]->priority) {
                    Task* temp = self->tasks[j];
                    self->tasks[j] = self->tasks[j + 1];
                    self->tasks[j + 1] = temp;
                }
            }
        }
        
        // Execute each task once
        for (int i = 0; i < self->task_count; i++) {
            Task* task = self->tasks[i];
            if (task->work_remaining > 0) {
                task->vtable->execute(task);
                active_tasks++;
            }
        }
        
        if (active_tasks > 0) {
            printf("  ---\n");
        }
    }
}

void scheduler_cleanup(Scheduler* self) {
    for (int i = 0; i < self->task_count; i++) {
        self->tasks[i]->vtable->destroy(self->tasks[i]);
    }
}


// MAIN - Demonstration

int main() {
    printf("Object-Oriented Programming in C with Coroutines Demo\n\n");
    
    // Demo 1: Polymorphism with Shape Hierarchy
    printf(" > DEMO 1: Polymorphism & Inheritance\n\n");
    
    Shape* shapes[5];
    shapes[0] = (Shape*)circle_create("Sun", 100, 100, 50);
    shapes[1] = (Shape*)rectangle_create("Building", 200, 50, 80, 120);
    shapes[2] = (Shape*)circle_create("Moon", 300, 80, 30);
    shapes[3] = (Shape*)rectangle_create("Window", 220, 100, 20, 30);
    shapes[4] = (Shape*)circle_create("Planet", 150, 200, 40);
    
    printf("Drawing all shapes (polymorphic behavior):\n");
    for (int i = 0; i < 5; i++) {
        shapes[i]->vtable->draw(shapes[i]);
        printf("    Area: %.2f, Perimeter: %.2f\n",
               shapes[i]->vtable->area(shapes[i]),
               shapes[i]->vtable->perimeter(shapes[i]));
    }
    
    printf("\n\n\n");
    

    // Demo 2: Iterator Pattern
    printf(" > DEMO 2: Coroutine-Based Iterator Pattern\n\n");
    
    ShapeIterator iterator;
    shape_iterator_init(&iterator, shapes, 5);
    
    printf("Iterating through shapes:\n");
    int index = 0;
    while (shape_iterator_next(&iterator)) {
        Shape* shape = iterator.current_shape;
        printf("  [%d] %s at (%.1f, %.1f)\n", 
               ++index, shape->name, shape->x, shape->y);
    }
    
    printf("\n\n\n");
    

    // Demo 3: State Machine - Animation Controller
    printf(" > DEMO 3: State Machine with Coroutines\n\n");
    
    AnimationController animator;
    animation_controller_init(&animator, shapes, 5, 10);
    
    printf("Starting animation controller:\n");
    animation_controller_update(&animator);
    animation_controller_update(&animator);
    
    animation_controller_play(&animator);
    for (int i = 0; i < 4; i++) {
        animation_controller_update(&animator);
    }
    
    animation_controller_pause(&animator);
    animation_controller_update(&animator);
    animation_controller_update(&animator);
    
    animation_controller_play(&animator);
    for (int i = 0; i < 8; i++) {
        animation_controller_update(&animator);
    }
    
    printf("\n\n\n");
    

    // Demo 4: Generator Pattern - Fibonacci
    printf(" > DEMO 4: Generator Pattern (Fibonacci)\n\n");
    
    FibonacciGenerator fib;
    fibonacci_init(&fib, 10);
    
    printf("Fibonacci sequence:\n  ");
    while (fibonacci_next(&fib)) {
        printf("%d ", fib.current);
    }
    printf("\n");
    
    printf("\n\n\n");
    

    // Demo 5: Producer-Consumer Pattern
    printf(" > DEMO 5: Producer-Consumer Pattern\n\n");
    
    Producer producer;
    producer_init(&producer, 100, 5);
    
    Consumer consumer;
    consumer_init(&consumer, &producer);
    
    printf("Running producer-consumer:\n");
    for (int i = 0; i < 12; i++) {
        printf("  [Cycle %d]\n", i + 1);
        producer_produce(&producer);
        consumer_consume(&consumer);
    }
    
    printf("\n\n\n");
    

    // Demo 6: Task Scheduler with Priorities
    printf(" > DEMO 6: Task Scheduler (Priority-Based)\n\n");
    
    Scheduler scheduler;
    scheduler_init(&scheduler);
    
    scheduler_add_task(&scheduler, (Task*)computation_task_create("Matrix Multiply", 10, 3));
    scheduler_add_task(&scheduler, (Task*)io_task_create("Read File", 5, 4));
    scheduler_add_task(&scheduler, (Task*)computation_task_create("Sort Array", 8, 2));
    scheduler_add_task(&scheduler, (Task*)io_task_create("Write Database", 7, 3));
    
    printf("Scheduler running tasks (highest priority first):\n");
    scheduler_run(&scheduler);
    
    printf("All tasks completed!\n");
    scheduler_cleanup(&scheduler);
    
    printf("\n\n\n");
    
    // Cleanup shapes
    for (int i = 0; i < 5; i++) {
        shapes[i]->vtable->destroy(shapes[i]);
    }
    
    printf("Done.\n\n");
    
    return 0;
}
