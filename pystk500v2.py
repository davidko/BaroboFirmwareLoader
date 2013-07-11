"""
A Python module for communicating with stk500v2 programmers, such as the Pololu
PGM03A for programming AVR chips.
"""

import serial

class STK500():
  MESSAGE_START                       = 0x1B        
  TOKEN                               = 0x0E

# *****************[ STK general command constants ]**************************

  CMD_SIGN_ON                         = 0x01
  CMD_SET_PARAMETER                   = 0x02
  CMD_GET_PARAMETER                   = 0x03
  CMD_SET_DEVICE_PARAMETERS           = 0x04
  CMD_OSCCAL                          = 0x05
  CMD_LOAD_ADDRESS                    = 0x06
  CMD_FIRMWARE_UPGRADE                = 0x07


# *****************[ STK ISP command constants ]******************************

  CMD_ENTER_PROGMODE_ISP              = 0x10
  CMD_LEAVE_PROGMODE_ISP              = 0x11
  CMD_CHIP_ERASE_ISP                  = 0x12
  CMD_PROGRAM_FLASH_ISP               = 0x13
  CMD_READ_FLASH_ISP                  = 0x14
  CMD_PROGRAM_EEPROM_ISP              = 0x15
  CMD_READ_EEPROM_ISP                 = 0x16
  CMD_PROGRAM_FUSE_ISP                = 0x17
  CMD_READ_FUSE_ISP                   = 0x18
  CMD_PROGRAM_LOCK_ISP                = 0x19
  CMD_READ_LOCK_ISP                   = 0x1A
  CMD_READ_SIGNATURE_ISP              = 0x1B
  CMD_READ_OSCCAL_ISP                 = 0x1C
  CMD_SPI_MULTI                       = 0x1D

# *****************[ STK PP command constants ]*******************************

  CMD_ENTER_PROGMODE_PP               = 0x20
  CMD_LEAVE_PROGMODE_PP               = 0x21
  CMD_CHIP_ERASE_PP                   = 0x22
  CMD_PROGRAM_FLASH_PP                = 0x23
  CMD_READ_FLASH_PP                   = 0x24
  CMD_PROGRAM_EEPROM_PP               = 0x25
  CMD_READ_EEPROM_PP                  = 0x26
  CMD_PROGRAM_FUSE_PP                 = 0x27
  CMD_READ_FUSE_PP                    = 0x28
  CMD_PROGRAM_LOCK_PP                 = 0x29
  CMD_READ_LOCK_PP                    = 0x2A
  CMD_READ_SIGNATURE_PP               = 0x2B
  CMD_READ_OSCCAL_PP                  = 0x2C    

  CMD_SET_CONTROL_STACK               = 0x2D

# *****************[ STK HVSP command constants ]*****************************

  CMD_ENTER_PROGMODE_HVSP             = 0x30
  CMD_LEAVE_PROGMODE_HVSP             = 0x31
  CMD_CHIP_ERASE_HVSP                 = 0x32
  CMD_PROGRAM_FLASH_HVSP              = 0x33
  CMD_READ_FLASH_HVSP                 = 0x34
  CMD_PROGRAM_EEPROM_HVSP             = 0x35
  CMD_READ_EEPROM_HVSP                = 0x36
  CMD_PROGRAM_FUSE_HVSP               = 0x37
  CMD_READ_FUSE_HVSP                  = 0x38
  CMD_PROGRAM_LOCK_HVSP               = 0x39
  CMD_READ_LOCK_HVSP                  = 0x3A
  CMD_READ_SIGNATURE_HVSP             = 0x3B
  CMD_READ_OSCCAL_HVSP                = 0x3C

# *****************[ STK status constants ]***************************

# Success
  STATUS_CMD_OK                       = 0x00

# Warnings
  STATUS_CMD_TOUT                     = 0x80
  STATUS_RDY_BSY_TOUT                 = 0x81
  STATUS_SET_PARAM_MISSING            = 0x82

# Errors
  STATUS_CMD_FAILED                   = 0xC0
  STATUS_CKSUM_ERROR                  = 0xC1
  STATUS_CMD_UNKNOWN                  = 0xC9

# *****************[ STK parameter constants ]***************************
  PARAM_BUILD_NUMBER_LOW              = 0x80
  PARAM_BUILD_NUMBER_HIGH             = 0x81
  PARAM_HW_VER                        = 0x90
  PARAM_SW_MAJOR                      = 0x91
  PARAM_SW_MINOR                      = 0x92
  PARAM_VTARGET                       = 0x94
  PARAM_VADJUST                       = 0x95
  PARAM_OSC_PSCALE                    = 0x96
  PARAM_OSC_CMATCH                    = 0x97
  PARAM_SCK_DURATION                  = 0x98
  PARAM_TOPCARD_DETECT                = 0x9A
  PARAM_STATUS                        = 0x9C
  PARAM_DATA                          = 0x9D
  PARAM_RESET_POLARITY                = 0x9E
  PARAM_CONTROLLER_INIT               = 0x9F

