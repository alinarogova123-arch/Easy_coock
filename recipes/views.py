from django.contrib.auth import login
from django.shortcuts import redirect, render

from .forms import RegistrationForm


def index(request):

	return render(request, "index.html", {})


def authentication(request):

    return render(request, "auth.html", {})


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


def lk(request):

    return render(request, "lk.html", {})

def get_card(request, card_num):

    return render(request, "card.html", {})

def get_order(request):

    return render(request, "order.html", {})


    
