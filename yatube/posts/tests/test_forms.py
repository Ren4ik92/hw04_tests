from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post, Group, User
from ..forms import PostForm


class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.authorized_author = Client()
        cls.author = User.objects.create(username='TestAuthor')
        cls.authorized_author.force_login(cls.author)
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test-slug',
            description='Тестовое описание',
        )
        cls.group2 = Group.objects.create(
            title='Тестовая группа1',
            slug='test-slug1',
            description='Тестовое описание1',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            text='Тестовый пост',
        )
        cls.form = PostForm()

    def test_create_post(self):
        """Валидная форма создает запись в post."""
        post_count = Post.objects.count()
        old_posts = Post.objects.all().values_list('id', flat=True)
        form_data = {
            'text': 'Новый пост созданный через форму',
            'group': self.group.pk,
        }
        response = self.authorized_author.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        new_posts = Post.objects.exclude(
            id__contains=old_posts).values('text', 'group', 'author')
        self.assertRedirects(response, reverse('posts:profile', kwargs={
            'username': self.author}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertEqual(new_posts.count(), 1)
        self.assertEqual(new_posts[0]['text'], form_data['text'])
        self.assertEqual(new_posts[0]['group'], form_data['group'])
        self.assertEqual(new_posts[0]['author'], self.author.pk)

    def test_edit_post(self):
        """Валидная форма перезаписывает запись."""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Отредактированный текст',
            'group': self.group2.pk,
        }
        response = self.authorized_author.post(
            reverse('posts:post_edit', kwargs={
                'post_id': self.post.pk}),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse('posts:post_detail', kwargs={
            'post_id': self.post.pk}))
        self.assertEqual(Post.objects.count(), post_count)
        self.assertTrue(
            Post.objects.filter(
                text=form_data['text'],
                author=self.author,
                group=self.group2,
            ).exists()
        )
