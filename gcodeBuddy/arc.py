import sys
# from matplotlib import pyplot as plt
import numpy as np


class Arc:
    """
    represents an arc toolpath travel


    :param center: center point of arc travel
    :type center: list[int, float]
    :param radius: radius of arc travel
    :type radius: int, float
    :param start_angle: starting angle of arc travel from +x axis (degrees)
    :type start_angle: int, float
    :param end_angle: ending angle of arc travel from +x axis (degrees)
    :type end_angle: int, float
    :param direction: direction of arc travel (clockwise or counter-clockwise)
    :type direction: "c", "cc"
    """

    def __init__(self, **kwargs):
        """
        initialization method
        """
        err_msg = "Error in arc.__init__(): "
        # ensuring valid keyword arguments passed
        req_args = ("center", "radius", "start_angle", "end_angle", "direction")
        for keyword in kwargs:
            if keyword not in req_args:
                raise ValueError("unrecognized keyword argument '" + keyword + "'")

        # ensuring valid center argument
        if "center" in kwargs:
            if isinstance(kwargs["center"], list):
                if len(kwargs["center"]) == 2:
                    valid_coord_types = True
                    for coord in kwargs["center"]:
                        if not isinstance(coord, (int, float)):
                            valid_coord_types = False
                    if valid_coord_types:
                        self.center = kwargs["center"]
                    else:
                        raise TypeError("entry in keyword argument 'center' of non-int, non-float type")
                else:
                    raise ValueError("keyword argument 'center' not of length 2")
            else:
                raise TypeError("keyword argument 'center' of non-list type")
        else:
            raise ValueError("required keyword argument 'center' not passed")

        # ensuring valid radius argument
        if "radius" in kwargs:
            if isinstance(kwargs["radius"], (int, float)):
                self.radius = kwargs["radius"]
            else:
                raise TypeError("keyword argument 'radius' of non-int, non-float type")
        else:
            raise ValueError("required keyword argument 'radius' not passed")

        # ensuring valid start_angle argument
        if "start_angle" in kwargs:
            if isinstance(kwargs["start_angle"], (int, float)):
                if 0 <= kwargs["start_angle"] < 360:
                    self.start_angle = kwargs["start_angle"]
                else:
                    raise ValueError("keyword argument 'start_angle' pass value out of range [0, 360]")
            else:
                raise TypeError("keyword argument 'start_angle' of non-int, non-float type")
        else:
            raise ValueError("required keyword argument 'start_angle' not passed")

        # ensuring valid end_angle argument
        if "end_angle" in kwargs:
            if isinstance(kwargs["end_angle"], (int, float)):
                if 0 <= kwargs["end_angle"] < 360:
                    self.end_angle = kwargs["end_angle"]
                else:
                    raise ValueError("keyword argument 'end_angle' pass value out of range [0, 360]")
            else:
                raise TypeError("keyword argument 'end_angle' of non-int, non-float type")
        else:
            raise ValueError("required keyword argument 'end_angle' not passed")

        # ensuring valid direction argument
        if "direction" in kwargs:
            if kwargs["direction"] in ("c", "cc"):
                self.direction = kwargs["direction"]
            else:
                raise TypeError("keyword argument 'direction' must be string \"c\" (clockwise) or \"cc\" (counter-clockwise)")
        else:
            raise ValueError("keyword argument 'direction' not passed")

    def get_center(self):
        """
        :return: center point of arc travel
        :rtype: list[int, float]
        """
        return self.center

    def get_radius(self):
        """
        :return: radius of arc travel
        :rtype: int, float
        """
        return self.radius

    def get_start_angle(self):
        """
        :return: starting angle of arc travel from +x axis (degrees)
        :rtype: int, float
        """
        return self.start_angle

    def get_end_angle(self):
        """
        :return: ending angle of arc travel from +x axis (degrees)
        :rtype: int, float
        """
        return self.end_angle

    def get_direction(self):
        """
        :return: direction of arc travel (clockwise or counter-clockwise)
        :rtype: "c", "cc"
        """
        return self.direction

    def get_angle(self):
        """
        :return: angle about center point traced out by arc travel (degrees)
        :rtype: int, float
        """
        if np.abs(self.start_angle - self.end_angle) < 0.001:  # approximate equality, given inaccuracy of floats
            return 360
        elif self.start_angle > self.end_angle:
            if self.direction == "cc":
                return 360 - (self.start_angle - self.end_angle)
            else:
                return self.start_angle - self.end_angle
        else:
            if self.direction == "cc":
                return self.end_angle - self.start_angle
            else:
                return 360 - (self.end_angle - self.start_angle)

    def set_center(self, new_center):
        """
        changes center point of arc travel to new_center

        :param new_center: new center point of arc travel
        :type new_center: list[int/float]
        """
        err_msg = "Error in arc.set_center(): "
        # ensuring valid new_center argument
        if isinstance(new_center, list):
            if len(new_center) == 2:
                valid_coord_types = True
                for coord in new_center:
                    if not isinstance(coord, (int, float)):
                        valid_coord_types = False
                if valid_coord_types:
                    self.center = new_center
                else:
                    raise TypeError("entry in argument 'new_center' of non-int, non-float type")
            else:
                raise ValueError("argument 'new_center' not of length 2")
        else:
            raise TypeError("argument 'new_center' of non-list type")

    def set_radius(self, new_radius):
        """
        changes radius of arc travel to new_radius

        :param new_radius: new radius of arc travel
        :type new_radius: int, float
        """
        err_msg = "Error in arc.set_radius(): "
        # ensuring valid new_radius argument
        if isinstance(new_radius, (int, float)):
            self.radius = new_radius
        else:
            raise TypeError("argument 'new_radius' of non-int, non-float type")

    def set_start_angle(self, new_start_angle):
        """
        changes starting angle of arc travel

        :param new_start_angle: new starting angle of arc travel from +x axis (degrees)
        :type new_start_angle: int, float
        """
        err_msg = "Error in arc.set_start_angle(): "
        # ensuring valid new_start_angle argument
        if isinstance(new_start_angle, (int, float)):
            if 0 <= new_start_angle < 360:
                self.start_angle = new_start_angle
            else:
                raise ValueError("argument 'new_start_angle' pass value out of range [0, 360]")
        else:
            raise TypeError("argument 'new_start_angle' of non-int, non-float type")

    def set_end_angle(self, new_end_angle):
        """
        changes ending angle of arc travel

        :param new_end_angle: new ending angle of arc travel from +x axis (degrees)
        :type new_end_angle: int, float
        """
        err_msg = "Error in arc.set_end_angle(): "
        # ensuring valid new_end_angle argument
        if isinstance(new_end_angle, (int, float)):
            if 0 <= new_end_angle < 360:
                self.end_angle = new_end_angle
            else:
                raise ValueError("argument 'new_end_angle' pass value out of range [0, 360]")
        else:
            raise TypeError("argument 'new_end_angle' of non-int, non-float type")

    def set_direction(self, new_direction):
        """
        changes direction of arc travel

        :param new_direction: new direction of arc travel
        :type new_direction: "c", "cc"
        """
        err_msg = "Error in arc.set_direction(): "
        # ensuring valid new_direction argument
        if new_direction in ("c", "cc"):
            self.direction = new_direction
        else:
            raise TypeError("argument 'new_direction' must be string \"c\" (clockwise) or \"cc\" (counter-clockwise)")

    def print(self):
        """
        prints key arc values to the console. Useful for debugging/getting info about an Arc object
        """
        print("\n------------------------------------------")
        print("Defining Values:")
        print("\tCenter Point: (", self.center[0], ", ", self.center[1], ")", sep="")
        print("\tRadius: ", self.radius, sep="")
        print("\tStarting Angle: ", self.start_angle, " degrees", sep="")
        print("\tEnding Angle: ", self.end_angle, " degrees", sep="")
        direction_full = "clockwise"
        if self.direction == "cc":
            direction_full = "counter_clockwise"
        print("\tDirection: ", direction_full, sep="")
        print("------------------------------------------")
        print("Angle traced out by arc: ", self.get_angle(), " degrees", sep="")
        print("------------------------------------------")

    # def plot(self):
    #     """
    #     plots arc travel in new window using matplotlib
    #     """
    #     # setting offsets based on center
    #     x_offset = self.center[0]
    #     y_offset = self.center[1]
    #     # determining start/end angles for arc plotting
    #     if np.abs(self.start_angle - self.end_angle) < 0.001:  # approximate equality, given inaccuracy of floats
    #         if self.direction == "cc":
    #             theta_1 = self.start_angle * (np.pi / 180)
    #             theta_2 = (self.end_angle + 360) * (np.pi / 180)
    #         else:
    #             theta_1 = (self.start_angle + 360) * (np.pi / 180)
    #             theta_2 = self.end_angle * (np.pi / 180)
    #     elif self.start_angle > self.end_angle and self.direction == "cc":
    #         theta_1 = self.start_angle * (np.pi / 180)
    #         theta_2 = (self.end_angle + 360) * (np.pi / 180)
    #     elif self.start_angle < self.end_angle and self.direction == "c":
    #         theta_1 = (self.start_angle + 360) * (np.pi / 180)
    #         theta_2 = self.end_angle * (np.pi / 180)
    #     else:
    #         theta_1 = self.start_angle * (np.pi / 180)
    #         theta_2 = self.end_angle * (np.pi / 180)
    #     # defining points to plot:
    #     t_vals = np.linspace(theta_1, theta_2, num=360)
    #     path_points = ((self.radius * np.cos(t_vals)) + x_offset, (self.radius * np.sin(t_vals)) + y_offset)
    #     start_point = ((self.radius * np.cos(theta_1)) + x_offset, (self.radius * np.sin(theta_1)) + y_offset)
    #     end_point = ((self.radius * np.cos(theta_2)) + x_offset, (self.radius * np.sin(theta_2)) + y_offset)
    #     # setting aspect ratio
    #     ax = plt.gca()
    #     ax.set_aspect(1)
    #     # plotting and showing
    #     plt.plot(path_points[0], path_points[1], "b", label="path")
    #     plt.plot(start_point[0], start_point[1], "ro", label="start", alpha = 0.5)
    #     plt.plot(end_point[0], end_point[1], "go", label="end", alpha=0.5)
    #     plt.legend()
    #     plt.show()


# debug station
if __name__ == "__main__":
    arc = Arc(center=[0, 0], radius=1.0, start_angle=0, end_angle=180, direction="cc")
    arc.print()
