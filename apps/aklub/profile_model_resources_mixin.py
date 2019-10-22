# -*- coding: utf-8 -*-

from import_export import fields
from import_export.resources import ModelResource

from .models import (
    BankAccount, DonorPaymentChannel, Event, Preference,
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

def import_obj(self, obj, data, dry_run):  # noqa
    bank_account = BankAccount.objects.all().first()
    # Call this method only in the ProfileResource model resource subclass
    if hasattr(self, '_set_child_model_field_value'):
        self._set_child_model_field_value(obj=obj, data=data)
    obj.save()
    if data.get('username') == "":
        data["username"] = None
    if data.get('telephone'):
        telephone, _ = Telephone.objects.get_or_create(
            telephone=data['telephone'],
            user=obj,
            defaults={'is_primary': None},
        )
    if data.get("email") == "":
        data["email"] = None
    if data.get("email"):
        ProfileEmail.objects.get_or_create(
            email=data["email"],
            user=obj,
            defaults={'is_primary': True},
        )

    if data.get("administrative_units"):
        if not obj.administrative_units.filter(id=data["administrative_units"]):
            obj.administrative_units.add(data["administrative_units"])
            obj.save()
        preference, _ = Preference.objects.get_or_create(
            user=obj,
            administrative_unit=obj.administrative_units.get(id=data["administrative_units"]),
        )
        if data.get("newsletter_on") is not None:
            preference.newsletter_on = data['newsletter_on']
        if data.get("call_on") is not None:
            preference.call_on = data['call_on']
        if data.get("challenge_on") is not None:
            preference.challenge_on = data['challenge_on']
        if data.get("letter_on") is not None:
            preference.letter_on = data['letter_on']
        if data.get("send_mailing_lists") is not None:
            preference.send_mailing_lists = data['send_mailing_lists']
        if data.get("public") is not None:
            preference.public = data['public']

        preference.save()

    if data.get('event') and data.get('donor') == 'x':
        SS = data.get('SS', None)
        if data.get('VS') != "":
            VS = data['VS']
        else:
            from .views import generate_variable_symbol
            VS = generate_variable_symbol()
        event, _ = Event.objects.get_or_create(id=data['event'])
        donors, _ = DonorPaymentChannel.objects.get_or_create(
            user=obj,
            event=event,
            defaults={'VS': VS, 'SS': SS},
        )
        if data.get('bank_account') and data.get("administrative_units"):
            bank_account, _ = BankAccount.objects.get_or_create(bank_account_number=data['bank_account'])
            bank_account.administrative_unit = obj.administrative_units.get(id=data["administrative_units"])
            bank_account.save()

            donors.bank_account = bank_account
            donors.save()
        if data.get('user_bank_account'):
            user_bank_account, _ = UserBankAccount.objects.get_or_create(bank_account_number=data['user_bank_account'])
            donors.user_bank_account = user_bank_account
            donors.save()
    return super(ModelResource, self).import_obj(obj, data, dry_run)


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
                donor_list.append(f"bank_accout:{donor.bank_account.bank_account_number}\n")
            except AttributeError:
                donor_list.append('bank_accout:\n')
            try:
                donor_list.append(f"user_bank_account:{donor.user_bank_account.bank_account_number}\n")
            except AttributeError:
                donor_list.append(f"user_bank_account:\n")
            donor_list.append("\n")

    return "".join(tuple(donor_list))


def before_import_row(self, row, **kwargs):
    row['is_superuser'] = 0
    row['is_staff'] = 0
    row['email'] = row['email'].lower() if row.get('email') else ''


def import_field(self, field, obj, data, is_m2m=False):
    if field.attribute and field.column_name in data:  # and not getattr(obj, field.column_name):
        field.save(obj, data, is_m2m)


def get_profile_model_resource_mixin_class_body():
    body = {}
    body['import_obj'] = import_obj
    body['dehydrate_telephone'] = dehydrate_telephone
    body['dehydrate_donor'] = dehydrate_donor
    body['before_import_row'] = before_import_row
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
