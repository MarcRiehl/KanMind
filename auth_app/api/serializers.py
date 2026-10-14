from rest_framework import serializers
from django.contrib.auth.models import User

class RegistrationSerializer(serializers.ModelSerializer):
    """Serializer for registering new users."""

    fullname = serializers.CharField()
    repeated_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['fullname', 'email', 'password', 'repeated_password']
        extra_kwargs = {
            'password': {
                'write_only': True
            }
        }

    def save(self):
        """
        Create a new user after validating the registration data.

        Returns:
            User: The newly created user instance.

        Raises:
            serializers.ValidationError: If the passwords do not match
                or the email address is already registered.
        """
        pw = self.validated_data['password']
        repeated_pw = self.validated_data['repeated_password']
        email = self.validated_data['email']
        fullname = self.validated_data['fullname']

        if pw != repeated_pw:
            raise serializers.ValidationError(
                {'error': 'passwords dont match'})

        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('Email already exists')

        account = User(email=self.validated_data['email'], username=fullname)
        account.set_password(pw)
        account.save()
        return account