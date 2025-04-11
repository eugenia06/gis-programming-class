from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.core import QgsProject, QgsPoint
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QDialog, QListWidget, QMessageBox

import matplotlib.pyplot
import os.path
from .resources import *
from .mod_layer_dialog_base import Ui_mod_layer_dialog_base
from matplotlib.colors import ListedColormap

class mod_layer:
    """QGIS Plugin Implementation."""
    def __init__(self, iface):
        """Constructor."""
        self.iface = iface
        self.plugin_dir = os.path.dirname(__file__)
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'mod_layer_{}.qm'.format(locale))
        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)
        self.actions = []
        self.menu = self.tr(u'&Mod Layer')
        self.first_start = None
        
    def tr(self, message):
        """Get the translation for a string using Qt translation API."""
        return QCoreApplication.translate('ModLayer', message)

    def add_action(self, icon_path, text, callback, enabled_flag=True,
                   add_to_menu=True, add_to_toolbar=True,
                   status_tip=None, whats_this=None, parent=None):
        """Add a toolbar icon to the toolbar."""
        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)
        if status_tip is not None:
            action.setStatusTip(status_tip)
        if whats_this is not None:
            action.setWhatsThis(whats_this)
        if add_to_toolbar:
            self.iface.addToolBarIcon(action)
        if add_to_menu:
            self.iface.addPluginToMenu(self.menu, action)
        self.actions.append(action)

    def run(self):
        """Run method that performs all the real work."""
        selected_layers = self.select_layers()
        if selected_layers is None or len(selected_layers) < 1:
            return
        try:
            self.build_3d_model(selected_layers)
        except Exception as e:
            QMessageBox.critical(self.iface.mainWindow(), "Ошибка", str(e))

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""
        icon_path = ':/plugins/mod_layer/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Построить график'),
            callback=self.run,
            parent=self.iface.mainWindow()  
        )

    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(self.tr(u'&Mod Layer'), action)
            self.iface.removeToolBarIcon(action)
            
    def select_layers(self):
        """Выбор слоёв."""
        layers = QgsProject.instance().layerTreeRoot().children()
        layer_names = [layer.layer().name() for layer in layers if layer.layer().isSpatial()]
        dialog = QDialog(self.iface.mainWindow()) # выбор слоёв
        ui = Ui_mod_layer_dialog_base() 
        ui.setupUi(dialog) 
        ui.listWidget.addItems(layer_names) 
        ui.listWidget.setSelectionMode(QListWidget.MultiSelection) 
        if dialog.exec_() == QDialog.Accepted:
            selected_layers = ui.listWidget.selectedItems()
            selected_layers_objects = [
               layer.layer() for layer in layers 
               if layer.layer().name() in [item.text() for item in selected_layers]
            ]
            return selected_layers_objects
        else:
            return None

    def build_3d_model(self, layers):
        """Построить модель для слоёв с поддержкой точек как 2D, так и 3D."""
        color = ["#79d6fe", "#b70421", "#a4ee25", "#ed4115", "#652fea", "#4abe5b", "#fe589e", "#a42dd9", "#5098c0"] 
        colors = ListedColormap(color[:len(layers)])
        o = matplotlib.pyplot.figure(figsize=(11, 8))
        grafik = o.add_subplot(111, projection='3d') # создание графика

        for i, layer in enumerate(layers): # enumerate - позволяет проходиться в ходе цикла и по слоям и по их порядковому номеру
            features = layer.getFeatures()
            x, y, z = [], [], []
            for feature in features: # обход всех точек
                geom = feature.geometry()
                if geom.isMultipart():
                    points = geom.asMultiPoint() #для обработки "множеств" точек (сгруппированных объектов)
                    for point in points:
                        if isinstance(point, QgsPoint):
                            x.append(point.x())
                            y.append(point.y())
                            z.append(point.z() if point.hasZ() else 0) # обработка точек с 3-мя координатами [x, y, z]
                        else: # обработка точек с 2-мя координатами
                            x.append(point.x())
                            y.append(point.y())
                            try: # фильтр на наличие поля "height" без вызова ошибки
                                elevation = feature['height'] 
                                z.append(elevation) 
                            except KeyError:
                                z.append(0)
                else: # для обработки обычных точек
                    point = geom.asPoint()
                    if isinstance(point, QgsPoint):
                        x.append(point.x())
                        y.append(point.y())
                        z.append(point.z() if point.hasZ() else 0) # обработка точек с 3-мя координатами [x, y, z]
                    else: # обработка точек с 2-мя координатами
                        x.append(point.x())
                        y.append(point.y())
                        try: # фильтр на наличие поля "height" без вызова ошибки
                            elevation = feature['height'] 
                            z.append(elevation) 
                        except KeyError:
                            z.append(0)
            grafik.scatter(x, y, z, color=colors(i / len(layers)), label=layer.name())
            # нанесение точки на график с определённым для её слоя цветом
        grafik.set_xlabel('Долгота')
        grafik.set_ylabel('Широта')
        grafik.set_zlabel('Высота')
        grafik.legend(loc='upper center', bbox_to_anchor=(0.05, 1))
        matplotlib.pyplot.tight_layout() # автоматическое увеличение графика под окно
        matplotlib.pyplot.show()