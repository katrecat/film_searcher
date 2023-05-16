from .forms import NewUserForm
from .models import Movie, Genre, Rating
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.template import loader
from django.views import generic


def index(request: HttpRequest):
    movies = Movie.objects.order_by('-title')
    template = loader.get_template('userview/home.html')
    context = {'movies': movies}
    return HttpResponse(template.render(context, request))


def view_movie(request: HttpRequest, movie_id):
    response = 'you are looking at the movie with an id %s'
    return HttpResponse(response % movie_id)


def view_genre(request: HttpRequest, genre_id):
    response = 'you are looking at the genre with an id %s'
    return HttpResponse(response % genre_id)


def movies_view(request: HttpRequest):
    movie_list = Movie.objects.order_by('-title')
    paginator = Paginator(movie_list, 3)  # Show n movies per page

    page_number = request.GET.get('page')
    movies = paginator.get_page(page_number)

    template = loader.get_template('userview/movies.html')
    context = {
        'movies': movies,
        'pagination': movies,
    }
    return HttpResponse(template.render(context, request))


def genres_view(request: HttpRequest):
    genre_list = Genre.objects.order_by('name')
    paginator = Paginator(genre_list, 3)  # Show n genres per page

    page_number = request.GET.get('page')
    genres = paginator.get_page(page_number)

    template = loader.get_template('userview/genres.html')
    context = {
        'genres': genres,
        'pagination': genres,
    }
    return HttpResponse(template.render(context, request))


def register_request(request):
    form = NewUserForm()
    if request.method == "POST":
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registration successful.")
            return redirect("/")
            info_msg = "Unsuccessful registration. Invalid information."
            messages.error(request, info_msg)
    return render(request=request, template_name="userview/register.html",
                  context={"register_form": form})


class IndexView(generic.ListView):
    template_name = 'userview/index.html'
    context_object_name = 'movies'

    def get_queryset(self):
        return Movie.objects.order_by('-title')


class MovieView(generic.DetailView):
    model = Movie
    template_name = 'userview/movies.html'


class GenreView(generic.DetailView):
    model = Genre
    template_name = 'userview/genres.html'


def user_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, 'Login successful.')
            return redirect('/')
        else:
            messages.error(request, 'Invalid username or password.')
    return render(request, 'userview/login.html')


def logout_request(request):
    logout(request)
    messages.success(request, 'Logout successful.')
    return redirect('/')


def ratings(request):
    if request.user.is_authenticated:
        if request.method == 'POST':
            movie_id = request.POST.get('movie')
            rating_value = request.POST.get('rating')

            try:
                movie = Movie.objects.get(id=movie_id)
                rating = Rating.objects.create(value=rating_value, movie=movie,
                                               user=request.user)
                rating.save()
            except Movie.DoesNotExist:
                # Handle the case where the movie does not exist
                pass

        movies = Movie.objects.all()
        ratings = Rating.objects.filter(user=request.user)
        return render(request, 'userview/ratings.html', {'movies': movies,
                                                         'ratings': ratings})
    else:
        return render(request, 'userview/ratings.html')
