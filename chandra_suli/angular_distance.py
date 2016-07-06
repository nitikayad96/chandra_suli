from astropy.coordinates import SkyCoord
import astropy.units as u


def angular_distance(ra1, dec1, ra2, dec2):
    """
    Compute angular distance between pairs of coordinates

    :param ra1:
    :param dec1:
    :param ra2:
    :param dec2:
    :return: angular distance
    """
    point_1 = SkyCoord(ra=ra1 * u.degree, dec=dec1 * u.degree, frame='icrs')

    point_2 = SkyCoord(ra=ra2 * u.degree, dec=dec2 * u.degree, frame='icrs')

    angular_distance = point_1.separation(point_2).to(u.degree)

    return angular_distance.value
