from rest_framework.exceptions import ValidationError


def validate_image(file):
    if not file.content_type.startswith("image"):
        raise ValidationError("Invalid file type")
    if file.size > 5 * 1024 * 1024:
        raise ValidationError("Image maximun size 5 MB")