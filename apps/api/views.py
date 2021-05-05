import datetime

from aklub.models import (
    AdministrativeUnit, CompanyContact, CompanyProfile, DonorPaymentChannel, MoneyAccount, ProfileEmail, Telephone, UserProfile,
)

from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import EmailMultiAlternatives
from django.db.models import Prefetch
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _

from django_filters import rest_framework as filters

from drf_yasg.utils import swagger_auto_schema

from events.models import Event, OrganizationTeam

from interactions.models import Interaction, InteractionCategory, InteractionType

from oauth2_provider.contrib.rest_framework import TokenHasReadWriteScope

from rest_framework import filters as rf_filters, generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .exceptions import DonorPaymentChannelDoesntExist, EmailDoesntExist, PaymentsDoesntExist
from .filters import EventCustomFilter
from .serializers import (
    AdministrativeUnitSerializer,
    CreateUserProfileInteractionSerializer, CreateUserProfileSerializer, CreditCardPaymentSerializer,
    DonorPaymetChannelSerializer, EventCheckSerializer, EventSerializer, GetDpchCompanyProfileSerializer, GetDpchUserProfileSerializer,
    InteractionSerizer, MoneyAccountCheckSerializer, PaymentSerializer, ProfileSerializer, ResetPasswordbyEmailConfirmSerializer,
    ResetPasswordbyEmailSerializer, VSReturnSerializer,
)
from .utils import check_last_month_year_payment, get_or_create_dpch


class CheckMoneyAccountView(generics.RetrieveAPIView):
    """
     Check if MoneyAccount  Bank/Api with this slug exists
     -- is used to communicate with 3rd aplication
    """
    permission_classes = [TokenHasReadWriteScope]
    required_scopes = ['can_check_if_exist']
    queryset = MoneyAccount.objects.all()
    lookup_field = 'slug'
    serializer_class = MoneyAccountCheckSerializer


class CheckEventView(generics.RetrieveAPIView):
    """
    Check if Event with this slug exists
    -- is used to communicate with 3rd aplication
    """

    permission_classes = [TokenHasReadWriteScope]
    required_scopes = ['can_check_if_exist']
    queryset = Event.objects.all()
    lookup_field = 'slug'
    serializer_class = EventCheckSerializer


class CreateDpchUserProfileView(generics.GenericAPIView):
    """
    Creates or GET DonorPaymentChannel and return VS
    -- is used to communicate with 3rd aplication
    """
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
    """
    Creates or GET DonorPaymentChannel and return VS
    -- is used to communicate with 3rd aplication
    """
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
    """
    Check last assigned payment
    -- is used to communicate with 3rd aplication
    """
    permission_classes = [TokenHasReadWriteScope]
    required_scopes = ['can_check_last_payments']
    serializer_class = DonorPaymetChannelSerializer

    @swagger_auto_schema(responses={200: PaymentSerializer(many=True)})
    def post(self, request):
        serializer = self.serializer_class(data=self.request.data)
        if serializer.is_valid(raise_exception=True):
            try:
                dpch = DonorPaymentChannel.objects.get(
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
                    type='bank-transfer',
                    date__gte=serializer.validated_data['date'],
                    date__lte=serializer.validated_data['date'] + datetime.timedelta(days=14),
                )
            if payments:
                return Response(PaymentSerializer(payments, many=True).data)
            else:
                raise PaymentsDoesntExist()


class CreateInteractionView(generics.GenericAPIView):
    """
    Create Interaction based on choice
    -- is used to communicate with 3rd aplication
    """
    permission_classes = [TokenHasReadWriteScope]
    required_scopes = ['can_create_interactions']
    serializer_class = InteractionSerizer

    @swagger_auto_schema(responses={200: 'returns empty json'})
    def post(self, request):
        serializer = self.serializer_class(data=self.request.data)
        if serializer.is_valid(raise_exception=True):
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


