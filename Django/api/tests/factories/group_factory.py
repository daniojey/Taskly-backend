from django.utils import timezone
import factory
from factory.django import DjangoModelFactory

from api.tests.factories.user_factory import UserFactory
from users.models import Group


class GroupFactory(DjangoModelFactory):
    class Meta:
        model = Group

    class Params:
        group = "general"


    name = factory.LazyAttributeSequence(lambda o, n: f"{o.group}-room-{n}")
    owner = factory.SubFactory(UserFactory)
    created_at = timezone.now()
    updated_at = timezone.now()

    @factory.post_generation
    def members(self, create, extracted, **kwargs):
        if not create:
            return
        
        self.members.add(self.owner)
        if extracted:
            self.members.add(*extracted)