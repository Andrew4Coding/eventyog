from datetime import datetime
import json
from django.contrib import messages
from django.shortcuts import get_object_or_404, render, redirect, reverse
from modules.yogevent.forms import EventForm
from django.http import HttpRequest, HttpResponse, HttpResponseRedirect, JsonResponse
from modules.main.models import *
from eventyog.decorators import check_user_profile
from django.core import serializers
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils.html import strip_tags
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.db.models import Avg
from django.shortcuts import redirect

@check_user_profile(is_redirect=True)
def main(request: HttpRequest) -> HttpResponse:
    user_profile = UserProfile.objects.get(user=request.user)
    events = Event.objects.all()

    query = request.GET.get('q')
    category = request.GET.get('category')

    if query:
        events = events.filter(Q(title__icontains=query))

    if category:
        events = events.filter(category=category)
        
    context = {
        'user': request.user,
        'user_profile': user_profile,
        'show_navbar': True,
        'show_footer': True,
        'is_admin': user_profile.role == 'AD' if user_profile else False,
        'events': events,
    }

    return render(request, 'yogevent.html', context)

def show_event_xml(request):    
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile:
        events = Event.objects.filter(userprofile=user_profile)
    else:
        events = Event.objects.all()

    return HttpResponse(serializers.serialize("xml", events), content_type="application/json") 

def show_event_json(request):
    user_profile = UserProfile.objects.get(user=request.user)
    if user_profile:
        events = Event.objects.filter(userprofile=user_profile)
    else:
        events = Event.objects.all()

    return HttpResponse(serializers.serialize("json", events), content_type="application/json") 

def show_xml_event_by_id(request, id):
    data = Event.objects.filter(pk=id)  # Cari event berdasarkan primary key
    return HttpResponse(serializers.serialize("xml", data), content_type="application/xml")

def show_json_event_by_id(request, id):
    data = Event.objects.filter(pk=id)
    return HttpResponse(serializers.serialize("json", data), content_type="application/json")

@check_user_profile(is_redirect=True)
@csrf_exempt
@require_POST
def create_event_entry_ajax(request):
    title = strip_tags(request.POST.get('title'))
    description = strip_tags(request.POST.get('description'))
    category = request.POST.get('category')
    start_time = request.POST.get('start_time')
    end_time = request.POST.get('end_time', '')
    location = strip_tags(request.POST.get('location'))
    image_url = strip_tags(request.POST.get('image_url'))

    end_time = end_time if end_time != "" else None

    if title == "" or description == "" or location == "" or category =="":
        return JsonResponse({'status': False, 'message': 'Invalid input'})

    if end_time and start_time >= end_time:
        return JsonResponse({'status': False, 'message': 'Acara berakhir sebelum dimulai.'})

    try:
        new_event = Event(
            title=title,
            description=description,
            category=category,
            start_time=start_time,
            end_time=end_time,
            location=location,
            image_urls=[image_url]
        )
        new_event.save()
        return JsonResponse({'status': True, 'message': 'Event created successfully.'})
    
    except Exception as e:
        return JsonResponse({'status': False, 'message': 'Error creating event.'})


def detail_event(request, uuid):
    event = get_object_or_404(Event, uuid=uuid)
    user_profile = UserProfile.objects.get(user=request.user)
    ratings = Rating.objects.filter(rated_event=event)
    average_rating = ratings.aggregate(Avg('rating'))['rating__avg'] or 0

    context = {
        'user': request.user,
        'user_profile': user_profile,
        'image_url': user_profile.profile_picture,
        'show_navbar': True,
        'show_footer': True,
        'is_admin': user_profile.role == 'AD' if user_profile else False,
        'event': event,
        'average_rating': round(average_rating, 1),
    }
    return render(request, 'detail_event.html', context)

def delete_event(request, uuid):
    event = get_object_or_404(Event, uuid=uuid)
    event.delete()
    return HttpResponseRedirect(reverse('yogevent:main'))

