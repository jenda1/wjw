from typing import cast

from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse

from users.models import MyUser

from . import forms
from .models import Profile


def index(request: HttpRequest):
    msgs = messages.get_messages(request)
    if 'prvni_login' in [m.message for m in msgs]:
        return redirect(reverse('new_user'))

    user = cast(MyUser, request.user) if request.user.is_authenticated else None
    profile = user and user.profile

    if profile and profile.status == Profile.ProfileStatus.ACTIVE[0]:
        return redirect(reverse('actual'))

    return render(request, 'main/index.html', {
        'user': request.user,
        'is_known': profile is not None,
    })


@login_required
def new_user(request: HttpRequest):
    user = cast(MyUser, request.user)
    profile_form = forms.ProfileForm(user)
    students_form = forms.ProfileStudentRequestFormSet()
    merge_form = forms.ProfileMergeRequestForm()

    if request.method == 'POST':
        if 'submit_profile' in request.POST:
            profile_form = forms.ProfileForm(request.user, request.POST)
            students_form = forms.ProfileStudentRequestFormSet(request.POST)

            if profile_form.is_valid() and students_form.is_valid():
                with transaction.atomic():
                    profile = profile_form.save()
                    user.profile = profile
                    user.save()
                    students_form.save()

                messages.success(request, 'Váše žádost byla zaregistrována a bude schválena na dalši Výkonné radě spolku.')
                return redirect('home')

        elif 'submit_merge' in request.POST:
            merge_form = forms.ProfileMergeRequestForm(request.POST)
            if merge_form.is_valid():
                merge_form.instance.user = request.user
                merge_form.save()

                messages.success(request, 'Váše žádost byla zaregistrována hned jak ji zkontrolujeme vás budeme informovat emailem.')
                return redirect('home')

    return render(request, 'main/new_user.html', {
        'profile_form': profile_form,
        'students_form': students_form,
        'merge_form': merge_form,
        'profile_form_is_valid': profile_form.is_valid() and students_form.is_valid(),
    })
