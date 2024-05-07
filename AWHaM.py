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
        self.NameLabel = self.addWidget(ModLabel(self.Name),0,3)
        self.ActiveCB = self.addWidget(QtWidgets.QCheckBox(""),0,1)
        self.ActiveCB.setFixedSize(20,20)
        self.ActiveCB.setChecked(self.Data["active"])
        self.setToolTip(self.Data["short"])
        self.initWorkshopID()
        #self.IDLabel = self.addWidget(ModLabel(self.WorkshopID),0,4)
        self.installEventFilter(self)
        self.OrderInput.installEventFilter(self)
    
    @property
    def Order(self):
        return self.OrderInput.value()
    
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
    
    def refreshOrderDisplays(self):
        for c, i, w, d in self.enumItems():
            w.setOrderButBlockSignal(c+1)
    
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

class AWHaMWindow(AWWF):
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
        self.TabWidget.addTab(self.ModListContainer,"Mod List")
        
        self.start()
    
    def start(self):
        self.setupPaths()
        self.ModListWidget.loadModList()
    
    def applyMods(self):
        self.ModListWidget.applyMods()
        self.saveModFile(self.ModListWidget.ModData)
    
    def setupPaths(self): #TODO: Add Windows support and dynamic selection
        # Temp setup
        self.WHModFileLastUsedLog = os.path.expanduser("~/.steam/steam/steamapps/common/Total War WARHAMMER III/used_mods.txt")
        self.WHModFile = os.path.expanduser("~/.steam/steam/steamapps/compatdata/1142710/pfx/drive_c/users/steamuser/AppData/Roaming/The Creative Assembly/Launcher")
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
