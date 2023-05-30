from .forms import NewUserForm
from .models import Movie, Genre, Rating, Comment
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.template import loader
from django.views import generic
from urllib.parse import urlencode
from django.db.models import Avg


def index(request: HttpRequest):
    movies = Movie.objects.order_by('-title')
    template = loader.get_template('userview/home.html')
    context = {'movies': movies}
    return HttpResponse(template.render(context, request))


def create_movie(request: HttpRequest):
    template = loader.get_template('userview/create_movie.html')
    all_genres = Genre.objects.all()
    all_genres = sorted(all_genres, key=lambda x: x.name)

    if request.method == 'POST':
        title = request.POST.get('title')
        genres = request.POST.getlist('genres')
        if genres and title:
            try:
                movie = Movie.objects.get(title=title)
                return HttpResponse(template.render({"error":
                                                     "Movie already exists.",
                                                     "title": title,
                                                     "genres":
                                                     all_genres},
                                                    request))

            except Movie.DoesNotExist:
                movie = Movie.objects.create(title=title)
                for genre in genres:
                    movie.genres.add(Genre.objects.get(id=genre))
                movie.save()
                return redirect(f'/movie/{movie.id}')
    else:
        return HttpResponse(template.render({"error": "",
                                             "genres": all_genres},
                                            request))


def edit_movie(request: HttpRequest, movie_id):
    template = loader.get_template('userview/edit_movie.html')
    if request.method == 'POST':
        title = request.POST.get('title')
        genres = request.POST.getlist('genres')
        movie = Movie.objects.get(id=movie_id)
        # Verify that the genres are correct
        if genres and title:
            # Check if the movie already exists
            try:
                tmp_movie = Movie.objects.get(title=title)
                # If the movie already exists, check if it is the same movie
                if movie.id != tmp_movie.id:
                    error_msg = f"Movie '{title}' already exists."
                    return HttpResponse(
                            template.render({"error": error_msg,
                                             "movie": movie,
                                             "movie_id": movie_id,
                                             "genres": Genre.objects.all()},
                                            request))

            except Movie.DoesNotExist:
                pass
            movie.title = title
            movie.genres.clear()
            for genre in genres:
                movie.genres.add(Genre.objects.get(id=genre))
            movie.save()
            return redirect(f'/movie/{movie_id}')
    else:
        try:
            movie = Movie.objects.get(id=movie_id)
        except Movie.DoesNotExist:
            return HttpResponse(template.render({'movie': None,
                                                 'movie_id': movie_id},
                                                request))
        try:
            genres = Genre.objects.all()
        except Genre.DoesNotExist:
            genres = []
        return HttpResponse(template.render({'movie': movie,
                                             'movie_id': movie_id,
                                             'genres': genres}, request))


def view_movie(request: HttpRequest, movie_id):
    if request.method == 'POST':
        comment = request.POST.get('comment')
        movie = Movie.objects.get(id=movie_id)
        comment = Comment.objects.create(text=comment, movie=movie,
                                         user=request.user)
        comment.save()
        return redirect(f'/movie/{movie_id}')
    else:
        template = loader.get_template('userview/movie.html')
        try:
            movie = Movie.objects.get(id=movie_id)
        except Movie.DoesNotExist:
            return HttpResponse(template.render({'movie': None,
                                                 'movie_id': movie_id},
                                                request))
        context = {'movie': movie,
                   'movie_id': movie_id,
                   }
        comments = []

        try:
            average_rating = 0
            ratings = Rating.objects.filter(movie=movie)
            if ratings:
                for rating in ratings:
                    average_rating += rating.value
                average_rating /= len(ratings)
                average_rating = round(average_rating, 2)
                average_rating = f"{average_rating} / 10.0"
            else:
                average_rating = "No ratings yet."
        except Rating.DoesNotExist:
            average_rating = "No ratings yet."
        context['average_rating'] = average_rating

        # If user is authenticated, get their rating for the movie
        if request.user.is_authenticated:
            try:
                user_rating = 0
                user_ratings = Rating.objects.filter(movie=movie,
                                                     user=request.user)
                if user_ratings:
                    for rating in user_ratings:
                        user_rating += rating.value
                    user_rating /= len(user_ratings)
                    user_rating = f"{round(user_rating, 2)} / 10.0"
                else:
                    user_rating = "No rating yet."
            except Rating.DoesNotExist:
                user_rating = "No rating yet."
            context['user_rating'] = user_rating

        try:
            comments = Comment.objects.filter(movie=movie)
        except Comment.DoesNotExist:
            comments = []
        context['comments'] = comments

        return HttpResponse(template.render(context, request))


def view_genre(request: HttpRequest, genre_id):
    response = 'you are looking at the genre with an id %s'
    return HttpResponse(response % genre_id)

def movies_view(request):
    movies = Movie.objects.order_by('-title')

    title = request.GET.get('title')
    if title:
        movies = movies.filter(title__icontains=title)

    genre_ids = request.GET.getlist('genre')
    if genre_ids:
        movies = movies.filter(genres__id__in=genre_ids)

    average_rating = request.GET.get('average_rating')
    if average_rating:
        filtered_movies = []
        for movie in movies:
            try:
                ratings = Rating.objects.filter(movie=movie)
                if ratings:
                    average_rating_sum = sum(rating.value for rating in ratings)
                    average_rating_value = average_rating_sum / len(ratings)
                    if average_rating_value >= float(average_rating):
                        filtered_movies.append(movie)
            except Rating.DoesNotExist:
                pass
        movies = filtered_movies

    view = request.GET.get('view')
    if view == 'table':
        # Render grid view
        paginator = Paginator(movies, 3)  # Show n movies per page

        page_number = request.GET.get('page')
        movies = paginator.get_page(page_number)

        genres = Genre.objects.all()  #
    else:
        # Render list view with pagination
        paginator = Paginator(movies, 3)  # Show n movies per page

        page_number = request.GET.get('page')
        movies = paginator.get_page(page_number)

        genres = Genre.objects.all()  # Retrieve all genres from the database

        # Calculate average rating for each movie
        for movie in movies:
            try:
                ratings = Rating.objects.filter(movie=movie)
                if ratings:
                    average_rating_sum = sum(rating.value for rating in ratings)
                    average_rating_value = average_rating_sum / len(ratings)
                    average_rating = round(average_rating_value, 2)
                    average_rating = f"{average_rating}"
                else:
                    average_rating = "No ratings yet."
            except Rating.DoesNotExist:
                average_rating = "No ratings yet."
            movie.average_rating = average_rating

        # Preserve the filter parameters in the pagination links
        filter_params = request.GET.copy()
        if 'page' in filter_params:
            del filter_params['page']
        query_string = filter_params.urlencode()

        context = {
            'movies': movies,
            'genres': genres,
            'pagination': movies,
            'current_view': view,
            'query_string': query_string,
        }
        return render(request, 'userview/movies.html', context)


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
