from rest_framework.serializers import ModelSerializer

from rest_framework.serializers import ValidationError
from task.models import SubTask

class CreateSubTaskSerializer(ModelSerializer):

    def create(self, validated_data):
        position = self.context.get("position", None)

        if not position:
            raise ValidationError
        
        new_validated_data = validated_data.copy()
        new_validated_data['position'] = position

        return super().create(new_validated_data)
    
    class Meta:
        model = SubTask
        fields = ['task', 'title', 'description']
