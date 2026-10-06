import struct
import unittest
from capture_photo_lights_readonly import (sample, queue_header, decode_record, registered_light_queries,
    query_summary, pointer, decode_planes, PRIMARY, PHOTO, QUEUE, ARCHIVE)


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
        if 0xF0000 <= address < 0xF0000 + len(self.mem.get(0xF0000, b'')):
            # Single request slot inside the registry backing block.
            data = self.mem[0xF0000][address - 0xF0000:address - 0xF0000 + amount]
        elif address not in self.mem:
            raise OSError('Unmapped')
        else:
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

    GENERATION = 5

    def key(self, index=0, bit=0, generation=None):
        generation = self.GENERATION if generation is None else generation
        return generation << 32 | index * 2 | bit

    def request_slot(self, index=0, kind='fixed', key=None, output=0xB0000):
        """Fixed request: count pointer query+10, key at query+70.
        Optional request: count pointer query+20, key at query+68."""
        registry = 0x6414C30
        key = self.key(index) if key is None else key
        slot = bytearray(0xC0)
        struct.pack_into('<Q', slot, 0, key)
        struct.pack_into('<Q', slot, 0x78, self.base + 0x12B8740)
        struct.pack_into('<Q', slot, 0x38, self.base + 0x674EC10)
        struct.pack_into('<Q', slot, 0x68, output)
        struct.pack_into('<Q', slot, 0x48, 0x200000)
        self.mem[0x200000] = bytes(0x100)
        struct.pack_into('<Q', slot, 0x70, 0xA0000 + (0x10 if kind == 'fixed' else 0x20))
        slots = bytearray(self.mem.get(0xF0000, b''))
        slots.extend(bytes(max(0, (index + 1) * 0xC0 - len(slots))))
        slots[index * 0xC0:(index + 1) * 0xC0] = slot
        self.mem[0xF0000] = bytes(slots)
        query = bytearray(self.mem[0xA0000])
        struct.pack_into('<Q', query, 0x70 if kind == 'fixed' else 0x68, key)
        self.mem[0xA0000] = bytes(query)
        self.mem[self.base + registry + 0x508] = struct.pack('<Qii', 0xF0000, 16, len(slots) // 0xC0)
        self.mem[self.base + registry + 0x598] = struct.pack('<I', self.GENERATION)
        return slot

    def test_typed_registered_query(self):
        self.request_slot()
        queries, errors = registered_light_queries(self.read, self.base, self.view)
        self.assertEqual(len(queries), 1)
        self.assertEqual(len(queries[0]['sources']), 2)
        request = queries[0]['requests'][0]
        self.assertEqual(request['kind'], 'fixed')
        self.assertEqual(request['key'], hex(self.key()))
        self.assertEqual(request['worker_output']['count'], 2)
        self.assertEqual(errors, [])

    def test_wrong_callback_not_treated_as_lights(self):
        slot = self.request_slot()
        struct.pack_into('<Q', slot, 0x78, self.base + 0x12B8741)
        self.mem[0xF0000] = bytes(slot)
        queries, _ = registered_light_queries(self.read, self.base, self.view)
        self.assertEqual(queries, [])

    def test_output_mismatch_reported_separately(self):
        # Worker output need not equal the current query array (10BAC65).
        self.request_slot(output=0x123000)
        self.mem[0x123000] = struct.pack('<QQ', 0x50000, 0x125000)
        self.mem[0x125000] = bytes(0xD0)
        queries, errors = registered_light_queries(self.read, self.base, self.view)
        self.assertEqual(len(queries), 1)
        out = queries[0]['requests'][0]['worker_output']
        self.assertEqual(out['pointer'], hex(0x123000))
        self.assertEqual(out['words'], [hex(0x50000), hex(0x125000)])
        # Already-summarised source is not duplicated; output-only one is.
        self.assertEqual(list(out['sources']), [hex(0x125000)])
        self.assertEqual(queries[0]['arrays']['input_fixed']['pointers'], [hex(0x50000), hex(0x60000)])
        self.assertEqual(errors, [])

    def assert_refused_without_array_reads(self):
        array_reads = []
        def read(address, amount):
            if address in (0xB0000, 0x50000, 0x60000):
                array_reads.append(address)
            return self.read(address, amount)
        queries, _ = registered_light_queries(read, self.base, self.view)
        self.assertEqual(queries, [])
        self.assertEqual(array_reads, [])

    def test_stale_generation_key_refused(self):
        self.request_slot(key=self.key(generation=self.GENERATION - 1))
        self.assert_refused_without_array_reads()

    def test_wrong_index_key_refused(self):
        self.request_slot(key=self.key(index=1))
        self.assert_refused_without_array_reads()

    def test_wrong_registry_bit_refused(self):
        self.request_slot(key=self.key(bit=1))
        self.assert_refused_without_array_reads()

    def test_zero_key_refused(self):
        self.GENERATION = 0
        self.request_slot(key=0)
        self.assert_refused_without_array_reads()

    def test_query_key_mismatch_refused(self):
        self.request_slot()
        query = bytearray(self.mem[0xA0000])
        struct.pack_into('<Q', query, 0x70, self.key() + 2)
        self.mem[0xA0000] = bytes(query)
        self.assert_refused_without_array_reads()

    def test_key_in_wrong_query_field_refused(self):
        # A fixed slot whose key appears only in the optional field.
        self.request_slot()
        query = bytearray(self.mem[0xA0000])
        struct.pack_into('<Q', query, 0x68, self.key())
        struct.pack_into('<Q', query, 0x70, 0)
        self.mem[0xA0000] = bytes(query)
        self.assert_refused_without_array_reads()

    def test_optional_request_and_shared_query(self):
        self.request_slot(0, 'fixed')
        query = bytearray(self.mem[0xA0000])
        struct.pack_into('<Q', query, 0x18, 0x126000)
        struct.pack_into('<i', query, 0x20, 1)
        self.mem[0xA0000] = bytes(query)
        self.mem[0x126000] = struct.pack('<Q', 0x60000)
        self.request_slot(1, 'optional', output=0x124000)
        self.mem[0x124000] = struct.pack('<Q', 0x60000)
        queries, _ = registered_light_queries(self.read, self.base, self.view)
        self.assertEqual(len(queries), 1)
        kinds = [r['kind'] for r in queries[0]['requests']]
        self.assertEqual(kinds, ['fixed', 'optional'])
        self.assertEqual(queries[0]['requests'][1]['key'], hex(self.key(1)))
        self.assertEqual(queries[0]['requests'][1]['worker_output']['count'], 1)

    def test_unbounded_output_count_refused(self):
        self.request_slot(output=0x123000)
        query = bytearray(self.mem[0xA0000])
        struct.pack_into('<i', query, 0x10, 100000)
        self.mem[0xA0000] = bytes(query)
        queries, errors = registered_light_queries(self.read, self.base, self.view)
        self.assertEqual(queries, [])
        self.assertTrue(errors)

    def test_output_change_refused(self):
        self.request_slot(output=0x123000)
        self.mem[0x123000] = struct.pack('<QQ', 0x50000, 0x60000)
        calls = 0
        def read(address, amount):
            nonlocal calls
            if address == 0x123000:
                calls += 1
                if calls > 1: return bytes(amount)
            return self.read(address, amount)
        queries, errors = registered_light_queries(read, self.base, self.view)
        self.assertEqual(queries, [])
        self.assertIn('Request output changed during sample', errors)

    def test_late_generation_change_refused(self):
        # Generation change after query/output reads still fails the sample.
        self.request_slot()
        target = self.base + 0x6414C30 + 0x598
        calls = 0
        def read(address, amount):
            nonlocal calls
            if address == target:
                calls += 1
                if calls > 2: return struct.pack('<I', self.GENERATION + 1)
            return self.read(address, amount)
        with self.assertRaises(RuntimeError): registered_light_queries(read, self.base, self.view)

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

    def test_plane_decoding(self):
        raw = bytearray(0x100)
        # Plane 5: block 1, lane 1 -> nx +0x44, ny +0x54, nz +0x64, d +0x74.
        for off, value in ((0x44, 1), (0x54, 2), (0x64, 3), (0x74, -4)):
            struct.pack_into('<f', raw, off, value)
        planes = decode_planes(bytes(raw))
        self.assertEqual(len(planes), 16)
        self.assertEqual(planes[5], [1, 2, 3, -4])
        self.assertEqual(planes[4], [0, 0, 0, 0])
        with self.assertRaises(RuntimeError): decode_planes(bytes(0x40))

    def test_typed_query_records_shape(self):
        self.request_slot()
        queries, _ = registered_light_queries(self.read, self.base, self.view)
        self.assertEqual(queries[0]['requests'][0]['shape_48'], hex(0x200000))
        self.assertEqual(len(queries[0]['requests'][0]['planes']), 16)

    def test_bad_record_and_nonfinite(self):
        with self.assertRaises(RuntimeError): decode_record(bytes(128))
        data = bytearray(0x170)
        struct.pack_into('<f', data, 0x70, float('nan'))
        self.assertIsNone(decode_record(data)['rgb_70'][0])


if __name__ == '__main__':
    unittest.main()
