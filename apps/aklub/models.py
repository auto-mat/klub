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

# Django imports
import django
from django.contrib.admin.templatetags.admin_list import _boolean_icon
from django.db import models
from django.db.models import Sum, Count, Q
from django.core.mail import EmailMultiAlternatives
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.core.files.temp import NamedTemporaryFile
from django.utils.timesince import timesince
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import string_concat
from django.utils.html import mark_safe
from django.contrib.auth.models import User
from django.contrib.humanize.templatetags.humanize import intcomma
from denorm import denormalized, depend_on_related
import html2text
# External dependencies
import datetime
import csv
import codecs
import os.path
import stdimage
# Local modules
from . import confirmation
import logging
logger = logging.getLogger(__name__)


class Campaign(models.Model):
    """Campaign -- abstract event with description

    These events can be associated to a user."""

    class Meta:
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")

    created = models.DateField(
        verbose_name=_("Created"))
    terminated = models.DateField(
        verbose_name=_("Terminated"),
        blank=True,
        null=True,
        )
    name = models.CharField(
        verbose_name=_("Name"),
        help_text=_("Choose some unique name for this campaign"),
        max_length=100, blank=True)
    darujme_name = models.CharField(
        verbose_name=_("Name in Darujme.cz"),
        unique=True,
        default=None,
        max_length=100,
        blank=True,
        null=True,
        )
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Description of this campaign"),
        max_length=3000, blank=True)
    acquisition_campaign = models.BooleanField(
        verbose_name=_("Acquisition campaign"),
        default=False,
        )
    real_yield = models.FloatField(
        verbose_name=_("Real yield"),
        help_text=_("Use if yield differs from counted value"),
        blank=True, null=True)
    slug = models.SlugField(
        verbose_name=_("Slug"),
        help_text=_("Identifier of the campaign"),
        default=None,
        max_length=100,
        unique=True,
        blank=True,
        null=True,
    )
    allow_statistics = models.BooleanField(
        verbose_name=_("Allow statistics exports"),
        default=False)

    def number_of_members(self):
        return self.userincampaign_set.count()
    number_of_members.short_description = _("number of members")

    def recruiters(self):
        return Recruiter.objects.filter(campaigns=self)
    recruiters.short_description = _("recruiters")

    def number_of_recruiters(self):
        return len(self.recruiters())
    number_of_recruiters.short_description = _("number of recruiters")

    def yield_total(self):
        if self.acquisition_campaign:
            return UserInCampaign.objects.filter(campaign=self).aggregate(yield_total=Sum('payment__amount'))['yield_total']
        else:
            return self.real_yield
    yield_total.short_description = _("total yield")

    def expected_yearly_income(self):
        income = 0
        for campaign_member in UserInCampaign.objects.filter(campaign=self):
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
        blank=False, null=False)
    item = models.CharField(
        verbose_name=_("item"),
        max_length=300,
        blank=True,
        )
    campaign = models.ForeignKey(
        Campaign,
        verbose_name=_("campaign"),
        related_name='expenses',
        on_delete=models.CASCADE,
        null=False, blank=False)


class Recruiter(models.Model):
    """Recruiter -- person that recruits new club members"""

    class Meta:
        verbose_name = _("Recruiter")
        verbose_name_plural = _("Recruiters")

    registered = models.DateField(
        verbose_name=_("Registered"),
        default=django.utils.timezone.now)
    recruiter_id = models.PositiveIntegerField(
        verbose_name=_("Recruiter ID"),
        blank=False, unique=True)
    firstname = models.CharField(
        verbose_name=_("First name"),
        max_length=40, blank=False)
    surname = models.CharField(
        verbose_name=_("Surname"),
        max_length=40, blank=False)
    email = models.CharField(
        verbose_name=_("Email"),
        max_length=40, blank=True)
    telephone = models.CharField(
        verbose_name=_("Telephone"),
        max_length=30, blank=True)
    note = models.TextField(
        verbose_name=_("Note"),
        max_length=3000, blank=True)
    problem = models.BooleanField(
        verbose_name=_("Problem"),
        help_text=_("Check this field if there is a problem with this recruiter which "
                    "only be resolved later or by somebody else. Uncheck as soon as the problem is "
                    "resolved. If the problem is of permanent nature and no further action "
                    "is needed, leave it unchecked and lower the rating bellow accordingly."),
        default=False)
    rating = models.IntegerField(
        verbose_name=_("Rating"),
        help_text=_("5 = ordinary (modestly good), 0 = hopelessly bad "
                    "10 = excelent much above average"),
        choices=[(i, str(i)) for i in range(0, 11)],
        default=5,
        blank=False)
    campaigns = models.ManyToManyField(Campaign,
                                       help_text=_("Associated campaigns"),
                                       blank=True,
                                       editable=True)

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
        max_length=100, blank=False)
    name = models.CharField(
        verbose_name=_("Name"),
        help_text=_("Name of the source"),
        max_length=100, blank=False)
    direct_dialogue = models.BooleanField(
        verbose_name=_("Is from Direct Dialogue"),
        default=False)

    def __str__(self):
        return str(self.name)


