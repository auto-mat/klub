# -*- coding: utf-8 -*-
import datetime

from django.core.exceptions import ValidationError
from django.utils.timezone import make_aware
from django.utils.translation import ugettext_lazy as _

from events.models import Event

from import_export import fields
from import_export.resources import ModelResource

from .models import (
    BankAccount, CompanyContact, DonorPaymentChannel, Preference,
    ProfileEmail, Telephone, UserBankAccount,
)


def get_preference_model_fields():
    """ Get Preference model fields """
    exclude_fields = ('id', 'user', 'administrative_unit')
    fields = Preference._meta.fields

    return [field.name for field in fields if field.name not in exclude_fields]


def dehydrate_base(self, profile):
    pass


def get_profile_model_resource_custom_fields():
    """ Get profile model resource custom fields """
    _fields = ['telephone', 'donor']
    _fields.extend(get_preference_model_fields())
    result = {}
    for field in _fields:
        result[field] = fields.Field()

    return result


def save_email(email, obj):
    # needs to be done, because company profile can't have multiple primary emails
    email, _ = ProfileEmail.objects.get_or_create(
        email=email,
        user=obj,
        defaults={'is_primary': True},
    )
    if not ProfileEmail.objects.filter(user=obj, is_primary=True):
        email.is_primary = True
        email.save()
    return email


def new_objects_validations(check, errors):
    for key in check.keys():
        try:
            check[key].full_clean()
        except Exception as e:  # noqa
            e.update_error_dict(errors)
    if errors:
        raise ValidationError(errors)


def import_obj(self, obj, data, dry_run):  # noqa
    check = {}
    errors = {}
    # Call this method only in the ProfileResource model resource subclass
    if hasattr(self, '_set_child_model_field_value'):
        self._set_child_model_field_value(obj=obj, data=data)
    # profile signal for m2m is called during import and save data...
    # we add dry_run to obj and solve it in signal to avoid it
    obj.dry_run = dry_run
    obj.save()
    if data.get('date_joined'):
        # firstly to datetime then to timezone
        try:
            local_time = datetime.datetime.strptime(data.get('date_joined'), '%Y-%m-%d %H:%M:%S')
            obj.date_joined = make_aware(local_time)
        except Exception as e: # noqa
            errors['date_joined'] = e

    if obj.is_userprofile():
        if data.get('telephone'):
            check['telephone'], _ = Telephone.objects.get_or_create(
                telephone=data['telephone'],
                user=obj,
                defaults={'is_primary': True},
            )
        if data.get("email"):
            check['email'] = save_email(data['email'], obj)
    else:
        if data.get('telephone') or data.get("email"):
            company_contact, _ = CompanyContact.objects.get_or_create(
                telephone=data.get('telephone'),
                email=data.get("email"),
                company=obj,
                administrative_unit_id=data["administrative_units"],
                defaults={
                    'is_primary': True,
                    },
                )
            if not company_contact.contact_first_name and not company_contact.contact_last_name:
                company_contact.contact_first_name = data.get('contact_first_name')
                company_contact.contact_last_name = data.get('contact_last_name')
                company_contact.save()

    if data.get("administrative_units"):
        if not obj.administrative_units.filter(id=data["administrative_units"]):
            obj.administrative_units.add(data["administrative_units"])
            obj.save()
        check['preference'], _ = Preference.objects.get_or_create(
            user=obj,
            administrative_unit=obj.administrative_units.get(id=data["administrative_units"]),
            defaults={
                "newsletter_on": data['newsletter_on'],
                "call_on": data['call_on'],
                "challenge_on": data['challenge_on'],
                "letter_on": data['letter_on'],
                "send_mailing_lists": data['send_mailing_lists'],
                "public": data['public'],
            },
        )
        # allow update if user has permisison....
        if self.user.has_perm("can_edit_during_importing") and data.get('allow_edit') == "x":
            check['preference'].newsletter_on = data['newsletter_on']
            check['preference'].call_on = data['call_on']
            check['preference'].challenge_on = data['challenge_on']
            check['preference'].letter_on = data['letter_on']
            check['preference'].send_mailing_lists = data['send_mailing_lists']
            check['preference'].public = data['public']

        if data.get('country'):
            obj.country = data['country']
        if data.get('correspondence_country'):
            obj.correspondence_country = data['correspondence_country']

    if data.get('event') and data.get('bank_account') and data.get('donor') == 'x':
        can_create_dpch = True
        SS = data.get('SS', None)
        try:
            check['bank_account'] = BankAccount.objects.get(id=data['bank_account'])
        except Exception as e: # noqa
            errors['bank_account'] = e
            can_create_dpch = False
        try:
            check['event'] = Event.objects.get(id=data['event'])
        except Exception as e: # noqa
            errors['event'] = e
            can_create_dpch = False
        if can_create_dpch:
            check['donors'], _ = DonorPaymentChannel.objects.get_or_create(
                    user=obj,
                    event=check['event'],
                    defaults={'SS': SS, 'money_account': check['bank_account']},
                )
            if data.get('VS') != "" and _:
                check['donors'].VS = data.get('VS')

            check['donors'].money_account = check['bank_account']
            check['donors'].full_clean()
            check['donors'].save()

            if data.get('user_bank_account'):
                check['user_bank_account'], _ = UserBankAccount.objects.get_or_create(bank_account_number=data['user_bank_account'])
                check['donors'].user_bank_account = check['user_bank_account']
                check['donors'].save()
    new_objects_validations(check, errors)
    if check.get('preference'):
        check['preference'].save()
    super(ModelResource, self).import_obj(obj, data, dry_run)


