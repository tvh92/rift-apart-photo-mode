"""Malformed-file and embedded-renderer-error checks for the saved dump reader."""
from pathlib import Path
import struct
import tempfile
import unittest
from inspect_game_minidump import inspect


class DumpTest(unittest.TestCase):
    def decode(self, data):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'fixture.mdmp'
            path.write_bytes(data)
            return inspect(path)

    def header(self, count=0, directory=32):
        return bytearray(struct.pack('<4s7I', b'MDMP', 0, count, directory, 0, 0, 0, 0))

    def test_empty_dump_no_exception(self):
        report = self.decode(self.header())
        self.assertIsNone(report['exception'])
        self.assertEqual(report['writes'], 0)

    def test_wrong_signature_refused(self):
        with self.assertRaises(ValueError): self.decode(b'BAD!' + bytes(28))

    def test_directory_outside_file_refused(self):
        with self.assertRaises(ValueError): self.decode(self.header(1, 0x1000))

    def test_excess_stream_count_refused(self):
        with self.assertRaises(ValueError): self.decode(self.header(129))

    def test_stream_payload_outside_file_refused(self):
        data = self.header(1)
        data += struct.pack('<III', 6, 168, 0x1000)
        with self.assertRaises(ValueError): self.decode(data)

    def test_incomplete_exception_refused(self):
        data = self.header(1)
        data += struct.pack('<III', 6, 16, 44) + bytes(16)
        with self.assertRaises(ValueError): self.decode(data)

    def test_invalid_module_count_refused(self):
        data = self.header(1)
        data += struct.pack('<III', 4, 4, 44) + struct.pack('<I', 513)
        with self.assertRaises(ValueError): self.decode(data)

    def test_only_renderer_error_is_extracted(self):
        data = self.header()
        data += b'irrelevant private text\0[nri(D3D12)::ERROR] -- ID3D12Resource::Map() failed, error code: 0x887A0005.\0'
        report = self.decode(data)
        self.assertEqual(report['embedded_nri_errors'], [
            '[nri(D3D12)::ERROR] -- ID3D12Resource::Map() failed, error code: 0x887A0005.'])


if __name__ == '__main__':
    unittest.main()
