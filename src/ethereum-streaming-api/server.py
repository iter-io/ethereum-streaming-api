import eventlet
import os
import psycopg2

from eventlet import wsgi
from eventlet import websocket
from eventlet.hubs import trampoline
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


dsn = os.environ.get('POSTGRES_DSN')
port = os.environ.get('PORT', 5678)


def pg_listen(queue, channel):
    """Open a postgres connection and add notifications to the queue.
    """
    connection = psycopg2.connect(dsn)
    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = connection.cursor()
    cursor.execute("LISTEN {};".format(channel))
    while 1:
        trampoline(connection, read=True)
        connection.poll()
        while connection.notifies:
            item = connection.notifies.pop()
            queue.put(item)


@websocket.WebSocketWSGI
def handle_blocks(websocket):
    """Receive a connection and send it database notifications.
    """
    queue = eventlet.Queue()
    eventlet.spawn(pg_listen, queue, 'blocks')
    while 1:
        item = queue.get()
        websocket.send(item.payload)


@websocket.WebSocketWSGI
def handle_transactions(websocket):
    """Receive a connection and send it raw transactions.

    :param websocket:
    :return:


    We create queue and pass it to the pg_listen function.  Then we wait for
    data on the queue and send it through the websocket.
    """
    queue = eventlet.Queue()
    eventlet.spawn(pg_listen, queue, 'transactions')
    while 1:
        item = queue.get()
        websocket.send(item.payload)


@websocket.WebSocketWSGI
def handle_fees_sum(websocket):
    queue = eventlet.Queue()
    eventlet.spawn(pg_listen, queue, 'fees_sum')
    while 1:
        item = queue.get()
        websocket.send(item.payload)


@websocket.WebSocketWSGI
def handle_fees_sum(websocket):
    queue = eventlet.Queue()
    eventlet.spawn(pg_listen, queue, 'fees_sum')
    while 1:
        item = queue.get()
        websocket.send(item.payload)


@websocket.WebSocketWSGI
def handle_fees_avg(websocket):
    queue = eventlet.Queue()
    eventlet.spawn(pg_listen, queue, 'fees_avg')
    while 1:
        item = queue.get()
        websocket.send(item.payload)


def dispatch(environ, start_response):
    """
    TODO:  /fees?aggregate=sum&window_size_in_blocks=10

    :param environ:
    :param start_response:
    :return:
    """
    path = environ.get('PATH_INFO')
    query_string = environ.get('QUERY_STRING', None)

    if path == '/blocks':
        return handle_blocks(environ, start_response)

    elif path == '/transactions':
        return handle_transactions(environ, start_response)

    elif path == '/fees' and query_string == 'aggregate=sum':
        return handle_fees_sum(environ, start_response)

    elif path == '/fees' and query_string == 'aggregate=avg':
        return handle_fees_avg(environ, start_response)

    else:
        start_response('200 OK', [('content-type', 'text/html')])
        html_path = os.path.join(os.path.dirname(__file__), 'assets/html/blocks.html')
        return [open(html_path).read() % {'port': port}]


if __name__ == "__main__":
    listener = eventlet.listen(('127.0.0.1', port))
    wsgi.server(listener, dispatch)
