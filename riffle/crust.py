
from greenlet import greenlet
import ctypes
import random
import os
import json

# When runnin as a package
# _DIRNAME = os.path.dirname(__file__)
# go = ctypes.cdll.LoadLibrary(os.path.join(_DIRNAME, 'libriffmantle.so'))

# When running locally-- no gopy
# mantle = ctypes.cdll.LoadLibrary('./libriffmantle.so')

# When running with gopy
import riffle

class Deferred(object):

    def __init__(self):
        self._callback, self._errback = None, None
        self._callbackId, self._errbackId = -1, -1

def cbid():
    return random.getrandbits(53)
    
class App(object):

    def __init__(self):
        self._app = riffle.App()
        self._app.Init()

        self.registrations, self.subscriptions, self.meta = {}, {}, {}

    def recv(self):
        while True:
            i, args = json.loads(self._app.Receive())
            args = args if args is not None else []

            # Wrap it all in a try-catch, return publish and call errors
            # Don't return yield errors-- its not clear who should deal with those 

            if i in self.meta:
                # Remove the meta call after called? It should not be called more than once, no?
                self.meta[i](*args)

            elif i in self.subscriptions:
                self.subscriptions[i](*args)

            elif i in self.registrations:
                ret = self.registrations[i](*args)


            else: 
                print "No handler available for ", i


# Internalize this reference into the domain object. For now, its ok global
app = App()


class Domain(object):

    def __init__(self, name):
        self.mantleDomain = app._app.NewDomain(name)
        self.name = name

    def join(self):
        cb, eb = cbid(), cbid()
        app.meta[cb] = self.onJoin
        self.mantleDomain.Join(cb, eb)

        # Make this explicit by putting it in its own method
        app.recv()

    def onJoin(self):
        riffle.Info("Default onJoin")

    def onLeave(self):
        riffle.Info("Default onLeave")

    def subscribe(self, endpoint, handler):
        fn = cbid()
        riffle.Debug('Subscribing with id: ' + str(fn))
        self.mantleDomain.Subscribe(fn, endpoint)
        app.subscriptions[fn] = handler

    def register(self, endpoint, handler):
        fn = cbid()
        self.mantleDomain.Register(fn, endpoint)
        app.registrations[fn] = handler

    def publish(self, endpoint, *args):
        self.mantleDomain.Publish(cbid(), endpoint, json.dumps(args))

    def call(self, endpoint, *args):
        fn = cbid()
        self.mantleDomain.Call(fn, endpoint, json.dumps(args))
        # app.callbacks[fn] = handler

