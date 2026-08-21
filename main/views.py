from typing import cast

from allauth.socialaccount.models import SocialAccount

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Manager, Q
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from wagtail.query import PageQuerySet

from . import forms
from .models import (
    Circle,
    CircleMembership,
    ClassCollective,
    ClassRepresentative,
    ParentRelationship,
    Profile,
    ProfileMergeRequest,
    ProfileStudentRequest,
    Student,
)
from .permissions import (
    CAPO_DI_TUTTI_GROUP_NAME,
    VR_MEMBER_GROUP_NAME,
    approver_required,
    can_view_all_classes,
    view_others_required,
)

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
    'seznam': 'main/images/seznam-logo-esko-18-cervena.svg',
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

    pending_student_requests = profile.profilestudentrequest_set.filter(
        status=ProfileStudentRequest.RequestStatus.PENDING
    ) if profile is not None else ProfileStudentRequest.objects.none()

    return render(request, 'main/index.html', {
        'user': request.user,
        'is_known': profile is not None,
        'pending_student_requests': pending_student_requests,
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
    user = cast(User, request.user)
    profile = getattr(user, 'profile', None)

    if profile is None:
        return redirect(reverse('new_user'))

    if request.method == 'POST':
        old_email = user.email
        profile_form = forms.ProfileForm(
            user, request.POST, instance=profile, allow_membership_change=False, allow_email_change=True
        )

        if profile_form.is_valid():
            new_email = profile_form.cleaned_data['email']
            social_emails = {
                account['email'].lower()
                for account in get_connected_social_accounts(user)
                if account['email']
            }

            profile_form.save()

            if new_email != old_email and social_emails and new_email.lower() not in social_emails:
                messages.warning(
                    request,
                    'Nový e-mail neodpovídá žádnému z propojených účtů (Google/Facebook/...). '
                    'Zkontrolujte jej prosím, že je opravdu správný!'
                )

            messages.success(request, 'Vaše údaje byly úspěšně uloženy.')
            return redirect('home')
    else:
        profile_form = forms.ProfileForm(
            user, instance=profile, allow_membership_change=False, allow_email_change=True
        )

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
    ).select_related('user', 'student_by_name', 'student_by_name__school_class').order_by('id')

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
    ).select_related('profile__user', 'student_by_name', 'student_by_name__school_class').order_by('id')

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
def orphaned_students(request: HttpRequest):
    user = cast(User, request.user)
    students = Student.objects.filter(parents__isnull=True).select_related('school_class').order_by(
        'last_name', 'first_name'
    )

    if not can_view_all_classes(user):
        profile = getattr(user, 'profile', None)
        today = timezone.localdate()
        currently_valid = Q(valid_until__isnull=True) | Q(valid_until__gte=today)
        represented_class_ids = ClassRepresentative.objects.filter(
            currently_valid, representative=profile,
            representant_type=ClassRepresentative.RepresentantType.VR,
        ).values_list('school_class_id', flat=True)
        students = students.filter(school_class_id__in=represented_class_ids)

    return render(request, 'main/orphaned_students.html', {
        'students': students,
    })


@view_others_required
def orphaned_members(request: HttpRequest):
    profiles = Profile.objects.filter(
        status=Profile.ProfileStatus.ACTIVE, children__isnull=True
    ).select_related('user').order_by('user__last_name', 'user__first_name')

    return render(request, 'main/orphaned_members.html', {
        'profiles': profiles,
    })


@view_others_required
def orphaned_classes(request: HttpRequest):
    today = timezone.localdate()
    currently_valid = Q(valid_until__isnull=True) | Q(valid_until__gte=today)

    classes_with_vr = set(ClassRepresentative.objects.filter(
        currently_valid, representant_type=ClassRepresentative.RepresentantType.VR
    ).values_list('school_class_id', flat=True))
    classes_with_treasurer = set(ClassRepresentative.objects.filter(
        currently_valid, representant_type=ClassRepresentative.RepresentantType.TREASURER
    ).values_list('school_class_id', flat=True))

    incomplete_classes = (
        ClassCollective.objects.exclude(pk__in=classes_with_vr)
        | ClassCollective.objects.exclude(pk__in=classes_with_treasurer)
    ).distinct().order_by('-year', 'school_class', 'variant')

    classes = [
        {
            'class_collective': class_collective,
            'missing_vr': class_collective.pk not in classes_with_vr,
            'missing_treasurer': class_collective.pk not in classes_with_treasurer,
        }
        for class_collective in incomplete_classes
    ]

    return render(request, 'main/orphaned_classes.html', {
        'classes': classes,
    })


