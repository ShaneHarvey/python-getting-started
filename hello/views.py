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

import objgraph

import gc

if hasattr(gc, 'set_debug'):
    gc.set_debug(
        gc.DEBUG_UNCOLLECTABLE |
        getattr(gc, 'DEBUG_OBJECTS', 0) |
        getattr(gc, 'DEBUG_LEAK', 0) |
        getattr(gc, 'DEBUG_INSTANCES', 0))


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

from pymongo import network


def _get_documents(request):
    def _receive_data_on_socket_mod(sock, length):
        buf = bytearray(length)
        i = 0
        while length:
            try:
                chunk = sock.recv(min(length, 16384))
            except (IOError, OSError) as exc:
                if network._errno_from_exception(exc) == network.errno.EINTR:
                    continue
                raise
            if chunk == b"":
                raise network.AutoReconnect("connection closed")

            buf[i:i + len(chunk)] = chunk
            i += len(chunk)
            length -= len(chunk)

        return bytes(buf)

    network._receive_data_on_socket = _receive_data_on_socket_mod

    uri = os.environ.get('MONGODB_URI')
    if not uri:
        return ['MONGODB_URI not set!']

    limit = 10
    with MongoClient(uri) as client:
        coll = client.heroku.test
        large_batch_coll = client.heroku.large
        if large_batch_coll.estimated_document_count() == 0:
            # Add ~20Mib of data
            large = 's'*1024*1024
            large_batch_coll.insert_many(
                [{'s': large, 'i': i} for i in range(20)])
        docs = list(large_batch_coll.find(batch_size=1024))
        del docs
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
    extra = '%s\nEXTRA:\n%s' % (stream.getvalue(), '')
    print('objgraph.show_growth(limit=100):')
    objgraph.show_growth(limit=100)
    return render(request, "mongodb.html", {"documents": docs, "extra": extra})
