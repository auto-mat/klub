# -*- coding: utf-8 -*-
# Author: Petr Dlouhý <petr.dlouhy@email.cz>
#
# Copyright (C) 2013 o.s. Auto*Mat
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

# Create your views here.
import datetime
import json
from collections import OrderedDict

from betterforms.multiform import MultiModelForm

from django import forms, http
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.core.exceptions import PermissionDenied
from django.core.mail import EmailMultiAlternatives
from django.core.validators import MinLengthValidator, RegexValidator, ValidationError
from django.db.models import Case, Count, IntegerField, Q, Sum, When
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, render_to_response
from django.template.loader import render_to_string
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.views.generic.edit import FormView

from events.models import Event

from interactions.models import PetitionSignature

from sesame.backends import ModelBackend

from . import autocom
from .models import (
    AdministrativeUnit, BankAccount, DonorPaymentChannel, MoneyAccount, Payment, Preference,
    Profile, ProfileEmail, Telephone, UserProfile,
)


class RegularUserForm_UserProfile(forms.ModelForm):
    required_css_class = 'required'

    email = forms.EmailField(
        required=True,
        error_messages={'unique': "This e-mail is already used."},
    )
    username = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean_username(self):
        "This function is required to overwrite an inherited username clean"
        return self.cleaned_data['username']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.Meta.required:
            self.fields[field].required = True

    required_css_class = 'required'

    telephone = forms.CharField(
        label=_(u"Telefon"),
        validators=[RegexValidator(r'^[0-9+ ]*$', _('Telephone must consist of numbers, spaces and plus sign')), MinLengthValidator(9)],
        max_length=30,
    )

    class Meta:
        model = UserProfile
        fields = ('first_name', 'last_name',
                  'email', 'username', 'telephone',)
        required = ('first_name', 'last_name',
                    'email', 'telephone',)


class EventMixin(forms.ModelForm):
    Event = forms.ModelChoiceField(
        queryset=Event.objects.filter(slug__isnull=False, enable_registration=True).exclude(slug=""),
        to_field_name="slug",
    )


class BankAccountMixin(forms.ModelForm):
    money_account = forms.ModelChoiceField(
        queryset=MoneyAccount.objects.filter(slug__isnull=False).exclude(slug=""),
        to_field_name="slug",
    )


class RegularUserForm_DonorPaymentChannel(BankAccountMixin, forms.ModelForm):
    required_css_class = 'required'

    regular_payments = forms.CharField(
        label=_("Regular payments"),
        required=False,
        widget=forms.HiddenInput(),
    )
    regular_frequency = forms.ChoiceField(
        label=_("Regular payments"),
        choices=DonorPaymentChannel.REGULAR_PAYMENT_FREQUENCIES,
        required=False,
        widget=forms.RadioSelect(),
    )
    regular_amount = forms.IntegerField(
        label=_("Regularly (amount)"),
        help_text=_(u"Minimum yearly payment is 1800 Kč"),
        min_value=1,
    )
    payment_type = forms.ChoiceField(
        label=_("payment_type"),
        choices=(('credit-card', _('Credit Card')), ('bank-transfer', _('Bank transfer'))),
        initial='bank-transfer',
    )

    def clean_regular_payments(self):
        if self.cleaned_data['regular_frequency']:
            return 'regular'
        else:
            return 'onetime'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['event'].queryset = Event.objects.filter(slug__isnull=False, enable_registration=True).exclude(slug="")
        self.fields['event'].to_field_name = "slug"

    class Meta:
        model = DonorPaymentChannel
        fields = ('regular_frequency', 'regular_amount', 'regular_payments', 'event', 'money_account', 'payment_type')


class RegularUserForm(MultiModelForm):
    required_css_class = 'required'
    base_fields = {}
    form_classes = OrderedDict([
        ('userprofile', RegularUserForm_UserProfile),
        ('donorpaymentchannel', RegularUserForm_DonorPaymentChannel),
    ])


