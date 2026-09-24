from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import FileShare

User = get_user_model()


class FileShareSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = FileShare
        fields = ['id', 'username', 'permission', 'created_at']


class CreateFileShareSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    permission = serializers.ChoiceField(choices=FileShare.Permission.choices)

    def validate_username(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError('No user has that username.')
