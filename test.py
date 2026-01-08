import struct

data = bytes([0x28, 0x00, 0x00, 0x00])

# Little endian (<)
little_endian_val = struct.unpack('<i', data)[0]

# Big endian (>)
big_endian_val = struct.unpack('>i', data)[0]

print("Little endian:", little_endian_val)
print("Big endian:", big_endian_val)
