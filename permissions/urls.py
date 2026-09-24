from django.urls import path

from .views import FileShareDetailView, FileSharesView

app_name = 'permissions'

urlpatterns = [
    path('files/<uuid:file_id>/shares/', FileSharesView.as_view(), name='file-shares'),
    path('files/<uuid:file_id>/shares/<int:share_id>/', FileShareDetailView.as_view(), name='file-share-detail'),
]