# *****************[ STK answer constants ]***************************

  ANSWER_CKSUM_ERROR                  = 0xB0

  def __init__(self, serialport):
    self.ser = serial.Serial(serialport, baudrate=115200)
    self.comms = _CommsEngine(self.ser)
    self.seq = 0

  def sign_on(self):
    resp = self.comms.sendrecv(self.seq, [self.CMD_SIGN_ON], 0.2)
    print resp[3:]

class _CommsEngine():
  def __init__(self, ser): 
    self.ser = ser
    self.bytes = bytearray()

  def sendrecv(self, seq, data, timeout = 1):
    self.numerrs = 0
    self.seqNum = seq
    self.ser.setTimeout(timeout)
    bytes = bytearray()
    bytes += bytearray([0x1B])
    bytes += bytearray([seq])
    size = len(data)
    bytes += bytearray([ (size >> 8) & 0x00ff ])
    bytes += bytearray([ size & 0x00ff ])
    bytes += bytearray([0x0E])
    bytes += bytearray(data)
    checksum = reduce( lambda x, y: x^y, bytes )
    bytes += bytearray([checksum])
    self.ser.write(bytes)
    return self.start()

  def start(self):
    self.numerrs += 1
    if self.numerrs > 10:
      raise IOError("Too many errors. Aborting.")
    bytes = bytearray(self.ser.read())
    if len(bytes) < 1:
      raise IOError("Message timed out.")
    if bytes[0] != 0x1b:
      self.start()
    else:
      self.bytes += bytes
      self.getSeqNumber()
      return self.data

  def getSeqNumber(self):
    bytes = bytearray(self.ser.read())
    if len(bytes) < 1:
      raise IOError("Message timed out.")
    if bytes[0] != self.seqNum:
      self.start()
    else:
      self.bytes += bytes
      self.getMessageSize()

  def getMessageSize(self):
    bytes = bytearray(self.ser.read(2))
    if len(bytes) < 2:
      raise IOError("Message timed out.")
    else:
      self.size = bytes[0]<<8 | bytes[1]
      self.bytes += bytes
      self.getToken()

  def getToken(self):
    bytes = bytearray(self.ser.read())
    if len(bytes) < 1:
      raise IOError("Message timed out.")
    if bytes[0] != 14:
      self.start()
    else:
      self.bytes += bytes
      self.getData()

  def getData(self):
    self.data = bytearray(self.ser.read(self.size))
    if len(self.data) < self.size:
      raise IOError("Message timed out.")
    else:
      self.bytes += self.data
      self.getChecksum()

  def getChecksum(self):
    bytes = bytearray(self.ser.read())
    if len(bytes) < 1:
      raise IOError("Message timed out.")
    else:
      sum = reduce(lambda x, y: x^y, self.bytes)
      if sum != bytes[0]:
        self.start()
      


class HexFile():
  def __init__(self):
    self.data = bytearray(0)
    self.extaddr = 0 # Extended address (Upper byte of address)

  def fromIHexFile(self, filename, offset=0):
    """Open and parse an Intel hex file."""
    f = open(filename, 'r')
    self.fromIHexString(f.read(), offset)
    f.close()

  def fromIHexString(self, string, offset=0):
    """Parse an Intel hex string."""
    for substr in string.split('\n'):
      self._parseLine(substr, offset)

  def toIHexString(self, blocksize=0x10):
    """Generate Intel hex string"""
    currentAddr = 0
    extAddr = 0
    hexstring = ''
    while currentAddr < len(self.data):
      if (currentAddr & 0xffff == 0) and (currentAddr > 0):
        extAddr+=1
        hexline = ':02000004{:04X}'.format(extAddr)
        hexline += self._calculateChecksum(hexline[1:])
        hexstring += hexline + '\n'
      hexstring += self._toIHexLine(currentAddr, blocksize)
      currentAddr += blocksize
    hexstring += ':00000001FF\n'
    return hexstring

  def _toIHexLine(self, address, blocksize):
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
  s = STK500("/dev/ttyACM0")
  s.sign_on()
  """
  h = HexFile()
  h.fromIHexFile('dof.hex')
  h.fromIHexFile('bootloader.hex')
  print h.toIHexString(blocksize=0x20)
  """
