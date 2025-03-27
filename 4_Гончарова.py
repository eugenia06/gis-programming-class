from osgeo import gdal
import os
layer = QgsProject.instance().mapLayersByName('5')[0] #получение растрового слоя
ds = gdal.Open(layer.dataProvider().dataSourceUri())
band_red, band_green, band_blue = ds.GetRasterBand(1).ReadAsArray(), ds.GetRasterBand(2).ReadAsArray(), ds.GetRasterBand(3).ReadAsArray()
all_band = [band_red, band_green, band_blue]
#all_band = [ds.GetRasterBand(i).ReadAsArray() for i in range(1, 4)]
x_size, y_size = ds.RasterXSize, ds.RasterYSize
geo_transform_layer = ds.GetGeoTransform()
prn_layer = ds.GetProjection()
#новый растр - new_layer
d = os.path.join(os.path.expanduser('~'), 'Desktop') #создание файла на рабочем столе запускающего код
new_path = os.path.join(d, 'layer_5.tif_footprint_5.tif')
new_layer = gdal.GetDriverByName('GTiff').Create(new_path, x_size, y_size, 3, gdal.GDT_Float32) #создание нового растрового слоя
for i in range(3): #перенос каналов
    new_layer.GetRasterBand(i + 1).WriteArray(all_band[i])
new_layer.SetGeoTransform(geo_transform_layer)
new_layer.SetProjection(prn_layer)
#обработка footprint_5
footprint_5 = QgsProject.instance().mapLayersByName('footprint_5')[0]
poly_g = list(footprint_5.getFeatures())[0].geometry()
coords, gcp = [(i.x(), i.y()) for i in poly_g.asPolygon()[0]], []
for i in range(0, 4):
    pixel, line = 0, 0
    if i!=0 and i!=3: pixel = x_size - 1
    if i==2 or i==3: line = y_size - 1
    gcp.append(((gdal.GCP(coords[i][0], coords[i][1], 0, pixel, line))))
new_layer.SetGCPs(gcp, crs.toWkt()) #изменение координат углов
new_layer.FlushCache()
new_layer = None 

new_raster_layer = QgsRasterLayer(new_path, '5.tif/footprint_5')
QgsProject.instance().addMapLayer(new_raster_layer)
