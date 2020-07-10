# -*- coding: utf-8 -*-
# Author: Hynek Hanke <hynek.hanke@auto-mat.cz>
# Author: Petr Dlouhý <petr.dlouhy@auto-mat.cz>
#
# Copyright (C) 2010 o.s. Auto*Mat
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

"""Database models for the club management application"""
import datetime
import logging

from colorfield.fields import ColorField

from computedfields.models import ComputedFieldsModel, computed

from django.conf import settings
from django.contrib.admin.templatetags.admin_list import _boolean_icon
from django.contrib.auth.models import (
    AbstractBaseUser, AbstractUser, PermissionsMixin,
    User, UserManager,
)
from django.contrib.contenttypes.models import ContentType
from django.contrib.humanize.templatetags.humanize import intcomma
from django.core.files.storage import FileSystemStorage
from django.core.validators import MaxValueValidator, MinValueValidator, RegexValidator, ValidationError
from django.db import models, transaction
from django.db.models import Count, Q, Sum, signals
from django.dispatch import receiver
from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html, format_html_join, mark_safe
from django.utils.text import format_lazy
from django.utils.timesince import timesince
from django.utils.translation import ugettext_lazy as _

from polymorphic.managers import PolymorphicManager
from polymorphic.models import PolymorphicModel, PolymorphicTypeUndefined

from smmapdfs.model_abcs import PdfSandwichABC, PdfSandwichFieldABC

import stdimage

from stdnumfield.models import StdNumField

from vokativ import vokativ

from . import autocom
from .parse_account_statements import ParseAccountStatement
from .utils import WithAdminUrl, create_model

logger = logging.getLogger(__name__)

COMMUNICATION_METHOD = (
    ('email', _("Email")),
    ('phonecall', _("Phonecall")),
    ('mail', _("Mail")),
    ('personal', _("Personal")),
    ('internal', _("Internal")),
)


class CustomUserManager(PolymorphicManager, UserManager):

    def create_user(self, email, password, **extra_fields):
        if extra_fields.get('polymorphic_ctype_id', None):
            ctype_id = extra_fields.pop('polymorphic_ctype_id')
            model = ContentType.objects.get(id=ctype_id).model_class()
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        email = ProfileEmail(
            email=email,
            is_primary=True,
            user=user,
        )
        email.save()

        return user

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        if extra_fields.get('is_staff') is not True:
            raise ValueError(_('Superuser must have is_staff=True.'))
        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_('Superuser must have is_superuser=True.'))

        return self.create_user(email, password, **extra_fields)


def get_full_name(self):
    """ Sometimes can return parent model 'Profile' """
    try:
        return self.first_name + ' ' + self.last_name
    except AttributeError:
        return self.userprofile.first_name + ' ' + self.userprofile.last_name


def get_profile_abstract_base_user_model_attrs():
    attrs = {}
    for field in AbstractUser._meta.fields:
        if field.name not in ['first_name', 'last_name', 'last_login']:
            attrs[field.name] = field
    attrs['USERNAME_FIELD'] = 'username'
    attrs['get_full_name'] = get_full_name
    return attrs


AbstractProfileBaseUser = create_model(
    name='AbstractProfileBaseUser',
    fields=get_profile_abstract_base_user_model_attrs(),
    app_label='aklub',
    module='',
    options={'abstract': True},
    parent_class=(
        AbstractBaseUser,
        PermissionsMixin,
        models.Model,
    ),
)


def get_abstract_user_profile_model_attrs():
    attrs = {}
    for field in AbstractUser._meta.fields:
        if field.name in ['first_name', 'last_name']:
            attrs[field.name] = field

    return attrs


AbstractUserProfile = create_model(
    name='AbstractUserProfile',
    fields=get_abstract_user_profile_model_attrs(),
    app_label='aklub',
    module='',
    options={'abstract': True},
)


ICO_ERROR_MESSAGE = _("IČO není zadáno ve správném formátu. Zkontrolujte že číslo má osm číslic a případně ho doplňte nulami zleva.")


class AdministrativeUnit(models.Model, ParseAccountStatement):
    name = models.CharField(
        verbose_name=_("Name"),
        max_length=255,
        blank=False,
        null=False,
    )
    ico = StdNumField(
        'cz.dic',
        default=None,
        verbose_name=_(u"IČO"),
        validators=[RegexValidator(r'^[0-9]*$', _('IČO musí být číslo'))],
        error_messages={'stdnum_format': ICO_ERROR_MESSAGE},
        blank=True,
        null=True,
    )
    from_email_address = models.EmailField(
        verbose_name=_("E-mail from address"),
        help_text=_("Every new address has to be set up by system administrator"),
        default="kp@auto-mat.cz",
        blank=False,
        null=False,
    )
    from_email_str = models.CharField(
        verbose_name=_("E-mail from identifier"),
        default='Klub pratel Auto*Matu <kp@auto-mat.cz>',
        max_length=255,
        blank=False,
        null=False,
    )

    color = ColorField(
        default='#000000',
        help_text=_("Choose color to help discern Administrative unit in app"),
    )

    def __str__(self):
        return str(self.name)


class Event(models.Model):
    """Campaign -- abstract event with description

    These events can be associated to a user."""

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")

    created = models.DateField(
        verbose_name=_("Created"),
        blank=True,
        null=True,
    )
    terminated = models.DateField(
        verbose_name=_("Terminated"),
        blank=True,
        null=True,
    )
    name = models.CharField(
        verbose_name=_("Name"),
        help_text=_("Choose some unique name for this campaign"),
        max_length=100,
    )
    variable_symbol_prefix = models.PositiveIntegerField(
        validators=[MinValueValidator(10000), MaxValueValidator(99999)],
        verbose_name=_("Variable_symbol_prefix"),
        help_text=_("Number between 10000-99999"),
        blank=True,
        null=True,
    )
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Description of this campaign"),
        max_length=3000,
        blank=True,
    )
    acquisition_campaign = models.BooleanField(
        verbose_name=_("Acquisition campaign"),
        default=False,
    )
    real_yield = models.FloatField(
        verbose_name=_("Real yield"),
        help_text=_("Use if yield differs from counted value"),
        blank=True,
        null=True,
    )
    result = models.ManyToManyField(
        'interactions.result',
        verbose_name=_("Acceptable results of communication"),
        blank=True,
    )
    slug = models.SlugField(
        verbose_name=_("Slug"),
        help_text=_("Identifier of the campaign"),
        default=None,
        max_length=100,
        unique=True,
        blank=True,
        null=True,
    )
    enable_signing_petitions = models.BooleanField(
        verbose_name=_("Enable registration through petition/mailing list forms"),
        default=False,
    )
    enable_registration = models.BooleanField(
        verbose_name=_("Enable registration through donation forms"),
        default=False,
    )
    allow_statistics = models.BooleanField(
        verbose_name=_("Allow statistics exports"),
        default=False,
    )
    email_confirmation_redirect = models.URLField(
        blank=True,
        null=True,
    )
    administrative_units = models.ManyToManyField(
        AdministrativeUnit,
        verbose_name=_("administrative units"),
    )

    def number_of_members(self):
        return self.donorpaymentchannel_set.count()

    number_of_members.short_description = _("number of members")

    def number_of_regular_members(self):
        return self.donorpaymentchannel_set.filter(regular_payments="regular", payment__amount__gt=0).distinct().count()

    def number_of_onetime_members(self):
        return self.donorpaymentchannel_set.exclude(regular_payments="regular")\
            .filter(payment__amount__gt=0).distinct().count()

    def number_of_active_members(self):
        return self.donorpaymentchannel_set.filter(payment__amount__gt=0).distinct().count()

    def number_of_all_members(self):
        return self.donorpaymentchannel_set.distinct().count()

    def number_of_confirmed_members(self):
        return self.petitionsignature_set.filter(email_confirmed=True).distinct().count()

    def recruiters(self):
        return Recruiter.objects.filter(campaigns=self)

    recruiters.short_description = _("recruiters")

    def number_of_recruiters(self):
        return len(self.recruiters())

    number_of_recruiters.short_description = _("number of recruiters")

    def yield_total(self):
        if self.acquisition_campaign:
            return DonorPaymentChannel.objects.filter(event=self).aggregate(yield_total=Sum('payment__amount'))[
                'yield_total']
        else:
            return self.real_yield

    yield_total.short_description = _("total yield")

    def expected_yearly_income(self):
        income = 0
        for campaign_member in DonorPaymentChannel.objects.filter(event=self, payment__amount__gt=0).distinct():
            # TODO: use aggregate to count this
            income += campaign_member.yearly_regular_amount()
        return income

    expected_yearly_income.short_description = _("expected yearly income")

    def expected_monthly_income(self):
        return float(self.expected_yearly_income()) / 12.0

    expected_monthly_income.short_description = _("expected monthly income")

    def return_of_investmensts(self):
        if self.total_expenses() and self.expected_monthly_income():
            return self.total_expenses() / self.expected_monthly_income()

    return_of_investmensts.short_description = _("return of investmensts")

    def total_expenses(self):
        return self.expenses.aggregate(Sum('amount'))['amount__sum']

    total_expenses.short_description = _("total expenses")

    def average_expense(self):
        if self.total_expenses() and self.number_of_members():
            return self.total_expenses() / self.number_of_members()

    average_expense.short_description = _("average expense")

    def average_yield(self):
        if self.yield_total() and self.number_of_members():
            return self.yield_total() / self.number_of_members()

    average_yield.short_description = _("average yield")

    def __str__(self):
        return str(self.name)