class CreateCreditCardPaymentView(generics.CreateAPIView):
    """
    creates credit card payment in crm
    -- is used to communicate with 3rd aplication
    """
    permission_classes = [TokenHasReadWriteScope]
    required_scopes = ['can_create_credit_card_payment']
    serializer_class = CreditCardPaymentSerializer

    @swagger_auto_schema(responses={200: ProfileSerializer()})
    def post(self, request):
        serializer = self.serializer_class(data=self.request.data)
        if serializer.is_valid(raise_exception=True):
            if serializer.validated_data.pop('profile_type') == 'user':
                email = ProfileEmail.objects.filter(email=serializer.validated_data.pop('email'))
                profile = 'user'
            else:
                email = CompanyContact.objects.filter(email=serializer.validated_data.pop('email'))
                profile = 'company'
            if email.exists():
                email = email.first()
                user_channels = getattr(email, profile).userchannels.filter(
                    event=serializer.validated_data.pop('event'),
                )
                if user_channels.exists():
                    user_channel = user_channels.first()
                    payment = serializer.create(serializer.validated_data)
                    payment.user_donor_payment_channel = user_channel
                    payment.save()
                    return Response(ProfileSerializer(user_channel.user).data, status=status.HTTP_200_OK)
                else:
                    raise DonorPaymentChannelDoesntExist()
            else:
                raise EmailDoesntExist()


class CreateUserProfileView(generics.CreateAPIView):
    """
    Create new userprofile with PW to has acces to paid section
    """
    serializer_class = CreateUserProfileSerializer


class CheckLastPaymentView(generics.GenericAPIView):
    """
    check if payment exist in CRM or on darujme
    """
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = self.request.user
        has_payment = check_last_month_year_payment(user)
        if has_payment:
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_404_NOT_FOUND)


class ResetPasswordbyEmailView(generics.GenericAPIView):
    serializer_class = ResetPasswordbyEmailSerializer

    def post(self, request):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        emails = ProfileEmail.objects.filter(email=serializer.validated_data['email'])
        if emails.exists():
            email = emails.first()
            user = email.user
            if not user.password:
                # password muset be set or token is not generated
                user.set_password(UserProfile.objects.make_random_password())
                user.save()
                user.refresh_from_db()
            administrative_unit = AdministrativeUnit.objects.filter(from_email_str__isnull=False).first()
            user_uid = urlsafe_base64_encode(force_bytes(user.pk))
            token = default_token_generator.make_token(user)
            template = _("""
                Hello,\n

                We received a request to reset the password for your account for this email address.
                To initiate the password reset process for your account, click the link below.\n\n
                You login Username is : %(username)s\n
                %(url)s\n
                This link can only be used once.\n

                If you did not make this request, you can simply ignore this email.\n

                Sincerely,\n
                The %(site_name)s Team\n
            """) % {
                "url": settings.WEB_URL + '?u=' + user_uid + "&t=" + token,
                "username": user.username,
                "site_name": settings.SITE_NAME,
                }
            email = EmailMultiAlternatives(
                subject=_("Password reset"),
                body=template,
                from_email=administrative_unit.from_email_str,
                to=[email.email],
            )
            email.send(fail_silently=False)

        return Response(status=status.HTTP_200_OK)


class ResetPasswordbyEmailConfirmView(generics.GenericAPIView):
    serializer_class = ResetPasswordbyEmailConfirmSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = UserProfile.objects.get(id=urlsafe_base64_decode(kwargs['uid']).decode())
        except (UserProfile.DoesNotExist, UserProfile.MultipleObjectsReturned):
            return Response(status=status.HTTP_403_FORBIDDEN)
        valid_token = default_token_generator.check_token(user, kwargs['token'])
        if valid_token:
            user.set_password(serializer.validated_data['password_1'])
            user.save()
            return Response(status=status.HTTP_200_OK)
        else:
            return Response(status=status.HTTP_403_FORBIDDEN)


