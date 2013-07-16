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

    # Set up known serial ports
    self.serialPorts = _getSerialPorts()
    self.serialPorts.sort()
   
    self.mainSizer = wx.BoxSizer(wx.VERTICAL)

    # Populate "Dongle Management" area
    box = wx.StaticBox(self, -1, "Dongle Management")
    bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)
    hsizer = wx.BoxSizer(wx.HORIZONTAL)
    hsizer.Add(wx.StaticText(self, -1, "Dongle COM Port:"), 0, wx.ALIGN_RIGHT)
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
    hsizer.Add(wx.StaticText(self, -1, "Programmer COM Port:"), 0, wx.ALIGN_RIGHT)
    self.progComboBox = wx.ComboBox(self, 
                               -1, 
                               value=self.serialPorts[0],
                               choices=self.serialPorts, 
                               style=wx.EXPAND)
    hsizer.Add(self.progComboBox, 0, wx.EXPAND)
    bsizer.Add(hsizer, 0, wx.EXPAND)

    self.flashButton = wx.Button(self, label="Flash and Test board")    
    self.flashButton.Disable()

    bsizer.Add(self.flashButton, 0, wx.EXPAND|wx.ALL, 10)
    self.mainSizer.Add(bsizer, 0, wx.EXPAND|wx.ALL, 25)

    # Box frame for testing the board
    box = wx.StaticBox(self, -1, "Test Board")
    bsizer = wx.StaticBoxSizer(box, wx.VERTICAL)

    hbuttonsizer = wx.BoxSizer(wx.HORIZONTAL)
    self.tempIdText = wx.TextCtrl(self, -1)
    self.setTempIdButton = wx.Button(self, label="Set Temporary ID")
    hbuttonsizer.Add( wx.StaticText(self, -1, "Temporary Id:", style=wx.ALIGN_RIGHT), 0, wx.ALIGN_RIGHT)
    hbuttonsizer.Add(self.tempIdText, 0, wx.EXPAND)
    hbuttonsizer.Add(self.setTempIdButton, 0, wx.EXPAND)

    bsizer.Add(hbuttonsizer, 0, wx.EXPAND|wx.ALL, 10)
    runTestButton = wx.Button(self, label="Run Test Routine")
    bsizer.Add(runTestButton, 0, wx.EXPAND|wx.ALL, 10)

    self.mainSizer.Add(bsizer, 0, wx.EXPAND|wx.ALL, 25)

    self.SetSizer(self.mainSizer)
    self.SetAutoLayout(1)
    self.mainSizer.Fit(self)

    # Connect button handlers
    self.Bind(wx.EVT_BUTTON, self.onFlashButtonClicked, self.flashButton)

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
                            maximum=100,
                            parent=self,
                            style = wx.PD_APP_MODAL | wx.PD_ELAPSED_TIME
                            )
    programmer.programAllAsync()

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

  def onSetIDCLicked(self, event):
    pass

  def onRunTestClicked(self, event):
    pass

  def onConnectDongleClicked(self, event):
    self.dongle = barobo.Linkbot()
    try:
      print "Connecting to {0}...".format(self.dongleComboBox.GetValue())
      self.dongle.connectWithTTY(str(self.dongleComboBox.GetValue()))
      self.flashButton.Enable()
      print "Connect success"
      event.GetEventObject().Disable()
      event.GetEventObject().SetLabel("Connected.")
    except Exception as e:
      dlg = wx.MessageDialog(self, "Error connecting to dongle: {0}".format(str(e)),
          'Error', wx.OK | wx.ICON_WARNING )
      dlg.ShowModal()
      dlg.Destroy()


if __name__ == "__main__":
  app = wx.App(False)
  frame = wx.Frame(None, size=(-1, -1))
  panel = MainPanel(frame)
  frame.Show()
  app.MainLoop()
