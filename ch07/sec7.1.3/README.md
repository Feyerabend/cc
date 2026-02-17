
## Abstract Data Types (ADTs)

An *Abstract Data Type (ADT)* is a *mathematical model* for data types,
defined by its *behaviour* (operations it supports) rather than its
*implementation* (how it stores data internally).

Think of an ADT as a *contract* or *interface*:
- It says *what* you can do with the data
- It says *nothing* about *how* it's done internally

This separation is the core idea behind *abstraction* in computer science.

The *user* of an ADT only cares about the operations.
The *implementer* decides how to store and manage data.
This is the principle of *encapsulation*.



### Why ADTs Are Important

| Benefit | Explanation |
|---------|-------------|
| *Encapsulation* | Internal details are hidden; users can't accidentally corrupt state |
| *Interchangeability* | You can swap implementations without changing calling code |
| *Modularity* | Large systems are built from well-defined, testable pieces |
| *Reusability* | An ADT written once can be used in many different programs |
| *Correctness* | Invariants (rules) are enforced by the ADT itself |
| *Testability* | You can test the interface independently of the implementation |



### Classic ADTs and Their Operations

| ADT | Core Operations | Property |
|-----|-----------------|----------|
| *Stack* | push, pop, peek, isEmpty | LIFO |
| *Queue* | enqueue, dequeue, front, isEmpty | FIFO |
| *List* | insert, delete, get, size | Ordered sequence |
| *Set* | add, remove, contains, union | No duplicates |
| *Map / Dictionary* | put, get, remove, containsKey | Key-value pairs |
| *Priority Queue* | insert, extractMin/Max, peek | Priority ordering |
| *Graph* | addVertex, addEdge, neighbors | Relationships |



### ADTs in C: Manual Abstraction

C has no classes, so ADTs are implemented using *structs + function pointers*
or *opaque pointers*. This forces discipline: you define a public interface
in a header file and hide the implementation in a `.c` file.


#### Stack ADT in C (Array-based implementation)

*`stack.h`--The public interface (the "contract")*

```c
#ifndef STACK_H
#define STACK_H

// Opaque pointer: the user sees Stack*, but NOT what's inside it.
// This enforces true encapsulation in C.
typedef struct Stack Stack;

// Constructor / Destructor
Stack* stack_create(int capacity);
void stack_destroy(Stack* s);

// Operations--this IS the ADT definition
int stack_push(Stack* s, int value);   // returns 1 on success, 0 on overflow
int stack_pop(Stack* s, int* out);     // returns 1 on success, 0 on underflow
int stack_peek(Stack* s, int* out);    // returns 1 on success, 0 if empty
int stack_is_empty(Stack* s);
int stack_size(Stack* s);

#endif // STACK_H
```

*`stack.c`--Implementation A: Array-based (hidden from user)*

```c
#include <stdlib.h>
#include "stack.h"

// The real struct definition--hidden in the .c file
struct Stack {
    int* data;
    int  top;
    int  capacity;
};

Stack* stack_create(int capacity) {
    Stack* s = malloc(sizeof(Stack));
    if (!s) return NULL;
    s->data = malloc(sizeof(int) * capacity);
    if (!s->data) { free(s); return NULL; }
    s->top = -1;
    s->capacity = capacity;
    return s;
}

void stack_destroy(Stack* s) {
    if (!s) return;
    free(s->data);
    free(s);
}

int stack_push(Stack* s, int value) {
    if (s->top >= s->capacity - 1) return 0; // overflow
    s->data[++(s->top)] = value;
    return 1;
}

int stack_pop(Stack* s, int* out) {
    if (s->top < 0) return 0; // underflow
    *out = s->data[(s->top)--];
    return 1;
}

int stack_peek(Stack* s, int* out) {
    if (s->top < 0) return 0;
    *out = s->data[s->top];
    return 1;
}

int stack_is_empty(Stack* s) { return s->top < 0; }
int stack_size(Stack* s)     { return s->top + 1; }
```

