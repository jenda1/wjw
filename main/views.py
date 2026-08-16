from typing import cast

from allauth.socialaccount.models import SocialAccount

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import Manager
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from . import forms
from .models import ParentRelationship, Profile, ProfileMergeRequest, ProfileStudentRequest, Student
from .permissions import approver_required, view_others_required

def is_member(profile: Profile | None) -> bool:
    return profile is not None and profile.status == Profile.ProfileStatus.ACTIVE


# Bootstrap Icons pro poskytovatele, kteří v nich mají oficiální ikonu (viz přihlašovací stránka).
SOCIAL_PROVIDER_ICONS = {
    'google': 'bi-google',
    'facebook': 'bi-facebook',
}

# Ostatní poskytovatelé nemají ikonu v Bootstrap Icons - použije se stejný obrázek
# jako na přihlašovací stránce (templates/account/login.html).
SOCIAL_PROVIDER_ICON_IMAGES = {
    'seznam': 'main/images/seznam-icon.png',
    'mojeid': 'main/images/mojeid-icon.png',
}


def get_connected_social_accounts(user):
    """Vrátí propojené účty (Google/Facebook/Seznam/MojeID/...) s ikonou poskytovatele a e-mailem."""
    accounts = []
    for account in user.socialaccount_set.all():
        email = account.extra_data.get('email') or account.extra_data.get('username') or user.username
        icon_image = SOCIAL_PROVIDER_ICON_IMAGES.get(account.provider)
        accounts.append({
            'provider': account.provider,
            'icon': None if icon_image else SOCIAL_PROVIDER_ICONS.get(account.provider, 'bi-person-circle'),
            'icon_image': icon_image,
            'email': email,
        })
    return accounts


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
    assert profile is not None

    pending_student_requests = profile.profilestudentrequest_set.filter(
        status=ProfileStudentRequest.RequestStatus.PENDING
    )

    return render(request, 'main/home.html', {
        'user': request.user,
        'pending_student_requests': pending_student_requests,
        'connected_social_accounts': get_connected_social_accounts(request.user),
    })




@login_required
def profile_edit(request: HttpRequest):
    user = request.user
    profile = getattr(user, 'profile', None)

    if profile is None:
        return redirect(reverse('new_user'))

    if request.method == 'POST':
        profile_form = forms.ProfileForm(user, request.POST, instance=profile, allow_membership_change=False)

        if profile_form.is_valid():
            profile_form.save()
            messages.success(request, 'Vaše údaje byly úspěšně uloženy.')
            return redirect('home')
    else:
        profile_form = forms.ProfileForm(user, instance=profile, allow_membership_change=False)

    return render(request, 'main/profile_edit.html', {
        'profile_form': profile_form,
    })


