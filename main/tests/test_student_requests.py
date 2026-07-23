import datetime

from django.test import TestCase
from django.urls import reverse

from main.models import ParentRelationship, Profile, ProfileStudentRequest, Student

from .helpers import create_profile, create_student, create_user


class AddStudentViewTests(TestCase):
    def test_requires_login(self):
        resp = self.client.get(reverse('add_student'))
        self.assertEqual(resp.status_code, 302)

    def test_non_active_member_is_redirected(self):
        user = create_user('pending1')
        create_profile(user, status=Profile.ProfileStatus.PENDING)
        self.client.force_login(user)

        resp = self.client.get(reverse('add_student'))
        self.assertRedirects(resp, reverse('index'))

    def test_active_member_can_submit_request(self):
        user = create_user('parent1')
        profile = create_profile(user, status=Profile.ProfileStatus.ACTIVE)
        self.client.force_login(user)

        resp = self.client.post(reverse('add_student'), {
            'first_name': 'Anicka', 'last_name': 'Novakova', 'birth_date': '2016-01-01', 'comments': '',
        }, follow=True)

        self.assertEqual(resp.status_code, 200)
        request = ProfileStudentRequest.objects.get(profile=profile)
        self.assertEqual(request.first_name, 'Anicka')
        self.assertEqual(request.status, ProfileStudentRequest.RequestStatus.PENDING)

    def test_matches_existing_student_on_submit(self):
        user = create_user('parent1')
        create_profile(user, status=Profile.ProfileStatus.ACTIVE)
        student = create_student(first_name='Tomas', last_name='Novak', birth_date=datetime.date(2015, 5, 10))
        self.client.force_login(user)

        self.client.post(reverse('add_student'), {
            'first_name': 'tomas', 'last_name': 'NOVAK', 'birth_date': '2015-05-10', 'comments': '',
        })

        request = ProfileStudentRequest.objects.get()
        self.assertEqual(request.student_by_name, student)


class StudentRequestsListViewTests(TestCase):
    def test_requires_staff(self):
        user = create_user('parent1')
        create_profile(user)
        self.client.force_login(user)

        resp = self.client.get(reverse('student_requests'))
        self.assertNotEqual(resp.status_code, 200)

    def test_lists_only_pending_requests(self):
        user = create_user('parent1')
        profile = create_profile(user)
        pending = ProfileStudentRequest.objects.create(
            profile=profile, first_name='Anicka', last_name='Novakova', birth_date=datetime.date(2016, 1, 1),
        )
        ProfileStudentRequest.objects.create(
            profile=profile, first_name='Jiny', last_name='Zak', birth_date=datetime.date(2016, 1, 1),
            status=ProfileStudentRequest.RequestStatus.APPROVED,
        )

        staff = create_user('staff1', is_staff=True)
        self.client.force_login(staff)

        resp = self.client.get(reverse('student_requests'))
        content = resp.content.decode()
        self.assertIn(pending.first_name, content)
        self.assertNotIn('Jiny', content)


class StudentRequestDetailViewTests(TestCase):
    def setUp(self):
        self.staff = create_user('staff1', is_staff=True)
        self.parent_user = create_user('parent1', first_name='Petr', last_name='Novak')
        self.profile = create_profile(self.parent_user, status=Profile.ProfileStatus.ACTIVE)
        self.request_obj = ProfileStudentRequest.objects.create(
            profile=self.profile, first_name='Anicka', last_name='Novakova', birth_date=datetime.date(2016, 1, 1),
        )

    def test_requires_staff(self):
        self.client.force_login(self.parent_user)
        resp = self.client.get(reverse('student_request_detail', args=[self.request_obj.pk]))
        self.assertNotEqual(resp.status_code, 200)

    def test_approve_with_existing_student_creates_relationship_without_duplicating(self):
        student = create_student(
            first_name='Anicka', last_name='Novakova', birth_date=datetime.date(2016, 1, 1),
        )
        self.client.force_login(self.staff)

        resp = self.client.post(
            reverse('student_request_detail', args=[self.request_obj.pk]),
            {'student': student.pk},
            follow=True,
        )

        self.assertEqual(resp.status_code, 200)
        self.request_obj.refresh_from_db()
        self.assertEqual(self.request_obj.status, ProfileStudentRequest.RequestStatus.APPROVED)
        self.assertEqual(self.request_obj.student_by_name, student)
        self.assertTrue(
            ParentRelationship.objects.filter(parent=self.profile, student=student).exists()
        )
        self.assertEqual(Student.objects.filter(first_name='Anicka', last_name='Novakova').count(), 1)

    def test_approve_without_selecting_student_fails_validation(self):
        self.client.force_login(self.staff)

        resp = self.client.post(
            reverse('student_request_detail', args=[self.request_obj.pk]), {}, follow=True
        )

        self.assertEqual(resp.status_code, 200)
        self.request_obj.refresh_from_db()
        self.assertEqual(self.request_obj.status, ProfileStudentRequest.RequestStatus.PENDING)
        self.assertEqual(Student.objects.count(), 0)

    def test_reject_marks_rejected_without_creating_relationship(self):
        self.client.force_login(self.staff)

        resp = self.client.post(
            reverse('student_request_detail', args=[self.request_obj.pk]), {'reject': '1'}, follow=True
        )

        self.assertEqual(resp.status_code, 200)
        self.request_obj.refresh_from_db()
        self.assertEqual(self.request_obj.status, ProfileStudentRequest.RequestStatus.REJECTED)
        self.assertFalse(ParentRelationship.objects.filter(parent=self.profile).exists())

    def test_already_processed_request_404s(self):
        self.request_obj.status = ProfileStudentRequest.RequestStatus.APPROVED
        self.request_obj.save()
        self.client.force_login(self.staff)

        resp = self.client.get(reverse('student_request_detail', args=[self.request_obj.pk]))
        self.assertEqual(resp.status_code, 404)
