#!/usr/bin/env python

"""
BaroboFirmwareLoader

A graphical utility for flashing the bootloader and firmware onto Barobo
Linkbot mainboards using the Barobo Linkbot test jig and a Pololu PGM03A
AVRISP_2 programmer.
"""

import wx
import barobo
import pystk500v2 as stk
import os
import random
import time

def _getSerialPorts():
  if os.name == 'nt':
    available = []
    for i in range(256):
      try:
        s = serial.Serial(i)
        available.append('\\\\.\\COM'+str(i+1))
        s.close()
      except Serial.SerialException:
        pass
    return available
  else:
    from serial.tools import list_ports
    return [port[0] for port in list_ports.comports()]

class MainPanel(wx.Panel):
  def __init__(self, parent):
    wx.Panel.__init__(self, parent)
    self.dongle = None
    random.seed()

    # Set up known serial ports
    self.serialPorts = _getSerialPorts()
    self.serialPorts.sort()
   
    self.mainSizer = wx.BoxSizer(wx.VERTICAL)

    # Populate "Help" and "Refresh COM Ports" buttons
    hsizer = wx.BoxSizer(wx.HORIZONTAL)
    button = wx.Button(self, label="Help")
    self.Bind(wx.EVT_BUTTON, self.onHelpClicked, button)
    hsizer.Add(button, 0, wx.EXPAND)
    button = wx.Button(self, label="Refresh COM ports")
    self.Bind(wx.EVT_BUTTON, self.onRefreshClicked, button)
    hsizer.Add(button, 0, wx.EXPAND)
    self.mainSizer.Add(hsizer, 0, wx.EXPAND|wx.ALL, 15)

    # Populate "Dongle Management" area
    box = wx.StaticBox(self, -1, "Dongle Management")
    bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
    hsizer = wx.BoxSizer(wx.HORIZONTAL)
    hsizer.Add(wx.StaticText(self, -1, "Dongle Port:"), 0, wx.ALIGN_RIGHT)
    self.dongleComboBox = wx.ComboBox(self,
        -1,
        value=self.serialPorts[0],
        choices=self.serialPorts,
        style=wx.EXPAND)
    hsizer.Add(self.dongleComboBox, 0, wx.EXPAND)
    bsizer.Add(hsizer, 0, wx.EXPAND|wx.ALL, 10)
    button = wx.Button(self, label="Connect")
    bsizer.Add(button, 0, wx.EXPAND|wx.ALL, 10)
    self.Bind(wx.EVT_BUTTON, self.onConnectDongleClicked, button)
    self.mainSizer.Add(bsizer, 0, wx.EXPAND|wx.ALL, 25)
    
    
    # Populate "Program Board" box area
    box = wx.StaticBox(self, -1, "Program Board")
    bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
    
    hsizer = wx.BoxSizer(wx.HORIZONTAL)
    hsizer.Add(wx.StaticText(self, -1, "Programmer Port:"), 0, wx.ALIGN_RIGHT)
    self.progComboBox = wx.ComboBox(self, 
                               -1, 
                               value=self.serialPorts[0],
                               choices=self.serialPorts, 
                               style=wx.EXPAND)
    hsizer.Add(self.progComboBox, 0, wx.EXPAND)
    bsizer.Add(hsizer, 0, wx.EXPAND|wx.ALL, 10)

    self.flashButton = wx.Button(self, label="Flash and Test board")    
    self.Bind(wx.EVT_BUTTON, self.onFlashButtonClicked, self.flashButton)

    bsizer.Add(self.flashButton, 0, wx.EXPAND|wx.ALL, 10)
    self.mainSizer.Add(bsizer, 0, wx.EXPAND|wx.ALL, 25)

    # Box frame for testing the board
    box = wx.StaticBox(self, -1, "Test Board")
    bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)

    hbuttonsizer = wx.BoxSizer(wx.HORIZONTAL)
    self.tempIdText = wx.TextCtrl(self, -1)
    #self.setTempIdButton = wx.Button(self, label="Set Temporary ID")
    #self.Bind(wx.EVT_BUTTON, self.onSetIDClicked, self.setTempIdButton)
    hbuttonsizer.Add( wx.StaticText(self, -1, "Temporary Id:", style=wx.ALIGN_RIGHT), 0, wx.ALIGN_RIGHT)
    hbuttonsizer.Add(self.tempIdText, 0, wx.EXPAND)
    #hbuttonsizer.Add(self.setTempIdButton, 0, wx.EXPAND)

    bsizer.Add(hbuttonsizer, 0, wx.EXPAND|wx.ALL, 10)
    runTestButton = wx.Button(self, label="Run Test Routine")
    self.Bind(wx.EVT_BUTTON, self.onRunTestClicked, runTestButton)
    bsizer.Add(runTestButton, 0, wx.EXPAND|wx.ALL, 10)

    self.mainSizer.Add(bsizer, 0, wx.EXPAND|wx.ALL, 25)

    self.SetSizer(self.mainSizer)
