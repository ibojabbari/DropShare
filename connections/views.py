from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Connection
from .serializers import ConnectionSerializer, CreateConnectionSerializer


class ConnectionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        connections = Connection.objects.filter(
            Q(sender=request.user) | Q(recipient=request.user),
        ).select_related('sender', 'recipient')
        return Response({
            'connections': ConnectionSerializer(connections, many=True, context={'request': request}).data,
        })

    def post(self, request):
        serializer = CreateConnectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        recipient = serializer.validated_data['username']
        if recipient == request.user:
            raise ValidationError({'detail': 'You cannot connect to yourself.'})
        if Connection.objects.filter(
            Q(sender=request.user, recipient=recipient) | Q(sender=recipient, recipient=request.user),
        ).exists():
            raise ValidationError({'detail': 'A connection already exists between these users.'})

        connection = Connection.objects.create(sender=request.user, recipient=recipient)
        return Response(
            ConnectionSerializer(connection, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )


class AcceptConnectionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, connection_id):
        connection = get_object_or_404(
            Connection,
            pk=connection_id,
            recipient=request.user,
            status=Connection.Status.PENDING,
        )
        connection.status = Connection.Status.ACCEPTED
        connection.save(update_fields=['status'])
        return Response(ConnectionSerializer(connection, context={'request': request}).data)
