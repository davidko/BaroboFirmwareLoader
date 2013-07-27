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
    """
    button = wx.Button(self, label="Help")
    self.Bind(wx.EVT_BUTTON, self.onHelpClicked, button)
    hsizer.Add(button, 0, wx.EXPAND)
    """
    button = wx.Button(self, label="Refresh COM ports")
    self.Bind(wx.EVT_BUTTON, self.onRefreshClicked, button)
    hsizer.Add(button, 0, wx.EXPAND)
    self.mainSizer.Add(hsizer, 0, wx.EXPAND|wx.ALL, 15)

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

    self.flashButton = wx.Button(self, label="Flash Linkbot USB board")    
    self.Bind(wx.EVT_BUTTON, self.onFlashButtonClicked, self.flashButton)

    bsizer.Add(self.flashButton, 0, wx.EXPAND|wx.ALL, 10)
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
      programmer = stk.ATmega32U4Programmer(self.progComboBox.GetValue())
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
      return

if __name__ == "__main__":
  app = wx.App(False)
  frame = wx.Frame(None, size=(400, 300))
  panel = MainPanel(frame)
  frame.Show()
  app.MainLoop()
