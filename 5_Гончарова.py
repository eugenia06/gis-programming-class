from random import randint
pr = QgsProject.instance()
layer = pr.mapLayersByName("station")[0]
poligons = pr.mapLayersByName("districts")[0]
print(layer.featureCount())
layer.setSubsetString('"colour" = \'orange\'')
print(layer.featureCount())
station = QgsVectorLayer('Polygon?crs=EPSG:3857', "station_copy", "memory")
prov = station.dataProvider()
prov.addAttributes(layer.fields())
station.updateFields()
random_1 = randint(1, 100)
b_d = (random_1 + 5) * 20
for stations in layer.getFeatures():
    n_f = QgsFeature()
    n_f.setGeometry(QgsGeometry.fromPointXY(stations.geometry().asPoint()).buffer(b_d, 8))
    n_f.setAttributes(stations.attributes())
    prov.addFeature(n_f)
station.updateExtents()
#pr.addMapLayer(station)
layer.setSubsetString('')
print(layer.featureCount())
layer_with_intersects = QgsVectorLayer('Polygon?crs=EPSG:3857', "station/districts", "memory")
prov_2 = layer_with_intersects.dataProvider()
prov_2.addAttributes(poligons.fields())
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
layer_with_intersects.updateExtents()
pr.addMapLayer(layer_with_intersects)




