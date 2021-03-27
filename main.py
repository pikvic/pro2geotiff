from utils import readproj, projmapper    
import rasterio
from rasterio.transform import Affine
from pyproj import Transformer, CRS
from rasterio.warp import calculate_default_transform, reproject, Resampling

def reproject_raster(in_path, out_path, crs="EPSG:4326"):
    with rasterio.open(in_path) as src:
        src_crs = src.crs
        transform, width, height = calculate_default_transform(src_crs, crs, src.width, src.height, *src.bounds)
        kwargs = src.meta.copy()

        kwargs.update({
            'crs': crs,
            'transform': transform,
            'width': width,
            'height': height})

        with rasterio.open(out_path, 'w', **kwargs) as dst:
            for i in range(1, src.count + 1):
                reproject(
                    source=rasterio.band(src, i),
                    destination=rasterio.band(dst, i),
                    src_transform=src.transform,
                    src_crs=src.crs,
                    dst_transform=transform,
                    dst_crs=crs,
                    resampling=Resampling.nearest)

def main():
    b0, data = readproj.readproj('1.pro')
    
    lon = b0['b0_proj_common']['lon'][0]
    lat = b0['b0_proj_common']['lat'][0]
    latsize = b0['b0_proj_common']['latSize'][0]
    lonsize = b0['b0_proj_common']['lonSize'][0]
    latres = b0['b0_proj_common']['latRes'][0]
    lonres = b0['b0_proj_common']['lonRes'][0]
    rows = b0['b0_proj_common']['scanNum'][0]
    cols = b0['b0_proj_common']['pixNum'][0]
    pt = b0['b0_proj_common']['projType'][0] - 1

    prjmap = projmapper.ProjMapper(pt, lon, lat, lonsize, latsize, lonres, latres)
    
    print(lat, lon, latsize, lonsize, latres, lonres)

    # ESPG:3395 - наш
    # ESPG:3857 - Web Mercator
    # ESPG:4326 - градусы равнопромежуточная
    # data = data.astype(float)
    tf = Transformer.from_crs("EPSG:4326", "EPSG:3395", always_xy=True)

    top_left = tf.transform(lon, lat + latsize)
    bottom_right = tf.transform(lon + lonsize, lat) 
    latres = (top_left[1] - bottom_right[1]) / rows 
    lonres = (bottom_right[0] - top_left[0]) / cols
    lon = top_left[0]
    lat = top_left[1]

    print(top_left, bottom_right, latres, lonres)
    #latres /= 3600
    #lonres /= 3600
    transform = Affine.translation(lon - lonres / 2, lat + latsize - latres / 2) * Affine.scale(lonres, latres)
    print(transform)
   #  transform = rasterio.transform.from_bounds(lon, lat, lon + lonsize, lat + latsize, cols, rows)
    # print(transform)
    transform = rasterio.transform.from_origin(lon, lat, lonres, latres)
    # print(transform)
    

    new_dataset = rasterio.open(
                                'new.tif', 
                                'w', 
                                driver='GTiff', 
                                height=rows, 
                                width=cols, 
                                count=1, 
                                dtype=data.dtype, 
                                crs='EPSG:3395',
                                transform=transform,
                            )
    new_dataset.write(data, 1)
    new_dataset.close()

    reproject_raster('new.tif', 'new2.tif')

if __name__ == "__main__":
    main()