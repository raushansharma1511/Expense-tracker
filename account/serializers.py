from rest_framework import serializers
from django.contrib.auth import authenticate


from .models import User


class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "password", "email", "name", "phone", "is_staff"]
        read_only_fields = ["id"]  # default uuid generated

    def create(self, validated_data):

        user = User.objects.create(**validated_data)
        user.set_password(validated_data["password"])
        user.save()
        return user


class LogInSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        print(data)
        user = authenticate(username=data["username"], password=data["password"])
        if user is None:
            raise serializers.ValidationError("Invalid username or password")
        return user
