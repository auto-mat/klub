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
from django.db.models import Sum, Count
from django.core.mail import EmailMessage
from django.utils.timesince import timesince
from django.utils.translation import ugettext as _
# External dependencies
import datetime
import csv
import os.path
# Local modules
import autocom

class UserManager(models.Manager):
    def get_query_set(self):
        return super(UserManager,self).get_query_set().annotate(
            payment_total=Sum('payment__amount'),
            payments_number=Count('payment'))

class Campaign(models.Model):
    """Campaign -- abstract event with description

    These events can be associated to a user."""

    class Meta:
        verbose_name = _("Campaign")
        verbose_name_plural = _("Campaigns")

    created = models.DateField(
        verbose_name=_("Created"))
    name = models.CharField(
        verbose_name=_("Name"),
        help_text=_("Choose some unique name for this campaign"),
        max_length=100, blank=True)
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Description of this campaign"),
        max_length=3000, blank=True)

    def __unicode__(self):
        return self.name

class Recruiter(models.Model):
    """Recruiter -- person that recruits new club members"""

    class Meta:
        verbose_name = _("Recruiter")
        verbose_name_plural = _("Recruiters")

    registered = models.DateField(
        verbose_name=_("Registered"),
        default=datetime.datetime.now())
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
        ('direct-dialogue-partial-form', _("Direct dialogue -- partial form (not automatic in bank)")),
        ('direct-dialogue-full-form', _("Direct dialogue -- full form (automatic in bank)")),
        ('personal', _('Personal recommendation')),
        ('other', _('Another form of contact')))
    REGULAR_PAYMENT_FREQUENCIES = (
        ('monthly', _('Monthly')),
        ('quaterly', _('Quaterly')),
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
        verbose_name=_("City"),
        max_length=40, blank=True)
    country = models.CharField(
        verbose_name=_("Country"),
        # TODO: Default country should come from app settings
        default=u"Česká republika",
        max_length=40, blank=True)
    zip_code = models.CharField(
        verbose_name=_("ZIP Code"),
        max_length=10, blank=True)
    # -- Additional Info
    age = models.PositiveIntegerField(
        verbose_name=_("Age"),
        max_length=5, blank=True)
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
        default=datetime.datetime.now(),
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
    # TODO: This needs to be replaced by amount and periodicity fields to
    # account also for quaterly and annual payments
    regular_amount = models.PositiveIntegerField(
        verbose_name=_("Amount of regular payment"),
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
        help_text=("Uncheck if you don't want your name to appear in the lists of supporters."),
        default=True)
    wished_tax_confirmation = models.BooleanField(
        verbose_name=_("Send tax confirmation"),
        help_text=("If you wish to receive tax confirmation at the end of year, check this field."),
        default=True)
    wished_welcome_letter = models.BooleanField(
        verbose_name=_("Send welcome letter"),
        help_text=("If you wish to receive welcome letter with your club card."),
        default=True)
    wished_information = models.BooleanField(
        verbose_name=_("Send regular news via email"),
        help_text=("If you wish to receive regular news about our activities."),
        default=True)
    active = models.BooleanField(
        verbose_name=_("Active"),
        help_text=("Is the user active member? Use this field to disable old "
                   "or temporary users."),
        default=True)
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
                                       blank=True,
                                       editable=True)
    recruiter = models.ForeignKey(Recruiter, blank=True, null=True)
    verified = models.BooleanField(
        _("Verified"),
        help_text=("Was the the user information verified by a club administrator?"),
        default=False)
    verified_by = models.ForeignKey(
        'auth.User',
        verbose_name=_("Verified by"),
        related_name='verified_users',
        null=True, blank=True)
    objects = UserManager()

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
        """Return number of payments made by this user"""
	return self.payments_number
    number_of_payments.admin_order_field = 'payments_number'
    
    def last_payment(self):
        """Return last payment"""
        user_payments = self.payments().order_by('-date')
        if len(user_payments):
            return user_payments[0]
        else:
            return None

    def last_payment_date(self):
        """Return date of last payment"""
        try:
            return self.last_payment().date
        except AttributeError:
            return None

    def expected_regular_payment_date(self):
        last_payment = self.last_payment()
        if not self.regular_payments:
            return None
        if last_payment:
            # Exactly a month after last payment or whatever
            # expectation record for the given user is set to
            interval_in_days = {'monthly': 31,
                                'quaterly': 92,
                                'annually': 366}
            expected = last_payment.date+datetime.timedelta(
                days=interval_in_days[self.regular_frequency])
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
        if self.regular_payments:
            # Check for regular payments
            # (Allow 7 days for payment processing)
            expected_with_tolerance = self.expected_regular_payment_date() + datetime.timedelta(days=10)
            if (expected_with_tolerance
                < datetime.date.today()):
                return datetime.date.today()-expected_with_tolerance
            else:
                return datetime.timedelta(days=0)
        else:
            return datetime.timedelta(days=0)

    def regular_payments_info(self):
        if not self.regular_payments:
            return _boolean_icon(False)
        out = [ u"%s: %s" % (_(u"Expected"), self.expected_regular_payment_date()) ]
        if self.regular_payments_delay():
            out.append(u"%s: %s" % (_(u"Delay"), timesince(self.expected_regular_payment_date())))
        return u"<br>".join(out)
    regular_payments_info.allow_tags = True
    regular_payments_info.short_description = _(u"Regular payments")

    def total_contrib(self):
        """Return the sum of all money received from this user"""
	return self.payment_total
    total_contrib.admin_order_field = 'payment_total'

    def save(self, *args, **kwargs):
        """Record save hook

        Perform a check for automated communications. Since the state of this
        user was changed, a new communication might arrise from this
        situation. See module 'autocom'.
        """
        super(User, self).save(*args, **kwargs)
        autocom.check(users=[self])

