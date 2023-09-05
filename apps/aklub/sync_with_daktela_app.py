"""
@package aklub.sync_with_daktela_app

@brief sync UserProfile, Interaction models with Daktela app Contacts,
       Tickets models

Funcs:
 - sync_with_daktela_app::create_or_update_contact
 - sync_with_daktela_app::create_or_update_ticket
 - sync_with_daktela_app::delete_contact
 - sync_with_daktela_app::delete_contact_tickets
 - sync_with_daktela_app::delete_ticket
 - sync_with_daktela_app::get_contact
 - sync_with_daktela_app::get_contact_tickets
 - sync_with_daktela_app::get_hash_hexdigest
 - sync_with_daktela_app::get_hash_hexdigest_as_int
 - sync_with_daktela_app::get_ticket
 - sync_with_daktela_app::get_ticket_by_uniq_title
 - sync_with_daktela_app::get_ticket
 - sync_with_daktela_app::get_tickets_max_uniq_id
 - sync_with_daktela_app::get_uniq_contact_name
 - sync_with_daktela_app::get_uniq_contact_name
 - sync_with_daktela_app::get_uniq_ticket_name
 - sync_with_daktela_app::get_user_auth_token
 - sync_with_daktela_app::sync_contacts
 - sync_with_daktela_app::sync_tickets
"""


import hashlib
import json
import logging
import re
import requests
from urllib.parse import urljoin

from django.conf import settings

logger = logging.getLogger(__name__)


def get_hash_hexdigest(input_str):
    """Get unique md5 hexdigest from input string

    :param str input_str: input string

    :return str: unique md5 hexdigest
    """
    return hashlib.md5(input_str.encode()).hexdigest()


def get_uniq_contact_name(userprofile):
    """
    Get unique name create from UserProfile model instance

    :param object userprofile: UserProfile model instance

    :return str: unique name based on UserProfile model instance username
                 and pk field
    """
    return get_hash_hexdigest(f"{userprofile.username}-{userprofile.pk}")


def get_user_auth_token():
    """Get Daktela web app user token

    :return str|None: Daktela app user token
    """
    error_message = "Obtain Daktela app user token fails due error: '{error}'"
    get_token_url = urljoin(
        settings.DAKTELA["base_rest_api_url"],
        "login.json",
    )
    data = {
        "username": settings.DAKTELA["username"],
        "password": settings.DAKTELA["password"],
        "only_token": 1,
    }
    try:
        response = requests.post(get_token_url, data)
        if response.ok:
            return response.json()["result"]
        else:
            logger.error(error_message.format(error=response.status_code))
    except (
        requests.RequestException,
        requests.ConnectionError,
        requests.HTTPError,
        requests.URLRequired,
        requests.TooManyRedirects,
        requests.Timeout,
    ) as error:
        logger.error(error_message.format(error=error))


def get_contact_tickets(contact, user_auth_token):
    """
    Get contact tickets

    :param str contact: Contact model instance unique name
    :param str user_auth_token: Daktela app user auth token

    :return list tickets_names: list of Contact tickets models instances
                                unique names
    """
    tickets_names = []
    tickets = get_tickets(user_auth_token)["result"]["data"]
    for ticket in tickets:
        if ticket["contact"]:
            if ticket["contact"]["name"] == contact:
                tickets_names.append(ticket["name"])
    return tickets_names


def get_contact(userprofile, user_auth_token):
    """
    Get Daktela app contact

    :param object userprofile: UserProfile model instance
    :param str user_auth_token: Daktela app user auth token

    :return bool: True if UserProfile username Daktela app contact name
                  exists else False
    """
    error_message = (
        "Obtain Daktela app contact with name '{name}' fails due error: '{error}'"
    )
    uniq_name = get_uniq_contact_name(userprofile)
    get_contact_url = urljoin(
        settings.DAKTELA["base_rest_api_url"],
        f"contacts/{uniq_name}.json",
    )
    request = requests.models.PreparedRequest()
    request.prepare_url(get_contact_url, {"accessToken": user_auth_token})
    try:
        response = requests.get(request.url)
        if response.ok:
            return True
        else:
            if response.status_code == 404:
                return False
            else:
                logger.error(
                    error_message.format(
                        error=response.status_code,
                        name=uniq_name,
                    )
                )
    except (
        requests.RequestException,
        requests.ConnectionError,
        requests.HTTPError,
        requests.URLRequired,
        requests.TooManyRedirects,
        requests.Timeout,
    ) as error:
        logger.error(
            error_message.format(
                error=error,
                name=uniq_name,
            )
        )


