

from abc import ABC, abstractmethod
from datetime import datetime
import random
import string

# ─────────────────────────────────────────
# SECTION 1: EXCEPTIONS (Custom)
# ─────────────────────────────────────────

class InsufficientFundsError(Exception):
    """Raised when withdrawal exceeds account balance."""
    def __init__(self, amount, balance):
        self.amount = amount
        self.balance = balance
        super().__init__(f"Cannot withdraw ₹{amount:.2f}. Balance: ₹{balance:.2f}")

class AccountFrozenError(Exception):
    """Raised when a transaction is attempted on a frozen account."""
    pass

class InvalidAmountError(Exception):
    """Raised when a negative or zero amount is entered."""
    pass


# ─────────────────────────────────────────
# SECTION 2: TRANSACTION CLASS
# ─────────────────────────────────────────

class Transaction:
    """Represents a single bank transaction."""

    def __init__(self, transaction_type, amount, balance_after, description=""):
        self.transaction_id = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        self.type        = transaction_type   # DEPOSIT, WITHDRAWAL, TRANSFER
        self.amount      = amount
        self.balance     = balance_after
        self.timestamp   = datetime.now()
        self.description = description

    def __repr__(self):
        ts = self.timestamp.strftime("%d-%b-%Y %H:%M:%S")
        return (f"  [{ts}] {self.type:<12} ₹{self.amount:>10.2f}  "
                f"Balance: ₹{self.balance:>10.2f}  {self.description}")


# ─────────────────────────────────────────
# SECTION 3: ABSTRACT BASE CLASS — BankAccount
# ─────────────────────────────────────────

class BankAccount(ABC):
    """Abstract base class for all bank account types."""

    _total_accounts = 0  # Class variable (shared across all instances)

    def __init__(self, owner_name, initial_deposit=0):
        if initial_deposit < 0:
            raise InvalidAmountError("Initial deposit cannot be negative.")

        BankAccount._total_accounts += 1

        self.__owner        = owner_name      # Private (name mangling)
        self.__account_no   = self._generate_account_no()
        self._balance       = float(initial_deposit)
        self._is_frozen     = False
        self._transactions  = []
        self._created_at    = datetime.now()

        if initial_deposit > 0:
            self._transactions.append(
                Transaction("DEPOSIT", initial_deposit, self._balance, "Account Opening"))

    @staticmethod
    def _generate_account_no():
        return "IN" + ''.join(random.choices(string.digits, k=12))

    # ── Properties (Encapsulation with getters/setters) ──

    @property
    def owner(self):
        return self.__owner

    @owner.setter
    def owner(self, value):
        if not value.strip():
            raise ValueError("Owner name cannot be empty.")
        self.__owner = value

    @property
    def account_no(self):
        return self.__account_no

    @property
    def balance(self):
        return self._balance

    @property
    def is_frozen(self):
        return self._is_frozen

    # ── Abstract Methods (must implement in subclasses) ──

    @abstractmethod
    def account_type(self):
        pass

    @abstractmethod
    def interest_rate(self):
        pass

    # ── Concrete Methods ──

    def _validate_amount(self, amount):
        if amount <= 0:
            raise InvalidAmountError(f"Amount must be positive. Got: {amount}")

    def deposit(self, amount, description="Deposit"):
        self._validate_amount(amount)
        if self._is_frozen:
            raise AccountFrozenError("Account is frozen. Contact bank.")
        self._balance += amount
        self._transactions.append(Transaction("DEPOSIT", amount, self._balance, description))
        print(f"  ✅ Deposited ₹{amount:.2f}. New balance: ₹{self._balance:.2f}")

    def withdraw(self, amount, description="Withdrawal"):
        self._validate_amount(amount)
        if self._is_frozen:
            raise AccountFrozenError("Account is frozen. Contact bank.")
        if amount > self._balance:
            raise InsufficientFundsError(amount, self._balance)
        self._balance -= amount
        self._transactions.append(Transaction("WITHDRAWAL", amount, self._balance, description))
        print(f"  ✅ Withdrew ₹{amount:.2f}. New balance: ₹{self._balance:.2f}")

    def transfer(self, target_account, amount):
        """Transfer funds between two accounts."""
        self._validate_amount(amount)
        self.withdraw(amount, f"Transfer to {target_account.account_no}")
        target_account.deposit(amount, f"Transfer from {self.account_no}")

    def apply_interest(self):
        """Apply annual interest to account."""
        interest = self._balance * self.interest_rate()
        self._balance += interest
        self._transactions.append(Transaction("INTEREST", interest, self._balance,
                                              f"Annual Interest @ {self.interest_rate()*100:.1f}%"))
        print(f"  💰 Interest applied: ₹{interest:.2f}. New balance: ₹{self._balance:.2f}")

    def freeze(self):
        self._is_frozen = True
        print(f"  🔒 Account {self.account_no} frozen.")

    def unfreeze(self):
        self._is_frozen = False
        print(f"  🔓 Account {self.account_no} unfrozen.")

    def show_statement(self, last_n=None):
        """Show transaction history."""
        txns = self._transactions if last_n is None else self._transactions[-last_n:]
        print(f"\n  ═══ Account Statement: {self.account_no} ═══")
        print(f"  Owner: {self.owner}  |  Type: {self.account_type()}")
        print(f"  {'─'*70}")
        for t in txns:
            print(repr(t))
        print(f"  {'─'*70}")
        print(f"  Current Balance: ₹{self._balance:.2f}\n")

    # ── Operator Overloading ──

    def __str__(self):
        return (f"[{self.account_type()}] {self.owner} | {self.account_no} | "
                f"₹{self._balance:.2f}")

    def __repr__(self):
        return f"BankAccount(owner={self.owner!r}, balance={self._balance})"

    def __add__(self, other):
        """Conceptual: combined balance of two accounts."""
        return self._balance + other._balance

    def __gt__(self, other):
        return self._balance > other._balance

    def __lt__(self, other):
        return self._balance < other._balance

    def __eq__(self, other):
        return self.account_no == other.account_no

    @classmethod
    def total_accounts(cls):
        return cls._total_accounts


