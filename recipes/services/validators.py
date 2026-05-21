from decimal import Decimal

from django.core.exceptions import ValidationError

from ..models import FoodType

MONEY_QUANT = Decimal('0.01')


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
