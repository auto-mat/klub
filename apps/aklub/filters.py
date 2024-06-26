# custom filters

import operator
from datetime import date, timedelta
from functools import reduce
from abc import ABC

from django.contrib import messages
from django.contrib.admin import SimpleListFilter
from django.contrib.admin.filters import FieldListFilter, RelatedFieldListFilter
from django.contrib.admin.utils import reverse_field_path
from django.db.models import (
    BooleanField,
    Case,
    CharField,
    Count,
    F,
    FloatField,
    IntegerField,
    OuterRef,
    Q,
    Subquery,
    Sum,
    Value,
    When,
)
from django.db.models.functions import Lower, Replace, Right
from django.utils.translation import ugettext as _

from interactions.models import Interaction

from aklub.models import (
    CompanyContact,
    CompanyProfile,
    DonorPaymentChannel,
    ProfileEmail,
    Telephone,
    UserProfile,
)


class ProfileMultiSelectDonorEvent(FieldListFilter):
    """
    allowe to multiple events from filters
    """

    def __init__(self, field, request, params, model, model_admin, field_path):
        self.lookup_kwarg = field_path + "__in"
        self.lookup_kwarg_isnull = field_path + "__isnull"

        super().__init__(field, request, params, model, model_admin, field_path)
        self.title = _("Donor's event")

        self.lookup_val = self.used_parameters.get(self.lookup_kwarg, [])
        if len(self.lookup_val) == 1 and self.lookup_val[0] == "":
            self.lookup_val = []
        self.lookup_val_isnull = self.used_parameters.get(self.lookup_kwarg_isnull)

        self.empty_value_display = model_admin.get_empty_value_display()
        parent_model, reverse_path = reverse_field_path(model, field_path)

        if model == parent_model:
            queryset = model_admin.get_queryset(request)
        else:
            queryset = parent_model._default_manager.all()

        if request.user.has_perm("can_edit_all_units"):
            look_up = queryset.distinct().order_by(field.name)
        else:
            look_up = (
                queryset.filter(
                    administrative_units__in=request.user.administrated_units.all()
                )
                .distinct()
                .order_by(field.name)
            )
        self.lookup_choices = [(event.id, event.name) for event in look_up]

    def expected_parameters(self):
        return [self.lookup_kwarg, self.lookup_kwarg_isnull]

    def choices(self, changelist):
        yield {
            "selected": not self.lookup_val and self.lookup_val_isnull is None,
            "query_string": changelist.get_query_string(
                remove=[self.lookup_kwarg, self.lookup_kwarg_isnull]
            ),
            "display": _("All"),
        }
        include_none = False
        for lookup, title in self.lookup_choices:
            if lookup is None:
                include_none = True
                continue
            lookup = str(lookup)

            if lookup in self.lookup_val:
                values = [v for v in self.lookup_val if v != lookup]
            else:
                values = self.lookup_val + [lookup]

            if values:
                yield {
                    "selected": lookup in self.lookup_val,
                    "query_string": changelist.get_query_string(
                        {self.lookup_kwarg: ",".join(values)},
                        [self.lookup_kwarg_isnull],
                    ),
                    "display": title,
                }
            else:
                yield {
                    "selected": lookup in self.lookup_val,
                    "query_string": changelist.get_query_string(
                        remove=[self.lookup_kwarg]
                    ),
                    "display": title,
                }

        if include_none:
            yield {
                "selected": bool(self.lookup_val_isnull),
                "query_string": changelist.get_query_string(
                    {self.lookup_kwarg_isnull: "True"}, [self.lookup_kwarg]
                ),
                "display": self.empty_value_display,
            }


class PreferenceMailingListAllowed(SimpleListFilter):
    title = _("Mailing list allowed")
    parameter_name = "mailing_list_allowed"

    def lookups(self, request, model_admin):
        return (("yes", _("Yes")), ("no", _("No")), ("unknown", _("Unknown")))

    def queryset(self, request, queryset):
        filters = {}
        if not request.user.has_perm("can_edit_all_units"):
            filters.update(
                {
                    "preference__administrative_unit": request.user.administrated_units.first()
                }
            )

        if self.value() == "yes":
            filters.update({"preference__send_mailing_lists": True})
            queryset = queryset.filter(**filters)
        elif self.value() == "no":
            filters.update({"preference__send_mailing_lists": False})
            queryset = queryset.filter(**filters)
        elif self.value() == "unknown":
            filters.update({"preference__send_mailing_lists": None})
            queryset = queryset.filter(**filters)
        return queryset


