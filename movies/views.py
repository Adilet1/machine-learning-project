import random, json, urllib, numpy, pandas
from django.urls import reverse
from django.shortcuts import render, redirect
from django.views.generic.list import ListView
from django.views.generic.detail import DetailView
from .models import Movie
from .recommender import getRecommendations

ratings = {}
ratings[0] = {}
updated = False

# def sigmoid(x):
#     return 1.0/(1+ np.exp(-x))

# def sigmoid_derivative(x):
#     return x * (1.0 - x)

# class NeuralNetwork:
#     def __init__(self, x, y):
#         self.input      = x
#         self.weights1   = np.random.rand(self.input.shape[1],4) 
#         self.weights2   = np.random.rand(4,1)                 
#         self.y          = y
#         self.output     = np.zeros(self.y.shape)

#     def feedforward(self):
#         self.layer1 = sigmoid(np.dot(self.input, self.weights1))
#         self.output = sigmoid(np.dot(self.layer1, self.weights2))

#     def backprop(self):
#         d_weights2 = np.dot(self.layer1.T, (2*(self.y - self.output) * sigmoid_derivative(self.output)))
#         d_weights1 = np.dot(self.input.T,  (np.dot(2*(self.y - self.output) * sigmoid_derivative(self.output), self.weights2.T) * sigmoid_derivative(self.layer1)))

#         self.weights1 += d_weights1
#         self.weights2 += d_weights2

def recommend_movie(request):
    # data = pandas.read_csv('data/movies.csv', sep=',')
    # for i in range(int(data.size / 3)):
    #     row = data.iloc[i]
    #     print(row['movieId'], row['title'])
    #     movie = Movie(id=row['movieId'], name=row['title'])
    #     movie.save()
    # data = pandas.read_csv('data/links.csv', sep=',')
    # for i in range(int(data.size / 3)):
    #     row = data.iloc[i]
    #     print(row['movieId'], row['tmdbId'])
    #     movie = Movie.objects.get(id=row['movieId'])
    #     if pandas.isna(row['tmdbId']) == False:
    #         movie.tmdb_id = int(row['tmdbId'])
    #         movie.save()
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
    if len(ratings[0]) != 0:
        recommendation = getRecommendations(ratings, 0)
        if len(recommendation) > 0:
            movie = Movie.objects.get(id=recommendation[0][1])
            didRecommend = True
    if didRecommend == False:
        movie = random.choice(Movie.objects.all())
    with urllib.request.urlopen('https://api.themoviedb.org/3/movie/' + str(movie.tmdb_id) + '?api_key=1b5adf76a72a13bad99b8fc0c68cb085') as url:
        api_data = json.loads(url.read().decode())
        movie.info = api_data
    return render(request, 'recommend.html', {'didRecommend': didRecommend, 'movie': movie})

def random_movie(request):
    movie = random.choice(Movie.objects.all())
    with urllib.request.urlopen('https://api.themoviedb.org/3/movie/' + str(movie.tmdb_id) + '?api_key=1b5adf76a72a13bad99b8fc0c68cb085') as url:
        api_data = json.loads(url.read().decode())
        movie.info = api_data
    return render(request, 'random.html', {'movie': movie})

def rate(request, pk):
    ratings[0][pk] = int(request.POST['rating'])
    return redirect('recommend')

def search(request):
    query = request.GET['query']
    movies = Movie.objects.filter(name__icontains=query)
    for movie in movies:
        with urllib.request.urlopen('https://api.themoviedb.org/3/movie/' + str(movie.tmdb_id) + '?api_key=1b5adf76a72a13bad99b8fc0c68cb085') as url:
            api_data = json.loads(url.read().decode())
            movie.info = api_data
    return render(request, 'search.html', {'query': query, 'movies': movies})

class MovieListView(ListView):
    model = Movie
    paginate_by = 10
    context_object_name = 'movies'

    def get_queryset(self):
        movies = Movie.objects.all()
        for movie in movies:
            with urllib.request.urlopen('https://api.themoviedb.org/3/movie/' + str(movie.tmdb_id) + '?api_key=1b5adf76a72a13bad99b8fc0c68cb085') as url:
                api_data = json.loads(url.read().decode())
                movie.info = api_data
        return movies

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
