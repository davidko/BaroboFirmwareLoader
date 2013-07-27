"""
A Python module for communicating with stk500v2 programmers, such as the Pololu
PGM03A for programming AVR chips.
"""

import serial
import threading
import time

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

  def sign_on(self):
    resp = self.comms.sendrecv([self.CMD_SIGN_ON], 0.2)
    if resp[3:] == 'AVRISP_2':
      self.programmertype = 'avrisp2'
    elif resp[3:] == 'STK500_2':
      self.programmertype = 'stk500_2'
    else:
      raise Exception("Unkown programmer type: {0}".format(resp[3:]))

  def set_parameter(self, param, value):
    resp = self.comms.sendrecv(
        [self.CMD_SET_PARAMETER, param, value])
    if resp[0] != self.CMD_SET_PARAMETER or resp[1] != self.STATUS_CMD_OK:
      raise IOError("Error setting parameter {0} to value {0}.".format(param, value))

  def get_parameter(self, param):
    resp = self.comms.sendrecv(
        [self.CMD_GET_PARAMETER, param])
    if resp[0] != self.CMD_GET_PARAMETER or resp[1] != self.STATUS_CMD_OK:
      raise IOError("Error getting parameter: {0}.".format(param))
    else:
      return resp[2]

  def osccal(self):
    resp = self.comms.sendrecv([self.CMD_OSCCAL])
    return resp[1]

  def load_address(self, address):
    addrbytes = bytearray(4)
    addrbytes[0] = (address >> 24) & 0x00ff
    addrbytes[1] = (address >> 16) & 0x00ff
    addrbytes[2] = (address >> 8) & 0x00ff
    addrbytes[3] = address & 0x00ff
    resp = self.comms.sendrecv(
        bytearray([self.CMD_LOAD_ADDRESS]) + addrbytes)
    if resp[0] != self.CMD_LOAD_ADDRESS or resp[1] != self.STATUS_CMD_OK:
      raise IOError("Error loading address.")

  def enter_progmode_isp(
      self, 
      timeout, 
      stabDelay, 
      cmdexeDelay, 
      synchLoops, 
      byteDelay, 
      pollValue, 
      pollIndex, 
      cmdbytes):
    if len(cmdbytes) != 4:
      raise Exception("Expected 4 command bytes. Got {0}.".format(len(cmdbytes)))
    resp = self.comms.sendrecv(
        bytearray(
          [
            self.CMD_ENTER_PROGMODE_ISP, 
            timeout,
            stabDelay,
            cmdexeDelay,
            synchLoops,
            byteDelay,
            pollValue,
            pollIndex
          ]
        ) + bytearray(cmdbytes), 5 )
    if resp[0] != self.CMD_ENTER_PROGMODE_ISP or resp[1] != self.STATUS_CMD_OK:
      raise IOError("Could not enter programming mode. Please make sure the "
          "board is receiving power and is correctly loaded into the programming "
          "jig.")

  def spi_multi(self, numRX, data, rxStartAddr):
    resp = self.comms.sendrecv(
        bytearray([self.CMD_SPI_MULTI, len(data), numRX, rxStartAddr]) + bytearray(data))
    if resp[0] != self.CMD_SPI_MULTI or resp[1] != self.STATUS_CMD_OK:
      raise IOError("Error executing ISP command.")
    return resp[2:-1]

  def chip_erase_isp(self, eraseDelay, pollMethod, cmdbytes):
    if len(cmdbytes) != 4:
      raise Exception("Expected 4 command bytes. Got {0}.".format(len(cmdbytes)))
    resp = self.comms.sendrecv(
        bytearray([self.CMD_CHIP_ERASE_ISP, eraseDelay, pollMethod])+bytearray(cmdbytes))
    if resp[0] != self.CMD_CHIP_ERASE_ISP or resp[1] != self.STATUS_CMD_OK:
      raise IOError("Error erasing chip.")

  def program_flash_isp(self, numbytes, mode, delay, cmd1, cmd2, cmd3, poll1, poll2, data):
    buf = bytearray([self.CMD_PROGRAM_FLASH_ISP])
    buf += bytearray([ (numbytes >> 8) & 0x00ff ])
    buf += bytearray([ numbytes & 0x00ff ])
    buf += bytearray([ mode, delay, cmd1, cmd2, cmd3, poll1, poll2])
    buf += bytearray( data )
    resp = self.comms.sendrecv(buf, timeout=5)
    if resp[0] != self.CMD_PROGRAM_FLASH_ISP or resp[1] != self.STATUS_CMD_OK:
      raise IOError("Error programming flash.")

  def read_flash_isp(self, numbytes, cmd1=0x20):
    buf = bytearray([self.CMD_READ_FLASH_ISP])
    buf += bytearray( [(numbytes >> 8) & 0x00ff, numbytes & 0x00ff, cmd1] )
    resp = self.comms.sendrecv(buf)
    if resp[0] != self.CMD_READ_FLASH_ISP or resp[1] != self.STATUS_CMD_OK:
      raise IOError("Error reading page from flash memory")
    return resp[2:-1]

  def program_eeprom_isp(self, numbytes, mode, delay, cmd1, cmd2, cmd3, poll1, poll2, data):
    buf = bytearray([self.CMD_PROGRAM_EEPROM_ISP])
    buf += bytearray([ (numbytes >> 8) & 0x00ff ])
    buf += bytearray([ numbytes & 0x00ff ])
    buf += bytearray([ mode, delay, cmd1, cmd2, cmd3, poll1, poll2])
    buf += bytearray( data )
    resp = self.comms.sendrecv(buf, timeout=5)
    if resp[0] != self.CMD_PROGRAM_EEPROM_ISP or resp[1] != self.STATUS_CMD_OK:
      raise IOError("Error programming eeprom.")

  def read_eeprom_isp(self, numbytes, cmd1=0xA0):
    buf = bytearray([self.CMD_READ_EEPROM_ISP])
    buf += bytearray( [(numbytes >> 8) & 0x00ff, numbytes & 0x00ff, cmd1] )
    resp = self.comms.sendrecv(buf)
    if resp[0] != self.CMD_READ_EEPROM_ISP or resp[1] != self.STATUS_CMD_OK:
      raise IOError("Error reading page from eeprom memory")
    return resp[2:-1]


