from django.utils import timezone
import factory
from django.contrib.auth import get_user_model
from factory.django import DjangoModelFactory

from users.models import Group


User = get_user_model()

class UserFactory(DjangoModelFactory):
    class Meta:
        model = User
        django_get_or_create = ("username",)
        skip_postgeneration_save = True


    username = factory.Sequence(lambda n: f"user{n}")
    email = factory.LazyAttribute(lambda o: f"{o.username}@example.com")

    password = factory.django.Password("testpass123")

    @factory.post_generation
    def user_groups(self, create, extracted, **kwargs):
        if not create or not extracted:
            return 

        self.user_groups.add(*extracted)
    

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
    
        