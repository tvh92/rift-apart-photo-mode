"""Isolated probe safety tests; no real game process is opened or changed."""
import contextlib
import ctypes as C
import hashlib
import io
import struct
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
import probe_photo_fog_range as probe


class Function:
    def __init__(self, fn): self.fn = fn
    def __call__(self, *args): return self.fn(*args)


class ProbeTests(unittest.TestCase):
    def test_identity_and_ownership_restore_guards(self):
        original, replacement = struct.pack('<f',64), struct.pack('<f',128)
        args = (10,10,b'header',b'header',replacement,original,replacement)
        self.assertEqual(probe.restoration_action(*args),'restore')
        for index,value,expected in ((0,11,'object_changed'),(2,b'new','object_changed'),
                                     (4,original,'already_original'),(4,b'abcd','native_value_changed')):
            changed=list(args); changed[index]=value
            self.assertEqual(probe.restoration_action(*changed),expected)

    def test_photo_gate(self):
        base=0x100000
        photo=bytearray(0x58)
        struct.pack_into('<Q',photo,0,base+probe.PHOTO_VTABLE)
        struct.pack_into('<i',photo,0x50,4); photo[0x54]=1
        self.assertTrue(probe.valid_photo(photo,base))
        for offset,value in ((0,0),(0x50,14),(0x54,0)):
            changed=bytearray(photo); changed[offset]=value
            self.assertFalse(probe.valid_photo(changed,base))

    def test_profile_restoration_preserves_only_changed_native_fields(self):
        original=struct.pack('<3f',1,2,3); replacement=struct.pack('<3f',4,5,6)
        current=struct.pack('<3f',4,99,3)
        merged,preserved=probe.restore_owned_fields(current,original,replacement)
        self.assertEqual(merged,struct.pack('<3f',1,99,3)); self.assertEqual(preserved,[4])

    def test_near_payload_excludes_texture_tail_and_refuses_wrong_build(self):
        fog=bytearray(0x8C)
        struct.pack_into('<3f',fog,0,.24,.15,.24)
        struct.pack_into('<3f',fog,0x54,.01,-100,32)
        struct.pack_into('<2f',fog,0x60,0,48)
        fog[-8:]=b'textures'
        report={'exe_sha256':probe.EXPECTED,'label':'corson-near-processed',
                'photo_system_candidate':{'vtable_rva':'0x2fbf630','state_50':4,'setup_54':1},
                'renderer_samples':[{'fog_110_19C_hex':fog.hex()}]}
        self.assertEqual(probe.near_fog_payload(report),bytes(fog[:0x84]))
        report['exe_sha256']='unsupported'
        with self.assertRaises(RuntimeError): probe.near_fog_payload(report)

    def simulate(self, apply=False, photo_state=4, overwrite=False, fail_readback=False, profile=False):
        base,pointer=0x100000,0x900000
        block=bytearray(probe.BLOCK_SIZE)
        struct.pack_into('<2f',block,0x44C,0,64)
        initial=bytes(block)
        photo=bytearray(0x58)
        struct.pack_into('<Q',photo,0,base+probe.PHOTO_VTABLE)
        struct.pack_into('<i',photo,0x50,photo_state); photo[0x54]=1
        memory={base+probe.PHOTO_RVA:photo,base+probe.REGISTRY_RVA+0x1C8:struct.pack('<Q',pointer),
                pointer:block}
        writes=[]
        pending_failure=[False]
        def read(handle,address,buffer,size,got):
            if pending_failure[0]:
                pending_failure[0]=False
                raise OSError('simulated readback failure')
            for start,data in memory.items():
                if start <= address and address+size <= start+len(data):
                    C.memmove(buffer,bytes(data[address-start:address-start+size]),size)
                    got._obj.value=size; return True
            raise AssertionError(hex(address))
        def write(handle,address,buffer,size,got):
            expected_offset,expected_size=(0x3EC,0x84) if profile else (probe.ENDPOINT_OFFSET,4)
            self.assertEqual((address,size),(pointer+expected_offset,expected_size))
            value=C.string_at(buffer,size); writes.append(value)
            block[expected_offset:expected_offset+size]=value; got._obj.value=size
            if fail_readback and len(writes)==1: pending_failure[0]=True
            return True
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory); (root/'work/live-atmosphere-readonly').mkdir(parents=True)
            exe=root/'RiftApart.exe'; exe.touch(); exe.with_name('hid.dll').write_bytes(b'test')
            def query(handle,flags,name,size): name.value=str(exe); return True
            api=type('Kernel',(),{})()
            for name,fn in {'OpenProcess':lambda *a:1,'CloseHandle':lambda *a:True,
                            'ReadProcessMemory':read,'WriteProcessMemory':write,
                            'QueryFullProcessImageNameW':query,
                            'GetExitCodeProcess':lambda *a:True}.items():
                setattr(api,name,Function(fn))
            report={'module_base':hex(base),'selected_pointer':hex(pointer),
                    'fallback':False,'pointer_stable':True,
                    'primary_view_candidates':{'0x6739b10':{'position_30_raw_floats':[0,0,100]}}}
            argv=['probe','7','--seconds','1']+(['--apply'] if apply else [])
            if profile:
                fog=bytearray(0x8C)
                struct.pack_into('<3f',fog,0,.24,.15,.24)
                struct.pack_into('<f',fog,0x54,.01); struct.pack_into('<f',fog,0x64,48)
                near={'exe_sha256':probe.EXPECTED,'label':'corson-near-processed',
                      'photo_system_candidate':{'vtable_rva':'0x2fbf630','state_50':4,'setup_54':1},
                      'primary_view_candidates':{'0x6739b10':{'position_30_raw_floats':[0,0,0]}},
                      'renderer_samples':[{'fog_110_19C_hex':fog.hex()}]}
                near_path=root/'near.json'
                import json
                near_path.write_text(json.dumps(near),encoding='utf-8')
                argv+=['--near-fog',str(near_path)]
            def sleep(seconds):
                if overwrite: struct.pack_into('<f',block,probe.ENDPOINT_OFFSET,96)
            with patch.object(probe,'ROOT',root),patch.object(probe,'EXE',exe),\
                 patch.object(probe,'DLL_HASH',hashlib.sha256(b'test').hexdigest()),\
                 patch.object(probe,'capture',return_value=(report,initial)),\
                 patch.object(probe.C,'WinDLL',return_value=api),\
                 patch('sys.argv',argv),patch.object(probe.time,'sleep',side_effect=sleep),\
                 patch.object(probe.time,'monotonic',side_effect=[0,0,0,2]),\
                 contextlib.redirect_stdout(io.StringIO()):
                try: probe.main()
                except (RuntimeError,OSError):
                    if photo_state==4 and not fail_readback: raise
            return writes,struct.unpack_from('<f',block,probe.ENDPOINT_OFFSET)[0]

    def test_dry_run_never_writes(self): self.assertEqual(self.simulate(),([],64))
    def test_apply_restores_after_deadline(self):
        writes,value=self.simulate(apply=True)
        self.assertEqual(writes,[struct.pack('<f',128),struct.pack('<f',64)])
        self.assertEqual(value,64)
    def test_outside_photo_refuses_write(self): self.assertEqual(self.simulate(True,14),([],64))
    def test_native_change_is_not_overwritten(self):
        writes,value=self.simulate(True,overwrite=True)
        self.assertEqual(writes,[struct.pack('<f',128)]); self.assertEqual(value,96)
    def test_failed_readback_still_restores(self):
        writes,value=self.simulate(True,fail_readback=True)
        self.assertEqual(writes,[struct.pack('<f',128),struct.pack('<f',64)])
        self.assertEqual(value,64)

    def test_near_profile_whole_block_restores(self):
        writes,value=self.simulate(True,profile=True)
        self.assertEqual(len(writes),2); self.assertEqual(len(writes[0]),0x84)
        self.assertEqual(writes[1][:0x64],bytes(0x64)); self.assertEqual(value,64)

    def test_near_profile_native_edit_restores_other_fields(self):
        writes,value=self.simulate(True,overwrite=True,profile=True)
        self.assertEqual(len(writes),2); self.assertEqual(value,96)
        self.assertEqual(writes[1][:0x64],bytes(0x64))


if __name__=='__main__': unittest.main()
