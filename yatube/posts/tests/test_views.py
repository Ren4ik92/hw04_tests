import shutil
import tempfile
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse


from ..models import Post, Group
from django import forms

User = get_user_model()

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.user2 = User.objects.create_user(username='другой пользователь')
        cls.group = Group.objects.create(
            title='group',
            slug='slug',
            description='Тестовое описание'
        )

        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='тестовый текст поста',
            group=cls.group,
            image=cls.uploaded,
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Модуль shutil - библиотека Python с удобными инструментами
        # для управления файлами и директориями:
        # создание, удаление, копирование, перемещение, изменение папок и файлов
        # Метод shutil.rmtree удаляет директорию и всё её содержимое
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.author_client = Client()
        self.author_client.force_login(self.user)

    def test_urls_views_templates(self):
        """Тест на соотвецтвие адресов и шаблонов"""
        urls_templates = {
            'posts/index.html': '/',
            'posts/group_list.html': reverse('posts:postsname',
                                             kwargs={'slug': self.group.slug}),
            'posts/profile.html': reverse('posts:profile',
                                          kwargs={
                                              'username': self.user.username}),
            'posts/post_detail.html': reverse('posts:post_detail',
                                              kwargs={
                                                  'post_id': self.post.id}),
            'posts/create_post.html': reverse('posts:post_edit',
                                              kwargs={
                                                  'post_id': self.post.id}),
        }
        for template, address in urls_templates.items():
            with self.subTest(address=address):
                response = self.author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        post = response.context['page_obj'][0]
        self.assertEqual(post, self.post)
        self.assertEqual(self.post.image, 'posts/small.gif')

    def test_posts_list_page_show_correct_context(self):
        """Шаблон posts_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:postsname', kwargs={'slug': self.group.slug}))
        post = response.context['page_obj'][0]
        group = response.context['group']
        post_image = post.image
        self.assertEqual(post, self.post)
        self.assertEqual(group, self.group)
        self.assertEqual(post_image, 'posts/small.gif')

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        post = response.context['page_obj'][0]
        post_image = post.image
        self.assertEqual(post, self.post)
        self.assertEqual(response.context['author'], self.post.author)
        self.assertEqual(post_image, 'posts/small.gif')

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        post = response.context['post']
        post_image = post.image
        self.assertEqual(post, self.post)
        self.assertEqual(post_image, 'posts/small.gif')

    def test_post_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.author_client.get(reverse('posts:post_create'))
        for field, expected in self.form_fields.items():
            with self.subTest(field=field):
                form_field = response.context['form'].fields[field]
                self.assertIsInstance(form_field, expected)

    def test_post_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.author_client.get(
            reverse('posts:post_edit', kwargs={'post_id': self.post.id}))
        post = Post.objects.get(pk=self.post.id)
        context_form = response.context['form'].instance
        context_author = response.context.get('user')
        for field, expected in self.form_fields.items():
            with self.subTest(field=field):
                form_field = response.context['form'].fields[field]
                self.assertIsInstance(form_field, expected)
        self.assertTrue(response.context['is_edit'])
        self.assertEqual(context_form, post)
        self.assertEqual(context_author, post.author)
        self.assertEqual(self.post.image, 'posts/small.gif')

    def test_post_not_another_group(self):
        """Созданный пост не попал в чужую группу"""
        another_group = Group.objects.create(
            title='Группа2',
            slug='test-another-slug',
            description='Тест сообщение группы2',
        )
        response = self.authorized_client.get(
            reverse('posts:postsname', kwargs={'slug': another_group.slug})
        )
        self.assertEqual(len(response.context['page_obj']), 0)


class PaginatorTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug='test_slug',
            description='Тестовое описание',
        )
        Post.objects.bulk_create(
            Post(text=f'Post {i}', author=cls.user, group=cls.group)
            for i in range(13))
        cls.authorized_client = Client()
        cls.authorized_client.force_login(cls.user)

    def test_first_page_index(self):
        """Index на первой странице должно быть 10 постов"""
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_page_index(self):
        """Index на второй странице должно быть 3 поста"""
        response = (self.authorized_client.get(
            reverse('posts:index') + '?page=2'))
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_group_list(self):
        """Group_list На первой странице должно быть 10 постов"""
        response = (self.authorized_client.get(
            reverse('posts:postsname',
                    kwargs={'slug': self.group.slug})))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_group_list(self):
        """Group_list второй странице должно быть 3 поста"""
        response = (self.authorized_client.get(
            reverse('posts:postsname',
                    kwargs={'slug': self.group.slug}) + '?page=2'))
        self.assertEqual(len(response.context['page_obj']), 3)

    def test_first_profile(self):
        """Profile На первой странице должно быть 10 постов"""
        response = (self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user.username})))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_profile(self):
        """Profile На второй странице должно быть 3 поста"""
        response = (self.authorized_client.get(
            reverse('posts:profile',
                    kwargs={'username': self.user.username}) + '?page=2'))
        self.assertEqual(len(response.context['page_obj']), 3)
