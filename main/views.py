from typing import cast

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse

from users.models import MyUser

from . import forms
from .models import Profile


def index(request: HttpRequest):
    user = cast(MyUser, request.user) if request.user.is_authenticated else None

    msgs = messages.get_messages(request)
    if 'prvni_login' in [m.message for m in msgs]:
        return redirect(reverse('new_user'))

    return render(request, 'main/index.html', {
        'user': request.user,
        'is_known': user and user.profile,  # or user.profile_merge_request),
        'is_member': user and user.profile and user.profile.status == Profile.ProfileStatus.APPROVED,
    })


@login_required
def new_user(request: HttpRequest):
    profile_form = forms.ProfileForm(request.user)
    merge_form = forms.RequestMergeUserForm()

    if request.method == 'POST':
        if 'submit_profile' in request.POST:
            profile_form = forms.ProfileForm(request.user, request.POST)
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
