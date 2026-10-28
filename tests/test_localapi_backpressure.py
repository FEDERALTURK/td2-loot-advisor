"""Bounded WebSocket writers: fake slow sockets and loopback only."""
import base64
import json
import os
import socket
import struct
import sys
import threading
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import localapi


class BlockedSocket:
    def __init__(self):
        self.entered = threading.Event()
        self.released = threading.Event()
        self.timeout = None

    def settimeout(self, seconds):
        self.timeout = seconds

    def sendall(self, frame):
        self.entered.set()
        if not self.released.wait(3):
            raise RuntimeError("test socket was not shut down")
        raise OSError("closed")

    def shutdown(self, how):
        self.released.set()

    def close(self):
        self.released.set()


class RecordingSocket(BlockedSocket):
    def __init__(self, count=3):
        super().__init__()
        self.frames = []
        self.written = threading.Event()
        self.count = count

    def sendall(self, frame):
        self.frames.append(frame)
        if len(self.frames) >= self.count:
            self.written.set()


class BackpressureTests(unittest.TestCase):
    def setUp(self):
        self.api = localapi.LocalAPI(lambda: {})
        self.clients = []

    def tearDown(self):
        self.api.stop()
        for client in self.clients:
            client.close()
            self.assertTrue(client.closed.wait(2))

    def client(self, sock, **options):
        client = localapi._Client(sock, **options)
        self.clients.append(client)
        self.api.clients.append(client)
        return client

    def test_broadcast_returns_while_network_send_is_blocked(self):
        sock = BlockedSocket()
        client = self.client(sock)
        client.send({"type": "hello"})
        self.assertTrue(sock.entered.wait(1))
        done, result = threading.Event(), []

        def publish():
            result.append(self.api.broadcast({"type": "scan", "name": "test"}))
            done.set()

        caller = threading.Thread(target=publish, daemon=True)
        caller.start()
        # Completion is required before releasing the intentionally stuck
        # sendall, not inferred from an arbitrary fast elapsed-time threshold.
        self.assertTrue(done.wait(1))
        self.assertFalse(sock.released.is_set())
        self.assertEqual(result, [1])
        self.assertEqual(client.outgoing.qsize(), 1)
        self.assertEqual(sock.timeout, localapi.SOCKET_TIMEOUT)

    def test_full_queue_disconnects_without_growing(self):
        sock = BlockedSocket()
        client = self.client(sock, max_pending=2)
        client.send({"type": "hello"})
        self.assertTrue(sock.entered.wait(1))
        self.assertEqual(self.api.broadcast({"i": 1}), 1)
        self.assertEqual(self.api.broadcast({"i": 2}), 1)
        self.assertEqual(client.outgoing.qsize(), 2)
        self.assertEqual(self.api.broadcast({"i": 3}), 0)
        self.assertFalse(client.alive)
        self.assertLessEqual(client.outgoing.qsize(), 2)
        self.assertTrue(client.closed.wait(1))
        self.assertEqual(client.queued_bytes, 0)

    def test_outgoing_bytes_are_bounded_too(self):
        sock = BlockedSocket()
        client = self.client(sock, max_bytes=80)
        client.send({"type": "hello"})
        self.assertTrue(sock.entered.wait(1))
        self.assertFalse(client.send({"text": "x" * 100}))
        self.assertFalse(client.alive)
        self.assertTrue(client.closed.wait(1))

    def test_text_and_control_frames_use_one_writer_in_order(self):
        sock = RecordingSocket()
        client = self.client(sock)
        client.send({"type": "hello"})
        client.send_frame(b"ping payload", 0xA)
        client.send({"type": "scan"})
        self.assertTrue(sock.written.wait(1))
        self.assertEqual([frame[0] & 0xF for frame in sock.frames], [1, 0xA, 1])
        self.assertIn(b'"hello"', sock.frames[0])
        self.assertIn(b'"scan"', sock.frames[2])

    def test_socket_send_timeout_releases_writer(self):
        class TimeoutSocket(BlockedSocket):
            def sendall(self, frame):
                raise socket.timeout("slow reader")

        client = self.client(TimeoutSocket())
        client.send({"type": "hello"})
        self.assertTrue(client.closed.wait(1))
        self.assertFalse(client.alive)

    def test_stop_releases_blocked_writer_even_without_http_server(self):
        sock = BlockedSocket()
        client = self.client(sock)
        client.send({"type": "hello"})
        self.assertTrue(sock.entered.wait(1))
        self.api.stop()
        self.assertTrue(client.closed.wait(1))
        self.assertEqual(self.api.clients, [])

    def test_idle_receive_timeout_keeps_connection_alive(self):
        payload, mask = b'{"cmd":"get_state"}', b"abcd"

        class IdleThenFrame(RecordingSocket):
            def __init__(self):
                super().__init__()
                self.first = True
                self.data = (bytes([0x81, 0x80 | len(payload)]) + mask +
                             bytes(value ^ mask[i % 4] for i, value in enumerate(payload)))

            def recv(self, n):
                if self.first:
                    self.first = False
                    raise socket.timeout("idle")
                data, self.data = self.data[:n], self.data[n:]
                return data

        client = self.client(IdleThenFrame())
        self.assertEqual(client.recv_frame(), (1, payload))
        self.assertTrue(client.alive)


