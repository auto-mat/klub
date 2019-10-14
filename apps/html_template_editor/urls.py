
from django.urls import path

from . import upload_views, views

urlpatterns = [
    path(
        'add/',
        views.TemplateContentAdd.as_view(),
        name='add',
    ),
    path(
        'retrieve/<uuid:uuid>/',
        views.TemplateContentRetrieve.as_view(),
        name="retrieve",
    ),
    path(
        'update/<uuid:uuid>/',
        views.TemplateContentUpdate.as_view(),
        name='update',
    ),
    path(
        'list/',
        views.TemplateContentList.as_view(),
        name="list",
    ),
    path(
        'delete/<uuid:uuid>/',
        views.TemplateContentDelete.as_view(),
        name="delete",
    ),
    path(
        'images/add/',
        upload_views.ImagesAdd.as_view(),
        name='images_add',
    ),
    path(
        'images/update/<int:id>/',
        upload_views.ImagesUpdate.as_view(),
        name='images_update',
    ),
    path(
        'images/list/',
        upload_views.ImagesList.as_view(),
        name='images_list',
    ),
]
