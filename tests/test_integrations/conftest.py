"""Travelling tests may use doubles or loopback fixtures, never live providers."""

import ipaddress
import socket

import pytest


def _loopback(host):
    if host == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


@pytest.fixture(autouse=True)
def no_live_provider_network(monkeypatch):
    original_connect = socket.socket.connect
    original_connect_ex = socket.socket.connect_ex
    original_resolve = socket.getaddrinfo

    def check_address(address):
        if isinstance(address, tuple) and not _loopback(address[0]):
            raise AssertionError("Live provider network is forbidden in verification")

    def connect(sock, address):
        check_address(address)
        return original_connect(sock, address)

    def connect_ex(sock, address):
        check_address(address)
        return original_connect_ex(sock, address)

    def resolve(host, *args, **kwargs):
        if host is not None and not _loopback(host):
            raise AssertionError("External DNS is forbidden in verification")
        return original_resolve(host, *args, **kwargs)

    monkeypatch.setattr(socket.socket, "connect", connect)
    monkeypatch.setattr(socket.socket, "connect_ex", connect_ex)
    monkeypatch.setattr(socket, "getaddrinfo", resolve)
