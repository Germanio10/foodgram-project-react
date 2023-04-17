from django.db import models
from django.contrib.auth.models import AbstractUser

from .validators import validate_user


class User(AbstractUser):
    email = models.EmailField(max_length=254)
    username = models.CharField(max_length=150,
                                unique=True,
                                verbose_name='Логин',
                                validators=[validate_user])
    first_name = models.CharField(max_length=150,
                                  verbose_name='Имя',
                                  help_text='Введите имя')
    last_name = models.CharField(max_length=150,
                                 verbose_name='Фамилия',
                                 help_text='Введите фамилию')
    password = models.CharField(max_length=150,
                                verbose_name='Пароль')

    def __str__(self):
        return self.username

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class Subscribe(models.Model):
    user = models.ForeignKey(
        User,
        related_name='follower',
        on_delete=models.CASCADE
    )
    author = models.ForeignKey(
        User,
        related_name='following',
        on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(fields=['user', 'author'],
                                    name='unique_user_author')
        ]

    def __str__(self):
        return f'{self.user}, {self.author}'