class UserProfile(models.Model):
    GENDER = (
        ('male', _('Male')),
        ('female', _('Female')),
        ('unknown', _('Unknown')))
    LANGUAGE = (
        # TODO: List of languages used in the club should come from app settings
        ('cs', _('Czech')),
        ('en', _('English')))
    user = models.OneToOneField(
        User,
        related_name='userprofile',
        unique=True,
        null=False,
        on_delete=models.CASCADE,
        blank=False,
    )
    campaigns = models.ManyToManyField(
        Campaign,
        help_text=_("Associated campaigns"),
        blank=True,
        editable=True)
    title_after = models.CharField(
        verbose_name=_("Title after name"),
        max_length=15, blank=True)
    title_before = models.CharField(
        verbose_name=_("Title before name"),
        max_length=15, blank=True)
    sex = models.CharField(
        verbose_name=_("Gender"),
        choices=GENDER,
        max_length=50)
    addressment = models.CharField(
        verbose_name=_("Addressment in letter"),
        max_length=40, blank=True)
    addressment_on_envelope = models.CharField(
        verbose_name=_("Addressment on envelope"),
        max_length=40, blank=True)
    language = models.CharField(
        verbose_name=_("Language"),
        help_text=_("This is the language which will be used to "
                    "communicate with this user. The system will send "
                    "emails in this language and administrators will use "
                    "this language in phone calls and personal contacts."),
        choices=LANGUAGE,
        default="cs",
        max_length=50)
    telephone = models.CharField(
        verbose_name=_("Telephone"),
        max_length=30, blank=True)
    street = models.CharField(
        verbose_name=_("Street and number"),
        max_length=80, blank=True)
    city = models.CharField(
        verbose_name=_("City/City part"),
        max_length=40, blank=True)
    country = models.CharField(
        verbose_name=_("Country"),
        # TODO: Default country should come from app settings
        default=u"Česká republika",
        max_length=40, blank=True)
    zip_code = models.CharField(
        verbose_name=_("ZIP Code"),
        max_length=10, blank=True)
    different_correspondence_address = models.BooleanField(
        verbose_name=_("Different correspondence address"),
        help_text=_("User has different correspondence address"),
        default=False)
    other_support = models.TextField(
        verbose_name=_("Other support"),
        help_text=_(
            "If the user supports us in other ways, please specify here."),
        max_length=500, blank=True)
    public = models.BooleanField(
        verbose_name=_("Publish my name in the list of supporters"),
        default=True)
    profile_text = models.TextField(
        verbose_name=_("What is your reason?"),
        help_text=_("Tell others why you support Auto*Mat"),
        max_length=3000, blank=True, null=True)
    profile_picture = stdimage.StdImageField(
        verbose_name=_("Profile picture"),
        help_text=_("Your profile picture, which others will see."),
        upload_to='profile-images',
        variations={
            'thumbnail': (100, 100, True),
        },
        blank=True, null=True)
    # Benefits
    club_card_available = models.BooleanField(
        verbose_name=_("Club card available"),
        default=False, help_text=_("Is he entitled to posses a club card?"))
    club_card_dispatched = models.BooleanField(
        verbose_name=_("Club card dispatched?"),
        help_text=_("Did we send him the club card already?"),
        default=False)
    other_benefits = models.TextField(
        verbose_name=_("Other benefits"),
        help_text=_("Did he receive some other benefits?"),
        max_length=500, blank=True)
    # -- Notes (club administrators private notes)
    note = models.TextField(
        verbose_name=_("Note for making a boring form more lively"),
        max_length=2000, blank=True)
    created = models.DateTimeField(
        verbose_name=_(u"Datum vytvoření"),
        auto_now_add=True,
        null=True,
    )
    updated = models.DateTimeField(
        verbose_name=_(u"Datum poslední změny"),
        auto_now=True,
        null=True,
    )

    def person_name(self):
        if hasattr(self, 'user'):
            return " ".join((self.user.last_name, self.user.first_name))
        else:
            return "UserProfile: %s " % self.id
    person_name.short_description = _("Full name")

    def __str__(self):
        return str(self.person_name())


