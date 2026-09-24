from django.conf import settings
from django.db import models


class FileShare(models.Model):
    class Permission(models.TextChoices):
        READ = 'read', 'Read only'
        EDIT = 'edit', 'Can edit'

    file = models.ForeignKey('workspace.StoredFile', on_delete=models.CASCADE, related_name='shares')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='file_shares')
    permission = models.CharField(max_length=4, choices=Permission.choices, default=Permission.READ)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'workspace_fileshare'
        constraints = [
            models.UniqueConstraint(fields=['file', 'user'], name='one_share_per_user_per_file'),
        ]
