from decimal import Decimal, ROUND_HALF_UP

from django.core.exceptions import ValidationError

from .models import FoodType


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
