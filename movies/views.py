import random, copy, json, urllib, numpy, pandas
from datetime import datetime
from django.urls import reverse
from django.shortcuts import render, redirect
from django.core.paginator import Paginator
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from .models import Movie
from .recommender import getRecommendations
from .network import NeuralNetwork

ratings = {}
ratings[0] = {}
updated = False
network = None
movie_vectors = []
scores = []

def get_movie_vector(movie):
    release_date = movie.info['release_date'].split('-')
    movie_info = [int(release_date[0]), int(release_date[1]), int(release_date[2]), int(movie.info['runtime']), int(movie.info['budget']), int(movie.info['revenue']), int(movie.info['popularity']), int(movie.info['vote_average'])]
    return movie_info

def recommend_movie(request):
    movies = Movie.objects.all()
    if len(movies) == 0:
        data = pandas.read_csv('data/movies.csv', sep=',')
        for i in range(int(data.size / 3)):
            row = data.iloc[i]
            print(row['movieId'], row['title'])
            movie = Movie(id=row['movieId'], name=row['title'])
            movie.save()
        data = pandas.read_csv('data/links.csv', sep=',')
        for i in range(int(data.size / 3)):
            row = data.iloc[i]
            print(row['movieId'], row['tmdbId'])
            movie = Movie.objects.get(id=row['movieId'])
            if pandas.isna(row['tmdbId']) == False:
                movie.tmdb_id = int(row['tmdbId'])
                movie.save()

    global updated

    if updated == False:
        print('Constructing ratings...')
        data = pandas.read_csv('data/ratings.csv', sep=',')
        for i in range(int(data.size / 4)):
            row = data.iloc[i]
            if row['userId'] in ratings:
                ratings[row['userId']][row['movieId']] = row['rating']
            else:
                ratings[row['userId']] = {}
        updated = True

    didRecommend = False
    movie_list = []
    movies = []
    if len(ratings[0]) != 0:
        recommendations = getRecommendations(ratings, 0)
        if len(recommendations) > 0:
            didRecommend = True
            recommendations = recommendations[0:5]
            for recommendation in recommendations:
                movie = Movie.objects.get(id=int(recommendation[1]))
                movie.rating = recommendation[0]
                movie_list.append(movie)
    for movie in movie_list:
        try:
            with urllib.request.urlopen('https://api.themoviedb.org/3/movie/' + str(movie.tmdb_id) + '?api_key=1b5adf76a72a13bad99b8fc0c68cb085') as url:
                api_data = json.loads(url.read().decode())
                movie.info = api_data
                movies.append(movie)
        except urllib.error.HTTPError:
            print(movie.tmdb_id)
    if network:
        for movie in movies:
            movie_vector = get_movie_vector(movie)
            net = copy.deepcopy(network)
            net.input = numpy.array([movie_vector])
            net.feedforward()
            movie.score = net.output[0][0]
    return render(request, 'recommend.html', {'didRecommend': didRecommend, 'movies': movies})

def random_movie(request):
    movie = random.choice(Movie.objects.all())
    with urllib.request.urlopen('https://api.themoviedb.org/3/movie/' + str(movie.tmdb_id) + '?api_key=1b5adf76a72a13bad99b8fc0c68cb085') as url:
        api_data = json.loads(url.read().decode())
        movie.info = api_data
    return render(request, 'random.html', {'movie': movie})

def rate(request, pk):
    global network, movie_vectors, scores
    ratings[0][pk] = int(request.POST['rating'])
    movie = Movie.objects.get(id=pk)
    with urllib.request.urlopen('https://api.themoviedb.org/3/movie/' + str(movie.tmdb_id) + '?api_key=1b5adf76a72a13bad99b8fc0c68cb085') as url:
        api_data = json.loads(url.read().decode())
        movie.info = api_data
    movie_vector = get_movie_vector(movie)
    movie_vectors.append(movie_vector)
    score = 0
    if ratings[0][pk] >= 3:
        score = 1
    scores.append([score])
    network = NeuralNetwork(numpy.array(movie_vectors), numpy.array(scores))
    for i in range(2000):
        network.feedforward()
        network.backprop()
    return redirect('recommend')

def search(request):
    query = request.GET['query']
    movies = Movie.objects.filter(name__icontains=query)
    for movie in movies:
        with urllib.request.urlopen('https://api.themoviedb.org/3/movie/' + str(movie.tmdb_id) + '?api_key=1b5adf76a72a13bad99b8fc0c68cb085') as url:
            api_data = json.loads(url.read().decode())
            movie.info = api_data
    return render(request, 'search.html', {'query': query, 'movies': movies})

def list_movies(request):
    movies_list = Movie.objects.all()
    paginator = Paginator(movies_list, 5)
    page = request.GET.get('page')
    movies = paginator.get_page(page)
    for movie in movies:
        with urllib.request.urlopen('https://api.themoviedb.org/3/movie/' + str(movie.tmdb_id) + '?api_key=1b5adf76a72a13bad99b8fc0c68cb085') as url:
            api_data = json.loads(url.read().decode())
            movie.info = api_data
    return render(request, 'movies/movie_list.html', {'movies': movies})

class MovieDetailView(DetailView):
    model = Movie

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.id in ratings[0]:
            context['rating'] = ratings[0][self.object.id]
        with urllib.request.urlopen('https://api.themoviedb.org/3/movie/' + str(self.object.tmdb_id) + '?api_key=1b5adf76a72a13bad99b8fc0c68cb085') as url:
            api_data = json.loads(url.read().decode())
            context['info'] = api_data
        with urllib.request.urlopen('https://api.themoviedb.org/3/movie/' + str(self.object.tmdb_id) + '/images?api_key=1b5adf76a72a13bad99b8fc0c68cb085') as url:
            api_data = json.loads(url.read().decode())
            context['images'] = api_data
        with urllib.request.urlopen('https://api.themoviedb.org/3/movie/' + str(self.object.tmdb_id) + '/videos?api_key=1b5adf76a72a13bad99b8fc0c68cb085') as url:
            api_data = json.loads(url.read().decode())
            context['videos'] = api_data
        return context