class LoopbackTests(unittest.TestCase):
    def setUp(self):
        self.api = localapi.LocalAPI(lambda: {"test": True}, port=0)
        self.api.start()
        self.port = self.api.httpd.server_address[1]
        self.sockets = []

    def tearDown(self):
        for sock in self.sockets:
            sock.close()
        self.api.stop()

    def connect(self):
        sock = socket.create_connection(("127.0.0.1", self.port), timeout=2)
        self.sockets.append(sock)
        key = base64.b64encode(os.urandom(16)).decode()
        req = (f"GET /ws?t={self.api.token} HTTP/1.1\r\nHost: 127.0.0.1:{self.port}\r\n"
               f"Upgrade: websocket\r\nConnection: Upgrade\r\nSec-WebSocket-Key: {key}\r\n"
               "Sec-WebSocket-Version: 13\r\n\r\n")
        sock.sendall(req.encode())
        response = b""
        while b"\r\n\r\n" not in response:
            chunk = sock.recv(1)
            if not chunk:
                raise ConnectionError("handshake closed")
            response += chunk
        return sock, response.split(b"\r\n", 1)[0]

    def receive(self, sock):
        def need(n):
            data = b""
            while len(data) < n:
                chunk = sock.recv(n - len(data))
                if not chunk:
                    raise ConnectionError("frame closed")
                data += chunk
            return data

        h = need(2)
        n = h[1] & 0x7F
        if n == 126:
            n = struct.unpack(">H", need(2))[0]
        elif n == 127:
            n = struct.unpack(">Q", need(8))[0]
        return h[0] & 0xF, need(n)

    def test_hello_precedes_events_and_client_limit_is_enforced(self):
        for _ in range(localapi.MAX_CLIENTS):
            sock, status = self.connect()
            self.assertIn(b" 101 ", status)
            opcode, raw = self.receive(sock)
            self.assertEqual(opcode, 1)
            self.assertEqual(json.loads(raw)["type"], "hello")
        self.assertEqual(len(self.api.clients), localapi.MAX_CLIENTS)
        _, status = self.connect()
        self.assertIn(b" 503 ", status)
        self.assertEqual(self.api.broadcast({"type": "scan"}), localapi.MAX_CLIENTS)
        for sock in self.sockets[:localapi.MAX_CLIENTS]:
            self.assertEqual(json.loads(self.receive(sock)[1])["type"], "scan")


if __name__ == "__main__":
    unittest.main()
