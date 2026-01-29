int phi_test(int x) {
    int a;
    a = 5;
    if (x > 0) {
        a = 10;
    } else {
        a = 20;
    }
    return a;
}

int main() {
    return phi_test(5);
}