class ATmega128rfa1Programmer(STK500):
  WORDSIZE = 2 # Word size in bytes, for addressing
  def __init__(self, serialport):
    STK500.__init__(self, serialport)
    self.progress = 0.0

  def enter_progmode_isp(
      self, 
      timeout = 0xc8, 
      stabDelay = 0x64, 
      cmdexeDelay = 0x19, 
      synchLoops = 0x20, 
      byteDelay = 0x00, 
      pollValue = 0x53, 
      pollIndex = 0x03, 
      cmdbytes = bytearray([0xac, 0x53, 0, 0])
      ):
    return STK500.enter_progmode_isp(
        self,
        timeout,
        stabDelay,
        cmdexeDelay,
        synchLoops,
        byteDelay,
        pollValue,
        pollIndex,
        cmdbytes)

  def get_signature_byte(self, byte):
    data = self.spi_multi(4, [0x30, 0, byte, 0], 0)
    return data[3]

  def check_signature(self):
    sig = 0
    for i in range(0, 3):
      sig |= self.get_signature_byte(i) << ((2-i)*8)
    #print "{:06X}".format(sig)
    if sig != 0x1ea701:
      raise IOError("Wrong signature. Expected {:06X}, got {:06X}".format(0x1ea701, sig))

  def chip_erase_isp(self):
    STK500.chip_erase_isp(self, 0x37,0x00, [0xac,0x80,0,0])

  def load_page(self, data):
    self.program_flash_isp(
        len(data), 
        mode = 0xc1,
        delay = 0x14,
        cmd1 = 0x40,
        cmd2 = 0x4c,
        cmd3 = 0x20,
        poll1 = 0,
        poll2 = 0,
        data=data)

  def load_address(self, byteaddr):
    STK500.load_address(self, byteaddr/self.WORDSIZE)

  def load_data(self, data, blocksize = 0x0100):
    size = len(data)
    currentByteAddr = 0
    while currentByteAddr < size:
      # Check to see if the page is a whole page of 0xff. If it is, no need to program it
      isblank = reduce(
          lambda x, y: True if x and y == 0xff else False,
          data[currentByteAddr:currentByteAddr+blocksize], 
          True )
      if not isblank:
        self.load_address(currentByteAddr)
        self.load_page(data[currentByteAddr:currentByteAddr+blocksize])
      currentByteAddr += blocksize
      self.progress = (float(currentByteAddr)/size) * 0.5

  def check_data(self, hexdata, blocksize = 0x0100):
    size = len(hexdata)
    self.load_address(0)
    self.mydata = bytearray()
    while len(self.mydata) < size:
      if size - len(self.mydata) >= blocksize:
        self.mydata += bytearray(self.read_flash_isp(blocksize))
      else:
        self.mydata += bytearray(self.read_flash_isp(size-len(self.mydata)))
      self.progress = (float(len(self.mydata))/size)*0.5 + 0.5
    if self.mydata != bytearray(hexdata):
      """
      for i in range(0, len(hexdata)):
        if self.mydata[i] != hexdata[i]:
          print "Mismatch at byte 0x{:04X}: 0x{:02X} - 0x{:02X}".format(i, self.mydata[i], hexdata[i])
      """
      raise Exception("Flash verification failed.")

  def write_hfuse(self, byte=0xd8):
    self.spi_multi(4, [0xac, 0xA8, 0x00, byte], 0)

  def write_lfuse(self, byte=0xef):
    self.spi_multi(4, [0xac, 0xA0, 0x00, byte], 0)

  def write_efuse(self, byte=0xff):
    self.spi_multi(4, [0xac, 0xA4, 0x00, byte], 0)

  def read_hfuse(self):
    resp = self.spi_multi(4, [0x58, 0x08, 0x00, 0x00], 0)
    return resp[3]

  def read_lfuse(self):
    resp = self.spi_multi(4, [0x50, 0x00, 0x00, 0x00], 0)
    return resp[3]

  def read_efuse(self):
    resp = self.spi_multi(4, [0x50, 0x08, 0x00, 0x00], 0)
    return resp[3]

  def programAll(self, hexfiles=['bootloader.hex','dof.hex']):
    self.sign_on()
    self.enter_progmode_isp()
    self.check_signature()
    h = HexFile()
    for f in hexfiles:
      h.fromIHexFile(f)
    self.chip_erase_isp()
    self.load_data(h)
    self.check_data(h)
    self.write_hfuse()
    self.write_lfuse()
    self.write_efuse()
    if self.serialID is not None:
      self.writeEEPROM(0x412, self.serialID)

  def _tryProgramAll(self, hexfiles=['bootloader.hex', 'dof.hex']):
    self.threadException = None
    try:
      self.programAll(hexfiles=hexfiles)
    except Exception as e:
      self.threadException = e

  def getProgress(self):
    return self.progress

  def programAllAsync(self, serialID="1234"):
    if serialID != None and len(serialID) != 4:
      raise Exception('The Serial ID must be a 4 digit alphanumeric string.')
    self.serialID=serialID
    self.thread = threading.Thread(target=self._tryProgramAll)
    self.thread.start()

  def isProgramming(self):
    return self.thread.isAlive()

  def getLastException(self):
    return self.threadException

  def writeEEPROMbyte(self, address, byte):
    self.spi_multi(4, bytearray([0xc0, (address >> 8)&0x000f, address&0x00ff, byte]), 0)
  
  def writeEEPROM(self, startaddress, bytes):
    time.sleep(0.02)
    for offset, byte in enumerate(bytes):
      self.writeEEPROMbyte(startaddress+offset, byte)
      time.sleep(0.02)