*`stack_linked.c`--Implementation B: Linked-list-based (SAME interface!)*

```c
#include <stdlib.h>
#include "stack.h"

// Completely different internal structure--but same interface!
typedef struct Node {
    int value;
    struct Node* next;
} Node;

struct Stack {
    Node* head;
    int   size;
    int   capacity; // unused here, but kept for interface compatibility
};

Stack* stack_create(int capacity) {
    Stack* s = malloc(sizeof(Stack));
    if (!s) return NULL;
    s->head = NULL;
    s->size = 0;
    s->capacity = capacity;
    return s;
}

void stack_destroy(Stack* s) {
    Node* curr = s->head;
    while (curr) {
        Node* next = curr->next;
        free(curr);
        curr = next;
    }
    free(s);
}

int stack_push(Stack* s, int value) {
    Node* n = malloc(sizeof(Node));
    if (!n) return 0;
    n->value = value;
    n->next  = s->head;
    s->head  = n;
    s->size++;
    return 1;
}

int stack_pop(Stack* s, int* out) {
    if (!s->head) return 0;
    Node* old = s->head;
    *out = old->value;
    s->head = old->next;
    free(old);
    s->size--;
    return 1;
}

int stack_peek(Stack* s, int* out) {
    if (!s->head) return 0;
    *out = s->head->value;
    return 1;
}

int stack_is_empty(Stack* s) { return s->head == NULL; }
int stack_size(Stack* s)     { return s->size; }
```

*`main.c`--User code works with EITHER implementation without modification*

```c
#include <stdio.h>
#include "stack.h"

// Real-world use case: balanced parentheses checker
int is_balanced(const char* expr) {
    Stack* s = stack_create(256);
    int balanced = 1;
    int val;

    for (int i = 0; expr[i] != '\0'; i++) {
        char c = expr[i];
        if (c == '(' || c == '[' || c == '{') {
            stack_push(s, (int)c);
        } else if (c == ')' || c == ']' || c == '}') {
            if (!stack_pop(s, &val)) { balanced = 0; break; }
            if ((c == ')' && val != '(') ||
                (c == ']' && val != '[') ||
                (c == '}' && val != '{')) {
                balanced = 0;
                break;
            }
        }
    }

    if (!stack_is_empty(s)) balanced = 0;
    stack_destroy(s);
    return balanced;
}

int main(void) {
    const char* exprs[] = {
        "({[a + b] * (c - d)})",
        "({[mismatched)}",
        "((()))",
        "((("
    };

    for (int i = 0; i < 4; i++) {
        printf("%-30s -> %s\n", exprs[i],
               is_balanced(exprs[i]) ? "BALANCED" : "UNBALANCED");
    }
    return 0;
}
```

To compile the program using the array-based
stack implementation (from `stack.c`):

```
gcc main.c stack.c -o balanced_checker
```

To compile using the linked-list stack
implementation (from `stack_linked.c`):

```
gcc main.c stack_linked.c -o balanced_checker
```

In both cases, run the executable with `./balanced_checker`
(assuming a Unix-like environment; adjust for Windows if needed).
Note that you cannot compile both `stack.c` and `stack_linked.c` together,
as they provide duplicate function definitions.


*Output:*
```
({[a + b] * (c - d)})          -> BALANCED
({[mismatched)}                -> UNBALANCED
((()))                         -> BALANCED
(((                            -> UNBALANCED
```

Notice: `is_balanced()` never touches `s->data` or `s->top` directly.
It only uses the interface. You can swap `stack.c` for `stack_linked.c`
and `main.c` compiles and runs identically--*that's ADT power*.



### ADTs in Python: Native Support via Classes & ABCs

Python makes ADTs much easier to express using *Abstract Base Classes (ABC)*
from the `abc` module, which enforces that all required operations are implemented.

#### Defining the ADT with ABC

