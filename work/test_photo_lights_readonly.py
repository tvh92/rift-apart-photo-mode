import struct
import unittest
from capture_photo_lights_readonly import (sample, queue_header, decode_record, registered_light_queries,
    query_summary, pointer, PRIMARY, PHOTO, QUEUE, ARCHIVE)


class CaptureTest(unittest.TestCase):
    def setUp(self):
        self.base, self.view = 0x140000000, 0x20000
        photo = bytearray(0x58)
        struct.pack_into('<Q', photo, 0, self.base + 0x2FBF630)
        struct.pack_into('<i', photo, 0x50, 4)
        photo[0x54] = 1
        query = bytearray(0x90)
        struct.pack_into('<Q', query, 0, self.view)
        struct.pack_into('<Q', query, 8, 0xB0000)
        struct.pack_into('<i', query, 0x10, 2)
        struct.pack_into('<Q', query, 0x38, 0xB0000)
        struct.pack_into('<i', query, 0x44, 2)
        record = bytearray(0x170)
        struct.pack_into('<3f', record, 0xB0, 1, 2, 3)
        struct.pack_into('<4f', record, 0x70, .1, .2, .3, .7)
        struct.pack_into('<f', record, 0xDC, 20)
        job = bytearray(0x20)
        struct.pack_into('<Q', job, 0x18, 0xA0000)
        self.mem = {
            self.base + PHOTO: bytes(photo),
            self.base + PRIMARY: struct.pack('<Q', self.view),
            self.view + 0x30: struct.pack('<3f', 4, 5, 6),
            self.view + QUEUE: struct.pack('<QIHH', 0x30000, 77, 3, 4),
            self.view + 0x1670: struct.pack('<QIHH', 0x31000, 88, 1, 4),
            self.base + ARCHIVE: struct.pack('<Qii', 0, 0, 0),
            0x30000: struct.pack('<6Q', 0x67 << 48, 0x70000,
                                0x67 << 48, 0x80000, 0xBB << 48, 0x90000),
            0x31000: struct.pack('<QQ', 0xBB << 48, 0x90000),
            0x50000: bytes(0xD0), 0x60000: bytes(0xD0),
            0x70000: bytes(record), 0x80000: bytes(record),
            0x90000: bytes(job), 0xA0000: bytes(query),
            0xB0000: struct.pack('<QQ', 0x50000, 0x60000),
        }
        for registry in (0x6414C30, 0x64151D8):
            self.mem[self.base + registry + 0x508] = struct.pack('<Qii', 0, 0, 0)
            self.mem[self.base + registry + 0x598] = bytes(4)

    def read(self, address, amount):
        data = self.mem[address]
        if len(data) != amount:
            raise OSError('Unmapped amount')
        return data

    def test_queue_and_query(self):
        result = sample(self.read, self.base)
        self.assertEqual(result['pass67_record_count'], 2)
        self.assertEqual(result['queries'], [])
        self.assertEqual(query_summary(self.read, 0xA0000, self.view)['arrays']['selected']['count'], 2)
        self.assertEqual(result['records'][0]['world_position_B0'], [1, 2, 3])
        self.assertFalse(result['atomic'])
        self.assertFalse(result['callback_order_proven'])

    def test_matching_archived_segment(self):
        self.mem[self.base + ARCHIVE] = struct.pack('<Qii', 0xC0000, 2, 2)
        self.mem[0xC0000] = struct.pack('<QIIQII', 0xD0000, 1, 77, 0xE0000, 1, 99)
        self.mem[0xD0000] = struct.pack('<QQ', 0x67 << 48, 0x70000)
        result = sample(self.read, self.base)
        self.assertEqual(result['pass67_record_count'], 3)
        self.assertEqual(result['segments'], 2)

    def test_archive_overflow_refused(self):
        self.mem[self.base + ARCHIVE] = struct.pack('<Qii', 0xC0000, 3, 2)
        with self.assertRaises(RuntimeError): sample(self.read, self.base)

    def test_large_unused_archive_allocation(self):
        self.mem[self.base + ARCHIVE] = struct.pack('<Qii', 0, 0, 16384)
        self.assertEqual(sample(self.read, self.base)['pass67_record_count'], 2)

    def request_slot(self):
        registry = 0x6414C30
        slot = bytearray(0xC0)
        struct.pack_into('<Q', slot, 0x78, self.base + 0x12B8740)
        struct.pack_into('<Q', slot, 0x38, self.base + 0x674EC10)
        struct.pack_into('<Q', slot, 0x68, 0xB0000)
        struct.pack_into('<Q', slot, 0x70, 0xA0010)
        self.mem[0xF0000] = bytes(slot)
        self.mem[0xA0000 + 0x1000] = bytes(0x28)
        self.mem[self.base + registry + 0x508] = struct.pack('<Qii', 0xF0000, 16, 1)
        return slot

    def test_typed_registered_query(self):
        self.request_slot()
        # Fake reader supports the short header and full query reads.
        def read(address, amount):
            if address == 0xA0000 and amount == 0x28:
                return self.mem[address][:0x28]
            return self.read(address, amount)
        queries, errors = registered_light_queries(read, self.base, self.view)
        self.assertEqual(len(queries), 1)
        self.assertEqual(len(queries[0]['sources']), 2)
        self.assertEqual(errors, [])

    def test_wrong_callback_not_treated_as_lights(self):
        slot = self.request_slot()
        struct.pack_into('<Q', slot, 0x78, self.base + 0x12B8741)
        self.mem[0xF0000] = bytes(slot)
        queries, _ = registered_light_queries(self.read, self.base, self.view)
        self.assertEqual(queries, [])

    def test_output_mismatch_refuses_source_arrays(self):
        slot = self.request_slot()
        self.mem[0xA0000 - 0x10] = bytes(0x28)
        struct.pack_into('<Q', slot, 0x68, 0x123000)
        self.mem[0xF0000] = bytes(slot)
        array_reads = []
        def read(address, amount):
            if address == 0xA0000 and amount == 0x28:
                return self.mem[address][:0x28]
            if address == 0xA0000 and amount == 0x90:
                array_reads.append(address)
            return self.read(address, amount)
        queries, _ = registered_light_queries(read, self.base, self.view)
        self.assertEqual(queries, [])
        self.assertEqual(array_reads, [])

    def test_request_generation_change_refused(self):
        calls = 0
        target = self.base + 0x6414C30 + 0x598
        def read(address, amount):
            nonlocal calls
            if address == target:
                calls += 1
                if calls > 1: return struct.pack('<I', 2)
            return self.read(address, amount)
        with self.assertRaises(RuntimeError): registered_light_queries(read, self.base, self.view)

    def test_inactive_photo_refused(self):
        data = bytearray(self.mem[self.base + PHOTO])
        struct.pack_into('<i', data, 0x50, 0)
        self.mem[self.base + PHOTO] = bytes(data)
        with self.assertRaises(RuntimeError): sample(self.read, self.base)

    def test_auxiliary_query_refused(self):
        data = bytearray(self.mem[0xA0000])
        struct.pack_into('<Q', data, 0, self.view + 16)
        self.mem[0xA0000] = bytes(data)
        with self.assertRaisesRegex(RuntimeError, 'another view'):
            query_summary(self.read, 0xA0000, self.view)

    def test_retired_record_reported(self):
        def read(address, amount):
            if address == 0x70000: raise OSError('Retired')
            return self.read(address, amount)
        result = sample(read, self.base)
        self.assertEqual(result['pass67_record_count'], 1)
        self.assertEqual(len(result['errors']), 1)

    def test_view_changes_refused(self):
        calls = 0
        def read(address, amount):
            nonlocal calls
            if address == self.base + PRIMARY:
                calls += 1
                if calls > 1: return struct.pack('<Q', 0x40000)
            return self.read(address, amount)
        with self.assertRaises(RuntimeError): sample(read, self.base)

    def test_queue_changes_refused(self):
        calls = 0
        def read(address, amount):
            nonlocal calls
            if address == 0x30000:
                calls += 1
                if calls > 1: return bytes(amount)
            return self.read(address, amount)
        with self.assertRaises(RuntimeError): sample(read, self.base)

    def test_unbounded_query_refused(self):
        data = bytearray(self.mem[0xA0000])
        struct.pack_into('<i', data, 0x10, 1000000)
        self.mem[0xA0000] = bytes(data)
        with self.assertRaises(RuntimeError): query_summary(self.read, 0xA0000, self.view)

    def test_array_change_refused(self):
        calls = 0
        def read(address, amount):
            nonlocal calls
            if address == 0xB0000:
                calls += 1
                if calls > 1: return bytes(amount)
            return self.read(address, amount)
        with self.assertRaises(RuntimeError): query_summary(read, 0xA0000, self.view)

    def test_queue_bounds(self):
        for count, capacity in ((5, 4), (1, 129)):
            with self.assertRaises(RuntimeError): queue_header(struct.pack('<QIHH', 0x30000, 77, count, capacity))

    def test_pointer_bounds(self):
        for value in (0, 1234, 0x20001, 0x800000000000):
            with self.assertRaises(RuntimeError): pointer(value)

    def test_bad_record_and_nonfinite(self):
        with self.assertRaises(RuntimeError): decode_record(bytes(128))
        data = bytearray(0x170)
        struct.pack_into('<f', data, 0x70, float('nan'))
        self.assertIsNone(decode_record(data)['rgb_70'][0])


if __name__ == '__main__':
    unittest.main()
