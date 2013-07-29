import wx
import os
import json
import binascii
import time
import base64

register_column_mapping = {}
register_column_mapping['eip'] = 3
register_column_mapping['eax'] = 4
register_column_mapping['ebx'] = 5
register_column_mapping['ecx'] = 6
register_column_mapping['edx'] = 7
register_column_mapping['edi'] = 8
register_column_mapping['esi'] = 9
register_column_mapping['esp'] = 10
register_column_mapping['ebp'] = 11

REGISTERS = ['eip', 'eax', 'ebx', 'ecx', 'edx', 'edi', 'esi', 'esp', 'ebp']

class HexViewerFrame (wx.Frame) :
    def __init__ (self, address, data) :
        wx.Frame.__init__(self, None, wx.ID_ANY, 'Memory')
        self.data = data
        self.address = address

        self.control = wx.TextCtrl(self, style=wx.TE_MULTILINE)

        font = wx.Font(9, wx.FONTFAMILY_MODERN, wx.NORMAL, wx.FONTWEIGHT_NORMAL, False)
        self.control.SetFont(font)

        self.Show()
        self.load_step()


    def load_step (self) :
        address = self.address
        data    = self.data
        while len(data) > 0 :
            line = hex(address)[2:]

            hexchars = []
            asciichars = []
            if len(data) < 32 :
                size = len(data)
            else :
                size = 32
                hexlify = binascii.hexlify
            for i in range(size) :
                hexchars.append(hexlify(data[i]))
                if ord(data[i]) >= 32 and ord(data[i]) < 127 :
                    asciichars.append(data[i])
                else :
                    asciichars.append('.')

            line += '  ' + ' '.join(hexchars) + '  ' + ''.join(asciichars)

            self.control.AppendText(line + '\n')
            address += size
            data = data[size:]
        self.Update()