class UserInCampaign(models.Model):
    """Club user model and DB table"""

    class Meta:
        verbose_name = _("User in campaign")
        verbose_name_plural = _("Users in campaign")
        ordering = ("userprofile__user__last_name", "userprofile__user__last_name")

    GENDER = (
        ('male', _('Male')),
        ('female', _('Female')),
        ('unknown', _('Unknown')))
    REGULAR_PAYMENT_FREQUENCIES = (
        ('monthly', _('Monthly')),
        ('quaterly', _('Quaterly')),
        ('biannually', _('Bianually')),
        ('annually', _('Anually')))

    # -- Basic personal information
    userprofile = models.ForeignKey(
        UserProfile,
        blank=True,
        on_delete=models.CASCADE,
        null=True,
    )
    campaign = models.ForeignKey(
        Campaign,
        help_text=_("Campaign"),
        default=None,
        blank=True,
        on_delete=models.CASCADE,
        null=True,
        editable=True)
    # -- Additional Info
    knows_us_from = models.CharField(
        verbose_name=_("Where does he/she know us from?"),
        max_length=80, blank=True)
    why_supports = models.TextField(
        verbose_name=_("Why does he/she support us?"),
        max_length=500, blank=True)
    field_of_work = models.CharField(
        verbose_name=_("Field of work"),
        help_text="His/her area of expertise and/or interest",
        max_length=80, blank=True)
    source = models.ForeignKey(
        Source,
        verbose_name=_("Source"),
        help_text=_("How did he contact us / became a member? In direct dialog, please distinguish "
                    "between partial form (he still needs to send a permanent order into his bank) "
                    "and full form (we are going to submit his form directly into bank, no further "
                    "action is needed from him)."),
        max_length=80, blank=True, null=True, default=None, on_delete=models.SET_NULL)
    additional_information = models.TextField(
        verbose_name=_("Additional information"),
        max_length=500, blank=True)
    # -- Support
    variable_symbol = models.CharField(
        verbose_name=_("Variable symbol"),
        default="",
        unique=True,
        max_length=30, blank=False)
    registered_support = models.DateTimeField(
        verbose_name=_("Registered support"),
        help_text=_("When did this user register to support us"),
        default=django.utils.timezone.now,
        blank=True)
    exceptional_membership = models.BooleanField(
        verbose_name=_("Exceptional membership"),
        help_text=_("In special cases, people can become members of "
                    "the club even if they do not pay any money. This should "
                    "be justified in the note."),
        default=False)
    regular_payments = models.BooleanField(
        verbose_name=_("Regular payments"),
        help_text=_("Is this user registered for regular payments?"),
        default=False)
    old_account = models.BooleanField(
        verbose_name=_("Old account"),
        help_text=_("User has old account"),
        default=False)
    # TODO: This needs to be replaced by amount and periodicity fields to
    # account also for quaterly and annual payments
    regular_amount = models.PositiveIntegerField(
        verbose_name=_("Regularly (amount)"),
        help_text=_(u"Minimum yearly payment is 1800 Kč"),
        blank=True, null=True)
    regular_frequency = models.CharField(
        verbose_name=_("Frequency of regular payments"),
        choices=REGULAR_PAYMENT_FREQUENCIES,
        max_length=20, blank=True, null=True)
    expected_date_of_first_payment = models.DateField(
        verbose_name=_("Expected date of first payment"),
        help_text=("When should the first payment arrive on our account"),
        blank=True, null=True)
    other_support = models.TextField(
        verbose_name=_("Other support"),
        help_text=_(
            "If the user supports us in other ways, please specify here."),
        max_length=500, blank=True)

    # -- Notes (club administrators private notes)
    note = models.TextField(
        verbose_name=_("Note for making a boring form more lively"),
        max_length=2000, blank=True)
    verified = models.BooleanField(
        _("Verified"),
        help_text=_("Was the the user information verified by a club administrator?"),
        default=False)
    verified_by = models.ForeignKey(
        'auth.User',
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
        blank=False)
    updated = models.DateTimeField(
        verbose_name=_(u"Datum poslední změny"),
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
        default=True)
    wished_welcome_letter = models.BooleanField(
        verbose_name=_("Send welcome letter"),
        default=True)
    wished_information = models.BooleanField(
        verbose_name=_("Send regular news via email"),
        default=True)
    end_of_regular_payments = models.DateField(
        verbose_name=_("End of regular payments (for payments by card)"),
        blank=True,
        null=True,
        )

    def __str__(self):
        return str(self.person_name())

    def person_name(self):
        if hasattr(self, 'userprofile') and hasattr(self.userprofile, 'user'):
            return self.userprofile.__str__()
        else:
            return "UserInCampaign: %s " % self.id
    person_name.short_description = _("Full name")

    def requires_action(self):
        """Return true if the user requires some action from
        the club manager, otherwise return False"""
        if len(Communication.objects.filter(user=self, dispatched=False)) > 0:
            return True
        else:
            return False

    def is_direct_dialogue(self):
        if self.source:
            return self.source.direct_dialogue
        else:
            return False

    def payments(self):
        return Payment.objects.filter(user=self)

    @denormalized(models.IntegerField, null=True)
    @depend_on_related('Payment', foreign_key="user")
    def number_of_payments(self):
        """Return number of payments made by this user
        """
        return self.payment_set.aggregate(count=Count('amount'))['count']
    number_of_payments.short_description = _("# payments")
    number_of_payments.admin_order_field = 'payments_number'

    def last_payment_function(self):
        """Return last payment"""
        return self.payments().order_by('date').last()

    @denormalized(models.ForeignKey, to='Payment', default=None, null=True, related_name="user_last_payment", on_delete=models.SET_NULL)
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
    last_payment_date.short_description = _("Last payment")
    last_payment_date.admin_order_field = 'last_payment__date'

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
        interval_in_days = {'monthly': 31,
                            'quaterly': 92,
                            'biannually': 183,
                            'annually': 366}
        try:
            return datetime.timedelta(days=interval_in_days[self.regular_frequency])
        except KeyError:
            return None

    @denormalized(models.DateField, null=True)
    @depend_on_related('Payment', foreign_key="user")
    def expected_regular_payment_date(self):
        last_payment = self.last_payment_function()
        if last_payment:
            last_payment_date = last_payment.date
        else:
            last_payment_date = None
        if not self.regular_payments:
            return None
        if last_payment_date:
            # Exactly a month after last payment or whatever
            # expectation record for the given user is set to
            freq = self.regular_frequency_td()
            if not freq:
                return None
            expected = last_payment_date+freq
            if self.expected_date_of_first_payment:
                expected = max(expected, self.expected_date_of_first_payment)
        elif self.expected_date_of_first_payment:
            # Expected date + 3 days tolerance on user side
            expected = self.expected_date_of_first_payment+datetime.timedelta(days=3)
        else:
            # Registration + month (always, even for quaterly and annual payments)
            expected = self.registered_support.date()+datetime.timedelta(days=31)
        return expected

    def regular_payments_delay(self):
        """Check if his payments are OK

        Return True if so, otherwise return the delay in payment as dattime.timedelta
        """
        expected_regular_payment_date = self.expected_regular_payment_date
        if self.regular_payments and expected_regular_payment_date:
            # Check for regular payments
            # (Allow 7 days for payment processing)
            if expected_regular_payment_date:
                expected_with_tolerance = expected_regular_payment_date + datetime.timedelta(days=10)
                if (expected_with_tolerance <
                        datetime.date.today()):
                    return datetime.date.today()-expected_with_tolerance
                else:
                    return False
        else:
            return False

    @denormalized(models.IntegerField, null=True)
    @depend_on_related('Payment', foreign_key="user")
    def extra_money(self):
        """Check if we didn't receive more money than expected"""
        if self.regular_payments:
            freq = self.regular_frequency_td()
            if not freq:
                return None
            total = sum([p.amount for p in Payment.objects.filter(
                        user=self, date__gt=datetime.date.today() - freq +
                        datetime.timedelta(days=3))])
            if self.regular_amount and total > self.regular_amount:
                return total - self.regular_amount
        return None

    def regular_payments_info(self):
        if not self.regular_payments:
            return _boolean_icon(False)
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

    def mail_communications_count(self):
        return self.communications.filter(method="mail").count()

    @denormalized(models.FloatField, null=True)
    @depend_on_related('Payment', foreign_key="user")
    def payment_total(self):
        return self.payment_set.aggregate(sum=Sum('amount'))['sum'] or 0

    def total_contrib_string(self):
        """Return the sum of all money received from this user
        """
        return mark_safe(u"%s&nbsp;Kč" % intcomma(int(self.payment_total)))
    total_contrib_string.short_description = _("Total")
    total_contrib_string.admin_order_field = 'payment_total'

    def registered_support_date(self):
        return self.registered_support.strftime('%d. %m. %Y')
    registered_support_date.short_description = _("Registration")
    registered_support_date.admin_order_field = 'registered_support'

    def payment_total_range(self, from_date, to_date):
        return self.payment_set.filter(date__gte=from_date, date__lte=to_date).aggregate(sum=Sum('amount'))['sum'] or 0

    def save(self, *args, **kwargs):
        """Record save hook

        Perform a check for automated communications. Since the state of this
        user was changed, a new communication might arrise from this
        situation. See module 'autocom'.
        """
        if self.pk is None:
            insert = True
        else:
            insert = False
        super().save(*args, **kwargs)
        from .autocom import check as autocom_check
        autocom_check(users=UserInCampaign.objects.filter(pk=self.pk), action=(insert and 'new-user' or None))

    def make_tax_confirmation(self, year):
        amount = self.payment_set.exclude(type='expected').filter(date__year=year).aggregate(Sum('amount'))['amount__sum']
        if not amount:
                return
        temp = NamedTemporaryFile()
        name = u"%s %s" % (self.userprofile.user.first_name, self.userprofile.user.last_name)
        addr_city = u"%s %s" % (self.userprofile.zip_code, self.userprofile.city)
        confirmation.makepdf(temp, name, self.userprofile.sex, self.userprofile.street, addr_city, year, amount)
        try:
                conf = TaxConfirmation.objects.get(user=self, year=year)
        except TaxConfirmation.DoesNotExist:
                conf = TaxConfirmation(user=self, year=year)
        conf.file = File(temp)
        conf.amount = amount
        conf.save()
        return conf

    @denormalized(models.NullBooleanField, null=True)
    @depend_on_related('Payment', foreign_key="user")
    def no_upgrade(self):
        """Check for users without upgrade to payments

        Returns true if:
        1. user is regular at least for the last year
        2. user didn't increase the amount of his payments during last year

        This really only makes sense for monthly payments.
        """
        if not self.regular_payments:
            return False
        payment_now = self.last_payment_function()
        if ((not payment_now) or
                (payment_now.date < (datetime.date.today() - datetime.timedelta(days=45)))):
            return False
        payments_year_before = Payment.objects.filter(
            user=self,
            date__lt=datetime.datetime.now()-datetime.timedelta(days=365)
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
            'annually': 1}
        if self.regular_frequency and self.regular_amount:
            return self.regular_amount * times[self.regular_frequency]
        else:
            return 0

    def monthly_regular_amount(self):
        return float(self.yearly_regular_amount()) / 12.0


