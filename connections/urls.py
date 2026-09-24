from django.urls import path

from .views import AcceptConnectionView, ConnectionsView

app_name = 'connections'

urlpatterns = [
    path('', ConnectionsView.as_view(), name='list-create'),
    path('<int:connection_id>/accept/', AcceptConnectionView.as_view(), name='accept'),
]
