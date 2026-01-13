// main.c
// Elliptic Curve demo: y^2 = x^3 + x + 6 (mod 17)
// Educational implementation

#include <stdio.h>
#include <stdint.h>

#define P 17        // Prime field
#define A 1
#define B 6

typedef struct {
    int x;
    int y;
    int infinity;   // 1 = point at infinity, 0 = normal point
} Point;

/* Check if a point is on the curve */
int is_on_curve(Point p) {
    if (p.infinity) return 1;
    int left  = (p.y * p.y) % P;
    int right = (p.x*p.x*p.x + A*p.x + B) % P;
    if (left < 0)  left += P;
    if (right < 0) right += P;
    return left == right;
}

/* Modular inverse using extended Euclidean algorithm */
int mod_inverse(int a, int m) {
    a %= m;
    if (a < 0) a += m;

    int m0 = m, t, q;
    int x0 = 0, x1 = 1;

    if (m == 1) return 0;

    while (a > 1) {
        q = a / m;
        t = m;
        m = a % m;
        a = t;

        t = x0;
        x0 = x1 - q * x0;
        x1 = t;
    }

    if (x1 < 0)
        x1 += m0;

    return x1;
}

/* Point doubling */
Point point_double(Point p) {
    if (p.infinity) return p;

    // If y == 0, tangent is vertical → infinity
    if (p.y == 0) {
        Point inf = {0, 0, 1};
        return inf;
    }

    Point r;
    int num = (3 * p.x * p.x + A) % P;
    int den = mod_inverse(2 * p.y, P);
    int lambda = (num * den) % P;

    r.x = (lambda * lambda - 2 * p.x) % P;
    r.y = (lambda * (p.x - r.x) - p.y) % P;

    if (r.x < 0) r.x += P;
    if (r.y < 0) r.y += P;
    r.infinity = 0;
    return r;
}

/* Point addition */
Point point_add(Point p1, Point p2) {
    if (p1.infinity) return p2;
    if (p2.infinity) return p1;

    // P + (-P) = infinity
    if (p1.x == p2.x && (p1.y + p2.y) % P == 0) {
        Point inf = {0, 0, 1};
        return inf;
    }

    // P + P = 2P
    if (p1.x == p2.x && p1.y == p2.y) {
        return point_double(p1);
    }

    Point r;
    int dx = (p2.x - p1.x) % P;
    if (dx < 0) dx += P;

    int dy = (p2.y - p1.y) % P;
    if (dy < 0) dy += P;

    int lambda = (dy * mod_inverse(dx, P)) % P;

    r.x = (lambda * lambda - p1.x - p2.x) % P;
    r.y = (lambda * (p1.x - r.x) - p1.y) % P;

    if (r.x < 0) r.x += P;
    if (r.y < 0) r.y += P;
    r.infinity = 0;
    return r;
}

/* Scalar multiplication (double-and-add) */
Point scalar_mult(int k, Point g) {
    Point r = {0, 0, 1};  // Infinity
    Point t = g;

    while (k > 0) {
        if (k & 1)
            r = point_add(r, t);

        t = point_double(t);
        k >>= 1;
    }
    return r;
}

/* Print a point */
void print_point(Point p) {
    if (p.infinity)
        printf("INF");
    else
        printf("(%2d, %2d)", p.x, p.y);
}

int main(void) {
    printf("Elliptic Curve Demo\n");
    printf("Curve: y^2 = x^3 + x + 6 (mod %d)\n\n", P);

    // Valid base point for this curve:
    // (2,4) since:
    // 4^2 = 16
    // 2^3 + 2 + 6 = 8 + 2 + 6 = 16  (mod 17)
    Point G = {2, 4, 0};

    if (!is_on_curve(G)) {
        printf("Base point is NOT on the curve!\n");
        return 1;
    }

    printf("Base point G = ");
    print_point(G);
    printf("\n\n");

    printf("Multiples of G:\n");
    printf("-------------------------------\n");

    Point Pk = G;
    for (int i = 1; i <= 20; i++) {
        printf("%2dG = ", i);
        print_point(Pk);
        printf("\n");

        Pk = point_add(Pk, G);
        if (Pk.infinity) {
            printf("%2dG = INF  (cycle reached)\n", i + 1);
            break;
        }
    }

    printf("\nScalar multiplication example:\n");
    int k = 7;
    Point Q = scalar_mult(k, G);

    printf("k = %d\n", k);
    printf("Q = kG = ");
    print_point(Q);
    printf("\n");

    printf("\nThis demonstrates:\n");
    printf("- Point addition\n");
    printf("- Point doubling\n");
    printf("- Scalar multiplication\n");
    printf("- Finite cyclic group behavior\n");

    return 0;
}