@login_required
def show_vr(request: HttpRequest):
    today = timezone.localdate()
    currently_valid = Q(valid_until__isnull=True) | Q(valid_until__gte=today)

    vr_profiles = Profile.objects.filter(
        user__groups__name=VR_MEMBER_GROUP_NAME
    ).select_related('user').distinct().order_by('user__last_name', 'user__first_name')

    members = []
    other_profiles = []
    for profile in vr_profiles:
        if cast(User, profile.user).groups.filter(name=CAPO_DI_TUTTI_GROUP_NAME).exists():
            members.append({'profile': profile, 'role': "Předseda spolku"})
        else:
            other_profiles.append(profile)

    for profile in other_profiles:
        represented_classes = ClassRepresentative.objects.filter(
            currently_valid, representative=profile,
            representant_type=ClassRepresentative.RepresentantType.VR,
        ).select_related('school_class')
        class_names = ", ".join(str(rep.school_class) for rep in represented_classes)
        role = f"Zástupce třídy {class_names}" if class_names else "Zástupce třídy"
        members.append({'profile': profile, 'role': role})

    return render(request, 'main/show_vr.html', {
        'members': members,
    })


@login_required
def show_members(request: HttpRequest, pk: int):
    class_collective = get_object_or_404(ClassCollective, pk=pk)
    user = cast(User, request.user)
    profile = getattr(user, 'profile', None)

    if not is_member(profile):
        raise PermissionDenied("Nemáte oprávnění zobrazit kontakty na členy třídy.")

    assert profile is not None
    class_students = cast('Manager[Student]', class_collective.students)
    if not can_view_all_classes(user) and not class_students.filter(parents=profile).exists():
        raise PermissionDenied("Nemáte oprávnění zobrazit kontakty na členy této třídy.")

    today = timezone.localdate()
    currently_valid = Q(valid_until__isnull=True) | Q(valid_until__gte=today)
    representatives = ClassRepresentative.objects.filter(
        currently_valid, school_class=class_collective,
    ).select_related('representative__user').order_by('representant_type')

    members = Profile.objects.filter(
        status=Profile.ProfileStatus.ACTIVE, children__school_class=class_collective
    ).select_related('user').distinct().order_by('user__last_name', 'user__first_name')

    members_data = [
        {
            'profile': member,
            'children': cast('Manager[Student]', member.children).filter(school_class=class_collective),
        }
        for member in members
    ]

    return render(request, 'main/show_members.html', {
        'class_collective': class_collective,
        'representatives': representatives,
        'members': members_data,
    })


@login_required
def show_circle(request: HttpRequest, pk: int):
    circle = get_object_or_404(Circle, pk=pk)
    user = cast(User, request.user)
    profile = getattr(user, 'profile', None)

    if not is_member(profile):
        raise PermissionDenied("Nemáte oprávnění zobrazit kontakty na členy kruhu.")

    today = timezone.localdate()
    currently_valid = Q(valid_until__isnull=True) | Q(valid_until__gte=today)

    memberships = CircleMembership.objects.filter(
        currently_valid, circle=circle, profile__status=Profile.ProfileStatus.ACTIVE,
    ).select_related('profile__user').order_by(
        '-speaker_of_circle', 'profile__user__last_name', 'profile__user__first_name'
    )

    pages = cast('PageQuerySet', circle.pages).live().specific()
    visible_pages = [
        page for page in pages
        if all(restriction.accept_request(request) for restriction in page.get_view_restrictions())
    ]

    return render(request, 'main/show_circle.html', {
        'circle': circle,
        'memberships': memberships,
        'pages': visible_pages,
    })
