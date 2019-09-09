# Generated by Django 2.2.4 on 2019-09-09 07:12

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion

from .data_migration.migrate_user_first_last_name import (
    get_user_model_data, set_user_model_data
)


class Migration(migrations.Migration):

    dependencies = [
        ('aklub', '0041_auto_20190904_1819'),
    ]

    operations = [
        # Get data
        migrations.RunPython(
            code=get_user_model_data,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
        migrations.RemoveField(
            model_name='profile',
            name='first_name',
        ),
        migrations.RemoveField(
            model_name='profile',
            name='last_name',
        ),
        migrations.AddField(
            model_name='companyprofile',
            name='name',
            field=models.CharField(blank=True, max_length=180, null=True, verbose_name='Name'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='first_name',
            field=models.CharField(blank=True, max_length=30, verbose_name='first name'),
        ),
        migrations.AddField(
            model_name='userprofile',
            name='last_name',
            field=models.CharField(blank=True, max_length=150, verbose_name='last name'),
        ),
        migrations.AlterField(
            model_name='companyprofile',
            name='crn',
            field=models.CharField(max_length=20, null=True, verbose_name='Company Registration Number'),
        ),
        migrations.AlterField(
            model_name='profileemail',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='terminalcondition',
            name='variable',
            field=models.CharField(blank=True, choices=[('Profile.addressment', 'Profile Oslovení v dopise: CharField '), ('Profile.addressment_on_envelope', 'Profile Oslovení na obálku: CharField '), ('Profile.call_on', 'Profile DEPRECATED FIELD: NullBooleanField '), ('Profile.challenge_on', 'Profile DEPRECATED FIELD: NullBooleanField '), ('Profile.city', 'Profile Město/Městská část: CharField '), ('Profile.club_card_available', 'Profile Nárok na klubovou kartu: BooleanField '), ('Profile.club_card_dispatched', 'Profile Klubová karta odeslána?: BooleanField '), ('Profile.correspondence_city', 'Profile Město/Městská část: CharField '), ('Profile.correspondence_country', 'Profile Země: CharField '), ('Profile.correspondence_street', 'Profile Ulice a číslo domu (č.p./č.o.): CharField '), ('Profile.correspondence_zip_code', 'Profile PSČ: CharField '), ('Profile.country', 'Profile Země: CharField '), ('Profile.created', 'Profile Datum vytvoření: DateTimeField '), ('Profile.date_joined', 'Profile datum registrace: DateTimeField '), ('Profile.different_correspondence_address', 'Profile Jiná korespondenční adresa: BooleanField '), ('Profile.email', 'Profile e-mailová adresa: CharField '), ('Profile.id', 'Profile ID: AutoField '), ('Profile.is_active', 'Profile aktivní: BooleanField '), ('Profile.is_staff', 'Profile administrační přístup: BooleanField '), ('Profile.is_superuser', 'Profile superuživatel: BooleanField '), ('Profile.language', "Profile Jazyk: CharField ('cs', 'en')"), ('Profile.last_login', 'Profile poslední přihlášení: DateTimeField '), ('Profile.letter_on', 'Profile DEPRECATED FIELD: NullBooleanField '), ('Profile.newsletter_on', 'Profile DEPRECATED FIELD: NullBooleanField '), ('Profile.note', 'Profile Poznámky: TextField '), ('Profile.other_benefits', 'Profile Další benefity: TextField '), ('Profile.other_support', 'Profile Jiná podpora: TextField '), ('Profile.password', 'Profile heslo: CharField '), ('Profile.polymorphic_ctype', 'Profile polymorphic ctype: ForeignKey '), ('Profile.profile_picture', 'Profile Profilová fotografie: FileField '), ('Profile.profile_text', 'Profile A jaký je Tvůj důvod?: TextField '), ('Profile.public', 'Profile DEPRECATED FIELD: BooleanField '), ('Profile.send_mailing_lists', 'Profile DEPRECATED FIELD: BooleanField '), ('Profile.street', 'Profile Ulice a číslo domu (č.p./č.o.): CharField '), ('Profile.updated', 'Profile Datum poslední změny: DateTimeField '), ('Profile.username', 'Profile uživatelské jméno: CharField '), ('Profile.zip_code', 'Profile PSČ: CharField '), ('User.date_joined', 'User datum registrace: DateTimeField '), ('User.email', 'User e-mailová adresa: CharField '), ('User.first_name', 'User křestní jméno: CharField '), ('User.id', 'User ID: AutoField '), ('User.is_active', 'User aktivní: BooleanField '), ('User.is_staff', 'User administrační přístup: BooleanField '), ('User.is_superuser', 'User superuživatel: BooleanField '), ('User.last_login', 'User poslední přihlášení: DateTimeField '), ('User.last_name', 'User příjmení: CharField '), ('User.password', 'User heslo: CharField '), ('User.username', 'User uživatelské jméno: CharField '), ('User.last_payment.BIC', 'User.last_payment BIC: CharField '), ('User.last_payment.KS', 'User.last_payment KS: CharField '), ('User.last_payment.SS', 'User.last_payment SS: CharField '), ('User.last_payment.VS', 'User.last_payment VS 1: CharField '), ('User.last_payment.VS2', 'User.last_payment VS 2: CharField '), ('User.last_payment.account', 'User.last_payment Account: CharField '), ('User.last_payment.account_name', 'User.last_payment Jméno účtu: CharField '), ('User.last_payment.account_statement', 'User.last_payment account statement: ForeignKey '), ('User.last_payment.amount', 'User.last_payment Částka: PositiveIntegerField '), ('User.last_payment.bank_code', 'User.last_payment Kód banky: CharField '), ('User.last_payment.bank_name', 'User.last_payment Jméno banky: CharField '), ('User.last_payment.created', 'User.last_payment Datum vytvoření: DateTimeField '), ('User.last_payment.currency', 'User.last_payment Měna: CharField '), ('User.last_payment.date', 'User.last_payment Datum platby: DateField '), ('User.last_payment.done_by', 'User.last_payment Provedl: CharField '), ('User.last_payment.id', 'User.last_payment ID: AutoField '), ('User.last_payment.operation_id', 'User.last_payment ID Operace: CharField '), ('User.last_payment.order_id', 'User.last_payment ID objednávky: CharField '), ('User.last_payment.recipient_message', 'User.last_payment Zpráva pro příjemce: CharField '), ('User.last_payment.specification', 'User.last_payment Specifikace: CharField '), ('User.last_payment.transfer_note', 'User.last_payment Poznámka k převodu: CharField '), ('User.last_payment.transfer_type', 'User.last_payment Typ převodu: CharField '), ('User.last_payment.type', "User.last_payment Typ: CharField ('bank-transfer', 'cash', 'expected', 'darujme')"), ('User.last_payment.updated', 'User.last_payment Datum poslední změny: DateTimeField '), ('User.last_payment.user_donor_payment_channel', 'User.last_payment user donor payment channel: ForeignKey '), ('User.last_payment.user_identification', 'User.last_payment Identifikace odesílatele: CharField '), ('User.source.direct_dialogue', 'User.source Pochází z Direct dialogu: BooleanField '), ('User.source.id', 'User.source ID: AutoField '), ('User.source.name', 'User.source Jméno: CharField '), ('User.source.slug', 'User.source Identifikátor: SlugField '), ('UserInCampaign.activity_points', 'UserInCampaign Body za aktivitu: IntegerField '), ('UserInCampaign.additional_information', 'UserInCampaign Rozšiřující informace: TextField '), ('UserInCampaign.campaign', 'UserInCampaign campaign: ForeignKey '), ('UserInCampaign.created', 'UserInCampaign Datum vytvoření: DateTimeField '), ('UserInCampaign.email_confirmed', 'UserInCampaign Je potvrzeno e-mailem: BooleanField '), ('UserInCampaign.exceptional_membership', 'UserInCampaign Výjimečné členství: BooleanField '), ('UserInCampaign.expected_date_of_first_payment', 'UserInCampaign Očekávané datum první platby: DateField '), ('UserInCampaign.field_of_work', 'UserInCampaign Pracovní oblast: CharField '), ('UserInCampaign.gdpr_consent', 'UserInCampaign GDPR souhlas: BooleanField '), ('UserInCampaign.id', 'UserInCampaign ID: AutoField '), ('UserInCampaign.knows_us_from', 'UserInCampaign Odkud nás zná?: CharField '), ('UserInCampaign.next_communication_date', 'UserInCampaign Datum příští komunikace: DateField '), ('UserInCampaign.next_communication_method', "UserInCampaign Metoda příští komunikace: CharField ('email', 'phonecall', 'mail', 'personal', 'internal')"), ('UserInCampaign.note', 'UserInCampaign Poznámky: TextField '), ('UserInCampaign.old_account', 'UserInCampaign Starý účet: BooleanField '), ('UserInCampaign.other_support', 'UserInCampaign Jiná podpora: TextField '), ('UserInCampaign.public', 'UserInCampaign Zveřejnit mé jméno v seznamu podporovatelů/petentů této kampaně: BooleanField '), ('UserInCampaign.recruiter', 'UserInCampaign recruiter: ForeignKey '), ('UserInCampaign.registered_support', 'UserInCampaign Registrace podpory: DateTimeField '), ('UserInCampaign.regular_amount', 'UserInCampaign Částka pravidelné platby: PositiveIntegerField '), ('UserInCampaign.regular_frequency', "UserInCampaign Frekvence pravidelných plateb: CharField ('monthly', 'quaterly', 'biannually', 'annually', None)"), ('UserInCampaign.regular_payments', "UserInCampaign Pravidelné platby: CharField ('regular', 'onetime', 'promise')"), ('UserInCampaign.source', 'UserInCampaign Zdroj: ForeignKey '), ('UserInCampaign.updated', 'UserInCampaign Datum poslední změny: DateTimeField '), ('UserInCampaign.userprofile', 'UserInCampaign userprofile: ForeignKey '), ('UserInCampaign.variable_symbol', 'UserInCampaign Variabilní symbol: CharField '), ('UserInCampaign.verified', 'UserInCampaign Ověřen: BooleanField '), ('UserInCampaign.verified_by', 'UserInCampaign Ověřil: ForeignKey '), ('UserInCampaign.why_supports', 'UserInCampaign Proč nás podporuje?: TextField '), ('UserInCampaign.wished_information', 'UserInCampaign Zasílat pravidelné informace emailem: BooleanField '), ('UserInCampaign.wished_tax_confirmation', 'UserInCampaign Zaslat daňové potvrzení (na konci roku): BooleanField '), ('UserInCampaign.wished_welcome_letter', 'UserInCampaign Odeslat uvítací dopis s členskou kartou: BooleanField '), ('action', "Akce: CharField ('daily', 'new-user', 'new-payment')")], help_text='Value or variable on left-hand side', max_length=50, null=True, verbose_name='Variable'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='title_after',
            field=models.CharField(blank=True, max_length=15, null=True, verbose_name='Title after name'),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='title_before',
            field=models.CharField(blank=True, max_length=15, null=True, verbose_name='Title before name'),
        ),
        # Get data
        migrations.RunPython(
            code=set_user_model_data,
            reverse_code=django.db.migrations.operations.special.RunPython.noop,
        ),
    ]
