from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import ValidationError

from connections.models import Connection
from workspace.models import StoredFile

from .models import FileShare


def accessible_files(user):
    return StoredFile.objects.filter(
        Q(owner=user) | Q(shares__user=user),
    ).prefetch_related('shares').distinct()


def accessible_file(user, file_id):
    return get_object_or_404(accessible_files(user), pk=file_id)


def owned_file(user, file_id):
    return get_object_or_404(StoredFile, pk=file_id, owner=user)


def file_access(stored_file, user):
    if stored_file.owner_id == user.pk:
        return {'role': 'owner', 'permission': 'edit'}
    share = next((share for share in stored_file.shares.all() if share.user_id == user.pk), None)
    if share is None:
        raise Http404
    return {'role': 'shared', 'permission': share.permission}


def require_edit(stored_file, user):
    if file_access(stored_file, user)['permission'] != FileShare.Permission.EDIT:
        raise Http404


def file_shares(stored_file, user):
    if stored_file.owner_id != user.pk:
        raise Http404
    return stored_file.shares.select_related('user')


def share_file(stored_file, user, *, recipient, permission):
    if stored_file.owner_id != user.pk:
        raise Http404
    if permission == FileShare.Permission.EDIT and not hasattr(stored_file, 'document'):
        raise ValidationError({'detail': 'Only DropShare documents can be shared with edit permission.'})
    is_connected = Connection.objects.filter(status=Connection.Status.ACCEPTED).filter(
        Q(sender=user, recipient=recipient) | Q(sender=recipient, recipient=user),
    ).exists()
    if not is_connected:
        raise ValidationError({'detail': 'You can only share files with accepted connections.'})
    share, _ = FileShare.objects.update_or_create(
        file=stored_file,
        user=recipient,
        defaults={'permission': permission},
    )
    return share


def revoke_share(stored_file, user, share_id):
    if stored_file.owner_id != user.pk:
        raise Http404
    get_object_or_404(FileShare, pk=share_id, file=stored_file).delete()
