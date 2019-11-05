import datetime

from aklub.models import Payment, ProfileEmail, UserProfile

from django.utils.translation import ugettext as _

from helpdesk.query import __Query__


class Query(__Query__):
    def get_timeline_context(self):  # noqa
        context = super().get_timeline_context()
        search = self.params.get('search_string', '')
        events = []
        profiles = set()
        for subsearch in search.split("OR"):
            if "@" in subsearch:
                for profileemail in ProfileEmail.objects.filter(email=subsearch.strip()):
                    profiles.add(profileemail.user)
                for profile in UserProfile.objects.filter(email=subsearch.strip()):
                    profiles.add(profile)
        for profile_pk in self.params.get('search_profile_pks', []):
            fps = UserProfile.objects.filter(pk=profile_pk)
            for profile in fps:
                profiles.add(profile)
        for profile in profiles:
            if self.huser.user.can_administer_profile(profile):
                events.append({
                    'group': _('Events'),
                    'start_date': self.mk_timeline_date(
                        profile.created,
                    ),
                    'text': {
                        'headline': _("Profile created"),
                        'text': "",
                    },
                })
                for interaction in profile.interaction_set.all():
                    events.append({
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
                    })
                for payment in Payment.objects.gate(self.huser.user).filter(user_donor_payment_channel__user=profile.pk):
                    events.append({
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
                    })
        context['events'] = context['events'] + events
        return context
