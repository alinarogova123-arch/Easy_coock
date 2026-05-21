from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError
from django.utils import timezone

from .models import FoodType, PromoCode


MONEY_QUANT = Decimal('0.01')

MEAL_PRICES = {
    FoodType.BREAKFAST: Decimal('200.00'),
    FoodType.LUNCH: Decimal('300.00'),
    FoodType.DINNER: Decimal('400.00'),
    FoodType.DESSERT: Decimal('100.00'),
}


def normalize_food_types(food_types):
    selected_food_types = []
    for food_type in food_types:
        try:
            normalized_food_type = FoodType(food_type)
        except ValueError as error:
            raise ValidationError(
                f'Неизвестный тип приёма пищи: {food_type}'
            ) from error

        if normalized_food_type not in selected_food_types:
            selected_food_types.append(normalized_food_type)

    if not selected_food_types:
        raise ValidationError('Выберите хотя бы один приём пищи для подписки.')

    return selected_food_types


def calculate_meals_price(food_types):
    selected_food_types = normalize_food_types(food_types)
    total = sum(
        (MEAL_PRICES[food_type] for food_type in selected_food_types),
        Decimal('0.00'),
    )
    return total.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


def calculate_subscription_price(food_types, plan):
    meals_price = calculate_meals_price(food_types)
    total = meals_price * Decimal(plan.price_coefficient)
    return total.quantize(MONEY_QUANT, rounding=ROUND_HALF_UP)


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


def calculate_order_price(food_types, plan, promo_code=None):
    total_before_discount = calculate_subscription_price(food_types, plan)
    return apply_promo_code(total_before_discount, promo_code)