def filter_by_condition(queryset, cond):
    # Hack: It would be better to work directly on the objects
    # of the queryset rather than extracting ids from another
    # DB query and then filtering the former queryset
    return queryset.filter(cond.get_query())


class NewUserManager(models.Manager):
    def get_queryset(self):
        return super(NewUserManager, self).get_queryset().filter(verified=False)


class NewUser(UserInCampaign):
    objects = NewUserManager()

    class Meta:
        proxy = True
        verbose_name = _("new user")
        verbose_name_plural = _("new users")


class UserYearPayments(UserInCampaign):

    def get_queryset(self):
        return super(NewUserManager, self).get_queryset().filter(verified=False)

    class Meta:
        proxy = True
        verbose_name = _("Payment for users in time period")
        verbose_name_plural = _("Payments for users in time periods")


def str_to_datetime(date):
    return datetime.date(
        **dict(zip(
            ['day', 'month', 'year'],
            [int(val) for val in date.split('.')])))


class AccountStatements(models.Model):
    """AccountStatemt entry and DB model

    Account statements serve primarily to load data into the Payments
    table. The loaded files are then archived for later evidence.
    """

    class Meta:
        verbose_name = _("Account Statement")
        verbose_name_plural = _("Account Statements")
        ordering = ['-import_date']

    TYPE_OF_STATEMENT = (
        ('account', _('Account statement')),
        ('darujme', 'Darujme.cz'),
    )

    type = models.CharField(max_length=20, choices=TYPE_OF_STATEMENT)
    import_date = models.DateField(auto_now=True)
    csv_file = models.FileField(
        upload_to='account-statements')
    date_from = models.DateField(
        blank=True, null=True)
    date_to = models.DateField(
        blank=True, null=True)

    def clean(self, *args, **kwargs):
        super(AccountStatements, self).clean(*args, **kwargs)
        if not self.pk:  # new Account statement
            if self.type == 'account':
                self.payments = self.parse_bank_csv()
            elif self.type == 'darujme':
                from aklub.darujme import parse_darujme
                self.payments, self.skipped_payments = parse_darujme(self.csv_file)

    def save(self, *args, **kwargs):
        super(AccountStatements, self).save(*args, **kwargs)
        if hasattr(self, "payments"):
            for payment in self.payments:
                payment.account_statement = self
                payment.save()

    def pair_vs(self, payment):
        # Payments pairing'
        if payment.VS == '':
            payment.VS = None
        else:
            users_with_vs = UserInCampaign.objects.filter(variable_symbol=payment.VS)
            if len(users_with_vs) == 1:
                payment.user = users_with_vs[0]
            elif len(users_with_vs) > 1:
                raise Exception(
                    "Duplicit variable symbol (%s) detected "
                    "for users: %s!" %
                    (payment.VS, ",".join(
                        [str(user) for user in users_with_vs])))

    def parse_bank_csv(self):
        # Read and parse the account statement
        # TODO: This should be separated into a dedicated module
        payments_reader = csv.DictReader(
            codecs.iterdecode(self.csv_file, 'utf-8'),
            delimiter=';',
            fieldnames=[
                'operation_id', 'date', 'amount', 'currency', 'account', 'account_name',
                'bank_code', 'bank_name', 'KS', 'VS',
                'SS', 'user_identification', 'recipient_message', 'transfer_type', 'done_by',
                'specification', 'transfer_note', 'BIC', 'order_id'
                ])
        payments = []
        in_header = True

        for payment in payments_reader:
            if in_header:
                header_line = payment["operation_id"]
                logger.debug(header_line)
                if header_line.startswith("Období:"):
                    name, date_start, dash, date_end = header_line.split()
                    self.date_from = str_to_datetime(date_start)
                    self.date_to = str_to_datetime(date_end)
                    super(AccountStatements, self).save()

                if header_line == "ID operace":
                    in_header = False
                    continue
            else:
                logger.debug(payment)
                logging.debug("PAYMENT %s" % payment)
                logging.debug(payment['date'])
                d, m, y = payment['date'].split('.')
                payment['date'] = "%04d-%02d-%02d" % (int(y), int(m), int(d))
                payment['amount'] = int(round(float(
                    payment['amount'].replace(',', '.').replace(' ', ''))))
                if payment['amount'] < 0:
                    # Skip transfers from the club account,
                    # only process contributions
                    continue
                p = Payment(**payment)
                self.pair_vs(p)
                p.type = 'bank-transfer'
                p.account_statement = self
                payments.append(p)
        return payments

    def __str__(self):
        return "%s (%s)" % (self.pk, self.import_date)


