import sys
import struct
import binascii
import pawn_decrypt_data

def loadApp():
	data = open('./Generated Floppy Files/FILE1.BIN','rb').read()
	#print('LEN:%#x' % len(data))
	offset = 0
	tableSize,streamSize = struct.unpack('>HL', data[offset:offset+2+4])
	offset += struct.calcsize('>HL')
	
	# decompress the data
	tableOffset = offset
	streamOffset = offset + 1024
	decompressedData = bytearray()
	streamByte = data[streamOffset]
	streamOffset += 1
	bitPosition = 7
	while streamSize > 0:
		tableIndex = tableSize
		while True:
			if (streamByte & (1 << bitPosition)) == 0:
				tableIndex = struct.unpack('>H', data[tableOffset + 2 + tableIndex * 4:tableOffset + 2 + tableIndex * 4 + 2])[0]
			else:
				tableIndex = struct.unpack('>H', data[tableOffset + tableIndex * 4:tableOffset + tableIndex * 4 + 2])[0]
			bitPosition -= 1
			if bitPosition < 0:
				streamByte = 0
				if streamOffset < len(data):
					streamByte = data[streamOffset]
				streamOffset += 1
				bitPosition = 7
			tableIndex &= 0x1FF
			if (tableIndex & 0x100) != 0:
				break
		decompressedData.append(tableIndex & 0xFF)
		streamSize -= 1
	return decompressedData

# Keys for the floppy access code (acts as copy protection)
key = bytearray([0x2F,0x3A,0x60,0x8C,0x60,0x8C,0x3F,0x3A,0x2E,0xE2])
keyCounter = 0x2f3a
decompressedData = loadApp()
# write the unpatched file
#open('./AtariImages/THE_PAWN.PRG','wb').write(decompressedData)

# decrypt the floppy access code for easier analysis
encryptedBlock = decompressedData[0x0dd2+0x1c:0x12e0+0x1c]
encryptedLength = len(encryptedBlock)
pawn_decrypt_data.decryptData(encryptedBlock, encryptedLength, key, keyCounter)

def patchBlock(patch, offset, repeat = 1):
	global decompressedData
	decompressedData = decompressedData[:offset] + patch * repeat + decompressedData[offset + len(patch * repeat):]

patchBlock(encryptedBlock, 0xdd2+0x1c)
nops = bytearray([0x4e,0x71])
# patch out the directory reading code during setup, it is no longer needed
patchBlock(nops, 0x64, 21)

# patch out the call into decryption during loading an image
patchBlock(nops, 0xdcc, 9)
# patch out the call into reencryption during loading an image
patchBlock(nops, 0xde0, 4)

# now replace the sector based loading code with a small block, which uses Gemdos to load the images
# The floppy is now no longer accessed.
patch = binascii.unhexlify('48E7FFFE2C4843FA005680FC000AD03C00301340000C4840D03C00301340000D42672F093F3C003D4E41508F3E006B2A2F0E4879000080003F073F3C003F4E414FEF000C4A806B0C3F073F3C003E4E41584F4A404CDF7FFF4E7570FF60F62E2F494D472F494D4147455F30302E4441540000')
patchBlock(patch, 0xf10, 1)

# The encryption for the save files stays including the checksum check for it to allow compatibility with existing saves.


open('./AtariImages/THE_PAWN.PRG','wb').write(decompressedData)

# This is the 68k Assembly code to load a file
#	; fileindex in D0
#	; load buffer in A0
#			movem.l D0-A6,-(SP)
#			movea.l A0,A6
#			lea     filename(PC),A1
#			divu    #10,D0
#			add.b   #'0',D0
#			move.b  D0,12(A1)
#			swap    D0
#			add.b   #'0',D0
#			move.b  D0,13(A1)
#			clr.w   -(SP)
#			move.l  A1,-(SP)
#			move.w  #$3D,-(SP)
#			trap    #1
#			addq.l  #8,SP
#			move.w  D0,D7
#			bmi.s   error
#			move.l  A6,-(SP)
#			pea     $8000           ; try reading 32kb
#			move.w  D7,-(SP)
#			move.w  #$3F,-(SP)
#			trap    #1
#			lea     12(SP),SP
#			tst.l   D0
#			bmi.s   return
#			move.w  D7,-(SP)
#			move.w  #$3E,-(SP)
#			trap    #1
#			addq.w  #4,SP
#			tst.w   D0
#	return: ; the return status is actually not tested...
#			movem.l (SP)+,D0-A6
#			rts
#		
#	error:
#			moveq   #-1,D0
#			bra.s   return
#		
#	filename:       DC.B './IMG/IMAGE_00.DAT',0
