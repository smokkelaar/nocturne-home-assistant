import io
import json
from pathlib import Path
import sys
import unittest
from unittest.mock import patch
import urllib.error
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
import registry


class ImmutableRegistryTests(unittest.TestCase):
    def error(self, status, code):
        return urllib.error.HTTPError('https://ghcr.io/test', status, 'Synthetic', {},
            io.BytesIO(json.dumps({'errors':[{'code':code}]}).encode()))

    def test_only_explicit_manifest_or_repository_absence_allows_initial_push(self):
        for code in ('MANIFEST_UNKNOWN','NAME_UNKNOWN'):
            with patch.object(registry,'fetch',side_effect=[({'token':'synthetic'},''), self.error(404,code)]):
                registry.require_absent('owner/repo/image','1.0.1','synthetic-token')

    def test_auth_timeout_server_errors_and_existing_tags_fail_closed(self):
        for result in (self.error(401,'UNAUTHORIZED'),self.error(500,'UNKNOWN'),
                       self.error(404,'UNAUTHORIZED'),urllib.error.URLError('synthetic timeout'), ({'config':{}},'')):
            with patch.object(registry,'fetch',side_effect=[({'token':'synthetic'},''),result]), self.assertRaises((ValueError,urllib.error.URLError)):
                registry.require_absent('owner/repo/image','1.0.1','synthetic-token')
