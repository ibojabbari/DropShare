from django.urls import path

from .views import (
    DocumentDetailView, DocumentsView,
    FileDownloadView, FilePreviewView, OwnedFileDetailView,
    OwnedFilesView,
)

app_name = 'workspace'

urlpatterns = [
    path('', OwnedFilesView.as_view(), name='file-list-create'),
    path('documents/', DocumentsView.as_view(), name='documents'),
    path('<uuid:file_id>/document/', DocumentDetailView.as_view(), name='document-detail'),
    path('<uuid:file_id>/preview/', FilePreviewView.as_view(), name='file-preview'),
    path('<uuid:file_id>/download/', FileDownloadView.as_view(), name='file-download'),
    path('<uuid:file_id>/', OwnedFileDetailView.as_view(), name='file-detail'),
]
