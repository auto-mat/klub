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
from django.db import models
from django.db.models import Sum
from django.core.mail import send_mail
from django.utils.translation import ugettext as _
# External dependencies
import datetime
import csv
# Local modules
import autocom

class UserManager(models.Manager):
    def get_query_set(self):
        return super(UserManager,self).get_query_set().annotate(
            payment_total=Sum('payment__amount'))

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
        ('czech', _('Czech')), 
        ('english', _('English')))
    SOURCE = (
        ('web', _("Web form")),
        ('direct-dialogue-event', _("Direct dialogue on one of our events")),
        ('direct-dialogue-street', _("Direct dialogue on the street/other")),
        ('personal', _('Personal recommendation')),
        ('other', _('Another form of contact')))
    REGULAR_PAYMENT_FREQUENCIES = (
        ('monthly', _('Monthly')),
        ('quaterly', _('Quaterly')),
        ('annually', _('Anually')))
             
    # -- Basic personal information
    title_before = models.CharField(
        _("Title before name"),
        max_length=15, blank=True)
    firstname = models.CharField(
        _("First name"),
        max_length=80) # TODO AFTER DB CLEANUP: null=False
    surname = models.CharField(
        _("Surname"),
        max_length=80) # TODO AFTER DB CLEANUP: null=False
    title_after = models.CharField(
        _("Title after name"),
        max_length=15, blank=True)
    sex = models.CharField(
        _("Gender"),
        choices=GENDER,
        max_length=50)
    addressment = models.CharField(
        _("Addressment in letter"),
        max_length=40, blank=True)
    addressment_on_envelope = models.CharField(
        _("Addressment on envelope"),
        max_length=40, blank=True)
    language = models.CharField(
        _("Language"),
        help_text=_("This is the language which will be used to "
                    "communicate with this user. The system will send "
                    "emails in this language and administrators will use "
                    "this language in phone calls and personal contacts."),
        choices=LANGUAGE,
        default="czech",
        max_length=50)
    # -- Contacts
    email = models.CharField(
        _("Email"),
        max_length=40, blank=True)
    telephone = models.CharField(
        _("Telephone"),
        max_length=30, blank=True)
    street = models.CharField(
        _("Street"),
        max_length=80, blank=True)
    city = models.CharField(
        _("City"),
        default="Praha", # TODO: Default city should come from app settings
        max_length=40, blank=True)
    country = models.CharField(
        _("Country"),
        # TODO: Default country should come from app settings
        default="Ceska Republika",
        max_length=40, blank=True)
    zip_code = models.CharField(
        _("ZIP Code"),
        max_length=10, blank=True)
    # -- Additional Info
    age = models.PositiveIntegerField(
        _("Age"),
        max_length=5, blank=True)
    knows_us_from = models.CharField(
        _("Where does he/she know us from?"),
        max_length=80, blank=True)
    why_supports = models.TextField(
        _("Why does he/she support us?"),
        max_length=500, blank=True)
    field_of_work = models.CharField(
        _("Field of work"),
        help_text="His/her area of expertise and/or interest",
        max_length=80, blank=True)
    source = models.CharField(
        _("Source"),
        help_text=_("How did he contact us / became a member?"),
        choices=SOURCE,
        max_length=80, blank=False)
    additional_information = models.TextField(
        _("Additional information"),
        max_length=500, blank=True)
    # -- Support
    variable_symbol = models.CharField(
        default="",
        max_length=30, blank=False)
    registered_support = models.DateTimeField(
        _("Registered support"),
        help_text=_("When did this user register to support us"),
        default=datetime.datetime.now(),
        blank=True)
    exceptional_membership = models.BooleanField(
        _("Exceptional membership"),
        help_text=_("In special cases, people can become members of "
                    "the club even if they do not pay any money. This should "
                    "be justified in the note."),
        default=False)
    regular_payments = models.BooleanField(
        _("Regular payments"),
        help_text=_("Is this user registered for regular payments?"),
        default=False)
    # TODO: This needs to be replaced by amount and periodicity fields to
    # account also for quaterly and annual payments
    regular_amount = models.PositiveIntegerField(
        _("Amount of regular payment"),
        blank=True, null=True)
    regular_frequency = models.CharField(
        _("Frequency of regular payments"),
        choices=REGULAR_PAYMENT_FREQUENCIES,
        max_length=20, blank=True, null=True)
    other_support = models.TextField(
        _("Other support"),
        help_text=
        _("If the user supports us in other ways, please specify here."),
        max_length=500, blank=True)
    public = models.BooleanField(
        _("Public"),
        help_text=("Does he wish his name to appear publicly in the list of "
                   "supporters of our organization?"),
        default=True)
    active = models.BooleanField(
        _("Active"),
        help_text=("Is the user active member? Use this field to disable old "
                   "or temporary users."),
        default=True)
    # --- Communication
    # TODO: wished_information should be a set (0 or more) of references into the
    # table of available information types (regular emailing about our causes,
    # Auto*Journal, invitations etc.)
    wished_information = models.CharField(
        max_length=200, blank=True) 
    # Benefits
    club_card_available = models.BooleanField(
        _("Club card available"),
        default=False, help_text=_("Is he entitled to posses a club card?"))
    club_card_dispatched = models.BooleanField(
        _("Club card dispatched?"),
        help_text=_("Did we send him the club card already?"),
        default=False)
    other_benefits = models.TextField(
        _("Other benefits"),
        help_text=_("Did he receive some other benefits?"),
        max_length=500, blank=True)
    # -- Notes (club administrators private notes)
    note = models.TextField(
        _("Notes"),
        help_text=_("Private notes of the club administrators"),
        max_length=2000, blank=True)

    objects = UserManager()

    def __unicode__(self):
        return self.person_name()

    def person_name(self):
        return " ".join((self.firstname, self.surname))
    person_name.short_description = _("Full name") 

    def requires_action(self):
        """Return true if the user requires some action from
        the club manager, otherwise return False"""
        if len(Communication.objects.filter(user=self)) > 0:
            return True
        else:
            return False

    def payments(self):
        return Payment.objects.filter(user=self)

    def number_of_payments(self):
        """Return number of payments made by this user"""
        p = self.payments()
        return p and len(p) or 0 
    
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
        if last_payment:
            return last_payment.date+datetime.timedelta(days=31)
        else:
            return self.registered_support.date()+datetime.timedelta(days=14)

    def regular_payments_ok(self):
        """Check if his payments are OK

        Return True if so, otherwise return the delay in payment as dattime.timedelta
        """

        if self.regular_payments:
            # Check for regular payments
            # (Allow 7 days for payment processing)
            if ((self.expected_regular_payment_date() + datetime.timedelta(days=7))
                < datetime.date.today()):
                return (self.expected_regular_payment_date() - datetime.today())
            else:
                return True
        else:
            return True

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
        autocom.check()

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
        _("Date of payment"))
    amount = models.PositiveIntegerField(
        _("Amount"),
        help_text=_("Amount of money in the main used curency"))
    account = models.CharField(
        _("Account"),
        help_text=_("Bank account from which money was received"),
        max_length=100, blank=True)
    bank_code = models.CharField(
        _("Bank code"),
        help_text=_("Code of bank from which money was received"),
        max_length=30, blank=True)
    VS = models.CharField(
        _("VS"),
        help_text= _("Variable symbol"),
        max_length=30, blank=True)
    SS = models.CharField(
        _("SS"),
        help_text=_("Specific symbol"),
        max_length=30, blank=True)
    KS = models.CharField(
        _("CS"),
        help_text=_("Constant symbol"),
        max_length=30, blank=True)
    user_identification = models.CharField(
        _("Sender identification"),
        help_text=_("Sender identification string on the account statement"),
        max_length=30, blank=True)
    type = models.CharField(
        help_text=_("Type of payment"),
        choices=TYPE_OF_PAYMENT,
        max_length=200, blank=True)
    done_by = models.CharField(
        _("Done by"),
        help_text=_("This is a column imported from the account statements. "
                    "It's purpose is not clear. It has been usually blank on "
                    "the account statement we have received so far."),
        max_length=500, blank=True)
    account_name = models.CharField(
        _("Account name"),
        max_length=200, blank=True)
    bank_name = models.CharField(
        _("Bank name"),
        max_length=500, blank=True)    
    # Pairing of payments with a specific club system user
    user = models.ForeignKey(User, blank=True, null=True)

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
        _("Method"),
        max_length=30, choices=COMMUNICATION_METHOD)
    date = models.DateTimeField(
        _("Date"))
    subject = models.CharField(
        _("Subject"),
        _("The topic of this communication"),
        max_length=100)
    summary = models.TextField(
        _("Text"),
        help_text=_("Text or summary of this communication"),
        max_length=10000)
    note = models.TextField(
        _("Notes"),
        help_text=_("Internal notes about this communication"),
        max_length=3000, blank=True)
    # TODO: This needs to be a foreign key to table of Django users
    handled_by = models.ForeignKey(
        'auth.User',
        verbose_name=_("Handled by"),
        null=True, blank=True)
    dispatched = models.BooleanField(
        _("Dispatched"),
        _("Was this message already sent/communicated to the client? In case "
          "of emails, changing this field to 'checked' will result in automatic "
          "sending of the email to the client."),
        default=True)

    def save(self, *args, **kwargs):
        """Record save hook

        If state of the dispatched field changes to True, call
        the automated dispatch() method.
        """
        if self.pk is not None:
            orig = Communication.objects.get(pk=self.pk)
            if orig.dispatched == False and self.dispatched == True:
                self.dispatch()
        super(Communication, self).save(*args, **kwargs)

    def dispatch(self):
        """Dispatch the communication

        Currently only method 'email' is implemented. For these messages, the
        email is sent via the service configured in application settings.

        TODO: Implement 'mail': the form with the requested text should be
        typeseted and the admin presented with a 'print' button. Address for
        filling on the envelope should be displayed to the admin.
        """
        if self.method == 'email':
            send_mail(self.subject, self.summary, 'kp@auto-mat.cz',
                      [self.user.email, 'kp@auto-mat.cz'],
                      # Above, a copy is sent back home for feedback and
                      # monitoring
                      fail_silently=False)
            if not self.dispatched:
                self.dispatched = True
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
        ('and', 'and'),
        ('or', 'or'),
        ('=', 'is equal to'),
        ('!=', 'is not equal to'),
        ('like', 'is like'), # in SQL sense
        ('>', 'greater than'),
        ('<', 'less than'))

    name = models.CharField(
        _("Name of condition"),
        max_length=200, blank=False, null=True)
    # One of variable or cond1 must be non-null
    variable = models.CharField(
        _("Value"),
        choices=ConditionValues(('User',)),
        help_text=_("Value or variable on left-hand side"),
        max_length=30, blank=True, null=True)
    cond1 = models.ForeignKey(
        'self',
        related_name='cond1_rel',
        verbose_name=_("Condition"),
        blank=True, null=True)
    operation = models.CharField(
        _("Operation"),
        choices=OPERATORS,
        max_length=30)
    # One of value or cond2 must be non-null
    value = models.CharField(
        _("Value"),
        help_text=_("Value or variable on right-hand side"),
        max_length=50, blank=True, null=True)
    conds2 = models.ManyToManyField('self',
                                    related_name='conds_rel',
                                    symmetrical=False,
                                    verbose_name=_("Conditions"),
                                    blank=True, null=True)


    def __unicode__(self):
        return self.name


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

    name = models.CharField(max_length=50, blank=False, null=True)
    condition = models.ForeignKey(Condition)
    method = models.CharField(max_length=30, choices=COMMUNICATION_METHOD)
    subject = models.CharField(max_length=30)
    template = models.TextField(max_length=10000)
    only_once = models.BooleanField(default=True)
    dispatch_auto = models.BooleanField(default=False)
    sent_to_users = models.ManyToManyField(User, blank=True)

    def __unicode__(self):
        return self.name

class AccountStatements(models.Model):
    """AccountStatemt entry and DB model

    Account statements serve primarily to load data into the Payments
    table. The loaded files are then archived for later evidence.
    """

    class Meta:
        verbose_name = _("Account Statement")
        verbose_name_plural = _("Account Statements")
	ordering = ['-import_date']

    import_date = models.DateField()
    csv_file = models.FileField(upload_to='account-statements')
    
    def save(self, *args, **kwargs):
        super(AccountStatements, self).save(*args, **kwargs)
        # Read and parse the account statement
        # TODO: This should be separated into a dedicated module
        win1250_contents = open(self.csv_file.path).read()
        unicode_contents = win1250_contents.decode('windows-1250')
        splitted = unicode_contents.encode('utf-8').split('\n\n')
        header = splitted[0]
        data = splitted[1]

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
                p.save()

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

