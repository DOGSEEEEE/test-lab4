import unittest
from unittest.mock import MagicMock
from app.eshop import Product, ShoppingCart, Order

class TestEshop(unittest.TestCase):
    def setUp(self):
        self.product = Product(name='Test', price=100.0, available_amount=20)
        self.cart = ShoppingCart()
        self.mock_service = MagicMock() # Заглушка для сервісу доставки

    def test_add_product_to_cart(self):
        self.cart.add_product(self.product, 5)
        self.assertTrue(self.cart.contains_product(self.product))

    def test_calculate_total(self):
        self.cart.add_product(self.product, 2)
        self.assertEqual(self.cart.calculate_total(), 200.0)

    def test_order_reduces_stock(self):
        self.cart.add_product(self.product, 5)
        # Передаємо mock_service другим аргументом
        order = Order(self.cart, self.mock_service)
        order.place_order("Самовивіз")
        self.assertEqual(self.product.available_amount, 15)

    def test_order_clears_cart(self):
        self.cart.add_product(self.product, 1)
        # Передаємо mock_service другим аргументом
        order = Order(self.cart, self.mock_service)
        order.place_order("Самовивіз")
        self.assertEqual(len(self.cart.products), 0)