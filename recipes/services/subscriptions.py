from calendar import monthrange

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from ..models import PromoCode, Subscription, SubscriptionStatus
from .promo import validate_promo_code


def add_months(value, months):
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


def activate_subscription(subscription, activated_at=None):
    current_time = activated_at or timezone.now()

    with transaction.atomic():
        subscription = (
            Subscription.objects.select_for_update()
            .select_related('plan', 'promo_code')
            .get(pk=subscription.pk)
        )

        if subscription.status != SubscriptionStatus.PENDING:
            raise ValidationError(
                'Активировать можно только подписку в статусе ожидания.'
            )
        if not subscription.selected_food_types:
            raise ValidationError(
                'Нельзя активировать подписку без выбранных приёмов пищи.'
            )

        if subscription.promo_code_id:
            promo_code = PromoCode.objects.select_for_update().get(
                pk=subscription.promo_code_id
            )
            validate_promo_code(promo_code, now=current_time)
            promo_code.used_count += 1
            promo_code.save(update_fields=['used_count'])

        subscription.status = SubscriptionStatus.ACTIVE
        subscription.activated_at = current_time
        subscription.expires_at = add_months(
            current_time,
            subscription.plan.duration,
        )
        subscription.save(
            update_fields=['status', 'activated_at', 'expires_at']
        )

    return subscription
