"""
Serializers for the user API View.
"""

from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext as _
from rest_framework import serializers


class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user object."""

    class Meta:
        model = get_user_model()
        fields = ["email", "password", "name"]
        extra_kwargs = {"password": {"write_only": True, "min_length": 5}}

    def create(self, validated_data):
        """Create and return a user with encrypted password."""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        """Update and return a user with updated and validated data."""
        password = validated_data.pop("password", None)
        # we retrieve the password from validated data, and remove
        # it afterwards.
        # making it optional, since we accept later none value on the update
        user = super().update(instance, validated_data)
        if password:
            # If user specified a password to update password.
            user.set_password(password)
            user.save()
        return user


class AuthTokenSerializer(serializers.Serializer):
    """Serializer for the user auth token."""

    email = serializers.EmailField()
    password = serializers.CharField(
        style={"input_type": "password"},
        trim_whitespace=False,
    )

    # validator method called during the validation stage
    def validate(self, attrs):
        """Validate and authenticate the user."""
        email = attrs.get("email")
        password = attrs.get("password")
        print(attrs)
        user = authenticate(
            request=self.context.get("request"),
            username=email,
            password=password,
        )
        if not user:
            msg = _("Unable to authenticate with provided user credentials.")
            raise serializers.ValidationError(msg, code="authorization")
        # We set the user attribute so we can use it in the view.
        attrs["user"] = user
        return attrs
