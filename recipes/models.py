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
    pass


class Allergen(models.Model):
    name = models.CharField('Название', max_length=50, unique=True)

    class Meta:
        verbose_name = 'Аллерген'
        verbose_name_plural = 'Аллергены'

    def __str__(self):
        return self.name


class Recipe(models.Model):
    name = models.CharField(max_length=200, verbose_name='Название')
    description = models.TextField(verbose_name='Описание')
    instruction = models.TextField(verbose_name='Инструкция')
    cooking_time = models.PositiveIntegerField(
        verbose_name='Время готовки (мин)'
    )

    images = models.ImageField(
        verbose_name='Изображение', upload_to='', blank=True
    )

    food_type = models.CharField(
        verbose_name='Тип еды', max_length=20, choices=FoodType.choices
    )
    menu_type = models.CharField(
        verbose_name='Тип меню', max_length=20, choices=MenuType.choices
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

    def __str__(self):
        return (
            f'{self.recipe.name}: {self.ingredient.name}'
            f'- {self.amount} {self.ingredient.unit}'
        )


class UserAccount(models.Model):
    pass


class Subscription(models.Model):
    pass


class PromoCode(models.Model):
    pass
