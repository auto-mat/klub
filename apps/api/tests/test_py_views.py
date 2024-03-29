from aklub.models import UserProfile

from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from freezegun import freeze_time


class TestAdministrativeUnitView:
    def test_administrative_unit_get_request(
        self, administrative_unit_1, userprofile_superuser_2, app_request
    ):
        url = reverse("administrative_unit")
        response = app_request.get(url)
        assert response.status_code == 200
        assert len(response.json()) == 1
        resp_data = response.json()[0]
        assert resp_data["id"] == administrative_unit_1.id
        assert resp_data["name"] == administrative_unit_1.name
        assert resp_data["city"] == administrative_unit_1.city
        assert resp_data["street"] == administrative_unit_1.street
        assert resp_data["zip_code"] == administrative_unit_1.zip_code
        assert resp_data["gps_latitude"] == administrative_unit_1.gps_latitude
        assert resp_data["gps_longitude"] == administrative_unit_1.gps_longitude
        assert resp_data["telephone"] == administrative_unit_1.telephone
        assert (
            resp_data["from_email_address"] == administrative_unit_1.from_email_address
        )
        assert resp_data["web_url"] == administrative_unit_1.web_url
        assert (
            resp_data["president_name"]
            == f"{userprofile_superuser_2.first_name} {userprofile_superuser_2.last_name}"
        )
        assert (
            resp_data["manager_name"]
            == f"{userprofile_superuser_2.first_name} {userprofile_superuser_2.last_name}"
        )
        assert resp_data["level"] == administrative_unit_1.level


class TestEventView:
    def _assert_data(
        self,
        data,
        event_1,
        location_1,
        event_type_1,
        userprofile_superuser_2,
        telephone_2,
        profileemail_2,
    ):
        assert data["name"] == event_1.name
        assert data["date_from"] == event_1.date_from
        assert data["date_to"] == event_1.date_to
        assert data["program"] == event_1.program
        assert data["intended_for"] == event_1.intended_for
        assert data["responsible_person"] == event_1.responsible_person
        assert (
            data["administrative_unit_name"]
            == event_1.administrative_units.first().name
        )
        assert (
            data["administrative_unit_web_url"]
            == event_1.administrative_units.first().web_url
        )

        location = data["location"]
        assert location["name"] == location_1.name
        assert location["place"] == location_1.place
        assert location["region"] == location_1.region
        assert location["gps_latitude"] == location_1.gps_latitude
        assert location["gps_longitude"] == location_1.gps_longitude

        event_type = data["event_type"]
        assert event_type["name"] == event_type_1.name
        assert event_type["slug"] == event_type_1.slug

        assert data["age_from"] == event_1.age_from
        assert data["age_to"] == event_1.age_to
        assert data["start_date"] == event_1.start_date
        assert data["participation_fee"] == event_1.participation_fee
        assert data["accommodation"] == event_1.accommodation
        assert data["diet"] == event_1.diet
        assert data["looking_forward_to_you"] == event_1.looking_forward_to_you
        assert data["working_hours"] == event_1.working_hours

        assert data["entry_form_url"] == event_1.entry_form_url
        assert data["web_url"] == event_1.web_url
        assert data["invitation_text_1"] == event_1.invitation_text_1
        assert data["invitation_text_2"] == event_1.invitation_text_2
        assert data["invitation_text_3"] == event_1.invitation_text_3
        assert data["invitation_text_4"] == event_1.invitation_text_4
        assert data["additional_photo_1"] == event_1.additional_photo_1
        assert data["additional_photo_2"] == event_1.additional_photo_2
        assert data["additional_photo_3"] == event_1.additional_photo_3
        assert data["additional_photo_4"] == event_1.additional_photo_4
        assert data["additional_photo_5"] == event_1.additional_photo_5
        assert data["additional_photo_6"] == event_1.additional_photo_6
        assert data["additional_question_1"] == event_1.additional_question_1
        assert data["additional_question_2"] == event_1.additional_question_2
        assert data["additional_question_3"] == event_1.additional_question_3
        assert data["contact_person_name"] == event_1.contact_person_name
        assert data["contact_person_email"] == event_1.contact_person_email
        assert data["contact_person_telephone"] == event_1.contact_person_telephone

    def test_event_list_view(
        self,
        event_1,
        app_request,
        location_1,
        userprofile_superuser_2,
        organization_team_1,
        organization_position_1,
        profileemail_2,
        event_type_1,
        telephone_2,
    ):
        url = reverse("event")
        response = app_request.get(url)
        assert response.status_code == 200
        assert len(response.json()["results"]) == 1
        data = response.json()["results"][0]
        self._assert_data(
            data,
            event_1,
            location_1,
            event_type_1,
            userprofile_superuser_2,
            telephone_2,
            profileemail_2,
        )

    def test_event_detail_view(
        self,
        event_1,
        app_request,
        location_1,
        userprofile_superuser_2,
        organization_team_1,
        organization_position_1,
        profileemail_2,
        event_type_1,
        telephone_2,
    ):
        url = reverse("event_detail", kwargs={"id": event_1.id})
        response = app_request.get(url)
        assert response.status_code == 200
        data = response.json()
        self._assert_data(
            data,
            event_1,
            location_1,
            event_type_1,
            userprofile_superuser_2,
            telephone_2,
            profileemail_2,
        )
