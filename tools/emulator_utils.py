"""Headless emulator helpers; test runs never persist battery saves."""
from PIL import Image, ImageChops
from pyboy import PyBoy

def boot(path):
    emu = PyBoy(str(path), window='null', sound_emulated=False)
    emu.set_emulation_speed(0)
    return emu


def tick_to(emu, frame):
    emu.tick(frame-emu.frame_count, True)


def tap(emu, button):
    emu.button_press(button)
    emu.tick(8, True)
    emu.button_release(button)
    emu.tick(8, True)


def equal_screens(a, b):
    return ImageChops.difference(a.screen.image.convert('RGB'), b.screen.image.convert('RGB')).getbbox() is None


def apply_ips(original, patch):
    assert patch[:5] == b'PATCH'
    result = bytearray(original)
    pos = 5
    while patch[pos:pos+3] != b'EOF':
        offset = int.from_bytes(patch[pos:pos+3], 'big')
        size = int.from_bytes(patch[pos+3:pos+5], 'big')
        pos += 5
        assert size > 0
        if offset+size > len(result):
            result.extend(b'\0'*(offset+size-len(result)))
        result[offset:offset+size] = patch[pos:pos+size]
        pos += size
    return bytes(result)
