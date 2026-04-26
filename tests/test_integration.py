import pytest
import time
import boto3
import uuid
from datetime import datetime, timedelta, timezone
from app.eshop import Product, ShoppingCart, Order, Shipment
from services import ShippingService
from services.repository import ShippingRepository
from services.publisher import ShippingPublisher
from services.db import get_dynamodb_resource

# 1. Тест успішного повного циклу: від замовлення до зміни статусу в БД
def test_full_cycle_order_to_db_status(dynamo_resource):
    repo = ShippingRepository()
    pub = ShippingPublisher()
    service = ShippingService(repo, pub)
    
    cart = ShoppingCart()
    cart.add_product(Product("Laptop", 1000, 5), 1)
    order = Order(cart, service)
    
    shipping_id = order.place_order("Нова Пошта")
    
    # Перевіряємо, чи статус у базі "in progress"
    status = service.check_status(shipping_id)
    assert status == ShippingService.SHIPPING_IN_PROGRESS

# 2. Тест: Обробка черги (Batch processing) змінює статуси в БД
def test_process_batch_updates_multiple_shippings(dynamo_resource):
    service = ShippingService(ShippingRepository(), ShippingPublisher())
    
    # Створюємо 2 відправки
    id1 = service.create_shipping("Укр Пошта", ["item1"], "order1", datetime.now(timezone.utc) + timedelta(minutes=5))
    id2 = service.create_shipping("Самовивіз", ["item2"], "order2", datetime.now(timezone.utc) + timedelta(minutes=5))
    
    # Обробляємо чергу
    service.process_shipping_batch()
    
    assert service.check_status(id1) == ShippingService.SHIPPING_COMPLETED
    assert service.check_status(id2) == ShippingService.SHIPPING_COMPLETED

# 3. Тест: Провал доставки через прострочений дедлайн (due_date)
def test_shipping_fails_if_due_date_passed(dynamo_resource):
    repo = ShippingRepository()
    pub = ShippingPublisher()
    service = ShippingService(repo, pub)
    
    # Створюємо доставку з коротким терміном
    due_date = datetime.now(timezone.utc) + timedelta(seconds=1)
    shipping_id = service.create_shipping("Нова Пошта", ["p1"], "ord1", due_date)
    
    # Чекаємо 2 секунди, щоб час вийшов
    time.sleep(2)
    
    service.process_shipping(shipping_id)
    assert service.check_status(shipping_id) == ShippingService.SHIPPING_FAILED

# 4. Тест інтеграції зі складом: замовлення через сервіс доставки зменшує залишок
def test_order_delivery_reduces_product_stock(dynamo_resource):
    prod = Product("Phone", 500, 10)
    cart = ShoppingCart()
    cart.add_product(prod, 3)
    
    service = ShippingService(ShippingRepository(), ShippingPublisher())
    order = Order(cart, service)
    
    order.place_order("Самовивіз")
    assert prod.available_amount == 7

# 5. Тест: Валідація некоректного часу доставки (дедлайн у минулому)
def test_create_shipping_with_past_date_raises_error(dynamo_resource):
    service = ShippingService(ShippingRepository(), ShippingPublisher())
    past_date = datetime.now(timezone.utc) - timedelta(days=1)
    
    with pytest.raises(ValueError, match="Shipping due datetime must be greater than datetime now"):
        service.create_shipping("Укр Пошта", ["item"], "order_id", past_date)

# 6. Тест: Кошик стає порожнім після інтеграції з сервісом доставки
def test_cart_is_empty_after_successful_order_placement(dynamo_resource):
    cart = ShoppingCart()
    cart.add_product(Product("A", 10, 10), 2)
    service = ShippingService(ShippingRepository(), ShippingPublisher())
    order = Order(cart, service)
    
    order.place_order("Meest Express")
    assert len(cart.products) == 0

# 7. Тест: Повторна перевірка статусу через об'єкт Shipment
def test_shipment_object_integration_with_service(dynamo_resource):
    service = ShippingService(ShippingRepository(), ShippingPublisher())
    shipping_id = service.create_shipping("Самовивіз", ["item"], "ord", datetime.now(timezone.utc) + timedelta(minutes=1))
    
    shipment = Shipment(shipping_id, service)
    assert shipment.check_shipping_status() == ShippingService.SHIPPING_IN_PROGRESS

# 8. Тест: Перевірка DynamoDB на наявність всіх полів після створення
def test_repository_saves_correct_data_structure(dynamo_resource):
    repo = ShippingRepository()
    due_date = datetime.now(timezone.utc) + timedelta(hours=1)
    ship_id = repo.create_shipping("Нова Пошта", ["prod1", "prod2"], "order99", "created", due_date)
    
    data = repo.get_shipping(ship_id)
    assert data["order_id"] == "order99"
    assert data["product_ids"] == "prod1,prod2"
    assert "created_date" in data

# 9. Тест: SQS Publisher надсилає коректний ID (Mock-інтеграція)
def test_publisher_integration_sends_id(mocker):
    mock_pub = mocker.Mock(spec=ShippingPublisher)
    service = ShippingService(mocker.Mock(), mock_pub)
    
    # Виклик створення через сервіс
    service.create_shipping("Самовивіз", ["p"], "o", datetime.now(timezone.utc) + timedelta(hours=1))
    
    # Перевіряємо, що видавець отримав команду надіслати ID
    assert mock_pub.send_new_shipping.called

# 10. Тест: Отримання декількох повідомлень з черги (SQS Poll)
def test_sqs_poll_integration(dynamo_resource):
    pub = ShippingPublisher()
    
    # 1. Створюємо абсолютно унікальні ID, щоб не плутати зі старими
    id1 = f"new_test_{uuid.uuid4().hex[:6]}"
    id2 = f"new_test_{uuid.uuid4().hex[:6]}"

    # 2. Надсилаємо їх
    pub.send_new_shipping(id1)
    pub.send_new_shipping(id2)

    # 3. Викачуємо повідомлення великою порцією (до 10), 
    # щоб забрати і старе сміття, і наші нові ID
    messages = pub.poll_shipping(batch_size=10)
    
    # 4. Перевіряємо, що наші ID є серед отриманих
    assert id1 in messages, f"ID {id1} не знайдено в черзі серед {messages}"
    assert id2 in messages, f"ID {id2} не знайдено в черзі серед {messages}"
@pytest.fixture
def dynamo_resource():
    return get_dynamodb_resource()