class IsUserInCompanyProfile(SimpleListFilter):
    title = _("Is UserProfile in CompanyContact?")
    parameter_name = "us_userprofile_in_companycontact"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Yes")),
            ("no", _("No")),
        )

    def queryset(self, request, queryset):
        if self.value():
            emails = ProfileEmail.objects.filter(
                user_id__in=queryset.values_list("id", flat=True)
            )
            filter_kwargs = {"email__in": emails.values_list("email", flat=True)}
            if not request.user.has_perm("can_edit_all_units"):
                filter_kwargs[
                    "company__administrative_units__in"
                ] = request.user.administrated_units.all()
                filter_kwargs[
                    "administrative_unit__in"
                ] = request.user.administrated_units.all()
            # duplicate emails
            contacts = CompanyContact.objects.filter(**filter_kwargs)
            profile_emails = ProfileEmail.objects.filter(
                email__in=contacts.values_list("email", flat=True)
            )
            if self.value() == "yes":
                queryset = queryset.filter(id__in=profile_emails.values_list("user_id"))
            elif self.value() == "no":
                queryset = queryset.exclude(
                    id__in=profile_emails.values_list("user_id")
                )
            return queryset


class ProfileHasFullAdress(SimpleListFilter):
    title = _("Full adress")
    parameter_name = "full_adress"

    def lookups(self, request, model_admin):
        return (
            ("full_address", _("Complete address")),
            ("not_full_address", _("Not complete address")),
        )

    def queryset(self, request, queryset):
        if self.value() == "full_address":
            return queryset.filter(
                ~Q(user_profile__street=""),
                ~Q(user_profile__city=""),
                ~Q(user_profile__zip_code=""),
                ~Q(user_profile__country=""),
            )
        elif self.value() == "not_full_address":
            return queryset.filter(
                Q(user_profile__street="")
                | Q(user_profile__city="")
                | Q(user_profile__zip_code="")
                | Q(user_profile__country=""),
            )
        else:
            return queryset


class ProfileHasEmail(SimpleListFilter):
    title = _("Has primary email")
    parameter_name = "profile_email"

    def lookups(self, request, model_admin):
        return (
            ("Yes", _("Yes")),
            ("No", _("No")),
        )

    def queryset(self, request, queryset):
        if self.value() == "No":
            return queryset.filter(
                email_address_user__isnull=True,
                email_address_company__isnull=True,
            )
        elif self.value() == "Yes":
            return queryset.filter(
                ~Q(
                    email_address_user__isnull=True,
                    email_address_company__isnull=True,
                ),
            )
        else:
            return queryset


class NullFieldFilter(SimpleListFilter):
    """This fiters nullable fields by
        'All' (no filter),
        'Empty' (field__isnull=True filter)
        'Filled in' (not null).

    Child classes must override the field attribute
    to specify which field this filter should be applied to."""

    field = None

    def lookups(self, request, model_admin):
        return (("filled", _("Filled-in")), ("empty", _("Empty")))

    def queryset(self, request, queryset):
        if not self.value():
            return queryset
        return queryset.filter(
            **{"%s__isnull" % self.field: self.value() == "empty" and True}
        )


class PaymentsAssignmentsFilter(NullFieldFilter):
    field = "user_donor_payment_channel"
    title = _("User assignment")
    parameter_name = "user_assignment"


class ActiveCampaignFilter(SimpleListFilter):
    title = "Active"
    parameter_name = "active"

    def lookups(self, request, model_admin):
        return (
            ("yes", _("Yes")),
            ("no", _("No")),
        )

    def queryset(self, request, queryset):
        if self.value() == "yes":
            return queryset.filter(
                Q(date_to__gte=date.today()) | Q(date_to=None),
                date_from__lte=date.today(),
            )
        if self.value() == "no":
            return queryset.exclude(
                Q(date_to__gte=date.today()) | Q(date_to=None),
                date_from__lte=date.today(),
            )
        return queryset


