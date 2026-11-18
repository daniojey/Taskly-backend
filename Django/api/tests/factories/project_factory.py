from django.utils import timezone
import factory
from factory.django import DjangoModelFactory

from task.models import Project
from api.tests.factories.group_factory import GroupFactory
from api.tests.factories.user_factory import UserFactory


class ProjectFactory(DjangoModelFactory):
    class Meta:
        model = Project

    owner = factory.SubFactory(UserFactory)
    group = factory.SubFactory(GroupFactory)
    title = factory.Sequence(lambda n: f"project{n}")
    desction = factory.LazyAttribute(lambda o: f"{o.title}-description")
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)