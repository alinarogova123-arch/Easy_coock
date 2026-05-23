from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone


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


class SubscriptionStatus(models.TextChoices):
    PENDING = 'pending', 'Ожидает активации'
    ACTIVE = 'active', 'Активна'
    EXPIRED = 'expired', 'Истекла'
    CANCELLED = 'cancelled', 'Отменена'


class SubscriptionPlan(models.Model):
    name = models.CharField(verbose_name='Название', max_length=50)
    duration = models.PositiveIntegerField(
        verbose_name='Срок подписки(месяцев)', unique=True
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
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscriptions',
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

    has_breakfast = models.BooleanField(verbose_name='Завтраки', default=False)
    has_lunch = models.BooleanField(verbose_name='Обеды', default=False)
    has_dinner = models.BooleanField(verbose_name='Ужины', default=False)
    has_dessert = models.BooleanField(verbose_name='Десерты', default=False)

    status = models.CharField(
        verbose_name='Статус',
        max_length=20,
        choices=SubscriptionStatus.choices,
        default=SubscriptionStatus.PENDING,
        db_index=True,
    )
    created_at = models.DateTimeField(
        verbose_name='Создана',
        default=timezone.now,
        editable=False,
    )
    activated_at = models.DateTimeField(
        verbose_name='Активирована',
        null=True,
        blank=True,
    )
    expires_at = models.DateTimeField(
        verbose_name='Истекает',
        null=True,
        blank=True,
    )

    promo_code = models.ForeignKey(
        'PromoCode',
        on_delete=models.PROTECT,
        verbose_name='Промокод',
        related_name='subscriptions',
        null=True,
        blank=True,
    )
    total_before_discount = models.DecimalField(
        verbose_name='Стоимость до скидки',
        max_digits=10,
        decimal_places=2,
        default=0,
    )
    discount_amount = models.DecimalField(
        verbose_name='Скидка',
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    total_paid = models.DecimalField(
        verbose_name='Итоговая сумма',
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'

    def __str__(self):
        return f'{self.user.username} - {self.plan.name} ({self.get_status_display()})'

    @property
    def selected_food_types(self):
        selected_types = []
        if self.has_breakfast:
            selected_types.append(FoodType.BREAKFAST)
        if self.has_lunch:
            selected_types.append(FoodType.LUNCH)
        if self.has_dinner:
            selected_types.append(FoodType.DINNER)
        if self.has_dessert:
            selected_types.append(FoodType.DESSERT)
        return selected_types

    def clean(self):
        super().clean()
        if not self.selected_food_types:
            raise ValidationError(
                'Выберите хотя бы один приём пищи для подписки.'
            )


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
    used_count = models.PositiveIntegerField(
        verbose_name='Использовано', default=0
    )

    class Meta:
        verbose_name = 'Промокод'
        verbose_name_plural = 'Промокоды'

    def __str__(self):
        return f'{self.code} ({self.discount_percent}%)'

    def clean(self):
        super().clean()
        errors = {}
        if not 1 <= self.discount_percent <= 100:
            errors['discount_percent'] = 'Скидка должна быть от 1 до 100%.'
        if self.max_uses < 1:
            errors['max_uses'] = 'Максимум использований должен быть больше 0.'
        if self.used_count > self.max_uses:
            errors['used_count'] = (
                'Использований не может быть больше максимального лимита.'
            )
        if errors:
            raise ValidationError(errors)


class DailyMenu(models.Model):
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.CASCADE,
        related_name='daily_menus',
        verbose_name='Подписка',
    )
    date = models.DateField(
        verbose_name='Дата', default=timezone.now, db_index=True
    )

    breakfast = models.ForeignKey(
        Recipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        limit_choices_to={'food_type': FoodType.BREAKFAST},
    )
    lunch = models.ForeignKey(
        Recipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        limit_choices_to={'food_type': FoodType.LUNCH},
    )
    dinner = models.ForeignKey(
        Recipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        limit_choices_to={'food_type': FoodType.DINNER},
    )
    dessert = models.ForeignKey(
        Recipe,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='+',
        limit_choices_to={'food_type': FoodType.DESSERT},
    )

    class Meta:
        verbose_name = 'Ежедневное меню'
        verbose_name_plural = 'Ежедневные меню'
        unique_together = ('subscription', 'date')


class Comment(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='comments',
        verbose_name='Рецепт',
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='recipe_comments',
        verbose_name='Автор',
    )
    text = models.TextField(verbose_name='Комментарий')
    rating = models.PositiveSmallIntegerField(
        verbose_name='Оценка',
        choices=[
            (1, '★☆☆☆☆'),
            (2, '★★☆☆☆'),
            (3, '★★★☆☆'),
            (4, '★★★★☆'),
            (5, '★★★★★'),
        ],
    )
    created_at = models.DateTimeField(
        verbose_name='Дата создания',
        auto_now_add=True,
        db_index=True,
    )
    is_approved = models.BooleanField(
        verbose_name='Одобрен',
    )

    class Meta:
        verbose_name = 'Комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.author.username}: {self.text[:30]}...'