class ATmega32U4Programmer(STK500):
  WORDSIZE = 2 # Word size in bytes, for addressing
  def __init__(self, serialport):
    STK500.__init__(self, serialport)
    self.progress = 0.0

  def enter_progmode_isp(
      self, 
      timeout = 0xc8, 
      stabDelay = 0x64, 
      cmdexeDelay = 0x19, 
      synchLoops = 0x20, 
      byteDelay = 0x00, 
      pollValue = 0x53, 
      pollIndex = 0x03, 
      cmdbytes = bytearray([0xac, 0x53, 0, 0])
      ):
    return STK500.enter_progmode_isp(
        self,
        timeout,
        stabDelay,
        cmdexeDelay,
        synchLoops,
        byteDelay,
        pollValue,
        pollIndex,
        cmdbytes)

  def get_signature_byte(self, byte):
    data = self.spi_multi(4, [0x30, 0, byte, 0], 0)
    return data[3]

  def check_signature(self):
    sig = 0
    for i in range(0, 3):
      sig |= self.get_signature_byte(i) << ((2-i)*8)
    #print "{:06X}".format(sig)
    if sig != 0x1e9587:
      raise IOError("Wrong signature. Expected {:06X}, got {:06X}".format(0x1e9587, sig))

  def chip_erase_isp(self):
    STK500.chip_erase_isp(self, 0x37,0x00, [0xac,0x80,0,0])

  def load_page(self, data):
    self.program_flash_isp(
        len(data), 
        mode = 0xc1,
        delay = 0x06,
        cmd1 = 0x40,
        cmd2 = 0x4c,
        cmd3 = 0x20,
        poll1 = 0,
        poll2 = 0,
        data=data)

  def load_address(self, byteaddr):
    STK500.load_address(self, byteaddr/self.WORDSIZE)

  def load_data(self, data, blocksize = 0x0080):
    size = len(data)
    currentByteAddr = 0
    while currentByteAddr < size:
      # Check to see if the page is a whole page of 0xff. If it is, no need to program it
      isblank = reduce(
          lambda x, y: True if x and y == 0xff else False,
          data[currentByteAddr:currentByteAddr+blocksize], 
          True )
      if not isblank:
        self.load_address(currentByteAddr)
        self.load_page(data[currentByteAddr:currentByteAddr+blocksize])
      currentByteAddr += blocksize
      self.progress = (float(currentByteAddr)/size) * 0.5

  def check_data(self, hexdata, blocksize = 0x0080):
    size = len(hexdata)
    self.load_address(0)
    self.mydata = bytearray()
    while len(self.mydata) < size:
      if size - len(self.mydata) >= blocksize:
        self.mydata += bytearray(self.read_flash_isp(blocksize))
      else:
        self.mydata += bytearray(self.read_flash_isp(size-len(self.mydata)))
      self.progress = (float(len(self.mydata))/size)*0.5 + 0.5
    if self.mydata != bytearray(hexdata):
      """
      for i in range(0, len(hexdata)):
        if self.mydata[i] != hexdata[i]:
          print "Mismatch at byte 0x{:04X}: 0x{:02X} - 0x{:02X}".format(i, self.mydata[i], hexdata[i])
      """
      raise Exception("Flash verification failed.")

  def write_hfuse(self, byte=0xd9):
    self.spi_multi(4, [0xac, 0xA8, 0x00, byte], 0)

  def write_lfuse(self, byte=0xff):
    self.spi_multi(4, [0xac, 0xA0, 0x00, byte], 0)

  def write_efuse(self, byte=0xff):
    self.spi_multi(4, [0xac, 0xA4, 0x00, byte], 0)

  def read_hfuse(self):
    resp = self.spi_multi(4, [0x58, 0x08, 0x00, 0x00], 0)
    return resp[3]

  def read_lfuse(self):
    resp = self.spi_multi(4, [0x50, 0x00, 0x00, 0x00], 0)
    return resp[3]

  def read_efuse(self):
    resp = self.spi_multi(4, [0x50, 0x08, 0x00, 0x00], 0)
    return resp[3]

  def programAll(self, hexfiles=['usb.hex']):
    self.sign_on()
    self.enter_progmode_isp()
    self.check_signature()
    h = HexFile()
    for f in hexfiles:
      h.fromIHexFile(f)
    self.chip_erase_isp()
    self.load_data(h)
    self.check_data(h)
    self.write_hfuse()
    self.write_lfuse()

  def _tryProgramAll(self, hexfiles=['usb.hex']):
    self.threadException = None
    try:
      self.programAll(hexfiles=hexfiles)
    except Exception as e:
      self.threadException = e

  def getProgress(self):
    return self.progress

  def programAllAsync(self):
    self.thread = threading.Thread(target=self._tryProgramAll)
    self.thread.start()

  def isProgramming(self):
    return self.thread.isAlive()

  def getLastException(self):
    return self.threadException

  def writeEEPROMbyte(self, address, byte):
    self.spi_multi(4, bytearray([0xc0, (address >> 8)&0x000f, address&0x00ff, byte]), 0)
  
  def writeEEPROM(self, startaddress, bytes):
    time.sleep(0.02)
    for offset, byte in enumerate(bytes):
      self.writeEEPROMbyte(startaddress+offset, byte)
      time.sleep(0.02)