def create_or_update_contact(userprofile, user_auth_token, create=True):
    """
    Create or update Daktela app contact

    :param object userprofile: UserProfile model instance
    :param str user_auth_token: Daktela app user auth token
    :param bool create: create contact if True else update existed contact
    """
    from aklub.models import Telephone

    error_message = (
        "{operation} Daktela app contact with name '{name}' fails due error:"
        " '{error}'"
    )

    first_name = userprofile.first_name if userprofile.first_name else ""
    last_name = userprofile.last_name if userprofile.last_name else userprofile.username
    title = f"{first_name} {last_name}" if last_name else first_name
    telephones = [t.format_number() for t in Telephone.objects.filter(user=userprofile)]
    uniq_name = get_uniq_contact_name(userprofile)
    data = {
        "title": title,
        "firstname": first_name,
        "lastname": last_name,
        "database": "Default",
        "customFields": json.dumps(
            {
                "number": [
                    *telephones,
                ],
                "email": [
                    userprofile.get_email_str(),
                ],
            }
        ),
        "name": uniq_name,
    }
    if create:
        contacts_url = urljoin(
            settings.DAKTELA["base_rest_api_url"],
            "contacts.json",
        )
        operation = "Create"
    else:
        contacts_url = urljoin(
            settings.DAKTELA["base_rest_api_url"],
            f"contacts/{get_uniq_contact_name(userprofile)}.json",
        )
        operation = "Update"
    request = requests.models.PreparedRequest()
    request.prepare_url(contacts_url, {"accessToken": user_auth_token})
    try:
        if create:
            response = requests.post(request.url, data)
        else:
            response = requests.put(request.url, data)
        if not response.ok:
            logger.error(
                error_message.format(
                    operation=operation,
                    name=uniq_name,
                    error=response.status_code,
                )
            )
    except (
        requests.RequestException,
        requests.ConnectionError,
        requests.HTTPError,
        requests.URLRequired,
        requests.TooManyRedirects,
        requests.Timeout,
    ) as error:
        logger.error(
            error_message.format(
                operation=operation,
                name=uniq_name,
                error=error,
            )
        )


def delete_contact_tickets(contact, user_auth_token):
    """Delete contact tickets

    :param str contact: Contact model instance unique name
    :param str user_auth_token: Daktela app user auth token
    """
    tickets = get_contact_tickets(contact, user_auth_token)
    for ticket_name in tickets:
        delete_ticket(ticket_name, user_auth_token)


def delete_contact(userprofile, user_auth_token):
    """
    Delete Daktela app contact

    :param object userprofile: UserProfile model instance
    :param str user_auth_token: Daktela app user auth token
    """
    if get_contact(userprofile, user_auth_token):
        error_message = (
            "Delete Daktela app contact with name '{name}' fails due error:"
            " '{error}'"
        )
        uniq_name = get_uniq_contact_name(userprofile)
        get_contact_url = urljoin(
            settings.DAKTELA["base_rest_api_url"],
            f"contacts/{uniq_name}.json",
        )
        request = requests.models.PreparedRequest()
        request.prepare_url(get_contact_url, {"accessToken": user_auth_token})
        try:
            response = requests.delete(request.url)
            if not response.ok:
                logger.error(
                    error_message.format(
                        error=response.status_code,
                        name=uniq_name,
                    )
                )
        except (
            requests.RequestException,
            requests.ConnectionError,
            requests.HTTPError,
            requests.URLRequired,
            requests.TooManyRedirects,
            requests.Timeout,
        ) as error:
            logger.error(
                error_message.format(
                    error=error,
                    name=uniq_name,
                )
            )
        delete_contact_tickets(uniq_name, user_auth_token)


def get_hash_hexdigest_as_int(input_str):
    """Get unique md5 hexdigest from input string as integer

    :param str input_str: input string

    :return int: unique md5 hexdigest as integer
    """
    return int(hashlib.md5(input_str.encode()).hexdigest(), 16)


def get_uniq_ticket_name(interaction):
    """
    Get unique name create from Interaction model instance

    :param object interaction: Interaction model instance

    :return str: unique name based on Intecation model instance created
                 and pk field
    """
    return get_hash_hexdigest(
        f"{interaction.created:%Y-%m-%d %H:%M:%S%z}-{interaction.pk}",
    )