class EmailFilter(SimpleListFilter):
    title = _("Email")
    parameter_name = "email"

    def lookups(self, request, model_admin):
        return (
            ("duplicate", _("Duplicate")),
            ("email-format", _("Not in e-mail format")),
            ("blank", _("Blank")),
        )

    def queryset(self, request, queryset):  # noqa
        if self.value():
            if not queryset:
                return queryset
            if queryset.first().is_userprofile():
                blank_filter = Q(profileemail__email__exact="") | Q(
                    profileemail__email__isnull=True
                )
            else:
                blank_filter = Q(companycontact__email__exact="") | Q(
                    companycontact__email__isnull=True
                )

            if self.value() == "blank":
                return queryset.filter(blank_filter)
            else:
                queryset = queryset.exclude(blank_filter)

            if self.value() == "duplicate":
                if queryset.first().is_userprofile():
                    # right now.. this shoud never ever return smth cuz of model definition.
                    duplicates = (
                        ProfileEmail.objects.filter(
                            email__isnull=False, user__isnull=False
                        )
                        .exclude(email__exact="")
                        .annotate(email_lower=Lower("email"))
                        .values("email_lower")
                        .annotate(Count("id"))
                        .values("email_lower")
                        .order_by()
                        .filter(id__count__gt=1)
                        .values_list("email_lower", flat=True)
                    )
                    duplicates = ProfileEmail.objects.annotate(
                        email_lower=Lower("email")
                    ).filter(email_lower__in=duplicates)
                    return queryset.filter(profileemail__in=duplicates)
                else:
                    if request.user.has_perm("can_edit_all_units"):
                        filter_kwargs = {}
                    else:
                        filter_kwargs = {
                            "administrative_unit__in": request.user.administrated_units.all()
                        }

                    duplicates = (
                        CompanyContact.objects.filter(email__isnull=False)
                        .filter(**filter_kwargs)
                        .exclude(email__exact="")
                        .annotate(email_lower=Lower("email"))
                        .values("email_lower")
                        .annotate(Count("company", distinct=True))
                        .filter(company__count__gt=1)
                        .values_list("email_lower", flat=True)
                    )
                    duplicates = CompanyContact.objects.annotate(
                        email_lower=Lower("email")
                    ).filter(email_lower__in=duplicates)
                    return queryset.filter(companycontact__in=duplicates)

            if self.value() == "email-format":
                if queryset.first().is_userprofile():
                    return queryset.exclude(
                        profileemail__email__iregex=r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+$)"
                    )
                else:
                    return queryset.exclude(
                        companycontact__email__iregex=r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9.-]+$)"
                    )
        return queryset


class RegularPaymentsFilter(SimpleListFilter):
    title = _("Regular payments in time")
    parameter_name = "regular_payments"

    def lookups(self, request, model_admin):
        return (
            ("not-delayed", _("Not delayed")),
            ("delayed", _("Delayed")),
        )

    def queryset(self, request, queryset):
        """
        In this filter we dont have to handle administrative units, because event is required for filter,
        thats good because user under AU can select only events under his AU
        """

        if self.value() == "not-delayed":
            queryset = queryset.filter(
                userchannels__expected_regular_payment_date__gt=date.today()
                - timedelta(days=11),
                userchannels__regular_payments="regular",
            )
        if self.value() == "delayed":
            queryset = queryset.filter(
                userchannels__expected_regular_payment_date__lt=date.today()
                - timedelta(days=11),
                userchannels__regular_payments="regular",
            )

        return queryset


