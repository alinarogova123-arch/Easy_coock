from django.contrib import admin, messages
from django.core.exceptions import ValidationError
from django.utils.html import format_html

from .models import (
    Allergen,
    Comment,
    Ingredient,
    PromoCode,
    Recipe,
    RecipeIngredient,
    Subscription,
    SubscriptionPlan,
)
from .services.subscriptions import (
    activate_subscription,
    cancel_subscription,
    expire_subscription,
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
    list_display = [
        'user',
        'plan',
        'persons',
        'status',
        'total_paid',
        'activated_at',
        'expires_at',
    ]
    list_filter = ['status', 'plan']
    search_fields = ['user__username', 'user__email']
    raw_id_fields = ['user']
    readonly_fields = [
        'status',
        'created_at',
        'activated_at',
        'expires_at',
        'total_before_discount',
        'discount_amount',
        'total_paid',
    ]
    filter_horizontal = ['excluded_allergens']
    actions = [
        'activate_selected_subscriptions',
        'cancel_selected_subscriptions',
        'expire_selected_subscriptions',
    ]
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

    @admin.action(description='Активировать выбранные подписки')
    def activate_selected_subscriptions(self, request, queryset):
        self.apply_subscription_action(
            request,
            queryset,
            activate_subscription,
            success_message='Активировано подписок: {}.',
            error_message='Не удалось активировать: ',
        )

    @admin.action(description='Отменить выбранные подписки')
    def cancel_selected_subscriptions(self, request, queryset):
        self.apply_subscription_action(
            request,
            queryset,
            cancel_subscription,
            success_message='Отменено подписок: {}.',
            error_message='Не удалось отменить: ',
        )

    @admin.action(description='Пометить истекшими выбранные подписки')
    def expire_selected_subscriptions(self, request, queryset):
        self.apply_subscription_action(
            request,
            queryset,
            expire_subscription,
            success_message='Помечено истекшими подписок: {}.',
            error_message='Не удалось пометить истекшими: ',
        )

    def apply_subscription_action(
        self,
        request,
        queryset,
        action_func,
        success_message,
        error_message,
    ):
        processed_count = 0
        failed_messages = []

        for subscription in queryset.select_related('plan', 'promo_code'):
            try:
                action_func(subscription)
            except ValidationError as error:
                failed_messages.append(
                    f'{subscription}: {"; ".join(error.messages)}'
                )
            else:
                processed_count += 1

        if processed_count:
            self.message_user(
                request,
                success_message.format(processed_count),
                level=messages.SUCCESS,
            )
        if failed_messages:
            self.message_user(
                request,
                error_message + ' | '.join(failed_messages[:5]),
                level=messages.ERROR,
            )


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
                'fields': ('image', 'image_preview'),
            },
        ),
    )

    def image_preview(self, obj):
        if obj.image:
            return format_html(
                '<img src="{}" style="max-width: 200px;" />', obj.image.url
            )


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ['author', 'recipe', 'rating', 'created_at', 'is_approved']
    list_filter = ['is_approved', 'rating', 'created_at']
    search_fields = ['author__username', 'recipe__name', 'text']
    list_editable = ['is_approved']
    readonly_fields = ['created_at']
