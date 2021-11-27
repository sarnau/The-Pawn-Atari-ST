import sys
import struct
import binascii

for imageIndex in range(2,33):
	data = open('./Generated Floppy Files/FILE%d.BIN' % imageIndex,'rb').read()
	#print('LEN:%#x' % len(data))
	offset = 0
	sizeMinusOne, hOffset, width, height = struct.unpack('>4H', data[offset:offset+8])
	offset += struct.calcsize('>4H')
	print('File #%d, Size=%d horizontal Offset=%d Width=%d, Height=%d' % (imageIndex, sizeMinusOne, hOffset, width, height))
	#print('Indices',struct.unpack('16B', data[offset:offset+16]))
	offset += struct.calcsize('16B')
	unknown, = struct.unpack('>L', data[offset:offset+4])
	offset += struct.calcsize('>L')
	if unknown != 0:
		print('# Unknown %d != 0' % unknown)
	paletteOffset = offset
	colors = []
	for color in struct.unpack('>16H', data[paletteOffset:paletteOffset+16*2]):
		colors.append('%03x' % color)
	offset += struct.calcsize('>16H')
	#print('Colors',colors)
	tableSize,streamSize = struct.unpack('>HL', data[offset:offset+2+4])
	offset += struct.calcsize('>HL')
	#print('Table Size #%d' % tableSize)
	if sizeMinusOne + 1 != streamSize:
		print('# Unexpected size %#x != ' % (streamSize, sizeMinusOne + 1))

	# decompress the data
	tableOffset = offset
	streamOffset = offset + 2 * (tableSize + 1)
	decompressedData = bytearray()
	streamByte = data[streamOffset]
	streamOffset += 1
	bitPosition = 7
	while streamSize > 0:
		tableIndex = tableSize
		while True:
			if (streamByte & (1 << bitPosition)) == 0:
				tableIndex = data[tableOffset + 1 + tableIndex * 2]
			else:
				tableIndex = data[tableOffset + tableIndex * 2]
			bitPosition -= 1
			if bitPosition < 0:
				streamByte = 0
				if streamOffset < len(data):
					streamByte = data[streamOffset]
				streamOffset += 1
				bitPosition = 7
			if (tableIndex & 0x80) != 0:
				break
		decompressedData.append(tableIndex & 0x7F)
		streamSize -= 1
	
	# RLE decoding of the nibbles
	nibbleBitmap = bytearray(160 * 200)
	nibbleOffset = 0
	streamOffset = 0
	nibbleRepeat = 0
	for _ in range(0,height):
		nibbleOffset += hOffset >> 1
		xPos = hOffset
		while True:
			if nibbleRepeat:
				nibbleRepeat -= 1
				if (xPos & 1) == 0:
					nibbleBitmap[nibbleOffset] |= nibble << 4
				else:
					nibbleBitmap[nibbleOffset] |= nibble
					nibbleOffset += 1
			else:
				streamByte = 0
				if streamOffset < len(decompressedData):
					streamByte = decompressedData[streamOffset]
				streamOffset += 1
				if streamByte < 0x10:
					nibble = streamByte
					nibbleRepeat = 1
				else:
					nibbleRepeat = streamByte - 0x10
				continue
			xPos += 1
			if xPos == width:
				break
		nibbleOffset += 160 - ((width + 1) >> 1)

	# xor all lines with the next line
	for y in range(0,200-1):
		for x in range(0,160):
			nibbleBitmap[x + (y + 1) * 160] ^= nibbleBitmap[x + y * 160]
	# we now have a 320x200 pixel image with 4-bit (16 colors) per pixel

	# build the Atari bitmpa to be stored as a PI0 file
	atariBitmap = bytearray()
	for y in range(0,200):
		for x in range(0,160,8):
			planes = [0,0,0,0]
			for byte in range(0,8):
				for nibble in range(0,2):
					color = nibbleBitmap[x + byte + y * 160]
					if nibble == 0:
						color >>= 4
					color &= 0x0f
					bit = byte * 2 + nibble
					#print("%d+%d x %d = %d" % (x,bit,y,color))
					if color & 1:
						planes[0] |= 1 << (15 - bit)
					if color & 2:
						planes[1] |= 1 << (15 - bit)
					if color & 4:
						planes[2] |= 1 << (15 - bit)
					if color & 8:
						planes[3] |= 1 << (15 - bit)
			for plane in planes:
				atariBitmap.append(plane >> 8)
				atariBitmap.append(plane & 0xFF)

	if imageIndex == 32: # the title has one palette per line
		# 200 color palettes (one for each line) are stored at the very end of the main application
		palettes = open('./The Pawn/THE_PAWN.PRG' ,'rb').read()[-16*2*200:]
		spectrum512Image = bytearray()
		spectrum512Image += atariBitmap
		for paletteOffset in range(32,len(palettes),32): # skip the palette for the first line
			spectrum512Image += palettes[paletteOffset:paletteOffset+32]
			spectrum512Image += palettes[paletteOffset:paletteOffset+32]
			spectrum512Image += palettes[paletteOffset:paletteOffset+32]
		open('./AtariImages/FILE%d.SPU' % imageIndex,'wb').write(spectrum512Image)
	else:
		degasImage = bytearray()
		degasImage.append(0)
		degasImage.append(0)
		degasImage += data[paletteOffset:paletteOffset+16*2]
		degasImage += atariBitmap
		open('./AtariImages/FILE%d.PI1' % imageIndex,'wb').write(degasImage)
	