class Payment(models.Model):
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
        ('darujme', 'Darujme.cz'),
        )

    date = models.DateField(
        verbose_name=_("Date of payment"))
    amount = models.PositiveIntegerField(
        verbose_name=_("Amount"),
        help_text=_("Amount of money in the main used curency"))
    account = models.CharField(
        verbose_name=("Account"),
        help_text=_("Bank account from which money was received"),
        max_length=100, blank=True)
    bank_code = models.CharField(
        verbose_name=_("Bank code"),
        help_text=_("Code of bank from which money was received"),
        max_length=30, blank=True)
    VS = models.CharField(
        verbose_name=_("VS"),
        help_text=_("Variable symbol"),
        max_length=30, blank=True, null=True)
    SS = models.CharField(
        _("SS"),
        help_text=_("Specific symbol"),
        max_length=30, blank=True)
    KS = models.CharField(
        verbose_name=_("CS"),
        help_text=_("Constant symbol"),
        max_length=30, blank=True)
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
        max_length=30, blank=True)
    type = models.CharField(
        verbose_name=_("Type"),
        help_text=_("Type of payment"),
        choices=TYPE_OF_PAYMENT,
        max_length=200, blank=True)
    done_by = models.CharField(
        verbose_name=_("Done by"),
        help_text=_("This is a column imported from the account statements. "
                    "It's purpose is not clear. It has been usually blank on "
                    "the account statement we have received so far."),
        max_length=500, blank=True)
    account_name = models.CharField(
        verbose_name=_("Account name"),
        max_length=200, blank=True)
    bank_name = models.CharField(
        verbose_name=_("Bank name"),
        max_length=500, blank=True)
    transfer_note = models.CharField(
        verbose_name=_("Transfer note"),
        max_length=200, blank=True, null=True)
    currency = models.CharField(
        verbose_name=_("Currency"),
        max_length=200, blank=True, null=True)
    recipient_message = models.CharField(
        verbose_name=_("Recipient message"),
        max_length=200, blank=True, null=True)
    operation_id = models.CharField(
        verbose_name=_("Operation ID"),
        max_length=200, blank=True, null=True)
    transfer_type = models.CharField(
        verbose_name=_("Transfer type"),
        max_length=200, blank=True, null=True)
    specification = models.CharField(
        verbose_name=_("Specification"),
        max_length=200, blank=True, null=True)
    order_id = models.CharField(
        verbose_name=_("Order ID"),
        max_length=200, blank=True, null=True)
    # Pairing of payments with a specific club system user
    user = models.ForeignKey(
        UserInCampaign,
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

    def person_name(self):
        """Return name of the payer"""
        if self.user:
            return self.user.person_name()

    def paired_with_expected(self):
        """Return if the payment is paired with an expected payment

        Expected payments are of two types:

        1) Single individual payments, that were previously registered as
        'expected'
        2) Payments expected implicitly because the user is a regular
        contributor
        """
        # TODO: Logic to say if this payment was expected and processed correctly
        if self.user:
            return True
        else:
            return False

    def save(self, *args, **kwargs):
        if self.pk is None:
            insert = True
        else:
            insert = False
        super(Payment, self).save(*args, **kwargs)
        if self.user:
            # Evaluate autocom immediatelly only when the affected
            # user is known, otherwise the bellow check would be too
            # time-consuming (relying on Cron performing it in regular
            # intervals anyway)
            from .autocom import check as autocom_check
            autocom_check(users=UserInCampaign.objects.filter(pk=self.user.pk), action=(insert and 'new-payment' or None))

    def __str__(self):
        return str(self.amount)

COMMUNICATION_METHOD = (
    ('email', _("Email")),
    ('phonecall', _("Phonecall")),
    ('mail', _("Mail")),
    ('personal', _("Personal")),
    ('internal', _("Internal")),
)

COMMUNICATION_TYPE = (
    ('mass', _("Mass")),
    ('auto', _("Automatic")),
    ('individual', _("Individual")),
)


class Communication(models.Model):
    """Communication entry and DB Model

    A communication is one action in the dialog between the club
    administration and the user. Communication can have various forms,
    e.g. email, phonecall or snail mail. Some communications are
    dispatched automatically, others on confirmation or entirely
    manually by the club administration.
    """

    class Meta:
        verbose_name = _("Communication")
        verbose_name_plural = _("Communications")
        ordering = ['date']

    user = models.ForeignKey(
        UserInCampaign,
        on_delete=models.CASCADE,
        related_name="communications",
    )
    method = models.CharField(
        verbose_name=_("Method"),
        max_length=30, choices=COMMUNICATION_METHOD)
    type = models.CharField(
        verbose_name=_("Type of communication"),
        max_length=30, choices=COMMUNICATION_TYPE,
        default='individual')
    date = models.DateTimeField(
        verbose_name=_("Date"))
    subject = models.CharField(
        verbose_name=_("Subject"),
        help_text=_("The topic of this communication"),
        max_length=100)
    summary = models.TextField(
        verbose_name=_("Text"),
        help_text=_("Text or summary of this communication"),
        max_length=50000)
    attachment = models.FileField(
        verbose_name=_("Attachment"),
        upload_to='communication-attachments',
        blank=True, null=True
        )
    note = models.TextField(
        verbose_name=_("Notes"),
        help_text=_("Internal notes about this communication"),
        max_length=3000, blank=True)
    created_by = models.ForeignKey(
        'auth.User',
        verbose_name=_("Created by"),
        related_name='created_by_communication',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    handled_by = models.ForeignKey(
        'auth.User',
        verbose_name=_("Last handled by"),
        related_name='handled_by_communication',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    send = models.BooleanField(
        verbose_name=_("Send / Handle"),
        help_text=_("Request sending or resolving this communication. For emails, this means that "
                    "the email will be immediatelly sent to the user. In other types of "
                    "communications, someone must handle this manually."),
        default=False)
    dispatched = models.BooleanField(
        verbose_name=_("Dispatched / Done"),
        help_text=_("Was this message already sent, communicated and/or resolved?"),
        default=False)

    def save(self, *args, **kwargs):
        """Record save hook

        If state of the dispatched field changes to True, call
        the automated dispatch() method.
        """
        if self.send:
            self.dispatch(save=False)  # then try to dispatch this email automatically
        super(Communication, self).save(*args, **kwargs)

    def dispatch(self, save=True):
        """Dispatch the communication

        Currently only method 'email' is implemented, all other methods will be only saved. For these messages, the
        email is sent via the service configured in application settings.

        TODO: Implement 'mail': the form with the requested text should be
        typeseted and the admin presented with a 'print' button. Address for
        filling on the envelope should be displayed to the admin.
        """
        if self.method == 'email':
            if self.type == 'mass':
                bcc = []
            else:
                bcc = ['kp@auto-mat.cz']

            email = EmailMultiAlternatives(
                subject=self.subject,
                body=self.summary_txt(),
                from_email='Klub pratel Auto*Matu <kp@auto-mat.cz>',
                to=[self.user.userprofile.user.email],
                bcc=bcc)
            if self.type != 'individual':
                email.attach_alternative(self.summary, "text/html")
            if self.attachment:
                att = self.attachment
                email.attach(os.path.basename(att.name), att.read())
            try:
                email.send(fail_silently=False)
            except:
                # TODO: At least warn about it!
                pass
            else:
                self.dispatched = True
            self.send = False
            if save:
                self.save()
        else:
            self.dispatched = True
            self.send = False
            if save:
                self.save()

    def summary_txt(self):
        if self.type == 'individual':
            return self.summary
        else:
            return html2text.html2text(self.summary)


class ConditionValues(object):
    """Iterator that returns values available for Klub Conditions

    Returns tuples (val, val) where val is a string of the form
    model.cid where model is the name of the model in lower case
    and cid is the database column id (name).

    This class is needed to be able to dynamically generate
    a list of values selectable in the Condition forms by
    dynamically introspecting the User and Payment models.
    """

    def __init__(self, model_names):
        self._columns = []
        # Special attributes
        self._columns += [('action', None, _(u"Action"), 'CharField', ('daily', 'new-user', 'new-payment'))]
        # Models attributes
        for name in model_names:
            model = {'UserInCampaign': UserInCampaign,
                     'Payment': Payment,
                     'UserInCampaign.source': Source,
                     'UserInCampaign.last_payment': Payment,
                     }[name]
            # DB fields
            self._columns += [
                (name, field.name, string_concat(name, " ", field.verbose_name), field.get_internal_type(), list(zip(*field.choices))[0] if field.choices else "")
                for field in model._meta.fields]
        self._columns.sort()
        self._index = 0

    def __iter__(self):
        return self

    def __next__(self):
        try:
            name, secondary_name, verbose_name, condition_type, choices = self._columns[self._index]
            if secondary_name:
                val = name+"."+secondary_name
            else:
                val = name
            name = u"%s: %s %s" % (verbose_name, condition_type, choices)
            self._index = self._index + 1
            return (val, name)
        except IndexError:
            raise StopIteration


class Condition(models.Model):
    """A condition entry and DB model

    Conditions are composed of the left hand side, an operator
    and the right hand side.

    Possible values for either side are:
    1) a value (string, integer...)
    2) a symbolic value -- variable, special value or reference to DB
    (e.g. u.regular)
    3) another condition

    Only one type of left and one type of right hand side value is permitted.
    Not all operators will work with all types of values (e.g. logic operators
    only work on other conditions on both sides)
    """

    class Meta:
        verbose_name = _("Condition")
        verbose_name_plural = _("Conditions")

    OPERATORS = (
        ('and', _(u'and')),
        ('or', _(u'or')),
        ('nor', _(u'nor')),
        )

    name = models.CharField(
        verbose_name=_("Name of condition"),
        max_length=200, blank=False, null=True)
    # One of variable or conds must be non-null
    operation = models.CharField(
        verbose_name=_("Operation"),
        choices=OPERATORS,
        max_length=30)
    conds = models.ManyToManyField('self',
                                   related_name='conds_rel',
                                   symmetrical=False,
                                   verbose_name=_("Conditions"),
                                   blank=True)
    as_filter = models.BooleanField(
        verbose_name=_("Display as filter?"),
        help_text=_("Determines whether this condition is available as a filter"
                    "in the table of Users"),
        default=False)
    on_dashboard = models.BooleanField(
        verbose_name=_("Display on dashboard?"),
        help_text=_("Determines whether this condition is available on dashboard"),
        default=False)

    def __str__(self):
        return str(self.name)

    def get_query(self, action=None):
        operation_dict = {
            'and': lambda x, y: x & y,
            'or': lambda x, y: x | y,
            'nor': lambda x, y: x | y,
        }
        ret_cond = None
        for cond in self.conds.all():
            if ret_cond:
                ret_cond = operation_dict[self.operation](ret_cond, cond.get_query(action))
            else:
                ret_cond = cond.get_query(action)
        for tcond in self.terminalcondition_set.all():
            if ret_cond:
                ret_cond = operation_dict[self.operation](ret_cond, tcond.get_query(action))
            else:
                ret_cond = tcond.get_query(action)

        if self.operation == 'nor':
            return ~(ret_cond)
        else:
            return ret_cond

    def condition_string(self):
        prefix = ""
        sufix = ""
        if self.operation == 'nor':
            prefix = "not("
            sufix = ")"
            op_string = " or "
        else:
            op_string = " %s " % self.operation

        condition_list = [condition.condition_string() for condition in self.conds.all()]
        terminalcondition_list = [str(condition) for condition in self.terminalcondition_set.all()]
        return "%s%s(%s)%s" % (
            prefix,
            self.name,
            op_string.join(condition_list + terminalcondition_list),
            sufix
            )


class TerminalCondition(models.Model):
    """A terminal condition entry and DB model

    Terminal conditions are composed of the left hand side, an operator
    and the right hand side.

    Possible values for either side are:
    1) a value (string, integer...)
    2) a symbolic value -- variable, special value or reference to DB
    (e.g. u.regular)

    Only one type of left and one type of right hand side value is permitted.
    Not all operators will work with all types of values (e.g. logic operators
    only work on other conditions on both sides)
    """

    class Meta:
        verbose_name = _("Terminal condition")
        verbose_name_plural = _("Terminal conditions")

    OPERATORS = (
                ('=', u'='),
                ('!=', u'≠'),
                ('>', '>'),
                ('<', '<'),
                ('>=', u'≤'),
                ('<=', u'≤'),
                ('containts', _(u'contains')),
                ('icontaints', _(u'contains (case insensitive)')),
    )

    variable = models.CharField(
        verbose_name=_("Variable"),
        choices=ConditionValues(('UserInCampaign', 'UserInCampaign.source', 'UserInCampaign.last_payment')),
        help_text=_("Value or variable on left-hand side"),
        max_length=50, blank=True, null=True)
    operation = models.CharField(
        verbose_name=_("Operation"),
        choices=OPERATORS,
        max_length=30)
    # One of value or conds must be non-null
    value = models.CharField(
        verbose_name=_("Value"),
        help_text=_(
            "Value or variable on right-hand side. <br/>"
            "\naction: daily, new-user<br/>"
            "\nDateField: month_ago, one_day, one_week, two_weeks, one_month<br/>"
            "\nBooleanField: True, False"),
        max_length=50, blank=True, null=True)
    condition = models.ForeignKey(
        Condition,
        on_delete=models.CASCADE,
    )

    def variable_description(self):
        if self.variable:
            try:
                return unicode(UserInCampaign._meta.get_field(self.variable.split(".")[1]).help_text)
            except:
                try:
                    return eval(self.variable).__doc__
                except:
                    return "action"

    def get_val(self, spec):
        if '.' in spec:
            variable, value = spec.split('.')
        else:
            variable = spec

        spec_dict = {
            'month_ago': datetime.datetime.now()-datetime.timedelta(days=30),
            'one_day': datetime.timedelta(days=1),
            'one_week': datetime.timedelta(days=7),
            'two_weeks': datetime.timedelta(days=14),
            'one_month': datetime.timedelta(days=31),
            'datetime': lambda value: datetime.datetime.strptime(value, '%Y-%m-%d %H:%M'),
            'timedelta': lambda value: datetime.timedelta(days=int(value)),
            'days_ago': lambda value: datetime.datetime.now() - datetime.timedelta(days=int(value)),
            'true': True,
            'false': False,
            'None': None,
        }
        if variable in spec_dict:
            expression = spec_dict[variable]
            if hasattr(expression, "__call__"):  # is function
                return spec_dict[variable](value)
            else:
                return spec_dict[variable]
        else:
            try:
                return int(spec)
            except (TypeError, ValueError):
                return spec

    def get_querystring(self, spec, operation):
        spec_ = spec.split('.')
        if spec_[0] != 'UserInCampaign':
            NotImplementedError("Unknown spec %s" % spec_[0])

        join_querystring = "__".join(spec_[1:])

        if operation == '=' or operation == '!=':
            return join_querystring
        elif operation == '<':
            return join_querystring + "__lt"
        elif operation == '>':
            return join_querystring + "__gt"
        elif operation == 'contains':
            return join_querystring + "__contains"
        elif operation == 'icontains':
            return join_querystring + "__icontains"
        elif operation == '<=':
            return join_querystring + "__lte"
        elif operation == '>=':
            return join_querystring + "__gte"
        else:
            NotImplementedError("Unknown operation %s" % operation)

    def get_query(self, action=None):
        if self.variable == 'action':
            if self.value == action:
                return Q()
            else:
                return Q(pk__in=[])  # empty set

        # Elementary conditions
        left = self.get_querystring(self.variable, self.operation)
        right = self.get_val(self.value)
        if self.operation == '!=':
            return ~Q(**{left: right})
        else:
            return Q(**{left: right})

    def __str__(self):
        return "%s %s %s" % (self.variable, self.operation, self.value)


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
        blank=False, null=True)
    condition = models.ForeignKey(
        Condition,
        null=True,
        on_delete=models.SET_NULL,
    )
    method = models.CharField(
        verbose_name=_("Method"),
        max_length=30,
        choices=COMMUNICATION_METHOD)
    subject = models.CharField(
        verbose_name=_("Subject"),
        max_length=100)
    subject_en = models.CharField(
        verbose_name=_("English subject"),
        max_length=100,
        blank=True, null=True)
    template = models.TextField(
        verbose_name=_("Template"),
        help_text=_("Template can contain variable substitutions like addressment, name, "
                    "variable symbol etc."),
        max_length=50000)
    template_en = models.TextField(
        verbose_name=_("English template"),
        max_length=50000,
        blank=True, null=True)
    only_once = models.BooleanField(
        verbose_name=_("Only once"),
        help_text=_("If checked, never send this communication twice to one user"),
        default=True)
    dispatch_auto = models.BooleanField(
        verbose_name=_("Dispatch auto"),
        help_text=_("If checked, the communication might be dispatched by the system "
                    "(e.g. an email sent) as soon as condition becomes true, without "
                    "any further action from the administrator. If not, the communication "
                    "is created, but the administrator must send it manually."),
        default=False)
    sent_to_users = models.ManyToManyField(
        UserInCampaign,
        help_text=_(
            "List of users to whom this communication was already sent"),
        blank=True,
        )

    def __str__(self):
        return str(self.name)


class MassCommunication(models.Model):
    """MassCommunication entry and DB model"""

    class Meta:
        verbose_name = _("Mass Communication")
        verbose_name_plural = _("Mass Communications")

    name = models.CharField(
        verbose_name=_("Name"),
        max_length=50,
        blank=False, null=True)
    date = models.DateField(
        verbose_name=_("Date"),
        default=None, blank=False, null=False)
    method = models.CharField(
        verbose_name=_("Method"),
        max_length=30,
        choices=COMMUNICATION_METHOD)
    subject = models.CharField(
        verbose_name=_("Subject"),
        max_length=100)
    subject_en = models.CharField(
        verbose_name=_("English subject"),
        help_text=_("English version of the subject. If empty, English speaking users will not receive this communication."),
        max_length=100,
        blank=True, null=True)
    template = models.TextField(
        verbose_name=_("Template"),
        help_text=_(
            "Template can contain variable substitutions like addressment, name, "
            "variable symbol etc."),
        max_length=50000,
        blank=True, null=True)
    template_en = models.TextField(
        verbose_name=_("English template"),
        max_length=50000,
        blank=True, null=True)
    attachment = models.FileField(
        verbose_name=_("Attachment"),
        upload_to='mass-communication-attachments',
        blank=True, null=True)
    attach_tax_confirmation = models.BooleanField(
        verbose_name=_("Attach tax confirmation"),
        help_text=_("If this field is checked, the tax confirmation "
                    "for last year is appended to the message."),
        default=False
        )
    send_to_users = models.ManyToManyField(
        UserInCampaign,
        verbose_name=_("send to users"),
        help_text=_(
            "All users who should receive the communication"),
        limit_choices_to={'userprofile__user__is_active': 'True', 'wished_information': 'True'},
        blank=True)
    note = models.TextField(
        verbose_name=_("note"),
        help_text=_("Note"),
        max_length=500,
        blank=True, null=True)

    def __str__(self):
        return str(self.name)


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


def confirmation_upload_to(instance, filename):
        return "confirmations/%s_%s.pdf" % (instance.user.id, instance.year)


class TaxConfirmation(models.Model):

        user = models.ForeignKey(
            UserInCampaign,
            on_delete=models.CASCADE,
        )
        year = models.PositiveIntegerField()
        amount = models.PositiveIntegerField(default=0)
        file = models.FileField(upload_to=confirmation_upload_to, storage=OverwriteStorage())

        def user__regular_payments(self):
            return self.user.regular_payments

        class Meta:
            verbose_name = _("Tax confirmation")
            verbose_name_plural = _("Tax confirmations")
            unique_together = ('user', 'year',)


class StatMemberCountsByMonths(models.Model):

    class Meta:
        managed = False
        db_table = 'aklub_v_member_counts_by_months'
        verbose_name_plural = _("Members by months")

    id = models.CharField(primary_key=True, max_length=20)
    year = models.IntegerField()
    month = models.IntegerField()
    regular = models.IntegerField()
    irregular = models.IntegerField()
    total = models.IntegerField()
    run_total = models.IntegerField()


class StatPaymentsByMonths(models.Model):

    class Meta:
        managed = False
        db_table = 'aklub_v_payments_by_months'
        verbose_name_plural = _("Payments by months")

    id = models.CharField(primary_key=True, max_length=20)
    year = models.IntegerField()
    month = models.IntegerField()
    donors = models.IntegerField()
    total = models.IntegerField()
    run_total = models.IntegerField()
