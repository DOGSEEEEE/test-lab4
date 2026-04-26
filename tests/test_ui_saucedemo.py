"""
Лабораторна робота №5: UI-тестування за допомогою Playwright.
Тестування сайту SauceDemo з використанням POM.
"""

import pytest
from playwright.sync_api import Page, expect

# --- SECTION: Page Object Model ---

class SauceDemoPOM:
    """Клас POM для сайту SauceDemo."""
    def __init__(self, page: Page):
        self.page = page
        self.url = "https://www.saucedemo.com/"
        self.user_input = page.locator('[data-test="username"]')
        self.pass_input = page.locator('[data-test="password"]')
        self.login_btn = page.locator('[data-test="login-button"]')
        self.inventory_list = page.locator(".inventory_list")
        self.cart_icon = page.locator(".shopping_cart_link")
        self.burger_menu = page.locator("#react-burger-menu-btn")
        self.logout_link = page.locator("#logout_sidebar_link")

    def navigate(self):
        """Перехід на головну сторінку."""
        self.page.goto(self.url)

    def login(self, user, password):
        """Авторизація користувача."""
        self.user_input.fill(user)
        self.pass_input.fill(password)
        self.login_btn.click()

    def logout(self):
        """Вихід із системи."""
        self.burger_menu.click()
        self.logout_link.click()

# --- SECTION: UI Tests ---

@pytest.fixture
def pom(page: Page):
    """Фікстура для ініціалізації POM перед кожним тестом."""
    sauce_pom = SauceDemoPOM(page)
    sauce_pom.navigate()
    return sauce_pom

# Тест 1: Успішний логін (Використовує POM)
def test_successful_login(pom):
    pom.login("standard_user", "secret_sauce")
    expect(pom.inventory_list).to_be_visible()

# Тест 2: Логін із заблокованим користувачем
def test_locked_out_user(pom):
    pom.login("locked_out_user", "secret_sauce")
    error_msg = pom.page.locator('[data-test="error"]')
    expect(error_msg).to_contain_text("Sorry, this user has been locked out.")

# Тест 3: Вихід із системи (Використовує POM)
def test_logout(pom):
    pom.login("standard_user", "secret_sauce")
    pom.logout()
    expect(pom.login_btn).to_be_visible()

# Тест 4: Додавання товару в кошик
def test_add_to_cart(pom):
    pom.login("standard_user", "secret_sauce")
    pom.page.locator('[data-test="add-to-cart-sauce-labs-backpack"]').click()
    expect(pom.page.locator(".shopping_cart_badge")).to_have_text("1")

# Тест 5: Видалення товару з кошика
def test_remove_from_cart(pom):
    pom.login("standard_user", "secret_sauce")
    pom.page.locator('[data-test="add-to-cart-sauce-labs-backpack"]').click()
    pom.page.locator('[data-test="remove-sauce-labs-backpack"]').click()
    expect(pom.page.locator(".shopping_cart_badge")).not_to_be_visible()

# Тест 6: Перевірка деталей товару
def test_product_details(pom):
    pom.login("standard_user", "secret_sauce")
    pom.page.click("text=Sauce Labs Backpack")
    expect(pom.page.locator(".inventory_details_name")).to_have_text("Sauce Labs Backpack")

# Тест 7: Сортування товарів (Price Low to High)
def test_sorting_price_low(pom):
    pom.login("standard_user", "secret_sauce")
    pom.page.select_option(".product_sort_container", "lohi")
    first_item_price = pom.page.locator(".inventory_item_price").first
    expect(first_item_price).to_have_text("$7.99")

# Тест 8: Перевірка порожнього кошика
def test_empty_cart_view(pom):
    pom.login("standard_user", "secret_sauce")
    pom.cart_icon.click()
    expect(pom.page.locator(".cart_list")).to_be_visible()
    expect(pom.page.locator(".inventory_item_name")).not_to_be_visible()

# Тест 9: Процес оформлення замовлення (Checkout Step 1)
def test_checkout_process_init(pom):
    pom.login("standard_user", "secret_sauce")
    pom.page.locator('[data-test="add-to-cart-sauce-labs-backpack"]').click()
    pom.cart_icon.click()
    pom.page.locator('[data-test="checkout"]').click()
    expect(pom.page).to_have_url("https://www.saucedemo.com/checkout-step-one.html")

# Тест 10: Скидання стану додатку (Reset App State)
def test_reset_app_state(pom):
    pom.login("standard_user", "secret_sauce")
    pom.page.locator('[data-test="add-to-cart-sauce-labs-backpack"]').click()
    pom.burger_menu.click()
    pom.page.locator("#reset_sidebar_link").click()
    expect(pom.page.locator(".shopping_cart_badge")).not_to_be_visible()