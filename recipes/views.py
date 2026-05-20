from django.shortcuts import render


def index(request):

	return render(request, "index.html", {})


def authentication(request):

    return render(request, "auth.html", {})


def registration(request):

    return render(request, "registration.html", {})


def lk(request):

    return render(request, "lk.html", {})

def get_card(request, card_num):

    return render(request, "card.html", {})

    
