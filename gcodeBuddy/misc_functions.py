import sys
import numpy as np


def unit_convert(value, current_units, needed_units):
    """
    converts given value to specified units

    :param value: numerical value to convert
    :type value: int, float
    :param current_units: current units of value
    :type current_units: str
    :param needed_units: units to convert value to
    :type needed_units: str
    :returns: value in requisite units
    :rtype: int, float

    Supported Units:
        Position: "mm", "cm", "m", "in", "ft" \n
        Speed: "mm/sec", "mm/min", "cm/sec", "cm/min", "m/sec", "m/min", "in/sec", "in/min", "ft/sec", "ft/min" \n
        Acceleration: Coming soon. \n

    """

    err_msg = "Error in misc_functions.unit_convert(): "

    if not isinstance(value, (int, float)):
        raise TypeError("Argument 'value' of non-int/non-float type")

    if not isinstance(current_units, str):
        raise TypeError("Argument 'current_units' of non-string type")

    if not isinstance(needed_units, str):
        raise TypeError("Argument 'needed_units' of non-string type")

    units = (
        ("mm", "cm", "m", "in", "ft"),  # distance
        ("mm/sec", "mm/min", "cm/sec", "cm/min", "m/sec", "m/min", "in/sec", "in/min", "ft/sec", "ft/min"),  # speed
        ()  # acceleration
    )

    unit_vals = (
        (1000.0, 100.0, 1.0, 39.37, 3.281),  # distance
        (1000.0, 60000.0, 100.0, 6000.0, 1.0, 60.0, 39.37, 2362.0, 3.280, 196.9),  # speed
        ()  # acceleration
    )

    current_units = current_units.lower()
    needed_units = needed_units.lower()

    for i in range(3):  # iterating through categories
        if current_units in units[i] and needed_units in units[i]:  # if both units in same category
            return value * ((unit_vals[i][units[i].index(needed_units)]) / (unit_vals[i][units[i].index(current_units)]))  # perform calculation
    # point will be reached if units aren't in same category
    raise ValueError("Unrecognized units passed in argument 'current_units' or 'needed_units'")


def angle(center_point, end_point):
    """
    returns angle between line formed by two points and +x direction

    :param center_point: point to be considered as the origin
    :type center_point: list[int, float], tuple(int, float)
    :param end_point: point to form line with the relative origin point
    :type end_point: list[int, float], tuple(int, float)
    :return: angle between line and +x axis, relative to origin point (degrees)
    :rtype: float
    """
    err_msg = "Error in misc_functions.angle(): "
    # error checking
    if isinstance(center_point, (list, tuple)):
        if len(center_point) == 2:
            valid_types = True
            for coord in center_point:
                if not isinstance(coord, (int, float)):
                    valid_types = False
            if not valid_types:
                raise TypeError("Element in argument 'center_point' of non-int/non-float type")
        else:
            raise ValueError("Argument 'center_point' not of length 2")
    else:
        raise TypeError("Argument 'center_point' of non-list/non-tuple type")

    if isinstance(end_point, (list, tuple)):
        if len(end_point) == 2:
            valid_types = True
            for coord in end_point:
                if not isinstance(coord, (int, float)):
                    valid_types = False
            if not valid_types:
                raise TypeError("Element in argument 'end_point' of non-int/non-float type")
        else:
            raise ValueError("Argument 'end_point' not of length 2")
    else:
        raise TypeError("Argument 'end_point' of non-list/non-tuple type")

    # establishing end point relative to center
    rel_point = [end_point[0] - center_point[0], end_point[1] - center_point[1]]
    if abs(rel_point[0]) < 0.001:  # approximate 0, floats aren't real (point on y-axis)
        if rel_point[1] > 0:
            return 90.0
        else:
            return 270.0
    elif abs(rel_point[1]) < 0.001:  # approximate 0, floats suck (point on x-axis)
        if rel_point[0] > 0:
            return 0.0
        else:
            return 180.0
    if rel_point[0] > 0 and rel_point[1] > 0:  # quadrant I
        return np.arctan(rel_point[1] / rel_point[0]) * (180 / np.pi)
    elif rel_point[0] < 0 and rel_point[1] > 0:  # quadrant II
        return (np.arctan(-rel_point[0] / rel_point[1]) * (180 / np.pi)) + 90
    elif rel_point[0] < 0 and rel_point[1] > 0:  # quadrant III
        return (np.arctan(rel_point[1] / rel_point[0]) * (180 / np.pi)) + 180
    else:  # quadrant IV
        return (np.arctan(-rel_point[0] / rel_point[1]) * (180 / np.pi)) + 270


