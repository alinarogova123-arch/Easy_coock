from django.contrib import admin
from django.utils.html import format_html

from .models import (
    Allergen,
    Ingredient,
    PromoCode,
    Recipe,
    RecipeIngredient,
    Subscription,
    SubscriptionPlan,
)


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ['name', 'duration', 'price_coefficient', 'is_active']


@admin.register(Allergen)
class AllergenAdmin(admin.ModelAdmin):
    list_display = ['name']
    search_fields = ['name']


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ['name', 'unit']
    search_fields = ['name']


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = [
        'code',
        'discount_percent',
        'valid_until',
        'is_active',
        'max_uses',
        'used_count',
    ]
    list_filter = ['is_active']
    search_fields = ['code']


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ['user', 'plan', 'persons', 'status', 'expires_at']
    list_filter = ['status', 'plan']
    search_fields = ['user__username', 'user__email']
    raw_id_fields = ['user']
    readonly_fields = ['created_at', 'activated_at']
    filter_horizontal = ['excluded_allergens']
    fields = [
        'user',
        'plan',
        'menu_type',
        'persons',
        'has_breakfast',
        'has_lunch',
        'has_dinner',
        'has_dessert',
        'excluded_allergens',
        'status',
        'created_at',
        'activated_at',
        'expires_at',
        'promo_code',
        'total_before_discount',
        'discount_amount',
        'total_paid',
    ]


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    fields = ['ingredient', 'amount', 'price']
    autocomplete_fields = ['ingredient']


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ['name', 'food_type', 'menu_type', 'cooking_time']
    list_filter = ['food_type', 'menu_type']
    search_fields = ['name']
    readonly_fields = ['image_preview']
    inlines = [RecipeIngredientInline]
    filter_horizontal = ['allergens']
    fieldsets = (
        (
            'Основная информация',
            {
                'fields': (
                    'name',
                    'description',
                    'instruction',
                    'cooking_time',
                    'calories',
                )
            },
        ),
        ('Классификация', {'fields': ('food_type', 'menu_type', 'allergens')}),
        (
            'Медиа',
            {
                'fields': ('images', 'image_preview'),
            },
        ),
    )

    def image_preview(self, obj):
        if obj.images:
            return format_html(
                '<img src="{}" style="max-width: 200px;" />', obj.images.url
            )