#self.SetAutoLayout(1)
#self.mainSizer.FitInside(self)

  def onHelpClicked(self, event):
    import subprocess
    subprocess.call(["xdg-open", "docs/BaroboFirmwareJig_UserGuide.pdf"])

  def onRefreshClicked(self, event):
    self.serialPorts = _getSerialPorts()
    self.serialPorts.sort()
    self.dongleComboBox.SetItems(self.serialPorts)
    self.progComboBox.SetItems(self.serialPorts)

  def onFlashButtonClicked(self, event):
    try:
      programmer = stk.ATmega128rfa1Programmer(self.progComboBox.GetValue())
    except Exception as e:
      dlg = wx.MessageDialog(self, 
                          'Could not connect to programmer. Please ensure that '
                          'the programmer is plugged into the computer and the '
                          'correct COM port is selected. {0}'.format(str(e)), 
                          'Error',
                          wx.OK | wx.ICON_WARNING)
      dlg.ShowModal()
      dlg.Destroy()
      return

    dlg = wx.ProgressDialog("Flashing Progress",
                            "Loading Linkbot Firmware...",
                            maximum=105,
                            parent=self,
                            style = wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME
                            )
    # Generate a random ID
    self.serialID = "{:04d}".format(random.randint(1000, 9999))
    self.tempIdText.SetValue(self.serialID)
    programmer.programAllAsync(serialID=self.serialID)

    while programmer.isProgramming():
      dlg.Update(programmer.getProgress()*100)
      wx.MilliSleep(250)

    dlg.Destroy()

    # See if there were any exceptions
    e = programmer.getLastException()
    if e:
      dlg = wx.MessageDialog(self, 
                             'Error programming board: {0}'.format(str(e)),
                             'Error',
                             wx.OK | wx.ICON_WARNING
                             )
      dlg.ShowModal()
      dlg.Destroy()

    self.onRunTestClicked(None)

  def onSetIDClicked(self, event):
    pass

  def onRunTestClicked(self, event):
    if self.dongle is None:
      dlg = wx.MessageDialog(self, 'There is currently no dongle associated with this '
          'utility. Please select and connect to a Linkbot dongle using the '
          '"Dongle Management" area above and try again.',
          'Warning',
          wx.OK|wx.ICON_WARNING)
      dlg.ShowModal()
      dlg.Destroy()
      return
    import threading
    testthread = threading.Thread(target=self.runTestRoutine)
    testthread.start()
    self.testingException = None
    dlg = wx.ProgressDialog("Testing board...",
        "Testing board...",
        parent=self,
        style=wx.PD_APP_MODAL)
    while testthread.is_alive():
      dlg.Pulse()
      time.sleep(0.25)
    dlg.Destroy()
    if self.testingException:
      dlg = wx.MessageDialog(self,
          'Testing board with ID {0} failed: {1}'.format(self.serialID, str(self.testingException)),
          'Error',
          wx.OK|wx.ICON_WARNING)
      dlg.ShowModal()
      dlg.Destroy()

  def runTestRoutine(self):
    print "Testing..."
    mybot = barobo.Linkbot()
    numtries = 10
    for i in range (numtries):
      try:
        self.serialID = self.tempIdText.GetValue()
        print "Connecting to {0}...".format(self.serialID)
        mybot.connectWithSerialID(str(self.serialID))
        break
      except Exception as e:
        if i == (numtries-1):
          dlg = wx.MessageDialog(self,
              'Could not connect wirelessly to Serial ID {0}: {1}'.format(self.serialID, str(e)),
              'Error',
              wx.OK|wx.ICON_WARNING)
          dlg.ShowModal()
          dlg.Destroy()
          return 
        else:
          pass

    try:
      for i in range(1, 4):
        mybot.setMotorPower(i, 100)
      time.sleep(1)
      for i in range(1, 4):
        mybot.setMotorPower(i, -100)
      time.sleep(1)
      mybot.stop()
      mybot.setBuzzerFrequency(220)
      mybot.setColorRGB(0xff, 0, 0)
      time.sleep(.5)
      mybot.setBuzzerFrequency(440)
      mybot.setColorRGB(0, 0xff, 0)
      time.sleep(.5)
      mybot.setBuzzerFrequency(220)
      mybot.setColorRGB(0, 0, 0xff)
      time.sleep(.5)
      mybot.setBuzzerFrequency(0)
      x, y, z = mybot.getAccelerometerData()
      if abs(x) > 0.1 or abs(y) > 0.1 or abs(1-z) > 0.1:
        raise Exception("Error: Detected anomaly in accelerometer readings: "
            "({0}, {1}, {2}). Should be (0, 0, 1)".format(x, y, z))
    except Exception as e:
      self.testingException = e
      return

  def onConnectDongleClicked(self, event):
    self.dongle = barobo.Linkbot()
    try:
      print "Connecting to {0}...".format(self.dongleComboBox.GetValue())
      self.dongle.connectWithTTY(str(self.dongleComboBox.GetValue()))
      self.dongle._setDongle()
      self.flashButton.Enable()
      print "Connect success"
      event.GetEventObject().Disable()
      event.GetEventObject().SetLabel("Connected.")
    except Exception as e:
      dlg = wx.MessageDialog(self, "Error connecting to dongle: {0}".format(str(e)),
          'Error', wx.OK | wx.ICON_WARNING )
      dlg.ShowModal()
      dlg.Destroy()
      self.dongle = None

  def onSerialComboBox(self, event):
    self.serialPorts = _getSerialPorts()
    self.serialPorts.sort()


if __name__ == "__main__":
  app = wx.App(False)
  frame = wx.Frame(None, size=(400, 600))
  panel = MainPanel(frame)
  frame.Show()
  app.MainLoop()
