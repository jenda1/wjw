from django.db import transaction
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.shortcuts import redirect, render
from django.urls import reverse

from . import forms
from .models import Profile


def is_member(profile: Profile | None) -> bool:
    return profile is not None and profile.status == Profile.ProfileStatus.ACTIVE


def index(request: HttpRequest):
    msgs = messages.get_messages(request)
    if 'prvni_login' in [m.message for m in msgs]:
        return redirect(reverse('new_user'))

    user = request.user if request.user.is_authenticated else None
    profile = getattr(user, 'profile', None)

    if is_member(profile):
        return redirect(reverse('home'))

    return render(request, 'main/index.html', {
        'user': request.user,
        'is_known': profile is not None,
    })


@login_required
def home(request: HttpRequest):
    user = request.user if request.user.is_authenticated else None
    profile = getattr(user, 'profile', None)

    if not is_member(profile):
        return redirect(reverse('index'))

    return render(request, 'main/home.html', {
        'user': request.user,
    })




@login_required
def new_user(request: HttpRequest):
    user = request.user
    profile_form = forms.ProfileForm()
    students_form = forms.ProfileStudentRequestFormSet()
    merge_form = forms.ProfileMergeRequestForm()

    if request.method == 'POST':
        if 'submit_profile' in request.POST:
            profile_form = forms.ProfileForm(request.POST)
            students_form = forms.ProfileStudentRequestFormSet(request.POST)

            if profile_form.is_valid() and students_form.is_valid():
                with transaction.atomic():
                    profile = profile_form.save(commit=False)
                    profile.user = user
                    profile.save()

                    for student_form in students_form:
                        # Přeskočíme prázdné (nevyplněné) formuláře, např. nevyužitý extra formulář
                        if not student_form.cleaned_data or not student_form.cleaned_data.get('student_name'):
                            continue

                        student_request = student_form.save(commit=False)
                        student_request.profile = profile
                        student_request.save()

                messages.success(request, 'Váše žádost byla zaregistrována a bude schválena na dalši Výkonné radě spolku.')
                return redirect('index')

        elif 'submit_merge' in request.POST:
            merge_form = forms.ProfileMergeRequestForm(request.POST)
            if merge_form.is_valid():
                merge_form.instance.user = request.user
                merge_form.save()

                messages.success(request, 'Váše žádost byla zaregistrována hned jak ji zkontrolujeme vás budeme informovat emailem.')
                return redirect('index')

    return render(request, 'main/new_user.html', {
        'profile_form': profile_form,
        'students_form': students_form,
        'merge_form': merge_form,
        'profile_form_is_valid': profile_form.is_valid() and students_form.is_valid(),
    })
