from django.db import models
from aklub.models import Profile, Event, AdministrativeUnit
from django.utils.translation import ugettext_lazy as _


class Results(models.Model):
    RESULT_SORT = (
        ('promise', _("Promise")),
        ('ongoing', _("Ongoing communication")),
        ('dont_contact', _("Don't contact again")),
    )

    name = models.CharField(
        verbose_name=_("Name of result"),
        max_length=200,
        blank=False,
        null=False,
    )
    sort = models.CharField(
        verbose_name=_("Sort of result"),
        max_length=30,
        choices=RESULT_SORT,
        default='individual',
    )

    def __str__(self):
        return str(self.name)


class InteractionCategory(models.Model):
    category = models.CharField(
        max_length=130,
        blank=False,
        null=False,
    )

    def __str__(self):
        return self.category


class BaseInteraction2(models.Model):
    user = models.ForeignKey(
        Profile,
        verbose_name=("User"),
        on_delete=models.CASCADE,
        null=False,
        blank=False,
    )
    event = models.ForeignKey(
        Event,
        verbose_name=("Event"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    date = models.DateTimeField(
        verbose_name=_("Date and time of the communication"),
        null=True,
    )
    created = models.DateTimeField(
        verbose_name=_("Date of creation"),
        auto_now_add=True,
        null=True,
    )
    updated = models.DateTimeField(
        verbose_name=_("Date of last change"),
        auto_now=True,
        null=True,
    )


class Interaction2(BaseInteraction2):
    SETTLEMENT_CHOICES = [
        ('a', _('Automatic')),
        ('m', _('Manual'))
    ]

    RATING_CHOICES = [
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
    ]

    type = models.ForeignKey(
        'InteractionType',
        help_text=("Type of interaction"),
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )

    administrative_unit = models.ForeignKey(
        AdministrativeUnit,
        verbose_name=("administrative units"),
        on_delete=models.CASCADE,
        null=False,
        blank=False,
        )

    date_from = models.DateTimeField(
        verbose_name=("Date and time of the communication"),
        auto_now_add=True,
        null=True,
        blank=True,
    )
    date_to = models.DateTimeField(
        verbose_name=("Date of creation"),
        auto_now_add=True,
        null=True,
        blank=True,
    )
    settlement = models.CharField(
        verbose_name=("Settlements"),
        help_text=("Handled by automatic or manual communication"),
        choices=SETTLEMENT_CHOICES,
        max_length=30,
        blank=True,
        null=True,
    )
    note = models.TextField(
        verbose_name=("Notes"),
        help_text=("Internal notes about this communication"),
        max_length=3000,
        blank=True,
        null=True,
    )
    text = models.TextField(
        verbose_name=("Notes"),
        help_text=("Internal notes about this communication"),
        max_length=3000,
        blank=True,
        null=True,
    )
    attachment = models.FileField(
        verbose_name=("Attachment"),
        upload_to='communication-attachments',
        blank=True,
        null=True,
    )
    subject = models.CharField(
        verbose_name=("Subject"),
        help_text=("The topic of this communication"),
        max_length=130,
        blank=True,
        null=True,
    )
    summary = models.TextField(
        verbose_name=("Text"),
        help_text=("Text or summary of this communication"),
        max_length=50000,
        blank=True,
        null=True,
    )
    status = models.CharField(
        verbose_name=("Subject"),
        help_text=("The topic of this communication"),
        max_length=130,
        blank=True,
        null=True,
    )
    result = models.ForeignKey(
        Results,
        verbose_name=_("Result of communication"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    rating = models.CharField(
        verbose_name=_("rating communication"),
        max_length=30,
        choices=RATING_CHOICES,
        help_text=("Rate communication (school grades)"),
        blank=True,
        null=True,
    )

    next_step = models.TextField(
        verbose_name=("Next steps"),
        help_text=("What happens next"),
        max_length=3000,
        blank=True,
        null=True,
    )
    next_communication_date = models.DateTimeField(
        verbose_name=("Date of creation"),
        auto_now_add=True,
        blank=True,
        null=True,
    )
    created_by = models.ForeignKey(
        Profile,
        verbose_name=_("Created by"),
        related_name='created_by_communications',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    handled_by = models.ForeignKey(
        Profile,
        verbose_name=_("Last handled by"),
        related_name='handled_by_communications',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
    )
    def __str__(self):
        return f'{self.user.username} - {self.type}'


class PetitionSignature(BaseInteraction2):
    email_confirmed = models.BooleanField(
        verbose_name=_("Is confirmed via e-mail"),
        default=False,
    )
    gdpr_consent = models.BooleanField(
        _("GDPR consent"),
        default=False,
    )
    public = models.BooleanField(
        verbose_name=_("Publish my name in the list of supporters/petitents of this campaign"),
        default=False,
    )

class InteractionType(models.Model):
    name = models.CharField(
        max_length=130,
        blank=False,
        null=False,
    )

    category = models.ForeignKey(
        InteractionCategory,
        help_text=("Timeline display category"),
        blank=False,
        null=False,
        on_delete=models.CASCADE,
    )

    def __str__(self):
        return self.name


# make bool field in InteractionType to every not required Interaction model field
for field in Interaction2._meta.fields:
    if Interaction2._meta.get_field(field.name).null:
        InteractionType.add_to_class(
                field.name + '_bool',
                models.BooleanField(
                                help_text=_(f'choose if {field.name} is visible in specific type of interaction '),
                                default=False,
                                blank=False,
                                null=False,
                                )
                )
