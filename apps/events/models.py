from aklub.models import DonorPaymentChannel, Recruiter

from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Sum
from django.utils.translation import ugettext_lazy as _


class Location(models.Model):
    class Meta:
        verbose_name = _("Location")
        verbose_name_plural = _("Locations")

    name = models.CharField(
        verbose_name=_("Name"),
        max_length=100,
    )
    place = models.CharField(
        verbose_name=_("Place"),
        max_length=100,
        blank=True,
    )
    region = models.CharField(
        verbose_name=_("Region"),
        max_length=100,
        blank=True,
    )
    gps = models.CharField(
        verbose_name=_("GPS location"),
        max_length=200,
        blank=True,
    )
    administrative_unit = models.ForeignKey(
        "aklub.AdministrativeUnit",
        verbose_name=_("administrative unit"),
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name


class EventType(models.Model):
    class Meta:
        verbose_name = _("Event type")
        verbose_name_plural = _("Event types")

    name = models.CharField(
        help_text=_("Name of event type"),
        verbose_name=_("Name"),
        max_length=100,
    )
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Description of this type"),
        max_length=3000,
        blank=True,
    )
    administrative_unit = models.ForeignKey(
        "aklub.AdministrativeUnit",
        verbose_name=_("administrative unit"),
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name


class OrganizingAssociation(models.Model):
    class Meta:
        verbose_name = _("Organizing association")
        verbose_name_plural = _("Organizing associations")

    name = models.CharField(max_length=300, verbose_name=_("Name"),)
    description = models.TextField(blank=True, verbose_name=_("Description"))
    administrative_unit = models.ForeignKey(
        "aklub.AdministrativeUnit",
        verbose_name=_("administrative unit"),
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name


class Event(models.Model):
    """Campaign -- abstract event with description

    These events can be associated to a user."""

    class Meta:
        verbose_name = _("Event")
        verbose_name_plural = _("Events")

    INTENDED_FOR = (
        ('everyone', _('Everyone')),
        ('adolescents_and_adults', _('Adolescents and adults')),
        ('children', _('Children')),
        ('parents_and_children', _('Parents and children')),
        ('newcomers', _("Newcomers")),
    )
    GRANT = (
        ('no_grant', _('No Grant')),
        ('MEYS', _("Ministry of Education, Youth and Sports")),
        ('others', _('Others')),
    )
    PROGRAM = (
        ("", ('---')),
        ('education', _('Education')),
        ('PsB', _('PsB')),
        ('monuments', _('Monuments')),
        ('nature', _('Nature')),
        ('eco_consulting', _('Eco consulting')),
        ('children_section ', _("Children's Section")),
    )
    BASIC_PURPOSE = (
        ('action', _('Action')),
        ('petition', _('Petition')),
        ('camp', _('Camp')),

    )
    REGISTRATION_METHOD = (
        ('standard', _('Standard')),
        ('other_electronic', _('Other electronic')),
        ('by_email', _("By organizer's email")),
        ('not_required', _("Not required")),
        ('full', _("Full, not anymore")),

    )
    registration_method = models.CharField(
        verbose_name=_("Registration method"),
        max_length=128,
        choices=REGISTRATION_METHOD,
        default='standard',
    )
    for i in range(1, 4):
        vars()[f"additional_question_{i}"] = models.CharField(
            verbose_name=_("Additional question number %(number)s" % {"number": i}),
            blank=True,
            max_length=300,
        )
    main_photo = models.FileField(
        verbose_name=_("Main photo"),
        blank=True,
        null=True,
        upload_to='event_photos',
    )
    for i in range(1, 7):
        vars()[f"additional_photo_{i}"] = models.FileField(
            verbose_name=_("Additional photo number %(number)s" % {"number": i}),
            blank=True,
            null=True,
            upload_to='event_photos',
        )
    invitation_text_1 = models.TextField(
        verbose_name=_("Invitation: What to expect"),
        help_text=_("What to except, basic informations."),
        max_length=3000,
        blank=True,
    )

    invitation_text_2 = models.TextField(
        verbose_name=_("Invitation: What, where and how"),
        help_text=_("Program of action."),
        max_length=3000,
        blank=True,
    )

    invitation_text_3 = models.TextField(
        verbose_name=_("Invitation: Volunter help"),
        help_text=_("Volunter help"),
        max_length=3000,
        blank=True,
    )

    invitation_text_4 = models.TextField(
        verbose_name=_("Invitation: Little sneek peek"),
        help_text=_("Little sneek peek"),
        max_length=3000,
        blank=True,
    )
    number_of_actions = models.PositiveIntegerField(
        verbose_name=_("Number of actions in given time period"),
        default=1,
    )
    organization_team = models.ManyToManyField(
        "aklub.Profile",
        verbose_name=_("Organization team"),
        through="OrganizationTeam",

    )
    location = models.ForeignKey(
        Location,
        verbose_name=_("Location"),
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )
    event_type = models.ForeignKey(
        EventType,
        verbose_name=_("Event type"),
        related_name='events',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    basic_purpose = models.CharField(
        verbose_name=_("Basic Purpose"),
        max_length=128,
        choices=BASIC_PURPOSE,
        default='action',
    )
    program = models.CharField(
        verbose_name=_("Program"),
        max_length=128,
        choices=PROGRAM,
        default="",
        blank=True,
    )
    is_internal = models.BooleanField(
        verbose_name=_("Only for internal members"),
        default=False,
    )
    age_from = models.PositiveIntegerField(
        verbose_name=_("Age from"),
        null=True,
        blank=True,
    )
    age_to = models.PositiveIntegerField(
        verbose_name=_("Age to"),
        null=True,
        blank=True,
    )
    indended_for = models.CharField(
        verbose_name=_("Indended for"),
        max_length=128,
        choices=INTENDED_FOR,
        default='everyone',
    )
    participation_fee = models.PositiveIntegerField(
        verbose_name=_("Participation fee"),
        null=True,
        blank=True,
    )

    meeting = models.CharField(
        verbose_name=_("Meeting at the event"),
        max_length=128,
        blank=True,
    )
    grant = models.CharField(
        verbose_name=_("Grant"),
        max_length=128,
        choices=GRANT,
        default='no_grant',
    )
    focus_on_members = models.BooleanField(
        verbose_name=_("Focus on members"),
        default=False,
    )

    public_on_web = models.BooleanField(
        verbose_name=_("Public on webpage"),
        default=False,
    )
    entry_form_url = models.URLField(
        verbose_name=_("Url address of register form"),
        blank=True,
        null=True,
    )
    web_url = models.URLField(
        verbose_name=_("Url address of register form"),
        blank=True,
        null=True,
    )
    name = models.CharField(
        verbose_name=_("Name"),
        help_text=_("Choose some unique name for this campaign"),
        max_length=100,
    )
    variable_symbol_prefix = models.PositiveIntegerField(
        validators=[MinValueValidator(10000), MaxValueValidator(99999)],
        verbose_name=_("Variable_symbol_prefix"),
        help_text=_("Number between 10000-99999"),
        null=True,
        blank=True,
    )
    description = models.TextField(
        verbose_name=_("Description"),
        help_text=_("Description of this campaign"),
        max_length=3000,
        blank=True,
    )
    note = models.TextField(
        verbose_name=_("Note"),
        help_text=_("Note of this campaign"),
        max_length=3000,
        blank=True,
    )
    real_yield = models.FloatField(
        verbose_name=_("Real yield"),
        help_text=_("Use if yield differs from counted value"),
        blank=True,
        null=True,
    )
    result = models.ManyToManyField(
        'interactions.result',
        verbose_name=_("Acceptable results of communication"),
        blank=True,
    )
    slug = models.SlugField(
        verbose_name=_("Slug"),
        help_text=_("Identifier of the campaign"),
        default=None,
        max_length=100,
        unique=True,
        blank=True,
        null=True,
    )
    enable_signing_petitions = models.BooleanField(
        verbose_name=_("Enable registration through petition/mailing list forms"),
        default=False,
    )
    enable_registration = models.BooleanField(
        verbose_name=_("Enable registration through donation forms"),
        default=False,
    )
    allow_statistics = models.BooleanField(
        verbose_name=_("Allow statistics exports"),
        default=False,
    )
    email_confirmation_redirect = models.URLField(
        verbose_name=_("Redirect to url after email confirmation"),
        blank=True,
        null=True,
    )

    date_from = models.DateField(
        verbose_name=_("Date from"),
        null=True,
        blank=True,
    )
    date_to = models.DateField(
        verbose_name=_("Date to"),
        blank=True,
        null=True,
    )
    start_date = models.DateField(
        verbose_name=_("Start date"),
        blank=True,
        null=True,
    )
    administrative_units = models.ManyToManyField(
        "aklub.administrativeunit",
        verbose_name=_("administrative units"),
    )
    organizing_associations = models.ManyToManyField(
        OrganizingAssociation,
        verbose_name=_("Organizing associations"),
        blank=True,
    )

    def number_of_members(self):
        return self.donorpaymentchannel_set.count()

    number_of_members.short_description = _("number of members")

    def number_of_regular_members(self):
        return self.donorpaymentchannel_set.filter(regular_payments="regular", payment__amount__gt=0).distinct().count()

    def number_of_onetime_members(self):
        return self.donorpaymentchannel_set.exclude(regular_payments="regular")\
            .filter(payment__amount__gt=0).distinct().count()

    def number_of_active_members(self):
        return self.donorpaymentchannel_set.filter(payment__amount__gt=0).distinct().count()

    def number_of_all_members(self):
        return self.donorpaymentchannel_set.distinct().count()

    def number_of_confirmed_members(self):
        return self.petitionsignature_set.filter(email_confirmed=True).distinct().count()

    def recruiters(self):
        return Recruiter.objects.filter(campaigns=self)

    recruiters.short_description = _("recruiters")

    def number_of_recruiters(self):
        return len(self.recruiters())

    number_of_recruiters.short_description = _("number of recruiters")

    def yield_total(self):
        if self.indended_for == 'newcomers':
            return DonorPaymentChannel.objects.filter(event=self).aggregate(yield_total=Sum('payment__amount'))[
                'yield_total']
        else:
            return self.real_yield

    yield_total.short_description = _("total yield")

    def expected_yearly_income(self):
        income = 0
        for campaign_member in DonorPaymentChannel.objects.filter(event=self, payment__amount__gt=0).distinct():
            # TODO: use aggregate to count this
            income += campaign_member.yearly_regular_amount()
        return income

    expected_yearly_income.short_description = _("expected yearly income")

    def expected_monthly_income(self):
        return float(self.expected_yearly_income()) / 12.0

    expected_monthly_income.short_description = _("expected monthly income")

    def return_of_investmensts(self):
        if self.total_expenses() and self.expected_monthly_income():
            return self.total_expenses() / self.expected_monthly_income()

    return_of_investmensts.short_description = _("return of investmensts")

    def total_expenses(self):
        return self.expenses.aggregate(Sum('amount'))['amount__sum']

    total_expenses.short_description = _("total expenses")

    def average_expense(self):
        if self.total_expenses() and self.number_of_members():
            return self.total_expenses() / self.number_of_members()

    average_expense.short_description = _("average expense")

    def average_yield(self):
        if self.yield_total() and self.number_of_members():
            return self.yield_total() / self.number_of_members()

    average_yield.short_description = _("average yield")

    def __str__(self):
        return str(self.name)


class OrganizationPosition(models.Model):
    class Meta:
        verbose_name = _("Organization position")
        verbose_name_plural = _("Organization position")

    name = models.CharField(max_length=300, verbose_name=_("Name"),)
    description = models.TextField(blank=True, verbose_name=_("Description"))

    def __str__(self):
        return self.name


class OrganizationTeam(models.Model):
    class Meta:
        verbose_name = _("Organization team")
        verbose_name_plural = _("Organization teams")

    profile = models.ForeignKey("aklub.Profile", on_delete=models.CASCADE)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, verbose_name=_("Event"))
    position = models.ForeignKey(OrganizationPosition, on_delete=models.CASCADE, verbose_name=_("Position"),)
    can_be_contacted = models.BooleanField(default=False, verbose_name=_("Can be contacted"))

    def __str__(self):
        return str(self.id)
