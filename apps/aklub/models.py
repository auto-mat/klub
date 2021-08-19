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

from admin_tools_stats.models import DashboardStats

from autoslug import AutoSlugField

from colorfield.fields import ColorField

from computedfields.models import ComputedFieldsModel, computed

from django.apps import apps
from django.contrib.admin.templatetags.admin_list import _boolean_icon
from django.contrib.auth.models import (
    AbstractBaseUser, AbstractUser, PermissionsMixin,
    User, UserManager,
)
from django.contrib.contenttypes.models import ContentType
from django.contrib.humanize.templatetags.humanize import intcomma
from django.contrib.postgres.fields import JSONField
from django.core.files.storage import FileSystemStorage
from django.core.validators import RegexValidator, ValidationError
from django.db import models, transaction
from django.db.models import Count, Q, Sum, signals
from django.db.models.functions import Trunc
from django.dispatch import receiver
from django.utils import timezone
from django.utils.html import format_html, format_html_join, mark_safe
from django.utils.text import format_lazy
from django.utils.translation import ugettext_lazy as _

from polymorphic.managers import PolymorphicManager
from polymorphic.models import PolymorphicModel, PolymorphicTypeUndefined
from polymorphic.query import PolymorphicQuerySet

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


class CustomUserQueryset(PolymorphicQuerySet):
    """
    Rewriting  base delete method to separatly delete UserProfile/CompanyProfile by calling parent delete method
    Bug is raised by diff FK for child model
    """
    def delete(self):
        UserProfile.objects.filter(id__in=self.instance_of(UserProfile).values_list('id', flat=True)).delete()
        CompanyProfile.objects.filter(id__in=self.instance_of(CompanyProfile).values_list('id', flat=True)).delete()


