from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.core import QgsProject, QgsPoint
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction, QDialog, QListWidget, QMessageBox

import matplotlib.pyplot
import os.path
from .resources import *
from .mod_layer_dialog_base import Ui_mod_layer_dialog_base
from matplotlib.colors import ListedColormap
import numpy as np
import requests
from scipy.interpolate import griddata
from mpl_toolkits.mplot3d import Axes3D
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
        color = [ "#b70421","#4553ed", "#a4ee25", "#ed4115", "#652fea", "#4abe5b", "#fe589e", "#a42dd9", "#5098c0", "#f26d00"] 
        colors = ListedColormap(color[:len(layers)])
        o = matplotlib.pyplot.figure(figsize=(12, 8))
        grafik = o.add_subplot(111, projection='3d') # создание графика
        all_x, all_y, all_z = [], [], []
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
            grafik.scatter(x, y, z, color=colors(i / len(layers)), label=layer.name(), zorder=1)
            all_x.extend(x)
            all_y.extend(y)
            all_z.extend(z)
            # нанесение точки на график с определённым для её слоя цветом
        grafik.set_xlabel('Долгота')
        grafik.set_ylabel('Широта')
        grafik.set_zlabel('Высота')
        min_dol, max_dol = min(all_x), max(all_x)
        min_sch, max_sch = min(all_y),  max(all_y)
        
# сообщения с крайними значениями
        #message = f"Крайние значения:\nДолгота: {min_longitude} - {max_longitude}\nШирота: {min_latitude} - {max_latitude}"
        #QMessageBox.information(None, "Крайние значения", message)

        def get_elevations(c):
            url = 'https://api.open-elevation.com/api/v1/lookup'
            l = '|'.join([f"{sch},{dol}" for sch, dol in c])
            p = {'locations': l}
            try:
                r = requests.get(url, params=p)
                r.raise_for_status()
                file = r.json()
                el = [result['elevation'] for result in file['results']]
                return el
            except Exception as e:
                return [None] * len(c)
    
        schirota = np.linspace(round(min_sch, 1), round(max_sch, 1), 15) 
        dolgota = np.linspace(round(min_dol, 1), round(max_dol, 1), 15)
        c = [(sch, dol) for sch in schirota for dol in dolgota] #создание списка точек в преелах графика для последующей интерполяции
        elevation = get_elevations(c)
        f_c, f_e = [], []
        for (sch, dol), vis in zip(c, elevation):
            if vis!=None:
                f_c.append((dol, sch))
                f_e.append(vis)
        p, e = np.array(f_c), np.array(f_e)
        grid_lon, grid_lat = np.linspace(min(dolgota), max(dolgota), 100), np.linspace(min(schirota), max(schirota), 100)
        grid_lon, grid_lat = np.meshgrid(grid_lon, grid_lat)
        grid_e = griddata(p, e, (grid_lon, grid_lat), method='cubic')
        min_e = np.nanmin(grid_e)
        max_e = max(all_z)+100
        grid_e_f = np.where(np.isnan(grid_e), min_e, grid_e)
        grafik.plot_surface(grid_lon, grid_lat, grid_e_f, cmap='viridis', edgecolor='none', alpha = 1, zorder=2)
        grafik.set_xlim(min(dolgota), max(dolgota))
        grafik.set_ylim(min(schirota), max(schirota))
        grafik.set_zlim(min(min_e, 0), max_e)
        grafik.set_box_aspect([2, 2, 0.7]) #соотношение сторон графика
        grafik.legend(loc='upper center', bbox_to_anchor=(0.05, 1))
        grafik.grid(True)
        matplotlib.pyplot.tight_layout() # автоматическое увеличение графика под окно
        matplotlib.pyplot.show()