# ACTIVE API SERIALIZERS: Required for the new React frontend and Mobile application.
from rest_framework import serializers
from account.models import User, UserType, UsersSettings

class UserTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserType
        fields = ['id', 'user_type']

class UsersSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsersSettings
        fields = ['id', 'prefered_view', 'using_hand', 'reminder_time', 'reminder_enabled']

class UserSerializer(serializers.ModelSerializer):
    user_type = UserTypeSerializer(read_only=True)
    settings = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'last_name', 'phone', 'user_type', 'settings']

    def get_settings(self, obj):
        try:
            settings_obj = UsersSettings.objects.get(user=obj)
            return UsersSettingsSerializer(settings_obj).data
        except UsersSettings.DoesNotExist:
            return None

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'phone', 'password']

    def create(self, validated_data):
        regular_user_type, _ = UserType.objects.get_or_create(user_type='regular_user')

        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone', ''),
            user_type=regular_user_type
        )
        
        # Create default settings for the registered user
        UsersSettings.objects.create(
            user=user,
            prefered_view='mobile',
            using_hand='right'
        )
        return user
