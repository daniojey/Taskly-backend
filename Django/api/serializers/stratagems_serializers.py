import copy

from rest_framework import serializers

from task.models import Stratagem

class StratagemCreateSerializer(serializers.ModelSerializer):
    action = serializers.CharField(write_only=True)

    def validate_action(self, data):
        print(data, 'DATA')
        return data

    def validate(self, data):
        new_data = copy.deepcopy(data)
        action = data['action']

        print(action)

        validate_map = {
            'group': Stratagem.OPEN_GROUP,
            'project': Stratagem.OPEN_PROJECT,
            'task': Stratagem.OPEN_TASK,
            'other': Stratagem.OPEN_URL,
        }

        match action:
            case 'group':
                new_data['action'] = validate_map[action]
            case 'other':
                new_data['action'] = validate_map[action]
                print(new_data, 'NEW DATA')
            case _:
                raise serializers.ValidationError('NO found action')
            
        return new_data
    
    def create(self, validated_data):
        combination = validated_data['combination']

        combination_list = [int(n) for n in combination.split(',')]

        validated_data['combination'] = combination_list

        instance = Stratagem.objects.create(**validated_data)

        return instance

    class Meta:
        model = Stratagem
        fields = ['user','name', 'url', 'action', 'combination']


class StratagemShortSerializer(serializers.ModelSerializer):

    class Meta:
        model = Stratagem
        fields = ['id', 'name', 'url', 'action', 'data', 'combination', 'active']