```python
from abc import ABC, abstractmethod
from typing import TypeVar, Generic, Optional

T = TypeVar('T')

class StackADT(ABC, Generic[T]):
    """
    Abstract Base Class defining the Stack ADT contract.
    Any class that inherits this MUST implement all abstract methods.
    """

    @abstractmethod
    def push(self, value: T) -> None:
        """Add an element to the top of the stack."""
        ...

    @abstractmethod
    def pop(self) -> T:
        """Remove and return the top element. Raises IndexError if empty."""
        ...

    @abstractmethod
    def peek(self) -> T:
        """Return (but don't remove) the top element. Raises IndexError if empty."""
        ...

    @abstractmethod
    def is_empty(self) -> bool:
        """Return True if the stack has no elements."""
        ...

    @abstractmethod
    def size(self) -> int:
        """Return the number of elements in the stack."""
        ...
```

#### Implementation A: Array-based (using Python list)

```python
class ArrayStack(StackADT[T]):
    """Concrete implementation using a Python list as the backing store."""

    def __init__(self) -> None:
        self._data: list[T] = []

    def push(self, value: T) -> None:
        self._data.append(value)           # O(1) amortized

    def pop(self) -> T:
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self._data.pop()            # O(1)

    def peek(self) -> T:
        if self.is_empty():
            raise IndexError("peek at empty stack")
        return self._data[-1]              # O(1)

    def is_empty(self) -> bool:
        return len(self._data) == 0

    def size(self) -> int:
        return len(self._data)

    def __repr__(self) -> str:
        return f"ArrayStack({self._data})"
```

#### Implementation B: Linked-list-based

```python
from dataclasses import dataclass

@dataclass
class _Node:
    value: object
    next: Optional['_Node'] = None

class LinkedStack(StackADT[T]):
    """Concrete implementation using a singly linked list."""

    def __init__(self) -> None:
        self._head: Optional[_Node] = None
        self._size: int = 0

    def push(self, value: T) -> None:
        self._head = _Node(value=value, next=self._head)
        self._size += 1

    def pop(self) -> T:
        if self.is_empty():
            raise IndexError("pop from empty stack")
        value = self._head.value
        self._head = self._head.next
        self._size -= 1
        return value

    def peek(self) -> T:
        if self.is_empty():
            raise IndexError("peek at empty stack")
        return self._head.value

    def is_empty(self) -> bool:
        return self._head is None

    def size(self) -> int:
        return self._size

    def __repr__(self) -> str:
        items, curr = [], self._head
        while curr:
            items.append(curr.value)
            curr = curr.next
        return f"LinkedStack({items})"
```

#### Polymorphic client code: works with any Stack implementation

```python
def evaluate_rpn(tokens: list[str], stack: StackADT[float]) -> float:
    """
    Evaluate a Reverse Polish Notation expression.
    Uses the StackADT interface: works with ArrayStack OR LinkedStack.
    e.g. "3 4 + 2 * 7 /" -> ((3+4)*2)/7 = 2.0
    """
    ops = {
        '+': lambda a, b: a + b,
        '-': lambda a, b: a - b,
        '*': lambda a, b: a * b,
        '/': lambda a, b: a / b,
    }
    for token in tokens:
        if token in ops:
            b, a = stack.pop(), stack.pop()
            stack.push(ops[token](a, b))
        else:
            stack.push(float(token))
    return stack.pop()

## Both implementations satisfy the contract--totally interchangeable
expressions = [
    ["3", "4", "+", "2", "*", "7", "/"],   ## -> 2.0
    ["5", "1", "2", "+", "4", "*", "+", "3", "-"],  ## -> 14.0
]

for tokens in expressions:
    result_array  = evaluate_rpn(tokens[:], ArrayStack())
    result_linked = evaluate_rpn(tokens[:], LinkedStack())
    print(f"{'  '.join(tokens)}")
    print(f"  ArrayStack  result: {result_array}")
    print(f"  LinkedStack result: {result_linked}")
    print(f"  Results match: {result_array == result_linked}\n")
```

