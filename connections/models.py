from django.conf import settings
from django.db import models


class Connection(models.Model):
    """A connection request between two accounts."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        ACCEPTED = 'accepted', 'Accepted'

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_connections',
    )
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_connections',
    )
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'workspace_connection'
        constraints = [
            models.UniqueConstraint(fields=['sender', 'recipient'], name='unique_connection_direction'),
            models.CheckConstraint(
                condition=~models.Q(sender=models.F('recipient')),
                name='connection_users_are_different',
            ),
        ]
