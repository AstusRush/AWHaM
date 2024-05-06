from AGeLib import *
import sys, os, typing, ast

class ModListItem(AGeWidgets.TightGridWidget):
    def __init__(self, parent, modData) -> None:
        super().__init__(parent)
        self.addWidget(QtWidgets.QLabel(modData["name"]))

class ModListWidget(AGeWidgets.ListWidget):
    def __init__(self, parent, mainWindow):
        #type: (AWHaMWindow,AWHaMWindow) -> None
        self.MainWindow = mainWindow
        super().__init__(parent)
        self.loadModList()
        self.setDragDropMode(AGeWidgets.ListWidget.DragDropMode.InternalMove)
    
    def loadModListFromWorkshopFolder(self):
        mod_folders = [name for name in os.listdir(self.MainWindow.WHModFolder) if os.path.isdir(os.path.join(self.MainWindow.WHModFolder, name))]
        self.clear()
        for mod in mod_folders:
            item = QtWidgets.QListWidgetItem(self)
            self.addItem(item)
            row = ModListItem(mod)
            item.setSizeHint(row.minimumSizeHint())
            self.setItemWidget(item, row)
    
    def loadModList(self):
        try:
            mods = self.MainWindow.parseModFile()
            self.clear()
            for mod in mods:
                item = QtWidgets.QListWidgetItem(self)
                self.addItem(item)
                row = ModListItem(self, mod)
                item.setSizeHint(row.minimumSizeHint())
                self.setItemWidget(item, row)
        except:
            NC(1,"Could not load mod list", exc=True)

class AWHaMWindow(AWWF):
    def __init__(self):
        super().__init__()
        
        self.setupPaths()
        
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
        
        # Overload
        self.ModListWidget = ModListWidget(self, self)
        self.ModListWidget.setObjectName("ModListWidget")
        self.TabWidget.addTab(self.ModListWidget,"Mod List")
    
    def setupPaths(self): #TODO: Windows and dynamic selection
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
    
    def parseModFile(self):
        with open(self.WHModFile) as file:
            data = file.read()
        data = data.replace("false", "False")
        data = data.replace("true", "True")
        data = ast.literal_eval(data)
        return data

if __name__ == "__main__":
    AGeQuick.QuickSetup(AWHaMWindow, "Astus' TW:WH3 Mod Manager")