*Output:*
```
3 4 + 2 * 7 /
  ArrayStack  result: 2.0
  LinkedStack result: 2.0
  Results match: True

5 1 2 + 4 * + 3 -
  ArrayStack  result: 14.0
  LinkedStack result: 14.0
  Results match: True
```



### Real-World Case: Strategy Design Pattern

The *Strategy Pattern* is ADTs applied to *algorithms*.
Instead of hardcoding a behaviour, you define an ADT
(the strategy interface) and inject different implementations at runtime.

*ADTs define what operations exist. Strategy pattern defines
what algorithms exist--and makes them swappable.*


#### The Scenario: A Payment System

A checkout system must support multiple payment methods: credit card,
PayPal, and cryptocurrency. New methods will be added later.
We don't want a giant `if/elif` chain.

#### Python: Strategy Pattern with ADTs

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


#  Step 1: Define the Strategy ADT (the interface)

@dataclass
class PaymentResult:
    success: bool
    transaction_id: Optional[str]
    message: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

class PaymentStrategy(ABC):
    """
    ADT: defines the contract for any payment method.
    New payment methods MUST implement this interface.
    """

    @abstractmethod
    def validate(self, amount: float) -> bool:
        """Validate that this payment method can handle the amount."""
        ...

    @abstractmethod
    def charge(self, amount: float, description: str) -> PaymentResult:
        """Execute the charge and return a result."""
        ...

    @abstractmethod
    def refund(self, transaction_id: str, amount: float) -> PaymentResult:
        """Refund a previous transaction."""
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable name of this payment method."""
        ...


#  Step 2: Concrete Strategy A: Credit Card

class CreditCardStrategy(PaymentStrategy):
    def __init__(self, card_number: str, expiry: str, cvv: str):
        self._card_number = card_number[-4:]  ## only store last 4 digits
        self._expiry = expiry
        self._cvv = cvv

    @property
    def name(self) -> str:
        return f"Credit Card (** ** ** {self._card_number})"

    def validate(self, amount: float) -> bool:
        ## Real code would check expiry date, Luhn algorithm, etc.
        return amount > 0 and amount < 10_000

    def charge(self, amount: float, description: str) -> PaymentResult:
        if not self.validate(amount):
            return PaymentResult(False, None, "Validation failed: amount out of range")
        ## Simulate API call to payment processor
        txn_id = f"CC-{hash((self._card_number, amount)) % 1_000_000:06d}"
        return PaymentResult(
            success=True,
            transaction_id=txn_id,
            message=f"Charged ${amount:.2f} to card ending {self._card_number}"
        )

    def refund(self, transaction_id: str, amount: float) -> PaymentResult:
        return PaymentResult(
            success=True,
            transaction_id=f"REF-{transaction_id}",
            message=f"Refunded ${amount:.2f} for transaction {transaction_id}"
        )


#  Step 3: Concrete Strategy B: PayPal

class PayPalStrategy(PaymentStrategy):
    def __init__(self, email: str):
        self._email = email

    @property
    def name(self) -> str:
        return f"PayPal ({self._email})"

    def validate(self, amount: float) -> bool:
        return 0 < amount < 50_000

    def charge(self, amount: float, description: str) -> PaymentResult:
        if not self.validate(amount):
            return PaymentResult(False, None, "PayPal validation failed")
        txn_id = f"PP-{hash(self._email) % 1_000_000:06d}"
        return PaymentResult(
            success=True,
            transaction_id=txn_id,
            message=f"PayPal charge of ${amount:.2f} sent to {self._email}"
        )

    def refund(self, transaction_id: str, amount: float) -> PaymentResult:
        return PaymentResult(
            success=True,
            transaction_id=f"PP-REF-{transaction_id}",
            message=f"PayPal refund of ${amount:.2f} processed"
        )


#  Step 4: Concrete Strategy C: Cryptocurrency

class CryptoStrategy(PaymentStrategy):
    def __init__(self, wallet_address: str, currency: str = "BTC"):
        self._wallet = wallet_address
        self._currency = currency

    @property
    def name(self) -> str:
        return f"{self._currency} Wallet ({self._wallet[:8]}...)"

    def validate(self, amount: float) -> bool:
        return amount > 0  ## crypto has no upper limit

    def charge(self, amount: float, description: str) -> PaymentResult:
        txn_id = f"CRYPTO-{hash(self._wallet) % 1_000_000:06d}"
        return PaymentResult(
            success=True,
            transaction_id=txn_id,
            message=f"Crypto payment of ${amount:.2f} initiated to {self._wallet[:8]}..."
        )

    def refund(self, transaction_id: str, amount: float) -> PaymentResult:
        ## Crypto refunds are manual by convention
        return PaymentResult(
            success=False,
            transaction_id=None,
            message="Crypto transactions are irreversible. Contact support for manual refund."
        )


#  STtep 5: The Context: uses the Strategy ADT

class ShoppingCart:
    """
    Context class: holds items and delegates payment to a Strategy.
    It knows NOTHING about how payment actually works.
    New payment methods can be added without touching this class.
    """

    def __init__(self) -> None:
        self._items: list[tuple[str, float]] = []
        self._payment_strategy: Optional[PaymentStrategy] = None
        self._order_history: list[PaymentResult] = []

    def add_item(self, name: str, price: float) -> None:
        self._items.append((name, price))
        print(f"  Added: {name}--${price:.2f}")

    def set_payment_strategy(self, strategy: PaymentStrategy) -> None:
        """Inject the payment strategy at runtime."""
        self._payment_strategy = strategy
        print(f"  Payment method set: {strategy.name}")

    @property
    def total(self) -> float:
        return sum(price for _, price in self._items)

    def checkout(self) -> PaymentResult:
        if not self._payment_strategy:
            raise RuntimeError("No payment strategy set!")
        if not self._items:
            raise RuntimeError("Cart is empty!")

        description = ", ".join(name for name, _ in self._items)
        print(f"\n  Processing payment of ${self.total:.2f} via {self._payment_strategy.name}...")

        result = self._payment_strategy.charge(self.total, description)
        self._order_history.append(result)

        status = "+ SUCCESS" if result.success else "✗ FAILED"
        print(f"  {status}: {result.message}")
        if result.transaction_id:
            print(f"  Transaction ID: {result.transaction_id}")
        return result


#  STEP 6: Demo

def demo():
    print("  STRATEGY PATTERN + ADT DEMO: Payment System\n")

    ## Create strategies (implementations of the PaymentStrategy ADT)
    strategies = [
        CreditCardStrategy("4111111111111234", "12/27", "123"),
        PayPalStrategy("user@example.com"),
        CryptoStrategy("1A2b3C4d5E6f7G8h9I0j", "ETH"),
    ]

    for strategy in strategies:
        print(f"\n{'-' * 50}")
        print(f"  Checking out with: {strategy.name}")
        print(f"{'-' * 50}")

        cart = ShoppingCart()
        cart.add_item("Laptop", 999.99)
        cart.add_item("Mouse", 49.99)
        cart.set_payment_strategy(strategy)   ## <-- swap strategy at runtime!
        cart.checkout()

    print(f"\n{'.' * 50}")
    print("  Adding a NEW payment method requires ZERO changes")
    print("  to ShoppingCart--just implement PaymentStrategy ADT!")
    print("." * 50)

demo()
```

*Output:*
```
  STRATEGY PATTERN + ADT DEMO: Payment System


--------------------------------------------------
  Checking out with: Credit Card (** ** ** 1234)
--------------------------------------------------
  Added: Laptop--$999.99
  Added: Mouse--$49.99
  Payment method set: Credit Card (** ** ** 1234)

  Processing payment of $1049.98 via Credit Card (** ** ** 1234)...
  + SUCCESS: Charged $1049.98 to card ending 1234
  Transaction ID: CC-984180

--------------------------------------------------
  Checking out with: PayPal (user@example.com)
--------------------------------------------------
  Added: Laptop--$999.99
  Added: Mouse--$49.99
  Payment method set: PayPal (user@example.com)

  Processing payment of $1049.98 via PayPal (user@example.com)...
  + SUCCESS: PayPal charge of $1049.98 sent to user@example.com
  Transaction ID: PP-719678

--------------------------------------------------
  Checking out with: ETH Wallet (1A2b3C4d...)
--------------------------------------------------
  Added: Laptop--$999.99
  Added: Mouse--$49.99
  Payment method set: ETH Wallet (1A2b3C4d...)

  Processing payment of $1049.98 via ETH Wallet (1A2b3C4d...)...
  + SUCCESS: Crypto payment of $1049.98 initiated to 1A2b3C4d...
  Transaction ID: CRYPTO-879193

..................................................
  Adding a NEW payment method requires ZERO changes
  to ShoppingCart--just implement PaymentStrategy ADT!
..................................................
```

#### Strategy Pattern with Function Pointers (in C)

In C, the Strategy Pattern is implemented using *structs of function pointers*--this
is actually the same mechanism that C++ uses internally for virtual method dispatch (vtables)
(see [ch05/addition](./../../ch05/addition/vtable/)).

```c
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
```

*Output:*
```
. C Strategy Pattern Demo .

[Credit Card] Processing $149.99...
  (+): Charged $149.99 to card ending 4321
  TXN: CC-1049

[PayPal] Processing $149.99...
  (+): PayPal: $149.99 sent via user@example.com
  TXN: PP-1949

--- Refund ---
  Refunded $149.99 for CC-1049
```



### ADTs and the Open/Closed Principle

The Strategy Pattern illustrates a core SOLID principle:
*Open for extension, closed for modification.*

```
WITHOUT ADTs (bad):                WITH ADTs + Strategy (good):

checkout():                        checkout(PaymentStrategy* s):
  if method == "card":               s->charge(s, amount, desc)
    process_card(...)                // Done. Nothing else needed.
  elif method == "paypal":
    process_paypal(...)            Adding Bitcoin?
  elif method == "crypto":           -> Create BitcoinStrategy
    process_crypto(...)            -> Inject it at runtime
  elif method == "bitcoin":          -> checkout() never changes
    ...                            -> Tests still pass
  # ^ Must modify this function
  # every time a new method
  # is added. Fragile!
```



### Summary Table

| Concept | C Approach | Python Approach |
|---------|------------|-----------------|
| *Define ADT interface* | Header file (`.h`) + opaque pointer | `ABC` with `@abstractmethod` |
| *Implement ADT* | `.c` file with hidden struct | Concrete class inheriting ABC |
| *Enforce interface* | Compiler checks function signatures | Python raises `TypeError` at instantiation |
| *Strategy Pattern* | Struct of function pointers (vtable) | Class implementing strategy ABC |
| *Polymorphism* | Array of `Strategy*`, call via pointer | List of strategy objects, call method |
| *Add new strategy* | New `.c` file, implement same signatures | New class, implement all abstractmethods |


### Takeaways

*ADTs give you:*
- A *contract* that separates *what* from *how*
- *Interchangeable implementations* behind a stable interface
- *Encapsulation*--internal state is protected
- *Extensibility*--new implementations don't break existing code

*The Strategy Pattern is ADTs applied to algorithms:*
- Define a family of algorithms as an ADT
- Encapsulate each one in its own class/struct
- Make them interchangeable at runtime
- The context (e.g., `ShoppingCart`) depends on the abstraction,
  not the concrete type

Gang of Four, *Design Patterns* (1994):
The golden rule is to
*Program to an interface, not an implementation.*