class RegularUserFormWithProfile(RegularUserForm):
    pass


class FieldNameMappingMixin(object):
    def add_prefix(self, field_name):
        field_name = self.FIELD_NAME_MAPPING.get(field_name, super().add_prefix(field_name))
        return field_name


class RegularDarujmeUserForm_UserProfile(FieldNameMappingMixin, RegularUserForm_UserProfile):
    FIELD_NAME_MAPPING = {
        'first_name': 'payment_data____jmeno',
        'last_name': 'payment_data____prijmeni',
        'email': 'payment_data____email',
        'telephone': 'payment_data____telefon',
    }


class PetitionUserForm_UserProfile(RegularUserForm_UserProfile):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['sex'].required = False
        self.fields['telephone'].required = False

    class Meta:
        model = UserProfile
        fields = ('age_group', 'sex', 'first_name', 'last_name',
                  'email', 'username', 'telephone', 'street', 'city', 'country', 'zip_code')
        required = ('email',)


REGULAR_PAYMENTS_MAP = {
    '28': 'regular',
    '365': 'regular',
    '': 'onetime',
}

REGULAR_FREQUENCY_MAP = {
    '28': 'monthly',
    '365': 'annually',
    '': None,
}


class RegularDarujmeUserForm_DonorPaymentChannel(FieldNameMappingMixin, RegularUserForm_DonorPaymentChannel):
    REGULAR_PAYMENT_CHOICES = (
        ('28', _('Monthly')),
        ('365', _('Anually')),
        ('', _('Onetime payment')),
    )
    regular_payments = forms.ChoiceField(
        label=_("Regular payments"),
        choices=REGULAR_PAYMENT_CHOICES,
        required=False,
        widget=forms.RadioSelect(),
    )
    regular_frequency = forms.ChoiceField(
        label=_("Regular frequency"),
        choices=REGULAR_PAYMENT_CHOICES,
        required=False,
        widget=forms.HiddenInput(),
    )

    FIELD_NAME_MAPPING = {
        'regular_frequency': 'recurringfrequency',
        'regular_payments': 'recurringfrequency',
        'regular_amount': 'amount',
    }

    def clean_regular_frequency(self):
        return REGULAR_FREQUENCY_MAP[self.cleaned_data['regular_frequency']]

    def clean_regular_payments(self):
        return REGULAR_PAYMENTS_MAP[self.cleaned_data['regular_payments']]

    class Meta:
        model = DonorPaymentChannel
        fields = ('regular_frequency', 'regular_payments', 'regular_amount', 'money_account', 'event')


class RegularUserForm_DonorPaymentChannelDPNK(RegularUserForm_DonorPaymentChannel):

    regular_frequency = forms.CharField(
        label=_("Regular frequency"),
        required=False,
        widget=forms.HiddenInput(),
    )

    regular_amount = forms.IntegerField(
        label=_("Amount of monthly donation"),
        help_text=_("We are happy for any donation. However, full membership with advantages, starts from CZK 150 per month."),
        min_value=1,
    )

    def clean_regular_frequency(self):
        return 'monthly'