class _CommsEngine():
  def __init__(self, ser): 
    self.ser = ser
    self.bytes = bytearray()
    self.seqNum = 0 

  def sendrecv(self, data, timeout = 1):
    self.seqNum += 1
    self.numerrs = 0
    self.bytes = bytearray()
    self.ser.setTimeout(timeout)
    bytes = bytearray()
    bytes += bytearray([0x1B])
    bytes += bytearray([self.seqNum&0xff])
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
    if bytes[0] != (self.seqNum & 0xff):
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
        print "Checksum mismatch: expected {:02X}, got {:02X}".format(sum, bytes[0])
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
    self.extaddr = 0
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

  def __getitem__(self, index):
    return self.data[index]

  def __len__(self):
    return len(self.data)

if __name__ == '__main__':
  s = ATmega128rfa1Programmer("/dev/ttyACM0")
  s.sign_on()
  s.enter_progmode_isp()
  s.check_signature()
  s.writeEEPROM(0x412, "abcd")
  """
  h = HexFile()
#h.fromIHexFile('dof.hex')
  h.fromIHexFile('bootloader.hex')
  s.chip_erase_isp()
  s.load_data(h)
#s.check_data(h)
  s.write_hfuse()
  s.write_lfuse()
  s.write_efuse()
  print "{:02X}".format(s.read_hfuse())
  print "{:02X}".format(s.read_lfuse())
  print "{:02X}".format(s.read_efuse())
#print h.toIHexString(blocksize=0x20)
  """