class TraceViewerFrame (wx.Frame) :
    def __init__ (self) :
        wx.Frame.__init__(self, None, wx.ID_ANY, 'Steps')

        self.index = 0

        font = wx.Font(9, wx.FONTFAMILY_MODERN, wx.NORMAL, wx.FONTWEIGHT_NORMAL, False)

        panel = wx.Panel(self, wx.ID_ANY)

        self.search_ctrl = wx.TextCtrl(panel)
        self.search_registers_button = wx.Button(panel, label="Search Registers")
        self.find_next_button = wx.Button(panel, label="Find Next")
        self.find_previous_button = wx.Button(panel, label="Find Previous")
        self.Bind(wx.EVT_BUTTON, self.onSearchRegisters, self.search_registers_button)
        self.Bind(wx.EVT_BUTTON, self.onFindNext,        self.find_next_button)
        self.Bind(wx.EVT_BUTTON, self.onFindPrevious,    self.find_previous_button)

        self.list_ctrl = wx.ListCtrl(panel,
                                     style=wx.LC_REPORT | wx.BORDER_SUNKEN)
        self.list_ctrl.SetFont(font)
        self.list_ctrl.InsertColumn(0,  'tid')
        self.list_ctrl.InsertColumn(1,  'label')
        self.list_ctrl.InsertColumn(2,  'Instruction')
        self.list_ctrl.InsertColumn(3,  'eip')
        self.list_ctrl.InsertColumn(4,  'eax')
        self.list_ctrl.InsertColumn(5,  'ebx')
        self.list_ctrl.InsertColumn(6,  'ecx')
        self.list_ctrl.InsertColumn(7,  'edx')
        self.list_ctrl.InsertColumn(8,  'edi')
        self.list_ctrl.InsertColumn(9,  'esi')
        self.list_ctrl.InsertColumn(10, 'esp')
        self.list_ctrl.InsertColumn(11, 'ebp')

        searchSizer = wx.BoxSizer(wx.HORIZONTAL)
        searchSizer.Add(self.search_ctrl, 1, wx.ALL|wx.EXPAND, 2)
        searchSizer.Add(self.search_registers_button, 0, wx.ALL|wx.EXPAND, 2)
        searchSizer.Add(self.find_next_button, 0, wx.ALL|wx.EXPAND, 2)
        searchSizer.Add(self.find_previous_button, 0, wx.ALL|wx.EXPAND, 2)

        verticalSizer = wx.BoxSizer(wx.VERTICAL)
        verticalSizer.Add(searchSizer, 0, wx.ALL|wx.EXPAND, 2)
        verticalSizer.Add(self.list_ctrl, 1, wx.ALL|wx.EXPAND, 2)
        panel.SetSizer(verticalSizer)

        filemenu = wx.Menu()
        menu_item = filemenu.Append(wx.ID_OPEN, "&Open", "Open Trace")
        self.Bind(wx.EVT_MENU, self.onOpen, menu_item)
        filemenu.AppendSeparator()
        menu_item = filemenu.Append(wx.ID_ABOUT, "&About", "Information about this program")
        self.Bind(wx.EVT_MENU, self.onAbout, menu_item)
        menu_item = filemenu.Append(wx.ID_EXIT, "E&xit", "Terminate this program")
        self.Bind(wx.EVT_MENU, self.onExit, menu_item)

        self.Bind(wx.EVT_LIST_ITEM_RIGHT_CLICK, self.onStepRightClick, self.list_ctrl)

        menuBar = wx.MenuBar()
        menuBar.Append(filemenu, "&File")
        self.SetMenuBar(menuBar)

    def loadFromJson (self, text) :
        text = text.strip()
        self.db = []

        self.list_ctrl.DeleteAllItems()
        self.index = 0

        i = 0
        print 'init db'
        for row in text.split('\n') :
            self.db.append(json.loads(row))
            i += 1
            if i & 0x7ff == 0 :
                print 'init rows', i

        i = 0
        SetStringItem = self.list_ctrl.SetStringItem

        for row in self.db :
            self.list_ctrl.InsertStringItem(self.index, "Line " + str(self.index))
            SetStringItem(self.index, 0,  str(row['thread_id']))
            SetStringItem(self.index, 1,  row['label'])
            SetStringItem(self.index, 2,  row['instruction_text'])
            SetStringItem(self.index, 3,  hex(row['eip'])[2:])
            SetStringItem(self.index, 4,  hex(row['eax'])[2:])
            SetStringItem(self.index, 5,  hex(row['ebx'])[2:])
            SetStringItem(self.index, 6,  hex(row['ecx'])[2:])
            SetStringItem(self.index, 7,  hex(row['edx'])[2:])
            SetStringItem(self.index, 8,  hex(row['edi'])[2:])
            SetStringItem(self.index, 9,  hex(row['esi'])[2:])
            SetStringItem(self.index, 10, hex(row['esp'])[2:])
            SetStringItem(self.index, 11, hex(row['ebp'])[2:])

            i += 1
            if i & 0x7ff == 0 :
                print 'display rows', i
                self.Update()
                time.sleep(0.05)

        self.db.reverse()

    def onStepRightClick (self, event) :
        self.selected_step_index = event.GetIndex()

        menu = wx.Menu()
        menu_item = menu.Append(0, 'View Stack')

        self.PopupMenu(menu, event.GetPoint())
        self.Bind(wx.EVT_MENU, self.showStack, menu_item)
        menu.Destroy()

    def onSearchRegisters (self, event) :
        for i in range(self.list_ctrl.GetItemCount()) :
            self.list_ctrl.SetItemBackgroundColour(i, wx.Colour(255, 255, 255, 255))

        register_value = int(self.search_ctrl.GetValue(), 16)

        print 'register_value', register_value

        i = 0
        global REGISTERS
        for i in range(len(self.db)) :
            for r in REGISTERS :
                if self.db[i][r] == register_value :
                    self.list_ctrl.SetItemBackgroundColour(i, wx.Colour(255, 127, 0, 64))
            i += 1
            if i & 0x7ff == 0 :
                print 'search rows', i

    def onFindNext (self, event) :
        #find selected item
        selected = self.list_ctrl.GetFirstSelected()
        selected += 1

        register_value = int(self.search_ctrl.GetValue(), 16)

        global REGISTERS
        for i in range(selected + 1, len(self.db)) :
            for r in REGISTERS :
                if self.db[i][r] == register_value :
                    self.list_ctrl.Focus(i)
                    self.list_ctrl.Select(i)
                    return

    def onFindPrevious (self, event) :
        #find selected item
        selected = self.list_ctrl.GetFirstSelected()
        selected += 1

        register_value = int(self.search_ctrl.GetValue(), 16)

        global REGISTERS
        rrange = range(0, selected)
        rrange.reverse()
        for i in rrange :
            for r in REGISTERS :
                if self.db[i][r] == register_value :
                    self.list_ctrl.Focus(i)
                    self.list_ctrl.Select(i)
                    return

    def showStack (self, event) :
        print self.db[self.selected_step_index]
        stack_memory = base64.b64decode(self.db[self.selected_step_index]['stack_memory'])
        esp = self.db[self.selected_step_index]['esp']
        mvf = HexViewerFrame(esp - len(stack_memory), stack_memory)


    def onOpen (self, event) :
        dirname = ''
        dlg = wx.FileDialog(self, "Choose Trace File", dirname, "", "*.json", wx.OPEN)
        if dlg.ShowModal() == wx.ID_OK :
            filename = dlg.GetFilename()
            dirname = dlg.GetDirectory()

            fh = open(os.path.join(dirname, filename), 'r')
            raw = fh.read()
            fh.close()
            self.loadFromJson(raw)

        dlg.Destroy()

    def onAbout (self, event) :
        dlg = wx.MessageDialog(self, "Viewer for trace dumps", "About", wx.OK)
        dlg.ShowModal()
        dlg.Destroy()

    def onExit (self, event) :
        self.Close(True)

app = wx.App(False)
frame = TraceViewerFrame()#(None, "Test Editor")
frame.Show()

app.MainLoop()