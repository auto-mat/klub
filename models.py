from django.db import models
from django.core.mail import send_mail
import django

import datetime
import csv

import autocom

def _(string):
    return string

class User(models.Model):
    GENDER = (('male', _('Male')),
              ('female', _('Female')),
              ('unknown', _('Unknown')))
    LANGUAGES = (('czech', _('Czech')),
                 ('english', _('English')))
    # TODO: Check field types and parameters (e.g. max_length)
    # one by one for reasonability and respecting the .xls doc

    # Basic personal information
    title_before = models.CharField(max_length=15, blank=True)
    firstname = models.CharField(max_length=80, blank=False) # TODO AFTER DB CLEANUP: null=False
    surname = models.CharField(max_length=80, blank=False) # TODO AFTER DB CLEANUP: null=False
    title_after = models.CharField(max_length=15, blank=True)
    sex = models.CharField(max_length=15, choices=GENDER)
    addressment = models.CharField(max_length=40, blank=True)
    addressment_on_envelope = models.CharField(max_length=40, blank=True)
    language = models.CharField(max_length=40, choices=LANGUAGES, default="czech")

    # Contacts
    email = models.CharField(max_length=40, blank=True)
    telephone = models.CharField(max_length=30, blank=True)
    street = models.CharField(max_length=80, blank=True)
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

    def was_published_today(self):
        return self.pub_date.date() == datetime.date.today()

    def person_name(self):
        return " ".join((self.firstname, self.surname))

    def requires_action(self):
        if len(Communication.objects.filter(user=self)) > 0:
            return True
        else:
            return False

    def payments(self):
        return len(Payment.objects.filter(user=self)) 

    def total_contrib(self):
        total = 0
        for payment in Payment.objects.filter(user=self):
            total += int(payment.amount)
        return total

    def save(self, *args, **kwargs):
        super(User, self).save(*args, **kwargs)
        autocom.check()

class Payment(models.Model):
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
    # pairing
    user = models.ForeignKey(User, blank=True, null=True)

    def person_name(self):
        return self.user.person_name()

    def paired_with_expected(self):
        # TODO: Logic to say if this payment was expected and processed correctly
        if self.user:
            return True
        else:
            return False

    def __unicode__(self):
        return str(self.amount)


COMMUNICATION_METHODS = (
    ('email', 'Email'),
    ('phonecall', 'Phonecall'),
    ('mail', 'Mail'),
    ('personal', 'Personal'),
)

class Communication(models.Model):
    user = models.ForeignKey(User)
    method = models.CharField(max_length=30, choices=COMMUNICATION_METHODS)
    date = models.DateTimeField()
    subject = models.CharField(max_length=100)
    summary = models.TextField(max_length=10000)
    note = models.TextField(max_length=3000, blank=True, null=True)
    handled_by = models.CharField(max_length=30, default="Klubovy Admin", null=True) # TODO: This needs to be a foreign key to table of Django users
    dispatched = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if self.pk is not None:
            orig = Communication.objects.get(pk=self.pk)
            if orig.dispatched == False and self.dispatched == True:
                self.dispatch()
        super(Communication, self).save(*args, **kwargs) # Call the "real" save() method

    def dispatch(self):
        if self.method == 'email':
            send_mail(self.subject, self.summary, 'kp@auto-mat.cz',
                      [self.user.email, 'klub-registrace@auto-mat.cz'],
                      fail_silently=False)
            if not self.dispatched:
                self.dispatched = True
                self.save()

class Condition(models.Model):
    OPERATORS = (
        ('and', 'and'),
        ('or', 'or'),
        ('=', 'is equal to'),
        ('!=', 'is not equal to'),
        ('like', 'is like'),
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
    name = models.CharField(max_length=50, blank=False, null=True)
    condition = models.ForeignKey(Condition)
    method = models.CharField(max_length=30, choices=COMMUNICATION_METHODS)
    subject = models.CharField(max_length=30)
    template = models.TextField(max_length=10000)
    only_once = models.BooleanField(default=True)
    dispatch_auto = models.BooleanField(default=False)
    sent_to_users = models.ManyToManyField(User, blank=True)

    def __unicode__(self):
        return self.name

class AccountStatements(models.Model):
    import_date = models.DateField()
    csv_file = models.FileField(upload_to='kp-test')
    
    def save(self, *args, **kwargs):
        super(AccountStatements, self).save(*args, **kwargs) # Call the "real" save() method first

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
                     
