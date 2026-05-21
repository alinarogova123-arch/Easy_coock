from django.utils import timezone

from ..models import DailyMenu, FoodType, Recipe


def generate_daily_menu(subscription):
    today_date = timezone.now().date()

    existing_menu = DailyMenu.objects.filter(
        subscription=subscription,
        date=today_date,
    ).first()
    if existing_menu:
        return existing_menu

    menu_type = subscription.menu_type
    excluded_allergens = subscription.excluded_allergens

    meals = {}

    if subscription.has_breakfast:
        meals['breakfast'] = get_random_recipe(
            FoodType.BREAKFAST, menu_type, excluded_allergens
        )
    if subscription.has_lunch:
        meals['lunch'] = get_random_recipe(
            FoodType.LUNCH, menu_type, excluded_allergens
        )
    if subscription.has_dinner:
        meals['dinner'] = get_random_recipe(
            FoodType.DINNER, menu_type, excluded_allergens
        )
    if subscription.has_dessert:
        meals['dessert'] = get_random_recipe(
            FoodType.DESSERT, menu_type, excluded_allergens
        )

    if not meals:
        return

    return DailyMenu.objects.create(
        subscription=subscription,
        date=today_date,
        breakfast=meals.get('breakfast'),
        lunch=meals.get('lunch'),
        dinner=meals.get('dinner'),
        dessert=meals.get('dessert'),
    )


def get_random_recipe(food_type, menu_type, excluded_allergens=None):
    recipes = Recipe.objects.filter(
        food_type=food_type,
        menu_type=menu_type,
    )

    if excluded_allergens and excluded_allergens.exists():
        recipes = recipes.exclude(allergens__in=excluded_allergens.all())

    return recipes.order_by('?').first()
