from django.urls import reverse


class TestAdministrativeUnitViewFilters:
    def test_administrative_unit_custom_filter(
        self, event_1, event_2, app_request, administrative_unit_1
    ):
        # without filter
        url = reverse("event")
        response = app_request.get(url)
        assert response.status_code == 200
        assert len(response.json()) == 2

        # with administrative_unit_
        url = reverse("event") + f"?administrative_unit={administrative_unit_1.id}"
        response = app_request.get(url)
        assert len(response.json()) == 1
        assert response.status_code == 200
        assert response.json()[0]["id"] == event_1.id
