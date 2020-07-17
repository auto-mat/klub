import datetime

from aklub.models import CompanyContact, CompanyProfile, DonorPaymentChannel, Event, MoneyAccount, ProfileEmail, Telephone, UserProfile

from drf_yasg.utils import swagger_auto_schema

from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope

from rest_framework import generics, status
from rest_framework.response import Response

from .exceptions import DonorPaymentChannelDoesntExist, PaymentsDoesntExist
from .serializers import (
    DonorPaymetChannelSerializer, EventCheckSerializer, GetDpchCompanyProfileSerializer, GetDpchUserProfileSerializer,
    InteractionSerizer, MoneyAccountCheckSerializer, PaymentSerializer, VSReturnSerializer,
)
from .utils import get_or_create_dpch


class CheckMoneyAccountView(generics.RetrieveAPIView):
    """ Check if MoneyAccount  Bank/Api with this slug exists"""
    permission_classes = [TokenHasReadWriteScope]
    required_scopes = ['can_check_if_exist']
    queryset = MoneyAccount.objects.all()
    lookup_field = 'slug'
    serializer_class = MoneyAccountCheckSerializer


class CheckEventView(generics.RetrieveAPIView):
    """ Check if Event with this slug exists"""
    permission_classes = [TokenHasReadWriteScope]
    required_scopes = ['can_check_if_exist']
    queryset = Event.objects.all()
    lookup_field = 'slug'
    serializer_class = EventCheckSerializer


class CreateDpchUserProfileView(generics.GenericAPIView):
    """ Creates or GET DonorPaymentChannel and return VS"""
    permission_classes = [TokenHasReadWriteScope]
    required_scopes = ['can_create_profiles']
    serializer_class = GetDpchUserProfileSerializer

    @swagger_auto_schema(responses={200: VSReturnSerializer()})
    def post(self, request):
        serializer = self.serializer_class(data=self.request.data)
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
            if user.sex == 'unknown':
                user.sex = serializer.validated_data.get('sex', 'unknown')
            user.save()

            if created:
                ProfileEmail.objects.create(email=serializer.validated_data['email'], user=user)

            Telephone.objects.get_or_create(telephone=serializer.validated_data['telephone'], user=user)

            dpch = get_or_create_dpch(serializer, user)
            return Response(VSReturnSerializer(dpch).data, status=status.HTTP_200_OK)


class CreateDpchCompanyProfileView(generics.GenericAPIView):
    """ Creates or GET DonorPaymentChannel and return VS"""
    permission_classes = [TokenHasReadWriteScope]
    required_scopes = ['can_create_profiles']
    serializer_class = GetDpchCompanyProfileSerializer

    @swagger_auto_schema(responses={200: VSReturnSerializer()})
    def post(self, request):
        serializer = self.serializer_class(data=self.request.data)
        if serializer.is_valid(raise_exception=True):
            # check profile data
            if serializer.validated_data.get('crn'):
                company, created = CompanyProfile.objects.get_or_create(
                    crn=serializer.validated_data.get('crn'),
                )
            else:
                company = CompanyProfile.objects.create()
            unit = serializer.validated_data['money_account'].administrative_unit
            company.administrative_units.add(unit)
            if not company.name:
                company.name = serializer.validated_data.get('name')
            if not company.street and not company.city and not company.zip_code:
                company.street = serializer.validated_data.get('street', '')
                company.city = serializer.validated_data.get('city', '')
                company.zip_code = serializer.validated_data.get('zip_code', '')
            company.save()

            contact, created = CompanyContact.objects.get_or_create(
                company=company,
                email=serializer.validated_data.get('email'),
                telephone=serializer.validated_data.get('telephone'),
                administrative_unit=unit,
                contact_first_name=serializer.validated_data.get('contact_first_name', ''),
                contact_last_name=serializer.validated_data.get('contact_last_name', ''),
            )
            dpch = get_or_create_dpch(serializer, company)
            return Response(VSReturnSerializer(dpch).data, status=status.HTTP_200_OK)


class CheckPaymentView(generics.GenericAPIView):
    """ Check last assigned payment"""
    permission_classes = [TokenHasReadWriteScope]
    required_scopes = ['can_check_last_payments']
    serializer_class = DonorPaymetChannelSerializer

    @swagger_auto_schema(responses={200: PaymentSerializer(many=True)})
    def post(self, request):
        serializer = self.serializer_class(data=self.request.data)
        if serializer.is_valid(raise_exception=True):
            try:
                dpch = DonorPaymentChannel.objects.get(
                    money_account=serializer.validated_data['money_account'],
                    event=serializer.validated_data['event'],
                    VS=serializer.validated_data['VS'],
                )
            except DonorPaymentChannel.DoesNotExist:
                raise DonorPaymentChannelDoesntExist()

            # there we filter payments which arrived between date of register in form + 14 days
            payments = dpch.payment_set\
                .order_by('date')\
                .filter(
                    amount=serializer.validated_data['amount'],
                    date__gte=serializer.validated_data['date'],
                    date__lte=serializer.validated_data['date'] + datetime.timedelta(days=14),
                )
            if payments:
                return Response(PaymentSerializer(payments, many=True).data)
            else:
                raise PaymentsDoesntExist()


class CreateInteraction(generics.GenericAPIView):
    """
        Create Interaction based on choice
    """
    permission_classes = [TokenHasReadWriteScope]
    required_scopes = ['can_create_interactions']
    serializer_class = InteractionSerizer

    @swagger_auto_schema(responses={200: 'returns empty json'})
    def post(self, request):
        serializer = self.serializer_class(data=self.request.data)
        if serializer.is_valid(raise_exception=True):
            from interactions.models import Interaction, InteractionType, InteractionCategory
            category, created = InteractionCategory.objects.get_or_create(category='emails')
            int_type, created = InteractionType.objects.get_or_create(
                slug=serializer.validated_data['interaction_type'],
                category=category,
                defaults={'name': serializer.validated_data['interaction_type'], 'summary_bool': True},
            )

            Interaction.objects.create(
                user_id=serializer.validated_data['profile_id'],
                type=int_type,
                date_from=serializer.validated_data['date'],
                event=serializer.validated_data['event'],
                administrative_unit=serializer.validated_data['event'].administrative_units.first(),
                subject=f"vizus-{serializer.validated_data['interaction_type']}",
                summary=serializer.validated_data['text'],
            )
            return Response({}, status=status.HTTP_200_OK)
