import sys
import binascii
import pawn_decrypt_data


# Keys for save files
key = bytearray([0x12,0x34,0x56,0x78,0x9A,0xBC,0xDE,0xF0,0x30,0x39])
keyCounter = 0x1a85
# a save is just an encrypted memory dump from 0x4250..0x66a2 relative to the start of the app (A6 register)
encryptedBlock = bytearray(open('TESTSAVE.BIN', 'rb').read())
encryptedLength = 0x2454
pawn_decrypt_data.decryptData(encryptedBlock, encryptedLength, key, keyCounter)

# erase previous checksum
checksum = ''
for checksumIndex in range(0x198,0x198+12):
	checksum += '%02x' % encryptedBlock[checksumIndex]
	encryptedBlock[checksumIndex] = 0x00

# calculate new checksum
wordSum = 0
xorSum = 0
multSum = 1
longSum = 0
zeroWordCounter = 0
for offset in range(0, encryptedLength, 2):
	word = (encryptedBlock[offset] << 8) + encryptedBlock[offset+1]
	wordSum += word
	wordSum &= 0xFFFF
	xorSum ^= word
	longSum += word
	if word != 0:
		multSum = ((multSum * word) >> 16) + 1
	else:
		zeroWordCounter += 1

checkSumStr = '%04x%04x%04x%04x%08x' % (wordSum,xorSum,multSum,zeroWordCounter,longSum)
if checkSumStr != checksum:
	print('# Checksum INVALID')
else:
	print(binascii.hexlify(encryptedBlock))
	print('# Checksum valid')
	