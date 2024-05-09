from AGeLib import *
import sys, os, platform
import typing
import json
import re

from PyQt5.QtCore import QEvent

class ModLabel(QtWidgets.QLabel):
    pass

class ModListItemWidget(AGeWidgets.TightGridWidget):
    def __init__(self, parent, modListWidget, modData, number, item) -> None:
        super().__init__(parent)
        self.ModListWidget:"ModListWidget" = modListWidget
        self.Item:QtWidgets.QListWidgetItem = item
        self.Data = modData
        self.Number = number
        self.Name = self.Data["name"]
        self.Order_initial = self.Data["order"]
        self.OrderInput = self.addWidget(QtWidgets.QSpinBox(self),0,0)
        self.OrderInput.setMinimum(0)
        self.OrderInput.setMaximum(9999)
        self.OrderInput.setValue(self.Order_initial)
        self.OrderInput.wheelEvent = lambda event: None
        self.OrderInput.setFixedWidth(int(App().font().pointSize()*6))
        #self.OrderInput.valueChanged.connect(lambda pos: self.reorder(pos))
        self.Picture = self.addWidget(ModLabel(),0,2)
        self.loadPicture()
        if self.Data["game"] == "warhammer3":
            self.NameLabel = self.addWidget(ModLabel(self.Name),0,3)
        else:
            self.NameLabel = self.addWidget(ModLabel(self.Data["game"]+" mod: "+self.Name),0,3)
        self.ActiveCB = self.addWidget(QtWidgets.QCheckBox(""),0,1)
        self.ActiveCB.setFixedSize(20,20)
        self.ActiveCB.setChecked(self.Data["active"])
        self.ActiveCB.stateChanged.connect(lambda _:self.setModified())
        self.setToolTip(self.Data["short"])
        self.initWorkshopID()
        #self.IDLabel = self.addWidget(ModLabel(self.WorkshopID),0,4)
        self.installEventFilter(self)
        self.OrderInput.installEventFilter(self)
    
    def setModified(self):
        self.ModListWidget.IsModified = True
    
    def toggleActive(self):
        self.Active = not self.Active
    
    @property
    def Order(self) -> int:
        return self.OrderInput.value()
    
    @property
    def Active(self) -> bool:
        return self.ActiveCB.isChecked()
    
    @Active.setter
    def Active(self, state:bool):
        self.ActiveCB.setChecked(state)
    
    @property
    def ActiveStr(self) -> bool:
        return "1" if self.ActiveCB.isChecked() else "0"
    
    def setOrderButBlockSignal(self, num):
        self.OrderInput.blockSignals(True)
        self.OrderInput.setValue(num)
        self.OrderInput.blockSignals(False)
    
    def eventFilter(self, source, event):
        # type: (QtWidgets.QWidget, QtCore.QEvent|QtGui.QKeyEvent) -> bool
        if source is self:
            if event.type() == QtCore.QEvent.FontChange:
                self.Picture.setMaximumSize(int(App().font().pointSize()*2),int(App().font().pointSize()*2))
                #self.setMinimumSize(int(App().font().pointSize()*2),int(App().font().pointSize()*2))
                self.OrderInput.setFixedWidth(int(App().font().pointSize()*6))
                self.Item.setSizeHint(self.minimumSizeHint())
        elif source is self.OrderInput:
            if event.type() == QtCore.QEvent.FocusOut:
                self.reorder(self.OrderInput.value())
            if event.type() == QtCore.QEvent.KeyPress:
                if event.key() == QtCore.Qt.Key_Return or event.key() == QtCore.Qt.Key_Enter:
                    self.reorder(self.OrderInput.value())
        return super(ModListItemWidget, self).eventFilter(source, event) # let the normal eventFilter handle the event
    
    def reorder(self, position):
        if position == 0: position = 1
        # There is no way to move an item without destroying its widget
        # except for drag and drop which I don't want to automate for this task
        # or resorting the entire list which I don't want to do
        # so I would need to generate a new widget which looks like this:
        """
        self.ModListWidget.takeItem(self.ModListWidget.row(self.Item))
        self.ModListWidget.insertItem(position-1, self.Item)
        newWidget = ModListItemWidget(self.ModListWidget, self.ModListWidget, self.Data, self.Number, self.Item)
        self.ModListWidget.setItemWidget(self.Item, newWidget)
        self.ModListWidget.refreshOrderDisplays()
        self.ModListWidget.setCurrentItem(self.Item)
        """
        # I should probably use a QListView instead a QListWidget but I am too stubborn...
        # So instead I will use the sort trick
        self.setOrderButBlockSignal(0)
        self.ModListWidget.prepareInsert(position)
        self.setOrderButBlockSignal(position)
        self.ModListWidget.sortItems()
        self.ModListWidget.refreshOrderDisplays()
        
    
    def initWorkshopID(self):
        try:
            self.WorkshopID = re.split("/1142710/", self.Data["packfile"])[1]
            self.WorkshopID = re.split("/", self.WorkshopID)[0]
        except:
            self.WorkshopID = "N/A"
    
    def loadPicture(self):
        self.Picture.setMaximumSize(int(App().font().pointSize()*2),int(App().font().pointSize()*2))
        try:
            pic = QtGui.QPixmap()
            picPath:str = self.Data["packfile"]
            if platform.system() == "Linux" : picPath = picPath.lstrip("Z:")
            picPath = picPath.rstrip(".pack")+".png"
            if pic.load(picPath):
                self.Picture.setPixmap(pic)
                self.Picture.setScaledContents(True)
        except:
            NC(2,f"Could Not load Picture for mod '{self.Name}'")

