"""Execute the literal HTTP helper against an in-memory Unix transport."""
import io
import hashlib
import json
import stat
import struct
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from tiny_swarm_world.infrastructure.adapters.clients.lxc.profile.cas import PROFILE_CAS

_NAME = 'tsw-manager-' + hashlib.sha256(b'11111111-1111-1111-1111-111111111111').hexdigest()[:24]
_PATH = '/1.0/profiles/' + _NAME + '?project=default'
_BEFORE = {'name': _NAME, 'project': 'default', 'description': 'Tiny Swarm World installation profile',
           'config': {'user.tiny_swarm_world.installation_id': '11111111-1111-1111-1111-111111111111',
                      'user.tiny_swarm_world.operation_id': 'a' * 32}, 'devices': {}, 'used_by': ['/1.0/instances/swarm-manager']}
_TARGET = {'description': _BEFORE['description'], 'config': _BEFORE['config'], 'devices': {
    'tsw-proxy-16080': {'type': 'proxy', 'bind': 'host', 'listen': 'tcp:127.0.0.1:16080',
                        'connect': 'tcp:127.0.0.1:16080', 'nat': 'false', 'proxy_protocol': 'false'}}}


def response(metadata, *, status=200, etag='"' + 'a' * 64 + '"', extra=''):
    data = json.dumps({'type': 'sync', 'status': 'Success', 'status_code': 200, 'operation': '',
                       'error_code': 0, 'error': '', 'metadata': metadata}).encode()
    return (f'HTTP/1.1 {status} OK\r\nContent-Type: application/json\r\nContent-Length: {len(data)}\r\nETag: {etag}\r\n{extra}\r\n'.encode() + data)


class Socket:
    def __init__(self, raw, trace, uid=0):
        self.raw, self.trace, self.uid = raw, trace, uid
    def settimeout(self, seconds): pass
    def connect(self, path): self.trace.append(('connect', path))
    def getsockopt(self, *args): return struct.pack('3i', 42, self.uid, 0)
    def sendall(self, raw): self.trace.append(('send', raw))
    def makefile(self, *args):
        if isinstance(self.raw, Exception):
            raise self.raw
        return io.BytesIO(self.raw)
    def close(self): pass


class ProfileHttpCasTests(unittest.TestCase):
    def run_helper(self, replies, *, before=None, uid=0, path=_PATH, endpoint_kind='incus_var_lib'):
        trace = []
        sockets = [Socket(raw, trace, uid) for raw in replies]
        def lstat(value):
            return SimpleNamespace(st_uid=0, st_mode=stat.S_IFSOCK | 0o660 if value.endswith('unix.socket') else stat.S_IFDIR | 0o755)
        output = io.StringIO()
        arg = {'endpoint_kind': endpoint_kind, 'path': path, 'before': _BEFORE if before is None else before, 'target': _TARGET}
        code: object = 0
        with patch('sys.argv', ['literal-cas', json.dumps(arg)]), patch('sys.stdout', output), \
                patch('http.client._MAXLINE', 65536), patch('http.client._MAXHEADERS', 100), \
                patch('os.lstat', side_effect=lstat), patch('socket.socket', side_effect=sockets):
            try:
                exec(compile(PROFILE_CAS, '<literal-profile-cas>', 'exec'), {'__name__': '__main__'})
                code = 0
            except SystemExit as error:
                code = error.code
        return code, output.getvalue(), trace

    def test_real_http_headers_bind_if_match_and_exact_target_and_fixed_socket(self):
        code, output, trace = self.run_helper([response(_BEFORE), response({})])
        sent = b''.join(item[1] for item in trace if item[0] == 'send')
        self.assertEqual((code, output), (0, 'PROFILE_CAS_APPLIED\n'))
        self.assertEqual([item[1] for item in trace if item[0] == 'connect'], ['/var/lib/incus/unix.socket'] * 2)
        self.assertIn(('GET ' + _PATH + ' HTTP/1.1').encode(), sent)
        self.assertIn(('PUT ' + _PATH + ' HTTP/1.1').encode(), sent)
        self.assertIn(('If-Match: "' + 'a' * 64 + '"').encode(), sent)
        self.assertIn(json.dumps(_TARGET, separators=(',', ':')).encode(), sent)

    def test_before_drift_bad_etag_peer_or_uri_cannot_issue_put(self):
        cases = [([response({**_BEFORE, 'config': {'secret': 'raw-canary'}})], {}),
                 ([response(_BEFORE, etag='unknown')], {}),
                 ([response(_BEFORE)], {'uid': 1000}),
                 ([response(_BEFORE)], {'path': 'https://foreign/1.0'})]
        for replies, options in cases:
            with self.subTest(options=options):
                code, output, trace = self.run_helper(replies, **options)
                self.assertEqual((code, output), (2, 'PROFILE_CAS_UNKNOWN\n'))
                self.assertNotIn(b'PUT ', b''.join(item[1] for item in trace if item[0] == 'send'))
                self.assertNotIn('raw-canary', output)

    def test_412_or_lost_put_response_never_retry_or_emit_raw_state(self):
        for final in (response({'secret': 'raw-canary'}, status=412), OSError('raw-canary')):
            with self.subTest(final_type=type(final).__name__):
                code, output, trace = self.run_helper([response(_BEFORE), final])
                sent = b''.join(item[1] for item in trace if item[0] == 'send')
                self.assertEqual((code, output), (2, 'PROFILE_CAS_UNKNOWN\n'))
                self.assertEqual(sent.count(b'PUT '), 1)
                self.assertEqual(len([item for item in trace if item[0] == 'connect']), 2)

    def test_bound_run_socket_kind_is_explicit_and_unknown_kind_never_connects(self):
        code, _, trace = self.run_helper([response(_BEFORE), response({})], endpoint_kind='incus_run')
        self.assertEqual(code, 0)
        self.assertEqual([item[1] for item in trace if item[0] == 'connect'], ['/run/incus/unix.socket'] * 2)
        code, output, trace = self.run_helper([], endpoint_kind='guess')
        self.assertEqual((code, output, trace), (2, 'PROFILE_CAS_UNKNOWN\n', []))
