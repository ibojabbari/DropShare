from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from .models import Connection


class ConnectionTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.alice = User.objects.create_user('alice')
        self.bob = User.objects.create_user('bob')
        self.alice_client = APIClient()
        self.alice_client.force_authenticate(self.alice)
        self.bob_client = APIClient()
        self.bob_client.force_authenticate(self.bob)




    def test_user_can_request_a_connection(self):
        """Just a basic test where a user could request a connection"""
        response = self.alice_client.post(reverse('connections:list-create'), {'username': 'bob'})

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Connection.objects.filter(sender=self.alice, recipient=self.bob).exists())




    def test_only_the_recipient_can_accept_a_connection(self):
        """Only the recipient can accept a pending connection request."""
        connection = Connection.objects.create(sender=self.alice, recipient=self.bob)
        url = reverse('connections:accept', kwargs={'connection_id': connection.pk})

        self.assertEqual(self.alice_client.post(url).status_code, 404)
        self.assertEqual(self.bob_client.post(url).status_code, 200)
        connection.refresh_from_db()
        self.assertEqual(connection.status, Connection.Status.ACCEPTED) # Confirm the database was updated.