def centers_from_params(point_a, point_b, radius):
    """
    returns two possible center positions of an arc given two points on arc and a radius

    :param point_a: one of two distinct points on arc
    :type point_a: list[int, float], tuple(int, float)
    :param point_b: one of two distinct points on arc
    :type point_b: list[int, float], tuple(int, float)
    :param radius: radius of arc
    :type radius: int, float
    :return: two possible center point values
    :rtype: list[list[int, float]]
    """
    err_msg = "Error in misc_functions.center(): "
    # error checking point_a
    if isinstance(point_a, (tuple, list)):
        if len(point_a) == 2:
            valid_types = True
            for coord in point_a:
                if not isinstance(coord, (int, float)):
                    valid_types = False
            if not valid_types:
                raise TypeError("Element in argument 'point_a' of non-int/non-float type")
        else:
            raise ValueError("Argument 'point_a' not of length 2")
    else:
        raise TypeError("Argument 'point_a' of non-list/non-tuple type")
    # error checking point_b
    if isinstance(point_b, (tuple, list)):
        if len(point_b) == 2:
            valid_types = True
            for coord in point_b:
                if not isinstance(coord, (int, float)):
                    valid_types = False
            if not valid_types:
                raise TypeError("Element in argument 'point_b' of non-int/non-float type")
        else:
            raise ValueError("Argument 'point_b' not of length 2")
    else:
        raise TypeError("Argument 'point_b' of non-list/non-tuple type")
    # error checking radius
    if not isinstance(radius, (float, int)):
        raise TypeError("Argument 'radius' of non-int/non-float type")


    # easier variables
    x_a, y_a = point_a
    x_b, y_b = point_b
    r = radius

    # error checking values
    if (np.sqrt((x_a - x_b)**2 + (y_a - y_b)**2) / 2) > r:
        raise ValueError("Unable to create circle from given points and radius (d_ab > 2r)")
    # sequential computing for readability
    ret_val_1, ret_val_2 = (0, 0), (0, 0)
    if np.abs(x_a - x_b) < 0.001 and np.abs(y_a - y_b) < 0.001:  # same point
        raise ValueError("Arguments 'point_a' and 'point_b' describe the same point and cannot define an arc")
    elif np.abs(x_a - x_b) < 0.001:  # points form vertical line
        y_m = (y_a + y_b) / 2
        s_h = np.sqrt(r**2 - (y_a - y_m)**2)

        ret_val_1 = [x_a + s_h, y_m]
        ret_val_2 = [x_a - s_h, y_m]
    elif np.abs(y_a - y_b) < 0.001:  # points form horizontal line
        x_m = (x_a + x_b) / 2
        s_v = np.sqrt(r**2 - (x_m - x_a)**2)

        ret_val_1 = [x_m, y_a + s_v]
        ret_val_2 = [x_m, y_a - s_v]
    else:
        # establishing situation - determining orientation of the rhombus formed by to ret_vals and given coords
        x_right, y_right = 0, 0
        x_left, y_left = 0, 0
        if x_a > x_b:  # x_a is on right
            x_right, y_right = x_a, y_a
            x_left, y_left = x_b, y_b
        else:  # x_b on right
            x_right, y_right = x_b, y_b
            x_left, y_left = x_a, y_a
        # setting parameters
        x_m = (x_right + x_left) / 2
        y_m = (y_right + y_left) / 2
        l_1 = (np.sqrt((x_right - x_left)**2 + (y_right - y_left)**2)) / 2
        l_1_x = (x_right - x_left) / 2
        l_1_y = (y_right - y_left) / 2
        l_2 = np.sqrt(r**2 - l_1**2)
        l_2_x = abs(l_1_y * (l_2 / l_1))
        l_2_y = abs(l_1_x * (l_2 / l_1))
        # using previous info to find centers:
        if y_left > y_right:  # centerline points up to the right
            ret_val_1 = [round(x_m + l_2_x, 2), round(y_m + l_2_y, 2)]
            ret_val_2 = [round(x_m - l_2_x), round(y_m - l_2_y, 2)]
        else:  # centerline points up to the left
            ret_val_1 = [round(x_m - l_2_x, 2), round(y_m + l_2_y, 2)]
            ret_val_2 = [round(x_m + l_2_x, 2), round(y_m - l_2_y, 2)]

    return [ret_val_1, ret_val_2]