class Expense(models.Model):
    """Expense in campaign"""

    class Meta:
        verbose_name = _("expense")
        verbose_name_plural = _("expenses")

    amount = models.FloatField(
        verbose_name=_("amount"),
        blank=False,
        null=False,
    )
    item = models.CharField(
        verbose_name=_("item"),
        max_length=300,
        blank=True,
    )
    campaign = models.ForeignKey(
        Event,
        verbose_name=_("campaign"),
        related_name='expenses',
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )


class Recruiter(models.Model):
    """Recruiter -- person that recruits new club members"""

    class Meta:
        verbose_name = _("Recruiter")
        verbose_name_plural = _("Recruiters")

    registered = models.DateField(
        verbose_name=_("Registered"),
        default=timezone.now,
    )
    recruiter_id = models.PositiveIntegerField(
        verbose_name=_("Recruiter ID"),
        blank=False,
        unique=True,
    )
    firstname = models.CharField(
        verbose_name=_("First name"),
        max_length=40,
        blank=False,
    )
    surname = models.CharField(
        verbose_name=_("Surname"),
        max_length=40,
        blank=False,
    )
    email = models.CharField(
        verbose_name=_("Email"),
        max_length=40,
        blank=True,
    )
    telephone = models.CharField(
        verbose_name=_("Telephone"),
        max_length=30,
        blank=True,
    )
    note = models.TextField(
        verbose_name=_("Note"),
        max_length=3000,
        blank=True,
    )
    problem = models.BooleanField(
        verbose_name=_("Problem"),
        help_text=_("Check this field if there is a problem with this recruiter which "
                    "only be resolved later or by somebody else. Uncheck as soon as the problem is "
                    "resolved. If the problem is of permanent nature and no further action "
                    "is needed, leave it unchecked and lower the rating bellow accordingly."),
        default=False,
    )
    rating = models.IntegerField(
        verbose_name=_("Rating"),
        help_text=_("5 = ordinary (modestly good), 0 = hopelessly bad "
                    "10 = excelent much above average"),
        choices=[(i, str(i)) for i in range(0, 11)],
        default=5,
        blank=False,
    )
    campaigns = models.ManyToManyField(
        Event,
        help_text=_("Associated campaigns"),
        blank=True,
        editable=True,
    )

    def __str__(self):
        return str(self.person_name())

    def person_name(self):
        return "%03d %s %s" % (self.recruiter_id or 0, self.firstname, self.surname)

    person_name.short_description = _("Name")


class Source(models.Model):
    """How did he contact us / became a member?"""

    class Meta:
        verbose_name = _("Source")
        verbose_name_plural = _("Sources")

    slug = models.SlugField(
        verbose_name=_("Slug"),
        help_text=_("Identifier of the source"),
        max_length=100,
        blank=False,
    )
    name = models.CharField(
        verbose_name=_("Name"),
        help_text=_("Name of the source"),
        max_length=100,
        blank=False,
    )
    direct_dialogue = models.BooleanField(
        verbose_name=_("Is from Direct Dialogue"),
        default=False,
    )

    def __str__(self):
        return str(self.name)


class Profile(PolymorphicModel, AbstractProfileBaseUser):
    class Meta:
        verbose_name = _("Profile")
        verbose_name_plural = _("Profiles")

        permissions = (
            ('can_edit_all_units', _('Může editovat všechno ve všech administrativních jednotkách')),
            ('can_remove_contact_from_administrative_unit', _('Can remove contact from his administrative unit')),
        )
    objects = CustomUserManager()
    REQUIRED_FIELDS = ['email', 'polymorphic_ctype_id']
    GENDER = (
        ('male', _('Male')),
        ('female', _('Female')),
        ('unknown', _('Unknown')))
    LANGUAGE = (
        # TODO: List of languages used in the club should come from app settings
        ('cs', _('Czech')),
        ('en', _('English')))
    username = models.CharField(
        _('user name'),
        max_length=150,
        blank=True,
        null=True,
        unique=True,
    )
    password = models.CharField(
        _('password'),
        max_length=128,
        blank=True,
        null=True,
    )
    email = models.EmailField(
        _('email address'),
        blank=True,
        null=True,
    )
    campaigns = models.ManyToManyField(
        Event,
        help_text=_("Associated campaigns"),
        blank=True,
        editable=True,
    )

    addressment = models.CharField(
        verbose_name=_("Addressment in letter"),
        max_length=40, blank=True,
    )
    addressment_on_envelope = models.CharField(
        verbose_name=_("Addressment on envelope"),
        max_length=40, blank=True,
    )
    language = models.CharField(
        verbose_name=_("Language"),
        help_text=_("This is the language which will be used to "
                    "communicate with this user. The system will send "
                    "emails in this language and administrators will use "
                    "this language in phone calls and personal contacts."),
        choices=LANGUAGE,
        default="cs",
        max_length=50,
    )

    street = models.CharField(
        verbose_name=_("Street and number"),
        max_length=80,
        blank=True,
    )
    city = models.CharField(
        verbose_name=_("City/City part"),
        max_length=40, blank=True,
    )
    country = models.CharField(
        verbose_name=_("Country"),
        # TODO: Default country should come from app settings
        default=u"Česká republika",
        max_length=40,
        blank=True,
    )
    zip_code = models.CharField(
        verbose_name=_("ZIP Code"),
        max_length=30,
        blank=True,
    )
    different_correspondence_address = models.BooleanField(
        verbose_name=_("Different correspondence address"),
        help_text=_("User has different correspondence address"),
        default=False,
    )

    correspondence_street = models.CharField(
        verbose_name=_("Street and number"),
        max_length=80,
        blank=True,
    )
    correspondence_city = models.CharField(
        verbose_name=_("City/City part"),
        max_length=40, blank=True,
    )
    correspondence_country = models.CharField(
        verbose_name=_("Country"),
        # TODO: Default country should come from app settings
        default=u"Česká republika",
        max_length=40,
        blank=True,
    )
    correspondence_zip_code = models.CharField(
        verbose_name=_("ZIP Code"),
        max_length=30,
        blank=True,
    )

    other_support = models.TextField(
        verbose_name=_("Other support"),
        help_text=_(
            "If the user supports us in other ways, please specify here."),
        max_length=500,
        blank=True,
    )
    profile_text = models.TextField(
        verbose_name=_("What is your reason?"),
        help_text=_("Tell others why you support Auto*Mat"),
        max_length=3000,
        blank=True,
        null=True,
    )
    profile_picture = stdimage.StdImageField(
        verbose_name=_("Profile picture"),
        help_text=_("Your profile picture, which others will see."),
        upload_to='profile-images',
        variations={
            'thumbnail': (150, 150, True),
        },
        blank=True,
        null=True,
    )

    # Benefits
    club_card_available = models.BooleanField(
        verbose_name=_("Club card available"),
        default=False, help_text=_("Is he entitled to posses a club card?"),
    )
    club_card_dispatched = models.BooleanField(
        verbose_name=_("Club card dispatched?"),
        help_text=_("Did we send him the club card already?"),
        default=False,
    )
    other_benefits = models.TextField(
        verbose_name=_("Other benefits"),
        help_text=_("Did he receive some other benefits?"),
        max_length=500,
        blank=True,
    )
    # -- Notes (club administrators private notes)
    note = models.TextField(
        verbose_name=_("Note for making a boring form more lively"),
        max_length=2000,
        blank=True,
    )
    created = models.DateTimeField(
        verbose_name=_("Date of creation"),
        auto_now_add=True,
        null=True,
    )
    updated = models.DateTimeField(
        verbose_name=_("Date of last change"),
        auto_now=True,
        null=True,
    )
    administrative_units = models.ManyToManyField(
        AdministrativeUnit,
        verbose_name=_("administrative units"),
        blank=True,
    )
    administrated_units = models.ManyToManyField(
        AdministrativeUnit,
        verbose_name=_("administrated units"),
        related_name='administrators',
        blank=True,
    )

    """
    next_communication_date = models.DateField(
        verbose_name=_("Date of next communication"),
        blank=True,
        null=True,
    )
    """

    def get_last_name_vokativ(self):
        if hasattr(self, 'last_name'):
            return vokativ(self.last_name.strip(), last_name=True).title()
        else:
            if hasattr(self, 'name'):
                if self.name:
                    return vokativ(self.name.strip(), last_name=False).title()
        return None

    get_last_name_vokativ.short_description = _("Last name vokativ")
    get_last_name_vokativ.admin_order_field = 'last_name'

    def get_addressment(self):
        if self.addressment:
            return self.addressment
        if hasattr(self, 'first_name'):
            if self.first_name:
                return vokativ(self.first_name.strip()).title()
        if self.language == 'cs':
            if hasattr(self, 'sex'):
                if self.sex == 'male':
                    return 'příteli Auto*Matu'
                elif self.sex == 'female':
                    return 'přítelkyně Auto*Matu'
                else:
                    return 'příteli/kyně Auto*Matu'
            else:
                return 'Company'
        else:
            return 'Auto*Mat friend'

    get_addressment.short_description = _("Addressment")
    get_addressment.admin_order_field = 'addressment'

    def get_email_str(self):
        try:
            return self.profileemail_set.get(is_primary=True).email
        except ProfileEmail.DoesNotExist:
            return ""

    def mail_communications_count(self):
        return self.interaction_set.filter(type__send_email=True, dispatched=True).count()

    def person_name(self):
        try:
            profile = self.get_real_instance()
        except PolymorphicTypeUndefined:
            profile = self
        if hasattr(profile, 'title_before'):
            if profile.first_name or profile.last_name:
                return " ".join(
                    filter(
                        None,
                        [
                            profile.title_before,
                            profile.last_name,
                            profile.first_name,
                        ],
                    ),
                ) + (", %s" % profile.title_after if profile.title_after else "")
        elif hasattr(profile, 'name') and profile.name:
            return profile.name
        return profile.username

    person_name.short_description = _("Full name")
    person_name.admin_order_field = 'last_name'

    def userattendance_links(self):
        from .admin import admin_links
        return admin_links(
            [
                (
                    reverse('admin:aklub_userincampaign_change', args=(u.pk,)), str(u.campaign)
                ) for u in self.userincampaign_set.all()
            ]
        )

    userattendance_links.short_description = _('Users in campaign')

    def make_tax_confirmation(self, year, unit, pdf_type):
        payment_set = Payment.objects.filter(
                            user_donor_payment_channel__user=self,
                            user_donor_payment_channel__money_account__administrative_unit=unit,
                            )
        amount = payment_set.exclude(type='expected').filter(date__year=year).aggregate(Sum('amount'))['amount__sum']
        if not amount:
            return None, False
        confirm, created = TaxConfirmation.objects.update_or_create(
            user_profile=self,
            year=year,
            pdf_type=pdf_type,
            defaults={
                'amount': amount,
            },
        )
        return confirm, created

    def __str__(self):
        return str(self.person_name())

    def clean(self):
        if self.email:
            self.email = self.email.lower()
        if self.email == "":
            self.email = None

    def save(self, *args, **kwargs):
        self.clean()
        if not self.username and not self.id:
            from .views import get_unique_username
            self.username = get_unique_username(self.email)
        super().save(*args, **kwargs)

    def get_telephone(self):
        numbers = ','.join(number.telephone for number in self.telephone_set.all())
        return numbers

    def get_donor(self):
        donors = ','.join(donor.VS for donor in self.userchannels.all() if donor.VS is not None)
        return donors

    def get_main_telephone(self):
        active_numbers = self.telephone_set.all()
        numbers = list(map(lambda number: number.create_link(), active_numbers))
        return mark_safe('\n'.join(numbers))

    get_main_telephone.short_description = _("Telephone")
    get_main_telephone.admin_order_field = "telephone"

    def get_details(self, obj, attr, *args):
        return format_html_join(mark_safe('<br/>'), "{}", ((f[attr],) for f in list(obj.values(attr)) if f[attr] is not None))

    def format_list(self, values_list):
        return format_html_join(mark_safe('<br/>'), "{}", (values_list))

    def date_format(self, obj):
        return list(map(lambda o: (o[0].strftime('%d. %m. %Y'),), obj))

    def regular_payments_info(self):
        return self.format_list(self.userchannels.values_list("regular_payments"))

    regular_payments_info.short_description = _("Regular payment info")
    regular_payments_info.admin_order_field = 'userchannels'

    def regular_amount(self):
        return self.format_list(self.userchannels.values_list("regular_amount"))

    regular_amount.short_description = _("Regular amount")
    regular_amount.admin_order_field = 'userchannels'

    def registered_support_date(self):
        result = self.userchannels.values_list("registered_support")
        return self.format_list(self.date_format(result))

    registered_support_date.short_description = _("Registration")
    registered_support_date.admin_order_field = 'registered_support'

    def variable_symbol(self):
        return self.get_details(self.userchannels.all(), "VS")

    variable_symbol.short_description = _("VS")
    variable_symbol.admin_order_field = 'variable_symbol'

    def get_administrative_units(self):
        administrative_units = ', '.join(administrative_unit.name for administrative_unit in self.administrative_units.all())
        return administrative_units

    def can_administer_profile(self, profile):
        if self.has_perm('aklub.can_edit_all_units'):
            return True
        administrated_unit_pks = {unit.pk for unit in self.administrated_units.all()}
        administrative_unit_pks = {unit.pk for unit in profile.administrative_units.all()}
        if administrated_unit_pks.intersection(administrative_unit_pks):
            return True
        else:
            return False

    def get_email(self):
        emails = self.profileemail_set.all()
        result = list(
            map(
                lambda email:
                format_html('<b>{}</b>'.format(email.email))
                if email.is_primary
                else
                format_html('{}'.format(email.email)),
                emails,
            ),
        )
        result.sort(key=lambda item: -1 if '<b>' in item else 0)

        return mark_safe('\n'.join(result))

    get_email.short_description = _("Email")
    get_email.admin_order_field = "email"


