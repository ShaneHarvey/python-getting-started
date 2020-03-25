from django.shortcuts import render
from django.http import HttpResponse

from .models import Greeting

import os
from pymongo import MongoClient
from bson.son import SON
from bson.objectid import ObjectId

import psutil
import memory_profiler
try:
    from StringIO import StringIO
except ImportError:
    from io import StringIO

host_id = ObjectId()


def get_mem():
    process = psutil.Process(os.getpid())
    return process.memory_info().rss


# Create your views here.
def index(request):
    # return HttpResponse('Hello from Python!')
    return render(request, "index.html")


def db(request):

    greeting = Greeting()
    greeting.save()

    greetings = Greeting.objects.all()

    return render(request, "db.html", {"greetings": greetings})


def _get_documents(request):
    uri = os.environ.get('MONGODB_URI')
    if not uri:
        return ['MONGODB_URI not set!']

    limit = 10
    with MongoClient(uri) as client:
        coll = client.heroku.test
        for i in range(limit):
            coll.insert_one(SON([('mem', get_mem()), ('units', 'bytes'),
                                 ('client', i), ('host', host_id)]))
            # Close all connections.
            client.close()
        documents = list(coll.find(
            {'host': host_id}, limit=limit*50, sort=[('_id', -1)],
            projection={'_id': False, 'host': False}))

    return documents


def mongodb(request):
    stream = StringIO()
    docs = memory_profiler.profile(_get_documents, stream=stream)(request)
    extra = stream.getvalue()

    return render(request, "mongodb.html", {"documents": docs, "extra": extra})
