from rest_framework import serializers

from aklub.models import (
    Telephone,
    UserProfile,
)


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
