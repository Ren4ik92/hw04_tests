from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from ..models import Post, Group
from django import forms

User = get_user_model()


class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='group',
            slug='slug',
            description='Тестовое описание'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='тестовый текст поста',
            group=cls.group,
        )
        cls.form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }

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
                                          kwargs=
                                          {'username': self.user.username}),
            'posts/post_detail.html': reverse('posts:post_detail',
                                              kwargs={
                                                  'post_id': self.post.id}),
            'posts/create_post.html': reverse('posts:post_edit',
                                              kwargs={
                                                  'post_id': self.post.id}),
            'posts/create_post.html': reverse('posts:post_create'),
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

    def test_posts_list_page_show_correct_context(self):
        """Шаблон posts_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:postsname', kwargs={'slug': self.group.slug}))
        post = response.context['page_obj'][0]
        group = response.context['group']
        self.assertEqual(post, self.post)
        self.assertEqual(group, self.group)

    def test_profile_page_show_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:profile', kwargs={'username': self.user.username}))
        post = response.context['page_obj'][0]
        self.assertEqual(post, self.post)
        self.assertEqual(response.context['author'], self.post.author)

    def test_post_detail_page_show_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse(
            'posts:post_detail', kwargs={'post_id': self.post.id}))
        post = response.context['post']
        self.assertEqual(post, self.post)

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
        for i in range(0, 13):
            cls.post = Post.objects.create(
                author=cls.user,
                group=cls.group,
                text='Тестовый текст',
                pub_date='22.09.2022',
            )
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
