from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient, APITestCase

from connections.models import Connection
from workspace.models import StoredFile

from .models import FileShare


class FileShareTests(APITestCase):
    def setUp(self):
        User = get_user_model()
        self.alice = User.objects.create_user('alice')
        self.bob = User.objects.create_user('bob')
        self.file = StoredFile.objects.create(
            owner=self.alice,
            file='private/test.txt',
            original_name='test.txt',
            size=4,
        )
        self.alice_client = APIClient()
        self.alice_client.force_authenticate(self.alice)
        self.bob_client = APIClient()
        self.bob_client.force_authenticate(self.bob)

    def test_only_the_owner_can_revoke_a_share(self):
        share = FileShare.objects.create(file=self.file, user=self.bob)
        url = reverse('permissions:file-share-detail', kwargs={
            'file_id': self.file.pk,
            'share_id': share.pk,
        })

        self.assertEqual(self.bob_client.delete(url).status_code, 404)
        self.assertEqual(self.alice_client.delete(url).status_code, 204)
        self.assertFalse(FileShare.objects.filter(pk=share.pk).exists())

    def test_only_accepted_connections_can_receive_a_share(self):
        url = reverse('permissions:file-shares', kwargs={'file_id': self.file.pk})

        pending_response = self.alice_client.post(url, {'username': 'bob', 'permission': 'read'})
        Connection.objects.create(sender=self.alice, recipient=self.bob, status=Connection.Status.ACCEPTED)
        accepted_response = self.alice_client.post(url, {'username': 'bob', 'permission': 'read'})

        self.assertEqual(pending_response.status_code, 400)
        self.assertEqual(accepted_response.status_code, 201)
