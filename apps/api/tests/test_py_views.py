from django.urls import reverse


class TestAdministrativeUnitView:
    def test_administrative_unit_get_request(self, administrative_unit_1, userprofile_superuser_2, app_request):
        url = reverse('administrative_unit')
        response = app_request.get(url)
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