def edit_event(request, uuid):

    event = get_object_or_404(Event, uuid=uuid) 
    user_profile = UserProfile.objects.get(user=request.user)
    

    if request.method == "POST":  
        event.title = strip_tags(request.POST.get('title'))
        event.description = strip_tags(request.POST.get('description'))
        event.category = request.POST.get('category')
        event.start_time = request.POST.get('start_time')
        event.end_time = request.POST.get('end_time', '')
        event.location = strip_tags(request.POST.get('location'))
        event.image_urls = [request.POST.get('image_url')]
        event.end_time = event.end_time if event.end_time != "" else None


        if event.image_urls == [""]:
            event.image_urls = []

        if event.title == "" or event.category == "":
            return render(request, "error.html", {
                "message":"judul atau kategori tidak boleh kosong",
                'user': request.user,
                'user_profile': user_profile,
                'image_url': user_profile.profile_picture,
                'show_navbar': True,
                'show_footer': True,
                'is_admin': user_profile.role == 'AD' if user_profile else False,
                })

        if event.end_time and event.start_time >= event.end_time:
            return render(request, "error.html", {
                "message":"Acara berakhir sebelum dimulai.",
                'user': request.user,
                'user_profile': user_profile,
                'image_url': user_profile.profile_picture,
                'show_navbar': True,
                'show_footer': True,
                'is_admin': user_profile.role == 'AD' if user_profile else False,
                })
        
        event.save()
        return HttpResponseRedirect(reverse('yogevent:main'))
    
    context = {
        'user': request.user,
        'user_profile': user_profile,
        'show_navbar': True,
        'show_footer': True,
        'is_admin': user_profile.role == 'AD' if user_profile else False,
        'event': event,
    }

    return render(request, "edit_event.html", context)

@check_user_profile(is_redirect=True)
@require_POST
@csrf_exempt
def add_rating(request, event_id):
    event = get_object_or_404(Event, uuid=event_id)
    rating_value = request.POST.get('rating')
    review = request.POST.get('review', '')
    user_profile = getattr(request.user, 'userprofile', None)

    try:
        rating_value = int(rating_value)
    except ValueError:
        return JsonResponse({"status" : False, 'error': 'Invalid rating input'}, status=400)

    # Create and save the new rating
    new_rating = Rating(
        user=user_profile, 
        rated_event=event, 
        rating=rating_value, 
        review=review
    )
    new_rating.save()
    average_rating = Rating.objects.filter(rated_event=event).aggregate(Avg('rating'))['rating__avg']
    context = {
        'average_rating': round(average_rating, 1),
    }
    return JsonResponse({'status': True, 'message': 'Rating submitted successfully!', "data": context})

def create_rating_event(request, event_id): #Kemungkinan akan dihapus tapi keep dulu
    event = get_object_or_404(Event, uuid=event_id)
    average_rating = Rating.objects.filter(rated_event=event).aggregate(Avg('rating'))['rating__avg'] or 0
    user_profile = getattr(request.user, 'userprofile', None)

    return render(request, 'create_rating_event.html', {
        'user': request.user,
        'user_profile': user_profile,
        'show_navbar': True,
        'show_footer': True,
        'event': event,
        'average_rating': round(average_rating, 1),
    })

def get_rating_event(request, event_uuid):
    event = get_object_or_404(Event, uuid=event_uuid)
    average_rating = Rating.objects.filter(rated_event=event).aggregate(Avg('rating'))['rating__avg'] or 0
    user_profile = UserProfile.objects.get(user=request.user)

    context = {
        'user_name': user_profile.user.username, 
        'average_rating': round(average_rating, 1),
    }

    return JsonResponse({'status': True, 'message': 'Rating submitted successfully!', "data": context})

def load_event_ratings(request, event_id):
    event = get_object_or_404(Event, uuid=event_id)
    
    # Get all ratings for the event and calculate the average rating
    ratings = Rating.objects.filter(rated_event=event).values("rating", "review")
    average_rating = ratings.aggregate(Avg('rating'))['rating__avg'] or 0

    # Return the ratings data as JSON
    return JsonResponse({
        "average_rating": round(average_rating, 1),
        "ratings": list(ratings),
    })