class ModListItem(QtWidgets.QListWidgetItem):
    def __lt__(self, other):
        return self.data(103).Order < other.data(103).Order

class ModListWidget(AGeWidgets.ListWidget):
    def __init__(self, parent, mainWindow):
        #type: (AWHaMWindow,AWHaMWindow) -> None
        self.MainWindow = mainWindow
        super().__init__(parent)
        self.setDragDropMode(AGeWidgets.ListWidget.DragDropMode.InternalMove)
        self.model().rowsMoved.connect(lambda: self.refreshOrderDisplays())
        self.setAutoScrollMargin(32)
        self.IsModified = False
        self.itemDoubleClicked.connect(lambda i: i.data(103).toggleActive())
    
    def refreshOrderDisplays(self):
        for c, i, w, d in self.enumItems():
            w.setOrderButBlockSignal(c+1)
        self.IsModified = True
    
    def prepareInsert(self, pos):
        for c, i, w, d in self.enumItems():
            if w.Order >= pos:
                w.setOrderButBlockSignal(w.Order+1)
    
    def loadModListFromWorkshopFolder(self):
        mod_folders = [name for name in os.listdir(self.MainWindow.WHModFolder) if os.path.isdir(os.path.join(self.MainWindow.WHModFolder, name))]
        self.clear()
        for mod in mod_folders:
            item = QtWidgets.QListWidgetItem(self)
            self.addItem(item)
            row = ModListItemWidget(mod)
            item.setSizeHint(row.minimumSizeHint())
            self.setItemWidget(item, row)
    
    def loadModList(self):
        try:
            mods = self.MainWindow.loadModFile()
            self.ModData = mods
            self.clear()
            for number, mod in enumerate(mods):
                item = ModListItem(self)
                item.setData(101, mod["order"])
                item.setData(102, mod["name"])
                self.addItem(item)
                widget = ModListItemWidget(self, self, mod, number, item)
                item.setData(103, widget)
                item.setSizeHint(widget.minimumSizeHint())
                self.setItemWidget(item, widget)
            self.sortItems()
        except:
            NC(1, "Could not load mod list", exc=True)
    
    def itemWidget(self, *args, **kwargs) -> ModListItemWidget:
        return super().itemWidget(*args, **kwargs)
    
    def enumItems(self):
        for c in range(self.count()):
            i = self.item(c)
            w = self.itemWidget(i)
            d = self.ModData[w.Number]
            yield c, i, w, d
    
    def applyMods(self):
        print("Mods:")
        for c, i, w, d in self.enumItems():
            if not d["name"] == w.Name:
                name = d["name"]
                raise Exception(f"Mod order mismatch. Can not proceed safely. Num: {w.Number}, expected name '{name}' but got '{w.Name}'")
            self.ModData[w.Number]["order"] = c+1
            self.ModData[w.Number]["active"] = w.ActiveCB.isChecked()
            print(c+1,w.ActiveCB.isChecked(),w.Name)
        print()
    
    def checkIfModInstalled(self, ID):
        if ID == "N/A": return False
        for c, i, w, d in self.enumItems():
            if w.WorkshopID == ID:
                return True
        return False
    
    def deactivateAll(self, shift=0):
        for _, _, w, _ in self.enumItems():
            if shift: w.setOrderButBlockSignal(w.Order+shift)
            w.Active = False
    
    def applyModOrderFromIDs(self, IDs, warnMissing=True):
        """
        Takes list of pairs as Steam WS ID and a str "1" or "0" for activation status.\n
        Applies the mod order (order of entries in list) and activation status.\n
        Moves all other mods below and deactivates them.\n
        If warnMissing a warning notification is send to the user for each mod that is not found.
        """
        self.deactivateAll(len(IDs)+10) # +10 unnecessary but better save than sorry
        for i, ID in enumerate(IDs):
            for _, _, w, _ in self.enumItems():
                if w.WorkshopID == ID[0]:
                    w.setOrderButBlockSignal(i+1)
                    w.Active = ID[1] == "1"
                    break
            else:
                if warnMissing: NC(1,f"Mod with Steam Workshop ID {ID} was requested but could not be found! This should never happen! The other mods will still be sorted since the process has already started.")
        self.sortItems()