def get_ticket(interaction, user_auth_token):
    """
    Get Daktela app ticket

    :param object interaction: Interaction model instance
    :param str user_auth_token: Daktela app user auth token

    :return bool: True if Interaction Daktela app ticket name exists
                  else False
    """
    error_message = (
        "Obtain Daktela app ticket with name '{name}' fails due error: '{error}'"
    )
    uniq_name = get_ticket_by_uniq_title(
        f"{get_uniq_ticket_name(interaction)}",
        user_auth_token,
    )
    get_ticket_url = urljoin(
        settings.DAKTELA["base_rest_api_url"],
        f"tickets/{uniq_name}.json",
    )
    request = requests.models.PreparedRequest()
    request.prepare_url(get_ticket_url, {"accessToken": user_auth_token})
    try:
        response = requests.get(request.url)
        if response.ok:
            return True
        else:
            if response.status_code == 404:
                return False
            else:
                logger.error(
                    error_message.format(
                        error=response.status_code,
                        name=uniq_name,
                    )
                )
    except (
        requests.RequestException,
        requests.ConnectionError,
        requests.HTTPError,
        requests.URLRequired,
        requests.TooManyRedirects,
        requests.Timeout,
    ) as error:
        logger.error(
            error_message.format(
                error=error,
                name=uniq_name,
            )
        )


def get_tickets(user_auth_token):
    """
    Get Daktela app tickets

    :param str user_auth_token: Daktela app user auth token

    :return dict: Daktela app Tickets model dict
    """
    error_message = "Obtain Daktela app tickets fails due error: '{error}'"
    get_tickets_url = urljoin(
        settings.DAKTELA["base_rest_api_url"],
        "tickets.json",
    )
    request = requests.models.PreparedRequest()
    request.prepare_url(get_tickets_url, {"accessToken": user_auth_token})
    try:
        response = requests.get(request.url)
        if response.ok:
            return response.json()
        else:
            logger.error(
                error_message.format(
                    error=response.status_code,
                )
            )
    except (
        requests.RequestException,
        requests.ConnectionError,
        requests.HTTPError,
        requests.URLRequired,
        requests.TooManyRedirects,
        requests.Timeout,
    ) as error:
        logger.error(
            error_message.format(
                error=error,
            )
        )


def get_tickets_max_uniq_id(
    tickets,
    category_name="categories_649d3e48d108b040473027",
):
    """Get Daktela app Hovor category title tickets max uniq id

    :param dict tickets: Daktela app Tickets models dict
    :param str category_name: Daktela app Tickets category unique name
                              with default value categories_649d3e48d108b040473027
                              which is Hovor (title)
    :retun int: max Daktela app Tickets uniq id
    """
    for ticket in tickets["result"]["data"]:
        if ticket["category"]["name"] == category_name:
            return ticket["name"]


def get_ticket_by_uniq_title(title, user_auth_token):
    """Get Daktela app Ticket model instance by unique title

    :param str title: Ticket model unique title
    :param str user_auth_token: Daktela app user auth token

    :return str: corresponding Ticket model unique name
    """
    tickets = get_tickets(user_auth_token)["result"]["data"]
    for ticket in tickets:
        if ticket["title"].split("-")[0] == title:
            return ticket["name"]


