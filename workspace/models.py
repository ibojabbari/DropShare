from pathlib import Path
from uuid import uuid4

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models


def private_file_upload_path(instance, filename):
    """Store files under an unguessable name, never their user-provided name."""
    suffix = Path(filename).suffix.lower()
    if not suffix.isalnum() and not (suffix.startswith('.') and suffix[1:].isalnum()):
        suffix = ''
    return f'private/{instance.owner_id}/{uuid4().hex}{suffix}'


class StoredFile(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_files',
    )
    file = models.FileField(upload_to=private_file_upload_path, max_length=500)
    original_name = models.CharField(max_length=255)
    content_type = models.CharField(max_length=255, blank=True)
    size = models.PositiveBigIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['owner', '-created_at'])]

    def __str__(self):
        return self.original_name


class Document(models.Model):
    file = models.OneToOneField(StoredFile, on_delete=models.CASCADE, related_name='document')
    content = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.file.file.save(
            self.file.original_name,
            ContentFile(self.content.encode('utf-8')),
            save=True,
        )
        self.file.size = self.file.file.size
        self.file.save(update_fields=['file', 'size'])
