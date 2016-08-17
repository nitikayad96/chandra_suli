import numpy as np
import gzip
import os
import pandas as pd
import cPickle
from astropy.coordinates import SkyCoord
import astropy.units as u


class ChandraSourceCatalog(object):

    def __init__(self):

        # Find the catalog data file

        catalog_filename = 'chandra_csc_1.1.pickle.gz'

        # Define the search paths
        search_paths = ['.', os.path.dirname(__file__)]

        catalog_file = None

        for path in search_paths:

            catalog_file = os.path.abspath(os.path.join(path, catalog_filename))

            if os.path.exists(catalog_file):

                # Found it
                break

        assert catalog_file is not None, "Could not find catalog file in %s" % ",".join(search_paths)

        # Read the chandra source catalog from the CSV file

        f = gzip.GzipFile(catalog_file)

        data = cPickle.load(f)

        self._catalog = data['data_frame']
        self._sky_coords = data['sky_coords']

    def cone_search(self, ra, dec, radius, unit='arcmin'):
        """
        Find sources within the given radius of the given position

        :param ra: R.A. of position
        :param dec: Dec of position
        :param radius: radius
        :param unit: units to use for the radius (default: arcmin)
        :return: a pandas DataFrame containing the sources within the given radius
        """

        # Instance the SkyCoord instance

        cone_center = SkyCoord(ra=ra, dec=dec, unit='deg')

        # Find all sources within the requested cone

        idx = self._sky_coords.separation(cone_center) <= radius * u.Unit(unit)

        # Return the results

        return self._catalog[idx]

    def find_variable_sources(self, ra, dec, radius, unit='arcmin', column='var_flag'):
        """
        Find all variable sources within the given cone

        :param ra: R.A. of position
        :param dec: Dec of position
        :param radius: radius
        :param unit: units to use for the radius (default: arcmin)
        :return: a pandas DataFrame containing the variable sources within the given radius
        """

        # Get all sources within the cone

        temp_results = self.cone_search(ra, dec, radius, unit=unit)

        # Now select only the variable sources
        idx = temp_results[column]==True

        return temp_results[idx]
