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
from pyproj import Transformer


# Width and height of the output image in pixels
width = 2000
height = 2000

# Size of the area to be rendered in meters
size = 1000

# Center of the area to be rendered in latitude and longitude (WGS84)
center = (47.6182177390292, -122.31919478639601)

# Coordinate reference system of the output image
crs = "EPSG:3689"

transformer = Transformer.from_crs("EPSG:4326", crs)
center = transformer.transform(center[0], center[1])
bounds = (center[0] - size/2, center[1] - size/2, center[0] + size/2, center[1] + size/2)
transform=rasterio.transform.from_bounds(*bounds, width, height)

buildings = geopandas.read_file('Building_Outline_2015_8791546178963768032.zip').to_crs(crs)
buildings = buildings.clip(bounds)
buildings['apex'] = buildings['BP99_APEX'] * 0.3048
buildings = buildings.loc[buildings['geometry'].is_valid, :]
buildings = buildings.loc[buildings['apex'] > 0, :]

elevation = rasterio.open('USGS_1M_10_x55y528_WA_KingCounty_2021_B21.tif')

#elevation_image, elevation_transform = rasterio.mask.mask(elevation, neighborhood.geometry.to_crs(elevation.crs), crop=True, nodata=0)
elevation_transformed = np.zeros((width, height), dtype=np.float32)
reproject(
    elevation.read(1),
    elevation_transformed,
    src_transform=elevation.transform,
    src_crs=elevation.crs,
    dst_transform=transform,
    dst_crs="EPSG:3689",
    resampling=Resampling.nearest)

with rasterio.open("output.tif", 'w+', driver="GTiff", width=width, height=height, crs=crs, count=1, dtype=rasterio.float32, compress="lzw", transform=transform, nodata=0) as out:
    out.write(elevation_transformed, 1)
    out_arr = out.read(1)

    shapes = ((geom,value) for geom, value in zip(buildings.geometry, buildings.apex))
    burned = features.rasterize(shapes=shapes, out=out_arr, transform=transform)
    out.write_band(1, burned)