def create_or_update_ticket(
    interaction,
    user_auth_token,
    create=True,
    uniq_name=None,
    uniq_name_id_increment=1,
    category_name="categories_649d3e48d108b040473027",
):
    """
    Create or update Daktela app ticket

    :param object interaction: Interaction model instance
    :param str user_auth_token: Daktela app user auth token
    :param bool create: create contact if True else update existed contact
    :param str category_name: Daktela app Tickets category unique name
                              with default value categories_649d3e48d108b040473027
                              which is Hovor (title)
    """
    error_message = (
        "{operation} Daktela app ticket with name '{name}' fails due error:"
        " '{error}'"
    )
    uniq_name = get_uniq_ticket_name(interaction)
    uniq_title = f"{uniq_name}-{interaction.subject}"
    uniq_name = get_ticket_by_uniq_title(uniq_name, user_auth_token)
    data = {
        "title": uniq_title,
        "contact": get_uniq_contact_name(
            interaction.user
        ),  # "4f7543569c37266307170bfc72852fca",
        "category": category_name,  # Hovor (title) category name
        "stage": "OPEN",
        "priority": "LOW",
        "sla_deadtime": interaction.date_from,
    }
    if create:
        contacts_url = urljoin(
            settings.DAKTELA["base_rest_api_url"],
            "tickets.json",
        )
        operation = "Create"
        data["name"] = str(
            get_tickets_max_uniq_id(get_tickets(user_auth_token))
            + uniq_name_id_increment
        )
    else:
        if not uniq_name:
            uniq_name = get_ticket_by_uniq_title(uniq_title, user_auth_token)
        contacts_url = urljoin(
            settings.DAKTELA["base_rest_api_url"],
            f"tickets/{uniq_name}.json",
        )
        operation = "Update"
    request = requests.models.PreparedRequest()
    request.prepare_url(contacts_url, {"accessToken": user_auth_token})
    try:
        if create:
            response = requests.post(request.url, data)
        else:
            response = requests.put(request.url, data)
        if not response.ok:
            if response.status_code == 400:
                create_or_update_ticket(
                    interaction,
                    user_auth_token,
                    create=create,
                    uniq_name=None,
                    uniq_name_id_increment=uniq_name_id_increment + 1,
                )
            else:
                logger.error(
                    error_message.format(
                        operation=operation,
                        name=uniq_name,
                        error=response.status_code,
                    )
                )
    except (
        requests.RequestException,
        requests.ConnectionError,
        requests.HTTPError,
        requests.URLRequired,
        requests.TooManyRedirects,
        requests.Timeout,
    ) as error:
        logger.error(
            error_message.format(
                operation=operation,
                name=uniq_name,
                error=error,
            )
        )


def delete_ticket(interaction, user_auth_token):
    """
    Delete Daktela app ticket

    :param object|str interaction: Interaction model instance or Daktela
                                   app Ticket model instance unique name
    :param str user_auth_token: Daktela app user auth token
    """
    from interactions.models import Interaction

    if isinstance(interaction, Interaction):
        uniq_name = get_ticket_by_uniq_title(
            get_uniq_ticket_name(interaction),
            user_auth_token,
        )
    else:
        uniq_name = interaction
    if uniq_name:
        error_message = (
            "Delete Daktela app ticket with name '{name}' fails due error: '{error}'"
        )
        get_tickets_url = urljoin(
            settings.DAKTELA["base_rest_api_url"],
            f"tickets/{uniq_name}.json",
        )
        request = requests.models.PreparedRequest()
        request.prepare_url(get_tickets_url, {"accessToken": user_auth_token})
        try:
            response = requests.delete(request.url)
            if not response.ok:
                logger.error(
                    error_message.format(
                        error=response.status_code,
                        name=uniq_name,
                    )
                )
        except (
            requests.RequestException,
            requests.ConnectionError,
            requests.HTTPError,
            requests.URLRequired,
            requests.TooManyRedirects,
            requests.Timeout,
        ) as error:
            logger.error(
                error_message.format(
                    error=error,
                    name=uniq_name,
                )
            )


def sync_contacts(userprofiles):
    """
    Sync UserProfiles (create/update) with Daktela web app

    :param object userprofiles: list of UserProfiles models instance
    """
    user_auth_token = get_user_auth_token()
    if user_auth_token:
        for userprofile in userprofiles:
            # Update contact
            if get_contact(userprofile, user_auth_token):
                create_or_update_contact(
                    userprofile,
                    user_auth_token,
                    create=False,
                )
            # Create contact
            else:
                create_or_update_contact(userprofile, user_auth_token)


def sync_tickets(interactions):
    """
    Sync Interaction (create/update) with Daktela web app

    :param object interactions: list of Interaction models instance
    """
    user_auth_token = get_user_auth_token()
    if user_auth_token:
        for interaction in interactions:
            # Update ticket
            uniq_name = get_ticket_by_uniq_title(
                get_uniq_ticket_name(interaction),
                user_auth_token,
            )
            if uniq_name:
                create_or_update_ticket(
                    interaction,
                    user_auth_token,
                    create=False,
                    uniq_name=uniq_name,
                )
            # Create ticket
            else:
                create_or_update_ticket(
                    interaction,
                    user_auth_token,
                    uniq_name=uniq_name,
                )
