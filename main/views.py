from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.contrib import messages
from .forms import ProfileForm

def index(request):
    if request.session.get('new_user_redirect'):
        del request.session['new_user_redirect']

        from django.contrib import messages
        messages.info(request, "Vítejte! Prosím, vyplňte přihlášku do spolku")
        return redirect(reverse('user_config'))

    return render(request, 'main/index.html')


@login_required
def update_profile(request):
    user = request.user
    profile = user.profile

    if request.method == 'POST':
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Váš profil byl úspěšně aktualizován!')
            return redirect('update_profile')
    else:
        form = ProfileForm(instance=profile)

    return render(request, 'main/update_profile.html', {'form': form})
