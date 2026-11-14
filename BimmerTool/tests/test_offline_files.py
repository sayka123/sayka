import hashlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from bimmertool.offline_files import compare_binary, load_fa, MAX_BYTES

FA = '''<faList xmlns:f="http://bmw.com/2005/psdz.data.fa"><id><f:fa>
<f:header vinLong="WBY21CF000S123456"/>
<f:standardFA series="I020" typeKey="11CF" timeCriteria="0722" colourCode="0C57">
<f:saCodes><f:saCode>6CP</f:saCode><f:saCode>5AZ</f:saCode><f:saCode>6CP</f:saCode></f:saCodes>
</f:standardFA></f:fa></id></faList>'''


class OfflineFiles(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        self.root = Path(self.folder.name)
        self.addCleanup(self.folder.cleanup)

    def put(self, name, data):
        path = self.root / name
        path.write_bytes(data)
        return path

    def test_fa_namespace_codes_and_no_vin_disclosure(self):
        path = self.put('fa.xml', FA.encode())
        before = path.read_bytes()
        result = load_fa(path)
        self.assertEqual(result['metadata']['series'], 'I020')
        self.assertEqual(result['sa_codes'], ['5AZ', '6CP'])
        self.assertTrue(result['vin_present'])
        self.assertNotIn('WBY21CF000S123456', repr(result))
        self.assertEqual(result['sha256'], hashlib.sha256(before).hexdigest())
        self.assertEqual(path.read_bytes(), before)

    def test_utf16(self):
        result = load_fa(self.put('fa.xml', FA.encode('utf-16')))
        self.assertEqual(result['metadata']['typeKey'], '11CF')

    def test_rejects_entities_for_utf8_and_utf16(self):
        payload = '<!DOCTYPE fa [<!ENTITY x "hello">]><fa>&x;</fa>'
        for encoding in ['utf-8', 'utf-16']:
            with self.subTest(encoding=encoding), self.assertRaises(ValueError):
                load_fa(self.put('bad.xml', payload.encode(encoding)))

    def test_rejects_wrong_schema_multiple_fa_and_malformed(self):
        for value in ['<root/>', '<fa>', '<root><fa/><fa/></root>',
                      '<fa><standardFA/></fa>', FA.replace('6CP', 'bad-code')]:
            with self.subTest(value=value[:40]), self.assertRaises(ValueError):
                load_fa(self.put('bad.xml', value.encode()))

    def test_binary_diff_insertion_and_removal(self):
        a = self.put('a.ncd', b'\x00\x01\x02')
        b = self.put('b.ncd', b'\x00\xFF\x02\x03')
        result = compare_binary(a, b)
        self.assertEqual(result['changed_bytes'], 2)
        self.assertEqual(result['rows'], [{'offset': 0, 'before': '00 01 02', 'after': '00 FF 02 03'}])
        self.assertFalse(result['semantic_decode'])
        self.assertEqual(compare_binary(b, a)['changed_bytes'], 2)
        self.assertEqual(compare_binary(a, a)['rows'], [])

    def test_diff_display_limit_does_not_truncate_total_count(self):
        a = self.put('a.ncd', b'\x00' * 64)
        b = self.put('b.ncd', b'\x01' * 64)
        with patch('bimmertool.offline_files.MAX_DIFF_ROWS', 1):
            result = compare_binary(a, b)
        self.assertEqual(len(result['rows']), 1)
        self.assertEqual(result['changed_bytes'], 64)
        self.assertTrue(result['display_truncated'])

    def test_empty_and_oversized_files_rejected(self):
        valid = self.put('a', b'\x00')
        for data in [b'', b'0' * (MAX_BYTES + 1)]:
            invalid = self.put('bad', data)
            with self.assertRaises(ValueError):
                compare_binary(valid, invalid)
            with self.assertRaises(ValueError):
                load_fa(invalid)
