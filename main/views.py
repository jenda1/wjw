from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from . import forms

def index(request):
    if request.session.get('new_user_redirect'):
        del request.session['new_user_redirect']

        from django.contrib import messages
        messages.info(request, "Vítejte! Prosím, vyplňte přihlášku do spolku")
        return redirect(reverse('update_profile'))

    return render(request, 'main/index.html')

@login_required
def new_user(request):
    profile_form = forms.ProfileForm(request.user)
    merge_form = forms.RequestMergeUserForm()

    if request.method == 'POST':
        if 'submit_profile' in request.POST:
            profile_form = forms.ProfileForm(request.POST)
            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, 'Váše žádost byla zaregistrována a bude schválena na dalši Výkonné radě spolku.')
                return redirect('home')

        elif 'submit_merge' in request.POST:
            merge_form = forms.RequestMergeUserForm(request.POST)
            if merge_form.is_valid():
                merge_form.save()
                messages.success(request, 'Váše žádost byla zaregistrována hned jak ji zkontrolujeme vás budeme informovat emailem.')
                return redirect('home')

    return render(request, 'main/new_user.html', {
        'profile_form': profile_form,
        'merge_form': merge_form,
    })


@login_required
def profile_update(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Váš profil byl úspěšně aktualizován!')
            return redirect('home')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'main/profile_update.html', {'form': form})


def profile_merge(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Váš profil byl úspěšně aktualizován!')
            return redirect('home')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'main/profile_new.html', {'form': form})
  
