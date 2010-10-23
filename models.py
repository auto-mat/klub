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

# External dependencies
import django
from django.db import models
from django.core.mail import send_mail
import datetime
import csv  # for account statements parsing

# Local modules
import autocom # automated mailing

# TODO: This is just an internationalization placeholder
def _(string):
    return string

class User(models.Model):
    """Club user model and DB table"""

    GENDER = (('male', _('Male')),
              ('female', _('Female')),
              ('unknown', _('Unknown')))
    # TODO: List of languages used in the club should come from app settings
    LANGUAGE = (('czech', _('Czech')), 
                ('english', _('English')))

    # Basic personal information
    title_before = models.CharField(max_length=15, blank=True)
    firstname = models.CharField(max_length=80, blank=False) # TODO AFTER DB CLEANUP: null=False
    surname = models.CharField(max_length=80, blank=False) # TODO AFTER DB CLEANUP: null=False
    title_after = models.CharField(max_length=15, blank=True)
    sex = models.CharField(max_length=15, choices=GENDER)
    addressment = models.CharField(max_length=40, blank=True)
    addressment_on_envelope = models.CharField(max_length=40, blank=True)
    language = models.CharField(max_length=40, choices=LANGUAGE, default="czech")

    # Contacts
    email = models.CharField(max_length=40, blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    street = models.CharField(max_length=80, blank=True)
    # TODO: Default city and country should come from app settings
    city = models.CharField(max_length=40, default="Praha", blank=True)
    country = models.CharField(max_length=40, default="Ceska Republika", blank=True)
    zip_code = models.CharField(max_length=20, blank=True)

    # Additional Info
    age = models.PositiveIntegerField(max_length=5, null=True, blank=True)
    knows_us_from = models.CharField(max_length=80, blank=True)
    why_supports = models.TextField(max_length=200, blank=True)
    field_of_work = models.CharField(max_length=40, blank=True) # also of study or interest
    source = models.CharField(max_length=80, blank=True)
    additional_information = models.CharField(max_length=500, blank=True)

    # Support
    variable_symbol = models.CharField(max_length=30, default="unknown", blank=False)
    registered_support = models.DateTimeField(null=True, default=datetime.datetime.now())
    exceptional_membership = models.BooleanField(default=False)
    regular_payments = models.BooleanField(default=False)
    monthly_payment = models.PositiveIntegerField(blank=True, null=True)
    other_support = models.TextField(max_length=500, blank=True)
    public = models.BooleanField(default=True)

    # Communication
    # TODO: wished_information should be a set (0 or more) of references into
    # the table of available information types (regular emailing about our causes,
    # Auto*Journal, invitations etc.)
    wished_information = models.CharField(max_length=200, blank=True, null=True) 

    # Benefits
    club_card_available = models.BooleanField(default=False) # Whether he is entitled to posses a club card
    club_card_dispatched = models.BooleanField(default=False) # Whether we have already sent him the club card
    other_benefits = models.TextField(max_length=500, blank=True)

    # Notes (club administrators private notes)
    note = models.TextField(max_length=2000, blank=True)

    def __unicode__(self):
        return self.person_name()

    def person_name(self):
        return " ".join((self.firstname, self.surname))

    def requires_action(self):
        """Return true if the user requires some action from
        the club manager, otherwise return False"""
        if len(Communication.objects.filter(user=self)) > 0:
            return True
        else:
            return False

    def payments(self):
        """Return number of payments made by this user"""
        return len(Payment.objects.filter(user=self)) 

    def total_contrib(self):
        """Return the sum of all money received from this user"""
        total = 0
        for payment in Payment.objects.filter(user=self):
            total += int(payment.amount)
        return total

    def save(self, *args, **kwargs):
        """Record save hook

        Perform a check for automated communications. Since the
        state of this user was changed, a new communication might
        arrise from this situation. See module 'autocom'.
        """
        super(User, self).save(*args, **kwargs)
        autocom.check()

class Payment(models.Model):
    """Payment model and DB table

    There are three kinds of payments:

    1) Payments that correspond 1:1 to a line in an account statement with
    a positive amount of money transfered

    2) Payments in cash are introduced by club administration and do not
    have any binding to the account statements

    3) Expected payment -- if the user commits to a single isolated payment
    but haven't sent the money yet or we haven't received the account statement
    confirmation yet. Expected payments might become case (1) or might stay
    as expected indefinitely in case the user doesn't actually make the payment.
    """

    TYPE_OF_PAYMENT = (
        ('account', _('Bank transfer'))
        ('cash', _('In cash')),
        ('expected', _('Expected payment')),
        )

    date = models.DateField(blank=True)
    amount = models.PositiveIntegerField(blank=True)
    account = models.CharField(max_length=100, blank=True, null=True)
    bank_code = models.CharField(max_length=30, blank=True, null=True)
    KS = models.CharField(max_length=30, blank=True, null=True)
    VS = models.CharField(max_length=30, blank=True, null=True)
    SS = models.CharField(max_length=30, blank=True, null=True)
    user_identification = models.CharField(max_length=30, blank=True, null=True)
    type = models.CharField(max_length=200, blank=True, null=True)
    done_by = models.CharField(max_length=500, blank=True, null=True)
    account_name = models.CharField(max_length=200, blank=True, null=True)
    bank_name = models.CharField(max_length=500, blank=True, null=True)    
    # Pairing of payments with a specific club system user
    user = models.ForeignKey(User, blank=True, null=True)

    def person_name(self):
        """Return name of the payer"""
        return self.user.person_name()

    def paired_with_expected(self):
        """Return if the payment is paired with an expected payment
        
        Expected payments are of two types:
        1) Single individual payments, that were previously registered as 'expected'
        2) Payments expected implicitly because the user is a regular contributor
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
    ('mail', 'Mail'),
    ('personal', 'Personal'),
)

class Communication(models.Model):
    """Communication entry and DB Model

    A communication is one action in the dialog between the club
    administration and the user. Communication can have various forms,
    e.g. email, phonecall or snail mail. Some communications are
    dispatched automatically, others on confirmation or entirely
    manually by the club administration.
    """
    user = models.ForeignKey(User)
    method = models.CharField(max_length=30, choices=COMMUNICATION_METHOD)
    date = models.DateTimeField()
    subject = models.CharField(max_length=100)
    summary = models.TextField(max_length=10000)
    note = models.TextField(max_length=3000, blank=True, null=True)
    # TODO: This needs to be a foreign key to table of Django users
    handled_by = models.CharField(max_length=30, default="Klubovy Admin", null=True)
    dispatched = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        """Record save hook

        If state of the dispatched field changes to True, call
        the automated dispatch() method.
        """
        if self.pk is not None:
            orig = Communication.objects.get(pk=self.pk)
            if orig.dispatched == False and self.dispatched == True:
                self.dispatch()
        super(Communication, self).save(*args, **kwargs) # Call the "real" save() method

    def dispatch(self):
        """Dispatch the communication

        Currently only method 'email' is implemented. For these messages, the email
        is sent via the service configured in application settings.

        TODO: Implement 'mail': the form with the requested text
        should be typeseted and the admin presented with a 'print'
        button. Address for filling on the envelope should be
        displayed to the admin.
        """
        if self.method == 'email':
            send_mail(self.subject, self.summary, 'kp@auto-mat.cz',
                      [self.user.email, 'klub-registrace@auto-mat.cz'],
                      # Above, a copy is sent back home for feedback and monitoring
                      fail_silently=False)
            if not self.dispatched:
                self.dispatched = True
                self.save()

class Condition(models.Model):
    """A condition entry and DB model

    Conditions are composed of the left hand side, an operator
    and the right hand side.

    Possible values for either side are:
    1) a value (string, integer...)
    2) a symbolic value -- variable, special value or reference to DB (e.g. u.regular)
    3) another condition

    Only one type of left and one type of right hand side value is permitted.
    Not all operators will work with all types of values (e.g. logic operators only work
    on other conditions on both sides)
    """

    OPERATORS = (
        ('and', 'and'),
        ('or', 'or'),
        ('=', 'is equal to'),
        ('!=', 'is not equal to'),
        ('like', 'is like'), # in SQL sense
        ('>', 'greater than'),
        ('<', 'less than'))

    name = models.CharField(max_length=50, blank=False, null=True)
    # One of variable or cond1 must be non-null
    variable = models.CharField(max_length=30, blank=True, null=True)
    cond1 = models.ForeignKey('self', related_name='cond1_rel', null=True, blank=True)
    operation = models.CharField(max_length=30, choices=OPERATORS)
    # One of value or cond2 must be non-null
    value = models.CharField(max_length=50, blank=True, null=True)
    cond2 = models.ForeignKey('self', related_name='cond2_rel', null=True, blank=True)

    def __unicode__(self):
        return self.name

class AutomaticCommunication(models.Model):
    """AutomaticCommunication entry and DB model

    Automatic communication is a communication template bound to
    a specific condition. If the condition becomes true for the given
    user, a Communication is created for him and perhaps automatically
    dispatched, based on the configuration. See the 'Communication'
    model and the 'autocom' module."""

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
    import_date = models.DateField()
    csv_file = models.FileField(upload_to='account-statements')
    
    def save(self, *args, **kwargs):
        super(AccountStatements, self).save(*args, **kwargs) # Call the "real" save() method first

        # Read and parse the account statement
        # TODO: This should be separated into a dedicated module
        win1250_contents = open(self.csv_file.path).read()
        unicode_contents = win1250_contents.decode('windows-1250')
        splitted = unicode_contents.encode('utf-8').split('\n\n')
        header = splitted[0]
        data = splitted[1]

        #print header
        #print "-----------"
        #print data

        payments_reader = csv.DictReader(data.split("\n"), delimiter=';',
                                 fieldnames = [
                'transfer', 'date', 'amount', 'account', 'bank_code', 'KS', 'VS', 'SS',
                'user_identification', 'type', 'done_by', 'account_name', 'bank_name',
                'unknown'
                ])

        first_line = True
        for payment in payments_reader:
            if first_line:
                first_line = False
            elif payment['date'] == 'Suma':
                break
            else:
                del payment['transfer']
                del payment['unknown']
                #print payment['date']
                d,m,y = payment['date'].split('.')
                payment['date'] = "%04d-%02d-%02d" % (int(y),int(m),int(d))
                payment['amount'] = int(round(float(payment['amount'].replace(',','.').replace(' ',''))))
                #print str(payment)
                p = Payment(**payment)
                # Payments pairing
                users_with_vs = User.objects.filter(variable_symbol=p.VS)
                #print str(p.VS)
                #print str(users_with_vs)
                if len(users_with_vs) == 1:
                    p.user = users_with_vs[0]
                elif len(users_with_vs) > 1:
                    raise Exception("Duplicit variable symbol detected!")
                p.save()

class UserImports(models.Model):
    """CSV imports of users

    This is a one-purpose helper class for imports of users from the
    old Auto*Mat club database.

    TODO: Remove when the old database is definitely shut down.
    """
    import_date = models.DateField()
    csv_file = models.FileField(upload_to='kp-test/')
    
    def save(self, *args, **kwargs):
        super(UserImports, self).save(*args, **kwargs) # Call the "real" save() method first

        data = open(self.csv_file.path).read()
        user_reader = csv.DictReader(data.split("\n"), delimiter=';',
                                 fieldnames = [
                'uid', 'name', 'surname', 'city', 'psc', 'street', 'telephone', 'email', 'vsymbol',
                'stable_payment', 'amount', 'payment_method', 'public', 'information', 'user_note',
                'registration_date', 'nothing', 'note'
                ])

        for user in user_reader:
            #print "%s %s %s" % (user['name'], user['surname'], user['stable_payment'])

            regdate = user['registration_date']
            if regdate == "":
                regdate = '1999-01-01 00:00'

            note = user['note']
            if int(user['stable_payment']):
                monthly_payment = int(user['amount'])
            else:
                monthly_payment = 0
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
                     monthly_payment = monthly_payment,
                     exceptional_membership = False,
                     public = user['public'],
                     wished_information = user['information'],
                     note = note,
                     variable_symbol = user['vsymbol'])
            u.save()
                     
