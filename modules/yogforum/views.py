from django.shortcuts import render, redirect, get_object_or_404
from modules.main.models import Forum, ForumReply
from django.http import JsonResponse
from django.http import HttpRequest, HttpResponse
from django.http import HttpResponseBadRequest
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from modules.yogforum.forms import AddForm, AddReplyForm, EditPostForm

@login_required
def like_reply(request, id):
    reply = get_object_or_404(ForumReply, id=id)
    reply.like += 1  # Update like count (adjust logic as per your model's structure)
    reply.save()
    return JsonResponse({'success': True, 'total_likes': reply.like})

@login_required
def dislike_reply(request, id):
    reply = get_object_or_404(ForumReply, id=id)
    reply.dislike += 1  # Update dislike count (adjust logic as per your model's structure)
    reply.save()
    return JsonResponse({'success': True, 'total_dislikes': reply.dislike})

@login_required
def like_post(request, id):
    reply = get_object_or_404(Forum, id=id)
    reply.like += 1  # Update like count (adjust logic as per your model's structure)
    reply.save()
    return JsonResponse({'success': True, 'total_likes': reply.like})

@login_required
def dislike_post(request, id):
    reply = get_object_or_404(Forum, id=id)
    reply.dislike += 1  # Update dislike count (adjust logic as per your model's structure)
    reply.save()
    return JsonResponse({'success': True, 'total_dislikes': reply.dislike})

def viewforum(request, post_id):
    forum_post = get_object_or_404(Forum, id=post_id)
    replies = ForumReply.objects.filter(forum=forum_post)
    return render(request, 'yogforum/viewforum.html', {'forum_post': forum_post, 'replies': replies})

def main(request):
    # Ambil semua post
    forum_posts = Forum.objects.all().order_by('-created_at')
    
    context = {
        'forum_posts': forum_posts,
        'show_navbar': True,
        'show_footer': True
    }
    return render(request, 'yogforum.html', context)

def add_post(request):
    if request.method == 'POST':
        form = AddForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user.userprofile  # assuming user has a related profile
            post.save()
            return redirect('yogforum:main')  # redirect to forum main page after adding post
    else:
        form = AddForm()
    
    return render(request, 'components/new_post_modal.html', {'form': form})

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Forum, id=post_id, user=request.user.userprofile)
    post.delete()
    return redirect('yogforum:main')

@login_required
def delete_reply(request, reply_id):
    reply = get_object_or_404(ForumReply, id=reply_id, user=request.user.userprofile)
    reply.delete()
    return redirect('yogforum:viewforum', post_id=reply.forum.id)

def viewforum(request, post_id):
    # Cari post berdasarkan post_id
    forum_post = get_object_or_404(Forum, id=post_id)
    
    # Ambil semua reply yang terkait dengan post ini
    replies = ForumReply.objects.filter(forum=forum_post, reply_to=None).order_by('created_at')

    # Check if user is replying to a specific reply
    reply_id = request.GET.get('reply_to', None)
    reply = None
    if reply_id:
        reply = get_object_or_404(ForumReply, id=reply_id)

    context = {
        'forum_post': forum_post,
        'replies': replies,
        'reply': reply,  # Send the specific reply to the template if replying to a reply
        'show_navbar': True,
        'show_footer': True
    }
    return render(request, 'viewforum.html', context)

@login_required
def add_reply(request, post_id):
    try:
        forum_post = Forum.objects.get(id=post_id)
        forum_reply = None
    except Forum.DoesNotExist:
        forum_reply = get_object_or_404(ForumReply, id=post_id)
        forum_post = forum_reply.forum

    reply_to_id = request.POST.get('reply_to', None)

    if request.method == 'POST':
        content = request.POST.get('content')
        if not content:
            messages.error(request, "Content cannot be empty.")
            return redirect('yogforum:viewforum', post_id=forum_post.id)

        if reply_to_id:
            reply_to = get_object_or_404(ForumReply, id=reply_to_id)
            
            # Check reply depth before creating a new reply
            if get_reply_depth(reply_to) >= 2:
                messages.warning(request, "This post has reached the maximum number of replies.")
                return redirect('yogforum:view_reply_as_post', reply_id=forum_reply.id if forum_reply else forum_post.id)
            
            # Create the reply if depth is within the allowed limit
            ForumReply.objects.create(
                user=request.user.userprofile,
                forum=forum_post,
                content=content,
                reply_to=reply_to
            )
            messages.success(request, "Reply added successfully!")
        else:
            ForumReply.objects.create(
                user=request.user.userprofile,
                forum=forum_post,
                content=content,
                reply_to=forum_reply
            )
            messages.success(request, "Reply added successfully!")

        if forum_reply:
            return redirect('yogforum:view_reply_as_post', reply_id=forum_reply.id)
        else:
            return redirect('yogforum:viewforum', post_id=forum_post.id)

    return redirect('yogforum:viewforum', post_id=forum_post.id)

def get_reply_depth(reply):
    depth = 0
    while reply.reply_to is not None:
        reply = reply.reply_to
        depth += 1
    return depth

def view_reply_as_post(request, reply_id):
    # Get the reply by id
    reply_as_post = get_object_or_404(ForumReply, id=reply_id)
    
    # Get replies to this "reply" (nested replies)
    replies = ForumReply.objects.filter(reply_to=reply_as_post)
    
    context = {
        'forum_post': reply_as_post,  # treat reply as post
        'replies': replies,           # replies to the reply
        'show_navbar': True,
        'show_footer': True
    }
    
    return render(request, 'components/view_reply_as_post.html', context)

@login_required
def edit_post(request, post_id):
    post_object = None
    
    # Try to get the Forum post first
    try:
        post_object = Forum.objects.get(id=post_id, user=request.user.userprofile)
    except Forum.DoesNotExist:
        # If not found, try finding a reply instead
        post_object = get_object_or_404(ForumReply, id=post_id, user=request.user.userprofile)

    if request.method == 'POST':
        form = EditPostForm(request.POST, instance=post_object)
        if form.is_valid():
            form.save()
            if isinstance(post_object, Forum):
                return redirect('yogforum:viewforum', post_id=post_object.id)
            else:
                return redirect('yogforum:view_reply_as_post', reply_id=post_object.id)
    else:
        form = EditPostForm(instance=post_object)
    
    return render(request, 'components/edit_modal.html', {
        'form': form,
        'object': post_object,
        'modal_id': f"edit-modal-{post_id}"
    })
