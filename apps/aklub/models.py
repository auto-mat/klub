# -*- coding: utf-8 -*-
# Author: Hynek Hanke <hynek.hanke@auto-mat.cz>
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
from django.db.models import Sum, Count, Max
from django.core.mail import EmailMultiAlternatives
from django.core.files import File
from django.core.files.storage import FileSystemStorage
from django.core.files.temp import NamedTemporaryFile
from django.utils.timesince import timesince
from django.utils.translation import ugettext_lazy as _
import html2text
# External dependencies
import datetime
import csv
import os.path
import stdimage
# Local modules
import autocom
import confirmation
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

    def number_of_members(self):
        return self.members.count()
    number_of_members.short_description = _("number of members")

    def recruiters(self):
        return Recruiter.objects.filter(campaigns=self)
    recruiters.short_description = _("recruiters")

    def number_of_recruiters(self):
        return len(self.recruiters())
    number_of_recruiters.short_description = _("number of recruiters")

    def yield_total(self):
        if self.acquisition_campaign:
            return User.objects.filter(campaigns=self).aggregate(yield_total = Sum('payment__amount'))['yield_total']
        else:
            return self.real_yield
    yield_total.short_description = _("total yield")

    def expected_monthly_income(self):
        income = 0.0
        for campaign_member in User.objects.filter(campaigns=self):
            income += campaign_member.monthly_regular_amount()
        return income
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

    def __unicode__(self):
        return self.name

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
        choices=[(i, str(i)) for i in range(0,11)],
        default=5,
        blank=False)
    campaigns = models.ManyToManyField(Campaign,
                                       help_text = _("Associated campaigns"),
                                       blank=True,
                                       editable=True)
    def __unicode__(self):
        return self.person_name()

    def person_name(self):
        return " ".join(("%03d" % self.recruiter_id, self.firstname, self.surname))
    person_name.short_description = _("Name") 