class UserProfileInteractionView(generics.CreateAPIView):
    serializer_class = CreateUserProfileInteractionSerializer
    permission_classes = [TokenHasReadWriteScope]
    required_scopes = ['can_create_userprofile_interaction']

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        user, created = UserProfile.objects.get_or_create(
            profileemail__email=serializer.validated_data.get('email'),
            defaults={
                "first_name": serializer.validated_data.get('first_name'),
                "last_name": serializer.validated_data.get('last_name'),
                "age_group": serializer.validated_data.get('age_group'),
                "birth_month": serializer.validated_data.get('birth_month'),
                "birth_day": serializer.validated_data.get('birth_day'),
            },
        )
        event = serializer.validated_data.get('event')
        user.administrative_units.add(event.administrative_units.first()),
        telephone = serializer.validated_data.get("telephone")
        if telephone:
            Telephone.objects.get_or_create(telephone=telephone, user=user, defaults={"is_primary": True})
        email = serializer.validated_data.get("email")
        if email:
            ProfileEmail.objects.get_or_create(email=email, user=user, defaults={"is_primary": True})

        category, created = InteractionCategory.objects.get_or_create(category=_('Event registration'))
        int_type, created = InteractionType.objects.get_or_create(
            slug='event-registration',
            category=category,
            defaults={
                'name': _('Event registration'),
                'created_bool': True,
                'event_bool': True,
                'note_bool': True,
                'summary_bool': True,
            },
        )
        # prepare not from fields:
        add_answer_1 = f"{event.additional_question_1}:\n    {serializer.validated_data.get('additional_question_1', '-')}\n" \
            if event.additional_question_1 else "-"
        add_answer_2 = f"{event.additional_question_2}:\n    {serializer.validated_data.get('additional_question_2', '-')}\n" \
            if event.additional_question_2 else "-"
        add_answer_3 = f"{event.additional_question_3}:\n    {serializer.validated_data.get('additional_question_3', '-')}\n" \
            if event.additional_question_3 else "-"
        summary = f"{serializer.validated_data['note']}\n{add_answer_1}{add_answer_2}{add_answer_3}"

        Interaction.objects.create(
            user=user,
            type=int_type,
            summary=_("note:") + "\n    " + summary,
            event=event,
            administrative_unit=event.administrative_units.first(),
            date_from=timezone.now(),
            subject=_("Registration to event"),
        )
        return Response(self.serializer_class(serializer.validated_data).data, status=status.HTTP_200_OK)


class EventViewMixin:
    serializer_class = EventSerializer
    permission_classes = [TokenHasReadWriteScope]
    required_scopes = ['can_view_events']

    def get_queryset(self):
        return Event.objects.filter(public_on_web=True).prefetch_related(
            "organization_team",
            Prefetch(
                'organization_team',
                queryset=OrganizationTeam.objects.filter(can_be_contacted=True)
                    .prefetch_related(
                        "profile",
                        # "profile__userprofile__profileemail_set", # polymorphic fix
                        # "profile__userprofile__telephone_set", # polymorphic fix
                ),
                to_attr='filtered_organization_team',
            ),
        ).select_related('location')


class EventListView(EventViewMixin, generics.ListAPIView):
    """
    Reguired info for web
    -- is used to communicate with 3rd aplication
    """

    filter_backends = [filters.DjangoFilterBackend, rf_filters.OrderingFilter]
    filter_class = EventCustomFilter

    def get_queryset(self):
        return Event.objects.filter(public_on_web=True).prefetch_related(
            "organization_team",
            Prefetch(
                'organization_team',
                queryset=OrganizationTeam.objects.filter(can_be_contacted=True)
                    .prefetch_related(
                        "profile",
                        # "profile__userprofile__profileemail_set", # polymorphic fix
                        # "profile__userprofile__telephone_set", # polymorphic fix
                ),
                to_attr='filtered_organization_team',
            ),
        ).select_related('location')


class EventRetrieveView(EventViewMixin, generics.RetrieveAPIView):
    lookup_field = 'slug'


class AdministrativeUnitView(generics.ListAPIView):
    """
    Reguired info for web
    -- is used to communicate with 3rd aplication
    """
    serializer_class = AdministrativeUnitSerializer
    permission_classes = [TokenHasReadWriteScope]
    required_scopes = ['can_view_administrative_units']

    def get_queryset(self):
        return AdministrativeUnit.objects.all().select_related(
            'president',
            'manager',
        )
