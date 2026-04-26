"""
Модуль логіки електронного магазину.
Містить класи для керування товарами, кошиком та замовленнями.
"""

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Optional
from services.service import ShippingService


class Product:
    """Клас, що представляє товар у системі."""

    def __init__(self, name: str, price: float, available_amount: int):
        """Ініціалізація товару."""
        self.name = name
        self.price = price
        self.available_amount = available_amount

    def is_available(self, requested_amount: int) -> bool:
        """Перевіряє, чи є в наявності потрібна кількість товару."""
        return self.available_amount >= requested_amount

    def buy(self, requested_amount: int) -> None:
        """Зменшує кількість товару на складі після покупки."""
        self.available_amount -= requested_amount

    def __eq__(self, other: object) -> bool:
        """Порівнює товари за назвою."""
        return isinstance(other, Product) and self.name == other.name

    def __hash__(self) -> int:
        """Генерує хеш на основі назви товару."""
        return hash(self.name)

    def __str__(self) -> str:
        """Повертає назву товару у вигляді рядка."""
        return self.name


class ShoppingCart:
    """Клас для керування кошиком покупця."""

    def __init__(self) -> None:
        """Ініціалізація порожнього кошика."""
        self.products: Dict[Product, int] = {}

    def contains_product(self, product: Product) -> bool:
        """Перевіряє, чи є товар у кошику."""
        return product in self.products

    def calculate_total(self) -> float:
        """Обчислює загальну вартість товарів у кошику."""
        # Використання генератора замість списку для економії пам'яті
        return sum(p.price * count for p, count in self.products.items())

    def add_product(self, product: Product, amount: int) -> None:
        """Додає товар у кошик, якщо він доступний."""
        if not product.is_available(amount):
            raise ValueError(f"Product {product} has only {product.available_amount} items")
        self.products[product] = amount

    def remove_product(self, product: Product) -> None:
        """Видаляє товар із кошика."""
        if product in self.products:
            del self.products[product]

    def submit_cart_order(self) -> List[str]:
        """Оформлює товари в кошику та повертає список їх назв."""
        product_ids = []
        for product, count in self.products.items():
            product.buy(count)
            product_ids.append(str(product))
        self.products.clear()
        return product_ids


@dataclass
class Order:
    """Клас, що представляє замовлення клієнта."""

    cart: ShoppingCart
    shipping_service: ShippingService
    order_id: Optional[str] = None

    def __post_init__(self) -> None:
        """Генерує унікальний ID замовлення, якщо він не вказаний."""
        if self.order_id is None:
            self.order_id = str(uuid.uuid4())

    def place_order(self, shipping_type: str, due_date: datetime = None) -> str:
        """Відправляє замовлення в сервіс доставки."""
        if not due_date:
            due_date = datetime.now(timezone.utc) + timedelta(seconds=3)

        product_ids = self.cart.submit_cart_order()

        # Розбиваємо довгий рядок для Pylint (C0301)
        return self.shipping_service.create_shipping(
            shipping_type,
            product_ids,
            self.order_id,
            due_date
        )


@dataclass
class Shipment:
    """Клас для відстеження статусу доставки."""

    shipping_id: str
    shipping_service: ShippingService

    def check_shipping_status(self) -> str:
        """Повертає поточний статус доставки через сервіс."""
        return self.shipping_service.check_status(self.shipping_id)