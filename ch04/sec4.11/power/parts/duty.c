
// maybe impl? duty cycle?

int main() {
    while (true) {

        // read temperature sensor
        read_temperature_sensor();

        // sleep 1 second before next reading
        sleep_ms(1000);
    }
}