class PetitionUserForm_PetitionSignature(FieldNameMappingMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['event'].queryset = Event.objects.filter(slug__isnull=False, enable_signing_petitions=True).exclude(slug="")
        self.fields['event'].required = True
        self.fields['event'].to_field_name = "slug"
        self.fields['gdpr_consent'].required = True

    class Meta:
        model = PetitionSignature
        fields = ('event', 'public', 'gdpr_consent')

    FIELD_NAME_MAPPING = {
        'gdpr_consent': 'gdpr',
    }


class RegularUserFormDPNK(RegularUserFormWithProfile):
    form_classes = OrderedDict([
        ('userprofile', RegularUserForm_UserProfile),
        ('donorpaymentchannel', RegularUserForm_DonorPaymentChannelDPNK),
    ])


class RegularDarujmeUserForm(RegularUserForm):
    form_classes = OrderedDict([
        ('userprofile', RegularDarujmeUserForm_UserProfile),
        ('donorpaymentchannel', RegularDarujmeUserForm_DonorPaymentChannel),
    ])


class PetitionUserForm(RegularUserForm):
    form_classes = OrderedDict([
        ('userprofile', PetitionUserForm_UserProfile),
        ('petitionsignature', PetitionUserForm_PetitionSignature),
    ])


class RegisterUserForm(RegularUserForm):
    # TODO: maybe expanse
    form_classes = OrderedDict([
        ('userprofile', PetitionUserForm_UserProfile),
    ])


def get_unique_username(email):
    if not email:
        email = ""
    i = Profile.objects.count()
    while True:
        username = '%s%s' % (email.split('@', 1)[0], i)
        i += 1
        if not Profile.objects.filter(username=username).exists():
            break
    return username


def generate_variable_symbol(dpch):
    # TODO: must be more effective!
    vs_prefix = dpch.event.variable_symbol_prefix
    unit = dpch.money_account.administrative_unit
    if not vs_prefix:
        vs_prefix = '0'
        dpchs_VS = DonorPaymentChannel.objects.filter(
            money_account__administrative_unit=unit,
            VS__startswith=str(vs_prefix),
        ).order_by('-VS').values_list('VS', flat=True)
        if not dpchs_VS:
            # first number
            return '0000000001'
        # first shoud be free.. but just in case we loop over it
        # this is more faster than loop with prefix
        for VS in dpchs_VS:
            new_VS = '%0*d' % (10, int(VS)+1)
            exist = DonorPaymentChannel.objects.filter(
                        money_account__administrative_unit=unit,
                        VS=new_VS,
                        ).exists()
            if not exist:
                return new_VS
    else:
        dpchs_VS = DonorPaymentChannel.objects.filter(
            money_account__administrative_unit=unit,
            VS__startswith=str(vs_prefix),
        ).order_by('VS').values_list('VS', flat=True)
        if not dpchs_VS:
            # first number
            return str(vs_prefix) + '00001'
        for vs in dpchs_VS:
            # we can retype to int because prefix doesnt start with zero
            if str(int(vs)+1) not in dpchs_VS:
                # is it really free?
                exist = DonorPaymentChannel.objects.filter(
                            money_account__administrative_unit=unit,
                            VS=str(int(vs)+1),
                            ).exists()
                if not exist:
                    return str(int(vs)+1)
        else:
            raise ValidationError('OUT OF VS')


def get_or_create_new_user_profile(form):
    try:
        user = UserProfile.objects.get(profileemail__email=form.forms['userprofile'].cleaned_data['email'].lower())
    except UserProfile.DoesNotExist:
        new_user_objects = form.save(commit=False)
        user = new_user_objects['userprofile']
        user.save()
        ProfileEmail.objects.get_or_create(
            email=form.forms['userprofile'].cleaned_data['email'],
            user=user,
            defaults={
                'is_primary': True,
            },
        )

    if form.forms['userprofile'].cleaned_data['telephone']:
        Telephone.objects.get_or_create(telephone=form.forms['userprofile'].cleaned_data['telephone'], user=user)

    return user


def update_or_create_new_payment_channel(form, new_user_profile):
    data = form.clean()['donorpaymentchannel']
    payment_channel, created = DonorPaymentChannel.objects.get_or_create(
        user=new_user_profile,
        event=data.get('event'),
        defaults={
            'money_account': data.get('money_account'),
            'regular_payments': data.get('regular_payments'),
            'regular_amount': data.get('regular_amount'),
            'regular_frequency': data.get('regular_frequency') or None,
            'expected_date_of_first_payment': timezone.now().date() + datetime.timedelta(days=3),
        },
    )
    if not created:
        # update data!
        payment_channel.regular_amount = data.get('regular_amount')
        payment_channel.regular_payments = data.get('regular_payments')
        payment_channel.regular_frequency = data.get('regular_frequency') or None
        payment_channel.save()

    return payment_channel


def get_or_create_new_petition_signature(form, user):
    instance = form['petitionsignature'].instance
    instance.administrative_unit = instance.event.administrative_units.first()
    instance.user = user
    try:
        instance.full_clean()
    except ValidationError:
        instance = None
    else:
        instance.save()
    return instance


class RegularView(FormView):
    template_name = 'regular.html'
    form_class = RegularUserForm
    success_template = 'thanks.html'

    def success_page(self, payment_channel, bank_acc, amount=None, frequency=None, repeated_registration=False):
        if not amount:
            amount = payment_channel.regular_amount
        if not frequency:
            frequency = payment_channel.regular_frequency
        bank_acc = BankAccount.objects.filter(slug=bank_acc)
        donor_frequency = DonorPaymentChannel.REGULAR_PAYMENT_FREQUENCIES_MAP[frequency]
        response = render_to_response(
            self.success_template,
            {
                'amount': amount,
                'frequency': donor_frequency if donor_frequency != '---' else _('Onetime'),
                'account_number': bank_acc.first().bank_account_number if bank_acc else "",
                'user_id': payment_channel.id,
                'payment_channel': payment_channel,
                'user_profile': payment_channel.user,
                'repeated_registration': repeated_registration,
                'addressment': payment_channel.user.get_addressment(),
            },
        )
        if self.request.is_ajax():

            data = {
                'valid': True,
                'account_number': bank_acc.first().bank_account_number if bank_acc else "",
                'variable_symbol': payment_channel.VS,
                'email': payment_channel.user.email,
                'amount': amount,
                'frequency': frequency,
                'repeated_registration': repeated_registration,
                'addressment': payment_channel.user.get_addressment(),
            }
            return JsonResponse(data)
        return response

    def get_post_param(self, request, name, name1=None):
        if request.POST.get(name):
            return request.POST.get(name)
        if request.POST.get(name1):
            return request.POST.get(name1)

    def post(self, request, *args, **kwargs):
        form = self.form_class(request.POST)
        if form.is_valid():
            email = self.get_post_param(request, 'userprofile-email', 'payment_data____email')
            event = self.get_post_param(request, 'donorpaymentchannel-event')
            bank_acc = self.get_post_param(request, 'donorpaymentchannel-money_account')
            user_profiles = UserProfile.objects.filter(profileemail__email=email.lower())
            if user_profiles.exists():
                payment_channels = user_profiles.get().userchannels.filter(event__slug=event)
                if payment_channels.exists():
                    super().post(request, *args, **kwargs)
                    autocom.check(
                        user_profiles=user_profiles,
                        action='resent-data-' + self.request.POST['donorpaymentchannel-payment_type'],
                    )
                    user_data = {}
                    if 'recurringfrequency' in request.POST:
                        user_data['frequency'] = REGULAR_FREQUENCY_MAP[request.POST.get('recurringfrequency')]
                    else:
                        user_data['frequency'] = request.POST.get('donorpaymentchannel-regular_frequency')
                    user_data['name'] = self.get_post_param(request, 'userprofile-first_name', 'payment_data____jmeno')
                    user_data['surname'] = self.get_post_param(request, 'userprofile-last_name', 'payment_data____prijmeni')
                    user_data['amount'] = self.get_post_param(request, 'donorpaymentchannel-regular_amount', 'amount')
                    user_data['telephone'] = self.get_post_param(request, 'userprofile-telephone', 'payment_data____telefon')
                    user_data['email'] = email
                    return self.success_page(
                        payment_channels.get(),
                        bank_acc,
                        user_data['amount'],
                        user_data['frequency'],
                        True,

                    )
            super().post(request, *args, **kwargs)
            user_profiles = UserProfile.objects.filter(profileemail__email=email.lower())
            autocom.check(user_profiles=user_profiles, action='new-user-' + self.request.POST['donorpaymentchannel-payment_type'])
            dpchs = user_profiles.get().userchannels.filter(event__slug=event)
            if dpchs:
                dpch = dpchs.first()
            else:
                dpch = update_or_create_new_payment_channel(form, user_profiles.first())
            return self.success_page(
                dpch,
                bank_acc,
                dpch.regular_amount,
                dpch.regular_frequency,
                False,
            )
        return render(request, self.template_name, {'form': form})

    def get_initial(self):
        initial = super().get_initial()
        initial_userprofile = {}
        if self.request.GET.get('firstname'):
            initial_userprofile['first_name'] = self.request.GET.get('firstname')
        if self.request.GET.get('surname'):
            initial_userprofile['last_name'] = self.request.GET.get('surname')
        if self.request.GET.get('email'):
            initial_userprofile['email'] = self.request.GET.get('email')
        if self.request.GET.get('telephone'):
            initial_userprofile['telephone'] = self.request.GET.get('telephone')
        initial['userprofile'] = initial_userprofile
        return initial

    def form_valid(self, form):
        new_user_profile = get_or_create_new_user_profile(form)
        payment_channel = update_or_create_new_payment_channel(form, new_user_profile)
        new_user_profile.administrative_units.add(payment_channel.money_account.administrative_unit)
        return self.success_page(payment_channel, form.clean()['donorpaymentchannel']['money_account'].slug)

    def form_invalid(self, form):
        response = super().form_invalid(form)
        if self.request.is_ajax():
            return JsonResponse(form.errors, status=400)
        else:
            return response


@method_decorator(csrf_exempt, name='dispatch')
class RegularDPNKView(RegularView):
    template_name = 'regular-dpnk.html'
    form_class = RegularUserFormDPNK
    success_template = 'thanks-dpnk.html'

    def get_initial(self):
        initial = super().get_initial()
        initial['campaign'] = 'dpnk'
        return initial


class RegularWPView(RegularView):
    template_name = 'regular-wp.html'
    form_class = RegularUserFormWithProfile
    success_template = 'thanks-wp.html'


@method_decorator(csrf_exempt, name='dispatch')
class RegularDarujmeView(RegularView):
    template_name = 'regular.html'
    form_class = RegularDarujmeUserForm
    success_template = 'thanks-darujme.html'


@method_decorator(csrf_exempt, name='dispatch')
class RegisterWithoutPaymentView(FormView):
    template_name = 'regular.html'
    form_class = RegisterUserForm
    success_template = 'thanks-darujme.html'
    success_url = 'petition-signatures'

    def get(self, *args, **kwargs):
        get_object_or_404(AdministrativeUnit, slug=self.kwargs['unit'])
        return super().get(*args, **kwargs)

    def form_valid(self, form):
        unit = get_object_or_404(AdministrativeUnit, slug=self.kwargs['unit'])
        user = get_or_create_new_user_profile(form)
        user.administrative_units.add(unit)
        autocom.check(UserProfile.objects.filter(id=user.id), action='new-user')
        return http.HttpResponse(_("Thanks for register!"))


@method_decorator(csrf_exempt, name='dispatch')
class PetitionView(FormView):
    template_name = 'regular.html'
    form_class = PetitionUserForm
    success_template = 'thanks-darujme.html'
    success_url = 'petition-signatures'

    def form_valid(self, form):
        user = get_or_create_new_user_profile(form)
        petition_signature = get_or_create_new_petition_signature(form, user)
        if petition_signature:
            user.administrative_units.add(petition_signature.administrative_unit)
            action = 'user-signature'
        else:
            action = 'user-signature-again'
        autocom.check(UserProfile.objects.filter(id=user.id), action=action)
        super().form_valid(form)
        return http.HttpResponse(_('Petition signed'))


class DonatorsView(View):
    def get(self, request, unit):
        unit = get_object_or_404(AdministrativeUnit, slug=self.kwargs['unit'])
        users = Preference.objects.filter(administrative_unit=unit, public=True).values_list('user')
        donators = DonorPaymentChannel.objects.filter(
            user__in=users,
            money_account__administrative_unit=unit,
            payment_total__gt=0,
        )
        n_donators = donators.count()
        n_regular = donators.filter(user__is_active=True, regular_payments="regular").count()
        return render_to_response(
            'donators.html',
            {
                'n_donators': n_donators,
                'n_regular': n_regular,
                'donators': donators,
            },
        )


def stat_members(request):
    members_by_months = DonorPaymentChannel.objects\
        .filter(user__is_active=True)\
        .annotate(month=TruncMonth('user__date_joined'))\
        .values('month')\
        .annotate(
            total=Count('id'),
            regular=Count(Case(When(regular_payments="regular", then=1), output_field=IntegerField())),
            irregular=Count(Case(When(~Q(regular_payments="regular"), then=1), output_field=IntegerField())),
        )\
        .order_by('month')\
        .all()
    run_total = 0
    for payment in members_by_months:
        run_total += payment['total']
        payment['run_total'] = run_total
    return render_to_response(
        'stat-members.html',
        {
            'members_by_months': members_by_months,
            'total_members': DonorPaymentChannel.objects.all().filter(user__is_active=True).aggregate(Count('id'))['id__count'],
            'site_header': _("Member statistics"),
        },
    )


def stat_payments(request):
    payments_by_months = Payment.objects\
        .filter(~Q(type='expected'))\
        .annotate(month=TruncMonth('date'))\
        .values('month')\
        .annotate(total=Sum('amount'), donors=Count('user_donor_payment_channel'))\
        .order_by('month')\
        .all()
    run_total = 0
    for payment in payments_by_months:
        run_total += payment['total']
        payment['run_total'] = run_total
    return render_to_response(
        'stat-payments.html',
        {
            'payments_by_months': payments_by_months,
            'total_amount': Payment.objects.all().filter(~Q(type='expected')).aggregate(Sum('amount'))['amount__sum'],
            'site_header': _("Payments statistics"),
        },
    )


class CampaignStatistics(View):
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        campaign = get_object_or_404(Event, slug=kwargs['campaign_slug'], allow_statistics=True)
        return http.HttpResponse(
            json.dumps({
                'expected-yearly-income': campaign.expected_yearly_income(),
                'total-income': campaign.yield_total(),
                'number-of-onetime-members': campaign.number_of_onetime_members(),
                'number-of-regular-members': campaign.number_of_regular_members(),
                'number-of-active-members': campaign.number_of_active_members(),
                'number-of-all-members': campaign.number_of_all_members(),
                'number-of-confirmed-members': campaign.number_of_confirmed_members(),
            }
            ),
            content_type='application/json',
        )


class PetitionSignatures(View):
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        event = get_object_or_404(Event, slug=kwargs['campaign_slug'], allow_statistics=True)
        signatures = PetitionSignature.objects.filter(event=event, email_confirmed=True, public=True).order_by('-created')

        # signatures = signatures.annotate(
        #     userprofile_first_name=Case(
        #         When(public=True, then='user__userprofile__first_name'),
        #         default=Value('------'),
        #         output_field=CharField(),
        #     ),
        #     userprofile_last_name=Case(
        #         When(public=True, then='user__userprofile__last_name'),
        #         default=Value('------'),
        #         output_field=CharField(),
        #     ),
        #     companyprofile_name=Case(
        #         When(public=True, then='user__companyprofile__name'),
        #         default=Value('------'),
        #         output_field=CharField(),
        #     ),
        # )

        signatures = signatures.values(
            'user__userprofile__first_name',
            'user__userprofile__last_name',
            'created',
        )

        return JsonResponse(list(signatures), safe=False)


class SuccessMessageMixin (object):
    """
    From https://github.com/AndrewIngram/django-extra-views/pull/147/files
    Adds success message on views with inlines if django.contrib.messages framework is used.
    In order to use just add mixin in to inheritance before main class, e.g.:
    class MyCreateWithInlinesView (SuccessMessageMixin, CreateWithInlinesView):
        success_message='Something was created!'
    """
    success_message = ''

    def forms_valid(self, form, inlines):
        response = super(SuccessMessageMixin, self).forms_valid(form, inlines)
        success_message = self.get_success_message(form.cleaned_data)
        if success_message:
            messages.success(self.request, success_message)
        return response

    def get_success_message(self, cleaned_data):
        return self.success_message % cleaned_data


class SesameUserMixin():
    """
    We don't want to use django-sesame to authenticate system-wide,
    so we use it only to authenticate in certain views
    """
    def get_object(self):
        backend = ModelBackend()
        try:
            self.token = self.request.GET['url_auth_token']
        except KeyError:
            raise PermissionDenied("No auth token set")
        self.user = backend.parse_token(self.token)
        if self.user is None:
            raise PermissionDenied("bad token")
        return self.user

    def get_success_url(self):
        return "%s?url_auth_token=%s" % (super().get_success_url(), self.token)


class PetitionConfirmEmailView(SesameUserMixin, View):
    def get(self, *args, **kwargs):
        event = get_object_or_404(Event, slug=kwargs['campaign_slug'])
        user = self.get_object()
        if user:
            signature = PetitionSignature.objects.get(event=event, user=user)
            signature.email_confirmed = True
            signature.save()
            if event.email_confirmation_redirect:
                return redirect(event.email_confirmation_redirect, permanent=False)
            else:
                return http.HttpResponse(_('Signature was confirmed'))
        else:
            raise http.Http404


class SendMailingListView(SesameUserMixin, View):
    def get(self, request, *args, **kwargs):
        unit = get_object_or_404(AdministrativeUnit, slug=kwargs['unit'])
        user = self.get_object()
        preference = user.preference_set.get(administrative_unit=unit)

        preference.send_mailing_lists = False if kwargs['unsubscribe'] == 'unsubscribe' else True
        preference.save()
        user_profiles = UserProfile.objects.filter(id=user.id)
        autocom.check(user_profiles=user_profiles, action='user-mailing-' + kwargs['unsubscribe'])
        return http.HttpResponse(f"{kwargs['unsubscribe']} was done")


class PasswordResetView(View):
    template_name = "password/password_reset.html"

    def post(self, request, *args, **kwargs):
        form = PasswordResetForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data['email']
            email = ProfileEmail.objects.filter(email=data)
            if email.exists():
                email = email.first()
                user = email.user
                email_template_name = "password/password_reset_email.txt"

                if not user.password:
                    # password muset be set or token is not generated
                    user.set_password(UserProfile.objects.make_random_password())
                    user.save()
                    user.refresh_from_db()

                variables = {
                    "email": email.email,
                    'domain': settings.WEB_URL,
                    'site_name': settings.SITE_NAME,
                    "username": user.username,
                    "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                    "user": user,
                    'token': default_token_generator.make_token(user),
                }
                template = render_to_string(email_template_name, variables)
                administrative_unit = AdministrativeUnit.objects.first()

                email = EmailMultiAlternatives(
                    subject="password reset",
                    body=template,
                    from_email=administrative_unit.from_email_str,
                    to=[email.email],
                )
                email.send(fail_silently=False)
        return redirect("password_reset_done")

    def get(self, request, *args, **kwargs):
        password_reset_form = PasswordResetForm()
        return render(
            request=request,
            template_name="password/password_reset.html",
            context={"password_reset_form": password_reset_form},
        )
