from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Group(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    description = models.TextField()

    def __str__(self) -> str:
        return self.title


class Post(models.Model):
    text = models.TextField(verbose_name='Текст поста',
                            help_text='Введите текст поста')
    pub_date = models.DateTimeField(auto_now_add=True,
                                    verbose_name='Дата публикации',
                                    )
    author = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="posts",
        verbose_name='Автор'
    )
    group = models.ForeignKey(
        Group,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="posts"
    )

    def __str__(self):
        return self.text

    group = models.ForeignKey(
        Group,
        related_name='posts',
        verbose_name='Группа',
        help_text='Группа, относительно поста',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,
    )

    class Meta:
        ordering = ['-pub_date']
        verbose_name = 'запись', 'Автор', 'пост'
        verbose_name_plural = 'записи', 'Авторы', 'посты'
