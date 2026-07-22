from typing import cast

from allauth.socialaccount.models import SocialAccount

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from . import forms
from .models import Profile, ProfileMergeRequest


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
def profile_edit(request: HttpRequest):
    user = request.user
    profile = getattr(user, 'profile', None)

    if profile is None:
        return redirect(reverse('new_user'))

    if request.method == 'POST':
        profile_form = forms.ProfileForm(user, request.POST, instance=profile)

        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Vaše údaje byly úspěšně uloženy.')
            return redirect('home')
    else:
        profile_form = forms.ProfileForm(user, instance=profile)

    return render(request, 'main/profile_edit.html', {
        'profile_form': profile_form,
    })


@login_required
def new_user(request: HttpRequest):
    user = request.user
    profile_form = forms.ProfileForm(user)
    students_form = forms.ProfileStudentRequestFormSet()
    merge_form = forms.ProfileMergeRequestForm()

    if request.method == 'POST':
        if 'submit_profile' in request.POST:
            profile_form = forms.ProfileForm(user, request.POST)
            students_form = forms.ProfileStudentRequestFormSet(request.POST)

            if profile_form.is_valid() and students_form.is_valid():
                with transaction.atomic():
                    profile_form.instance.user = user
                    profile = profile_form.save()

                    for student_form in students_form:
                        # Přeskočíme prázdné (nevyplněné) formuláře, např. nevyužitý extra formulář
                        if not student_form.cleaned_data or not student_form.cleaned_data.get('last_name'):
                            continue

                        student_request = student_form.save(commit=False)
                        student_request.profile = profile
                        student_request.save()

                messages.success(
                    request, 'Váše žádost byla zaregistrována a bude schválena na dalši Výkonné radě spolku.'
                )
                return redirect('index')

        elif 'submit_merge' in request.POST:
            merge_form = forms.ProfileMergeRequestForm(request.POST)
            if merge_form.is_valid():
                merge_form.instance.user = request.user
                merge_form.save()

                messages.success(
                    request, 'Váše žádost byla zaregistrována hned jak ji zkontrolujeme vás budeme informovat emailem.'
                )
                return redirect('index')

    return render(request, 'main/new_user.html', {
        'profile_form': profile_form,
        'students_form': students_form,
        'merge_form': merge_form,
        'profile_form_is_valid': profile_form.is_valid() and students_form.is_valid(),
    })


@staff_member_required
def merge_requests(request: HttpRequest):
    pending_requests = ProfileMergeRequest.objects.filter(
        status=ProfileMergeRequest.RequestStatus.PENDING
    ).select_related('user', 'student_by_name').order_by('id')

    return render(request, 'main/merge_requests.html', {
        'merge_requests': pending_requests,
    })


@staff_member_required
def merge_request_detail(request: HttpRequest, pk: int):
    merge_request = get_object_or_404(
        ProfileMergeRequest, pk=pk, status=ProfileMergeRequest.RequestStatus.PENDING
    )

    if request.method == 'POST':
        if 'reject' in request.POST:
            merge_request.status = ProfileMergeRequest.RequestStatus.REJECTED
            merge_request.save()
            messages.success(request, 'Žádost o sloučení účtů byla zamítnuta.')
            return redirect('merge_requests')

        form = forms.MergeRequestApprovalForm(request.POST)
        if form.is_valid():
            target_user = form.cleaned_data['target_user']
            requester = cast('User | None', merge_request.user)

            with transaction.atomic():
                if requester is not None:
                    SocialAccount.objects.filter(user=requester).update(user=target_user)

                merge_request.status = ProfileMergeRequest.RequestStatus.APPROVED
                merge_request.save()

                if requester is not None:
                    requester.delete()

            messages.success(request, 'Účty byly úspěšně sloučeny.')
            return redirect('merge_requests')
    else:
        form = forms.MergeRequestApprovalForm()

    return render(request, 'main/merge_request_detail.html', {
        'merge_request': merge_request,
        'form': form,
    })
