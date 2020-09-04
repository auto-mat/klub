from django.urls import path

from . import views

urlpatterns = [
    path('<int:related_id>/list/', views.RelatedPdfListView.as_view(), name='pdfstorage_list'),
    path('pdf_file/<int:id>/', views.PaidPdfDownloadView.as_view(), name='pdfstorage_detail'),
]
