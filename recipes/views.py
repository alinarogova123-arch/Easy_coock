from collections import defaultdict
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_GET
from django.views.decorators.http import require_POST

from .forms import CommentForm, LoginForm, OrderForm, RegistrationForm
from .models import (
    Allergen,
    Recipe,
    Subscription,
    SubscriptionPlan,
    SubscriptionStatus,
)
from .services.menu_generator import generate_daily_menu
from .services.payments import (
    PaymentError,
    create_payment,
    get_payment_info,
    update_subscription_from_payment,
)
from .services.subscriptions import activate_subscription
from .services.validators import MONEY_QUANT


def index(request):

    return render(request, "index.html", {})


def authentication(request):
    if request.method == 'POST':
        form = LoginForm(request, request.POST)
        if form.is_valid():
            login(request, form.get_user())
            return redirect('lk')
    else:
        form = LoginForm()

    return render(request, "auth.html", {'form': form})


def registration(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('order')
    else:
        form = RegistrationForm()

    return render(request, "registration.html", {'form': form})


@login_required(login_url='auth')
def lk(request):
    subscriptions = (
        request.user.subscriptions.filter(status=SubscriptionStatus.ACTIVE)
        .select_related('plan')
        .prefetch_related('excluded_allergens')
    )
    pending_subscriptions = (
        request.user.subscriptions.filter(status=SubscriptionStatus.PENDING)
        .select_related('plan')
        .prefetch_related('excluded_allergens')
        .order_by('-created_at')
    )

    context = {
        'subscriptions': subscriptions,
        'pending_subscriptions': pending_subscriptions,
    }

    return render(request, "lk.html", context)


@require_POST
def logout_user(request):
    logout(request)
    return redirect('home')


@login_required(login_url='auth')
def get_order(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            subscription = form.save(request.user)
            request.session['pending_subscription_id'] = subscription.id
            messages.success(
                request,
                (
                    'Заявка на подписку создана. '
                    'Сейчас перейдём к оплате.'
                ),
            )
            return redirect('payment_create')
    else:
        form = OrderForm()

    order_values = {
        'menu_type': request.POST.get('menu_type', 'classic'),
        'plan_duration': int(request.POST.get('plan_duration', '1')),
        'has_breakfast': request.POST.get('has_breakfast', '1'),
        'has_lunch': request.POST.get('has_lunch', '1'),
        'has_dinner': request.POST.get('has_dinner', '1'),
        'has_dessert': request.POST.get('has_dessert', '1'),
        'persons': request.POST.get('persons', '1'),
        'promo_code': request.POST.get('promo_code', ''),
    }

    subscription_plans = SubscriptionPlan.objects.filter(
        is_active=True
    ).order_by('duration')
    price_coefficients = {
        str(plan.duration): float(plan.price_coefficient) * plan.duration
        for plan in subscription_plans
    }

    context = {
        'form': form,
        'order_values': order_values,
        'allergens': Allergen.objects.order_by('name'),
        'selected_allergen_ids': request.POST.getlist('excluded_allergens'),
        'breakfast_price': settings.BREAKFAST_PRICE,
        'lunch_price': settings.LUNCH_PRICE,
        'dinner_price': settings.DINNER_PRICE,
        'dessert_price': settings.DESSERT_PRICE,
        'price_coefficients': price_coefficients,
        'subscription_plans': subscription_plans,
    }
    return render(request, "order.html", context)


def build_payment_return_url(subscription_id):
    separator = '&' if '?' in settings.YOOKASSA_RETURN_URL else '?'
    return f'{settings.YOOKASSA_RETURN_URL}{separator}subscription_id={subscription_id}'


def get_payment_subscription_id(request):
    return (
        request.GET.get('subscription_id')
        or request.session.get('pending_subscription_id')
    )


def clear_pending_subscription_session(request, subscription):
    if request.session.get('pending_subscription_id') == subscription.id:
        del request.session['pending_subscription_id']


def payment_amount_matches_subscription(subscription):
    if not subscription.payment_id:
        return False

    try:
        payment_info = get_payment_info(subscription.payment_id)
        payment_amount = Decimal(str(payment_info.get('amount')))
    except (PaymentError, InvalidOperation, TypeError):
        return False

    return (
        payment_amount.quantize(MONEY_QUANT)
        == subscription.total_paid.quantize(MONEY_QUANT)
    )


@login_required(login_url='auth')
@require_GET
def payment_create(request):
    subscription_id = get_payment_subscription_id(request)
    if not subscription_id:
        messages.error(request, 'Подписка для оплаты не найдена.')
        return redirect('order')

    subscription = get_object_or_404(
        Subscription,
        id=subscription_id,
        user=request.user,
    )

    if subscription.status == SubscriptionStatus.ACTIVE:
        clear_pending_subscription_session(request, subscription)
        messages.info(request, 'Подписка уже активна.')
        return redirect('lk')

    if subscription.status != SubscriptionStatus.PENDING:
        clear_pending_subscription_session(request, subscription)
        messages.error(request, 'Эту подписку уже нельзя оплатить.')
        return redirect('lk')

    if subscription.is_paid:
        try:
            activate_subscription(subscription)
        except ValidationError as error:
            messages.error(request, '; '.join(error.messages))
        else:
            clear_pending_subscription_session(request, subscription)
            messages.success(request, 'Оплата уже получена. Подписка активирована.')
        return redirect('lk')

    if (
        subscription.payment_status in ('pending', 'waiting_for_capture')
        and subscription.confirmation_url
    ):
        if payment_amount_matches_subscription(subscription):
            return redirect(subscription.confirmation_url)

        subscription.payment_id = None
        subscription.payment_status = ''
        subscription.confirmation_url = ''
        subscription.save(
            update_fields=['payment_id', 'payment_status', 'confirmation_url']
        )

    try:
        payment_info = create_payment(
            subscription,
            return_url=build_payment_return_url(subscription.id),
        )
    except PaymentError as error:
        messages.error(request, f'Ошибка оплаты: {error}')
        return redirect('order')

    request.session['pending_subscription_id'] = subscription.id
    return redirect(payment_info['confirmation_url'])


@login_required(login_url='auth')
@require_GET
def payment_callback(request):
    subscription_id = get_payment_subscription_id(request)
    if not subscription_id:
        messages.warning(request, 'Подписка для проверки оплаты не найдена.')
        return redirect('order')

    subscription = get_object_or_404(
        Subscription,
        id=subscription_id,
        user=request.user,
    )

    if not subscription.payment_id:
        clear_pending_subscription_session(request, subscription)
        messages.error(request, 'Платёж для подписки не найден.')
        return redirect('order')

    try:
        payment_info = get_payment_info(subscription.payment_id)
    except PaymentError as error:
        messages.error(request, f'Ошибка проверки платежа: {error}')
        return redirect('lk')

    subscription = update_subscription_from_payment(subscription, payment_info)

    if subscription.is_paid:
        try:
            activate_subscription(subscription)
        except ValidationError as error:
            messages.error(request, '; '.join(error.messages))
        else:
            clear_pending_subscription_session(request, subscription)
            messages.success(request, 'Оплата получена. Подписка активирована.')
        return redirect('lk')

    messages.info(
        request,
        f'Платёж пока не завершён. Статус: {subscription.payment_status_text()}',
    )
    request.session['pending_subscription_id'] = subscription.id
    return redirect('lk')


@login_required
def get_daily_menu(request, subscription_id):
    subscription = get_object_or_404(
        Subscription,
        id=subscription_id,
        user=request.user,
        status=SubscriptionStatus.ACTIVE,
    )

    daily_menu = generate_daily_menu(subscription)

    recipes = []
    if daily_menu.breakfast:
        recipes.append(daily_menu.breakfast)
    if daily_menu.lunch:
        recipes.append(daily_menu.lunch)
    if daily_menu.dinner:
        recipes.append(daily_menu.dinner)
    if daily_menu.dessert:
        recipes.append(daily_menu.dessert)

    shopping_dict = defaultdict(
        lambda: {'amount': 0, 'price': Decimal('0'), 'unit': ''}
    )
    total_price = Decimal(0)

    for recipe in recipes:
        for recipe_ingredient in recipe.ingredients.select_related(
            'ingredient'
        ):
            name = recipe_ingredient.ingredient.name
            shopping_dict[name]['amount'] += recipe_ingredient.amount
            shopping_dict[name]['price'] += recipe_ingredient.price
            shopping_dict[name]['unit'] = recipe_ingredient.ingredient.unit
            total_price += recipe_ingredient.price

    shopping_list = []
    for name, data in shopping_dict.items():
        shopping_list.append(
            {
                'name': name,
                'amount': data['amount'],
                'unit': data['unit'],
                'price': data['price'],
            }
        )

    context = {
        'subscription': subscription,
        'daily_menu': daily_menu,
        'recipes': recipes,
        'shopping_list': shopping_list,
        'total_price': total_price,
        'date': daily_menu.date,
    }

    return render(request, 'subscription_menu.html', context)


def can_view_recipe(user, recipe):
    if user.is_staff:
        return True

    today_date = timezone.now().date()
    return (
        Subscription.objects.filter(
            user=user,
            status=SubscriptionStatus.ACTIVE,
            daily_menus__date=today_date,
        )
        .filter(
            Q(daily_menus__breakfast=recipe)
            | Q(daily_menus__lunch=recipe)
            | Q(daily_menus__dinner=recipe)
            | Q(daily_menus__dessert=recipe)
        )
        .exists()
    )


@login_required(login_url='auth')
def recipe_detail(request, recipe_id):
    recipe = get_object_or_404(Recipe, id=recipe_id)

    if not can_view_recipe(request.user, recipe):
        messages.error(
            request,
            'Этот рецепт доступен только из вашего активного меню на сегодня.',
        )
        return redirect('lk')

    comments = recipe.comments.filter(is_approved=True).select_related(
        'author'
    )

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.recipe = recipe
            comment.author = request.user
            comment.save()
            messages.success(
                request, 'Комментарий добавлен и отправлен на модерацию.'
            )
            return redirect('recipe', recipe_id=recipe.id)
    else:
        form = CommentForm()

    context = {
        'recipe': recipe,
        'comments': comments,
        'form': form,
    }

    return render(request, 'recipe.html', context)
