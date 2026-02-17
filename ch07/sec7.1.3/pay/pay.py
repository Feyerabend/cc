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
        print(f"\n{'─' * 50}")
        print(f"  Checking out with: {strategy.name}")
        print(f"{'─' * 50}")

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
