from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="files-index"),
    path("preview", views.preview, name="files-preview"),
]
