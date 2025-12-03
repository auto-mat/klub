from aklub.models import (
    ProfileEmail,
    Telephone,
    UserProfile,
)

from rest_framework import serializers
from rest_framework import filters as rf_filters, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response


class UpdateUserProfileSerializer(serializers.ModelSerializer):
    telephone = serializers.CharField(
        required=False,
        allow_blank=True,
        write_only=True,
    )

    class Meta:
        model = UserProfile
        fields = ["first_name", "last_name", "telephone", "sex", "language"]
        extra_kwargs = {
            "first_name": {"required": False, "allow_blank": True},
            "last_name": {"required": False, "allow_blank": True},
            "sex": {"required": False, "allow_blank": True},
            "language": {"required": False, "allow_blank": True},
        }

    def update(self, instance, validated_data):
        telephone = validated_data.pop("telephone", None)
        instance = super().update(instance, validated_data)

        # Telephone update
        if telephone is not None:
            if telephone:
                Telephone.objects.filter(user=instance).update(is_primary=None)
                tel, created = Telephone.objects.get_or_create(
                    telephone=telephone, user=instance
                )
                if not tel.is_primary:
                    tel.is_primary = True
                    tel.save()
            else:
                Telephone.objects.filter(user=instance, is_primary=True).update(
                    is_primary=None
                )

        return instance

class UserProfileView(generics.GenericAPIView):
    """
    Get and update authenticated user's profile information.
    GET: Retrieve user info (firstname, lastname, email, telephone, sex, language).
    PUT: Update user profile information.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UpdateUserProfileSerializer

    def get(self, request):
        """GET: Retrieve user info"""
        user = request.user
        
        try:
            email = user.profileemail_set.get(is_primary=True).email
        except ProfileEmail.DoesNotExist:
            email_obj = user.profileemail_set.first()
            email = email_obj.email if email_obj else None
        
        try:
            telephone = user.telephone_set.get(is_primary=True).telephone
        except Telephone.DoesNotExist:
            telephone_obj = user.telephone_set.first()
            telephone = telephone_obj.telephone if telephone_obj else None
        
        return Response({
            "firstname": user.first_name,
            "lastname": user.last_name,
            "email": email,
            "telephone": telephone,
            "sex": user.sex,
            "language": user.language,
        }, status=status.HTTP_200_OK)

    def put(self, request):
        """PUT: Update user profile"""
        user = self.request.user
        serializer = self.get_serializer(user, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(status=status.HTTP_200_OK)