from app.at_client import sms


def send_order_creation_sms(order_id, customer_name, phone_number):
    message = (f'Hello {customer_name}, Thank you for your order! Your order #{order_id} has been created successfully '
               f'and is being processed.')
    response = sms.send(message, [phone_number])
    return response