def save_m2m(self, *args, **kwargs):
    """
    overriding the original save_m2m, because we don't want to
    update original objects, we want to keep them and add more of them.
    TODO: if more fields with m2m will be imported for model Profile, this must be edited.
    """
    pass


def dehydrate_telephone(self, profile):
    return profile.get_telephone([self.administrative_unit])


def dehydrate_send_mailing_lists(self, profile):
    if profile.pk:
        return profile.preference_set.get(administrative_unit=self.administrative_unit).send_mailing_lists


def dehydrate_newsletter_on(self, profile):
    if profile.pk:
        return profile.preference_set.get(administrative_unit=self.administrative_unit).newsletter_on


def dehydrate_call_on(self, profile):
    if profile.pk:
        return profile.preference_set.get(administrative_unit=self.administrative_unit).call_on


def dehydrate_challenge_on(self, profile):
    if profile.pk:
        return profile.preference_set.get(administrative_unit=self.administrative_unit).challenge_on


def dehydrate_letter_on(self, profile):
    if profile.pk:
        return profile.preference_set.get(administrative_unit=self.administrative_unit).letter_on


def dehydrate_public(self, profile):
    if profile.pk:
        return profile.preference_set.get(administrative_unit=self.administrative_unit).public


def dehydrate_donor(self, profile):
    donor_list = []
    for donor in profile.userchannels.all():
        if donor:
            donor_list.append(f"VS:{donor.VS}\n")
            try:
                donor_list.append(f"event:{donor.event.name}\n")
            except AttributeError:
                donor_list.append('event:\n')
            try:
                donor_list.append(f"bank_accout:{donor.money_account.bank_account_number}\n")
            except AttributeError:
                donor_list.append('bank_accout:\n')
            try:
                donor_list.append(f"user_bank_account:{donor.user_bank_account.bank_account_number}\n")
            except AttributeError:
                donor_list.append("user_bank_account:\n")
            donor_list.append("\n")

    return "".join(tuple(donor_list))


def before_import(self, *args, **kwargs):
    # by celery or by classic import
    if hasattr(self, "import_job"):
        self.user = self.import_job.updated_by
        self.administrative_unit = self.import_job.importconnector.administrative_unit
    else:
        self.user = kwargs.get("user")
        self.administrative_unit = self.user.administrated_units.first()
    if not self.administrative_unit or not self.user:
        raise ValidationError(_("user or administrative_unit is not set for this import!"))


def before_import_row(self, row, **kwargs):
    row['is_superuser'] = 0
    row['is_staff'] = 0
    row['email'] = row['email'].lower() if row.get('email') else ''
    if row.get('username') == "":
        row["username"] = None
    if not row['administrative_units'] or row['administrative_units'] != str(self.administrative_unit.id):
        raise ValidationError(
            {'administrative_units': _('This field must be set or you are trying to import to another administrated_unit')}
        )


def import_field(self, field, obj, data, is_m2m=False):
    """dehydrate_donor
    rewrite original method to avoid data rewriting
    """
    if field.attribute and field.column_name in data:
        if getattr(obj, field.column_name) in ("", None, 'unknown'):
            field.save(obj, data, is_m2m)
        elif field.column_name == "note":
            if data['note'] not in obj.note:
                data['note'] = obj.note + '\n' + data.get('note')
                field.save(obj, data, is_m2m)
        elif field.column_name == "username" and data.get('username'):
            field.save(obj, data, is_m2m)


def get_profile_model_resource_mixin_class_body():
    # Custom fields (dehydrate funcs)
    body = {}
    body.update(get_profile_model_resource_custom_fields())
    # Preference model dehydrate funcs
    body['import_obj'] = import_obj
    body['dehydrate_telephone'] = dehydrate_telephone
    body['dehydrate_donor'] = dehydrate_donor
    body['dehydrate_send_mailing_lists'] = dehydrate_send_mailing_lists
    body['dehydrate_newsletter_on'] = dehydrate_newsletter_on
    body['dehydrate_call_on'] = dehydrate_call_on
    body['dehydrate_challenge_on'] = dehydrate_challenge_on
    body['dehydrate_letter_on'] = dehydrate_letter_on
    body['dehydrate_public'] = dehydrate_public
    body['before_import_row'] = before_import_row
    body['before_import'] = before_import
    body['save_m2m'] = save_m2m
    body['import_field'] = import_field
    return body


ProfileModelResourceMixin = type(
    'ProfileModelResourceMixin',
    (ModelResource,),
    get_profile_model_resource_mixin_class_body(),
)
