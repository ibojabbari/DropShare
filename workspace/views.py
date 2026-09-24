from django.core.files.base import ContentFile
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from permissions import services as permissions

from .models import Document, StoredFile
from .serializers import (
    CreateDocumentSerializer, DocumentSerializer,
    StoredFileSerializer, UploadFilesSerializer,
)


class OwnedFilesView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def get(self, request):
        files = permissions.accessible_files(request.user)
        data = StoredFileSerializer(files, many=True, context={'request': request}).data
        return Response({'files': data})

    def post(self, request):
        serializer = UploadFilesSerializer(data={'files': request.FILES.getlist('files')})
        serializer.is_valid(raise_exception=True)
        stored_files = serializer.save(owner=request.user)
        data = StoredFileSerializer(stored_files, many=True, context={'request': request}).data
        return Response({'files': data}, status=status.HTTP_201_CREATED)


class FileDownloadView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        stored_file = permissions.accessible_file(request.user, file_id)

        response = FileResponse(
            stored_file.file.open('rb'),
            as_attachment=True,
            filename=stored_file.original_name,
            content_type='application/octet-stream',
        )
        response['X-Content-Type-Options'] = 'nosniff'
        return response


class FilePreviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, file_id):
        stored_file = permissions.accessible_file(request.user, file_id)
        if stored_file.content_type not in {'image/png', 'image/jpeg', 'image/gif', 'image/webp'}:
            return Response({'detail': 'This file cannot be previewed.'}, status=status.HTTP_404_NOT_FOUND)

        response = FileResponse(stored_file.file.open('rb'), content_type=stored_file.content_type)
        response['X-Content-Type-Options'] = 'nosniff'
        response['Cross-Origin-Resource-Policy'] = 'same-origin'
        return response


class OwnedFileDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def delete(self, request, file_id):
        stored_file = permissions.owned_file(request.user, file_id)
        stored_file.file.delete(save=False)
        stored_file.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


class DocumentsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = CreateDocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        title = serializer.validated_data['title']
        stored_file = StoredFile.objects.create(
            owner=request.user,
            file=ContentFile(b'', name=title),
            original_name=title,
            content_type='text/plain',
            size=0,
        )
        document = Document.objects.create(file=stored_file, content=serializer.validated_data.get('content', ''))
        return Response(
            {
                'file': StoredFileSerializer(stored_file, context={'request': request}).data,
                'document': DocumentSerializer(document).data,
            },
            status=status.HTTP_201_CREATED,
        )


class DocumentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_document(self, request, file_id):
        stored_file = permissions.accessible_file(request.user, file_id)
        return get_object_or_404(Document, file=stored_file)

    def get(self, request, file_id):
        return Response(DocumentSerializer(self.get_document(request, file_id)).data)

    def patch(self, request, file_id):
        document = self.get_document(request, file_id)
        permissions.require_edit(document.file, request.user)

        serializer = DocumentSerializer(document, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
