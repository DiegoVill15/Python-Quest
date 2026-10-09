import io
import os
import socket
import ssl
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

from app import create_app
from quest import grader, providers, service


class SecurityTests(unittest.TestCase):
    def test_unsafe_programs_never_start(self):
        programs = [
            'scope = vars()\nhelpers = vars(scope["__builtins__"])\n'
            'helpers["exec"]("print(1)")\ndef vars():\n return 0\nprint(int(input()))',
            'import subprocess\nsubprocess.Popen(["echo", "unsafe"])',
            'open("example.txt", "w").write("unsafe")',
            'print((1).__class__.__base__.__subclasses__())',
            'print("{0.__class__}".format(1))',
            'def f():\n return 1\nf.__globals__["__builtins__"]',
        ]
        for source in programs:
            with self.subTest(source=source), patch('quest.grader.subprocess.Popen') as start:
                self.assertFalse(service.fits_world(source, 'funciones', 1))
                self.assertTrue(grader.run_one(source, '')['error'])
                start.assert_not_called()

    def test_functions_collections_and_comprehensions_still_work(self):
        source = ('def doble(n):\n return n * 2\n'
                  'datos = list(map(int, input().split()))\n'
                  'print(sum([doble(n) for n in datos]))\n')
        self.assertEqual(grader.run_one(source, '2 3\n')['actual'], '10')

    def test_unicode_input_and_output_have_portable_line_endings(self):
        result = grader.run_one('nombre = input()\nprint(nombre)\nprint("¡Buen trabajo!")', 'Lía 🐍\n')
        self.assertEqual(result['stdout'], 'Lía 🐍\n¡Buen trabajo!\n')
        self.assertEqual(result['error'], '')
        result = providers.run_cli([sys.executable, '-X', 'utf8', '-c', 'print(input())'], input='Lía 🐍', text=True)
        self.assertEqual(result.stdout.strip(), 'Lía 🐍')

    @unittest.skipUnless(os.name == 'posix', 'POSIX process groups')
    def test_cleanup_kills_children_even_after_parent_exits(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / 'child.txt'
            child = f'import time; from pathlib import Path; time.sleep(0.6); Path({str(marker)!r}).touch()'
            parent = (f'import subprocess, sys; subprocess.Popen([sys.executable, "-c", {child!r}], '
                      'stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)')
            process = subprocess.Popen([sys.executable, '-c', parent], start_new_session=True)
            try:
                process.wait(timeout=3)
                grader._stop_process(process)
                time.sleep(0.8)
                self.assertFalse(marker.exists())
            finally:
                grader._stop_process(process)

    def test_https_uses_validated_address_and_preserves_tls_hostname(self):
        public = [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', ('93.184.216.34', 443))]
        private = [(socket.AF_INET, socket.SOCK_STREAM, socket.IPPROTO_TCP, '', ('127.0.0.1', 443))]
        transport = MagicMock()
        with patch('quest.providers.socket.getaddrinfo', side_effect=[public, private]) as dns, patch(
                'quest.providers.socket.socket', return_value=transport), patch(
                'ssl.SSLContext.wrap_socket', return_value=MagicMock()) as tls:
            connection = providers.PublicHTTPSConnection('audit.example', timeout=providers.REQUEST_TIMEOUT)
            connection.connect()
            self.assertEqual(dns.call_count, 1)
            transport.connect.assert_called_once_with(('93.184.216.34', 443))
            self.assertEqual(tls.call_args.kwargs['server_hostname'], 'audit.example')
            self.assertTrue(connection._context.check_hostname)
            self.assertEqual(connection._context.verify_mode, ssl.CERT_REQUIRED)
        with patch('quest.providers.socket.getaddrinfo', return_value=private), patch(
                'quest.providers.socket.socket') as start:
            with self.assertRaises(providers.ProviderError):
                providers.PublicHTTPSConnection('audit.example').connect()
            start.assert_not_called()

        connection = providers.PublicHTTPSConnection('audit.example')
        connection.deadline = time.monotonic() - 1
        with patch('quest.providers.socket.getaddrinfo') as dns, self.assertRaises(TimeoutError):
            connection.connect()
        dns.assert_not_called()

    def test_http_response_limit_and_total_deadline(self):
        with patch('quest.providers.validate_endpoint'), patch('quest.providers.request.build_opener') as opener:
            opener.return_value.open.return_value = io.BytesIO(b'{}')
            self.assertEqual(providers.http_json('https://audit.example', 'dummy', 'compatible'), {})
            opener.return_value.open.return_value = io.BytesIO(b'x' * (providers.RESPONSE_LIMIT + 1))
            with self.assertRaisesRegex(providers.ProviderError, 'tamaño'):
                providers.http_json('https://audit.example', 'dummy', 'compatible')
            response = MagicMock()
            response.__enter__.return_value = response
            stopped = threading.Event()
            transport = MagicMock()
            transport.shutdown.side_effect = lambda how: stopped.set()
            def build(*handlers):
                handler = next(value for value in handlers if isinstance(value, providers.PublicHTTPSHandler))
                handler.connections.append(MagicMock(transport=transport))
                return opener.return_value
            opener.side_effect = build
            response.read.side_effect = lambda size: (stopped.wait(1), b'{}')[1]
            opener.return_value.open.return_value = response
            with patch('quest.providers.REQUEST_TIMEOUT', 0.02), self.assertRaisesRegex(providers.ProviderError, 'tardó'):
                providers.http_json('https://audit.example', 'dummy', 'compatible')
            self.assertTrue(stopped.is_set())
            transport.shutdown.assert_called_once_with(socket.SHUT_RDWR)

    def test_cli_response_limit_and_timeout(self):
        with patch('quest.providers.RESPONSE_LIMIT', 4096):
            with self.assertRaisesRegex(providers.ProviderError, 'tamaño'):
                providers.run_cli([sys.executable, '-c', 'print("x" * 5000)'])
        with self.assertRaises(subprocess.TimeoutExpired):
            providers.run_cli([sys.executable, '-c', 'import time; time.sleep(3)'], timeout=0.05)

    def test_malformed_mission_retries_without_execution(self):
        invalid = [None, [], {'tests': [None] * 6}, {'title': 1, 'reference_solution': []}]
        for value in invalid:
            with self.subTest(value=value), tempfile.TemporaryDirectory() as directory, patch(
                    'quest.codex_teacher.generate', return_value=value) as generate, patch(
                    'quest.service.grader.grade') as grade:
                client = create_app(directory).test_client()
                result = client.post('/api/challenges', json={'world_id': 'fundamentos'},
                                     headers={'X-Python-Quest': '1'})
                self.assertEqual(result.status_code, 503)
                self.assertEqual(generate.call_count, 3)
                grade.assert_not_called()
