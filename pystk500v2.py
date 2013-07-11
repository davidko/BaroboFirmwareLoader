"""
A Python module for communicating with stk500v2 programmers, such as the Pololu
PGM03A for programming AVR chips.
"""

class HexFile():
  def __init__(self):
    self.data = bytearray(0)
    self.extaddr = 0 # Extended address (Upper byte of address)

  def fromIHexFile(self, filename, offset=0):
    f = open(filename, 'r')
    self.fromIHexString(f.read(), offset)
    f.close()

  def fromIHexString(self, string, offset=0):
    for substr in string.split('\n'):
      self._parseLine(substr, offset)

  def toIHexString(self, blocksize=0x10):
    currentAddr = 0
    extAddr = 0
    hexstring = ''
    while currentAddr < len(self.data):
      if (currentAddr & 0xffff == 0) and (currentAddr > 0):
        extAddr+=1
        hexline = ':02000004{:04X}'.format(extAddr)
        hexline += self._calculateChecksum(hexline[1:])
        hexstring += hexline + '\n'
      hexstring += self.toIHexLine(currentAddr, blocksize)
      currentAddr += blocksize
    hexstring += ':00000001FF\n'
    return hexstring

  def toIHexLine(self, address, blocksize):
    # See if we have enough bytes left to fill up the block
    hexline = ''
    if len(self.data) - address < blocksize:
      blocksize = len(self.data) - address
    hexline = ':'
    hexline += "{:02X}".format(blocksize)
    hexline += "{:04X}".format(address&0xffff)
    hexline += "00"
    for i in range(0, blocksize):
      hexline += "{:02X}".format(self.data[address])
      address += 1
    hexline += self._calculateChecksum(hexline[1:])
    hexline += '\n'
    return hexline

  def _calculateChecksum(self, hexstring):
    mysum = 0
    for i in range(0, len(hexstring), 2):
      mysum += int(hexstring[i:i+2], 16)
    return "{:02X}".format((~mysum+1)&0x00ff)

  def _parseLine(self, string, offset=0):
    if len(string) == 0:
      return
    if string[0] != ':':
      raise BytesWarning("Parse error: Expected ':'")
    size = int(string[1:3], 16)
    address = int(string[3:7], 16)
    address += offset
    memtype = int(string[7:9], 16)
    data = []
    for i,j in enumerate(range(9,9+size*2,2)):
      data += [int(string[j:j+2], 16)]
    checksum = int(string[9+size*2:], 16)
    # Check the checksum
    self._checksum(string)
    if memtype == 4:
      self.extaddr = data[0]<<8 | data[1]
    elif memtype == 2:
      self.extaddr = data[0] >> 4
      offset += data[1] << 4
      offset += (data[0] & 0x00ff) << 12
    # See if the address is out of range of our current size. If so, pad with 0xFF
    address = (self.extaddr << 16) + address;
    oldlen = len(self.data)
    if address + size > oldlen:
      pad = bytearray(['\xff' for i in range(address+size-oldlen)])
      self.data += pad
    for i,d in zip(range(address, address+size),data):
      self.data[i] = d

  def _checksum(self, string):
    mysum = 0
    for i in range(1, len(string)-1, 2):
      mysum += int(string[i:i+2], 16)
    mysum = mysum & 0xff
    if mysum != 0:
      raise BytesWarning("Checksum failed." + string)


if __name__ == '__main__':
  h = HexFile()
  h.fromIHexFile('dof.hex')
  h.fromIHexFile('bootloader.hex')
  print h.toIHexString(blocksize=0x20)
