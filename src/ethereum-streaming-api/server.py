import eventlet
import os
import psycopg2

from eventlet import wsgi
from eventlet import websocket
from eventlet.hubs import trampoline
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT


dsn = os.environ.get('POSTGRES_DSN')

def pg_listen(queue):
    """Open a postgres connection and add notifications to the queue.
    """
    connection = psycopg2.connect(dsn)
    connection.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cursor = connection.cursor()
    cursor.execute("LISTEN blocks;")
    while 1:
        trampoline(connection, read=True)
        connection.poll()
        while connection.notifies:
            item = connection.notifies.pop()
            queue.put(item)


@websocket.WebSocketWSGI
def handle(websocket):
    """Receive a connection and send it database notifications.
    """
    queue = eventlet.Queue()
    eventlet.spawn(pg_listen, queue)
    while 1:
        item = queue.get()
        websocket.send(item.payload)


def dispatch(environ, start_response):
    return handle(environ, start_response)


if __name__ == "__main__":
    listener = eventlet.listen(('127.0.0.1', 5678))
    wsgi.server(listener, dispatch)
