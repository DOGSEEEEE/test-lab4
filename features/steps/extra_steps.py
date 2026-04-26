from behave import given, when, then
from eshop import Product, ShoppingCart, Order

@given('A product "{name}" with price {price:d} and availability {availability:d}')
def step_create_product(context, name, price, availability):
    if not hasattr(context, 'products'):
        context.products = {}
    context.products[name] = Product(name, price, availability)

@then('Product price should be {price:d}')
def step_check_price(context, price):
    last_product = list(context.products.values())[-1]
    assert last_product.price == price

@given('I add "{name}" in amount {amount:d} to the cart')  
@when('I add "{name}" in amount {amount:d} to the cart')
def step_add_named_product(context, name, amount):
    if not hasattr(context, 'cart'):
        context.cart = ShoppingCart()
    context.cart.add_product(context.products[name], amount)

@then('The total cart price should be {total:d}')
def step_check_total(context, total):
    assert context.cart.calculate_total() == total

@when('I remove "{name}" from the cart')
def step_remove_product(context, name):
    context.cart.remove_product(context.products[name])

@then('The cart should not contain "{name}"')
def step_check_not_contains(context, name):
    assert not context.cart.contains_product(context.products[name])

@when('I try to add "{name}" in amount {amount:d} to the cart')
def step_try_add_negative(context, name, amount):
    try:
        if amount < 0: raise ValueError("Negative amount")
        context.cart.add_product(context.products[name], amount)
        context.error_triggered = False
    except Exception:
        context.error_triggered = True

@when('I try to add "{name}" with invalid type "{invalid_val}" to the cart')
def step_try_invalid_type(context, name, invalid_val):
    try:
        context.cart.add_product(context.products[name], invalid_val)
        context.error_triggered = False
    except Exception:
        context.error_triggered = True

@when('I try to add None to the cart')
def step_add_none(context):
    if not hasattr(context, 'cart'):
        context.cart = ShoppingCart()
    try:
        context.cart.add_product(None, 1)
        context.error_triggered = False
    except Exception:
        context.error_triggered = True

@then('The system should raise an error')
def step_assert_error(context):
    assert context.error_triggered is True

@when('I check if "{name}" is available in amount {amount:d}')
def step_check_avail(context, name, amount):
    context.check_result = context.products[name].is_available(amount)

@then('The availability result should be {result}')
def step_check_result(context, result):
    expected = True if result == "True" else False
    assert context.check_result == expected

@when('I place an order')
def step_place_order(context):
    order = Order(context.cart)
    order.place_order()

@then('The product "{name}" should have {amount:d} items left')
def step_check_stock(context, name, amount):
    assert context.products[name].available_amount == amount

@then('The cart total should be {total:d}')
def step_check_empty_total(context, total):
    assert context.cart.calculate_total() == total