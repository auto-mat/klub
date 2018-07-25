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
from django.core.mail import mail_managers
from django.core.validators import MinLengthValidator, RegexValidator
from django.db.models import Case, Count, IntegerField, Q, Sum, When
from django.db.models.functions import TruncMonth
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render_to_response
from django.urls import reverse_lazy
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.cache import cache_page, never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.views.generic.edit import FormView

from extra_views import InlineFormSet, UpdateWithInlinesView

from . import autocom
from .models import Campaign, Payment, Source, UserInCampaign, UserProfile


class RegularUserForm_UserProfile(forms.ModelForm):
    required_css_class = 'required'

    email = forms.EmailField(
        required=True,
    )
    username = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean_username(self):
        "This function is required to overwrite an inherited username clean"
        return self.cleaned_data['username']

    def clean(self):
        if not self.errors:
            self.cleaned_data['username'] = get_unique_username(self.cleaned_data['email'])
        super().clean()
        return self.cleaned_data

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
        fields = ('first_name', 'last_name', 'email', 'username', 'telephone',)
        required = ('first_name', 'last_name', 'email', 'telephone',)


class CampaignMixin(forms.ModelForm):
    campaign = forms.ModelChoiceField(
        queryset=Campaign.objects.filter(slug__isnull=False, enable_registration=True).exclude(slug=""),
        to_field_name="slug",
    )


class RegularUserForm_UserInCampaign(CampaignMixin, forms.ModelForm):
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

    def clean_regular_payments(self):
        return 'regular'

    class Meta:
        model = UserInCampaign
        fields = ('regular_frequency', 'regular_amount', 'regular_payments', 'campaign')


class RegularUserForm(MultiModelForm):
    required_css_class = 'required'
    base_fields = {}
    form_classes = OrderedDict([
        ('userprofile', RegularUserForm_UserProfile),
        ('userincampaign', RegularUserForm_UserInCampaign),
    ])


class RegularUserFormWithProfile(RegularUserForm):
    pass


class FieldNameMappingMixin(object):
    def add_prefix(self, field_name):
        field_name = self.FIELD_NAME_MAPPING.get(field_name, field_name)
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

    class Meta:
        model = UserProfile
        fields = ('sex', 'first_name', 'last_name', 'email', 'username', 'telephone',)
        required = ('first_name', 'last_name', 'email', 'telephone',)


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


class RegularDarujmeUserForm_UserInCampaign(FieldNameMappingMixin, RegularUserForm_UserInCampaign):
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
        model = UserInCampaign
        fields = ('regular_frequency', 'regular_payments', 'regular_amount', 'campaign')


class RegularUserForm_UserInCampaignDPNK(RegularUserForm_UserInCampaign):

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