class CustomUserManager(PolymorphicManager, UserManager):
    queryset_class = PolymorphicQuerySet
    use_in_migrations = False

    def get_queryset(self):
        """
        we call diff Manager for Polymorphic parent and chill
        """
        if self.model == Profile:
            self.queryset_class = CustomUserQueryset
        qs = self.queryset_class(self.model, using=self._db, hints=self._hints)
        if self.model._meta.proxy:
            qs = qs.instance_of(self.model)
        return qs

    def create_user(self, email, password, **extra_fields):
        if extra_fields.get('polymorphic_ctype_id', None):
            ctype_id = extra_fields.pop('polymorphic_ctype_id')
            model = ContentType.objects.get(id=ctype_id).model_class()
        if not email:
            raise ValueError(_('The Email must be set'))
        email = self.normalize_email(email)
        user = model(email=email, **extra_fields)
        user.set_password(password)
        user_instance = user.save()
        email = ProfileEmail(
            email=email,
            is_primary=True,
            user=user_instance,
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
    class Meta:
        verbose_name = _("Administrative unit")
        verbose_name_plural = _("Administrative units")

    UNIT_LEVEL_CHOICES = (
        ('regional_center', _('Regional center')),
        ('basic_section', _('Basic section')),
        ('headquarter', _('Headquarter')),
        ('club', _("Club"))
    )

    name = models.CharField(
        verbose_name=_("Name"),
        max_length=255,
    )
    street = models.CharField(
        verbose_name=_("Street and number"),
        max_length=128,
        blank=True,
    )
    gps_latitude = models.FloatField(
        _('GPS latitude'),
        blank=True,
        null=True,
    )
    gps_longitude = models.FloatField(
        _('GPS longitude'),
        blank=True,
        null=True,
    )
    city = models.CharField(
        verbose_name=_("City/City part"),
        max_length=40, blank=True,
    )
    zip_code = models.CharField(
        verbose_name=_("ZIP Code"),
        max_length=30,
        blank=True,
    )
    web_url = models.URLField(
        verbose_name=_("Url address of website"),
        blank=True,
        null=True,
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
    level = models.CharField(
        default="club",
        choices=UNIT_LEVEL_CHOICES,
        max_length=128,
    )

    from_email_address = models.EmailField(
        verbose_name=_("E-mail from address"),
        help_text=_("Every new address has to be set up by system administrator"),
        default="example@nothing_will_sent.ex",
    )
    from_email_str = models.CharField(
        verbose_name=_("E-mail from identifier"),
        default='Example <example@nothing_will_sent.ex>',
        max_length=255,
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
    color = ColorField(
        default='#000000',
        help_text=_("Choose color to help discern Administrative unit in app"),
    )
    slug = AutoSlugField(
        verbose_name=_("Slug"),
        populate_from="name",
        editable=True,
        help_text=_("Identifier of the administrative unit"),
        max_length=100,
        unique=True,
        blank=True,
        null=True,
    )
    president = models.ForeignKey(
        "aklub.UserProfile",
        verbose_name=_("President"),
        related_name="au_president",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    president_since = models.DateField(
        verbose_name=_("President since"),
        null=True,
        blank=True,
    )
    vice_president = models.ForeignKey(
        "aklub.UserProfile",
        verbose_name=_("Vice president"),
        related_name="au_vice_president",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    vice_president_since = models.DateField(
        verbose_name=_("Vice president since"),
        null=True,
        blank=True,
    )
    manager = models.ForeignKey(
        "aklub.UserProfile",
        verbose_name=_("Manager"),
        related_name="au_manager",
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    manager_since = models.DateField(
        verbose_name=_("Manager since"),
        null=True,
        blank=True,
    )

    def __str__(self):
        return str(self.name)


class Expense(models.Model):
    """Expense in campaign"""

    class Meta:
        verbose_name = _("expense")
        verbose_name_plural = _("expenses")

    amount = models.FloatField(
        verbose_name=_("amount"),
    )
    item = models.CharField(
        verbose_name=_("item"),
        max_length=300,
        blank=True,
    )
    campaign = models.ForeignKey(
        "events.Event",
        verbose_name=_("campaign"),
        related_name='expenses',
        on_delete=models.CASCADE,
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
        unique=True,
    )
    firstname = models.CharField(
        verbose_name=_("First name"),
        max_length=40,
    )
    surname = models.CharField(
        verbose_name=_("Surname"),
        max_length=40,
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
    )
    campaigns = models.ManyToManyField(
        "events.Event",
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

    slug = AutoSlugField(
        verbose_name=_("Slug"),
        populate_from="name",
        editable=True,
        blank=True,
        help_text=_("Identifier of the source"),
        max_length=100,
    )
    name = models.CharField(
        verbose_name=_("Name"),
        help_text=_("Name of the source"),
        max_length=100,
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
        "events.Event",
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
        max_length=128,
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
        max_length=128,
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

    def get_email_str(self, administrative_unit=None):
        try:
            if self.is_userprofile():
                return self.profileemail_set.get(is_primary=True).email
            else:
                return self.companycontact_set.get(is_primary=True, administrative_unit=administrative_unit).email
        except (ProfileEmail.DoesNotExist, CompanyContact.DoesNotExist):
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
        if self.is_userprofile():
            numbers = ','.join(number.telephone for number in self.telephone_set.all())
        else:
            numbers = ','.join(number.telephone for number in self.companycontact_set.all())
        return numbers

    def get_donor(self):
        donors = ','.join(donor.VS for donor in self.userchannels.all() if donor.VS is not None)
        return donors

    def get_main_telephone(self, edited_query=None):
        if edited_query is not None:
            active_numbers = edited_query
        else:
            if self.is_userprofile():
                active_numbers = self.telephone_set.all()
            else:
                active_numbers = self.companycontact_set.all()
        numbers = list(map(lambda number: number.create_link() if number.telephone else '-', active_numbers))
        return mark_safe('<br>'.join(numbers))

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
    get_administrative_units.short_description = _("Administrative units")

    def can_administer_profile(self, profile):
        if self.has_perm('aklub.can_edit_all_units'):
            return True
        administrated_unit_pks = {unit.pk for unit in self.administrated_units.all()}
        administrative_unit_pks = {unit.pk for unit in profile.administrative_units.all()}
        if administrated_unit_pks.intersection(administrative_unit_pks):
            return True
        else:
            return False

    def is_userprofile(self):
        if self._meta.model_name == UserProfile._meta.model_name:
            return True
        else:
            return False

    def get_email(self, edited_query=None):
        if edited_query is not None:
            emails = edited_query
        else:
            if self.is_userprofile():
                emails = self.profileemail_set.all()
            else:
                emails = self.companycontact_set.all()
        result = list(
            map(
                lambda email:
                format_html('<b>{}</b>'.format(email.email or "-"))
                if email.is_primary
                else
                format_html('{}'.format(email.email or "-")),
                emails,
            ),
        )
        result.sort(key=lambda item: -1 if '<b>' in item else 0)
        return mark_safe('<br>'.join(result))

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

    def get_main_contact_name(self, edited_query=None):
        if edited_query is not None:
            com = edited_query
        else:
            com = self.companycontact_set.all()
        result = list(
            map(
                lambda contact:
                format_html('<nobr><b>{}</b></nobr>'.format(f'{contact.contact_first_name} {contact.contact_last_name}'))
                if contact.is_primary
                else
                format_html(
                    '<nobr>{}</nobr>'.format(f'{contact.contact_first_name} {contact.contact_last_name}') # noqa
                )
                if contact.contact_first_name or contact.contact_last_name else '-',
                com,
            ),
        )
        result.sort(key=lambda item: -1 if '<b>' in item else 0)
        return mark_safe('<br>'.join(result))

    get_main_contact_name.short_description = _("Contact name")
    get_main_contact_name.admin_order_field = 'full_contact_name'


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
    first_name = models.CharField(
        verbose_name=_('first name'),
        max_length=128,
        blank=True,
    )
    last_name = models.CharField(
        verbose_name=_('last name'),
        max_length=128,
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
    nickname = models.CharField(
        verbose_name=_("Nickname"),
        max_length=126,
        blank=True,
    )
    maiden_name = models.CharField(
        verbose_name=_("Maiden name"),
        max_length=126,
        blank=True,
    )

    @classmethod
    def export_resource_classes(cls):
        from .admin import UserProfileResource
        return {
            'users': ('Users resource', UserProfileResource),
        }


class CompanyContact(models.Model):
    class Meta:
        verbose_name = _("Company contact")
        verbose_name_plural = _("Company contacts")
        unique_together = (
            ('is_primary', 'administrative_unit', 'email'),
            ('is_primary', 'administrative_unit', 'company'),
            # ('company', 'administrative_unit', 'email'), # TODO: telephone number.. wont save?
        )
    BOOL_CHOICES = (
        (None, "No"),
        (True, "Yes")
    )

    contact_first_name = models.CharField(
        verbose_name=_("Contact first name"),
        max_length=256,
        blank=True,
    )
    contact_last_name = models.CharField(
        verbose_name=_("Contact last name"),
        max_length=256,
        blank=True,
    )
    email = models.EmailField(
        _('email address'),
        blank=True,
        null=True,
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
        verbose_name=_("Primary contact"),
        blank=True,
        default=None,
        choices=BOOL_CHOICES,
    )
    note = models.CharField(
        verbose_name=_("Note"),
        max_length=70,
        blank=True,
    )
    company = models.ForeignKey(
        CompanyProfile,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )
    administrative_unit = models.ForeignKey(
        AdministrativeUnit,
        verbose_name=_("administrative unit"),
        on_delete=models.CASCADE,
    )

    def format_number(self):
        if hasattr(self, "telephone") and self.telephone:
            removed_space_tel = self.telephone.replace(" ", "")
            if len(removed_space_tel) > 9:
                return '+' + removed_space_tel[-12:]
            else:
                return '+420' + removed_space_tel[-9:]
        else:
            return ""

    def create_link(self):
        if hasattr(self, "telephone"):
            formated_telephone = self.format_number()
            if self.is_primary is True:
                return format_html("<b><a href='sip:{}'>{}</a></b>", formated_telephone, formated_telephone)
            else:
                return format_html("<a href='sip:{}'>{}</a>", formated_telephone, formated_telephone)


class ProfileEmail(models.Model):
    class Meta:
        verbose_name = _("Email")
        verbose_name_plural = _("Emails")
        unique_together = (
            ("user", "is_primary"),
        )

    bool_choices = (
        (None, "No"),
        (True, "Yes")
    )
    email = models.EmailField(
        _('email address'),
        unique=True,
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
        UserProfile,
        blank=True,
        null=True,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.email

    def save(self, *args, **kwargs):
        if self.user and self.is_primary:
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
    class Meta:
        verbose_name = _("Preference")
        verbose_name_plural = _("Preferences")
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
        UserProfile,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = _("Telephone")
        verbose_name_plural = _("Telephones")
        unique_together = ("user", "is_primary")

    def validate_unique(self, exclude=None):
        super().validate_unique(exclude=exclude)

    def check_duplicate(self, *args, **kwargs):
        if self.pk is None:
            if Telephone.objects.filter(telephone=self.telephone, user=self.user).exists():
                raise ValidationError(_("Duplicate phone number for this user"))

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
        ('account_raiffeisenbank', 'Account statement - Raiffeisenbank '),
        ('darujme', 'Darujme.cz'),
    )

    type = models.CharField(max_length=30, choices=TYPE_OF_STATEMENT, verbose_name=_("Type"))  # noqa
    import_date = models.DateTimeField(auto_now=True, verbose_name=_("Import date"),)
    csv_file = models.FileField(
        verbose_name=_("csv file"),
        upload_to='account-statements',
    )
    date_from = models.DateField(
        verbose_name=_("Date from"),
        blank=True,
        null=True,
    )
    date_to = models.DateField(
        verbose_name=_("Date to"),
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

    def save(self, parse_csv=True, *args, **kwargs):
        super().save(*args, **kwargs)
        if hasattr(self, "payments"):
            for payment in self.payments:
                if payment:
                    payment.account_statement = self
                    payment.save()
        if self.payment_set.count() == 0 and parse_csv:
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
    class Meta:
        verbose_name = _("Bank/Api account")
        verbose_name_plural = _("Bank/Api accounts")

    note = models.TextField(
        verbose_name=_("Bank account note"),
        blank=True,
        null=True,
    )
    administrative_unit = models.ForeignKey(
        AdministrativeUnit,
        verbose_name=_("administrative unit"),
        on_delete=models.CASCADE,
    )
    slug = AutoSlugField(
        verbose_name=_("Slug"),
        help_text=_("Identifier of the Account"),
        max_length=100,
        editable=True,
        unique=True,
        blank=True,
        null=True,
        )


class BankAccount(MoneyAccount):
    class Meta:
        verbose_name = _("Bank account")
        verbose_name_plural = _("Bank accounts")

    bank_account = models.CharField(
        verbose_name=_("Bank Account"),
        max_length=50,
        blank=True,
        null=True,
    )
    bank_account_number = models.CharField(
        verbose_name=_("Bank account number"),
        max_length=50,
    )

    def __str__(self):
        return f'{self.administrative_unit} {self.bank_account_number}'


class ApiAccount(MoneyAccount):
    class Meta:
        verbose_name = _("Api Account")
        verbose_name_plural = _("Api Accounts")

    project_name = models.CharField(
        verbose_name=_("Name"),
        unique=True,
        default='',
        max_length=100,
    )
    project_id = models.IntegerField(
        verbose_name=_("project ID"),
        default=None,
        null=True,
    )
    api_id = models.IntegerField(
        verbose_name=_("API ID"),
        default=None,
        null=True,
    )
    api_secret = models.CharField(
        verbose_name=_("API secret"),
        default='',
        max_length=100,
    )
    api_organization_id = models.IntegerField(
        verbose_name=_("API organization ID"),
        default=None,
        null=True,
    )
    event = models.ForeignKey(
        "events.Event",
        help_text=("Event"),
        verbose_name=("Event"),
        on_delete=models.CASCADE,
    )
    is_active = models.BooleanField(
            verbose_name=_("Active"),
            help_text=_("Is the project active"),
            default=True,
    )

    def __str__(self):
        return f'{self.administrative_unit} -{self.event} - auto api'

    def darujme_url(self):
        url = 'https://www.darujme.cz/api/v1/organization/{0}/pledges-by-filter/?apiId={1}&apiSecret={2}&projectId={3}'.format(
            self.api_organization_id,
            self.api_id,
            self.api_secret,
            self.project_id,
        )
        return url


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
    )
    registered_support = models.DateTimeField(
        verbose_name=_("Registered support"),
        help_text=_("When did this user register to support us"),
        default=timezone.now,
        blank=True,
    )
    REGULAR_PAYMENT_FREQUENCIES = (
        (None, ('---')),
        ('monthly', _('Monthly')),
        ('quaterly', _('Quaterly')),
        ('biannually', _('Bianually')),
        ('annually', _('Anually')),
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
        verbose_name=_("Bank/Api account"),
        related_name='moneyaccounts',
        on_delete=models.CASCADE,
    )
    user_bank_account = models.ForeignKey(
        UserBankAccount,
        verbose_name=_("User bank account"),
        related_name='userbankaccounts',
        on_delete=models.CASCADE,
        default=None,
        null=True,
        blank=True,
    )
    event = models.ForeignKey(
        "events.Event",
        help_text=("Event"),
        verbose_name=("Event"),
        on_delete=models.CASCADE,
    )
    end_of_regular_payments = models.DateField(
        verbose_name=_("End of regular payments (for payments by card)"),
        blank=True,
        null=True,
    )

    def __str__(self):
        return f"Payment channel: {self.VS}"

    def _generate_variable_symbol(self):
        # TODO: must be more effective!
        vs_prefix = self.event.variable_symbol_prefix
        unit = self.money_account.administrative_unit
        if not vs_prefix:
            vs_prefix = '0'
            dpchs_VS = DonorPaymentChannel.objects.filter(
                money_account__administrative_unit=unit,
                VS__startswith=str(vs_prefix),
            ).order_by('-VS').values_list('VS', flat=True)
            if not dpchs_VS:
                # first number
                self.VS = '0000000001'
                return
            for VS in dpchs_VS:
                new_VS = '%0*d' % (10, int(VS)+1)
                exist = DonorPaymentChannel.objects.filter(
                            money_account__administrative_unit=unit,
                            VS=new_VS,
                            ).exists()
                if not exist:
                    self.VS = new_VS
                    return
        else:
            dpchs_VS = DonorPaymentChannel.objects.filter(
                money_account__administrative_unit=unit,
                VS__startswith=str(vs_prefix),
            ).order_by('VS').values_list('VS', flat=True)
            if not dpchs_VS:
                # first number
                self.VS = str(vs_prefix) + '00001'
                return
            for vs in dpchs_VS:
                # we can retype to int because prefix doesnt start with zero
                if str(int(vs)+1) not in dpchs_VS:
                    # is it really free?
                    exist = DonorPaymentChannel.objects.filter(
                                money_account__administrative_unit=unit,
                                VS=str(int(vs)+1),
                                ).exists()
                    if not exist:
                        self.VS = str(int(vs)+1)
                        return
            else:
                raise ValidationError('OUT OF VS')

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
                    raise ValidationError({"VS": _("Duplicate VS")})
        except MoneyAccount.DoesNotExist:
            pass

    @computed(models.IntegerField(null=True), depends=['payment_set'])
    def number_of_payments(self):
        """Return number of payments made by this user
        """
        return self.payment_set.aggregate(count=Count('amount'))['count']

    number_of_payments.short_description = _("Number of payments")
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

    payment_total.short_description = _("Payment total")

    def total_contrib_string(self):
        """Return the sum of all money received from this user
        """
        return mark_safe(u"%s&nbsp;Kč" % intcomma(int(self.payment_total)))

    total_contrib_string.short_description = _("Total")
    total_contrib_string.admin_order_field = 'payment_total'

    def regular_payments_delay(self):
        """Check if his payments are OK

        1) 0 if payments are ok,
        2) number of days from the expected payment date if payments are not ok
        3) None if expected_regular_payment_date is unknown or regular_payments are not "regular"
        """
        expected_regular_payment_date = self.expected_regular_payment_date
        if self.regular_payments == "regular" and expected_regular_payment_date:
            # Check for regular payments
            # (Allow 10 days for payment processing)
            expected_with_tolerance = expected_regular_payment_date + datetime.timedelta(days=10)
            if (expected_with_tolerance < datetime.date.today()):
                delay = datetime.date.today() - expected_with_tolerance
            else:
                delay = 0
        else:
            delay = None
        return delay

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
        except Profile.DoesNotExist:  # This happens, when DonorPaymentChannel is cached, but it is deleted already
            return "No Profile"

    person_name.short_description = _("Full name")

    def monthly_regular_amount(self):
        return float(self.yearly_regular_amount()) / 12.0

    def clean(self, *args, **kwargs):
        self.check_duplicate()
        return super().clean(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.clean()  # run twice in admin
        if not self.VS:
            self._generate_variable_symbol()
        super().save(*args, **kwargs)


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
    custom_fields = JSONField(default=dict)

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

    def __str__(self):
        return str(self.amount)

    @classmethod
    def export_resource_classes(cls):
        from .admin import PaymentResource
        return {
            'export': (_("All columns"), PaymentResource),
        }


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
        null=True,
    )
    condition = models.ForeignKey(
        'flexible_filter_conditions.NamedCondition',
        null=True,
        on_delete=models.SET_NULL,
    )
    method_type = models.ForeignKey(
        "interactions.interactiontype",
        verbose_name=_('Method/Type of Interaction'),
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
        "events.Event",
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
        Profile,
        help_text=_(
            "List of users to whom this communication was already sent"),
        blank=True,
    )
    administrative_unit = models.ForeignKey(
        AdministrativeUnit,
        verbose_name=_("administrative unit"),
        on_delete=models.CASCADE,
        null=True,
    )

    def __str__(self):
        return str(self.name)


gender_strings_validator = autocom.gendrify_text
variable_validator = RegexValidator(r'^([^$]*(\$(%s)\b)?)*$' % '|'.join(autocom.KNOWN_VARIABLES), _("Unknown variable"))


class MassCommunication(models.Model):
    """MassCommunication entry and DB model"""

    class Meta:
        verbose_name = _("Mass Communication")
        verbose_name_plural = _("Mass Communications")

    STATUS_CHOICES = (
        ('waiting_for_sent', _('Waiting for sent')),
        ('already_sent', _('Already sent')),
        ('unknown', _('Unknown'))
    )

    name = models.CharField(
        verbose_name=_("Name"),
        max_length=50,
        null=True,
    )
    date = models.DateField(
        verbose_name=_("Date"),
    )
    method_type = models.ForeignKey(
        "interactions.interactiontype",
        verbose_name=_('Method/Type of Interaction'),
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
    template = models.TextField(
        verbose_name=_("Template"),
        help_text=_("Template can contain following variable substitutions: <br/>") + ("{mr|mrs} or {mr/mrs}, $" + ", $"
                                                                                       .join(autocom.KNOWN_VARIABLES)),
        max_length=50000,
        null=True,
        validators=[gender_strings_validator, variable_validator],
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
    status = models.BooleanField(
        verbose_name=_("status"),
        help_text=_("have emails already been sent?"),
        default=False,
    )
    administrative_unit = models.ForeignKey(
        AdministrativeUnit,
        verbose_name=_("administrative unit"),
        on_delete=models.CASCADE,
        null=True,
    )

    def __str__(self):
        return str(self.name)

    def clean(self):
        if self.attach_tax_confirmation:
            if not self.attached_tax_confirmation_year or not self.attached_tax_confirmation_type:
                raise ValidationError(_("YEAR and PDF_TYPE must be set"))
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
        on_delete=models.CASCADE,
    )


def confirmation_upload_to(instance, filename):
    return "DEPRICATED"


class TaxConfirmation(models.Model):
    user_profile = models.ForeignKey(
        Profile,
        on_delete=models.CASCADE,
    )
    year = models.PositiveIntegerField(verbose_name=_('Year'))
    amount = models.PositiveIntegerField(default=0, verbose_name=_('Amount'))
    file = models.FileField(storage=OverwriteStorage())  # DEPRICATED!
    pdf_type = models.ForeignKey(
                    'smmapdfs.PdfSandwichType',
                    verbose_name=_('PDF type'),
                    on_delete=models.SET_NULL,
                    null=True,
                    blank=True,
    )

    def get_pdf(self):
        try:
            try:
                url = self.taxconfirmationpdf_set.all()[0].pdf.url
            except IndexError:
                url = self.file.url
        except ValueError:
            url = None
        if url:
            return format_html("<a href='{}'>{}</a>", url, _('PDF file'))
        else:
            return '-'

    get_pdf.short_description = _("PDF")

    def get_user_name(self):
        return "%s %s %s %s" % (
            self.user_profile.title_before or "",
            self.user_profile.first_name or "",
            self.user_profile.last_name or "",
            self.user_profile.title_after or "",
        )

    def get_street(self):
        return"%s" % (self.user_profile.street or "",)

    def get_addr_city(self):
        return "%s" % (self.user_profile.city or "",)

    def get_zip_code(self):
        return "%s" % (self.user_profile.zip_code or "",)

    def get_country(self):
        return "%s" % (self.user_profile.country or "",)

    sandwich_model = TaxConfirmationPdf

    def get_sandwich_type(self):
        return self.pdf_type

    def get_payment_set(self):
        return Payment.objects.filter(user_profile=self.user_profile).exclude(type='expected').filter(date__year=self.year)

    def get_administrative_unit(self):
        return "%s" % (self.pdf_type.pdfsandwichtypeconnector.administrative_unit.name or "",)

    def get_company_name(self):
        return "%s" % (self.user_profile.name or "")

    def get_company_contact_name(self):
        try:
            main_contact = self.user_profile.companycontact_set.get(
                is_primary=True,
                administrative_unit=self.pdf_type.pdfsandwichtypeconnector.administrative_unit,
            )
            return "%s %s" % (main_contact.contact_first_name, main_contact.contact_last_name)
        except CompanyContact.DoesNotExist:
            return ""

    def get_company_tin(self):
        return "%s" % (self.user_profile.tin or "",)

    def get_company_crn(self):
        return "%s" % (self.user_profile.crn or "",)

    class Meta:
        verbose_name = _("Tax confirmation")
        verbose_name_plural = _("Tax confirmations")


User._meta.get_field('email').__dict__['_unique'] = True


# we need to work with extra administrative_unit so money_patch is added there and extra filter by administrative_unit is added
# add model_name and path to administrative_unit
administrative_unit_extra_filters = {
    "UserProfile": "administrative_units__in",
    "Payment": "user_donor_payment_channel__money_account__administrative_unit__in",
}

def get_time_series(self, dynamic_criteria, all_criteria, request, time_since, time_until, interval): # noqa
    """ Get the stats time series """
    model_name = apps.get_model(self.model_app_name, self.model_name)
    kwargs = {}
    dynamic_kwargs = []
    if request and not request.user.is_superuser and self.user_field_name:
        kwargs[self.user_field_name] = request.user
    for m2m in all_criteria:
        criteria = m2m.criteria
        # fixed mapping value passed info kwargs
        if criteria.criteria_fix_mapping:
            for key in criteria.criteria_fix_mapping:
                # value => criteria.criteria_fix_mapping[key]
                kwargs[key] = criteria.criteria_fix_mapping[key]

        # dynamic mapping value passed info kwargs
        dynamic_key = "select_box_dynamic_%i" % m2m.id
        if dynamic_key in dynamic_criteria:
            if dynamic_criteria[dynamic_key] != '':
                dynamic_values = dynamic_criteria[dynamic_key]
                dynamic_field_name = m2m.get_dynamic_criteria_field_name()
                criteria_key = 'id' if dynamic_field_name == '' else dynamic_field_name
                if isinstance(dynamic_values, (list, tuple)):
                    single_value = False
                else:
                    dynamic_values = (dynamic_values,)
                    single_value = True

                for dynamic_value in dynamic_values:
                    try:
                        criteria_value = m2m.get_dynamic_choices(time_since, time_until)[dynamic_value]
                    except KeyError:
                        criteria_value = 0
                    if isinstance(criteria_value, (list, tuple)):
                        criteria_value = criteria_value[0]
                    else:
                        criteria_value = dynamic_value
                    criteria_key_string = criteria_key + ("__in" if isinstance(criteria_value, list) else "")
                    if single_value:
                        kwargs[criteria_key_string] = criteria_value
                    else:
                        dynamic_kwargs.append(Q(**{criteria_key_string: criteria_value}))

    aggregate_dict = {}
    i = 0
    if not dynamic_kwargs:
        dynamic_kwargs = [None]

    for dkwargs in dynamic_kwargs:
        i += 1
        aggregate_dict['agg_%i' % i] = self.get_operation(dkwargs)

    # TODO: maybe backport values_list support back to django-qsstats-magic and use it again for the query
    time_range = {'%s__range' % self.date_field_name: (time_since, time_until)}
    qs = model_name.objects
    qs = qs.filter(**time_range)
    qs = qs.filter(**kwargs)
    # this lines are added
    if not request.user.has_perm('aklub.can_edit_all_units'):
        qs = qs.filter(**{administrative_unit_extra_filters[self.model_name]: request.user.administrated_units.all()})
    # ^^^
    kind = interval[:-1]
    qs = qs.annotate(d=Trunc(self.date_field_name, kind))
    qs = qs.values_list('d')
    qs = qs.order_by('d')
    qs = qs.annotate(**aggregate_dict)
    return qs


DashboardStats.add_to_class("get_time_series", get_time_series)
