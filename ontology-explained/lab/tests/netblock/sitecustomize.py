"""Put this folder on PYTHONPATH to run Python with no network: any socket connect raises.

lab/tests/test_offline.py uses it to prove every step runs offline on its recorded answers.
"""
import socket


def _blocked(*args, **kwargs):
    raise OSError("network blocked by lab/tests/netblock (offline test)")


socket.socket.connect = _blocked
socket.socket.connect_ex = _blocked
socket.create_connection = _blocked
socket.getaddrinfo = _blocked
