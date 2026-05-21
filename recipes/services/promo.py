from decimal import ROUND_HALF_UP, Decimal

from django.core.exceptions import ValidationError
from django.utils import timezone

from ..models import PromoCode
from .validators import MONEY_QUANT


def find_promo_code(code):
    normalized_code = code.strip()
    if not normalized_code:
        return None
    return PromoCode.objects.filter(code__iexact=normalized_code).first()


def validate_promo_code(promo_code, now=None):
    if promo_code is None:
        raise ValidationError('Промокод не найден.')

    current_time = now or timezone.now()
    if not promo_code.is_active:
        raise ValidationError('Промокод неактивен.')
    if promo_code.valid_until < current_time:
        raise ValidationError('Срок действия промокода истёк.')
    if promo_code.used_count >= promo_code.max_uses:
        raise ValidationError('Лимит использований промокода исчерпан.')
    if not 1 <= promo_code.discount_percent <= 100:
        raise ValidationError('Скидка промокода должна быть от 1 до 100%.')
    return promo_code


def calculate_discount_amount(total, promo_code):
    valid_promo_code = validate_promo_code(promo_code)
    total = Decimal(total).quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)
    discount_rate = Decimal(valid_promo_code.discount_percent) / Decimal('100')
    discount_amount = total * discount_rate
    return discount_amount.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def apply_promo_code(total_before_discount, promo_code=None):
    total_before_discount = Decimal(total_before_discount).quantize(
        MONEY_QUANT,
        rounding=ROUND_HALF_UP,
    )
    if promo_code is None:
        return {
            'total_before_discount': total_before_discount,
            'discount_amount': Decimal('0.00'),
            'total_paid': total_before_discount,
        }

    discount_amount = calculate_discount_amount(
        total_before_discount,
        promo_code,
    )
    total_paid = total_before_discount - discount_amount
    if total_paid < Decimal('0.00'):
        total_paid = Decimal('0.00')

    return {
        'total_before_discount': total_before_discount,
        'discount_amount': discount_amount,
        'total_paid': total_paid.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP),
    }
