from django.contrib.auth.models import User
from django.db import models


class FoodType(models.TextChoices):
    BREAKFAST = 'breakfast', 'Завтрак'
    LUNCH = 'lunch', 'Обед'
    DINNER = 'dinner', 'Ужин'
    DESSERT = 'dessert', 'Десерт'


class MenuType(models.TextChoices):
    CLASSIC = 'classic', 'Классическое'
    VEGAN = 'vegan', 'Веганское'
    KETO = 'keto', 'Кето диета'
    LOW_CARB = 'low_carb', 'Низкоуглеводное'


class SubscriptionPlan(models.Model):
    name = models.CharField(verbose_name='Название', max_length=50)
    duration = models.PositiveIntegerField(
        verbose_name='Срок подписки(месяцев)', unique=True
    )
    price = models.DecimalField(
        verbose_name='Базовая цена (руб/мес)',
        max_digits=8,
        decimal_places=2,
    )
    price_coefficient = models.DecimalField(
        verbose_name='Коэффициент цены',
        max_digits=4,
        decimal_places=2,
    )

    is_active = models.BooleanField(
        verbose_name='Активен',
        default=True,
    )

    class Meta:
        verbose_name = 'Тарифный план'
        verbose_name_plural = 'Тарифные планы'
        ordering = ['duration']

    def __str__(self):
        return f'{self.name} - {self.duration} мес.'


class Allergen(models.Model):
    name = models.CharField(
        verbose_name='Название', max_length=50, unique=True
    )

    class Meta:
        verbose_name = 'Аллерген'
        verbose_name_plural = 'Аллергены'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(
        max_length=200, verbose_name='Название', db_index=True
    )
    description = models.TextField(verbose_name='Описание')
    instruction = models.TextField(verbose_name='Инструкция')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время готовки (мин)'
    )
    calories = models.PositiveIntegerField(verbose_name='Калории')

    images = models.ImageField(
        verbose_name='Изображение', upload_to='', blank=True
    )

    food_type = models.CharField(
        verbose_name='Тип еды',
        max_length=20,
        choices=FoodType.choices,
        db_index=True,
    )
    menu_type = models.CharField(
        verbose_name='Тип меню',
        max_length=20,
        choices=MenuType.choices,
        db_index=True,
    )

    allergens = models.ManyToManyField(
        Allergen, verbose_name='Аллергены', blank=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'

    def __str__(self):
        return f'{self.name}'


class Ingredient(models.Model):
    name = models.CharField(
        verbose_name='Название', max_length=100, unique=True
    )
    unit = models.CharField(verbose_name='Ед. измерения', max_length=20)

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'

    def __str__(self):
        return self.name


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, on_delete=models.CASCADE, related_name='ingredients'
    )
    ingredient = models.ForeignKey(Ingredient, on_delete=models.CASCADE)
    amount = models.PositiveIntegerField(verbose_name='Количество')
    price = models.DecimalField(
        verbose_name='Цена (руб)',
        max_digits=8,
        decimal_places=2,
    )

    class Meta:
        verbose_name = 'Ингредиент в рецепте'
        verbose_name_plural = 'Ингредиенты в рецептах'
        unique_together = ('recipe', 'ingredient')

    def __str__(self):
        return (
            f'{self.recipe.name}: {self.ingredient.name}'
            f'- {self.amount} {self.ingredient.unit}'
        )


class Subscription(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='subscriptions'
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name='selected',
    )

    menu_type = models.CharField(
        verbose_name='Тип меню',
        max_length=20,
        choices=MenuType.choices,
        db_index=True,
    )
    persons = models.PositiveIntegerField(verbose_name='Количество персон')
    excluded_allergens = models.ManyToManyField(Allergen, blank=True)

    started_at = models.DateTimeField(
        verbose_name='Активирована', auto_now_add=True
    )
    expires_at = models.DateTimeField(verbose_name='Истекает')
    is_active = models.BooleanField(verbose_name='Активна', default=True)

    total_paid = models.DecimalField(
        verbose_name='Оплаченная сумма',
        max_digits=10,
        decimal_places=2,
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user.username} - {self.plan.name} ({self.expires_at.date()})'


class PromoCode(models.Model):
    code = models.CharField('Промокод', max_length=50, unique=True)
    discount_percent = models.PositiveSmallIntegerField(
        verbose_name='Скидка в %'
    )
    valid_until = models.DateTimeField(verbose_name='Действителен до')
    is_active = models.BooleanField(verbose_name='Активен', default=True)
    max_uses = models.PositiveIntegerField(
        verbose_name='Максимум использований', default=1
    )

    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды'

    def __str__(self):
        return f'{self.code} ({self.discount_percent}%)'
