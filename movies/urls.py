from django.urls import path
from movies import views

urlpatterns = [
    path('', views.list_movies, name='list'),
    path('movie/<int:pk>/', views.MovieDetailView.as_view(), name='detail'),
    path('movie/<int:pk>/rate/', views.rate, name='rate'),
    path('search/', views.search, name='search'),
    path('recommend/', views.recommend_movie, name='recommend'),
    path('random/', views.random_movie, name='random'),
]
