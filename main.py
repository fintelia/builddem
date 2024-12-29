import pandas
import geopandas
import matplotlib.pyplot as plt
import math
import rasterio
from os.path import exists
from geocube.api.core import make_geocube
from rasterio import features
import numpy as np
from rasterio.warp import reproject, Resampling

width = 2000
height = 2000

neigborhoods = geopandas.read_file('Neighborhood_Map_Atlas_Neighborhoods.zip').to_crs("EPSG:32048")
neighborhood = neigborhoods[neigborhoods['L_HOOD'] == 'Capitol Hill'].buffer(0)
transform=rasterio.transform.from_bounds(*neighborhood.geometry.total_bounds, width, height)

if exists("Building_Outline_capitol_hill.geojson"):
    buildings = geopandas.read_file("Building_Outline_capitol_hill.geojson")
else:
    buildings = geopandas.read_file('Building_Outline_2015_8791546178963768032.zip').to_crs("EPSG:32048")
    buildings = buildings.clip(neighborhood.geometry.total_bounds)
    buildings.to_file("Building_Outline_capitol_hill.geojson", driver='GeoJSON')
buildings['apex'] = buildings['BP99_APEX'] * 0.3048
buildings = buildings.loc[buildings['geometry'].is_valid, :]
buildings = buildings.loc[buildings['apex'] > 0, :]

# buildings = buildings.loc[buildings.within(neighborhood.geometry.union_all()), :]


elevation = rasterio.open('USGS_1M_10_x55y528_WA_KingCounty_2021_B21.tif')

#elevation_image, elevation_transform = rasterio.mask.mask(elevation, neighborhood.geometry.to_crs(elevation.crs), crop=True, nodata=0)
elevation_transformed = np.zeros((width, height), dtype=np.float32)
reproject(
    elevation.read(1),
    elevation_transformed,
    src_transform=elevation.transform,
    src_crs=elevation.crs,
    dst_transform=transform,
    dst_crs="EPSG:32048",
    resampling=Resampling.nearest)

with rasterio.open("output.tif", 'w+', driver="GTiff", width=width, height=height, crs="EPSG:32048", count=1, dtype=rasterio.float32, compress="lzw", transform=transform, nodata=0) as out:
    out.write(elevation_transformed, 1)
    out_arr = out.read(1)

    shapes = ((geom,value) for geom, value in zip(buildings.geometry, buildings.apex))
    burned = features.rasterize(shapes=shapes, out=out_arr, transform=transform)
    out.write_band(1, burned)