class User(models.Model):
    """Club user model and DB table"""

    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        ordering = ("surname", "firstname")

    GENDER = (
        ('male', _('Male')),
        ('female', _('Female')),
        ('unknown', _('Unknown')))
    LANGUAGE = (
        # TODO: List of languages used in the club should come from app settings
        ('cs', _('Czech')), 
        ('en', _('English')))
    SOURCE = (
        ('web', _("Web form")),
        ('dpnk', _("DPNK campaign")),
        ('lead-dpnk', _("DPNK campaign - lead")),
        ('direct-dialogue-partial-form', _("Direct dialogue -- partial form (not automatic in bank)")),
        ('direct-dialogue-full-form', _("Direct dialogue -- full form (automatic in bank)")),
        ('telephone-call', _("Telephonic call")),
        ('personal', _('Personal recommendation')),
        ('darujme', 'Darujme.cz'),
        ('other', _('Another form of contact')))
    REGULAR_PAYMENT_FREQUENCIES = (
        ('monthly', _('Monthly')),
        ('quaterly', _('Quaterly')),
        ('biannually', _('Bianually')),
        ('annually', _('Anually')))
             
    # -- Basic personal information
    title_before = models.CharField(
        verbose_name=_("Title before name"),
        max_length=15, blank=True)
    firstname = models.CharField(
        verbose_name=_("First name"),
        max_length=80) # TODO AFTER DB CLEANUP: null=False
    surname = models.CharField(
        verbose_name=_("Surname"),
        max_length=80) # TODO AFTER DB CLEANUP: null=False
    title_after = models.CharField(
        verbose_name=_("Title after name"),
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
    # -- Contacts
    email = models.CharField(
        verbose_name=_("Email"),
        max_length=40, blank=True)
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
    source = models.CharField(
        verbose_name=_("Source"),
        help_text=_("How did he contact us / became a member? In direct dialog, please distinguish "
                    "between partial form (he still needs to send a permanent order into his bank) "
                    "and full form (we are going to submit his form directly into bank, no further "
                    "action is needed from him)."),
        choices=SOURCE,
        max_length=80, blank=False)
    additional_information = models.TextField(
        verbose_name=_("Additional information"),
        max_length=500, blank=True)
    # -- Support
    variable_symbol = models.CharField(
        verbose_name=_("Variable symbol"),
        default="",
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
        help_text = ("When should the first payment arrive on our account"),
        blank=True, null=True)
    other_support = models.TextField(
        verbose_name=_("Other support"),
        help_text=
        _("If the user supports us in other ways, please specify here."),
        max_length=500, blank=True)
    public = models.BooleanField(
        verbose_name=_("Publish my name in the list of supporters"),
        default=True)
    wished_tax_confirmation = models.BooleanField(
        verbose_name=_("Send tax confirmation"),
        default=True)
    wished_welcome_letter = models.BooleanField(
        verbose_name=_("Send welcome letter"),
        default=True)
    wished_information = models.BooleanField(
        verbose_name=_("Send regular news via email"),
        default=True)
    active = models.BooleanField(
        verbose_name=_("Active"),
        help_text=_("Is the user active member? Use this field to disable old "
                   "or temporary users."),
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

    # --- Communication
    
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
    campaigns = models.ManyToManyField(Campaign, 
                                       help_text = _("Associated campaigns"),
                                       related_name='members',
                                       blank=True,
                                       editable=True)
    recruiter = models.ForeignKey(Recruiter, blank=True, null=True)
    verified = models.BooleanField(
        _("Verified"),
        help_text=_("Was the the user information verified by a club administrator?"),
        default=False)
    verified_by = models.ForeignKey(
        'auth.User',
        verbose_name=_("Verified by"),
        related_name='verified_users',
        null=True, blank=True)
    activity_points = models.IntegerField(
        verbose_name=_("Activity points"),
        help_text=_("Points for users activity"),
        default=0,
        blank=False)

    # General annotation fields (some methods in this class rely on
    # the queryset being annotated as follows)
    annotations = {'payment_total': Sum('payment__amount'),
                   'payments_number': Count('payment'),
                   'last_payment_date': Max('payment__date')}
    
    def __unicode__(self):
        return self.person_name()

    def person_name(self):
        return " ".join((self.surname, self.firstname))
    person_name.short_description = _("Full name") 

    def requires_action(self):
        """Return true if the user requires some action from
        the club manager, otherwise return False"""
        if len(Communication.objects.filter(user=self, dispatched=False)) > 0:
            return True
        else:
            return False

    def is_direct_dialogue(self):
        if self.source in ['direct-dialogue-full-form', 'direct-dialogue-partial-form']:
            return True
        return False

    def payments(self):
        return Payment.objects.filter(user=self)

    def number_of_payments(self):
        """Return number of payments made by this user

        This depends on the query being previously annotated with
        self.annotations
        """
	return self.payments_number
    number_of_payments.short_description = _("# payments") 
    number_of_payments.admin_order_field = 'payments_number'
    number_of_payments.return_type = 'Integer'
    
    def last_payment(self):
        """Return last payment"""
        return self.payments().order_by('-date').last()

    def last_payment_date(self):
        """Return date of last payment or None

        This depends on the query being previously annotated with
        self.annotations
        """
	return self.last_payment_date
    last_payment_date.short_description = _("Last payment")
    last_payment_date.admin_order_field = 'last_payment_date'
    last_payment_date.return_type = "Date"

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

    def expected_regular_payment_date(self):
        last_payment_date = self.last_payment_date
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
        if self.regular_payments and self.expected_regular_payment_date():
            # Check for regular payments
            # (Allow 7 days for payment processing)
            if self.expected_regular_payment_date():
               expected_with_tolerance = self.expected_regular_payment_date() + datetime.timedelta(days=10)
               if (expected_with_tolerance
                   < datetime.date.today()):
                   return datetime.date.today()-expected_with_tolerance
               else:
                   return datetime.timedelta(days=0)
        else:
            return datetime.timedelta(days=0)
    regular_payments_delay.return_type = "TimeDelta"

    def extra_money(self):
        """Check if we didn't receive more money than expected"""
        total = 20
        if self.regular_payments:
            freq = self.regular_frequency_td()
            if not freq:
                return None
            total = sum([p.amount for p in Payment.objects.filter(
                        user=self, date__gt = datetime.date.today()-freq + \
                        + datetime.timedelta(days=3))])
            if total and self.regular_amount and total > self.regular_amount:
                return total - self.regular_amount
        return None
    extra_money.return_type = "Integer"

    def regular_payments_info(self):
        if not self.regular_payments:
            return _boolean_icon(False)
        return self.expected_regular_payment_date()
    regular_payments_info.allow_tags = True
    regular_payments_info.short_description = _(u"Expected payment")

    def payment_delay(self):
        if self.regular_payments_delay():
            return timesince(self.expected_regular_payment_date())
        else:
            return _boolean_icon(False)
    payment_delay.allow_tags = True
    payment_delay.short_description = _(u"Payment delay")

    def extra_payments(self):
        if self.extra_money():
            return self.extra_money()
        else:
            return _boolean_icon(False)
    extra_payments.allow_tags = True
    extra_payments.short_description = _(u"Extra money")

    def mail_communications_count(self):
        return self.communications.filter(method = "mail").count()

    def total_contrib(self):
        """Return the sum of all money received from this user

        This depends on the query being previously annotated with
        self.annotations
        """
	if self.payment_total:
            return str(self.payment_total) + " Kč"
        else:
            return "0 Kč"
    total_contrib.short_description = _("Total")
    total_contrib.admin_order_field = 'payment_total'
    total_contrib.return_type = "Integer"

    def registered_support_date(self):
        return self.registered_support.strftime('%d. %m. %Y')
    registered_support_date.short_description = _("Registration")
    registered_support_date.admin_order_field = 'registered_support'
    
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
        super(User, self).save(*args, **kwargs)
        autocom.check(users=[self], action=(insert and 'new-user' or None))

    def make_tax_confirmation(self, year):
	amount = self.payment_set.exclude(type='expected').filter(date__year=year).aggregate(Sum('amount'))['amount__sum']
	if not amount:
		return
	temp = NamedTemporaryFile()
	name = u"%s %s" % (self.firstname, self.surname)
	addr_city = u"%s %s" % (self.zip_code, self.city)
	confirmation.makepdf(temp, name, self.sex, self.street, addr_city, year, amount)
	try:
		conf = TaxConfirmation.objects.get(user=self,year=year)
	except TaxConfirmation.DoesNotExist:
		conf = TaxConfirmation(user=self,year=year)
	conf.file = File(temp)
        conf.amount = amount
	conf.save()
	return conf

    def no_upgrade(self):
        """Check for users without upgrade to payments

        Returns true if:
        1. user is regular at least for the last year
        2. user didn't increase the amount of his payments during last year

        This really only makes sense for monthly payments.
        """
        if self.regular_payments != True:
            return False
        payment_now = self.last_payment()
        if ((not payment_now) or
            (payment_now.date < (datetime.date.today()-datetime.timedelta(days=45)))):
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
    no_upgrade.return_type = "Boolean"

    def monthly_regular_amount(self):
        months = {
            'monthly': 1.0,
            'quaterly': 3.0,
            'biannually': 6.0,
            'annually': 12.0}
        if self.regular_frequency and self.regular_amount:
            return float(self.regular_amount) / months[self.regular_frequency]
        else:
            return 0.0

def filter_by_condition(queryset, cond):
    # Hack: It would be better to work directly on the objects
    # of the queryset rather than extracting ids from another
    # DB query and then filtering the former queryset
    all_users = User.objects.all().annotate(**User.annotations)
    filtered_ids = [user.id for user in all_users
                    if cond.is_true(user)]
    return queryset.filter(id__in=filtered_ids)

class NewUserManager(models.Manager):
    def get_queryset(self):
        return super(NewUserManager,self).get_queryset().filter(verified=False)

class NewUser(User):
    objects = NewUserManager()
    class Meta:
        proxy = True
        verbose_name = _("new user")
        verbose_name_plural = _("new users")

def str_to_datetime(date):
    return datetime.date(**dict(
        zip(['day', 'month', 'year'],
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
        if self.type == 'account':
            self.payments = self.parse_bank_csv()
        elif self.type == 'darujme':
            from aklub.darujme import parse_darujme
            self.payments, self.skipped_payments = parse_darujme(self.csv_file)

    def save(self, *args, **kwargs):
        super(AccountStatements, self).save(*args, **kwargs)
        for payment in self.payments:
            payment.account_statement = self
            payment.save()

    def parse_bank_csv(self):
        # Read and parse the account statement
        # TODO: This should be separated into a dedicated module
        win1250_contents = self.csv_file.read()
        unicode_contents = win1250_contents.decode('windows-1250')
        splitted = unicode_contents.encode('utf-8').split('\n\n')
        header = splitted[0]
        data = splitted[1]

        term_line = [line for line in header.split('\n')
                     if line.startswith("Období:")]
        name, date_start, dash, date_end = term_line[0].split()
        self.date_from = str_to_datetime(date_start)
        self.date_to = str_to_datetime(date_end)
        super(AccountStatements, self).save()

        payments_reader = csv.DictReader(data.split("\n"), delimiter=';',
                                 fieldnames = [
                'transfer', 'date', 'amount', 'account', 'bank_code', 'BIC', 'KS', 'VS',
                'SS', 'user_identification', 'type', 'done_by', 'account_name',
                'bank_name', 'unknown'
                ])

        first_line = True
        payments = []
        for payment in payments_reader:
	    #print payment
            if first_line:
                first_line = False
		#print "found first_line"
            elif payment['date'] == 'Suma':
                break
            else:
                del payment['transfer']
                del payment['unknown']
		#print "PAYMENT", payment
		#print payment['date']
                d,m,y = payment['date'].split('.')
                payment['date'] = "%04d-%02d-%02d" % (int(y),int(m),int(d))
                payment['amount'] = int(round(float(
                            payment['amount'].replace(',','.').replace(' ',''))))
                if payment['amount'] < 0:
                    # Skip transfers from the club account,
                    # only process contributions
                    continue                 
                p = Payment(**payment)
                # Payments pairing'
                if p.VS != '':
                    users_with_vs = User.objects.filter(variable_symbol=p.VS)
                    if len(users_with_vs) == 1:
                        p.user = users_with_vs[0]
                    elif len(users_with_vs) > 1:
                        raise Exception("Duplicit variable symbol (%s) detected "
                                        "for users: %s!" %
                                        (p.VS,
                                         ",".join(
                                    [str(user) for user in users_with_vs])))
                else:
                    p.VS = None
                p.type = 'bank-transfer'
                p.account_statement = self
                payments.append(p)
        return payments

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
        help_text= _("Variable symbol"),
        max_length=30, blank=True)
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
    # Pairing of payments with a specific club system user
    user = models.ForeignKey(User, blank=True, null=True)
    # Origin of payment from bank account statement
    account_statement = models.ForeignKey(AccountStatements, blank=True, null=True)

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
            autocom.check(users=[self.user], action=(insert and 'new-payment' or None))

    def __unicode__(self):
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

    user = models.ForeignKey(User,
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
        null=True, blank=True)
    handled_by = models.ForeignKey(
        'auth.User',
        verbose_name=_("Last handled by"),
        related_name='handled_by_communication',
        null=True, blank=True)
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
        if self.send == True:
            self.dispatch(save=False) # then try to dispatch this email automatically
        super(Communication, self).save(*args, **kwargs)

    def dispatch(self, save = True):
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

            email = EmailMultiAlternatives(subject=self.subject, body=self.summary_txt(),
                                 from_email = 'Klub pratel Auto*Matu <kp@auto-mat.cz>',
                                 to = [self.user.email],
                                 bcc = bcc)
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
        self._columns += [('action', None, _(u"Action"), 'CharField', ('daily', 'new-user'))]
        # Models attributes
        for name in model_names:
            model = {'User': User,
                     'Payment': Payment,
                     'User.last_payment': Payment,
                     }[name]
            # DB fields
            self._columns += [(name, field.name, field.verbose_name, field.get_internal_type(), zip(*field.choices)[0] if field.choices else "") for field in model._meta.fields]
            # Public methods
            # TODO: This really lists all attributes, we should
            # for callable attributes
            self._columns += [(
                name, method, 
                getattr(getattr(model, method, None), 'short_description', method),
                getattr(getattr(model, method, None), 'return_type', "function"),
                getattr(getattr(model, method, None), 'condition_choices', "")
                ) for method in dir(model)
                              if (not method.startswith("_")
                                  and hasattr(getattr(model, method, None), '__call__')
                                  and method not in dir(models.Model))]
        self._columns.sort()
        self._index = 0

    def __iter__(self):
        return self
 
    def next(self):
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
        ('Logical', (
                ('and', 'and'),
                ('or', 'or'),
                ('nor', 'nor'),
                )),
        ('Comparison', (
                ('=', 'is equal to'),
                ('!=', 'is not equal to'),
                ('like', 'is like'), # in SQL sense
                ('>', 'greater than'),
                ('<', 'less than'))))

    name = models.CharField(
        verbose_name=_("Name of condition"),
        max_length=200, blank=False, null=True)
    # One of variable or conds must be non-null
    operation = models.CharField(
        verbose_name=_("Operation"),
        choices=OPERATORS,
        max_length=30)
    variable = models.CharField(
        verbose_name=_("Variable"),
        choices=ConditionValues(('User','User.last_payment')),
        help_text=_("Value or variable on left-hand side"),
        max_length=50, blank=True, null=True)
    # One of value or conds must be non-null
    value = models.CharField(
        verbose_name=_("Value"),
        help_text=_("Value or variable on right-hand side"),
        max_length=50, blank=True, null=True)
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

    def __unicode__(self):
        return self.name


    def condition_list(self):
        return ", ".join([condition.name for condition in self.conds.all()])
    def variable_description(self):
        #import pudb; pudb.set_trace()
        if self.variable:
            try:
                return unicode(User._meta.get_field(self.variable.split(".")[1]).help_text)
            except:
                return eval(self.variable).__doc__

    def is_true(self, user, action=None):
        def get_val(spec, user):
            # Symbolic names
            if spec == 'month_ago':
                return datetime.datetime.now()-datetime.timedelta(days=30)
            if spec == 'one_day':
                return datetime.timedelta(days=1)
            if spec == 'one_week':
                return datetime.timedelta(days=7)
            if spec == 'two_weeks':
                return datetime.timedelta(days=14)
            if spec == 'one_month':
                return datetime.timedelta(days=31)
            if spec == 'true':
                return True
            if spec == 'false':
                return False
            if spec == 'None':
                return None
            if spec == 'action':
                return action
        
            # DB objects
            if '.' in spec:
                spec_ = spec.split('.')
                if spec_[0] == 'User':
                    assert user
                    obj = user
                    for s in spec_[1:]:
                        v = getattr(obj, s)
                        if callable(v):
                            v = v()
                        if v is None:
                            return None
                        obj = v
                    return v
                elif spec_[0] == 'datetime':
                    return datetime.datetime.strptime(spec_[1], '%Y-%m-%d %H:%M')
                elif spec_[0] == 'timedelta':
                    return datetime.timedelta(days=int(spec_[1]))
                elif spec_[0] == 'days_ago':
                    return datetime.datetime.now() - datetime.timedelta(days=int(spec_[1]))
            else:
                try:
                    return int(spec)
                except (TypeError, ValueError):
                    return spec
        # Composed conditions
        if self.operation == 'and':
            for cond in self.conds.all():
                if not cond.is_true(user, action):
                    return False
            return True
        if self.operation == 'or':
            for cond in self.conds.all():
                if cond.is_true(user, action):
                    return True
            return False
        if self.operation == 'nor':
            for cond in self.conds.all():
                if cond.is_true(user, action):
                    return False
            return True

        # Elementary conditions
        left = get_val(self.variable, user)
        right = get_val(self.value, user)
        
        if left == None or right == None:
            return False

        # Enable comparison of dates and datetimes by converting dates to datetimes as 00:00
        if isinstance(left, datetime.date) and isinstance(right, datetime.datetime):
            left = datetime.datetime.combine(left, datetime.time.min)

        if self.operation == '=':
            return left == right
        if self.operation == '<':
            return left < right
        if self.operation == '>':
            return left > right
        if self.operation == '!=':
            return not left == right
        raise NotImplementedError("Unknown operation %s" % self.operation)

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
    condition = models.ForeignKey(Condition)
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
        help_text = _("Template can contain variable substitutions like addressment, name, "
                      "variable symbol etc."),
        max_length=50000)
    template_en = models.TextField(
        verbose_name=_("English template"),
        max_length=50000,
        blank=True, null=True)
    only_once = models.BooleanField(
        verbose_name=_("Only once"),
        help_text = _("If checked, never send this communication twice to one user"),
        default=True)
    dispatch_auto = models.BooleanField(
        verbose_name=_("Dispatch auto"),
        help_text = _("If checked, the communication might be dispatched by the system "
                      "(e.g. an email sent) as soon as condition becomes true, without "
                      "any further action from the administrator. If not, the communication "
                      "is created, but the administrator must send it manually."),
        default=False)
    sent_to_users = models.ManyToManyField(User, 
                                           help_text = _(
            "List of users to whom this communication was already sent"),
                                           blank=True,
                                           editable=False)
    def __unicode__(self):
        return self.name

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
        help_text = _("Template can contain variable substitutions like addressment, name, "
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
    send_to_users = models.ManyToManyField(User, 
            verbose_name=_("send to users"),
                                           help_text = _(
            "All users who should receive the communication"),
                                           limit_choices_to = {'active': 'True', 'wished_information': 'True'},
                                           blank=True)
    note = models.TextField(
        verbose_name=_("note"),
        help_text = _("Note"),
        max_length=500,
        blank=True, null=True)

    def __unicode__(self):
        return self.name

class OverwriteStorage(FileSystemStorage):
    def get_available_name(self, name):
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

	user = models.ForeignKey(User)
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
