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
import json
from collections import OrderedDict

from betterforms.multiform import MultiModelForm

from django import forms, http
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.tokens import default_token_generator
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.mail import mail_managers
from django.core.validators import MinLengthValidator, RegexValidator, ValidationError
from django.db.models import Case, CharField, Count, IntegerField, Q, Sum, Value, When
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render, render_to_response
from django.template.loader import render_to_string
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.views.generic.edit import FormView

from extra_views import InlineFormSet, UpdateWithInlinesView

from interactions.models import PetitionSignature  # TODO: Not sure if it works (model moved from aklub to interaction app)

from sesame.backends import ModelBackend

from . import autocom
from .models import (
    DonorPaymentChannel, Event, MoneyAccount, Payment,
    Profile, ProfileEmail, Source, Telephone, UserInCampaign,
    UserProfile,
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

    def clean(self):
        if not self.errors:
            self.cleaned_data['username'] = get_unique_username(self.cleaned_data['email'])
        emails = ProfileEmail.objects.filter(email=self.cleaned_data['email'])
        if emails:
            self._errors['email'] = self.error_class(['This e-mail is already used.'])
        super().clean()
        return self.cleaned_data

    def save(self, commit, *args, **kwargs):
        ret_val = super().save(commit, *args, **kwargs)
        if commit:
            if self.cleaned_data['telephone']:
                Telephone.objects.create(telephone=self.cleaned_data['telephone'], user=self.instance)

            ProfileEmail.objects.create(email=self.cleaned_data['email'], user=self.instance)
        return ret_val

    def _post_clean(self):
        email = self.cleaned_data['email']
        r = super()._post_clean()
        if self._errors.get('email') == ['This e-mail is already used.']:
            del self._errors['email']
            self.email_used = email
        return r

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


class CampaignMixin(forms.ModelForm):
    campaign = forms.ModelChoiceField(
        queryset=Event.objects.filter(slug__isnull=False, enable_registration=True).exclude(slug=""),
        to_field_name="slug",
    )


class BankAccountMixin(forms.ModelForm):
    money_account = forms.ModelChoiceField(
            queryset=MoneyAccount.objects.filter(slug__isnull=False).exclude(slug=""),
            to_field_name="slug",
    )


class RegularUserForm_DonorPaymentChannel(BankAccountMixin, CampaignMixin, forms.ModelForm):
    required_css_class = 'required'

    regular_payments = forms.CharField(
        label=_("Regular payments"),
        required=False,
        widget=forms.HiddenInput(),
    )
    regular_frequency = forms.ChoiceField(
        label=_("Regular payments"),
        choices=UserInCampaign.REGULAR_PAYMENT_FREQUENCIES,
        required=False,
        widget=forms.RadioSelect(),
    )
    regular_amount = forms.IntegerField(
        label=_("Regularly (amount)"),
        help_text=_(u"Minimum yearly payment is 1800 Kč"),
        min_value=1,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['event'].required = False
        self.fields['event'].widget = forms.HiddenInput()

    def clean_regular_payments(self):
        return 'regular'

    def clean(self):
        if self.cleaned_data.get('campaign'):
            self.cleaned_data['event'] = self.cleaned_data['campaign']
        return self.cleaned_data

    class Meta:
        model = DonorPaymentChannel
        fields = ('regular_frequency', 'regular_amount', 'regular_payments', 'campaign', 'event', 'money_account')


class RegularUserForm(MultiModelForm):
    required_css_class = 'required'
    base_fields = {}
    form_classes = OrderedDict([
        ('userprofile', RegularUserForm_UserProfile),
        ('userincampaign', RegularUserForm_DonorPaymentChannel),
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
        'regular_amount': 'ammount',
    }

    def clean_regular_frequency(self):
        return REGULAR_FREQUENCY_MAP[self.cleaned_data['regular_frequency']]

    def clean_regular_payments(self):
        return REGULAR_PAYMENTS_MAP[self.cleaned_data['regular_payments']]

    class Meta:
        model = DonorPaymentChannel
        fields = ('regular_frequency', 'regular_payments', 'regular_amount', 'campaign', 'money_account', 'event')


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
    campaign = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean_campaign(self):
        return Event.objects.get(slug="dpnk")

    def clean_regular_frequency(self):
        return 'monthly'


class PetitionUserForm_PetitionSignature(FieldNameMappingMixin, CampaignMixin, BankAccountMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['event'].queryset = Event.objects.filter(slug__isnull=False, enable_signing_petitions=True).exclude(slug="")
        self.fields['gdpr_consent'].required = True

    class Meta:
        model = PetitionSignature
        fields = ('event', 'public', 'gdpr_consent', 'money_account')

    FIELD_NAME_MAPPING = {
        'gdpr_consent': 'gdpr',
    }


class PetitionUserForm_DonorPaymentChannel(CampaignMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['event'].queryset = Event.objects.filter(slug__isnull=False, enable_signing_petitions=True).exclude(slug="")

    class Meta:
        model = DonorPaymentChannel
        fields = ('event',)


class RegularUserFormDPNK(RegularUserFormWithProfile):
    form_classes = OrderedDict([
        ('userprofile', RegularUserForm_UserProfile),
        ('userincampaign', RegularUserForm_DonorPaymentChannelDPNK),
    ])


class RegularDarujmeUserForm(RegularUserForm):
    form_classes = OrderedDict([
        ('userprofile', RegularDarujmeUserForm_UserProfile),
        ('userincampaign', RegularDarujmeUserForm_DonorPaymentChannel),
    ])


class PetitionUserForm(RegularUserForm):
    form_classes = OrderedDict([
        ('userprofile', PetitionUserForm_UserProfile),
        ('userincampaign', PetitionUserForm_PetitionSignature),
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


def create_new_user_profile(form, regular):
    new_user_objects = form.save(commit=False)
    new_user_profile = new_user_objects['userprofile']
    # Save new user instance
    if hasattr(form.forms['userprofile'], 'email_used') and form.forms['userprofile'].email_used:
        new_user_profile = UserProfile.objects.get(profileemail__email=form.forms['userprofile'].email_used)
    else:
        new_user_profile.save()
        ProfileEmail.objects.create(email=form.forms['userprofile'].cleaned_data['email'], user=new_user_profile, is_primary=True)
    if form.forms['userprofile'].cleaned_data['telephone']:
        Telephone.objects.create(telephone=form.forms['userprofile'].cleaned_data['telephone'], user=new_user_profile)

    cache.clear()
    return new_user_profile


def create_new_payment_channel(form, source_type, new_user_profile, regular, source_slug='web'):
    if source_type == 'regular':
        new_user_objects = form.save(commit=False)
        payment_channel = new_user_objects['userincampaign']
    else:
        data = form.clean()
        payment_channel, _ = DonorPaymentChannel.objects.get_or_create(
                                                    user=new_user_profile,
                                                    regular_payments='',
                                                    money_account=data['userincampaign'].get('money_account'),
                                                    event=data['userincampaign'].get('campaign'),
        )
    assert isinstance(payment_channel, DonorPaymentChannel), \
        "payment_channel shoud be DonnorPaymentChannel, but is %s" % type(payment_channel)
    if regular:
        payment_channel.regular_payments = regular
    payment_channel.source = Source.objects.get(slug=source_slug)
    payment_channel.user = new_user_profile
    payment_channel.save()

    cache.clear()
    return payment_channel


def create_new_petition_signature(form, new_user_profile, regular):
    new_user_objects = form.save(commit=False)
    petition_signature = new_user_objects['userincampaign']
    assert isinstance(petition_signature, PetitionSignature), \
        "petition_signature shoud be PetitionSignature, but is %s" % type(petition_signature)
    petition_signature.user = new_user_profile
    petition_signature.save()

    cache.clear()
    return petition_signature


class RegularView(FormView):
    template_name = 'regular.html'
    form_class = RegularUserForm
    success_template = 'thanks.html'
    source_slug = 'web'

    def success_page(self, payment_channel, amount=None, frequency=None, repeated_registration=False):
        if not amount:
            amount = payment_channel.regular_amount
        if not frequency:
            frequency = payment_channel.regular_frequency
        response = render_to_response(
            self.success_template,
            {
                'amount': amount,
                'frequency': UserInCampaign.REGULAR_PAYMENT_FREQUENCIES_MAP[frequency],
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
                'account_number': "2400063333 / 2010",
                'variable_symbol': payment_channel.VS,
                'email': payment_channel.user.email,
                'amount': amount,
                'frequency': frequency,
                'repeated_registration': repeated_registration,
                'addressment': payment_channel.user.get_addressment(),
            }
            return JsonResponse(data)
        return response

    def get_post_param(self, request, name, name1):
        if request.POST.get(name):
            return request.POST.get(name)
        if request.POST.get(name1):
            return request.POST.get(name1)

    def post(self, request, *args, **kwargs):
        email = self.get_post_param(request, 'userprofile-email', 'payment_data____email')
        event = self.get_post_param(request, 'userincampaign-campaign', 'campaign')
        if email:
            user_profiles = UserProfile.objects.filter(profileemail__email=email)
            if user_profiles.exists():
                payment_channels = user_profiles.get().userchannels.filter(event__slug=event)
                if user_profiles.exists() and payment_channels.exists():
                    autocom.check(user_profiles=user_profiles, event=Event.objects.get(slug=event), action='resend-data')
                    user_data = {}
                    if 'recurringfrequency' in request.POST:
                        user_data['frequency'] = REGULAR_FREQUENCY_MAP[request.POST.get('recurringfrequency')]
                    else:
                        user_data['frequency'] = request.POST.get('userincampaign-regular_frequency')
                    user_data['name'] = self.get_post_param(request, 'userprofile-first_name', 'payment_data____jmeno')
                    user_data['surname'] = self.get_post_param(request, 'userprofile-last_name', 'payment_data____prijmeni')
                    user_data['amount'] = self.get_post_param(request, 'userincampaign-regular_amount', 'ammount')
                    user_data['telephone'] = self.get_post_param(request, 'userprofile-telephone', 'payment_data____telefon')
                    user_data['email'] = email
                    mail_managers(
                        _("Repeated registration"),
                        "Repeated registration for email %(email)s\n"
                        "name: %(name)s\n"
                        "surname: %(surname)s\n"
                        "frequency: %(frequency)s\n"
                        "telephone: %(telephone)s\n"
                        "amount: %(amount)s" % user_data,
                    )
                    return self.success_page(
                        payment_channels.get(),
                        user_data['amount'],
                        user_data['frequency'],
                        True,
                    )
        return super().post(request, *args, **kwargs)

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
        new_user_profile = create_new_user_profile(form, regular=None)
        payment_channel = create_new_payment_channel(form, 'regular', new_user_profile, regular=None, source_slug=self.source_slug)
        return self.success_page(payment_channel)

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
    source_slug = 'dpnk'

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
class PetitionView(RegularView):
    template_name = 'regular.html'
    form_class = PetitionUserForm
    success_template = 'thanks-darujme.html'
    success_url = 'petition-signatures'

    def form_valid(self, form):
        new_user_profile = create_new_user_profile(form, regular=None)
        create_new_petition_signature(form, new_user_profile, regular=None)
        payment_channel = create_new_payment_channel(form, 'petition', new_user_profile, regular=None, source_slug=self.source_slug)
        return self.success_page(payment_channel)


def donators(request):
    payed = Payment.objects.exclude(type='expected')
    donators = DonorPaymentChannel.objects.filter(
        user__preference__public=True,
        payment__in=payed,).distinct().order_by(
        'user__userprofile__last_name',
        'user__companyprofile__name',
    )
    n_donators = len(donators)
    n_regular = len(donators.filter(user__is_active=True, regular_payments="regular"))
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


def profiles(request):
    from_date = request.GET.get('from') or '1970-1-1'
    paying = request.GET.get('paying')

    users = (
        DonorPaymentChannel.objects.filter(registered_support__gte=from_date).order_by('-registered_support') |
        DonorPaymentChannel.objects.filter(id__in=(493, 89, 98, 921, 33, 886, 1181, 842, 954, 25))).\
        exclude(user__preference__public=False, user__profile_picture__isnull=False).\
        order_by(
            "-user__userprofile__last_name",
            "-user__companyprofile__name",
            "user__userprofile__first_name",
        )
    result = [
        {
            'firstname': (
                (u.user.preference_set.first().public if u.user.preference_set.first() else None)
                and u.user.first_name or ''
            ),
            'surname': (
                (u.user.preference_set.first().public if u.user.preference_set.first() else None)
                and u.user.last_name or ''
                ),
            'text': u.user.profile_text or '',
            'picture': u.user.profile_picture and u.user.profile_picture.url or '',
            'picture_thumbnail': u.user.profile_picture and u.user.profile_picture.thumbnail.url or '',
        } for u in users if ((not paying) or (u.payment_total > 0))
    ]
    return http.HttpResponse(json.dumps(result), content_type='application/json')


class CampaignStatistics(View):
    @method_decorator(never_cache)
    @method_decorator(cache_page(60))  # cache in memcached for 1 minute
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
    @method_decorator(never_cache)
    @method_decorator(cache_page(60))  # cache in memcached for 1 minute
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        event = get_object_or_404(Event, slug=kwargs['campaign_slug'], allow_statistics=True, enable_signing_petitions=True)
        signatures = PetitionSignature.objects.filter(event=event, email_confirmed=True)
        signatures = signatures.order_by('-date')
        signatures = signatures.annotate(
            userprofile_first_name=Case(
                When(public=True, then='user__userprofile__first_name'),
                default=Value('------'),
                output_field=CharField(),
            ),
            userprofile_last_name=Case(
                When(public=True, then='user__userprofile__last_name'),
                default=Value('------'),
                output_field=CharField(),
            ),
            companyprofile_name=Case(
                When(public=True, then='user__companyprofile__name'),
                default=Value('------'),
                output_field=CharField(),
            ),
        )
        signatures = signatures.values(
            'userprofile_first_name',
            'userprofile_last_name',
            'companyprofile_name',
            'date',
        )
        signatures = signatures[:100]
        for signature in signatures:
            signature['created'] = signature.pop('date')
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


class UserInCampaignInline(InlineFormSet):
    model = UserInCampaign
    factory_kwargs = {
        'fk_name': 'userprofile',
        'fields': ('wished_information',),
        'can_delete': False,
        'extra': 0,
    }
    fields = ('wished_information',)


class MailingFormSetView(SuccessMessageMixin, SesameUserMixin, UpdateWithInlinesView):
    model = UserProfile
    template_name = 'mailing.html'
    success_message = "Nastavení emailů úspěšně změněno"
    success_url = reverse_lazy('mailing-configuration')
    inlines = [UserInCampaignInline, ]
    fields = ('send_mailing_lists',)


class ConfirmEmailView(SesameUserMixin, View):

    def get(self, *args, **kwargs):
        user_in_campaign = UserInCampaign.objects.get(campaign__slug=kwargs['campaign_slug'], userprofile=self.get_object())
        user_in_campaign.email_confirmed = True
        user_in_campaign.save()
        cache.clear()
        return redirect(user_in_campaign.campaign.email_confirmation_redirect, permanent=False)


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
                    'protocol': 'https',
                }
                template = render_to_string(email_template_name, variables)

                from django.core.mail import EmailMultiAlternatives
                from .models import AdministrativeUnit
                administrative_unit = AdministrativeUnit.objects.first()

                email = EmailMultiAlternatives(
                    subject="password reset",
                    body=template,
                    from_email=administrative_unit.from_email_str if administrative_unit else 'Klub pratel Auto*Matu <kp@auto-mat.cz>',
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