# ─────────────────────────────────────────
# SECTION 4: DERIVED CLASSES
# ─────────────────────────────────────────

class SavingsAccount(BankAccount):
    """Savings account with interest and minimum balance requirement."""

    MIN_BALANCE = 1000.0

    def __init__(self, owner_name, initial_deposit=1000):
        if initial_deposit < self.MIN_BALANCE:
            raise ValueError(f"Minimum opening balance for Savings: ₹{self.MIN_BALANCE}")
        super().__init__(owner_name, initial_deposit)

    def account_type(self): return "Savings Account"
    def interest_rate(self): return 0.04  # 4% per annum

    def withdraw(self, amount, description="Withdrawal"):
        if (self._balance - amount) < self.MIN_BALANCE:
            raise InsufficientFundsError(amount,
                  self._balance - self.MIN_BALANCE)
        super().withdraw(amount, description)


class CurrentAccount(BankAccount):
    """Current account with overdraft facility."""

    OVERDRAFT_LIMIT = 10000.0

    def __init__(self, owner_name, initial_deposit=0):
        super().__init__(owner_name, initial_deposit)

    def account_type(self): return "Current Account"
    def interest_rate(self): return 0.01  # 1% per annum

    def withdraw(self, amount, description="Withdrawal"):
        """Allow overdraft up to OVERDRAFT_LIMIT."""
        self._validate_amount(amount)
        if self._is_frozen:
            raise AccountFrozenError("Account is frozen.")
        if amount > (self._balance + self.OVERDRAFT_LIMIT):
            raise InsufficientFundsError(amount, self._balance + self.OVERDRAFT_LIMIT)
        self._balance -= amount
        self._transactions.append(Transaction("WITHDRAWAL", amount, self._balance, description))
        if self._balance < 0:
            print(f"  ⚠ Overdraft used! Balance: ₹{self._balance:.2f}")
        else:
            print(f"  ✅ Withdrew ₹{amount:.2f}. Balance: ₹{self._balance:.2f}")


class FixedDepositAccount(BankAccount):
    """Fixed deposit account — no withdrawals until maturity."""

    def __init__(self, owner_name, deposit_amount, tenure_years=1):
        super().__init__(owner_name, deposit_amount)
        self.tenure   = tenure_years
        self.maturity = datetime.now().replace(year=datetime.now().year + tenure_years)

    def account_type(self): return "Fixed Deposit Account"
    def interest_rate(self): return 0.07  # 7% per annum

    def withdraw(self, amount, description="Withdrawal"):
        if datetime.now() < self.maturity:
            raise AccountFrozenError(
                f"FD matures on {self.maturity.strftime('%d-%b-%Y')}. "
                f"Early withdrawal not allowed.")
        super().withdraw(amount, description)