class NewUserManager(models.Manager):
    def get_query_set(self):
        return super(NewUserManager,self).get_query_set().filter(verified=False)

class NewUser(User):
    objects = NewUserManager()
    class Meta:
        proxy = True
        verbose_name = _("new user")
        verbose_name_plural = _("new users")

class AccountStatements(models.Model):
    """AccountStatemt entry and DB model

    Account statements serve primarily to load data into the Payments
    table. The loaded files are then archived for later evidence.
    """

    class Meta:
        verbose_name = _("Account Statement")
        verbose_name_plural = _("Account Statements")
	ordering = ['-import_date']

    import_date = models.DateField(
        default = datetime.date.today())
    csv_file = models.FileField(
        upload_to='account-statements')
    date_from = models.DateField(
        blank=True, null=True)
    date_to = models.DateField(
        blank=True, null=True)
    
    def save(self, *args, **kwargs):
        super(AccountStatements, self).save(*args, **kwargs)
        # Read and parse the account statement
        # TODO: This should be separated into a dedicated module
        win1250_contents = open(self.csv_file.path).read()
        unicode_contents = win1250_contents.decode('windows-1250')
        splitted = unicode_contents.encode('utf-8').split('\n\n')
        header = splitted[0]
        data = splitted[1]

        term_line = [line for line in header.split('\n')
                     if line.startswith("Období:")]
        name, date_start, dash, date_end = term_line[0].split()
        def str_to_datetime(date):
            return datetime.date(**dict(
                    zip(['day', 'month', 'year'],
                        [int(val) for val in date.split('.')])))
        self.date_from = str_to_datetime(date_start)
        self.date_to = str_to_datetime(date_end)
        super(AccountStatements, self).save()

        payments_reader = csv.DictReader(data.split("\n"), delimiter=';',
                                 fieldnames = [
                'transfer', 'date', 'amount', 'account', 'bank_code', 'KS', 'VS',
                'SS', 'user_identification', 'type', 'done_by', 'account_name',
                'bank_name', 'unknown'
                ])

        first_line = True
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
                p.save()

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
    user_identification = models.CharField(
        verbose_name=_("Sender identification"),
        help_text=_("Sender identification string on the account statement"),
        max_length=30, blank=True)
    type = models.CharField(
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

    def __unicode__(self):
        return str(self.amount)

COMMUNICATION_METHOD = (
    ('email', _("Email")),
    ('phonecall', _("Phonecall")),
    ('mail', _("Mail")),
    ('personal', _("Personal")),
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

    user = models.ForeignKey(User)
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
        max_length=10000)
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
        verbose_name=_("Send"),
        help_text=_("Request sending this communication to the user. For emails, this means that "
                     "the email will be immediatelly sent. In other types of communications, "
                     "someone must handle this manually."),
        default=False)
    dispatched = models.BooleanField(
        verbose_name=_("Dispatched"),
        help_text=_("Was this message already communicated with the client? Only check this "
                    "field when you are sure this communication was already sent or if this is "
                    " incomming communication. Only uncheck this field if you are sure the "
                    "recipient didn't get this communication "
                    "(such as due to lost mail)."),
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

        Currently only method 'email' is implemented. For these messages, the
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
            email = EmailMessage(subject=self.subject, body=self.summary,
                                 from_email = 'kp@auto-mat.cz',
                                 to = [self.user.email],
                                 bcc = bcc)
            if self.attachment:
                att = self.attachment
                email.attach(os.path.basename(att.name), att.read())
            try:
                email.send(fail_silently=False)
            except:
                pass
            else:
                self.dispatched = True
            self.send = False
            if save:
                self.save()

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
        for name in model_names:
            model = {'User': User,
                     'Payment': Payment}[name]
            # DB fields
            self._columns += [(name, field.name) for field in model._meta.fields]
            # Public methods
            # TODO: This really lists all attributes, we should
            # for callable attributes
            self._columns += [(name, method) for method in dir(model)
                              if (not method.startswith("_")
                                  and method not in dir(models.Model))]

        self._index = 0

    def __iter__(self):
        return self
 
    def next(self):
        try:
            val = ".".join(self._columns[self._index])
            self._index = self._index + 1
            return (val, val)
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
                ('or', 'or'))),
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
        choices=ConditionValues(('User',)),
        help_text=_("Value or variable on left-hand side"),
        max_length=30, blank=True, null=True)
    # One of value or conds must be non-null
    value = models.CharField(
        verbose_name=_("Value"),
        help_text=_("Value or variable on right-hand side"),
        max_length=50, blank=True, null=True)
    conds = models.ManyToManyField('self',
                                   related_name='conds_rel',
                                   symmetrical=False,
                                   verbose_name=_("Conditions"),
                                   blank=True, null=True)
    as_filter = models.BooleanField(
        verbose_name=_("Display as filter?"),
        help_text=_("Determines whether this condition is available as a filter"
                    "in the table of Users"),
        default=False)

    def __unicode__(self):
        return self.name

    def is_true(self, user):
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
        
            # DB objects
            if '.' in spec:
                obj, attr = spec.split('.')
                if obj == 'User':
                    attr_val = getattr(user, attr)
                    if callable(attr_val):
                        return attr_val()
                    else:
                        return attr_val
                elif obj == 'datetime':
                    return datetime.datetime.strptime(attr, '%Y-%m-%d %H:%M')
                elif obj == 'timedelta':
                    return datetime.timedelta(days=int(attr))
            else:
                try:
                    return int(spec)
                except TypeError:
                    return spec
        # Composed conditions
        if self.operation == 'and':
            for cond in self.conds.all():
                if not cond.is_true(user):
                    return False
            return True
        if self.operation == 'or':
            for cond in self.conds.all():
                if cond.is_true(user):
                    return True
            return False
        
        # Elementary conditions
        left = get_val(self.variable, user)
        right = get_val(self.value, user)
        #print "left: %s" % left
        #print "right: %s" % right
        
        if left == None or right == None:
            return False
        
        if self.operation == '=':
            return left == right
        if self.operation == '<':
            return left < right
        if self.operation == '>':
            return left > right
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
    template = models.TextField(
        verbose_name=_("Template"),
        help_text = _("Template can contain variable substitutions like addressment, name, "
                      "variable symbol etc."),
        max_length=10000)
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
        verbose_name=_("Date"), editable = False,
        default=None, blank=True, null=True)
    method = models.CharField(
        verbose_name=_("Method"),
        max_length=30,
        choices=COMMUNICATION_METHOD)
    subject = models.CharField(
        verbose_name=_("Subject"),
        max_length=100)
    template = models.TextField(
        verbose_name=_("Template"),
        help_text = _("Template can contain variable substitutions like addressment, name, "
                      "variable symbol etc."),
        max_length=10000,
        blank=True, null=True)
    template_en = models.TextField(
        verbose_name=_("English template"),
        max_length=10000,
        blank=True, null=True)
    attachment = models.FileField(
        verbose_name=_("Attachment"),
        upload_to='mass-communication-attachments',
        blank=True, null=True)
    send = models.BooleanField(
        verbose_name=_("Send"),
        help_text = _("If checked, the communication will be created for every user "
                      "on submitting this form. If possible (e.g. for emails), it will "
                      "also be automatically dispatched."),
        default=False)
    send_to_users = models.ManyToManyField(User, 
                                           help_text = _(
            "All users who should receive the communication"),
                                           blank=True)

    def __unicode__(self):
        return self.name


