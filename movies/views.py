from django.urls import reverse
from django.shortcuts import render, redirect
from django.db.models import Max
from django.views.generic.detail import DetailView
from .models import Movie

import math, random, pandas
from sklearn.model_selection import train_test_split

ratings = {}
ratings[0] = {}
refreshed = False

def done(request):
    print(ratings)
    movies = pandas.read_csv('movies.dat', sep='::', header=None)
    for i in range((int) (movies.size / 3)):
        movie = Movie(id=i, name=movies.iloc[i][1])
        movie.save()
    data = pandas.read_csv('ratings.dat', sep='::', header=None)
    d = train_test_split(data, train_size=0.01, test_size=0.99)
    for i in range(int(d[0].size / 4)):
        if d[0].iloc[i][0] in ratings:
            ratings[d[0].iloc[i][0]][d[0].iloc[i][1]] = d[0].iloc[i][2]
        else:
            ratings[d[0].iloc[i][0]] = {}

    def sim_pearson(prefs,p1,p2):
        si={}
        for item in prefs[p1]:
            if item in prefs[p2]: si[item]=1
        n=len(si)
        if n==0: return 0
        sum1=sum([prefs[p1][it] for it in si])
        sum2=sum([prefs[p2][it] for it in si])
        sum1Sq=sum([pow(prefs[p1][it],2) for it in si])
        sum2Sq=sum([pow(prefs[p2][it],2) for it in si])
        pSum=sum([prefs[p1][it]*prefs[p2][it] for it in si])
        num=pSum-(sum1*sum2/n)
        den=math.sqrt((sum1Sq-pow(sum1,2)/n)*(sum2Sq-pow(sum2,2)/n))
        if den==0: return 0
        r=num/den
        return r

    def topMatches(prefs,person,n=5,similarity=sim_pearson):
        scores=[(similarity(prefs,person,other),other) for other in prefs if other!=person]
        scores.reverse()
        return scores[0:n]

    def getRecommendations(prefs,person,similarity=sim_pearson):
        totals={}
        simSums={}
        for other in prefs:
            if other==person: continue
            sim=similarity(prefs,person,other)
            if sim<=0: continue
            for item in prefs[other]:
                if item not in prefs[person] or prefs[person][item]==0:
                    totals.setdefault(item,0)
                    totals[item]+=prefs[other][item]*sim
                    simSums.setdefault(item,0)
                    simSums[item]+=sim
        rankings=[(total/simSums[item],item) for item,total in totals.items()]
        rankings.sort()
        rankings.reverse()
        r = [rankings[0][0], rankings[0][1]]
        return r

    if len(ratings[0]) == 0:
        max_id = Movie.objects.all().aggregate(max_id=Max("id"))['max_id']
        pk = random.randint(1, max_id)
        movie = Movie.objects.get(pk=pk)
        name = movie.name
        id = movie.id
    else:
        movie = getRecommendations(ratings, 0)[0]
        name = movie[1]
        id = Movie.objects.get(name = name)[0]
    return render(request, 'done.html', {'id': id, 'name': name})

def rate(request, pk):
    ratings[0][pk] = int(request.POST['rating'])
    print(ratings)
    return redirect('done')

class MovieDetailView(DetailView):
    model = Movie
