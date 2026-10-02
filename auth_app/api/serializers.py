from rest_framework import serializers
from django.contrib.auth.models import User

# class UserProfileSerializer(serializers.ModelSerializer):
#     class Meta:
#         model = User
#         fields = ['id', 'username', 'email']


class RegistrationSerializer(serializers.ModelSerializer):
    
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
        pw = self.validated_data['password']
        repeated_pw = self.validated_data['repeated_password']
        email = self.validated_data['email']
        fullname = self.validated_data['fullname']


        if pw != repeated_pw:
            raise serializers.ValidationError(
                {'error':'passwords dont match'})
        
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError('Email already exists')

        account = User(email=self.validated_data['email'], username=fullname)
        account.set_password(pw)
        account.save()
        return account