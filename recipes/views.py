from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST
from .models import (
    Recipe,
    Ingredient,
    RecipeIngredient,
    SubscriptionPlan,
    Subscription
)

from .forms import LoginForm, RegistrationForm


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

    return render(request, "lk.html", {})


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
        all_calories = Recipe.objects.get(id = recipe.id).calories
        recipe_for_card['all_calories'] = all_calories
        recipe_for_card['images'] = recipe.images.url
        recipes_for_card.append(recipe_for_card)



    return render(request, "card.html", {"recipes_for_card":recipes_for_card})

def get_order(request):

    return render(request, "order.html", {})




    
