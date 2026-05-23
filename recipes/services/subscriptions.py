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


def cancel_subscription(subscription):
    with transaction.atomic():
        subscription = Subscription.objects.select_for_update().get(
            pk=subscription.pk
        )

        if subscription.status not in (
            SubscriptionStatus.PENDING,
            SubscriptionStatus.ACTIVE,
        ):
            raise ValidationError(
                'Отменить можно только ожидающую или активную подписку.'
            )

        subscription.status = SubscriptionStatus.CANCELLED
        subscription.save(update_fields=['status'])

    return subscription


def expire_subscription(subscription, expired_at=None):
    current_time = expired_at or timezone.now()

    with transaction.atomic():
        subscription = Subscription.objects.select_for_update().get(
            pk=subscription.pk
        )

        if subscription.status != SubscriptionStatus.ACTIVE:
            raise ValidationError(
                'Истечь может только активная подписка.'
            )
        if subscription.expires_at is None:
            raise ValidationError(
                'Нельзя завершить подписку без даты окончания.'
            )
        if subscription.expires_at > current_time:
            raise ValidationError(
                'Срок подписки ещё не истёк.'
            )

        subscription.status = SubscriptionStatus.EXPIRED
        subscription.save(update_fields=['status'])

    return subscription


def expire_due_subscriptions(expired_at=None):
    current_time = expired_at or timezone.now()
    subscriptions = Subscription.objects.filter(
        status=SubscriptionStatus.ACTIVE,
        expires_at__lte=current_time,
    )

    expired_count = 0
    for subscription in subscriptions:
        expire_subscription(subscription, expired_at=current_time)
        expired_count += 1

    return expired_count