@login_required
def add_student(request: HttpRequest):
    user = request.user
    profile = getattr(user, 'profile', None)

    if not is_member(profile):
        return redirect(reverse('index'))

    if request.method == 'POST':
        form = forms.ProfileStudentRequestForm(request.POST)
        if form.is_valid():
            student_request = form.save(commit=False)
            student_request.profile = profile
            student_request.save()
            messages.success(request, 'Žádost o přidání dítěte byla zaregistrována.')
            return redirect('home')
    else:
        form = forms.ProfileStudentRequestForm()

    return render(request, 'main/add_student.html', {
        'form': form,
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


@approver_required
def merge_requests(request: HttpRequest):
    pending_requests = ProfileMergeRequest.objects.filter(
        status=ProfileMergeRequest.RequestStatus.PENDING
    ).select_related('user', 'student_by_name').order_by('id')

    return render(request, 'main/merge_requests.html', {
        'merge_requests': pending_requests,
    })


@approver_required
def merge_request_detail(request: HttpRequest, pk: int):
    merge_request = get_object_or_404(
        ProfileMergeRequest, pk=pk, status=ProfileMergeRequest.RequestStatus.PENDING
    )

    # Hlavní signál pro nalezení účtu ke sloučení je dřívější e-mail (unikátní díky
    # ACCOUNT_UNIQUE_EMAIL) - ověřený žák podle jména slouží jen jako doplňkový tip.
    candidate_users: list[User] = []

    email_match = User.objects.filter(email__iexact=merge_request.old_email).first()
    if email_match:
        candidate_users.append(email_match)

    matched_student = cast('Student | None', merge_request.student_by_name)
    if matched_student:
        for profile in matched_student.parents.select_related('user').all():
            parent_user = cast(User, profile.user)
            if parent_user not in candidate_users:
                candidate_users.append(parent_user)

    if request.method == 'POST':
        if 'reject' in request.POST:
            merge_request.status = ProfileMergeRequest.RequestStatus.REJECTED
            merge_request.save()
            messages.success(request, 'Žádost o sloučení účtů byla zamítnuta.')
            return redirect('merge_requests')

        form = forms.MergeRequestApprovalForm(request.POST, candidate_users=candidate_users)
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
        form = forms.MergeRequestApprovalForm(candidate_users=candidate_users)

    return render(request, 'main/merge_request_detail.html', {
        'merge_request': merge_request,
        'form': form,
        'candidate_users': candidate_users,
    })


@approver_required
def membership_requests(request: HttpRequest):
    pending_profiles = Profile.objects.filter(
        status=Profile.ProfileStatus.PENDING
    ).select_related('user').order_by('id')

    return render(request, 'main/membership_requests.html', {
        'profiles': pending_profiles,
    })


@approver_required
def membership_request_detail(request: HttpRequest, pk: int):
    profile: Profile = get_object_or_404(Profile, pk=pk, status=Profile.ProfileStatus.PENDING)
    student_requests_manager = cast('Manager[ProfileStudentRequest]', profile.profilestudentrequest_set)
    student_requests = student_requests_manager.all()

    if request.method == 'POST':
        if 'reject' in request.POST:
            profile.status = Profile.ProfileStatus.CANCELLED
            profile.save()
            messages.success(request, 'Žádost o členství byla zamítnuta.')
        else:
            profile.status = Profile.ProfileStatus.ACTIVE
            profile.save()
            messages.success(request, 'Žádost o členství byla schválena.')

        return redirect('membership_requests')

    return render(request, 'main/membership_request_detail.html', {
        'profile': profile,
        'student_requests': student_requests,
    })


@approver_required
def student_requests(request: HttpRequest):
    pending_requests = ProfileStudentRequest.objects.filter(
        status=ProfileStudentRequest.RequestStatus.PENDING
    ).select_related('profile__user', 'student_by_name').order_by('id')

    return render(request, 'main/student_requests.html', {
        'student_requests': pending_requests,
    })


@approver_required
def student_request_detail(request: HttpRequest, pk: int):
    student_request: ProfileStudentRequest = get_object_or_404(
        ProfileStudentRequest, pk=pk, status=ProfileStudentRequest.RequestStatus.PENDING
    )

    if request.method == 'POST':
        if 'reject' in request.POST:
            student_request.status = ProfileStudentRequest.RequestStatus.REJECTED
            student_request.save()
            messages.success(request, 'Žádost o přidání žáka byla zamítnuta.')
            return redirect('student_requests')

        form = forms.StudentRequestApprovalForm(request.POST)
        if form.is_valid():
            student = form.cleaned_data['student']

            with transaction.atomic():
                ParentRelationship.objects.get_or_create(parent=student_request.profile, student=student)

                student_request.student_by_name = student
                student_request.status = ProfileStudentRequest.RequestStatus.APPROVED
                student_request.save()

            messages.success(request, 'Žák byl úspěšně přiřazen k rodiči.')
            return redirect('student_requests')
    else:
        form = forms.StudentRequestApprovalForm(initial={'student': student_request.student_by_name})

    return render(request, 'main/student_request_detail.html', {
        'student_request': student_request,
        'form': form,
    })


@view_others_required
def orphan_students(request: HttpRequest):
    students = Student.objects.filter(parents__isnull=True).select_related('school_class').order_by(
        'last_name', 'first_name'
    )

    return render(request, 'main/orphan_students.html', {
        'students': students,
    })
