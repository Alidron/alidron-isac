green_backend = 'gevent'

if green_backend == 'eventlet':
    import eventlet as green
    from eventlet.green import zmq
elif green_backend == 'gevent':
    import gevent as green
    import zmq.green as zmq

from netcall import concurrency

_tools = concurrency.get_tools(env=green_backend)
Future = _tools.Future
Event = _tools.Event
