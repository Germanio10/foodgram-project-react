import re
from django.core.exceptions import ValidationError


def validate_user(value):
    if not re.fullmatch(r'[\w\@\.\+\-]+', value):
        raise ValidationError('Запрещено.')
    if value == 'me':
        raise ValidationError('Использование имени me запрещено.')