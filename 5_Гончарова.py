from random import randint
pr = QgsProject.instance()
#подключение исходных слоёв к коду(исходные слои открыты в qgis)
layer = pr.mapLayersByName("station")[0] 
poligons = pr.mapLayersByName("districts")[0]
#print(layer.featureCount())
layer.setSubsetString('"colour" = \'orange\'') #фильтрации по цвету ветки
#print(layer.featureCount()) #проверка результата фильтрации
station = QgsVectorLayer('Polygon?crs=EPSG:3857', "station_copy", "memory")
prov = station.dataProvider()
prov.addAttributes(layer.fields())
station.updateFields() #обновление и сохранение данных на промежуточном слое

random_1 = randint(1, 100) #получение рандомного числа от 1 до 99(включительно)
b_d = (random_1 + 5) * 20 #получение радиуса для буферизации

for stations in layer.getFeatures():
    n_f = QgsFeature()
    n_f.setGeometry(QgsGeometry.fromPointXY(stations.geometry().asPoint()).buffer(b_d, 8))
    n_f.setAttributes(stations.attributes())
    prov.addFeature(n_f)
station.updateExtents() #обновление и сохранение данных на промежуточном слое
#pr.addMapLayer(station) #для вывода результата фильтрации станций метро по цвету ветки
layer.setSubsetString('') #снятие фильтрации с layer(исходный слой)
#print(layer.featureCount()) #для проверки снятия фильтрации

layer_with_intersects = QgsVectorLayer('Polygon?crs=EPSG:3857', "station/districts", "memory") #создание финального слоя с результатом пересечения 
layer_with_intersects.updateFields()
for poly in poligons.getFeatures():
    p_g = poly.geometry()
    for st in station.getFeatures():
        st_g = st.geometry()
        if st_g.intersects(p_g):
            n_f_2 = QgsFeature()
            n_f_2.setGeometry(p_g) 
            n_f_2.setAttributes(poly.attributes()) 
            prov_2.addFeature(n_f_2)
            break
layer_with_intersects.updateExtents() #обновление и сохранение данных на финальном слое
pr.addMapLayer(layer_with_intersects)




