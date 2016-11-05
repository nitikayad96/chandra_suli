import cPickle
import gzip
import os

import astropy.units as u
from astropy.coordinates import SkyCoord


class ChandraSourceCatalog(object):
    def __init__(self):

        # Find the catalog data file

        # TODO: Put it in the region repository

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

    def _compute_distances(self, ra, dec):

        # Instance the SkyCoord instance

        cone_center = SkyCoord(ra=ra, dec=dec, unit='deg')

        # Find all sources within the requested cone

        distances = self._sky_coords.separation(cone_center).to(u.arcmin)

        return distances

    def cone_search(self, ra, dec, radius, unit='arcmin'):
        """
        Find sources within the given radius of the given position

        :param ra: R.A. of position
        :param dec: Dec of position
        :param radius: radius
        :param unit: units to use for the radius (default: arcmin)
        :return: a pandas DataFrame containing the sources within the given radius
        """

        distances = self._compute_distances(ra, dec)  # arcmin

        idx = distances <= radius * u.Unit(unit)

        # Return the results

        # Copy the array, to avoid returning a slice instead

        results = self._catalog.copy().loc[idx]

        # Add the distance column
        results['distance'] = distances[idx]

        return results

    def find_closest_source(self, ra, dec):
        """
        Finds the closest source to the given position

        :param ra:
        :param dec:
        :return:
        """

        distances = self._compute_distances(ra, dec)  # arcmin

        temp_catalog = self._catalog.copy()

        temp_catalog['distance'] = distances

        src_id = temp_catalog['distance'].argmin()

        return temp_catalog.loc[src_id, :]

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
        idx = temp_results[column] == True

        # Get a copy
        results = temp_results.copy().loc[idx]

        return results

    def find_closest_variable_source(self, ra, dec, column='var_flag'):
        """
        Finds the closest source to the given position

        :param ra:
        :param dec:
        :return:
        """

        distances = self._compute_distances(ra, dec)  # arcmin

        temp_catalog = self._catalog.copy()

        temp_catalog['distance'] = distances

        # Select only variable sources
        idx = temp_catalog[column] == True

        variable_sources = temp_catalog.copy().loc[idx]

        src_id = variable_sources['distance'].argmin()

        return variable_sources.loc[src_id, :]
