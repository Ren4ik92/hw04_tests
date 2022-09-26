from django.shortcuts import render, get_object_or_404, redirect
from .models import Post, Group, User
from .forms import PostForm
from django.contrib.auth.decorators import login_required
from .units import paginator_posts, MESSAGE_N


def index(request):
    template = 'posts/index.html'
    post_list = Post.objects.all().order_by('-pub_date')
    context = {
        'page_obj': paginator_posts(post_list, MESSAGE_N, request),
        'post_list': post_list,
    }
    return render(request, template, context)


def group_posts(request, slug):
    group = get_object_or_404(Group, slug=slug)
    template = 'posts/group_list.html'
    post_list = Post.objects.filter(group=group).order_by('-pub_date')
    context = {
        'group': group,
        'page_obj': paginator_posts(post_list, MESSAGE_N, request)
    }
    return render(request, template, context)


def profile(request, username):
    author = get_object_or_404(User, username=username)
    user_post_list = author.posts.select_related('author').order_by(
        '-pub_date')
    context = {
        'page_obj': paginator_posts(user_post_list, MESSAGE_N, request),
        'author': author

    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id, ):
    post = get_object_or_404(Post, pk=post_id)
    context = {
        'post': post,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('posts:profile', post.author)
        return render(request, 'posts/create_post.html', {'form': form})
    form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    post = Post.objects.get(pk=post_id)
    if request.user != post.author:
        return redirect('posts:post_detail', post_id=post_id)
    form = PostForm(request.POST or None, instance=post)
    if form.is_valid():
        form.save()
        return redirect('posts:post_detail', post_id,)
    return render(request, 'posts/create_post.html',
                  {'form': form, 'is_edit': True},)
