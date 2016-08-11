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
from . import autocom
from .models import UserInCampaign, UserProfile, Payment, Source, StatMemberCountsByMonths, StatPaymentsByMonths, Campaign
from betterforms.multiform import MultiModelForm
from collections import OrderedDict
from django import forms, http
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.mail import EmailMessage
from django.core.validators import RegexValidator, MinLengthValidator
from django.db.models import Sum, Count, Q
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.utils.decorators import method_decorator
from django.utils.translation import ugettext as _
from django.views.decorators.cache import cache_page, never_cache
from django.views.generic import View
from django.views.generic.edit import FormView
from formtools.wizard.views import SessionWizardView
import datetime
import json
import re


class RegularUserForm_User(forms.ModelForm):
    required_css_class = 'required'

    email = forms.EmailField(
        required=True)
    username = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean_username(self):
        "This function is required to overwrite an inherited username clean"
        return self.cleaned_data['username']

    def clean(self):
        if not self.errors:
            self.cleaned_data['username'] = '%s%s' % (self.cleaned_data['email'].split('@', 1)[0], User.objects.count())
        super().clean()
        return self.cleaned_data

    def clean_email(self):
        email = self.cleaned_data['email']
        if UserInCampaign.objects.filter(userprofile__user__email=email).exists():
            user = UserInCampaign.objects.get(userprofile__user__email=email)
            autocom.check(users=UserInCampaign.objects.filter(pk=user.pk), action='resend-data')
            raise ValidationError(_(
                "Oops! This email address is already registered in our Auto*Mat support club, you are not registering for the first time."
                " We respect your inclination, but your registration is not need to repeat..."
                " All info you need has been sent to your email."))
        return email

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username')
        required = ('first_name', 'last_name', 'email')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.Meta.required:
            self.fields[field].required = True


class RegularUserForm_UserProfile(forms.ModelForm):
    required_css_class = 'required'

    telephone = forms.CharField(
        label=_(u"Telefon"),
        validators=[RegexValidator(r'^[0-9+ ]*$', _('Telephone must consist of numbers, spaces and plus sign')), MinLengthValidator(9)],
        max_length=30)

    class Meta:
        model = UserProfile
        fields = ('telephone',)
        required = ('telephone',)


class RegularUserForm_UserInCampaign(forms.ModelForm):
    required_css_class = 'required'

    regular_frequency = forms.ChoiceField(label=_("Regular payments"), choices=UserInCampaign.REGULAR_PAYMENT_FREQUENCIES, required=True, widget=forms.RadioSelect())
    regular_amount = forms.IntegerField(
        label=_("Regularly (amount)"),
        help_text=_(u"Minimum yearly payment is 1800 Kč"),
        min_value=1,
        )

    class Meta:
        model = UserInCampaign
        fields = ('regular_frequency', 'regular_amount')


class RegularUserForm(MultiModelForm):
    required_css_class = 'required'
    base_fields = {}
    form_classes = OrderedDict([
        ('user', RegularUserForm_User),
        ('userprofile', RegularUserForm_UserProfile),
        ('userincampaign', RegularUserForm_UserInCampaign),
    ])


class RegularUserFormWithProfile(RegularUserForm):
    pass


class RegularUserFormDPNK(RegularUserFormWithProfile):
    profile_text = forms.CharField(
        label=_("What is your reason (will be used on nakrmteautomat.cz page)?"),
        help_text=_("Tell others why you support Auto*Mat"),
        max_length=3000,
        widget=forms.Textarea,
        required=False,
    )


