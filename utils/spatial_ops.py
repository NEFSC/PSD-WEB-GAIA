# ------------------------------------------------------------------------------
# ----- spatial_ops.py ---------------------------------------------------------
# ------------------------------------------------------------------------------
#
#    authors:  John Wall (john.wall@noaa.gov)
#              
#    purpose:  Contains reusable global spatial methods
#
# ------------------------------------------------------------------------------



# ------------------------------------------------------------------------------
# Import libraries
# ------------------------------------------------------------------------------
import os
import math
import shutil
import tempfile
import subprocess
from time import time
from pyproj import CRS
from osgeo import gdal
from shapely.geometry import box
from shapely.ops import unary_union
import pandas as pd
import geopandas as gpd


# ------------------------------------------------------------------------------
# Spatial methods
# ------------------------------------------------------------------------------
def pansharpen_imagery(pan_image, msi_image):
    """Short term pansharpened method for testing, usuable only on Maxar WV"""
    start = time()
    shrp_image = pan_image.split('/')[-1].replace('P1BS', 'S1BS')
    print(f"YOUR SHARP IMAGE IS: {shrp_image}")
    gdal_pansharpen(['' ,
                     '-b', '5',
                     '-b', '3',
                     '-b', '2',
                     '-r', 'cubic',
                     '-threads', 'ALL_CPUS',
                     pan_image, msi_image, shrp_image])
    print(f"\n It took: {round(time() - start,2)} seconds to create a pansharpened image \n")


def create_cog(sharpened_imagery):
    start = time()
    cogtiff = sharpened_imagery.replace('.tif', '_cog.tif')
    subprocess.run(['rio',
                    'cogeo',
                    'create',
                    '--zoom-level', '20',
                    '--overview-resampling', 'cubic',
                    '-w',
                    sharpened_imagery, cogtiff])
    print(f"\n It took: {round(time() - start,2)} seconds to create your COG: {cogtiff} \n")


def is_projected_in_meters(crs: CRS) -> bool:
    return crs.axis_info[0].unit_name.lower() in ["metre", "meter"]


def create_hexagon(cx, cy, r):
    """Create a flat-top hexagon centered at (cx, cy) with radius r."""
    angles = [math.radians(a) for a in range(0, 360, 60)]
    points = [(cx + r * math.cos(a), cy + r * math.sin(a)) for a in angles]
    return gpd.GeoSeries([gpd.points_from_xy(*zip(*points)).unary_union.convex_hull])[0]


def create_fishnet(cogs: list, cell_width: float = 600, cell_height: float = 400,
    buffer_overlap: float = 0, shape: str = "rectangle"
    ):
    """ 
    
    """
    assert shape in ["rectangle", "hex"]

    tmp_dir = tempfile.mkdtemp()

    fishnet_gdfs = []
    for cog in cogs:
        tmp_shp = os.path.join(tmp_dir, os.path.basename(cog).replace('.tif', '_fp.shp'))
        print(f"\nCreating imagery footprint: {tmp_shp}\n")
        subprocess.run(['gdal_footprint',
                        '-srcnodata', '0',
                        cog,
                        tmp_shp], check=True)
        
        gdf = gpd.read_file(tmp_shp)
        crs = gdf.crs
        print(f"\nYour footprint is in {crs} CRS\n")

        if not is_projected_in_meters(CRS.from_user_input(crs)):
            raise ValueError("CRS units are not in meters." +
                             "Fishnet creation assumes meter-based projection.")
        
        bbox = box(*gdf.geometry[0].bounds)
        print(bbox)

        if buffer_overlap > 0:
            bbox = bbox.buffer(buffer_overlap)

        grid = []
        if shape == "rectangle":
            xmin, ymin, xmax, ymax = bbox.bounds
            x = xmin
            while x < xmax:
                y = ymin
                while y < ymax:
                    cell = box(x, y, x + cell_width, y + cell_height)
                    if cell.intersects(gdf.geometry[0]):
                        grid.append(cell)
                    y += cell_height
                x += cell_width
        elif shape == "hex":
            xmin, ymin, xmax, ymax = bbox.bounds
            dx = cell_width * 3/4
            dy = cell_height * math.sqrt(3)/2
            row = 0
            x = xmin
            while x < xmax + cell_width:
                y = ymin - (dy / 2 if row % 2 else 0)
                while y < ymax + cell_height:
                    cx = x
                    cy = y
                    hexagon = create_hexagon(cx, cy, cell_width / 2)
                    if hexagon.intersects(gdf.geometry[0]):
                        grid.append(hexagon)
                    y += dy
                x += dx
                row += 1

        fishnet_gdf = gpd.GeoDataFrame(geometry=grid, crs=crs)
        fishnet_gdf['vendor_id'] = os.path.basename(cog.replace('.tif', ''))
        fishnet_gdfs.append(fishnet_gdf)

    pdf = pd.concat(fishnet_gdfs, ignore_index=True)
    gdf = gpd.GeoDataFrame(pdf, geometry='geometry', crs=crs)
    # gdf.to_file(os.path.join(tmp_dir, os.path.basename(cog).replace('.tif', '_fishnet.shp')))
    # gdf.to_csv(os.path.join(tmp_dir, os.path.basename(cog).replace('.tif', '_fishnet.csv')))

    shutil.rmtree(tmp_dir)

    return gdf