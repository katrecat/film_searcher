from django.urls import path
from . import views

urlpatterns = [
    path("", views.index, name="home"),
    path('movies/', views.movies_view, name='movies'),
    path('genres/', views.genres_view, name='genres'),
    path("genre/<int:genre_id>", views.view_genre, name="index"),
    path("movie/<int:movie_id>", views.view_movie, name="index"),
    path("register/", views.register_request, name="register"),
    path("login/", views.user_login, name="login"),
    path('logout/', views.logout_request, name='logout'),
    path('ratings/', views.ratings, name='ratings'),
]
