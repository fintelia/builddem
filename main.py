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

neigborhoods = geopandas.read_file('Neighborhood_Map_Atlas_Neighborhoods.zip').to_crs("EPSG:32048")
neighborhood = neigborhoods[neigborhoods['L_HOOD'] == 'Capitol Hill'].buffer(0)
transform=rasterio.transform.from_bounds(*neighborhood.geometry.total_bounds, 1024, 1024)

if exists("Building_Outline_capitol_hill.geojson"):
    buildings = geopandas.read_file("Building_Outline_capitol_hill.geojson")
else:
    buildings = geopandas.read_file('Building_Outline_2015_8791546178963768032.zip').to_crs("EPSG:32048")
    buildings = buildings.clip(neighborhood.geometry.total_bounds)
    buildings.to_file("Building_Outline_capitol_hill.geojson", driver='GeoJSON')
buildings['apex'] = buildings['BP99_APEX'] * 0.3048
buildings = buildings.loc[buildings['geometry'].is_valid, :]
buildings = buildings.loc[buildings['apex'] > 0, :]

buildings = buildings.loc[buildings.within(neighborhood.geometry.union_all()), :]

# ['Loyal Heights', 'Ballard', 'Whittier Heights', 'West Woodland', 'Phinney Ridge', 'Wallingford', 'Fremont', 'Green Lake', 'View Ridge', 'Ravenna', 'Sand Point', 'Bryant', 'Windermere', 'Laurelhurst', 'Roosevelt', 'University of Washington', 'East Queen Anne', 'West Queen Anne', 'Lower Queen Anne', 'North Queen Anne', 'Westlake', 'Eastlake', 'South Lake Union', 'Lawton Park', 'Briarcliff', 'Southeast Magnolia', 'Madrona', 'Harrison/Denny-Blaine', 'Minor', 'Leschi', 'Mann', 'Atlantic', 'Pike-Market', 'Belltown', 'International District', 'Central Business District', 'First Hill', 'Yesler Terrace', 'Pioneer Square', 'Interbay', 'SODO', 'Georgetown', 'South Park', 'Harbor Island', 'Seaview', 'Gatewood', 'Arbor Heights', 'Alki', 'North Admiral', 'Fairmount Park', 'Genesee', 'Fauntleroy', 'North Beacon Hill', 'Mid-Beacon Hill', 'South Beacon Hill', 'Holly Park', 'Brighton', 'Dunlap', 'Rainier Beach', 'Rainier View', 'Mount Baker', 'Columbia City', 'Highland Park', 'North Delridge', 'Riverview', 'High Point', 'South Delridge', 'Roxhill', 'Seward Park', 'Wedgwood', 'Portage Bay', 'Montlake', 'Madison Park', 'Broadway', 'Stevens', 'Victory Heights', 'Matthews Beach', 'Meadowbrook', 'Olympic Hills', 'Cedar Park', 'Broadview', 'Bitter Lake', 'Haller Lake', 'Pinehurst', 'North Beach/Blue Ridge', 'Licton Springs', 'Maple Leaf', 'Crown Hill', 'Greenwood', 'Sunset Hill', 'University District', 'University Heights', 'Denny Triangle', 'Industrial District']


elevation = rasterio.open('USGS_1M_10_x55y528_WA_KingCounty_2021_B21.tif')

# meta = elevation.meta.copy()
# meta.update(compress='lzw')
# meta.update(dtype=rasterio.int16)
# meta.update(nodata=-9999)

elevation_image, elevation_transform = rasterio.mask.mask(elevation, neighborhood.geometry.to_crs(elevation.crs), crop=True, nodata=0)
elevation_transformed = np.zeros((1024, 1024), dtype=np.float32)
reproject(
    elevation_image,
    elevation_transformed,
    src_transform=elevation_transform,
    src_crs=elevation.crs,
    dst_transform=transform,
    dst_crs="EPSG:32048",
    resampling=Resampling.nearest)

with rasterio.open("output.tif", 'w+', driver="GTiff", width=1024, height=1024, crs="EPSG:32048", count=1, dtype=rasterio.float32, compress="lzw", transform=transform, nodata=0) as out:
    out.write(elevation_transformed, 1)
    out_arr = out.read(1)

    shapes = ((geom,value) for geom, value in zip(buildings.geometry, buildings.apex))
    burned = features.rasterize(shapes=shapes, out=out_arr, transform=transform)
    out.write_band(1, burned)



# cube = make_geocube(
#     buildings,
#     measurements=["apex"],
#     resolution=(1, -1),
# )
# cube.apex.rio.to_raster("output.tif")


# origin = neighborhood.geometry.centroid
# #ax = neighborhood.plot(figsize=(16,12), color='white', edgecolor='black', linewidth=2)
# ax = buildings.plot(color='lightblue')
# ax.axis('off')
# ax.margins(0)
# plt.show()
# plt.savefig("output.png", bbox_inches='tight')