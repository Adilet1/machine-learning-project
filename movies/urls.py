from django.urls import path
from movies import views

urlpatterns = [
    path('', views.done, name='done'),
    path('movie/<int:pk>', views.MovieDetailView.as_view(), name='detail'),
    path('movie/<int:pk>/rate', views.rate, name='rate'),
]