class UserImports(models.Model):
    """CSV imports of users

    This is a one-purpose helper class for imports of users from the
    old Auto*Mat club database.

    TODO: Remove when the old database is definitely shut down.
    """

    class Meta:
        verbose_name = _("User import")
        verbose_name_plural = _("Users imports")
	ordering = ['-import_date']

    import_date = models.DateField()
    csv_file = models.FileField(upload_to='kp-test/')
    
    def save(self, *args, **kwargs):
        super(UserImports, self).save(*args, **kwargs)

        data = open(self.csv_file.path).read()
        user_reader = csv.DictReader(data.split("\n"), delimiter=';',
                                 fieldnames = [
                'uid', 'name', 'surname', 'city', 'psc', 'street', 'telephone',
                'email', 'vsymbol', 'stable_payment', 'amount', 'payment_method',
                'public', 'information', 'user_note', 'registration_date',
                'nothing', 'note'
                ])

        for user in user_reader:
            regdate = user['registration_date']
            if regdate == "":
                regdate = '1999-01-01 00:00'

            note = user['note']
            if int(user['stable_payment']):
                regular_amount = int(user['amount'])
                regular_frequency = 'monthly'
            else:
                regular_amount = 0
                regular_frequency = None
                note += "Once paid %s as a single donation" % user['amount']

            u = User(firstname = user['name'],
                     surname = user['surname'],
                     sex = 'unknown',
                     email = user['email'],
                     telephone = user['telephone'],
                     street = user['street'],
                     zip_code = user['psc'],
                     registered_support = regdate,
                     regular_payments = int(user['stable_payment']),
                     regular_amount = regular_amount,
                     regular_frequency = regular_frequency,
                     exceptional_membership = False,
                     public = user['public'],
                     wished_information = user['information'],
                     note = note,
                     variable_symbol = user['vsymbol'])
            u.save()

