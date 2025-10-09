import logging

from celery import task

from interactions import models

from aklub.sync_with_daktela_app import (
    delete_ticket,
    get_user_auth_token,
    sync_tickets,
)


logger = logging.getLogger(__name__)


@task()
def sync_with_daktela(interactions_pks):
    """Sync Interactions models instances with Daktela app

    :param list userprofiles: UserProfiles models instances id
    """
    if not settings.DAKTELA["enable"]:
        return
    interactions = models.Interaction.objects.filter(
        pk__in=interactions_pks,
    )
    sync_tickets(interactions)


@task()
def delete_tickets_from_daktela(interactions_pks):
    """Delete Interaction models instances from Daktela app Ticket models

    :param list userprofiles: Interaction models instances id
    """
    if not settings.DAKTELA["enable"]:
        return
    interactions = models.Interaction.objects.filter(
        pk__in=interactions_pks,
    )
    user_auth_token = get_user_auth_token()
    for interaction in interactions:
        delete_ticket(interaction, user_auth_token)
    interactions.delete()