class CompanyProfile(Profile):
    class Meta:
        verbose_name = _("Company profile")
        verbose_name_plural = _("Company profiles")

    name = models.CharField(
        verbose_name=_("Company name"),
        max_length=180,
        blank=True,
        null=True,
    )

    contact_first_name = models.CharField(
        verbose_name=_("Contact first name"),
        max_length=256,
        blank=True,
        null=True,
    )
    contact_last_name = models.CharField(
        verbose_name=_("Contact last name"),
        max_length=256,
        blank=True,
        null=True,
    )
    crn = StdNumField(
        'cz.dic',
        default=None,
        verbose_name=_(u"IČO"),
        validators=[RegexValidator(r'^[0-9]*$', _('IČO musí být číslo'))],
        error_messages={'stdnum_format': ICO_ERROR_MESSAGE},
        help_text=_("only for Czech companies"),
        blank=True,
        null=True,
    )

    tin = StdNumField(
        'eu.vat',
        default=None,
        verbose_name=_(u"DIČ"),
        help_text=_("Czech and European companies, must be in valid formate"),
        blank=True,
        null=True,
    )

    def full_contact_name(self):
        """Return complete name"""
        if self.contact_first_name and self.contact_last_name:
            return f'{self.contact_first_name} {self.contact_last_name}'

    full_contact_name.short_description = _("Contact name")
    full_contact_name.admin_order_field = 'full_contact_name'


class UserProfile(Profile, AbstractUserProfile):
    class Meta:
        verbose_name = _("User profile")
        verbose_name_plural = _("User profiles")

    GENDER = (
        ('male', _('Male')),
        ('female', _('Female')),
        ('unknown', _('Unknown')))
    title_after = models.CharField(
        verbose_name=_("Title after name"),
        max_length=15,
        null=True,
        blank=True,
    )
    title_before = models.CharField(
        verbose_name=_("Title before name"),
        max_length=15,
        null=True,
        blank=True,
    )
    age_group = models.PositiveIntegerField(
        verbose_name=_("Birth year"),
        null=True,
        blank=True,
        choices=[(i, i) for i in range(datetime.date.today().year, datetime.date.today().year - 100, -1)],
    )
    birth_month = models.PositiveIntegerField(
        verbose_name=_("Month of birth"),
        null=True,
        blank=True,
        choices=[(i, i) for i in range(1, 13)],
    )
    birth_day = models.PositiveIntegerField(
        verbose_name=_("Day of birth"),
        null=True,
        blank=True,
        choices=[(i, i) for i in range(1, 32)],
    )
    sex = models.CharField(
        verbose_name=_("Gender"),
        choices=GENDER,
        max_length=50,
        default='unknown',
    )

    @classmethod
    def export_resource_classes(cls):
        from .admin import UserProfileResource
        return {
            'users': ('Users resource', UserProfileResource),
        }


