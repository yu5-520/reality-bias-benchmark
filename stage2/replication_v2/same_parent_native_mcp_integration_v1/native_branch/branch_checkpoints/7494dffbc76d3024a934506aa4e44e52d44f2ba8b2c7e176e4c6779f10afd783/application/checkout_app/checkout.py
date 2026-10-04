"""Current checkout behavior."""


def create_checkout(cart, method="card"):
    items = cart.get("items", [])
    if not items or any(item.get("quantity", 0) < 1 for item in items):
        raise ValueError("The cart needs items with positive quantities")
    if method not in ("card", "bank_transfer"):
        raise ValueError("Unsupported payment method")
    cents = sum(item["price_cents"] * item["quantity"] for item in items)
    return {"status": "pending_payment", "amount_cents": cents, "method": method}
