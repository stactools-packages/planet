import os
from copy import deepcopy
import json
import logging

import fsspec
import pystac
from pystac.utils import (str_to_datetime, make_absolute_href)
from pystac.extensions.eo import Band
from shapely.geometry import shape

from stactools.planet import PLANET_PROVIDER
from stactools.planet.constants import PLANET_EXTENSION_PREFIX

from osgeo import gdal

logger = logging.getLogger(__name__)

SKYSAT_BANDS = {'PAN': Band.create('PAN', center_wavelength= 655, full_width_half_max=440),
                'BLUE': Band.create('BLUE', center_wavelength= 470, full_width_half_max=70),
                'GREEN': Band.create('GREEN', center_wavelength= 560, full_width_half_max=80),
                'RED': Band.create('RED', center_wavelength= 645, full_width_half_max=90),
                'NIR': Band.create('NIR', center_wavelength= 800, full_width_half_max=152)
                }


class PlanetItem:
    def __init__(self,
                 item_metadata,
                 item_assets,
                 base_dir,
                 metadata_href=None):
        self.item_metadata = item_metadata
        self.item_assets = item_assets
        self.base_dir = make_absolute_href(base_dir)
        self.metadata_href = metadata_href

    def to_stac(self):
        props = deepcopy(self.item_metadata['properties'])

        # Core Item properties
        id = self.item_metadata['id']
        geom = self.item_metadata['geometry']
        bbox = list(shape(geom).bounds)
        datetime = str_to_datetime(props.pop('acquired'))

        item = pystac.Item(id=id,
                           geometry=geom,
                           bbox=bbox,
                           datetime=datetime,
                           properties={})

        # Common metadata
        item.common_metadata.providers = [PLANET_PROVIDER]
        item.common_metadata.gsd = props.pop('gsd')
        item.common_metadata.created = str_to_datetime(props.pop('published'))
        item.common_metadata.updated = str_to_datetime(props.pop('updated'))
        item.common_metadata.constellation = props.pop('provider')
        item.common_metadata.platform = props.pop('satellite_id')
        # Some do not have instrument (e.g. REOrthoTile)
        instrument = props.pop('instrument', None)
        if instrument is not None:
            item.common_metadata.instruments = [instrument]

        # eo
        item.ext.enable('eo')
        # STAC uses 0-100, planet 0-1
        item.ext.eo.cloud_cover = props.pop('cloud_cover') * 100

        # view
        item.ext.enable('view')
        item.ext.view.off_nadir = props.pop('view_angle')
        item.ext.view.azimuth = props.pop('satellite_azimuth')
        item.ext.view.sun_azimuth = props.pop('sun_azimuth')
        item.ext.view.sun_elevation = props.pop('sun_elevation')

        # Add all additional properties with Planet extension designation.
        whitelisted_props = [
                            'anomalous_pixels',
                            'ground_control',
                            'item_type',
                            'pixel_resolution',
                            'quality_category',
                            'strip_id',
                            'publishing_stage',
                            'clear_percent'
                            ]
        for name in whitelisted_props:
            if name in props:
                item.properties['{}:{}'.format(PLANET_EXTENSION_PREFIX, name)] = props[name]

        geotransform = None
        item_type = props.pop('item_type')
        for planet_asset in self.item_assets:
            href = make_absolute_href(planet_asset['path'],
                                      start_href=self.base_dir,
                                      start_is_dir=True)

            media_type = planet_asset['media_type']

            # Planet data is delivered as COGs
            if media_type == 'image/tiff':
                media_type = pystac.MediaType.COG
                roles = ['visual']
                thumbnail_path = f"{os.path.splitext(href)[0]}.thumbnail.png"
                datafile = gdal.Open(href)
                geotransform = datafile.GetGeoTransform()
                width = datafile.RasterXSize
                height = datafile.RasterYSize
                outsize = "256 0" if width > height else "0 256"
                gdal.Translate(thumbnail_path,
                               href,
                               options=f"-of PNG -outsize {outsize}")

                item.add_asset('thumbnail', pystac.Asset(href=thumbnail_path,
                                                         media_type="image/png",
                                                         roles=['thumbnail']))
            else:
                roles = ['metadata']

            asset_type = planet_asset['annotations']['planet/asset_type']
            bundle_type = planet_asset['annotations']['planet/bundle_type']
            # Use the asset type as the key if it's the same as the bundle
            # type, as this appears to be the 'main' asset of the bundle type.
            # If not, use a key that combines the bundle type and asset type.
            key = asset_type
            if asset_type != bundle_type:
                key = '{}:{}'.format(bundle_type, asset_type)

            item.add_asset(key, pystac.Asset(href=href, media_type=media_type, roles=roles))
            asset = pystac.Asset(href=href, media_type=media_type)

            if media_type == pystac.MediaType.COG:
                #add bands to asset
                if item_type.startswith('SkySat'):
                    if "panchro" in asset_type:
                        bands = [SKYSAT_BANDS['PAN']]
                    elif "analytic" in asset_type:
                        bands = [
                                 SKYSAT_BANDS['BLUE'],
                                 SKYSAT_BANDS['GREEN'],
                                 SKYSAT_BANDS['RED'],
                                 SKYSAT_BANDS['NIR']
                                ]
                    else:
                        bands = [
                                 SKYSAT_BANDS['RED'],
                                 SKYSAT_BANDS['GREEN'],
                                 SKYSAT_BANDS['BLUE']
                                ]
                    item.ext.eo.set_bands(bands, asset)

            item.add_asset(key, asset)

        # proj
        if 'epsg_code' in props:
            item.ext.enable('projection')
            item.ext.projection.epsg = props.pop('epsg_code')
            if geotransform is not None:
                item.ext.projection.transform = geotransform
                item.ext.projection.shape = [width, height]

        if self.metadata_href:
            item.add_asset(
                'metadata',
                pystac.Asset(href=self.metadata_href,
                             media_type=pystac.MediaType.JSON,
                             roles=['metadata']))

        return item

    @classmethod
    def from_file(cls, uri, assets, base_dir):
        logger.debug('Reading PlanetItem from {}'.format(uri))
        with fsspec.open(uri) as f:
            return cls(json.load(f), assets, base_dir, metadata_href=uri)