class PetitionUserForm_UserInCampaign(CampaignMixin, forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['campaign'].queryset = Campaign.objects.filter(slug__isnull=False, enable_signing_petitions=True).exclude(slug="")

    class Meta:
        model = UserInCampaign
        fields = ('campaign', )


class RegularUserFormDPNK(RegularUserFormWithProfile):
    form_classes = OrderedDict([
        ('userprofile', RegularUserForm_UserProfile),
        ('userincampaign', RegularUserForm_UserInCampaignDPNK),
    ])


class RegularDarujmeUserForm(RegularUserForm):
    form_classes = OrderedDict([
        ('userprofile', RegularDarujmeUserForm_UserProfile),
        ('userincampaign', RegularDarujmeUserForm_UserInCampaign),
    ])


class PetitionUserForm(RegularUserForm):
    form_classes = OrderedDict([
        ('userprofile', PetitionUserForm_UserProfile),
        ('userincampaign', PetitionUserForm_UserInCampaign),
    ])


def get_unique_username(email):
    if not email:
        email = ""
    i = UserProfile.objects.count()
    while True:
        username = '%s%s' % (email.split('@', 1)[0], i)
        i += 1
        if not UserProfile.objects.filter(username=username).exists():
            break
    return username


def generate_variable_symbol(max_variable_symbol=9999):
    now = datetime.datetime.now()
    reg_n_today = len(
        UserInCampaign.objects.filter(
            registered_support__gt=(
                now - datetime.timedelta(days=1)
            ),
        ),
    )
    for i in range(reg_n_today + 1, max_variable_symbol):
        variable_symbol = '%s%02d%02d%04d' % (
            str(now.year)[-2:], now.month, now.day, i)
        if len(UserInCampaign.objects.filter(variable_symbol=variable_symbol)) == 0:
            break
    else:
        assert 0, "Out of free variable symbols, date %s, reg_n_today=%d" % (now, reg_n_today)
    return variable_symbol


def new_user(form, regular, source_slug='web'):
    # Check number of registrations so far today
    # TODO: Lock DB access here (to ensure uniqueness of VS)
    variable_symbol = generate_variable_symbol()
    # variable_symbol is now unique in database
    # Create new user instance and fill in additional data
    new_user_objects = form.save(commit=False)
    new_user_profile = new_user_objects['userprofile']
    new_user_in_campaign = new_user_objects['userincampaign']
    if regular:
        new_user_in_campaign.regular_payments = regular
    new_user_in_campaign.variable_symbol = variable_symbol
    new_user_in_campaign.source = Source.objects.get(slug=source_slug)
    # Save new user instance
    if hasattr(form.forms['userprofile'], 'email_used') and form.forms['userprofile'].email_used:
        new_user_profile = UserProfile.objects.get(email=form.forms['userprofile'].email_used)
    else:
        new_user_profile.save()
    new_user_in_campaign.userprofile = new_user_profile
    new_user_in_campaign.save()
    # TODO: Unlock DB access here
    return new_user_in_campaign.id


class RegularView(FormView):
    template_name = 'regular.html'
    form_class = RegularUserForm
    success_template = 'thanks.html'
    source_slug = 'web'

    def success_page(self, userincampaign, amount=None, frequency=None, repeated_registration=False):
        if not amount:
            amount = userincampaign.regular_amount
        if not frequency:
            frequency = userincampaign.regular_frequency
        response = render_to_response(
            self.success_template,
            {
                'amount': amount,
                'frequency': UserInCampaign.REGULAR_PAYMENT_FREQUENCIES_MAP[frequency],
                'user_id': userincampaign.id,
                'userincampaign': userincampaign,
                'repeated_registration': repeated_registration,
            },
        )
        if self.request.is_ajax():
            data = {
                'valid': True,
                'account_number': "2400063333 / 2010",
                'variable_symbol': userincampaign.variable_symbol,
                'email': userincampaign.userprofile.email,
                'amount': amount,
                'frequency': frequency,
                'repeated_registration': repeated_registration,
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
        campaign = self.get_post_param(request, 'userincampaign-campaign', 'campaign')
        if email:
            if UserInCampaign.objects.filter(userprofile__email=email, campaign__slug=campaign).exists():
                userincampaign = UserInCampaign.objects.get(userprofile__email=email, campaign__slug=campaign)
                autocom.check(users=UserInCampaign.objects.filter(pk=userincampaign.pk), action='resend-data')
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
                    userincampaign,
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
        user_id = new_user(form, regular=None, source_slug=self.source_slug)
        userincampaign = UserInCampaign.objects.get(id=user_id)
        return self.success_page(userincampaign)

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


def donators(request):
    payed = Payment.objects.exclude(type='expected').values_list('user_id', flat=True)
    donators = UserInCampaign.objects.filter(userprofile__public=True, id__in=payed).order_by('userprofile__last_name')
    n_donators = len(donators)
    n_regular = len(donators.filter(userprofile__is_active=True, regular_payments="regular"))
    return render_to_response(
        'donators.html',
        {
            'n_donators': n_donators,
            'n_regular': n_regular,
            'donators': donators,
        },
    )


def stat_members(request):
    members_by_months = UserInCampaign.objects\
        .filter(userprofile__is_active=True)\
        .annotate(month=TruncMonth('userprofile__date_joined'))\
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
            'total_members': UserInCampaign.objects.all().filter(userprofile__is_active=True).aggregate(Count('id'))['id__count'],
            'site_header': _("Member statistics"),
        },
    )


def stat_payments(request):
    payments_by_months = Payment.objects\
        .filter(~Q(type='expected'))\
        .annotate(month=TruncMonth('date'))\
        .values('month')\
        .annotate(total=Sum('amount'), donors=Count('user'))\
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
        UserInCampaign.objects.filter(registered_support__gte=from_date).order_by('-registered_support') |
        UserInCampaign.objects.filter(id__in=(493, 89, 98, 921, 33, 886, 1181, 842, 954, 25))).\
        exclude(userprofile__public=False, userprofile__profile_picture__isnull=False).\
        order_by("-userprofile__last_name", "userprofile__first_name")

    result = [
        {
            'firstname': u.userprofile.public and u.userprofile.first_name or '',
            'surname': u.userprofile.public and u.userprofile.last_name or '',
            'text': u.userprofile.profile_text or '',
            'picture': u.userprofile.profile_picture and u.userprofile.profile_picture.url or '',
            'picture_thumbnail': u.userprofile.profile_picture and u.userprofile.profile_picture.thumbnail.url or '',
        } for u in users if ((not paying) or (u.payment_total > 0))
    ]
    return http.HttpResponse(json.dumps(result), content_type='application/json')


class CampaignStatistics(View):
    @method_decorator(never_cache)
    @method_decorator(cache_page(24 * 60))  # cache in memcached for 1h
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        campaign = get_object_or_404(Campaign, slug=kwargs['campaign_slug'], allow_statistics=True)
        return http.HttpResponse(
            json.dumps({
                'expected-yearly-income': campaign.expected_yearly_income(),
                'total-income': campaign.yield_total(),
                'number-of-onetime-members': campaign.number_of_onetime_members(),
                'number-of-regular-members': campaign.number_of_regular_members(),
                'number-of-active-members': campaign.number_of_active_members(),
            }
            ),
            content_type='application/json',
        )


class UserInCampaignInline(InlineFormSet):
    model = UserInCampaign
    factory_kwargs = {
        'fk_name': 'userprofile',
        'fields': ('wished_information',),
        'can_delete': False,
        'extra': 0,
    }
    fields = ('wished_information',)


class MailingFormSetView(UpdateWithInlinesView):
    model = UserProfile
    template_name = 'mailing.html'
    success_url = reverse_lazy('mailing-configuration')
    inlines = [UserInCampaignInline, ]
    fields = ('send_mailing_lists',)

    def get_object(self):
        return self.request.user
