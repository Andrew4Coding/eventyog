from django.shortcuts import render
from django.http import HttpRequest, HttpResponse
from modules.main.models import MerchCart, EventCart, UserProfile, Event, Merchandise
from eventyog.decorators import check_user_profile
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db import transaction
import json

@check_user_profile(is_redirect=False)
def main(request: HttpRequest) -> HttpResponse:
    
    # Retrieve cart items for events and merchandise
    cart_events = EventCart.objects.filter(user=request.user)
    cart_merch = MerchCart.objects.filter(user=request.user)
    user_profile = UserProfile.objects.get(user=request.user)

# Get the events the user has registered for
    buyedE = user_profile.registeredEvent.all()

# Get the merchandise the user has bought
    buyedM = user_profile.boughtMerch.all()

# Print the bought events
    for event in buyedE:
        print(event.title)  # or any other field in the Event model

# Print the bought merchandise
    for merch in buyedM:
        print(merch.name)  # or any other field in the Merchandise model

    # Calculate cumulative total price
    priceEvent = 0
    priceCart = 0
    for i in cart_events:
        priceEvent += i.totalPrice()
    
    for i in cart_merch:
        priceCart += i.totalPrice()
    
    total_price = priceEvent + priceCart


    context = {
        'user': request.user,
        'user_profile': request.user_profile,
        'image_url': request.image_url,
        'show_navbar': True,
        'show_footer': True,
        'is_admin': request.is_admin,
        'cart_events': cart_events,        # Pass events cart items
        'cart_merch': cart_merch,          # Pass merchandise cart items
        'total_price': total_price,        # Pass cumulative total price
    }

    return render(request, 'cart.html', context)

@require_POST
@transaction.atomic
def checkout(request):
    user = request.user
    user_profile = UserProfile.objects.get(user=user)

    # Parse updated quantities from the request
    data = json.loads(request.body)
    updated_events = data.get('event', {})
    updated_merch = data.get('merch', {})

    # Retrieve all EventCart and MerchCart items for the user
    cart_events = EventCart.objects.filter(user=user)
    cart_merch = MerchCart.objects.filter(user=user)

    # Update EventCart quantities
    for event_cart in cart_events:
        event_id = str(event_cart.id)
        if event_id in updated_events:
            event_cart.quantity = updated_events[event_id]['quantity']
            event_cart.save()

    # Update MerchCart quantities
    for merch_cart in cart_merch:
        merch_id = str(merch_cart.id)
        if merch_id in updated_merch:
            merch_cart.quantity = updated_merch[merch_id]['quantity']
            merch_cart.save()

    # Check if the cart is empty after updates
    cart_events = EventCart.objects.filter(user=user, quantity__gt=0)
    cart_merch = MerchCart.objects.filter(user=user, quantity__gt=0)

    if not cart_events.exists() and not cart_merch.exists():
        return JsonResponse({'success': False, 'error': 'Your cart is empty.'})

    # Save the updated user profile
    user_profile.save()

    # Return success response
    return JsonResponse({'success': True})