from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="files-index"),
    path("preview", views.preview, name="files-preview"),
    path("download", views.download, name="files-download"),
    path("download-bulk", views.download_bulk, name="files-download-bulk"),
]