class TelephoneFilter(SimpleListFilter):
    title = _("Telephone")
    parameter_name = "telephone"

    def lookups(self, request, model_admin):
        return (
            ("duplicate", _("Duplicate")),
            ("bad-format", _("Not in telephone format")),
            ("blank", _("Blank")),
        )

    def queryset(self, request, queryset):  # noqa
        if self.value():
            if not queryset:
                return queryset
            if queryset.first().is_userprofile():
                blank_filter = Q(telephone__telephone__exact="") | Q(
                    telephone__telephone__isnull=True
                )
            else:
                blank_filter = Q(companycontact__telephone__exact="") | Q(
                    companycontact__telephone__isnull=True
                )

            if self.value() == "blank":
                return queryset.filter(blank_filter)
            else:
                queryset = queryset.exclude(blank_filter)
            if self.value() == "duplicate":
                filter_kwargs = {}
                # check what perm admin has
                if queryset.first().is_userprofile():
                    if not request.user.has_perm("aklub.can_edit_all_units"):
                        filter_kwargs = {
                            "user__administrative_units__in": request.user.administrated_units.all()
                        }
                    # TODO: shoud be nicer
                    duplicate = (
                        Telephone.objects.annotate(
                            clean_telephone=Right(
                                Replace("telephone", Value(" "), Value("")),
                                9,
                            )
                        )
                        .values("clean_telephone")
                        .filter(**filter_kwargs)
                        .annotate(total_clean=Count("clean_telephone"))
                        .filter(total_clean__gt=1)
                        .values_list("clean_telephone", flat=True)
                    )

                    users_ids = (
                        Telephone.objects.annotate(
                            clean_telephone=Right(
                                Replace("telephone", Value(" "), Value("")),
                                9,
                            )
                        )
                        .filter(clean_telephone__in=duplicate)
                        .order_by("clean_telephone")
                        .values_list("user", flat=True)
                        .order_by("clean_telephone")
                    )
                    return queryset.filter(id__in=users_ids).distinct()
                else:
                    if not request.user.has_perm("aklub.can_edit_all_units"):
                        filter_kwargs = {
                            "company__administrative_units__in": request.user.administrated_units.all()
                        }
                    # TODO: shoud be nicer
                    duplicate = (
                        CompanyContact.objects.filter(**filter_kwargs)
                        .annotate(
                            clean_telephone=Right(
                                Replace("telephone", Value(" "), Value("")),
                                9,
                            )
                        )
                        .values("clean_telephone")
                        .annotate(total_clean=Count("clean_telephone"))
                        .filter(total_clean__gt=1)
                        .values_list("clean_telephone", flat=True)
                    )

                    companies_ids = (
                        CompanyContact.objects.annotate(
                            clean_telephone=Right(
                                Replace("telephone", Value(" "), Value("")),
                                9,
                            )
                        )
                        .filter(clean_telephone__in=duplicate)
                        .order_by("clean_telephone")
                        .values_list("company", flat=True)
                        .order_by("clean_telephone")
                    )
                    return queryset.filter(id__in=companies_ids).distinct()

            if self.value() == "bad-format":
                if queryset.first().is_userprofile():
                    return queryset.exclude(
                        telephone__telephone__iregex=r"^\+?([0-9] *){9,}$"
                    )
                else:
                    return queryset.exclude(
                        companycontact__telephone__iregex=r"^\+?([0-9] *){9,}$"
                    )

        return queryset


