from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Connection

User = get_user_model()


class ConnectionSerializer(serializers.ModelSerializer):
    username = serializers.SerializerMethodField()
    direction = serializers.SerializerMethodField()

    class Meta:
        model = Connection
        fields = ['id', 'username', 'status', 'direction', 'created_at']

    def get_username(self, connection):
        user = connection.recipient if connection.sender_id == self.context['request'].user.id else connection.sender
        return user.username

    def get_direction(self, connection):
        return 'sent' if connection.sender_id == self.context['request'].user.id else 'received'


class CreateConnectionSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)

    def validate_username(self, username):
        try:
            return User.objects.get(username=username)
        except User.DoesNotExist:
            raise serializers.ValidationError('No user has that username.')
