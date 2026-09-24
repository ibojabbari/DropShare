from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from . import services
from .serializers import CreateFileShareSerializer, FileShareSerializer


class FileSharesView(APIView):
    permission_classes = [IsAuthenticated]

    def get_file(self, request, file_id):
        return services.owned_file(request.user, file_id)

    def get(self, request, file_id):
        stored_file = self.get_file(request, file_id)
        shares = services.file_shares(stored_file, request.user)
        return Response({'shares': FileShareSerializer(shares, many=True).data})

    def post(self, request, file_id):
        stored_file = self.get_file(request, file_id)
        serializer = CreateFileShareSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        share = services.share_file(
            stored_file,
            request.user,
            recipient=serializer.validated_data['username'],
            permission=serializer.validated_data['permission'],
        )
        return Response(FileShareSerializer(share).data, status=status.HTTP_201_CREATED)


class FileShareDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, file_id, share_id):
        stored_file = services.owned_file(request.user, file_id)
        services.revoke_share(stored_file, request.user, share_id)
        return Response(status=status.HTTP_204_NO_CONTENT)
