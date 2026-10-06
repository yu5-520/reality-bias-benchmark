import unittest
from checkout_app.checkout import create_checkout


class CheckoutTests(unittest.TestCase):
    def test_card_checkout(self):
        self.assertEqual(create_checkout({"items": [{"price_cents": 1250, "quantity": 2}]}),
                         {"status": "pending_payment", "amount_cents": 2500, "method": "card"})

    def test_empty_cart(self):
        with self.assertRaises(ValueError):
            create_checkout({"items": []})


if __name__ == "__main__":
    unittest.main()
