import uuid
from decimal import ROUND_HALF_UP, Decimal

from django.conf import settings
from django.utils import timezone

from .validators import MONEY_QUANT


class PaymentError(ValueError):
    pass


def format_payment_amount(amount):
    return str(Decimal(amount).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP))


def configure_yookassa():
    if not settings.YOOKASSA_SHOP_ID or not settings.YOOKASSA_SECRET_KEY:
        raise PaymentError('Не настроены YOOKASSA_SHOP_ID и YOOKASSA_SECRET_KEY.')

    from yookassa import Configuration

    Configuration.account_id = settings.YOOKASSA_SHOP_ID
    Configuration.secret_key = settings.YOOKASSA_SECRET_KEY


def create_payment(subscription, return_url=None):
    from yookassa import Payment

    if not subscription.total_paid:
        raise PaymentError('Сумма подписки не указана.')

    configure_yookassa()

    payment_data = {
        'amount': {
            'value': format_payment_amount(subscription.total_paid),
            'currency': 'RUB',
        },
        'capture': True,
        'description': f'Оплата подписки Foodplan #{subscription.id}',
        'confirmation': {
            'type': 'redirect',
            'return_url': return_url or settings.YOOKASSA_RETURN_URL,
        },
        'metadata': {
            'subscription_id': subscription.id,
            'user_id': subscription.user_id,
        },
    }
    idempotence_key = f'subscription_{subscription.id}_{uuid.uuid4().hex[:16]}'

    try:
        payment = Payment.create(payment_data, idempotency_key=idempotence_key)
    except TypeError:
        payment = Payment.create(payment_data)
    except Exception as error:
        raise PaymentError(f'Ошибка создания платежа: {error}') from error

    subscription.payment_id = payment.id
    subscription.payment_status = payment.status
    subscription.confirmation_url = payment.confirmation.confirmation_url
    subscription.save(
        update_fields=['payment_id', 'payment_status', 'confirmation_url']
    )

    return {
        'payment_id': payment.id,
        'confirmation_url': payment.confirmation.confirmation_url,
        'status': payment.status,
    }


def get_payment_info(payment_id):
    from yookassa import Payment

    configure_yookassa()

    try:
        payment = Payment.find_one(payment_id)
    except Exception as error:
        raise PaymentError(f'Ошибка получения платежа: {error}') from error

    if not payment:
        raise PaymentError('Платёж не найден.')

    return {
        'id': payment.id,
        'status': payment.status,
        'paid': payment.paid,
        'amount': payment.amount.value if payment.amount else None,
    }


def update_subscription_from_payment(subscription, payment_info):
    subscription.payment_status = payment_info.get('status', '')

    paid_statuses = ('succeeded', 'waiting_for_capture')
    subscription.is_paid = (
        payment_info.get('paid', False)
        or subscription.payment_status in paid_statuses
    )

    if subscription.is_paid and not subscription.paid_at:
        subscription.paid_at = timezone.now()

    subscription.save(update_fields=['payment_status', 'is_paid', 'paid_at'])
    return subscription
