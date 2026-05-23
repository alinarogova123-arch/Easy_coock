from collections import defaultdict
from decimal import Decimal

from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from .forms import LoginForm, OrderForm, RegistrationForm
from .models import Allergen, Recipe, Subscription, SubscriptionStatus
from .services.menu_generator import generate_daily_menu


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

    context = {
        'subscriptions': subscriptions,
    }

    return render(request, "lk.html", context)


@require_POST
def logout_user(request):
    logout(request)
    return redirect('home')


def get_card(request):
    recipes = Recipe.objects.all()[:3]
    recipes_for_card = []
    for recipe in recipes:
        recipe_for_card = {}
        all_calories = 0
        recipe_for_card['name'] = recipe.name
        recipe_for_card['ingredients'] = recipe.ingredients.all()
        all_calories = Recipe.objects.get(id=recipe.id).calories
        recipe_for_card['all_calories'] = all_calories
        recipe_for_card['images'] = recipe.images.url
        recipe_for_card['instruction'] = recipe.instruction
        recipes_for_card.append(recipe_for_card)

    return render(request, "card.html", {"recipes_for_card": recipes_for_card})


@login_required(login_url='auth')
def get_order(request):
    if request.method == 'POST':
        form = OrderForm(request.POST)
        if form.is_valid():
            subscription = form.save(request.user)
            messages.success(
                request,
                (
                    'Заявка на подписку создана. '
                    f'Статус: {subscription.get_status_display()}.'
                ),
            )
            return redirect('order')
    else:
        form = OrderForm()

    order_values = {
        'menu_type': request.POST.get('menu_type', 'classic'),
        'plan_duration': request.POST.get('plan_duration', '1'),
        'has_breakfast': request.POST.get('has_breakfast', '1'),
        'has_lunch': request.POST.get('has_lunch', '1'),
        'has_dinner': request.POST.get('has_dinner', '1'),
        'has_dessert': request.POST.get('has_dessert', '1'),
        'persons': request.POST.get('persons', '1'),
        'promo_code': request.POST.get('promo_code', ''),
    }

    context = {
        'form': form,
        'order_values': order_values,
        'allergens': Allergen.objects.order_by('name'),
        'selected_allergen_ids': request.POST.getlist('excluded_allergens'),
    }
    return render(request, "order.html", context)


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
