"""Exercise the real guard with transport doubles so a defect cannot call out."""

import socket

import pytest

from tests.test_integrations import conftest as guard


@pytest.fixture
def fake_network(monkeypatch):
    calls = []

    class FakeSocket:
        def connect(self, address):
            calls.append(("connect", address))

        def connect_ex(self, address):
            calls.append(("connect_ex", address))
            return 0

        def sendto(self, data, *args):
            calls.append(("sendto", args[-1]))
            return len(data)

        def sendmsg(self, buffers, ancdata=(), flags=0, address=None):
            calls.append(("sendmsg", address))
            return sum(map(len, buffers))

    def resolve(host, *args, **kwargs):
        calls.append(("getaddrinfo", host))
        return []

    monkeypatch.setattr(socket, "socket", FakeSocket)
    monkeypatch.setattr(socket, "getaddrinfo", resolve)
    guard.no_live_provider_network.__wrapped__(monkeypatch)
    return calls


def call_socket(method, address):
    connection = socket.socket()
    if method == "sendto":
        return connection.sendto(b"synthetic", address)
    if method == "sendmsg":
        return connection.sendmsg([b"synthetic"], [], 0, address)
    return getattr(connection, method)(address)


@pytest.mark.parametrize("method", ["connect", "connect_ex", "sendto", "sendmsg"])
def test_remote_socket_is_refused_before_transport(fake_network, method):
    with pytest.raises(AssertionError, match="Live provider network"):
        call_socket(method, ("203.0.113.1", 443))
    assert fake_network == []


@pytest.mark.parametrize("host", ["provider.invalid", "203.0.113.1"])
def test_external_resolution_is_refused_before_resolver(fake_network, host):
    with pytest.raises(AssertionError, match="External DNS"):
        socket.getaddrinfo(host, 443)
    assert fake_network == []


@pytest.mark.parametrize("method", ["connect", "connect_ex", "sendto", "sendmsg"])
def test_loopback_transport_double_remains_available(fake_network, method):
    address = ("127.0.0.1", 1234)
    call_socket(method, address)
    assert fake_network == [(method, address)]


@pytest.mark.parametrize("host", ["localhost", "127.0.0.1", "::1"])
def test_loopback_resolver_double_remains_available(fake_network, host):
    socket.getaddrinfo(host, 1234)
    assert fake_network == [("getaddrinfo", host)]


def test_unix_transport_double_remains_available(fake_network):
    call_socket("connect", "/tmp/synthetic-test-only.sock")
    assert fake_network == [("connect", "/tmp/synthetic-test-only.sock")]