def generate_variable_symbol():
    now = datetime.datetime.now()
    reg_n_today = len(UserInCampaign.objects.filter(
        registered_support__gt=(
            now-datetime.timedelta(days=1))))
    for i in range(reg_n_today+1, 299):
        variable_symbol = '%s%02d%02d%03d' % (
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
    new_user = new_user_objects['user']
    new_user_profile = new_user_objects['userprofile']
    new_user_in_campaign = new_user_objects['userincampaign']
    new_user_in_campaign.regular_payments = regular
    new_user_in_campaign.variable_symbol = variable_symbol
    new_user_in_campaign.source = Source.objects.get(slug=source_slug)
    # Save new user instance
    new_user.save()
    new_user_profile.user = new_user
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

    def get_initial(self):
        initial = super().get_initial()
        initial_user = {}
        initial_userprofile = {}
        if self.request.GET.get('firstname'):
            initial_user['first_name'] = self.request.GET.get('firstname')
        if self.request.GET.get('surname'):
            initial_user['last_name'] = self.request.GET.get('surname')
        if self.request.GET.get('email'):
            initial_user['email'] = self.request.GET.get('email')
        if self.request.GET.get('telephone'):
            initial_userprofile['telephone'] = self.request.GET.get('telephone')
        initial['user'] = initial_user
        initial['userprofile'] = initial_userprofile
        return initial

    def form_valid(self, form):
        user_id = new_user(form, regular="promise", source_slug=self.source_slug)
        amount = UserInCampaign.objects.get(id=user_id).monthly_regular_amount()
        return render_to_response(self.success_template, {
            'amount': amount,
            'user_id': user_id,
            })


def donators(request):
    payed = Payment.objects.exclude(type='expected').values_list('user_id', flat=True)
    donators = UserInCampaign.objects.filter(userprofile__public=True, id__in=payed).order_by('userprofile__user__last_name')
    n_donators = len(donators)
    n_regular = len(donators.filter(userprofile__user__is_active=True, regular_payments="regular"))
    return render_to_response('donators.html', {
        'n_donators': n_donators,
        'n_regular': n_regular,
        'donators': donators})


class OneTimePaymentWizardFormBase(forms.Form):
    required_css_class = 'required'
    first_name = forms.CharField(label=_("First name"), max_length=40, required=True)
    last_name = forms.CharField(label=_("Surname"), max_length=40, required=True)
    email = forms.CharField(label=_("Email"), max_length=40, required=True)
    amount = forms.IntegerField(label=_("Amount"), required=True)


class OneTimePaymentWizardFormWhoIs(forms.Form):
    required_css_class = 'required'
    uid = forms.CharField(label=_("Account"))


class OneTimePaymentWizardFormConfirm(forms.Form):
    required_css_class = 'required'
    # Type in variable symbol for verification (sent by mail)
    vs_check = forms.CharField(
        label=_("Variable symbol"),
        max_length=40, required=False)


class OneTimePaymentWizardFormKnown(forms.Form):
    required_css_class = 'required'
    note = forms.CharField(max_length=40)


class OneTimePaymentWizardFormUnknown_UserInCampaign(forms.ModelForm):
    required_css_class = 'required'

    class Meta:
        model = UserInCampaign
        fields = ('note', 'wished_tax_confirmation', 'wished_information',)


class OneTimePaymentWizardFormUnknown_UserProfile(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = (
            'title_before', 'title_after',
            'street', 'city', 'country', 'zip_code',
            'language', 'telephone',
            'public', 'note'
        )
        required = (
            'street', 'city', 'country', 'zip_code',
            'language', 'telephone')
        widgets = {
            'language': forms.RadioSelect,  # should be set automatically
        }


class OneTimePaymentWizardFormUnknown_User(forms.ModelForm):
    username = forms.CharField(widget=forms.HiddenInput, required=False)

    def clean_username(self):
        "This function is required to overwrite an inherited username clean"
        return self.cleaned_data['username']

    def clean(self):
        if not self.errors:
            self.cleaned_data['username'] = '%s%s' % (self.cleaned_data['email'].split('@', 1)[0], User.objects.count())
        super().clean()
        return self.cleaned_data

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'email', 'username')
        required = ('first_name', 'last_name', 'email')


class OneTimePaymentWizardFormUnknown(MultiModelForm):
    base_fields = {}
    form_classes = {
        'user': OneTimePaymentWizardFormUnknown_User,
        'userprofile': OneTimePaymentWizardFormUnknown_UserProfile,
        'userincampaign': OneTimePaymentWizardFormUnknown_UserInCampaign,
    }


class OneTimePaymentWizard(SessionWizardView):
    success_template = 'thanks.html'

    def is_possibly_known(self):
        f = self._step_data(OneTimePaymentWizardFormBase)
        if f:
            return len(self._find_matching_users(f['email'], f['first_name'], f['last_name'])) > 0
        return True

    def is_unknown(self):
        return not self.is_possibly_known()

    def is_unknown_after_whois(self):
        u = self._step_data(OneTimePaymentWizardFormUnknown)
        f = self._step_data(OneTimePaymentWizardFormWhoIs)
        if u:
            return False
        elif f:
            return f['uid'] == 'None'
        else:
            return True

    def is_unknown_after_confirm(self):
        u = self._step_data(OneTimePaymentWizardFormUnknown)
        w = self._step_data(OneTimePaymentWizardFormWhoIs)
        c = self._step_data(OneTimePaymentWizardFormConfirm)
        if u:
            return False
        elif w and c:
            return c['vs_check'] != UserInCampaign.objects.filter(id=w['uid'])[0].variable_symbol
        else:
            return True

    FORMS = [['0', OneTimePaymentWizardFormBase, True, 'onetime_base.html'],
             ['1', OneTimePaymentWizardFormUnknown, is_unknown, 'onetime_unknown.html'],
             ['2', OneTimePaymentWizardFormWhoIs, is_possibly_known, 'onetime_whois.html'],
             ['3', OneTimePaymentWizardFormUnknown, is_unknown_after_whois, 'onetime_unknown.html'],
             ['4', OneTimePaymentWizardFormConfirm, is_possibly_known, 'onetime_confirm.html'],
             ['5', OneTimePaymentWizardFormUnknown, is_unknown_after_confirm, 'onetime_unknown.html']]

    def _step_number(self, form):
        for e in self.FORMS:
            if e[1] == form or isinstance(form, e[1]):
                return e[0]
        else:
            raise ValueError(("No such form as requested", form))

    def _step_data(self, form):
        stepn = self._step_number(form)
        try:
            return self.get_cleaned_data_for_step(stepn)
        except TypeError:
            return None

    def get_template_names(self):
        return self.FORMS[int(self.steps.current)][3]

    def done(self, form_list, form_dict, **kwargs):
        for form in form_list:
                if isinstance(form, OneTimePaymentWizardFormUnknown):
                        uid = new_user(form, "onetime")
                elif isinstance(form, OneTimePaymentWizardFormWhoIs):
                        uid = form.cleaned_data['uid']
        user = UserInCampaign.objects.filter(id=uid)[0]
        payment = Payment(date=datetime.datetime.now(),
                          amount=form_dict['0'].cleaned_data['amount'],
                          VS=user.variable_symbol,
                          type='expected',
                          user=user)
        payment.save()
        return render_to_response(self.success_template, {
            'amount': payment.amount,
            'user_id': user.id,
            })

    def send_vs_reminder(self, id):
        user = UserInCampaign.objects.filter(id=id)[0]
        mail_subject = _(
            "Auto*Mat: Reminder of variable symbol")
        mail_body = _(
            "Dear friend,\n\n"
            "if it is you who was just trying to let us know about his\n"
            "planned donation to us, thank you very much and for your\n"
            "convenience, here is your variable symbol:\n\n"
            "                %s\n\n"
            "If you do not know what this mean, it is possible that\n"
            "sombody else has entered your name into our system. In such\n"
            "a case, you can safely ignore this email, nothing will happen\n"
            "without your authorization, or if you receive it repeatedly,\n"
            "you can contact us on kp@auto-mat.cz.\n\n"
            "Best Regards,\n"
            "Auto*Mat\n" % user.variable_symbol)
        EmailMessage(subject=mail_subject, body=mail_body,
                     from_email='kp@auto-mat.cz', to=[user.userprofile.user.email]).send()

    def _find_matching_users(self, email, firstname, surname):
        users = (set(UserInCampaign.objects.filter(userprofile__user__email=email, userprofile__user__is_active=True).all()) |
                 set(UserInCampaign.objects.filter(userprofile__user__first_name=firstname, userprofile__user__last_name=surname, userprofile__user__is_active=True)))
        return list(users)

    def get_form(self, step=None, data=None, files=None):
        form = super().get_form(step, data, files)
        if step == self._step_number(OneTimePaymentWizardFormUnknown):
                cd0 = self._step_data(OneTimePaymentWizardFormBase)
                if cd0:
                        for f in ['first_name', 'last_name', 'email']:
                                form.forms['user'].fields .initial = cd0[f]
        elif step == self._step_number(OneTimePaymentWizardFormWhoIs):
                def obfuscate(email):
                        m = re.match('(?P<b1>.).*(?P<b2>.)@(?P<a>.).*\.(?P<d>.+)', email)
                        return m and ("%s***%s@%s***.%s" % m.groups()) or ""
                cd0 = self._step_data(OneTimePaymentWizardFormBase)
                if cd0:
                        users = self._find_matching_users(*[cd0[key] for key in [
                            'email', 'first_name', 'last_name']])
                        candidates = (
                            [
                                (
                                    u.id,
                                    "%s %s <%s>" % (u.userprofile.user.first_name, u.userprofile.user.last_name, obfuscate(u.userprofile.user.email))
                                ) for u in users
                            ] +
                            [('None', _("None of these accounts"))])
                        form.fields['uid'] = forms.ChoiceField(choices=candidates)
        elif step == self._step_number(OneTimePaymentWizardFormConfirm):
                d2 = self._step_data(OneTimePaymentWizardFormWhoIs)
                if d2['uid'] != 'None':
                        self.send_vs_reminder(d2['uid'])
        return form


def onetime(request):
    forms = OneTimePaymentWizard.FORMS
    cw = OneTimePaymentWizard.as_view(
        [form[1] for form in forms],
        condition_dict=dict([(form[0], form[2]) for form in forms]))
    return cw(request)


def stat_members(request):
    return render_to_response('stat-members.html',
                              {'members_by_months': StatMemberCountsByMonths.objects.all(),
                               'total_members': UserInCampaign.objects.all().filter(userprofile__user__is_active=True).aggregate(Count('id'))['id__count']
                               })


def stat_payments(request):
    return render_to_response('stat-payments.html',
                              {'payments_by_months': StatPaymentsByMonths.objects.all(),
                               'total_amount': Payment.objects.all().filter(~Q(type='expected')).aggregate(Sum('amount'))['amount__sum']
                               })

    return render_to_response(
        'stat-finance.html',
        RequestContext(request, {}),)


def profiles(request):
    from_date = request.GET.get('from') or '1970-1-1'
    paying = request.GET.get('paying')

    users = (
        UserInCampaign.objects.filter(registered_support__gte=from_date).order_by('-registered_support') |
        UserInCampaign.objects.filter(id__in=(493, 89, 98, 921, 33, 886, 1181, 842, 954, 25))).exclude(
            userprofile__public=False, userprofile__profile_picture__isnull=False)

    result = [{'firstname': u.userprofile.public and u.userprofile.user.first_name or '',
               'surname': u.userprofile.public and u.userprofile.user.last_name or '',
               'text': u.userprofile.profile_text or '',
               'picture': u.userprofile.profile_picture and u.userprofile.profile_picture.url or '',
               'picture_thumbnail': u.userprofile.profile_picture and u.userprofile.profile_picture.thumbnail.url or '',
               }
              for u in users
              if ((not paying) or (u.payment_total > 0))]
    return http.HttpResponse(json.dumps(result), content_type='application/json')


class CampaignStatistics(View):
    @method_decorator(never_cache)
    @method_decorator(cache_page(24 * 60))  # cache in memcached for 1h
    def dispatch(self, request, *args, **kwargs):
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        campaign = get_object_or_404(Campaign, slug=kwargs['campaign_slug'], allow_statistics=True)
        return http.HttpResponse(json.dumps({
            'expected-yearly-income': campaign.expected_yearly_income(),
            'total-income': campaign.yield_total(),
            'number-of-onetime-members': campaign.number_of_onetime_members(),
            'number-of-regular-members': campaign.number_of_regular_members(),
            'number-of-active-members': campaign.number_of_active_members(),
        }), content_type='application/json')