class ProfileTypeFilter(SimpleListFilter):
    title = _("Profile type")
    parameter_name = "user__polymorphic_ctype__model"

    def lookups(self, request, model_admin):
        return (
            ("companyprofile", _("Company")),
            ("userprofile", _("User")),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(user__polymorphic_ctype__model=self.value())
        return queryset


class NameFilter(SimpleListFilter):
    title = _("Name")
    parameter_name = "name"

    def lookups(self, request, model_admin):
        return (
            ("duplicate", _("Duplicate")),
            ("blank", _("Blank")),
        )

    def queryset(self, request, queryset):
        user_profile_qs = queryset.instance_of(UserProfile)
        company_profile_qs = queryset.instance_of(CompanyProfile)
        if self.value() == "duplicate":
            if user_profile_qs:
                duplicates = UserProfile.objects.filter(
                    first_name__isnull=False, last_name__isnull=False
                )
                duplicates = duplicates.exclude(
                    first_name__exact="", last_name__exact=""
                )
                duplicates = duplicates.values("first_name", "last_name")
                duplicates = duplicates.annotate(Count("id"))
                duplicates = duplicates.values("first_name", "last_name", "id")
                duplicates = duplicates.order_by()
                duplicates = duplicates.filter(id__count__gt=1)
                duplicates = duplicates.values_list("first_name", "last_name")
                query = reduce(
                    operator.or_,
                    (Q(first_name=fn, last_name=ln) for fn, ln in duplicates),
                )
                return queryset.filter(query)
            if company_profile_qs:
                duplicates = CompanyProfile.objects.filter(name__isnull=False)
                duplicates = duplicates.exclude(name__exact="")
                duplicates = duplicates.values("name")
                duplicates = duplicates.annotate(Count("id"))
                duplicates = duplicates.values("name", "id")
                duplicates = duplicates.order_by()
                duplicates = duplicates.filter(id__count__gt=1)
                duplicates = duplicates.values_list("name", flat=True)
                query = reduce(
                    operator.or_,
                    (Q(name=name) for name in duplicates),
                )
                return queryset.filter(query)

        if self.value() == "blank":
            if user_profile_qs:
                return queryset.filter(
                    (Q(first_name__exact="") or Q(first_name__isnull=True))
                    and (Q(last_name__exact="") or Q(last_name__isnull=True)),
                )
            if company_profile_qs:
                return queryset.filter(
                    Q(name__exact="") or Q(name__isnull=True),
                )
        return queryset


class UnitFilter(RelatedFieldListFilter):
    def field_choices(self, field, request, model_admin):
        if request.user.has_perm("aklub.can_edit_all_units"):
            return field.get_choices(include_blank=False)
        else:
            return field.get_choices(
                include_blank=False,
                limit_choices_to={"pk__in": request.user.administrated_units.all()},
            )


class AdministrativeUnitAdminMixin(object):
    queryset_unit_param = "administrative_units"

    def get_queryset(self, request):
        self.request = request
        queryset = super().get_queryset(request)
        if request.user.has_perm("aklub.can_edit_all_units"):
            return queryset
        kwargs = {
            self.queryset_unit_param + "__in": request.user.administrated_units.all()
        }
        return queryset.filter(
            **kwargs
        ).distinct()  # The distinct is necessarry here for unit admins, that have more cities

    def lookup_allowed(self, key, value):
        allowed_lookups = (
            self.queryset_unit_param,
            self.queryset_unit_param + "__id__exact",
            self.queryset_unit_param + "__isnull",
        )
        if key in allowed_lookups:
            return True
        return super().lookup_allowed(key, value)

    def gate_admined_units(self, db_field, request, **kwargs):
        if not request.user.has_perm("aklub.can_edit_all_units"):
            administrated_units = request.user.administrated_units.all()
            if db_field.name == self.queryset_unit_param:
                kwargs["queryset"] = administrated_units
                kwargs["required"] = True
                if administrated_units.count() == 1:
                    kwargs["initial"] = administrated_units
        return kwargs

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        kwargs = self.gate_admined_units(db_field, request, **kwargs)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        kwargs = self.gate_admined_units(db_field, request, **kwargs)
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def get_list_filter(self, request):
        list_filter = ((self.queryset_unit_param, UnitFilter),) + tuple(
            super().get_list_filter(request)
        )
        return list_filter


def unit_admin_mixin_generator(queryset_unit):
    class AUAMixin(AdministrativeUnitAdminMixin):
        queryset_unit_param = queryset_unit

    return AUAMixin


class BaseAF:
    @property
    def get_field(self):
        return self.field.split("__")[0]

    def __str__(self):
        return f"{self.model._meta.model_name}.{self.field.split('__')[0]}"


class DPCHRegularPayments(BaseAF):
    model = DonorPaymentChannel
    field = "regular_payments"
    values_list_field = "user__id"

    def query(self, *args, **kwargs):
        return {
            "userchannels__event__administrative_units__in": list(
                kwargs.get("administrative_unit").values_list(
                    "id",
                    flat=True,
                ),
            ),
        }

    def queryset(self, *args, **kwargs):
        if kwargs.get("administrative_unit"):
            queryset = self.model.objects.filter(
                **self.query(*args, **kwargs),
            )
        else:
            queryset = self.model.objects.none()
        return queryset


class DPCHRegularFrequency(DPCHRegularPayments):
    field = "regular_frequency"


class DPCHNumberOfPayments(BaseAF):
    model = DonorPaymentChannel
    field = "number_of_payments_conflict"
    field_verbose_name = _("Number of payments")
    values_list_field = "user__id"
    field_type = IntegerField()

    def queryset(self, *args, **kwargs):
        if kwargs.get("administrative_unit"):
            au = kwargs["administrative_unit"]
            subquery = (
                self.model.objects.filter(
                    event__administrative_units__in=au,
                    user=OuterRef("user"),
                )
                .values("user")
                .annotate(
                    number_of_payments_conflict=Count("payment__amount"),
                )
            )
            queryset = self.model.objects.filter(
                event__administrative_units__in=au,
            ).annotate(
                number_of_payments_conflict=Subquery(
                    subquery.values("number_of_payments_conflict")[:1],
                    output_field=self.field_type,
                ),
            )
        else:
            queryset = self.model.objects.none()
        return queryset


class DPCHSumOfAllPayments(BaseAF):
    model = DonorPaymentChannel
    field = "sum_off_all_payments"
    field_verbose_name = _("Sum of all payments")
    values_list_field = "user__id"
    field_type = FloatField()

    def queryset(self, *args, **kwargs):
        if kwargs.get("administrative_unit"):
            au = kwargs["administrative_unit"]
            subquery = (
                self.model.objects.filter(
                    event__administrative_units__in=au,
                    user=OuterRef("user"),
                )
                .values("user")
                .annotate(
                    sum_off_all_payments=Sum("payment__amount"),
                )
            )
            queryset = (
                self.model.objects.filter(
                    event__administrative_units__in=au,
                )
                .annotate(
                    sum_off_all_payments=Subquery(
                        subquery.values("sum_off_all_payments")[:1],
                        output_field=self.field_type,
                    ),
                )
                .annotate(
                    sum_off_all_payments=Case(
                        When(
                            sum_off_all_payments__isnull=True,
                            then=Value(0.0),
                        ),
                        default=F("sum_off_all_payments"),
                        output_field=self.field_type,
                    ),
                )
            )
        else:
            queryset = self.model.objects.none()
        return queryset


class DPCHWithoutPayments(BaseAF):
    model = DonorPaymentChannel
    field = "without_payments"
    field_verbose_name = _("Without payments")
    values_list_field = "user__id"
    field_type = BooleanField()

    def queryset(self, *args, **kwargs):
        if kwargs.get("administrative_unit"):
            au = kwargs["administrative_unit"]
            queryset = self.model.objects.filter(
                event__administrative_units__in=au,
            ).annotate(
                without_payments=Case(
                    When(
                        number_of_payments__isnull=True,
                        then=Value(True),
                    ),
                    default=Value(False),
                    output_field=self.field_type,
                ),
            )
        else:
            queryset = self.model.objects.none()
        return queryset


class DPCHNumberOfDPCHs(BaseAF):
    model = DonorPaymentChannel
    field = "number_of_dpchs"
    field_verbose_name = _("Number of DPCHs")
    values_list_field = "user__id"
    field_type = IntegerField()

    def queryset(self, *args, **kwargs):
        if kwargs.get("administrative_unit"):
            au = kwargs["administrative_unit"]
            subquery = (
                self.model.objects.filter(
                    event__administrative_units__in=au,
                    user=OuterRef("user"),
                )
                .values("user")
                .annotate(
                    number_of_dpchs=Count("pk"),
                )
            )
            queryset = self.model.objects.filter(
                event__administrative_units__in=au,
            ).annotate(
                number_of_dpchs=Subquery(
                    subquery.values("number_of_dpchs")[:1],
                    output_field=self.field_type,
                ),
            )
        else:
            queryset = self.model.objects.none()
        return queryset


class DPCHRegularPaymentsOk(BaseAF):
    model = DonorPaymentChannel
    field = "regular_payments_ok"
    field_verbose_name = _("Regular payment ok")
    values_list_field = "user__id"
    field_type = CharField()

    def queryset(self, *args, **kwargs):
        if kwargs.get("administrative_unit"):
            au = kwargs["administrative_unit"]
            queryset = self.model.objects.filter(
                event__administrative_units__in=au,
            ).annotate(
                regular_payments_ok=Case(
                    When(
                        expected_regular_payment_date__lt=(
                            date.today() - timedelta(days=11)
                        ),
                        then=Value(_("Delayed")),
                    ),
                    default=Value(_("Not delayed")),
                    output_field=self.field_type,
                ),
            )
        else:
            queryset = self.model.objects.none()
        return queryset


class DPCHPaymentsAmount(BaseAF):
    model = DonorPaymentChannel
    field = "payment_amount"
    field_verbose_name = _("Payment amount")
    values_list_field = "user__id"
    field_type = FloatField()

    def queryset(self, *args, **kwargs):
        if kwargs.get("administrative_unit"):
            queryset = self.model.objects.filter(
                event__administrative_units__in=kwargs["administrative_unit"],
            ).annotate(
                payment_amount=Case(
                    When(
                        payment__amount__isnull=True,
                        then=Value(0.0),
                    ),
                    default=F("payment__amount"),
                    output_field=self.field_type,
                ),
            )
        else:
            queryset = self.model.objects.none()
        return queryset


class DPCHRegularPaymentsAmount(BaseAF):
    model = DonorPaymentChannel
    field = "regular_payment_amount"
    field_verbose_name = _("Regular payment amount")
    values_list_field = "user__id"
    field_type = FloatField()

    def queryset(self, *args, **kwargs):
        if kwargs.get("administrative_unit"):
            queryset = self.model.objects.filter(
                event__administrative_units__in=kwargs["administrative_unit"],
                regular_payments="regular",
            ).annotate(
                regular_payment_amount=Case(
                    When(
                        payment__amount__isnull=True,
                        then=Value(0.0),
                    ),
                    default=F("payment__amount"),
                    output_field=self.field_type,
                ),
            )
        else:
            queryset = self.model.objects.none()
        return queryset


class DPCHEventName(BaseAF):
    model = DonorPaymentChannel
    field = "dpch_event_name"
    field_verbose_name = _("Event name")
    values_list_field = "user__id"

    def queryset(self, *args, **kwargs):
        if kwargs.get("administrative_unit"):
            queryset = self.model.objects.filter(
                event__administrative_units__in=kwargs["administrative_unit"],
            ).annotate(
                dpch_event_name=F("event__name"),
            )
        else:
            queryset = self.model.objects.none()
        return queryset


class DPCHEventPaymentsAmount(BaseAF):
    model = DonorPaymentChannel
    field = "event_payment_amount"
    field_verbose_name = _("Event payment amount")
    values_list_field = "user__id"
    field_type = FloatField()
    conditional_fields = {DPCHEventName.field: "event__name"}

    def queryset(self, *args, **kwargs):
        if kwargs.get("administrative_unit"):
            queryset = self.model.objects.filter(
                event__administrative_units__in=kwargs.pop("administrative_unit"),
                **kwargs,
            ).annotate(
                event_payment_amount=Case(
                    When(
                        payment__amount__isnull=True,
                        then=Value(0.0),
                    ),
                    default=F("payment__amount"),
                    output_field=self.field_type,
                ),
            )
        else:
            queryset = self.model.objects.none()
        return queryset


class InteractionEventName(BaseAF):
    model = Interaction
    field = "interaction_event_name"
    field_verbose_name = _("Event name")
    values_list_field = "user__id"

    def queryset(self, *args, **kwargs):
        if kwargs.get("administrative_unit"):
            queryset = self.model.objects.filter(
                administrative_unit__in=kwargs["administrative_unit"],
            ).annotate(
                interaction_event_name=F("event__name"),
            )
        else:
            queryset = self.model.objects.none()
        return queryset


class InteractionDateFrom(InteractionEventName):
    field = "date_from"


class InteractionDateTo(InteractionEventName):
    field = "date_to"


class InteractionCommunicationType(InteractionEventName):
    field = "communication_type"


class InteractionResultName(InteractionEventName):
    field = "result__name"


class InteractionNextCommunicationDate(InteractionEventName):
    field = "next_communication_date"


class InteractionNumberOfInteractions(BaseAF):
    model = Interaction
    field = "number_of_interactions"
    field_verbose_name = _("Number of interactions")
    values_list_field = "user__id"
    field_type = IntegerField()
    conditional_fields = {InteractionEventName.field: "event__name"}

    def queryset(self, *args, **kwargs):
        if kwargs.get("administrative_unit"):
            au = kwargs.pop("administrative_unit")
            subquery = (
                self.model.objects.filter(
                    administrative_unit__in=au,
                    user=OuterRef("user"),
                    **kwargs,
                )
                .values("user")
                .annotate(
                    number_of_interactions=Count("pk"),
                )
            )
            queryset = self.model.objects.filter(
                administrative_unit__in=au,
                **kwargs,
            ).annotate(
                number_of_interactions=Subquery(
                    subquery.values("number_of_interactions")[:1],
                    output_field=self.field_type,
                ),
            )
        else:
            queryset = self.model.objects.none()
        return queryset


class ProfileEmailIsEmailInCompanyprofile(BaseAF):
    model = ProfileEmail
    field = "is_email_in_companyprofile"
    field_verbose_name = _("Is email in the company profile")
    values_list_field = "user__id"
    field_type = BooleanField()

    def queryset(self, *args, **kwargs):
        if kwargs.get("administrative_unit"):
            au = kwargs["administrative_unit"]
            subquery = self.model.objects.filter(
                email=OuterRef("email"),
            ).values("email")
            queryset = CompanyContact.objects.filter(
                administrative_unit__in=au,
            ).annotate(
                common_email=Subquery(
                    subquery.values("email")[:1],
                ),
            )
            common_emails = list(
                queryset.filter(
                    common_email__isnull=False,
                ).values_list("common_email", flat=True),
            )
            queryset = self.model.objects.filter(
                user__administrative_units__in=au,
            ).annotate(
                is_email_in_companyprofile=Case(
                    When(
                        email__in=common_emails,
                        then=Value(True),
                    ),
                    default=Value(False),
                    output_field=self.field_type,
                ),
            )
        else:
            queryset = self.model.objects.none()
        return queryset


AF_FILTERS = [
    DPCHEventName,
    DPCHEventPaymentsAmount,
    DPCHNumberOfDPCHs,
    DPCHRegularPaymentsOk,
    DPCHNumberOfPayments,
    DPCHPaymentsAmount,
    DPCHRegularPayments,
    DPCHRegularPaymentsAmount,
    DPCHRegularFrequency,
    DPCHSumOfAllPayments,
    DPCHWithoutPayments,
    InteractionEventName,
    InteractionNumberOfInteractions,
    InteractionDateFrom,
    InteractionDateTo,
    InteractionResultName,
    InteractionNextCommunicationDate,
    InteractionCommunicationType,
    ProfileEmailIsEmailInCompanyprofile,
]

AF_FILTERS_CONDITIONAL_FIELDS = [
    [DPCHEventName.field, DPCHEventPaymentsAmount.field],
    [InteractionEventName.field, InteractionNumberOfInteractions.field],
]


class InputFilter(SimpleListFilter, ABC):
    """
    SimpleListFilter changed to TextInput (Search field)
    """

    template = "admin/input_filter.html"

    def _get_input_values(self, value):
        """Get list of input value(s) (required for query)

        :param str value: value string or values string separate with
                          list_item_separator

        :return list: list of value(s) (required for query)
        """
        return [value.strip() for value in value.split(self.list_item_separator)]

    def lookups(self, request, model_admin):
        return ((),)

    def choices(self, changelist):
        all_choice = next(super().choices(changelist))

        all_choice["query_parts"] = (
            (k, v)
            for k, v in changelist.get_filters_params().items()
            if k != self.parameter_name
        )

        yield all_choice


class AdminUnitTextSearchFilter(InputFilter):
    parameter_name = "administrative-unit"
    title = _("Administrative unit")

    def queryset(self, request, queryset):
        if self.value() is not None:
            admin_unit = self.value()

            return queryset.filter(administrative_units__name__icontains=admin_unit)


class DonorsEventTextSearchFilter(InputFilter):
    parameter_name = "donors-event"
    title = _("Donor's event")

    def queryset(self, request, queryset):
        if self.value() is not None:
            donors_event = self.value()

            return queryset.filter(userchannels__event__name__icontains=donors_event)


class EventOfInteractionTextSearchFilter(InputFilter):
    parameter_name = "event-of-interaction"
    title = _("Event of interaction")

    def queryset(self, request, queryset):
        if self.value() is not None:
            interaction_name = self.value()

            return queryset.filter(interaction__event__name__icontains=interaction_name)


class EventOfInteractionIDSearchFilter(InputFilter):
    parameter_name = "event-of-interaction-id"
    title = _("Event of interaction ID")

    def queryset(self, request, queryset):
        v = self.value()
        if v is None:
            return None
        try:
            event_id = int(v)
            return queryset.filter(interaction__event_id=event_id)
        except ValueError:
            return None
