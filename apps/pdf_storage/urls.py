from django.urls import path

from . import views

urlpatterns = [
    path(
        "<int:related_id>/list/",
        views.RelatedPdfListView.as_view(),
        name="pdfstorage_list",
    ),
    path(
        "pdf_file/<int:id>/",
        views.PaidPdfDownloadView.as_view(),
        name="pdfstorage_detail",
    ),
    path(
        "all_related_ids/",
        views.AllRelatedIdsView.as_view(),
        name="pdf_storage_all_related_ids",
    ),
]
