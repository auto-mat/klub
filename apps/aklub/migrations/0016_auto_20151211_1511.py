# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import stdimage.models


class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0015_auto_20151016_1636'),
    ]

    operations = [
        migrations.AlterField(
            model_name='accountstatements',
            name='csv_file',
            field=models.FileField(upload_to='account-statements'),
        ),
        migrations.AlterField(
            model_name='accountstatements',
            name='type',
            field=models.CharField(max_length=20, choices=[('account', 'Account statement'), ('darujme', 'Darujme.cz')]),
        ),
        migrations.AlterField(
            model_name='automaticcommunication',
            name='method',
            field=models.CharField(max_length=30, verbose_name='Method', choices=[('email', 'Email'), ('phonecall', 'Phonecall'), ('mail', 'Mail'), ('personal', 'Personal'), ('internal', 'Internal')]),
        ),
        migrations.AlterField(
            model_name='communication',
            name='attachment',
            field=models.FileField(upload_to='communication-attachments', verbose_name='Attachment', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='communication',
            name='method',
            field=models.CharField(max_length=30, verbose_name='Method', choices=[('email', 'Email'), ('phonecall', 'Phonecall'), ('mail', 'Mail'), ('personal', 'Personal'), ('internal', 'Internal')]),
        ),
        migrations.AlterField(
            model_name='communication',
            name='type',
            field=models.CharField(max_length=30, verbose_name='Type of communication', choices=[('mass', 'Mass'), ('auto', 'Automatic'), ('individual', 'Individual')], default='individual'),
        ),
        migrations.AlterField(
            model_name='condition',
            name='operation',
            field=models.CharField(max_length=30, verbose_name='Operation', choices=[('and', 'and'), ('or', 'or'), ('nor', 'nor')]),
        ),
        migrations.AlterField(
            model_name='masscommunication',
            name='attachment',
            field=models.FileField(upload_to='mass-communication-attachments', verbose_name='Attachment', blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='masscommunication',
            name='method',
            field=models.CharField(max_length=30, verbose_name='Method', choices=[('email', 'Email'), ('phonecall', 'Phonecall'), ('mail', 'Mail'), ('personal', 'Personal'), ('internal', 'Internal')]),
        ),
        migrations.AlterField(
            model_name='payment',
            name='account',
            field=models.CharField(max_length=100, verbose_name='Account', blank=True, help_text='Bank account from which money was received'),
        ),
        migrations.AlterField(
            model_name='payment',
            name='type',
            field=models.CharField(max_length=200, verbose_name='Type', choices=[('bank-transfer', 'Bank transfer'), ('cash', 'In cash'), ('expected', 'Expected payment'), ('darujme', 'Darujme.cz')], blank=True, help_text='Type of payment'),
        ),
        migrations.AlterField(
            model_name='recruiter',
            name='rating',
            field=models.IntegerField(verbose_name='Rating', choices=[(0, '0'), (1, '1'), (2, '2'), (3, '3'), (4, '4'), (5, '5'), (6, '6'), (7, '7'), (8, '8'), (9, '9'), (10, '10')], help_text='5 = ordinary (modestly good), 0 = hopelessly bad 10 = excelent much above average', default=5),
        ),
        migrations.AlterField(
            model_name='terminalcondition',
            name='operation',
            field=models.CharField(max_length=30, verbose_name='Operation', choices=[('=', 'is equal to'), ('!=', 'is not equal to'), ('like', 'is like'), ('>', 'greater than'), ('<', 'less than')]),
        ),
        migrations.AlterField(
            model_name='terminalcondition',
            name='variable',
            field=models.CharField(max_length=50, choices=[('User.active', 'User Active: BooleanField '), ('User.activity_points', 'User Activity points: IntegerField '), ('User.additional_information', 'User Additional information: TextField '), ('User.addressment', 'User Addressment in letter: CharField '), ('User.addressment_on_envelope', 'User Addressment on envelope: CharField '), ('User.city', 'User City/City part: CharField '), ('User.club_card_available', 'User Club card available: BooleanField '), ('User.club_card_dispatched', 'User Club card dispatched?: BooleanField '), ('User.country', 'User Country: CharField '), ('User.different_correspondence_address', 'User Different correspondence address: BooleanField '), ('User.email', 'User Email: CharField '), ('User.exceptional_membership', 'User Exceptional membership: BooleanField '), ('User.expected_date_of_first_payment', 'User Expected date of first payment: DateField '), ('User.expected_regular_payment_date', 'User expected regular payment date: DateField '), ('User.extra_money', 'User extra money: IntegerField '), ('User.field_of_work', 'User Field of work: CharField '), ('User.firstname', 'User First name: CharField '), ('User.id', 'User ID: AutoField '), ('User.knows_us_from', 'User Where does he/she know us from?: CharField '), ('User.language', "User Language: CharField ('cs', 'en')"), ('User.last_payment', 'User last payment: DenormDBField '), ('User.no_upgrade', 'User no upgrade: NullBooleanField '), ('User.note', 'User Note for making a boring form more lively: TextField '), ('User.number_of_payments', 'User number of payments: IntegerField '), ('User.old_account', 'User Old account: BooleanField '), ('User.other_benefits', 'User Other benefits: TextField '), ('User.other_support', 'User Other support: TextField '), ('User.payment_total', 'User payment total: FloatField '), ('User.profile_picture', 'User Profile picture: FileField '), ('User.profile_text', 'User What is your reason?: TextField '), ('User.public', 'User Publish my name in the list of supporters: BooleanField '), ('User.recruiter', 'User recruiter: ForeignKey '), ('User.registered_support', 'User Registered support: DateTimeField '), ('User.regular_amount', 'User Regularly (amount): PositiveIntegerField '), ('User.regular_frequency', "User Frequency of regular payments: CharField ('monthly', 'quaterly', 'biannually', 'annually')"), ('User.regular_payments', 'User Regular payments: BooleanField '), ('User.sex', "User Gender: CharField ('male', 'female', 'unknown')"), ('User.source', 'User Source: ForeignKey '), ('User.street', 'User Street and number: CharField '), ('User.surname', 'User Surname: CharField '), ('User.telephone', 'User Telephone: CharField '), ('User.title_after', 'User Title after name: CharField '), ('User.title_before', 'User Title before name: CharField '), ('User.variable_symbol', 'User Variable symbol: CharField '), ('User.verified', 'User Verified: BooleanField '), ('User.verified_by', 'User Verified by: ForeignKey '), ('User.why_supports', 'User Why does he/she support us?: TextField '), ('User.wished_information', 'User Send regular news via email: BooleanField '), ('User.wished_tax_confirmation', 'User Send tax confirmation: BooleanField '), ('User.wished_welcome_letter', 'User Send welcome letter: BooleanField '), ('User.zip_code', 'User ZIP Code: CharField '), ('User.last_payment.BIC', 'User.last_payment BIC: CharField '), ('User.last_payment.KS', 'User.last_payment CS: CharField '), ('User.last_payment.SS', 'User.last_payment SS: CharField '), ('User.last_payment.VS', 'User.last_payment VS: CharField '), ('User.last_payment.account', 'User.last_payment Account: CharField '), ('User.last_payment.account_name', 'User.last_payment Account name: CharField '), ('User.last_payment.account_statement', 'User.last_payment account statement: ForeignKey '), ('User.last_payment.amount', 'User.last_payment Amount: PositiveIntegerField '), ('User.last_payment.bank_code', 'User.last_payment Bank code: CharField '), ('User.last_payment.bank_name', 'User.last_payment Bank name: CharField '), ('User.last_payment.date', 'User.last_payment Date of payment: DateField '), ('User.last_payment.done_by', 'User.last_payment Done by: CharField '), ('User.last_payment.id', 'User.last_payment ID: AutoField '), ('User.last_payment.type', "User.last_payment Type: CharField ('bank-transfer', 'cash', 'expected', 'darujme')"), ('User.last_payment.user', 'User.last_payment user: ForeignKey '), ('User.last_payment.user_identification', 'User.last_payment Sender identification: CharField '), ('User.source.direct_dialogue', 'User.source Is from Direct Dialogue: BooleanField '), ('User.source.id', 'User.source ID: AutoField '), ('User.source.name', 'User.source Name: CharField '), ('User.source.slug', 'User.source Slug: SlugField '), ('action', "Action: CharField ('daily', 'new-user', 'new-payment')")], blank=True, null=True, verbose_name='Variable', help_text='Value or variable on left-hand side'),
        ),
        migrations.AlterField(
            model_name='user',
            name='expected_date_of_first_payment',
            field=models.DateField(null=True, verbose_name='Expected date of first payment', blank=True, help_text='When should the first payment arrive on our account'),
        ),
        migrations.AlterField(
            model_name='user',
            name='field_of_work',
            field=models.CharField(max_length=80, verbose_name='Field of work', blank=True, help_text='His/her area of expertise and/or interest'),
        ),
        migrations.AlterField(
            model_name='user',
            name='language',
            field=models.CharField(max_length=50, verbose_name='Language', choices=[('cs', 'Czech'), ('en', 'English')], help_text='This is the language which will be used to communicate with this user. The system will send emails in this language and administrators will use this language in phone calls and personal contacts.', default='cs'),
        ),
        migrations.AlterField(
            model_name='user',
            name='profile_picture',
            field=stdimage.models.StdImageField(upload_to='profile-images', verbose_name='Profile picture', blank=True, help_text='Your profile picture, which others will see.', null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='regular_frequency',
            field=models.CharField(max_length=20, verbose_name='Frequency of regular payments', choices=[('monthly', 'Monthly'), ('quaterly', 'Quaterly'), ('biannually', 'Bianually'), ('annually', 'Anually')], blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='user',
            name='sex',
            field=models.CharField(max_length=50, verbose_name='Gender', choices=[('male', 'Male'), ('female', 'Female'), ('unknown', 'Unknown')]),
        ),
        migrations.AlterField(
            model_name='user',
            name='variable_symbol',
            field=models.CharField(max_length=30, verbose_name='Variable symbol', default=''),
        ),
    ]