class ProfileEmail(models.Model):
    class Meta:
        verbose_name = _("Email")
        verbose_name_plural = _("Emails")
        unique_together = ("user", "is_primary")

    bool_choices = (
        (None, "No"),
        (True, "Yes")
    )
    email = models.EmailField(
        _('email address'),
        blank=False,
        null=True,
    )
    is_primary = models.NullBooleanField(
        verbose_name=_("Primary email"),
        blank=True,
        default=None,
        choices=bool_choices,
    )
    note = models.CharField(
        verbose_name=_("Note"),
        max_length=70,
        blank=True,
        null=True,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if self.is_primary:
            profile = Profile.objects.get(username=self.user.username)
            profile.email = self.email
            profile.save()
        self.email = self.email.strip()
        super().save(*args, **kwargs)


def on_transaction_commit(func):
    def inner(*args, **kwargs):
        transaction.on_commit(lambda: func(*args, **kwargs))
    return inner


@receiver(signals.m2m_changed, sender=Profile.administrative_units.through)
@on_transaction_commit
def Userprofile_administrative_unit_changed(sender, **kwargs):
    # this method is always called if m2m administrative_unit is changed in profile
    def choose_if_active(status):
        if user.preference_set.count() == 0 and not user.has_perm('aklub.can_edit_all_units'):
            user.is_active = status
            user.save()

    user = kwargs['instance']
    units = kwargs['pk_set']
    action = kwargs['action']
    # dry_run is defined during importing..
    # we want to call signal only if dry_run => false or doesnt exist
    if not hasattr(user, 'dry_run') or not user.dry_run:
        if action == 'post_add':
            # if user has 0 administrative units we set him as active because he was inactive before
            choose_if_active(True)
            for unit in units:
                Preference.objects.get_or_create(
                    user=user,
                    administrative_unit_id=unit,
                )

        elif action == 'post_remove':
            user.preference_set.filter(administrative_unit__id__in=units).delete()
            # if user has 0 administrative units we set him as inactive
            choose_if_active(False)


class Preference(models.Model):
    user = models.ForeignKey(
        Profile,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    newsletter_on = models.NullBooleanField(
        verbose_name=_("newsletter_on"),
        null=True,
        blank=True,
        default=False,
    )
    call_on = models.NullBooleanField(
        verbose_name=_("call_on"),
        null=True,
        blank=True,
        default=False,
    )
    challenge_on = models.NullBooleanField(
        verbose_name=_("challenge_on"),
        null=True,
        blank=True,
        default=False,
    )
    letter_on = models.NullBooleanField(
        verbose_name=_("letter_on"),
        null=True,
        blank=True,
        default=False,
    )
    send_mailing_lists = models.BooleanField(
        verbose_name=_("Sending of mailing lists allowed"),
        null=True,
        default=True,
    )
    public = models.BooleanField(
        verbose_name=_("Publish my name in the list of supporters"),
        null=True,
        default=True,
    )

    administrative_unit = models.ForeignKey(
        AdministrativeUnit,
        verbose_name=_("administrative unit"),
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )

    def __str__(self):
        return self.administrative_unit.name if self.administrative_unit else ''


class Telephone(models.Model):
    bool_choices = (
        (None, "No"),
        (True, "Yes")
    )

    telephone = models.CharField(
        verbose_name=_("Telephone number"),
        max_length=100,
        blank=True,
        validators=[
            RegexValidator(
                r'^\+?(42(0|1){1})?\s?\d{3}\s?\d{3}\s?\d{3}$',
                _("Telephone must consist of numbers, spaces and + sign or maximum number count is higher."),
            ),
        ],
    )
    is_primary = models.NullBooleanField(
        verbose_name=_("Primary phone"),
        blank=True,
        default=None,
        choices=bool_choices,
    )
    note = models.CharField(
        verbose_name=_("Note"),
        help_text=_("e.g. do not call during a workweek"),
        max_length=70,
        blank=True,
    )
    user = models.ForeignKey(
        Profile,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        verbose_name = _("Telephone")
        verbose_name_plural = _("Telephones")
        unique_together = ("user", "is_primary")

    def validate_unique(self, exclude=None):
        super().validate_unique(exclude=exclude)

    def check_duplicate(self, *args, **kwargs):
        qs = Telephone.objects.filter(telephone=self.telephone, user=self.user)
        if self.pk is None:
            if qs.filter(telephone=self.telephone, user=self.user).exists():
                raise ValidationError("Duplicate phone number for this user")

    def clean(self, *args, **kwargs):
        self.check_duplicate()
        primary = Telephone.objects.filter(is_primary=True, user=self.user)
        primary.is_primary = None
        primary.user = self.user
        self.validate_unique()
        super().clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return u"%s" % self.telephone

    def format_number(self):
        if hasattr(self, "telephone") and self.telephone != "":
            removed_space_tel = self.telephone.replace(" ", "")
            if len(removed_space_tel) > 9:
                return '+' + removed_space_tel[-12:]
            else:
                return '+420' + removed_space_tel[-9:]

    def create_link(self):
        if hasattr(self, "telephone"):
            formated_telephone = self.format_number()
            if self.is_primary is True:
                return format_html("<b><a href='sip:{}'>{}</a></b>", formated_telephone, formated_telephone)
            else:
                return format_html("<a href='sip:{}'>{}</a>", formated_telephone, formated_telephone)


class UserInCampaign(models.Model):
    """
    User instance in a campaign
    """

    class Meta:
        verbose_name = _("User in campaign")
        verbose_name_plural = _("Users in campaign")
        unique_together = ('userprofile', 'campaign',)
        ordering = [
            "userprofile__userprofile__last_name",
            "userprofile__userprofile__first_name",
            "userprofile__companyprofile__name",
        ]

    GENDER = (
        ('male', _('Male')),
        ('female', _('Female')),
        ('unknown', _('Unknown')))
    REGULAR_PAYMENT_FREQUENCIES = (
        ('monthly', _('Monthly')),
        ('quaterly', _('Quaterly')),
        ('biannually', _('Bianually')),
        ('annually', _('Anually')),
        (None, _('Onetime')),
    )
    REGULAR_PAYMENT_FREQUENCIES_MAP = dict(REGULAR_PAYMENT_FREQUENCIES)
    REGULAR_PAYMENT_FREQUENCIES_MAP[''] = REGULAR_PAYMENT_FREQUENCIES_MAP[None]
    REGULAR_PAYMENT_CHOICES = (
        ('regular', _('Regular payments')),
        ('onetime', _('No regular payments')),
        ('promise', _('Promise of regular payments')),
    )
    REGULAR_PAYMENT_CHOICES_MAP = dict(REGULAR_PAYMENT_CHOICES)

    # -- Basic personal information
    userprofile = models.ForeignKey(
        Profile,
        blank=False,
        default=None,
        on_delete=models.CASCADE,
        null=False,
    )
    campaign = models.ForeignKey(
        Event,
        help_text=_("Campaign"),
        default=None,
        blank=False,
        on_delete=models.CASCADE,
        null=False,
        editable=True,
    )
    # -- Additional Info
    knows_us_from = models.CharField(
        verbose_name=_("Where does he/she know us from?"),
        max_length=80,
        blank=True,
    )
    why_supports = models.TextField(
        verbose_name=_("Why does he/she support us?"),
        max_length=500,
        blank=True,
    )
    field_of_work = models.CharField(
        verbose_name=_("Field of work"),
        help_text="His/her area of expertise and/or interest",
        max_length=80,
        blank=True,
    )
    source = models.ForeignKey(
        Source,
        verbose_name=_("Source"),
        help_text=_("How did he contact us / became a member? In direct dialog, please distinguish "
                    "between partial form (he still needs to send a permanent order into his bank) "
                    "and full form (we are going to submit his form directly into bank, no further "
                    "action is needed from him)."),
        max_length=80,
        blank=True,
        null=True,
        default=None,
        on_delete=models.SET_NULL,
    )
    additional_information = models.TextField(
        verbose_name=_("Additional information"),
        max_length=500,
        blank=True,
    )
    # -- Support
    variable_symbol = models.CharField(
        verbose_name=_("Variable symbol"),
        default="",
        unique=True,
        max_length=30,
        blank=True,
        null=False,
    )
    registered_support = models.DateTimeField(
        verbose_name=_("Registered support"),
        help_text=_("When did this user register to support us"),
        default=timezone.now,
        blank=True,
    )
    exceptional_membership = models.BooleanField(
        verbose_name=_("Exceptional membership"),
        help_text=_("In special cases, people can become members of "
                    "the club even if they do not pay any money. This should "
                    "be justified in the note."),
        default=False,
    )
    regular_payments = models.CharField(
        verbose_name=_("Regular payments"),
        help_text=_("Is this user registered for regular payments?"),
        max_length=20,
        choices=REGULAR_PAYMENT_CHOICES,
    )
    old_account = models.BooleanField(
        verbose_name=_("Old account"),
        help_text=_("User has old account"),
        default=False,
    )
    # TODO: This needs to be replaced by amount and periodicity fields to
    # account also for quaterly and annual payments
    regular_amount = models.PositiveIntegerField(
        verbose_name=_("Regularly (amount)"),
        help_text=_(u"Minimum yearly payment is 1800 Kč"),
        blank=True,
        null=True,
    )
    regular_frequency = models.CharField(
        verbose_name=_("Frequency of regular payments"),
        choices=REGULAR_PAYMENT_FREQUENCIES,
        max_length=20,
        blank=True,
        null=True,
    )
    expected_date_of_first_payment = models.DateField(
        verbose_name=_("Expected date of first payment"),
        help_text=("When should the first payment arrive on our account"),
        blank=True,
        null=True,
    )
    other_support = models.TextField(
        verbose_name=_("Other support"),
        help_text=_(
            "If the user supports us in other ways, please specify here."),
        max_length=500,
        blank=True,
    )

    # -- Notes (club administrators private notes)
    note = models.TextField(
        verbose_name=_("Note for making a boring form more lively"),
        max_length=2000,
        blank=True,
    )
    verified = models.BooleanField(
        _("Verified"),
        help_text=_("Was the the user information verified by a club administrator?"),
        default=False,
    )
    gdpr_consent = models.BooleanField(
        _("GDPR consent"),
        default=False,
    )
    verified_by = models.ForeignKey(
        Profile,
        verbose_name=_("Verified by"),
        related_name='verified_users',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    activity_points = models.IntegerField(
        verbose_name=_("Activity points"),
        help_text=_("Points for users activity"),
        default=0,
        blank=False,
    )
    updated = models.DateTimeField(
        verbose_name=_("Date of last change"),
        auto_now=True,
        null=True,
    )
    recruiter = models.ForeignKey(
        Recruiter,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    wished_tax_confirmation = models.BooleanField(
        verbose_name=_("Send tax confirmation"),
        default=True,
    )
    wished_welcome_letter = models.BooleanField(
        verbose_name=_("Send welcome letter"),
        default=True,
    )
    wished_information = models.BooleanField(
        verbose_name=_("Send regular news via email"),
        default=True,
    )
    next_communication_date = models.DateField(
        verbose_name=_("Date of next communication"),
        blank=True,
        null=True,
    )
    next_communication_method = models.CharField(
        verbose_name=_("Method of next communication"),
        max_length=30,
        choices=COMMUNICATION_METHOD,
        blank=True,
        null=True,
    )
    public = models.BooleanField(
        verbose_name=_("Publish my name in the list of supporters/petitents of this campaign"),
        default=False,
    )
    created = models.DateTimeField(
        verbose_name=_("Date of creation"),
        auto_now_add=True,
        null=True,
    )
    updated = models.DateTimeField(
        verbose_name=_("Date of last change"),
        auto_now=True,
        null=True,
    )
    email_confirmed = models.BooleanField(
        verbose_name=_("Is confirmed via e-mail"),
        default=False,
    )

    def __str__(self):
        return "%s - %s (%s)" % (
            str(self.person_name()),
            self.userprofile.email,
            self.campaign,
        )

    def person_name(self):
        try:
            return self.userprofile.__str__()
        except Profile.DoesNotExist:  # This happens, when UserInCampaign is cached, but it is deleted already
            return "No Profile"

    person_name.short_description = _("Full name")
    '''
    def requires_action(self):
        """Return true if the user requires some action from
        the club manager, otherwise return False"""
        if len(Interaction.objects.filter(user=self, dispatched=False)) > 0:
            return True
        else:
            return False
    '''
    def is_direct_dialogue(self):
        if self.source:
            return self.source.direct_dialogue
        else:
            return False

    def mail_communications_count(self):
        return self.interaction_set.filter(method="mail").count()

    def save(self, *args, **kwargs):
        """Record save hook

        Perform a check for automated communications. Since the state of this
        user was changed, a new communication might arrise from this
        situation. See module 'autocom'.
        """
        raise NotImplementedError("UserInCampaign was deprecated")
        if self.pk is None:
            insert = True
        else:
            insert = False
        super().save(*args, **kwargs)
        from .autocom import check as autocom_check
        autocom_check(users=UserProfile.objects.filter(userchannels__pk=self.pk, event=self.event), action=(insert and 'new-user' or None))


def str_to_datetime_xml(date):
    return datetime.date(
        **dict(
            zip(
                ['year', 'month', 'day'],
                [int(val) for val in date.split('-')],
            ),
        ),
    )


def str_to_datetime(date):
    if not date:
        return None
    return datetime.date(
        **dict(
            zip(
                ['day', 'month', 'year'],
                [int(val) for val in date.split('.')],
            ),
        ),
    )


class AccountStatements(ParseAccountStatement, models.Model):
    """AccountStatemt entry and DB model

    Account statements serve primarily to load data into the Payments
    table. The loaded files are then archived for later evidence.
    """

    class Meta:
        verbose_name = _("Account Statement")
        verbose_name_plural = _("Account Statements")
        ordering = ['-import_date']

    TYPE_OF_STATEMENT = (
        ('account', 'Account statement - Fio Banka'),
        ('account_cs', 'Account statement - Česká spořitelna'),
        ('account_kb', 'Account statement - Komerční Banka'),
        ('account_csob', 'Account statement - ČSOB'),
        ('account_sberbank', 'Account statement - Sberbank'),
        ('darujme', 'Darujme.cz'),
    )

    type = models.CharField(max_length=20, choices=TYPE_OF_STATEMENT)  # noqa
    import_date = models.DateTimeField(auto_now=True)
    csv_file = models.FileField(
        upload_to='account-statements',
        null=False,
        blank=False,
    )
    date_from = models.DateField(
        blank=True,
        null=True,
    )
    date_to = models.DateField(
        blank=True,
        null=True,
    )
    pair_log = models.TextField(
        verbose_name=_("Payment pairing log"),
        help_text=_("Why Payment was not paired"),
        blank=True,
    )
    administrative_unit = models.ForeignKey(
        AdministrativeUnit,
        verbose_name=_("administrative unit"),
        on_delete=models.CASCADE,
        null=True,
    )

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if hasattr(self, "payments"):
            for payment in self.payments:
                if payment:
                    payment.account_statement = self
                    payment.save()
        if self.payment_set.count() == 0:
            from .tasks import parse_account_statement
            transaction.on_commit(lambda: parse_account_statement.delay(self.pk))

    def payment_pair(self, payment):
        # Variable symbols and user bank account Payments pairing
        log_message = ""
        try:
            donor_with_bank_account = DonorPaymentChannel.objects.get(
                                user_bank_account__bank_account_number=str(payment.account) + '/' + str(payment.bank_code),
                                money_account__administrative_unit=self.administrative_unit,
            )
            payment.user_donor_payment_channel = donor_with_bank_account
            payment.save()
            return True
        except DonorPaymentChannel.DoesNotExist:
            log_message = str(_("dpch with user_bank_account doesnt_exist // "))
        except DonorPaymentChannel.MultipleObjectsReturned:
            log_message = str(_('multiple dpch with user_bank_account // '))

        if payment.VS != '':
            try:
                donor_with_vs = DonorPaymentChannel.objects.get(
                                    VS=payment.VS,
                                    money_account__administrative_unit=self.administrative_unit,
                )
                payment.user_donor_payment_channel = donor_with_vs
                payment.save()
                return True
            except DonorPaymentChannel.DoesNotExist:
                log_message = log_message + str(_("dpch with VS doesnt_exist"))
            except DonorPaymentChannel.MultipleObjectsReturned:
                log_message = log_message + str(_("multiple dpch with VS"))
        else:
            log_message = log_message + str(_("VS not set"))
        self.pair_log = f'{self.pair_log} {payment.account_name}  => {log_message}\n'
        return False

    def __str__(self):
        return "%s (%s)" % (self.pk, self.import_date)


class MoneyAccount(PolymorphicModel):
    note = models.TextField(
        verbose_name=_("Bank account note"),
        blank=True,
        null=True,
    )
    administrative_unit = models.ForeignKey(
        AdministrativeUnit,
        verbose_name=_("administrative unit"),
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )
    slug = models.SlugField(
        verbose_name=_("Slug"),
        help_text=_("Identifier of the Account"),
        default=None,
        max_length=100,
        unique=True,
        blank=True,
        null=True,
        )


class BankAccount(MoneyAccount):
    class Meta:
        verbose_name = _("Bank account")
        verbose_name_plural = _("Bank accounts")

    bank_account = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )
    bank_account_number = models.CharField(
        verbose_name=_("Bank account number"),
        max_length=50,
        blank=False,
        null=False,
    )

    def __str__(self):
        return f'{self.administrative_unit} {self.bank_account_number}'


class ApiAccount(MoneyAccount):
    project_name = models.CharField(
        verbose_name=_("Name"),
        unique=True,
        default=None,
        max_length=100,
        blank=True,
        null=True,
    )
    project_id = models.IntegerField(
        verbose_name=_("project ID"),
        default=None,
        blank=True,
        null=True,
    )
    api_id = models.IntegerField(
        verbose_name=_("API ID"),
        default=None,
        blank=True,
        null=True,
    )
    api_secret = models.CharField(
        verbose_name=_("API secret"),
        default=None,
        max_length=100,
        blank=True,
        null=True,
    )
    event = models.ForeignKey(
        Event,
        help_text=("Event"),
        verbose_name=("Event"),
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return f'{self.administrative_unit} -{self.event} - auto api'


class UserBankAccount(models.Model):
    class Meta:
        verbose_name = _("User bank account")
        verbose_name_plural = _("User bank accounts")

    bank_account = models.CharField(
        max_length=50,
        blank=True,
        null=True,
    )
    bank_account_number = models.CharField(
        verbose_name=_("Bank account number"),
        max_length=50,
        blank=False,
        null=False,
    )
    note = models.TextField(
        verbose_name=_("Bank account note"),
        blank=True,
        null=True,
    )

    def __str__(self):
        return u"%s" % (self.bank_account_number)


class DonorPaymentChannel(ComputedFieldsModel):
    class Meta:
        verbose_name = _("Donor payment channel")
        verbose_name_plural = _("Donor payment channels")
        unique_together = (
            ('VS', 'money_account'),
            ('user', 'event'),
        )

    VS = models.CharField(
        verbose_name=_("VS"),
        help_text=_("Variable symbol"),
        max_length=30,
        blank=True,
        null=True,
    )
    SS = models.CharField(
        verbose_name=_("SS"),
        help_text=_("Specific symbol"),
        max_length=30,
        blank=True,
        null=True,
    )
    user = models.ForeignKey(
        Profile,
        verbose_name=_("User"),
        on_delete=models.CASCADE,
        related_name="userchannels",
        null=False,
        blank=False,
    )
    registered_support = models.DateTimeField(
        verbose_name=_("Registered support"),
        help_text=_("When did this user register to support us"),
        default=timezone.now,
        blank=True,
    )
    REGULAR_PAYMENT_FREQUENCIES = (
        ('monthly', _('Monthly')),
        ('quaterly', _('Quaterly')),
        ('biannually', _('Bianually')),
        ('annually', _('Anually')),
        (None, _('Onetime')),
    )
    REGULAR_PAYMENT_FREQUENCIES_MAP = dict(REGULAR_PAYMENT_FREQUENCIES)
    REGULAR_PAYMENT_CHOICES = (
        ('regular', _('Regular payments')),
        ('onetime', _('No regular payments')),
        ('promise', _('Promise of regular payments')),
    )
    REGULAR_PAYMENT_CHOICES_MAP = dict(REGULAR_PAYMENT_CHOICES)

    regular_frequency = models.CharField(
        verbose_name=_("Frequency of regular payments"),
        choices=REGULAR_PAYMENT_FREQUENCIES,
        max_length=20,
        blank=True,
        null=True,
    )
    expected_date_of_first_payment = models.DateField(
        verbose_name=_("Expected date of first payment"),
        help_text=("When should the first payment arrive on our account"),
        blank=True,
        null=True,
    )
    regular_amount = models.PositiveIntegerField(
        verbose_name=_("Regularly (amount)"),
        help_text=_(u"Minimum yearly payment is 1800 Kč"),
        blank=True,
        null=True,
    )
    exceptional_membership = models.BooleanField(
        verbose_name=_("Exceptional membership"),
        help_text=_("In special cases, people can become members of "
                    "the club even if they do not pay any money. This should "
                    "be justified in the note."),
        default=False,
    )
    regular_payments = models.CharField(
        verbose_name=_("Regular payments"),
        help_text=_("Is this user registered for regular payments?"),
        max_length=20,
        choices=REGULAR_PAYMENT_CHOICES,
        default='regular',
    )
    old_account = models.BooleanField(
        verbose_name=_("Old account"),
        help_text=_("User has old account"),
        default=False,
    )
    other_support = models.TextField(
        verbose_name=_("Other support"),
        help_text=_("If the user supports us in other ways, please specify here."),
        max_length=500,
        blank=True,
    )
    money_account = models.ForeignKey(
        MoneyAccount,
        related_name='moneyaccounts',
        on_delete=models.CASCADE,
    )
    user_bank_account = models.ForeignKey(
        UserBankAccount,
        related_name='userbankaccounts',
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
    )
    event = models.ForeignKey(
        Event,
        help_text=("Event"),
        verbose_name=("Event"),
        on_delete=models.CASCADE,
        null=True,
    )
    end_of_regular_payments = models.DateField(
        verbose_name=_("End of regular payments (for payments by card)"),
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"Payment channel: {self.VS}"

    def generate_VS(self):
        if self.VS == "" or self.VS is None:
            from .views import generate_variable_symbol
            VS = generate_variable_symbol(dpch=self)
            self.VS = VS

    def requires_action(self):
        """Return true if the user requires some action from
        the club manager, otherwise return False"""
        from interactions.models import Interaction
        if len(Interaction.objects.filter(user=self.user, dispatched=False)) > 0:
            return True
        else:
            return False

    def check_duplicate(self, *args, **kwargs):
        try:
            qs = DonorPaymentChannel.objects.filter(
                                VS=self.VS,
                                money_account__administrative_unit=self.money_account.administrative_unit,
                )
            if qs:
                if qs.first().pk != self.pk:
                    raise ValidationError("Duplicate VS")
        except MoneyAccount.DoesNotExist:
            pass

    @computed(models.IntegerField(null=True), depends=['payment_set'])
    def number_of_payments(self):
        """Return number of payments made by this user
        """
        return self.payment_set.aggregate(count=Count('amount'))['count']

    number_of_payments.short_description = _("# payments")
    number_of_payments.admin_order_field = 'payments_number'

    def last_payment_function(self):
        """Return last payment"""
        return self.payment_set.order_by('date').last()

    @computed(
        models.ForeignKey(
            to='Payment',
            default=None,
            null=True,
            related_name="user_last_payment",
            on_delete=models.SET_NULL,
        ),
        depends=['payment_set'],
    )
    def last_payment(self):
        """Return last payment"""
        return self.last_payment_function()

    def last_payment_date(self):
        """Return date of last payment or None
        """
        last_payment = self.last_payment
        if last_payment:
            return last_payment.date
        else:
            return None

    last_payment_date.short_description = _("Last payment date")
    last_payment_date.admin_order_field = 'last_payment__date'

    def last_payment_amount(self):
        """Return amount of last payment or None
        """
        last_payment = self.last_payment
        if last_payment:
            return last_payment.amount
        else:
            return None

    last_payment_amount.short_description = _("Last payment amount")
    last_payment_amount.admin_order_field = 'last_payment__amount'

    def registered_support_date(self):
        return self.registered_support.strftime('%d. %m. %Y')

    registered_support_date.short_description = _("Registration")
    registered_support_date.admin_order_field = 'registered_support'

    def payment_total_range(self, from_date, to_date):
        return self.payment_set.filter(date__gte=from_date, date__lte=to_date).aggregate(sum=Sum('amount'))['sum'] or 0

    def last_payment_type(self):
        """Return date of last payment or None
        """
        last_payment = self.last_payment
        if last_payment:
            return last_payment.type
        else:
            return None

    last_payment_type.short_description = _("Last payment type")
    last_payment_type.admin_order_field = 'last_payment__type'

    def regular_frequency_td(self):
        """Return regular frequency as timedelta"""
        interval_in_days = {
            'monthly': 31,
            'quaterly': 92,
            'biannually': 183,
            'annually': 366,
        }
        try:
            return datetime.timedelta(days=interval_in_days[self.regular_frequency])
        except KeyError:
            return None

    @computed(models.DateField(null=True), depends=['payment_set'])
    def expected_regular_payment_date(self):
        last_payment = self.last_payment_function()
        last_payment_date = last_payment.date if last_payment else None
        if self.regular_payments != "regular":
            return None
        if last_payment_date:
            # Exactly a month after last payment or whatever
            # expectation record for the given user is set to
            freq = self.regular_frequency_td()
            if not freq:
                return None
            expected = last_payment_date + freq
            if self.expected_date_of_first_payment:
                expected = max(expected, self.expected_date_of_first_payment)
        elif self.expected_date_of_first_payment:
            # Expected date + 3 days tolerance on user side
            expected = self.expected_date_of_first_payment + datetime.timedelta(days=3)
        else:
            # Registration + month (always, even for quaterly and annual payments)
            expected = self.registered_support.date() + datetime.timedelta(days=31)
        return expected

    @computed(models.FloatField(null=True), depends=['payment_set'])
    def payment_total(self):
        return self.payment_set.aggregate(sum=Sum('amount'))['sum'] or 0

    def total_contrib_string(self):
        """Return the sum of all money received from this user
        """
        return mark_safe(u"%s&nbsp;Kč" % intcomma(int(self.payment_total)))

    total_contrib_string.short_description = _("Total")
    total_contrib_string.admin_order_field = 'payment_total'

    def regular_payments_delay(self):
        """Check if his payments are OK

        Return True if so, otherwise return the delay in payment as dattime.timedelta
        """
        expected_regular_payment_date = self.expected_regular_payment_date
        if self.regular_payments == "regular" and expected_regular_payment_date:
            # Check for regular payments
            # (Allow 7 days for payment processing)
            if expected_regular_payment_date:
                expected_with_tolerance = expected_regular_payment_date + datetime.timedelta(days=10)
                if (expected_with_tolerance < datetime.date.today()):
                    return datetime.date.today() - expected_with_tolerance
        return False

    @computed(models.IntegerField(null=True), depends=['payment_set#amount'])
    def extra_money(self):
        """Check if we didn't receive more money than expected in the last payment period"""
        if self.regular_payments == "regular":
            freq = self.regular_frequency_td()
            if not freq:
                return None
            payments = self.payment_set.filter(
                date__gt=datetime.date.today() - freq + datetime.timedelta(days=3),
            )
            total = payments.aggregate(total=Sum('amount'))['total'] or 0
            if self.regular_amount and total > self.regular_amount:
                return total - self.regular_amount
        return None

    def regular_payments_info(self):
        if self.regular_payments == "onetime":
            return _boolean_icon(False)
        if self.regular_payments == "promise":
            return _boolean_icon(None)
        return self.expected_regular_payment_date

    regular_payments_info.allow_tags = True
    regular_payments_info.short_description = _(u"Expected payment")
    regular_payments_info.admin_order_field = 'expected_regular_payment_date'

    def payment_delay(self):
        if self.regular_payments_delay():
            return timesince(self.expected_regular_payment_date)
        else:
            return _boolean_icon(False)

    payment_delay.allow_tags = True
    payment_delay.short_description = _(u"Payment delay")
    payment_delay.admin_order_field = 'expected_regular_payment_date'

    def extra_payments(self):
        if self.extra_money:
            return "%s&nbsp;Kč" % self.extra_money
        else:
            return _boolean_icon(False)

    extra_payments.allow_tags = True
    extra_payments.short_description = _(u"Extra money")
    extra_payments.admin_order_field = 'extra_money'

    @computed(models.NullBooleanField(null=True), depends=['payment_set'])
    def no_upgrade(self):
        """Check for users without upgrade to payments

        Returns true if:
        1. user is regular at least for the last year
        2. user didn't increase the amount of his payments during last year

        This really only makes sense for monthly payments.
        """
        if self.regular_payments != "regular":
            return False
        payment_now = self.last_payment_function()
        if ((not payment_now) or (payment_now.date < (datetime.date.today() - datetime.timedelta(days=45)))):
            return False
        payments_year_before = Payment.objects.filter(
            user_donor_payment_channel=self,
            date__lt=datetime.datetime.now() - datetime.timedelta(days=365),
        ).order_by('-date')
        if (len(payments_year_before) == 0):
            return False
        if (payment_now.amount == payments_year_before[0].amount):
            return True
        else:
            return False

    def yearly_regular_amount(self):
        times = {
            'monthly': 12,
            'quaterly': 4,
            'biannually': 2,
            'annually': 1,
        }
        if self.regular_frequency and self.regular_amount:
            return self.regular_amount * times[self.regular_frequency]
        else:
            return 0

    def person_name(self):
        try:
            return self.user.__str__()
        except Profile.DoesNotExist:  # This happens, when UserInCampaign is cached, but it is deleted already
            return "No Profile"

    person_name.short_description = _("Full name")

    def monthly_regular_amount(self):
        return float(self.yearly_regular_amount()) / 12.0

    def clean(self, *args, **kwargs):
        self.generate_VS()
        self.check_duplicate()
        return super().clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.clean()  # run twice if saved in admin
        if self.pk is None:
            insert = True
        else:
            insert = False
        super().save(*args, **kwargs)
        if self.user:
            # Evaluate autocom immediatelly only when the affected
            # user is known, otherwise the bellow check would be too
            # time-consuming (relying on Cron performing it in regular
            # intervals anyway)
            from .autocom import check as autocom_check
            autocom_check(
                user_profiles=UserProfile.objects.filter(userchannels__pk=self.pk),
                event=self.event,
                action=(insert and 'new-user' or None),
            )


class NewUserManager(models.Manager):
    def get_queryset(self):
        return super(NewUserManager, self).get_queryset().filter()


class NewUser(DonorPaymentChannel):
    objects = NewUserManager()

    class Meta:
        proxy = True
        verbose_name = _("new user")
        verbose_name_plural = _("new users")


class GatedPaymentManager(models.Manager):
    def gate(self, user):
        if user.has_perm('aklub.can_edit_all_units'):
            return self
        return self.filter(user_donor_payment_channel__bank_account__administrative_unit__in=user.administrated_units.all())


class Payment(WithAdminUrl, models.Model):
    """Payment model and DB table

    There are three kinds of payments:

    1) Payments that correspond 1:1 to a line in an account statement with a
    positive amount of money transfered

    2) Payments in cash are introduced by club administration and do not have
    any binding to the account statements

    3) Expected payment -- if the user commits to a single isolated payment but
    haven't sent the money yet or we haven't received the account statement
    confirmation yet. Expected payments might become case (1) or might stay as
    expected indefinitely in case the user doesn't actually make the payment.
    """

    class Meta:
        verbose_name = _("Payment")
        verbose_name_plural = _("Payments")
        ordering = ['-date']

    TYPE_OF_PAYMENT = (
        ('bank-transfer', _('Bank transfer')),
        ('cash', _('In cash')),
        ('expected', _('Expected payment')),
        ('creadit_card', _('Credit card')),
        ('material_gift', _('Material gift')),
        ('darujme', 'Darujme.cz'),
    )
    our_note = models.CharField(
            verbose_name=("Our note"),
            help_text=_("Little note to payment"),
            max_length=100,
            default="",
            blank=True,
    )
    recipient_account = models.ForeignKey(
        MoneyAccount,
        verbose_name=("Recipient account"),
        help_text=_("Recipient bank account number"),
        on_delete=models.SET_NULL,
        null=True,
    )
    date = models.DateField(
        verbose_name=_("Date of payment"),
    )
    amount = models.PositiveIntegerField(
        verbose_name=_("Amount"),
        help_text=_("Amount of money in the main used curency"),
    )
    account = models.CharField(
        verbose_name=("Account"),
        help_text=_("Bank account from which money was received"),
        max_length=100,
        blank=True,
    )
    bank_code = models.CharField(
        verbose_name=_("Bank code"),
        help_text=_("Code of bank from which money was received"),
        max_length=30,
        blank=True,
    )
    VS = models.CharField(
        verbose_name=_("VS 1"),
        help_text=_("Variable symbol 1"),
        max_length=30,
        blank=True,
        null=True,
    )
    VS2 = models.CharField(
        verbose_name=_("VS 2"),
        help_text=_("Variable symbol 2"),
        max_length=30,
        blank=True,
        null=True,
        )
    SS = models.CharField(
        _("SS"),
        help_text=_("Specific symbol"),
        max_length=30,
        blank=True,
    )
    KS = models.CharField(
        verbose_name=_("CS"),
        help_text=_("Constant symbol"),
        max_length=30,
        blank=True,
    )
    BIC = models.CharField(
        verbose_name=_("BIC"),
        help_text=_("BIC"),
        max_length=30,
        blank=True,
        null=True,
    )
    user_identification = models.CharField(
        verbose_name=_("Sender identification"),
        help_text=_("Sender identification string on the account statement"),
        max_length=50,
        blank=True,
    )
    type = models.CharField(  # noqa
        verbose_name=_("Type"),
        help_text=_("Type of payment"),
        choices=TYPE_OF_PAYMENT,
        max_length=200,
        blank=True,
    )
    done_by = models.CharField(
        verbose_name=_("Done by"),
        help_text=_("This is a column imported from the account statements. "
                    "It's purpose is not clear. It has been usually blank on "
                    "the account statement we have received so far."),
        max_length=500,
        blank=True,
    )
    account_name = models.CharField(
        verbose_name=_("Account name"),
        max_length=200,
        blank=True,
    )
    bank_name = models.CharField(
        verbose_name=_("Bank name"),
        max_length=500,
        blank=True,
    )
    transfer_note = models.CharField(
        verbose_name=_("Transfer note"),
        max_length=200,
        blank=True,
        null=True,
    )
    currency = models.CharField(
        verbose_name=_("Currency"),
        max_length=200,
        blank=True,
        null=True,
    )
    recipient_message = models.CharField(
        verbose_name=_("Recipient message"),
        max_length=200,
        blank=True,
        null=True,
    )
    operation_id = models.CharField(
        verbose_name=_("Operation ID"),
        max_length=200,
        blank=True,
        null=True,
    )
    transfer_type = models.CharField(
        verbose_name=_("Transfer type"),
        max_length=200,
        blank=True,
        null=True,
    )
    specification = models.CharField(
        verbose_name=_("Specification"),
        max_length=200,
        blank=True,
        null=True,
    )
    order_id = models.CharField(
        verbose_name=_("Order ID"),
        max_length=200,
        blank=True,
        null=True,
    )
    # Pairing of payments with a specific club system user
    user_donor_payment_channel = models.ForeignKey(
        DonorPaymentChannel,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    # Origin of payment from bank account statement
    account_statement = models.ForeignKey(
        AccountStatements,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    created = models.DateTimeField(
        verbose_name=_("Date of creation"),
        auto_now_add=True,
        null=True,
    )
    updated = models.DateTimeField(
        verbose_name=_("Date of last change"),
        auto_now=True,
        null=True,
    )

    objects = GatedPaymentManager()

    def person_name(self):
        """Return name of the payer"""
        if self.user_donor_payment_channel:
            return self.user_donor_payment_channel.user.person_name()

    def paired_with_expected(self):
        """Return if the payment is paired with an expected payment

        Expected payments are of two types:

        1) Single individual payments, that were previously registered as
        'expected'
        2) Payments expected implicitly because the user is a regular
        contributor
        """
        # TODO: Logic to say if this payment was expected and processed correctly
        if self.user_donor_payment_channel:
            return True
        else:
            return False

    def save(self, *args, **kwargs):
        if self.pk is None:
            insert = True
        else:
            insert = False
        super().save(*args, **kwargs)
        if self.user_donor_payment_channel:
            # Evaluate autocom immediatelly only when the affected
            # user is known, otherwise the bellow check would be too
            # time-consuming (relying on Cron performing it in regular
            # intervals anyway)
            from .autocom import check as autocom_check
            autocom_check(
                event=self.user_donor_payment_channel.event,
                user_profiles=UserProfile.objects.filter(userchannels__pk=self.user_donor_payment_channel.pk),
                action=(insert and 'new-payment' or None),
                )

    def __str__(self):
        return str(self.amount)


COMMUNICATION_TYPE = (
    ('mass', _("Mass")),
    ('auto', _("Automatic")),
    ('individual', _("Individual")),
)


class AutomaticCommunication(models.Model):
    """AutomaticCommunication entry and DB model

    Automatic communication is a communication template bound to
    a specific condition. If the condition becomes true for the given
    user, a Communication is created for him and perhaps automatically
    dispatched, based on the configuration. See the 'Communication'
    model and the 'autocom' module."""

    class Meta:
        verbose_name = _("Automatic Communication")
        verbose_name_plural = _("Automatic Communications")

    name = models.CharField(
        verbose_name=_("Name"),
        max_length=50,
        blank=False,
        null=True,
    )
    condition = models.ForeignKey(
        'flexible_filter_conditions.NamedCondition',
        null=True,
        on_delete=models.SET_NULL,
    )
    method_type = models.ForeignKey(
        "interactions.interactiontype",
        help_text=_("Interaction type with allowed sending"),
        on_delete=models.CASCADE,
        limit_choices_to=Q(send_sms=True) | Q(send_email=True),
        null=True,
    )
    subject = models.CharField(
        verbose_name=_("Subject"),
        max_length=130,
    )
    subject_en = models.CharField(
        verbose_name=_("English subject"),
        max_length=130,
        blank=True,
        null=True,
    )
    event = models.ForeignKey(
        Event,
        help_text=("Event"),
        verbose_name=("Event from which are DonorPaymentChannel data selected"),
        blank=True,
        on_delete=models.SET_NULL,
        null=True,
    )
    template = models.TextField(
        verbose_name=_("Template"),
        help_text=_(
            "Template can contain following variable substitutions: "
            "$addressment  "
            "$last_name_vokativ  "
            "$name  "
            "$firstname  "
            "$surname  "
            "$street  "
            "$city  "
            "$zipcode  "
            "$email  "
            "$telephone  "
            "$regular_amount  "
            "$regular_frequency  "
            "$var_symbol  "
            "$last_payment_amount  "
            "$auth_token  "
        ),
        max_length=50000,
    )
    template_en = models.TextField(
        verbose_name=_("English template"),
        max_length=50000,
        blank=True,
        null=True,
    )
    only_once = models.BooleanField(
        verbose_name=_("Only once"),
        help_text=_("If checked, never send this communication twice to one user"),
        default=True,
    )
    dispatch_auto = models.BooleanField(
        verbose_name=_("Dispatch auto"),
        help_text=_("If checked, the communication might be dispatched by the system "
                    "(e.g. an email sent) as soon as condition becomes true, without "
                    "any further action from the administrator. If not, the communication "
                    "is created, but the administrator must send it manually."),
        default=False,
    )
    sent_to_users = models.ManyToManyField(
        DonorPaymentChannel,
        help_text=_(
            "List of users to whom this communication was already sent"),
        blank=True,
    )
    administrative_unit = models.ForeignKey(
        AdministrativeUnit,
        verbose_name=_("administrative unit"),
        on_delete=models.CASCADE,
        null=True,
        blank=False,
    )

    def __str__(self):
        return str(self.name)

    def clean(self):
        # TODO: remove after fixing
        # How shoud this work?
        # dont forget to uncomment/remove test_automatic_communication_changelist_post in test_admin
        raise ValidationError('Cant create new automatic communication because its under development!')


gender_strings_validator = autocom.gendrify_text
variable_validator = RegexValidator(r'^([^$]*(\$(%s)\b)?)*$' % '|'.join(autocom.KNOWN_VARIABLES), _("Unknown variable"))


class MassCommunication(models.Model):
    """MassCommunication entry and DB model"""

    class Meta:
        verbose_name = _("Mass Communication")
        verbose_name_plural = _("Mass Communications")

    EMAIL_BODY_CREATION_CHOICES = (
        ("new", _("Create new email body")),
        ('existed', _("Choose email body template")),
    )

    name = models.CharField(
        verbose_name=_("Name"),
        max_length=50,
        blank=False,
        null=True,
    )
    date = models.DateField(
        verbose_name=_("Date"),
        blank=False,
        null=False,
    )
    method_type = models.ForeignKey(
        "interactions.interactiontype",
        on_delete=models.CASCADE,
        help_text=_("Interaction type with allowed sending"),
        limit_choices_to=Q(send_sms=True) | Q(send_email=True),
        null=True,
    )
    subject = models.CharField(
        verbose_name=_("Subject"),
        max_length=130,
        help_text=_("Same variables as in template can be used"),
        validators=[gender_strings_validator, variable_validator],
    )
    subject_en = models.CharField(
        verbose_name=_("English subject"),
        help_text=format_lazy(
            "{}<br/>{}",
            _("English version of the subject. If empty, English speaking users will not receive this communication."),
            _("Same variables as in template can be used"),
        ),
        max_length=130,
        blank=True,
        null=True,
        validators=[gender_strings_validator, variable_validator],
    )
    template_type = models.CharField(
        verbose_name=_("Choose how to create an email body"),
        max_length=350,
        null=False,
        blank=True,
        default="new",
        choices=EMAIL_BODY_CREATION_CHOICES,
    )
    template_name = models.CharField(
        verbose_name=_("Choose template"),
        max_length=350,
        null=True,
        blank=True,
    )
    template = models.TextField(
        verbose_name=_("Template"),
        help_text=_("Template can contain following variable substitutions: <br/>") + ("{mr|mrs} or {mr/mrs}, $" + ", $"
                                                                                       .join(autocom.KNOWN_VARIABLES)),
        max_length=50000,
        blank=True,
        null=True,
        validators=[gender_strings_validator, variable_validator],
    )
    template_en_type = models.CharField(
        verbose_name=_("Choose how to create an email body"),
        max_length=350,
        null=False,
        blank=True,
        default="new",
        choices=EMAIL_BODY_CREATION_CHOICES,
    )
    template_en_name = models.CharField(
        verbose_name=_("Choose template"),
        max_length=350,
        null=True,
        blank=True,
    )
    template_en = models.TextField(
        verbose_name=_("English template"),
        max_length=50000,
        blank=True,
        null=True,
        help_text=_("Same variables as in template can be used"),
        validators=[gender_strings_validator, variable_validator],
    )
    attachment = models.FileField(
        verbose_name=_("Attachment"),
        upload_to='mass-communication-attachments',
        blank=True,
        null=True,
    )
    attach_tax_confirmation = models.BooleanField(
        verbose_name=_("Attach tax confirmation"),
        help_text=_("If this field is checked, select year and type of pdf to send"),
        default=False,
    )
    attached_tax_confirmation_year = models.PositiveIntegerField(
        verbose_name=_("Year"),
        blank=True,
        null=True,
    )

    attached_tax_confirmation_type = models.ForeignKey(
        'smmapdfs.PdfSandwichType',
        verbose_name=_("Type of PDF"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    send_to_users = models.ManyToManyField(
        Profile,
        verbose_name=_("send to users"),
        help_text=_(
            "All users who should receive the communication"),
        limit_choices_to={
            'is_active': 'True',
            # 'wished_information': 'True',
            'preference__send_mailing_lists': 'True',
        },
        blank=True,
    )
    note = models.TextField(
        verbose_name=_("note"),
        help_text=_("Note"),
        max_length=500,
        blank=True,
        null=True,
    )
    administrative_unit = models.ForeignKey(
        AdministrativeUnit,
        verbose_name=_("administrative unit"),
        on_delete=models.CASCADE,
        null=True,
        blank=False,
    )

    def __str__(self):
        return str(self.name)

    def clean(self):
        if self.attach_tax_confirmation:
            if not self.attached_tax_confirmation_year or not self.attached_tax_confirmation_type:
                raise ValidationError("YEAR and PDF_TYPE must be set")
        super().clean()


class OverwriteStorage(FileSystemStorage):

    def get_available_name(self, name, max_length):
        """
        Returns a filename that's free on the target storage system, and
        available for new content to be written to.
        """
        # If the filename already exists, remove it as if it was a true file syste
        if self.exists(name):
            self.delete(name)
        return name


class TaxConfirmationField(PdfSandwichFieldABC):
    # fields are used for userprofile taxs
    fields_user = {
        "year": (lambda tc: str(tc.year)),
        "amount": (lambda tc: "%s Kč." % intcomma(int(tc.amount))),
        "name": (lambda tc: tc.get_user_name()),
        "street": (lambda tc: tc.get_street()),
        "addr_city": (lambda tc: tc.get_addr_city()),
        "zip_code": (lambda tc: tc.get_zip_code()),
        "country": (lambda tc: tc.get_country()),
        "date": (lambda tc: datetime.date.today().strftime("%d.%m.%Y")),
        "administrative_unit": (lambda tc: tc.get_administrative_unit()),
    }
    # fields are used for company_profiles taxs
    fields_company = {
        "year": (lambda tc: str(tc.year)),
        "amount": (lambda tc: "%s Kč." % intcomma(int(tc.amount))),
        "street": (lambda tc: tc.get_street()),
        "addr_city": (lambda tc: tc.get_addr_city()),
        "zip_code": (lambda tc: tc.get_zip_code()),
        "country": (lambda tc: tc.get_country()),
        "date": (lambda tc: datetime.date.today().strftime("%d.%m.%Y")),
        "administrative_unit": (lambda tc: tc.get_administrative_unit()),
        "company_name": (lambda tc: tc.get_company_name()),
        "contact_name": (lambda tc: tc.get_company_contact_name()),
        "crn": (lambda tc: tc.get_company_crn()),
        "tin": (lambda tc: tc.get_company_tin()),

    }

    fields = dict(fields_user, **fields_company)


class TaxConfirmationPdf(PdfSandwichABC):
    field_model = TaxConfirmationField
    obj = models.ForeignKey(
        'TaxConfirmation',
        null=False,
        blank=False,
        on_delete=models.CASCADE,
    )


def confirmation_upload_to(instance, filename):
    return "DEPRICATED"


class TaxConfirmation(models.Model):
    user_profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )
    year = models.PositiveIntegerField()
    amount = models.PositiveIntegerField(default=0)
    file = models.FileField(storage=OverwriteStorage())  # DEPRICATED!
    pdf_type = models.ForeignKey(
                    'smmapdfs.PdfSandwichType',
                    on_delete=models.SET_NULL,
                    null=True,
                    blank=True,
    )

    def get_pdf(self):
        try:
            try:
                url = self.taxconfirmationpdf_set.get().pdf.url
            except TaxConfirmationPdf.DoesNotExist:
                url = self.file.url
        except ValueError:
            url = None
        if url:
            return format_html("<a href='{}'>{}</a>", url, _('PDF file'))
        else:
            return '-'

    get_pdf.short_description = _("PDF")

    def get_user_name(self):
        return "%s %s" % (self.user_profile.first_name, self.user_profile.last_name)

    def get_street(self):
        return"%s" % (self.user_profile.street)

    def get_addr_city(self):
        return "%s" % (self.user_profile.city)

    def get_zip_code(self):
        return "%s" % (self.user_profile.zip_code,)

    def get_country(self):
        return "%s" % (self.user_profile.country,)

    sandwich_model = TaxConfirmationPdf

    def get_sandwich_type(self):
        return self.pdf_type

    def get_payment_set(self):
        return Payment.objects.filter(user_profile=self.user_profile).exclude(type='expected').filter(date__year=self.year)

    def get_administrative_unit(self):
        return self.pdf_type.pdfsandwichtypeconnector.administrative_unit.name

    def get_company_name(self):
        return self.user_profile.name

    def get_company_contact_name(self):
        return f'{self.user_profile.contact_first_name} {self.user_profile.contact_last_name}'

    def get_company_tin(self):
        return self.user_profile.tin

    def get_company_crn(self):
        return self.user_profile.crn

    class Meta:
        verbose_name = _("Tax confirmation")
        verbose_name_plural = _("Tax confirmations")


User._meta.get_field('email').__dict__['_unique'] = True
