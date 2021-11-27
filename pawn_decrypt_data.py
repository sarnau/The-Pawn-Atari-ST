def decryptData(data, dataLength, key, keyCounter):
	def decryptModifyKey():
		key[4] = key[2]
		key[6] = key[3]
		d0 = key[3] + key[4]
		key[5] = d0 & 0xff
		d0 <<= 1
		key[7] = d0 & 0xff
		d0 += key[3]
		if d0 >= 0x100:
			d0 += 1
		key[8] = d0 & 0xff
		key[9] = (d0 >> 1) & 0xff
		
	def decryptMoveKey(xStatus=0):
		d0 = key[4] + key[8] + xStatus
		if d0 >= 0x100:
			d0 += 1
		d0 += key[9]
		key[4] = d0 & 0xff
		key[9] = key[8]
		key[8] = key[7]
		key[7] = key[6]
		key[6] = key[5]
		key[5] = key[4]
		return key[4]
	
	def decryptXorValue():
		val = (key[4] << 8) + key[5] + keyCounter
		key[4] = (val >> 8) & 0xff
		key[5] = val & 0xff
		key[0] = decryptMoveKey(val > 0xFFFF) # X status depends on the overflow of the additon
		key[1] = decryptMoveKey(1) # X status is always set because of previous DBRA
		return (key[0] << 8) + key[1]
	
	decryptModifyKey()
	for index in range(0, dataLength, 2):
		eorVal = decryptXorValue()
		data[index] ^= (eorVal >> 8) & 0xFF
		data[index+1] ^= eorVal & 0xFF
