from django.shortcuts import render, redirect
from django.urls import reverse


def index(request):
    if request.session.get('new_user_redirect'):
        del request.session['new_user_redirect']

        from django.contrib import messages
        messages.info(request, "Vítejte! Prosím, vyplňte přihlášku do spolku")
        return redirect(reverse('user_config'))

    return render(request, 'main/index.html')


def user_config(request):
    return render(request, 'main/user_config.html')
