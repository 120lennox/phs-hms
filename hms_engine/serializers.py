from dj_rest_auth.registration.serializers import RegisterSerializer
from rest_framework import serializers


class HospitalAdminRegisterSerializer(RegisterSerializer):
    """
    Extends dj-rest-auth's RegisterSerializer to also accept first_name /
    last_name and mark the new user as staff (hospital admin role).
    """
    first_name = serializers.CharField(required=True, max_length=150)
    last_name = serializers.CharField(required=True, max_length=150)

    def get_cleaned_data(self):
        data = super().get_cleaned_data()
        data['first_name'] = self.validated_data.get('first_name', '')
        data['last_name'] = self.validated_data.get('last_name', '')
        return data

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data.get('first_name', '')
        user.last_name = self.cleaned_data.get('last_name', '')
        user.is_staff = True   # grants hospital-admin privileges
        user.save()
        return user
