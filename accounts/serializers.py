from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(
        max_length=User._meta.get_field('username').max_length,
        validators=User._meta.get_field('username').validators,
    )
    password = serializers.CharField(write_only=True, trim_whitespace=False)

    def validate(self, attrs):
        username = attrs['username']

        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError(
                {'username': 'An account with this username already exists.'}
            )

        # Use Django's configured password validators with the proposed username.
        validate_password(attrs['password'], user=User(username=username))
        return attrs

    def create(self, validated_data):
        return User.objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=User._meta.get_field('username').max_length)
    password = serializers.CharField(write_only=True, trim_whitespace=False)
