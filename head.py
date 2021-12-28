from ctypes import *

class AckHeader(Structure):
    _pack_ = 1
    _fields_ = [
        ("header0", c_ubyte),
        ("header1", c_ubyte),
        ("length", c_uint32),
        ("chk_sum", c_uint16),
        ("client_id", c_ubyte),
        ("data_type", c_ubyte),
        ("reserve", c_ubyte*10)
    ]

class TransHeader(Structure):
    _pack_ = 1
    _fields_ = [
        ("header0", c_ubyte),
        ("header1", c_ubyte),
        ("count", c_uint32),
        ("client_id", c_ubyte),
        ("chk_sum", c_uint16),
        ("data_size", c_uint16),
        ("reserve", c_ubyte*9)
    ]
