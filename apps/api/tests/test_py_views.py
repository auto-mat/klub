from django.urls import reverse


class TestAdministrativeUnitView:
    def test_administrative_unit_get_request(self, administrative_unit_1, userprofile_superuser_2, app_request):
        url = reverse('administrative_unit')
        response = app_request.get(url)
        assert response.status_code == 200
        assert len(response.json()) == 1
        resp_data = response.json()[0]
        assert resp_data["id"] == administrative_unit_1.id
        assert resp_data["name"] == administrative_unit_1.name
        assert resp_data["city"] == administrative_unit_1.city
        assert resp_data["zip_code"] == administrative_unit_1.zip_code
        assert resp_data["gps_latitude"] == administrative_unit_1.gps_latitude
        assert resp_data["gps_longitude"] == administrative_unit_1.gps_longitude
        assert resp_data["telephone"] == administrative_unit_1.telephone
        assert resp_data["from_email_address"] == administrative_unit_1.from_email_address
        assert resp_data["web_url"] == administrative_unit_1.web_url
        assert resp_data["president_name"] == f"{userprofile_superuser_2.first_name} {userprofile_superuser_2.last_name}"
        assert resp_data["manager_name"] == f"{userprofile_superuser_2.first_name} {userprofile_superuser_2.last_name}"


class TestEventView:
    def test_event_list_view(
            self, event_1, app_request, location_1,  userprofile_superuser_2, organization_team_1, organization_position_1,
            profileemail_2, telephone_2,
            ):
        url = reverse('event')
        response = app_request.get(url)
        assert response.status_code == 200
        assert len(response.json()) == 1
        data = response.json()[0]

        assert data['name'] == event_1.name
        assert data['slug'] == event_1.slug
        assert data['date_from'] == event_1.date_from
        assert data['date_to'] == event_1.date_to
        assert data['program'] == event_1.program
        assert data['indended_for'] == event_1.indended_for

        location = data['location']
        assert location['name'] == location_1.name
        assert location['place'] == location_1.place
        assert location['region'] == location_1.region
        assert location['gps'] == location_1.gps

        assert data['age_from'] == event_1.age_from
        assert data['age_to'] == event_1.age_to
        assert data['start_date'] == event_1.start_date
        assert data['participation_fee'] == event_1.participation_fee

        assert len(data['organization_team']) == 1
        organization_team = data['organization_team'][0]
        assert organization_team["first_name"] == userprofile_superuser_2.first_name
        assert organization_team["last_name"] == userprofile_superuser_2.last_name
        assert organization_team["email"] == profileemail_2.email
        assert organization_team["telephone"] == telephone_2.telephone

        assert data['entry_form_url'] == event_1.entry_form_url
        assert data['web_url'] == event_1.web_url
        assert data['invitation_text_1'] == event_1.invitation_text_1
        assert data['invitation_text_2'] == event_1.invitation_text_2
        assert data['invitation_text_3'] == event_1.invitation_text_3
        assert data['invitation_text_4'] == event_1.invitation_text_4
        assert data['additional_photo_1'] == event_1.additional_photo_1
        assert data['additional_photo_2'] == event_1.additional_photo_2
        assert data['additional_photo_3'] == event_1.additional_photo_3
        assert data['additional_photo_4'] == event_1.additional_photo_4
        assert data['additional_photo_5'] == event_1.additional_photo_5
        assert data['additional_photo_6'] == event_1.additional_photo_6
