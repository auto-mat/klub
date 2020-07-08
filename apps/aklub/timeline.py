import datetime

from aklub.models import Payment, Profile

from django.utils import timezone
from django.utils.timezone import localtime
from django.utils.translation import ugettext as _

from helpdesk.query import __Query__


def get_unit_color(text, unit):
    return f'<p style="color:{unit.color};">{text}</p>'


def is_period(interaction):
    if interaction.type.date_to_bool:
        if interaction.date_to:
            date = interaction.date_to
        else:
            date = timezone.now()
    else:
        date = interaction.date_from
    return date


class Query(__Query__):
    def get_timeline_context(self):  # noqa
        context = super().get_timeline_context()
        events = []
        profiles = Profile.objects.filter(pk__in=self.params.get('search_profile_pks', []))
        for profile in profiles:
            if self.huser.user.can_administer_profile(profile):
                events.append({
                    'group': _('Events'),
                    'start_date': self.mk_timeline_date(
                        localtime(profile.date_joined),
                    ),
                    'text': {
                        'headline': _("Profile joined"),
                        'text': "",
                    },
                })

                for interaction in profile.interaction_set.select_related('type__category').all():
                    if interaction.type.category.display:
                        events.append({
                            'group': _(interaction.type.category.category),
                            'start_date': self.mk_timeline_date(localtime(interaction.date_from)),
                            'end_date': self.mk_timeline_date(localtime(is_period(interaction))),
                            'text': {
                                'headline': get_unit_color(
                                                    interaction.subject,
                                                    interaction.administrative_unit,
                                            ),
                                'text': "{summary}<br/><a href='{url}''/> {link_text} </a>".format(
                                    summary=interaction.summary,
                                    url=interaction.get_admin_url(),
                                    link_text=_('View interaction '),
                                ),
                            },
                        }
                        )
                if self.huser.user.has_perm('aklub.can_edit_all_units'):
                    payments = Payment.objects\
                         .select_related('user_donor_payment_channel__money_account__administrative_unit',)\
                         .filter(user_donor_payment_channel__user=profile.pk,)
                else:
                    payments = Payment.objects\
                        .select_related('user_donor_payment_channel__money_account__administrative_unit',)\
                        .filter(
                            user_donor_payment_channel__user=profile.pk,
                            user_donor_payment_channel__money_account__administrative_unit__in=self.huser.user.administrated_units.all(),
                        )

                for payment in payments:
                    events.append({
                        'group': _('Payments'),
                        'start_date': self.mk_timeline_date(
                            datetime.datetime.combine(payment.date, datetime.time(0, 0)),
                        ),
                        'text': {
                            'headline': get_unit_color(
                                                f'{payment.amount} Kč',
                                                payment.user_donor_payment_channel.money_account.administrative_unit,
                                        ),
                            'text': "{name} <br/><a href='{url}'/> {link_text} </a>".format(
                                name=payment.user_donor_payment_channel.event.name,
                                url=payment.get_admin_url(),
                                link_text=_('View payment'),
                            ),
                        },
                    })

        context['events'] = context['events'] + events
        return context
