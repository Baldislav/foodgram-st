from django.contrib.auth.models import AbstractUser
from django.db import models

from users.constants import MAX_EMAIL_LENGTH

class User(AbstractUser):
    email = models.EmailField(
        verbose_name='адрес электронной почты',
        unique=True,
        max_length=MAX_EMAIL_LENGTH,
    )
    avatar = models.ImageField(
        verbose_name='аватар',
        upload_to='users/avatars/',
        blank=True,
        null=True,
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ['username']

    def __str__(self):
        return self.username


class Follow(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик',
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор',
    )
    created_at = models.DateTimeField(
        verbose_name='Дата создания подписки',
        auto_now_add=True,
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'author'],
                name='unique_user_author_follow',
            ),
            models.CheckConstraint(
                check=~models.Q(user=models.F('author')),
                name='prevent_self_follow',
            ),
        ]

    def __str__(self):
        return f'{self.user.username} подписан на {self.author.username}'
