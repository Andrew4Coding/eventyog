from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
import uuid

class UserRoles(models.TextChoices):
    ADMIN='AD', 'Admin',
    USER='US', 'User',
    
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=200)
    email = models.EmailField()
    bio = models.TextField()
    profile_picture = CloudinaryField('image', null=True, default=None, blank=True)
    categories = models.CharField(max_length=200, null=True, blank=True)
    
    registeredEvent = models.ManyToManyField('Event', blank=True)
    boughtMerch = models.ManyToManyField('Merchandise', blank=True)
    friends = models.ManyToManyField('UserProfile', blank=True)
    
    wallet = models.DecimalField(max_digits=10, decimal_places=2, default=1000000)
    
    role = models.CharField(
        choices=UserRoles.choices,
        default=UserRoles.USER,
        max_length=2
    )
    
    def __str__(self):
        return self.user.username

class MerchCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    merchandise = models.ForeignKey('Merchandise', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def totalPrice(self):
        return self.merchandise.price * self.quantity

class EventCart(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ticket = models.ForeignKey('TicketPrice', on_delete=models.CASCADE)
    quantity = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def totalPrice(self):
        return self.ticket.price * self.quantity

# Class for Event Category
class EventCategory(models.TextChoices):
    OLAHRAGA='OL', 'Olahraga',
    SENI='SN', 'Seni',
    MUSIK='MS', 'Musik',
    COSPLAY='CP', 'Cosplay',
    LINGKUNGAN='LG', 'Lingkungan',
    VOLUNTEER='VL', 'Volunteer',
    LAINNYA='LN', 'Lainnya'

class TicketPrice(models.Model):
    event = models.ForeignKey('Event', on_delete=models.CASCADE, related_name='ticketPrice')
    name = models.CharField(max_length=200)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def isFree(self):
        return self.price == 0

class Rating(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    rated_event = models.ForeignKey('Event', on_delete=models.CASCADE)
    rating = models.IntegerField(max)
    review = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class Event(models.Model):
    uuid = models.UUIDField(primary_key=True, editable=False, default=uuid.uuid4)
    title = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    category = models.CharField(
        choices=EventCategory.choices,
        default=EventCategory.LAINNYA,
        max_length=2
    )
    
    start_time = models.DateTimeField()
    end_time = models.DateTimeField(null=True, blank=True)
    
    location = models.CharField(max_length=200, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    merch = models.ManyToManyField('Merchandise', blank=True)
    
    user_rating = models.ManyToManyField(Rating, blank=True)
    image_urls = models.JSONField(null=True, blank=True)
    
class Merchandise(models.Model):
    image_url = models.URLField()
    name = models.CharField(max_length=200)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
class Forum(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    like = models.ManyToManyField(UserProfile, related_name='forum_like', blank=True)
    dislike = models.ManyToManyField(UserProfile, related_name='forum_dislike', blank=True)
    
    def __str__(self):
        return self.title
    
    def totalLike(self):
        return self.like.count()

    def totalDislike(self):
        return self.dislike.count()
    
class ForumReply(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    forum = models.ForeignKey(Forum, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reply_to = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True)
    
    like = models.ManyToManyField(UserProfile, related_name='forum_reply_like', blank=True)
    dislike = models.ManyToManyField(UserProfile, related_name='forum_reply_dislike', blank=True)
    
    def __str__(self):
        return self.content

        
    def totalLike(self):
        return self.like.count()

    def totalDislike(self):
        return self.dislike.count()