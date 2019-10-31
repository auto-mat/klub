import datetime

from aklub.models import Payment, UserProfile

from django.utils.translation import ugettext as _

from helpdesk.query import __Query__


class Query(__Query__):
    def get_timeline_context(self):
        context = super().get_timeline_context()
        search = self.params.get('search_string', '')
        events = []
        if "@" in search:
            profile = UserProfile.objects.get(email=search)
            if profile:
                if self.huser.user.can_administer_profile(profile):
                    for interaction in profile.interaction_set.all():
                        event = {
                            'group': _('Interaction') + " - " + interaction.method,
                            'start_date': self.mk_timeline_date(interaction.date),
                            'text': {
                                'headline': interaction.subject,
                                'text': "{summary}<br/><a href='{url}''/> {link_text} </a>".format(
                                    summary=interaction.summary,
                                    url=interaction.get_admin_url(),
                                    link_text=_('View interaction '),
                                ),
                            },
                        }
                        events.append(event)
                    for payment in Payment.objects.gate(self.huser.user).filter(user_donor_payment_channel__user=profile.pk):
                        event = {
                            'group': _('Payment'),
                            'start_date': self.mk_timeline_date(
                                datetime.datetime.combine(payment.date, datetime.time(0, 0)),
                            ),
                            'text': {
                                'headline': "%s Kč" % payment.amount,
                                'text': "{name} <br/><a href='{url}'/> {link_text} </a>".format(
                                    name=payment.user_donor_payment_channel.event.name,
                                    url=payment.get_admin_url(),
                                    link_text=_('View payment'),
                                ),
                            },
                        }
                        events.append(event)
        context['events'] = context['events'] + events
        return context
