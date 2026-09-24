import shutil
import tempfile
from pathlib import Path

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from django.core.files.uploadedfile import SimpleUploadedFile
from rest_framework import status
from rest_framework.test import APIClient, APITestCase

from connections.models import Connection

from .models import Document, StoredFile


class PrivateFileTests(APITestCase):
    def setUp(self):
        # Throttle state is shared between test clients; isolate each test case.
        cache.clear()
        self.media_dir = tempfile.mkdtemp()
        self.media_override = override_settings(MEDIA_ROOT=self.media_dir)
        self.media_override.enable()
        self.alice = User.objects.create_user('alice', password='CorrectHorseBatteryStaple!2026')
        self.bob = User.objects.create_user('bob', password='CorrectHorseBatteryStaple!2026')

    def tearDown(self):
        self.media_override.disable()
        shutil.rmtree(self.media_dir, ignore_errors=True)

    def authenticated_client(self, username):
        client = APIClient(enforce_csrf_checks=True)
        csrf_response = client.get('/api/auth/csrf/')
        login_response = client.post(
            '/api/auth/login/',
            {'username': username, 'password': 'CorrectHorseBatteryStaple!2026'},
            format='json',
            HTTP_X_CSRFTOKEN=csrf_response.data['csrfToken'],
        )
        self.assertEqual(login_response.status_code, status.HTTP_200_OK)
        return client, login_response.data['csrfToken']

    def create_file(self, owner, name='private-notes.txt', content=b'Private notes'):
        return StoredFile.objects.create(
            owner=owner,
            file=SimpleUploadedFile(name, content, content_type='text/plain'),
            original_name=name,
            content_type='text/plain',
            size=len(content),
        )

    def test_authenticated_owner_can_upload_and_list_a_file(self):
        client, csrf_token = self.authenticated_client('alice')
        upload = SimpleUploadedFile('private-notes.txt', b'Private notes', content_type='text/plain')

        response = client.post(
            reverse('workspace:file-list-create'),
            {'files': [upload]},
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['files'][0]['original_name'], 'private-notes.txt')
        self.assertEqual(StoredFile.objects.get().owner, self.alice)

        list_response = client.get(reverse('workspace:file-list-create'))
        self.assertEqual(list_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(list_response.data['files']), 1)

    def test_user_only_sees_their_own_files(self):
        self.create_file(self.alice, name='alice.txt')
        self.create_file(self.bob, name='bob.txt')
        client, _ = self.authenticated_client('alice')

        response = client.get(reverse('workspace:file-list-create'))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual([item['original_name'] for item in response.data['files']], ['alice.txt'])

    def test_owner_can_download_file_as_an_attachment(self):
        stored_file = self.create_file(self.alice)
        client, _ = self.authenticated_client('alice')

        response = client.get(reverse('workspace:file-download', kwargs={'file_id': stored_file.pk}))

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('attachment;', response['Content-Disposition'])
        # Browsers must not guess a different MIME type and execute the download as active content.
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')
        self.assertEqual(b''.join(response.streaming_content), b'Private notes')

    def test_other_authenticated_user_cannot_download_or_delete_file(self):
        stored_file = self.create_file(self.alice)
        client, csrf_token = self.authenticated_client('bob')
        detail_url = reverse('workspace:file-detail', kwargs={'file_id': stored_file.pk})

        download_response = client.get(
            reverse('workspace:file-download', kwargs={'file_id': stored_file.pk})
        )
        delete_response = client.delete(detail_url, HTTP_X_CSRFTOKEN=csrf_token)

        # A missing response does not reveal that Alice's file exists to Bob (IDOR protection).
        self.assertEqual(download_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(delete_response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(StoredFile.objects.filter(pk=stored_file.pk).exists())

    def test_owner_can_delete_their_file_and_its_stored_contents(self):
        stored_file = self.create_file(self.alice)
        stored_file_path = Path(stored_file.file.path)
        client, csrf_token = self.authenticated_client('alice')

        response = client.delete(
            reverse('workspace:file-detail', kwargs={'file_id': stored_file.pk}),
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(StoredFile.objects.filter(pk=stored_file.pk).exists())
        self.assertFalse(stored_file_path.exists())

    @override_settings(MAX_UPLOAD_SIZE=4)
    def test_upload_rejects_a_file_over_the_size_limit(self):
        client, csrf_token = self.authenticated_client('alice')

        response = client.post(
            reverse('workspace:file-list-create'),
            {'files': [SimpleUploadedFile('too-large.txt', b'12345')]},
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(StoredFile.objects.exists())

    @override_settings(MAX_UPLOAD_SIZE=10, MAX_BATCH_UPLOAD_SIZE=4)
    def test_upload_rejects_files_that_exceed_the_batch_size_limit(self):
        client, csrf_token = self.authenticated_client('alice')

        response = client.post(
            reverse('workspace:file-list-create'),
            {
                'files': [
                    SimpleUploadedFile('first.txt', b'123'),
                    SimpleUploadedFile('second.txt', b'45'),
                ]
            },
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(StoredFile.objects.exists())

    def test_upload_requires_a_csrf_token(self):
        client, _ = self.authenticated_client('alice')

        response = client.post(
            reverse('workspace:file-list-create'),
            {'files': [SimpleUploadedFile('private.txt', b'Private')]},
        )

        # Upload changes server state, so a logged-in browser still needs a CSRF token.
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_upload_rejects_svg_and_executable_files(self):
        client, csrf_token = self.authenticated_client('alice')

        for filename, content in (
            ('unsafe.svg', b'<svg></svg>'),
            ('installer.exe', b'MZ executable content'),
            ('disguised.txt', b'MZ executable content'),
        ):
            response = client.post(
                reverse('workspace:file-list-create'),
                {'files': [SimpleUploadedFile(filename, content)]},
                HTTP_X_CSRFTOKEN=csrf_token,
            )

            self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # The .txt filename confirms the server also checks executable file signatures, not only extensions.
        self.assertFalse(StoredFile.objects.exists())

    def test_read_only_share_can_download_but_cannot_edit_a_document(self):
        stored_file = self.create_file(self.alice, name='shared.txt', content=b'Original')
        document = Document.objects.create(file=stored_file, content='Original')
        Connection.objects.create(
            sender=self.alice,
            recipient=self.bob,
            status=Connection.Status.ACCEPTED,
        )
        owner_client, owner_csrf_token = self.authenticated_client('alice')
        share_response = owner_client.post(
            reverse('permissions:file-shares', kwargs={'file_id': stored_file.pk}),
            {'username': 'bob', 'permission': 'read'},
            format='json',
            HTTP_X_CSRFTOKEN=owner_csrf_token,
        )
        self.assertEqual(share_response.status_code, status.HTTP_201_CREATED)

        bob_client, bob_csrf_token = self.authenticated_client('bob')
        read_response = bob_client.get(reverse('workspace:document-detail', kwargs={'file_id': stored_file.pk}))
        download_response = bob_client.get(reverse('workspace:file-download', kwargs={'file_id': stored_file.pk}))
        update_response = bob_client.patch(
            reverse('workspace:document-detail', kwargs={'file_id': stored_file.pk}),
            {'content': 'Changed'},
            format='json',
            HTTP_X_CSRFTOKEN=bob_csrf_token,
        )

        self.assertEqual(read_response.status_code, status.HTTP_200_OK)
        self.assertEqual(read_response.data['content'], document.content)
        self.assertEqual(download_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.status_code, status.HTTP_404_NOT_FOUND)
        document.refresh_from_db()
        self.assertEqual(document.content, 'Original')

    def test_edit_share_can_update_document_but_cannot_manage_shares(self):
        stored_file = self.create_file(self.alice, name='team-note.txt')
        Document.objects.create(file=stored_file, content='Draft')
        Connection.objects.create(
            sender=self.alice,
            recipient=self.bob,
            status=Connection.Status.ACCEPTED,
        )
        owner_client, owner_csrf_token = self.authenticated_client('alice')
        owner_client.post(
            reverse('permissions:file-shares', kwargs={'file_id': stored_file.pk}),
            {'username': 'bob', 'permission': 'edit'},
            format='json',
            HTTP_X_CSRFTOKEN=owner_csrf_token,
        )

        bob_client, bob_csrf_token = self.authenticated_client('bob')
        update_response = bob_client.patch(
            reverse('workspace:document-detail', kwargs={'file_id': stored_file.pk}),
            {'content': 'Updated by Bob'},
            format='json',
            HTTP_X_CSRFTOKEN=bob_csrf_token,
        )
        share_response = bob_client.get(
            reverse('permissions:file-shares', kwargs={'file_id': stored_file.pk})
        )

        self.assertEqual(update_response.status_code, status.HTTP_200_OK)
        self.assertEqual(update_response.data['content'], 'Updated by Bob')
        self.assertEqual(share_response.status_code, status.HTTP_404_NOT_FOUND)

    def test_regular_files_cannot_receive_edit_permission(self):
        stored_file = self.create_file(self.alice, name='image.png')
        Connection.objects.create(
            sender=self.alice,
            recipient=self.bob,
            status=Connection.Status.ACCEPTED,
        )
        client, csrf_token = self.authenticated_client('alice')

        response = client.post(
            reverse('permissions:file-shares', kwargs={'file_id': stored_file.pk}),
            {'username': 'bob', 'permission': 'edit'},
            format='json',
            HTTP_X_CSRFTOKEN=csrf_token,
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_image_preview_is_private(self):
        image = self.create_file(self.alice, name='photo.png', content=b'\x89PNG\r\n\x1a\nimage')
        image.content_type = 'image/png'
        image.save(update_fields=['content_type'])

        alice_client, _ = self.authenticated_client('alice')
        bob_client, _ = self.authenticated_client('bob')
        preview_url = reverse('workspace:file-preview', kwargs={'file_id': image.pk})

        preview_response = alice_client.get(preview_url)
        other_user_response = bob_client.get(preview_url)

        self.assertEqual(preview_response.status_code, status.HTTP_200_OK)
        self.assertEqual(preview_response['Content-Type'], 'image/png')
        # This stops browsers from trying to reinterpret an image response as another content type.
        self.assertEqual(preview_response['X-Content-Type-Options'], 'nosniff')
        # A private preview must not become visible just because another user knows its UUID.
        self.assertEqual(other_user_response.status_code, status.HTTP_404_NOT_FOUND)
