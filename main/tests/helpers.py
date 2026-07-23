import datetime
from unittest.mock import patch

from django.contrib.auth import get_user_model

from main.models import ClassCollective, Profile, Student

User = get_user_model()


def create_user(username, email='', first_name='Test', last_name='User', **kwargs):
    return User.objects.create_user(
        username=username, email=email or f'{username}@example.com',
        first_name=first_name, last_name=last_name, password='x', **kwargs
    )


def create_profile(user, status=Profile.ProfileStatus.ACTIVE, **kwargs):
    defaults = dict(
        birth_date=datetime.date(1980, 1, 1),
        street_and_number='Ulice 1',
        city='Praha',
        zip_code='11000',
        membership=Profile.MembershipType.ACTIVE,
        status=status,
    )
    defaults.update(kwargs)
    with patch('main.models.validuj_adresu'):
        return Profile.objects.create(user=user, **defaults)


def create_class_collective(**kwargs):
    defaults = dict(year=2023, school_class=3)
    defaults.update(kwargs)
    return ClassCollective.objects.create(**defaults)


def create_student(school_class=None, **kwargs):
    defaults = dict(
        first_name='Anicka', last_name='Novakova', birth_date=datetime.date(2016, 1, 1),
        school_class=school_class or create_class_collective(),
    )
    defaults.update(kwargs)
    return Student.objects.create(**defaults)
