from django.contrib import admin
from .models import Rating, Genre, Movie

admin.site.register(Genre)
admin.site.register(Movie)
admin.site.register(Rating)