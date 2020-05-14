
import datetime

from aklub.models import CompanyProfile, DonorPaymentChannel, ProfileEmail, Telephone,  UserProfile

from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import GetDpchCompanyProfileSerializer, GetDpchUserProfileSerializer


def get_or_create_dpch(serializer, profile):
    dpch, created = DonorPaymentChannel.objects.get_or_create(
                    event=serializer.validated_data['event'],
                    money_account=serializer.validated_data['money_account'],
                    user=profile,
                    )
    if created:
        dpch.expected_date_of_first_payment = datetime.date.today() + datetime.timedelta(days=3)
        if serializer.validated_data.get('regular'):
            dpch.regular_payments = 'regular'
        else:
            dpch.regular_payments = 'onetime'
        dpch.regular_amount = serializer.validated_data['amount']
        dpch.generate_VS()
        dpch.save()
    return dpch.VS


class CreateDpchUserProfileView(APIView):
    """ accepts email and so... create DPCH or find existed and return VS"""
    permission_classes = [TokenHasReadWriteScope]

    def post(self, request):
        serializer = GetDpchUserProfileSerializer(data=self.request.data)
        if serializer.is_valid(raise_exception=True):
            # check profile data
            user, created = UserProfile.objects.get_or_create(
                                    profileemail__email=serializer.validated_data.get('email'),
            )
            user.administrative_units.add(serializer.validated_data.get('money_account').administrative_unit)
            if not user.first_name:
                user.first_name = serializer.validated_data.get('first_name', '')
            if not user.last_name:
                user.last_name = serializer.validated_data.get('last_name', '')
            if not user.street and not user.city and not user.zip_code:
                user.street = serializer.validated_data.get('street', '')
                user.city = serializer.validated_data.get('city', '')
                user.zip_code = serializer.validated_data.get('zip_code', '')
            if not user.age_group and not user.birth_month and not user.birth_day:
                user.age_group = serializer.validated_data.get('age_group', None)
                user.birth_month = serializer.validated_data.get('birth_month', None)
                user.birth_day = serializer.validated_data.get('birth_day', None)
            if not user.sex:

                user.sex = serializer.validated_data.get('sex', 'unknow')
            user.save()

            if created:
                ProfileEmail.objects.create(email=serializer.validated_data['email'], user=user)

            Telephone.objects.get_or_create(telephone=serializer.validated_data['telephone'], user=user)

            VS = get_or_create_dpch(serializer, user)
            return Response({'VS': VS}, status=status.HTTP_200_OK)


class CreateDpchCompanyProfileView(APIView):
    """ accepts crn and so... create DPCH or find existed and return VS"""
    permission_classes = [TokenHasReadWriteScope]

    def post(self, request):
        serializer = GetDpchCompanyProfileSerializer(data=self.request.data)
        if serializer.is_valid(raise_exception=True):
            # check profile data
            if serializer.validated_data.get('crn'):
                company, created = CompanyProfile.objects.get_or_create(
                                        crn=serializer.validated_data.get('crn'),

                )
            else:
                company = CompanyProfile.objects.create()

            company.administrative_units.add(serializer.validated_data['money_account'].administrative_unit)
            if not company.name:
                company.name = serializer.validated_data.get('name')
            if not company.street and not company.city and not company.zip_code:
                company.street = serializer.validated_data.get('street', '')
                company.city = serializer.validated_data.get('city', '')
                company.zip_code = serializer.validated_data.get('zip_code', '')
            company.save()

            ProfileEmail.objects.get_or_create(email=serializer.validated_data.get('email'), user=company)
            Telephone.objects.get_or_create(telephone=serializer.validated_data.get('telephone'), user=company)

            VS = get_or_create_dpch(serializer, company)
            return Response({'VS': VS}, status=status.HTTP_200_OK)
