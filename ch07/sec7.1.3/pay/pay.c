#include <stdio.h>
#include <string.h>

// -  Result type  -
typedef struct {
    int  success;
    char transaction_id[64];
    char message[256];
} PaymentResult;

// -- Strategy ADT: struct of function pointers --
// This IS the interface--equivalent to an abstract class
typedef struct PaymentStrategy {
    const char* name;

    // Function pointers define the "methods"
    int           (*validate)(struct PaymentStrategy* self, double amount);
    PaymentResult (*charge)  (struct PaymentStrategy* self, double amount, const char* desc);
    PaymentResult (*refund)  (struct PaymentStrategy* self, const char* txn_id, double amount);

    // Internal state (opaque to users of the ADT)
    void* _data;
} PaymentStrategy;


// -- Concrete Strategy: Credit Card --
typedef struct { char last_four[5]; } CreditCardData;

int cc_validate(PaymentStrategy* self, double amount) {
    return amount > 0 && amount < 10000;
}

PaymentResult cc_charge(PaymentStrategy* self, double amount, const char* desc) {
    CreditCardData* d = (CreditCardData*)self->_data;
    PaymentResult r;
    if (!cc_validate(self, amount)) {
        r.success = 0;
        strcpy(r.transaction_id, "");
        snprintf(r.message, sizeof(r.message), "Validation failed");
        return r;
    }
    r.success = 1;
    snprintf(r.transaction_id, sizeof(r.transaction_id), "CC-%04d", (int)(amount * 7) % 9999);
    snprintf(r.message, sizeof(r.message),
             "Charged $%.2f to card ending %s", amount, d->last_four);
    return r;
}

PaymentResult cc_refund(PaymentStrategy* self, const char* txn_id, double amount) {
    PaymentResult r = { .success = 1 };
    snprintf(r.transaction_id, sizeof(r.transaction_id), "REF-%s", txn_id);
    snprintf(r.message, sizeof(r.message), "Refunded $%.2f for %s", amount, txn_id);
    return r;
}

PaymentStrategy make_credit_card(const char* last_four) {
    static CreditCardData data;
    strncpy(data.last_four, last_four, 4);
    data.last_four[4] = '\0';

    PaymentStrategy s;
    s.name     = "Credit Card";
    s.validate = cc_validate;
    s.charge   = cc_charge;
    s.refund   = cc_refund;
    s._data    = &data;
    return s;
}


// -- Concrete Strategy: PayPal --
typedef struct { char email[128]; } PayPalData;

int pp_validate(PaymentStrategy* self, double amount) { return amount > 0; }

PaymentResult pp_charge(PaymentStrategy* self, double amount, const char* desc) {
    PayPalData* d = (PayPalData*)self->_data;
    PaymentResult r = { .success = 1 };
    snprintf(r.transaction_id, sizeof(r.transaction_id), "PP-%04d", (int)(amount * 13) % 9999);
    snprintf(r.message, sizeof(r.message),
             "PayPal: $%.2f sent via %s", amount, d->email);
    return r;
}

PaymentResult pp_refund(PaymentStrategy* self, const char* txn_id, double amount) {
    PaymentResult r = { .success = 1 };
    snprintf(r.transaction_id, sizeof(r.transaction_id), "PP-REF-%s", txn_id);
    snprintf(r.message, sizeof(r.message), "PayPal refund: $%.2f", amount);
    return r;
}

PaymentStrategy make_paypal(const char* email) {
    static PayPalData data;
    strncpy(data.email, email, 127);

    PaymentStrategy s;
    s.name     = "PayPal";
    s.validate = pp_validate;
    s.charge   = pp_charge;
    s.refund   = pp_refund;
    s._data    = &data;
    return s;
}


// -- Context: Shopping Cart --
// Works with any PaymentStrategy--doesn't know which one!
void checkout(PaymentStrategy* strategy, double amount, const char* description) {
    printf("\n[%s] Processing $%.2f...\n", strategy->name, amount);

    if (!strategy->validate(strategy, amount)) {
        printf("  (-) Validation failed\n");
        return;
    }

    PaymentResult result = strategy->charge(strategy, amount, description);
    printf("  %s: %s\n", result.success ? "(+)" : "(-)", result.message);
    if (result.success && strlen(result.transaction_id) > 0) {
        printf("  TXN: %s\n", result.transaction_id);
    }
}


//
int main(void) {
    PaymentStrategy cc  = make_credit_card("4321");
    PaymentStrategy pp  = make_paypal("user@example.com");

    // Array of strategies--polymorphism in pure C!
    PaymentStrategy* strategies[] = { &cc, &pp, NULL };

    printf(". C Strategy Pattern Demo .\n");

    for (int i = 0; strategies[i] != NULL; i++) {
        checkout(strategies[i], 149.99, "Keyboard + Mousepad");
    }

    // Refund via credit card
    printf("\n--- Refund ---\n");
    PaymentResult refund = cc.refund(&cc, "CC-1049", 149.99);
    printf("  %s\n", refund.message);

    return 0;
}

