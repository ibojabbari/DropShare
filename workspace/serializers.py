from pathlib import Path

from django.conf import settings
from django.urls import reverse
from rest_framework import serializers

from permissions import services as permissions

from .models import Document, StoredFile

SAFE_IMAGE_TYPES = {
    b'\x89PNG\r\n\x1a\n': 'image/png',
    b'GIF87a': 'image/gif',
    b'GIF89a': 'image/gif',
    b'\xff\xd8\xff': 'image/jpeg',
}

# Files in these formats either execute code themselves or are commonly used to
# launch code on a user's device. DropShare is a sharing app, not a software-
# distribution service, so it rejects them before storing anything.
BLOCKED_UPLOAD_EXTENSIONS = {
    '.apk', '.appimage', '.bat', '.cmd', '.com', '.cpl', '.dll', '.dmg',
    '.exe', '.hta', '.jar', '.js', '.jse', '.lnk', '.msi', '.msix',
    '.msixbundle', '.msp', '.mst', '.pif', '.ps1', '.psd1', '.psm1', '.py',
    '.pyc', '.reg', '.scr', '.sh', '.svg', '.svgz', '.vbe', '.vbs', '.wsf',
    '.wsh',
}

EXECUTABLE_SIGNATURES = (
    b'MZ',              # Windows Portable Executable
    b'\x7fELF',          # Linux executable
    b'\xfe\xed\xfa\xce',  # 32-bit Mach-O executable
    b'\xfe\xed\xfa\xcf',  # 64-bit Mach-O executable
    b'\xce\xfa\xed\xfe',  # 32-bit Mach-O executable, little-endian
    b'\xcf\xfa\xed\xfe',  # 64-bit Mach-O executable, little-endian
)

def detect_raster_image_type(uploaded_file):
    """Identify only simple raster formats that are safe to render in an img element."""
    header = uploaded_file.read(16)
    uploaded_file.seek(0)

    for signature, content_type in SAFE_IMAGE_TYPES.items():
        if header.startswith(signature):
            return content_type
    if header.startswith(b'RIFF') and header[8:12] == b'WEBP':
        return 'image/webp'
    return ''


def looks_like_an_executable(uploaded_file):
    """Reject executable content even when the filename has been disguised."""
    header = uploaded_file.read(4)
    uploaded_file.seek(0)
    return any(header.startswith(signature) for signature in EXECUTABLE_SIGNATURES)


class StoredFileSerializer(serializers.ModelSerializer):
    download_url = serializers.SerializerMethodField()
    preview_url = serializers.SerializerMethodField()
    owner = serializers.CharField(source='owner.username', read_only=True)
    is_document = serializers.SerializerMethodField()
    access = serializers.SerializerMethodField()

    class Meta:
        model = StoredFile
        fields = [
            'id', 'original_name', 'size', 'created_at', 'download_url', 'preview_url', 'owner', 'is_document', 'access',
        ]

    def get_download_url(self, stored_file):
        return reverse('workspace:file-download', kwargs={'file_id': stored_file.pk})

    def get_preview_url(self, stored_file):
        if stored_file.content_type in SAFE_IMAGE_TYPES.values() or stored_file.content_type == 'image/jpeg' or stored_file.content_type == 'image/webp':
            return reverse('workspace:file-preview', kwargs={'file_id': stored_file.pk})
        return None

    def get_is_document(self, stored_file):
        return hasattr(stored_file, 'document')

    def get_access(self, stored_file):
        return permissions.file_access(stored_file, self.context['request'].user)


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['content', 'updated_at']


class CreateDocumentSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=251)
    content = serializers.CharField(required=False, allow_blank=True)

    def validate_title(self, title):
        title = Path(title).name.strip()
        if not title:
            raise serializers.ValidationError('Choose a document title.')
        if not title.lower().endswith('.txt'):
            title = f'{title}.txt'
        return title


class UploadFilesSerializer(serializers.Serializer):
    files = serializers.ListField(
        child=serializers.FileField(),
        allow_empty=False,
        write_only=True,
    )

    def validate_files(self, uploaded_files):
        total_size = sum(uploaded_file.size for uploaded_file in uploaded_files)
        if total_size > settings.MAX_BATCH_UPLOAD_SIZE:
            raise serializers.ValidationError(
                f'The total upload must be {settings.MAX_BATCH_UPLOAD_SIZE // (1024 * 1024)} MB or smaller.'
            )

        for uploaded_file in uploaded_files:
            if uploaded_file.size > settings.MAX_UPLOAD_SIZE:
                raise serializers.ValidationError(
                    f'Each file must be {settings.MAX_UPLOAD_SIZE // (1024 * 1024)} MB or smaller.'
                )
            filename = Path(uploaded_file.name).name
            if not filename:
                raise serializers.ValidationError('Choose files with valid names.')
            if Path(filename).suffix.lower() in BLOCKED_UPLOAD_EXTENSIONS:
                raise serializers.ValidationError(
                    f'{filename} cannot be uploaded because executable, script, and SVG files are not supported.'
                )
            if looks_like_an_executable(uploaded_file):
                raise serializers.ValidationError(
                    f'{filename} cannot be uploaded because it contains executable file content.'
                )

        return uploaded_files

    def create(self, validated_data):
        owner = validated_data['owner']
        return [
            StoredFile.objects.create(
                owner=owner,
                file=uploaded_file,
                original_name=Path(uploaded_file.name).name[:255],
                content_type=detect_raster_image_type(uploaded_file),
                size=uploaded_file.size,
            )
            for uploaded_file in validated_data['files']
        ]
