# -*- coding: utf-8 -*-
import datetime

from django.core.exceptions import ValidationError
from django.utils.timezone import make_aware

from import_export import fields
from import_export.resources import ModelResource

from .models import (
    BankAccount, CompanyContact, DonorPaymentChannel, Event, Preference,
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


def preference_model_dehydrate_decorator(field):
    def wrap(f):
        def wrapped_f(self, profile):
            if profile.pk:
                preference = profile.preference_set.filter(
                    administrative_unit=profile.administrated_units.first(),
                ).first()
                if preference:
                    return getattr(preference, field)
        return wrapped_f
    return wrap


def get_preference_model_custom_field_dehydrate_func():
    funcs = {}
    fields = get_preference_model_fields()
    for field in fields:
        func_name = 'dehydrate_{}'.format(field)
        funcs[func_name] = (preference_model_dehydrate_decorator(field=field))(dehydrate_base)

    return funcs


def save_email(email, obj):
    # needs to be done, because company profile can't have multiple primary emails
    email, _ = ProfileEmail.objects.get_or_create(
        email=email,
        user=obj,
        defaults={'is_primary': None},
    )
    if not ProfileEmail.objects.filter(user=obj, is_primary=True):
        email.is_primary = True
        email.save()
    return email


def new_objects_validations(check, errors):
    for key in check.keys():
        try:
            check[key].full_clean()
        except Exception as e:
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
        except Exception as e:
            errors['date_joined'] = e

    if obj.is_userprofile():
        if data.get('telephone'):
            check['telephone'], _ = Telephone.objects.get_or_create(
                telephone=data['telephone'],
                user=obj,
                defaults={'is_primary': None},
            )
        if data.get("email"):
            check['email'] = save_email(data['email'], obj)
    else:
        if data.get('telephone') or data.get("email"):
            email, _ = CompanyContact.objects.get_or_create(
                telephone=data.get('telephone'),
                email=data.get("email"),
                company=obj,
                administrative_unit_id=data["administrative_units"],
                defaults={
                    'is_primary': None,
                    },
                )
            if not email.contact_first_name and not email.contact_last_name:
                email.contact_first_name = data.get('contact_first_name')
                email.contact_last_name = data.get('contact_last_name')
                email.save()

    if data.get("administrative_units"):
        if not obj.administrative_units.filter(id=data["administrative_units"]):
            obj.administrative_units.add(data["administrative_units"])
            obj.save()
        check['preference'], _ = Preference.objects.get_or_create(
            user=obj,
            administrative_unit=obj.administrative_units.get(id=data["administrative_units"]),
        )
        if data.get("newsletter_on") is not None:
            check['preference'].newsletter_on = data['newsletter_on']
        if data.get("call_on") is not None:
            check['preference'].call_on = data['call_on']
        if data.get("challenge_on") is not None:
            check['preference'].challenge_on = data['challenge_on']
        if data.get("letter_on") is not None:
            check['preference'].letter_on = data['letter_on']
        if data.get("send_mailing_lists") is not None:
            check['preference'].send_mailing_lists = data['send_mailing_lists']
        if data.get("public") is not None:
            check['preference'].public = data['public']

    if data.get('event') and data.get('bank_account') and data.get('donor') == 'x':
        can_create_dpch = True
        SS = data.get('SS', None)
        try:
            check['bank_account'] = BankAccount.objects.get(bank_account_number=data['bank_account'])
        except Exception as e:
            errors['bank_account'] = e
            can_create_dpch = False
        try:
            check['event'] = Event.objects.get(id=data['event'])
        except Exception as e:
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
    return profile.get_telephone()


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


def before_import_row(self, row, **kwargs):
    row['is_superuser'] = 0
    row['is_staff'] = 0
    row['email'] = row['email'].lower() if row.get('email') else ''
    if row.get('username') == "":
        row["username"] = None
    if not row['administrative_units']:
        raise ValidationError({'administrative_units': 'This field must be set'})


def import_field(self, field, obj, data, is_m2m=False):
    """
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
    body = {}
    body['import_obj'] = import_obj
    body['dehydrate_telephone'] = dehydrate_telephone
    body['dehydrate_donor'] = dehydrate_donor
    body['before_import_row'] = before_import_row
    body['save_m2m'] = save_m2m
    body['import_field'] = import_field
    # Custom fields (dehydrate funcs)
    body.update(get_profile_model_resource_custom_fields())
    # Preference model dehydrate funcs
    body.update(get_preference_model_custom_field_dehydrate_func())

    return body


ProfileModelResourceMixin = type(
    'ProfileModelResourceMixin',
    (ModelResource,),
    get_profile_model_resource_mixin_class_body(),
)
