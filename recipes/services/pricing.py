from decimal import ROUND_HALF_UP, Decimal

from ..models import FoodType
from .promo import apply_promo_code
from .validators import MONEY_QUANT, normalize_food_types

MEAL_PRICES = {
    FoodType.BREAKFAST: Decimal('200.00'),
    FoodType.LUNCH: Decimal('300.00'),
    FoodType.DINNER: Decimal('400.00'),
    FoodType.DESSERT: Decimal('100.00'),
}


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


def calculate_order_price(food_types, plan, promo_code=None):
    total_before_discount = calculate_subscription_price(food_types, plan)
    return apply_promo_code(total_before_discount, promo_code)
