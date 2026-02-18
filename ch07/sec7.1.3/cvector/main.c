#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include "vector.h"

void simulate_sensor_readings() {
    printf("-- Temperature Sensor Data Collection --\n\n");
    
    Vector* readings = vector_create();
    srand(time(NULL));
    
    // Simulate 20 temperature readings
    printf("Collecting readings:\n");
    for (int i = 0; i < 20; i++) {
        int temp = 15 + (rand() % 20); // 15-34°C
        vector_push_back(readings, temp);
        if (i < 5) printf("  Reading %2d: %d°C (capacity: %d)\n", 
                          i+1, temp, vector_capacity(readings));
    }
    printf("  ... (15 more readings collected)\n");
    printf("  Final capacity after auto-growth: %d\n\n", 
           vector_capacity(readings));
    
    // Calculate average
    int sum = 0;
    for (int i = 0; i < vector_size(readings); i++) {
        int val;
        vector_get(readings, i, &val);
        sum += val;
    }
    
    printf("Statistics:\n");
    printf("  Total readings: %d\n", vector_size(readings));
    printf("  Average temp:   %.1f°C\n", sum / (float)vector_size(readings));
    
    vector_destroy(readings);
}

int main(void) {
    simulate_sensor_readings();
    return 0;
}
