import sys
import struct

data = open('./Generated Floppy Files/DIR.BIN','rb').read()
print('DIR : o:%08x len:%08x' % (0, struct.unpack('>i', data[0:4])[0]))
for index in range(0,63,1):
	offset = struct.unpack('>i', data[index*4:(index+1)*4])[0]
	nextoffset = struct.unpack('>i', data[(index+1)*4:(index+2)*4])[0]
	if nextoffset < 0:
		break
	print('#%2d : o:%08x len:%08x' % (index, offset, nextoffset-offset))
