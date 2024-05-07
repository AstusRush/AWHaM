from AGeLib import *
import sys, os, platform
import typing
#import ast
import json

from PyQt5.QtCore import QEvent

class ModLabel(QtWidgets.QLabel):
    pass

class ModListItemWidget(AGeWidgets.TightGridWidget):
    def __init__(self, parent, modListWidget, modData, number, item) -> None:
        super().__init__(parent)
        self.ModListWidget = modListWidget
        self.Item:QtWidgets.QListWidgetItem = item
        self.Data = modData
        self.Number = number
        self.Name = self.Data["name"]
        self.Order = self.Data["order"]
        self.Picture = self.addWidget(ModLabel(),0,1)
        self.loadPicture()
        self.NameLabel = self.addWidget(ModLabel(self.Name),0,3)
        self.ActiveCB = self.addWidget(QtWidgets.QCheckBox(""),0,0)
        self.ActiveCB.setFixedSize(20,20)
        self.ActiveCB.setChecked(self.Data["active"])
        self.setToolTip(self.Data["short"])
        self.installEventFilter(self)
    
    def eventFilter(self, source, event):
        # type: (QtWidgets.QWidget, QtCore.QEvent|QtGui.QKeyEvent) -> bool
        if event.type() == QtCore.QEvent.FontChange:
            self.Picture.setMaximumSize(int(App().font().pointSize()*2),int(App().font().pointSize()*2))
            #self.setMinimumSize(int(App().font().pointSize()*2),int(App().font().pointSize()*2))
            self.Item.setSizeHint(self.minimumSizeHint())
        return super(ModListItemWidget, self).eventFilter(source, event) # let the normal eventFilter handle the event
    
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
        return self.data(101) < other.data(101)

class ModListWidget(AGeWidgets.ListWidget):
    def __init__(self, parent, mainWindow):
        #type: (AWHaMWindow,AWHaMWindow) -> None
        self.MainWindow = mainWindow
        super().__init__(parent)
        self.setDragDropMode(AGeWidgets.ListWidget.DragDropMode.InternalMove)
    
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
                row = ModListItemWidget(self, self, mod, number, item)
                item.setSizeHint(row.minimumSizeHint())
                self.setItemWidget(item, row)
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
