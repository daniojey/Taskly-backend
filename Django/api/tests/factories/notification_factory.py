from django.utils import timezone
import factory
from factory.declarations import SubFactory
from factory.django import DjangoModelFactory
import factory.fuzzy

from api.tests.factories.user_factory import UserFactory
from users.models import Notification

class NotificationFactory(DjangoModelFactory):
    class Meta:
        model = Notification

    notify_type = factory.fuzzy.FuzzyChoice(Notification.TYPE_MESSAGES, getter=lambda c: c[0])
    user = SubFactory(UserFactory)
    message = factory.faker.Faker("text", max_nb_chars=1000)
    data = factory.Dict({})
    created_at = factory.LazyFunction(timezone.now)
    updated_at = factory.LazyFunction(timezone.now)
    is_read = factory.faker.Faker('py_bool') # TODO it`s not working right now