class AWHaMWindow(AWWF):
    #TODO: On close ask user if they want to apply mod list
    #TODO: Only ask user if there are unapplied changes to the mod setup
    def __init__(self):
        super().__init__()
        
        # UI
        self.TopBar.init(IncludeFontSpinBox=True,IncludeErrorButton=True,IncludeAdvancedCB=True)
        self.setWindowTitle("Astus' TW:WH3 Mod Manager")
        self.StandardSize = (900, 500)
        self.resize(*self.StandardSize)
        self.setWindowIcon(QtWidgets.QApplication.style().standardIcon(QtWidgets.QStyle.SP_ComputerIcon))
        
        self.TabWidget = AGeWidgets.MTabWidget(self)
        self.setCentralWidget(self.TabWidget)
        
        self.TabWidget.setCornerWidget(self.TopBar, QtCore.Qt.TopRightCorner)
        self.TopBar.setVisible(True)
        #self.TabWidget.tabBar().setUsesScrollButtons(True)
        self.TopBar.setMinimumHeight(self.MenuBar.minimumHeight())
        self.TopBar.CloseButton.setMinimumHeight(self.MenuBar.minimumHeight())
        self.MenuBar.setVisible(False)
        self.setMenuBar(None)
        
        #self.ApplyButton = AGeWidgets.Button(self,"Apply and Save",self.applyMods)
        #self.TopBar.layout().addWidget(self.ApplyButton, 0, 1, 1, 1,QtCore.Qt.AlignRight)
        
        # ModList
        self.ModListContainer = AGeWidgets.TightGridWidget(self,False)
        self.ModListContainer.layout().setSpacing(0)
        self.ModListWidget = self.ModListContainer.addWidget(ModListWidget(self, self), 0,0)
        self.ModListButtonContainer = self.ModListContainer.addWidget(AGeWidgets.TightGridWidget(self,False), 1,0)
        self.ApplyButton = self.ModListButtonContainer.addWidget(AGeWidgets.Button(self,"Apply and Save",self.applyMods), 0,10)
        self.ShareButton = self.ModListButtonContainer.addWidget(AGeWidgets.Button(self,"Share",self.shareMods), 0,9)
        self.ShareButton.setToolTip("Copies a list of all active mods to the clipboard.\nPaste this into the chat of your choice so that your friends can copy it!")
        self.ModSetSelect = self.ModListButtonContainer.addWidget(QtWidgets.QComboBox(self), 0,0)
        self.LoadFromClipboardButton = self.ModListButtonContainer.addWidget(AGeWidgets.Button(self,"Load from Clipboard",self.loadModsFromClipboard), 0,8)
        self.TabWidget.addTab(self.ModListContainer,"Mod List")
        
        self.start()
    
    def close(self) -> bool:
        #NOTE: This only works when using the window's red x to close it; alt+F4 and similar methods will not trigger this method
        if self.ModListWidget.IsModified:
            msgBox = QtWidgets.QMessageBox(self)
            msgBox.setText("Unsaved Changes")
            msgBox.setInformativeText("There seem to be unapplied changes.\nDo you want to apply those changes or discard them?")
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Apply | QtWidgets.QMessageBox.Discard | QtWidgets.QMessageBox.Cancel)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.Apply)
            option = msgBox.exec()
            if option == QtWidgets.QMessageBox.Apply:
                self.applyMods()
            elif option == QtWidgets.QMessageBox.Cancel:
                return False
        return super().close()
    
    def start(self):
        self.setupPaths()
        self.ModListWidget.loadModList()
        self.init_modSetSelect()
    
    def init_modSetSelect(self):
        self.ModSetSelect.setEditable(False)
        self.ModSetSelect.wheelEvent = lambda event: None
        self.ModSetSelect.textActivated.connect(lambda text: self.modSetSelect(text))
        self.loadModSetList()
    
    def loadModSetList(self, current="Select mod set to load..."):
        self.ModSetSelect.clear()
        self.ModSetSelect.addItems(["Select mod set to load...","Vanilla","SAVE AS NEW"])
        files:typing.List[str] = [name.rstrip(".AWHaMSet") for name in os.listdir(self.ModSetStoragePath) if os.path.isfile(os.path.join(self.ModSetStoragePath, name))]
        self.ModSetSelect.addItems(files)
        self.ModSetSelect.setCurrentText(current)
    
    def modSetSelect(self, text:str):
        if text=="Select mod set to load...":
            return
        elif text=="Vanilla":
            self.ModListWidget.deactivateAll()
        elif text=="SAVE AS NEW":
            try:
                name = QtWidgets.QInputDialog.getText(self,"Mod Set Name","What should the mod set be called?\n"\
                                                        "NOTE: It must be a valid filename cause I am currently too lazy to implement a more complex system.\n"\
                                                        "So only use ASCII numbers and letters and space and underscore to be on the save side.")[0].strip()
                if name is None or name == "":
                    NC(2,"saving mod set has been cancelled")
                    return
                modSetData = "TW:WH3 Mod List:"
                for c, i, w, d in self.ModListWidget.enumItems():
                    modSetData += f"\n{w.WorkshopID}:{w.ActiveStr}: {w.Name}"
                with open(os.path.join(self.ModSetStoragePath, name+".AWHaMSet"),"w") as file:
                    file.write(modSetData)
            except:
                NC(1,"Could not save modset!",exc=True)
            else:
                self.loadModSetList(name)
        else:
            try:
                with open(os.path.join(self.ModSetStoragePath, text+".AWHaMSet"),"r") as file:
                    self.loadMods(file.read(), skipMissing=False, skipNoID=True)
            except:
                NC(1,"Could not load modset!",exc=True)
    
    def shareMods(self):
        try:
            s = "TW:WH3 Mod List:"
            for c, i, w, d in self.ModListWidget.enumItems():
                if w.Active and w.Data["game"] == "warhammer3":
                    s += f"\n{w.WorkshopID}:{w.ActiveStr}: {w.Name}"
            QtWidgets.QApplication.clipboard().setText(s)
        except:
            NC(2,"Could not copy mod list to clipboard",exc=sys.exc_info())
        else:
            NC(3,"Mods list is now in your clipboard!\nPaste this into the chat of your choice so that your friends can copy it!",DplStr="Now Paste into Chat!")
    
    def loadModsFromClipboard(self):
        s = QtWidgets.QApplication.clipboard().text()
        if not s.startswith("TW:WH3 Mod List:\n"):
            NC(2,"The content of the clipboard seems invalid.\nIt should start with \"TW:WH3 Mod List:\"",DplStr="Invalid Clipboard")
            return
        self.loadMods(s)
    
    def loadMods(self, text:str, skipMissing=False, skipNoID=False):
        try:
            s:str = text
            if not s.startswith("TW:WH3 Mod List:\n"):
                NC(2,"The content of the modset seems invalid.\nIt should start with \"TW:WH3 Mod List:\"",DplStr="Invalid modset")
                return
            mods = s.splitlines()[1:]
            NotInstalled = []
            for i in mods:
                if skipNoID and i.split(":")[0] == "N/A": continue
                if not self.ModListWidget.checkIfModInstalled(i.split(":")[0]):
                    NotInstalled.append(i)
            if NotInstalled and not skipMissing:
                NC(2,"The following mods are not installed, thus the modset can not be applied (Note: mods are searched by Steam Workshop ID):\n"+"\n".join(NotInstalled),DplStr="Mods Missing")
                return
            IDs = [i.split(":")[0:2] for i in mods]
            self.ModListWidget.applyModOrderFromIDs(IDs)
            #for c, i, w, d in self.ModListWidget.enumItems():
            #    if w.Active:
            #        s += f"\n{w.WorkshopID}: {w.Name}"
            #QtWidgets.QApplication.clipboard().setText(s)
        except:
            NC(3,"Could not apply mods",exc=sys.exc_info())
    
    def applyMods(self):
        self.ModListWidget.applyMods()
        self.saveModFile(self.ModListWidget.ModData)
        self.ModListWidget.IsModified = False
    
    def setupPaths(self):
        self.AWHaMPath = os.path.join(App().AGeLibPath,"AWHaM")
        os.makedirs(self.AWHaMPath,exist_ok=True)
        self.ModSetStoragePath = os.path.join(self.AWHaMPath,"Mod Sets")
        os.makedirs(self.ModSetStoragePath,exist_ok=True)
        
        #self.WHModFileLastUsedLog = os.path.expanduser("~/.steam/steam/steamapps/common/Total War WARHAMMER III/used_mods.txt")
        if platform.system() == "Linux":
            self.WHModFile = os.path.expanduser("~/.steam/steam/steamapps/compatdata/1142710/pfx/drive_c/users/steamuser/AppData/Roaming/The Creative Assembly/Launcher")
        else:
            self.WHModFile = os.path.expanduser(r"~\AppData\Roaming\The Creative Assembly\Launcher")
        if not os.path.isdir(self.WHModFile):
            msgBox = QtWidgets.QMessageBox(self)
            msgBox.setText("Please Locate Path")
            msgBox.setInformativeText(  "The mod info file is not in the usual location.\nPlease locate it yourself.\nIt should normally be in\nUSERNAME\\AppData\\Roaming\\The Creative Assembly\\Launcher\n"\
                                        "Please only select the folder \"Launcher\"\nA file dialogue will open once you click ok.\n"\
                                        "Currently the selected path will not be saved for the next session. Sorry for the inconvenience. I will get around to save the selected location eventually...") #TODO: Save selected path!
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msgBox.exec()
            self.WHModFile = QtWidgets.QFileDialog.getExistingDirectory(self,"Please Locate Directory \"The Creative Assembly\\Launcher\"")
        folders:typing.List[str] = [name for name in os.listdir(self.WHModFile) if os.path.isfile(os.path.join(self.WHModFile, name))]
        print(folders)
        for i in folders:
            if i.endswith("-moddata.dat"):
                self.WHModFile = os.path.join(self.WHModFile,i)
                break
        print(self.WHModFile)
        self.WHModFolder = os.path.expanduser("~/.steam/steam/steamapps/workshop/content/1142710/")
    
    def loadModFile(self):
        with open(self.WHModFile) as file:
            data = json.load(file)
        return data
    
    def saveModFile(self, data):
        dataStr = json.dumps(data)
        with open(self.WHModFile,"w") as file:
            file.write(dataStr)

if __name__ == "__main__":
    AGeQuick.QuickSetup(AWHaMWindow, "Astus' TW:WH3 Mod Manager")