# ─────────────────────────────────────────
# SECTION 5: BANK CLASS (Composition)
# ─────────────────────────────────────────

class Bank:
    """Manages a collection of accounts — demonstrates composition."""

    def __init__(self, bank_name):
        self.name     = bank_name
        self.accounts = {}

    def register(self, account: BankAccount):
        self.accounts[account.account_no] = account
        print(f"  ✅ Registered: {account}")

    def get(self, account_no) -> BankAccount:
        acc = self.accounts.get(account_no)
        if not acc:
            raise KeyError(f"Account {account_no} not found.")
        return acc

    def total_deposits(self):
        return sum(a.balance for a in self.accounts.values())

    def report(self):
        print(f"\n  ╔═══════ {self.name} — Bank Report ═══════╗")
        print(f"  Total Accounts  : {len(self.accounts)}")
        print(f"  Total Deposits  : ₹{self.total_deposits():,.2f}")
        print(f"\n  {'No.':<4} {'Owner':<20} {'Type':<25} {'Balance':>12}")
        print(f"  {'─'*65}")
        for i, acc in enumerate(sorted(self.accounts.values(),
                                        key=lambda a: a.balance, reverse=True), 1):
            print(f"  {i:<4} {acc.owner:<20} {acc.account_type():<25} ₹{acc.balance:>10.2f}")
        print(f"  {'═'*65}\n")


# ─────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────

def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║  Bank Account Management — OOP in Python                 ║")
    print("║  BSc Computer Science (Minor) | IGNOU                   ║")
    print("╚══════════════════════════════════════════════════════════╝\n")

    bank = Bank("National Python Bank")

    # Create accounts
    print("━━━ Creating Accounts ━━━")
    acc1 = SavingsAccount("Arjun Sharma",  50000)
    acc2 = SavingsAccount("Priya Verma",   75000)
    acc3 = CurrentAccount("Rahul Gupta",   20000)
    acc4 = FixedDepositAccount("Anjali Singh", 100000, tenure_years=1)

    for acc in [acc1, acc2, acc3, acc4]:
        bank.register(acc)

    # Transactions
    print("\n━━━ Transactions ━━━")
    acc1.deposit(5000, "Salary Credit")
    acc1.withdraw(2000, "Grocery")
    acc2.deposit(10000, "Freelance Income")
    acc3.deposit(15000, "Business Revenue")
    acc3.withdraw(25000, "Business Expense")   # Overdraft demo

    # Transfer
    print("\n━━━ Transfer: Arjun → Priya ━━━")
    acc1.transfer(acc2, 3000)

    # Interest
    print("\n━━━ Applying Interest ━━━")
    for acc in [acc1, acc2, acc3, acc4]:
        acc.apply_interest()

    # Statement
    acc1.show_statement()

    # Bank Report
    bank.report()

    # OOP Features Demo
    print("━━━ Operator Overloading Demo ━━━")
    print(f"  acc1 > acc2 : {acc1 > acc2}")
    print(f"  acc1 + acc2 (combined) : ₹{acc1 + acc2:.2f}")
    print(f"  acc1 == acc1 : {acc1 == acc1}")
    print(f"  acc1 == acc2 : {acc1 == acc2}")

    # Exception Handling Demo
    print("\n━━━ Exception Handling Demo ━━━")
    try:
        acc1.withdraw(500000)
    except InsufficientFundsError as e:
        print(f"  ⚠ Caught: {e}")

    try:
        acc4.withdraw(50000)
    except AccountFrozenError as e:
        print(f"  ⚠ Caught: {e}")

    print(f"\n  Total Accounts Created: {BankAccount.total_accounts()}")
    print("\n  OOP Concepts: Encapsulation ✓  Inheritance ✓")
    print("  Polymorphism ✓  Abstraction ✓  Operator Overloading ✓")
    print("  Composition ✓  Class Variables ✓  Properties ✓")


if __name__ == "__main__":
    main()
