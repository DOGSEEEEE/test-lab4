Feature: Extended E-shop Tests

    # 1. Тест на безкоштовний товар
    Scenario: Product price is zero
        Given A product "Freebie" with price 0 and availability 10
        Then Product price should be 0

    # 2. Тест на підрахунок суми декількох товарів
    Scenario: Total cost of multiple items
        Given A product "Laptop" with price 1000 and availability 5
        And A product "Mouse" with price 50 and availability 10
        When I add "Laptop" in amount 2 to the cart
        And I add "Mouse" in amount 3 to the cart
        Then The total cart price should be 2150

    # 3. Видалення товару
    Scenario: Remove product from cart
        Given A product "Phone" with price 500 and availability 5
        And I add "Phone" in amount 1 to the cart
        When I remove "Phone" from the cart
        Then The cart should not contain "Phone"

    # 4. Пограничне значення: Від’ємна кількість (має бути помилка)
    Scenario: Add negative amount of product
        Given A product "Valid" with price 10 and availability 10
        When I try to add "Valid" in amount -5 to the cart
        Then The system should raise an error

    # 5. Некоректний тип даних: Текст замість числа
    Scenario: Add string instead of number to cart
        Given A product "Valid" with price 10 and availability 10
        When I try to add "Valid" with invalid type "text" to the cart
        Then The system should raise an error

    # 6. Спроба взяти більше, ніж є на складі
    Scenario: Check availability for more than exists
        Given A product "Limited" with price 10 and availability 5
        When I check if "Limited" is available in amount 6
        Then The availability result should be False

    # 7. Перевірка, що замовлення зменшує залишок на складі
    Scenario: Placing a valid order reduces stock
        Given A product "StockItem" with price 10 and availability 100
        And I add "StockItem" in amount 10 to the cart
        When I place an order
        Then The product "StockItem" should have 90 items left

    # 8. Після замовлення корзина має стати порожньою
    Scenario: Order clears the cart after completion
        Given A product "StockItem" with price 10 and availability 100
        And I add "StockItem" in amount 5 to the cart
        When I place an order
        Then The cart total should be 0

    # 9. Помилка при спробі додати порожній об'єкт (None)
    Scenario: Add None as a product
        When I try to add None to the cart
        Then The system should raise an error

    # 10. Розрахунок суми для порожньої корзини
    Scenario: Calculate total for an empty cart
        Given An empty shopping cart
        Then The total cart price should be 0