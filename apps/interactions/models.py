import os.path

from aklub.models import AdministrativeUnit, Profile
from aklub.utils import WithAdminUrl

from autoslug import AutoSlugField

from django.core.mail import EmailMultiAlternatives
from django.db import models
from django.utils.translation import ugettext_lazy as _

import html2text


class Result(models.Model):
    class Meta:
        verbose_name = _("Result")
        verbose_name_plural = _("Results")

    RESULT_SORT = (
        ('promise', _("Promise")),
        ('ongoing', _("Ongoing communication")),
        ('dont_contact', _("Don't contact again")),
    )

    name = models.CharField(
        verbose_name=_("Name of result"),
        max_length=200,
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
    class Meta:
        verbose_name = _("Interaction Category")
        verbose_name_plural = _("Interaction Categories")

    category = models.CharField(
        verbose_name=_("Category name"),
        max_length=130,
    )
    display = models.BooleanField(
        max_length=130,
        verbose_name=_("Show on timeline"),
        default=True,
        help_text=_("Interactions under this category will show on timeline"),
    )

    def __str__(self):
        return self.category


class BaseInteraction2(models.Model):
    class Meta:
        abstract = True
    user = models.ForeignKey(
        Profile,
        verbose_name=("User"),
        on_delete=models.CASCADE,
    )
    event = models.ForeignKey(
        "events.Event",
        verbose_name=("Event"),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
    )
    administrative_unit = models.ForeignKey(
        AdministrativeUnit,
        verbose_name=("Administrative unit"),
        on_delete=models.CASCADE,
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


class Interaction(WithAdminUrl, BaseInteraction2):
    """
    Every field must have  blank=True to auto create bool (display field)
    if we want to have it False, we must handle it in admin context with ignored fields
    also must be added to field_set in admin inline and import_export fields.
    """
    class Meta:
        verbose_name = _("Interaction")
        verbose_name_plural = _("Interactions")

    SETTLEMENT_CHOICES = [
        ('a', _('Automatic')),
        ('m', _('Manual')),
    ]

    RATING_CHOICES = [
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4'),
        ('5', '5'),
    ]
    COMMUNICATION_TYPE = (
        ('mass', _("Mass")),
        ('auto', _("Automatic")),
        ('individual', _("Individual")),
    )
    type = models.ForeignKey( # noqa
        'InteractionType',
        verbose_name=("Type"),
        help_text=("Type of interaction"),
        on_delete=models.CASCADE,
    )
    subject = models.CharField(
        verbose_name=("Subject"),
        help_text=("The topic of this communication"),
        max_length=130,
    )
    date_from = models.DateTimeField(
        verbose_name=("Date of interaction"),
    )
    date_to = models.DateTimeField(
        verbose_name=("End of period date"),
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

    attachment = models.FileField(
        verbose_name=("Attachment"),
        upload_to='communication-attachments',
        blank=True,
        null=True,
    )

    summary = models.TextField(
        verbose_name=("Text"),
        help_text=("Text or summary of this communication"),
        max_length=50000,
        blank=True,
        default='',
    )
    status = models.CharField(
        verbose_name=("Status"),
        help_text=("Status/progress of this communication"),
        max_length=130,
        blank=True,
        default='',
    )
    result = models.ForeignKey(
        Result,
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
        default='',
    )
    next_communication_date = models.DateTimeField(
        verbose_name=("Date of next communication"),
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
    communication_type = models.CharField(  # noqa
        verbose_name=_("Type of communication"),
        max_length=30,
        choices=COMMUNICATION_TYPE,
        default='individual',
        blank=True,
    )
    dispatched = models.BooleanField(
        verbose_name=_("Dispatched / Done"),
        help_text=_("Was this message already sent, communicated and/or resolved?"),
        default=False,
        blank=True,
        null=True,
    )

    def __str__(self):
        return f'{self.user.username} - {self.type}'

    def save(self, *args, **kwargs):
        """Record save hook

        If state of the dispatched field changes to True, call
        the automated dispatch() method.
        """
        if self.type.send_email or self.type.send_sms:
            if not self.dispatched:  # take ride of duplicity email send if mass communictaion is used
                self.dispatch(save=False)  # then try to dispatch this email automatically
        super().save(*args, **kwargs)

    def dispatch(self, save=True, is_test=False):
        """Dispatch the communication
        Currently only method 'email' is implemented, all other methods will be only saved. For these messages, the
        email is sent via the service configured in application settings.

        TODO: Implement 'mail': the form with the requested text should be
        typeseted and the admin presented with a 'print' button. Address for
        filling on the envelope should be displayed to the admin.
        """
        administrative_unit = getattr(self, 'administrative_unit', None)
        if self.type.send_sms:  # TODO: implement SMS method
            pass

        if self.type.send_email:
            user_email = self.user.get_email_str(self.administrative_unit)
            if user_email:
                # if we dpmt wamt to save email => its fake communicaiton and we sent some user to administrative unit
                if is_test:
                    to = administrative_unit.from_email_str
                    body = _(
                        "Testing email\n"
                        "Similar email will be sent to every user (email originaly to: %(email)s !!\n"
                        "^^^Ignore those lines ^^^\n\n"
                    ) % {'email': user_email}
                    body = str(body) + self.summary_txt()

                else:
                    to = user_email
                    body = self.summary_txt()

                email = EmailMultiAlternatives(
                    subject=self.subject,
                    body=body,
                    from_email=administrative_unit.from_email_str,
                    to=[to],
                )
                if self.communication_type != 'individual':
                    email.attach_alternative(self.summary, "text/html")
                if self.attachment:
                    att = self.attachment
                    email.attach(os.path.basename(att.name), att.read())
                email.send(fail_silently=False)
                self.dispatched = True
            if save:
                self.save()
        else:
            self.dispatched = True
            if save:
                self.save()

    def summary_txt(self):
        if self.communication_type == 'individual':
            return self.summary
        else:
            return html2text.html2text(self.summary)


class PetitionSignature(BaseInteraction2):
    class Meta:
        verbose_name = _("Petition signature")
        verbose_name_plural = _("Petition signatures")
        unique_together = ('user', 'event')

    email_confirmed = models.BooleanField(
        verbose_name=_("Is confirmed via e-mail"),
        default=False,
    )
    gdpr_consent = models.BooleanField(
        verbose_name=_("GDPR consent"),
        default=False,
    )
    public = models.BooleanField(
        verbose_name=_("Publish my name in the list of supporters/petitents of this campaign"),
        default=False,
    )


class InteractionType(models.Model):
    class Meta:
        verbose_name = _("Interaction Type")
        verbose_name_plural = _("Interaction Types")

    name = models.CharField(
        max_length=130,
    )

    category = models.ForeignKey(
        InteractionCategory,
        verbose_name=_("Category"),
        help_text=("Timeline display category"),
        on_delete=models.CASCADE,
    )
    slug = AutoSlugField(
        verbose_name=_("Slug"),
        editable=True,
        populate_from="name",
        help_text=_("Identifier of the Interaction Type"),
        max_length=100,
        blank=True,
        null=True,
    )

    send_email = models.BooleanField(
        verbose_name=_("Sent email"),
        help_text=_("the email will be immediatelly sent to the user"),
        default=False,
        blank=True,
        null=True,
    )
    send_sms = models.BooleanField(
        verbose_name=_("Sent sms"),
        help_text=_("the sms will be immediatelly send to the use"),
        default=False,
        blank=True,
        null=True,
    )

    def __str__(self):
        return self.name


# make bool field in InteractionType to every not required Interaction model field
for field in Interaction._meta.fields:
    if Interaction._meta.get_field(field.name).blank and field.name != "id":
        InteractionType.add_to_class(
                field.name + '_bool',
                models.BooleanField(
                    verbose_name=_(field.verbose_name),
                    help_text=_(
                        'Choose if %(field_name)s is visible in specific type of interaction.'
                    ) % {'field_name': field.name},
                    default=False,
                    blank=False,
                    null=False,
                ),
        )
