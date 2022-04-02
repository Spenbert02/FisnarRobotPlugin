import sys
import numpy as np

from . import angle, Arc, centers_from_params

from UM.Logger import Logger

class Command:
    """
    represents line of Marlin g-code

    :param init_string: line of Marlin g-code
    :type init_string: str
    """

    def __init__(self, init_string):
        """
        initialization method
        """

        err_msg = "Error in marlin.gcode_command.__init__(): "

        no_parameter_commands = ["M84"]  # list of commands that don't require a value after the parameters

        if len(init_string) == 0:
            raise ValueError("initialization string can't be empty")

        # removing extraneous spaces
        command_string = init_string
        while command_string[0] == " ":
            command_string = command_string[1:]
        while command_string[-1] == " ":
            command_string = command_string[:-1]
        ind = 0
        while (ind + 1) < len(command_string):
            if command_string[ind] == " " and command_string[ind + 1] == " ":
                command_string = command_string[:ind] + command_string[(ind + 1):]
            else:
                ind += 1

        # ensuring valid command
        command_list = command_string.split(" ")
        if command_list[0] in marlin_commands():
            self.command = command_list[0]
            command_list = command_list[1:]
        else:
            raise ValueError("Unrecognized Marlin command passed in argument 'init_string': " + str(command_list[0]))

        self.params = dict()  # a dictionary storing param - values pairs (ie. {"x": 0, ... }
        for parameter_str in command_list:
            if parameter_str[0].isalpha():
                if self.command in no_parameter_commands:
                    self.params[parameter_str.upper()] = 0
                else:
                    try:
                        float(parameter_str[1:])
                    except ValueError:
                        raise TypeError("Marlin parameter passed in argument 'init_string' of non-int/non-float type")
                    else:
                        self.params[parameter_str[0].upper()] = float(parameter_str[1:])
            else:
                raise ValueError("Unrecognized Marlin parameter passed in argument 'init_string'")

    def get_command(self):
        """
        :return: g-code command
        :rtype: str
        """
        return self.command

    def has_param(self, param_char):
        """
        :param param_char: parameter character to search for in g-code command
        :type param_char: str
        :return: whether the Command object has the given parameter
        :rtype: bool
        """
        err_msg = "Error in marlin.gcode_command.has_param(): "
        # ensuring string passed
        if isinstance(param_char, str):
            return param_char.upper() in self.params
        else:
            raise TypeError("Argument 'param_char' of non-string type")

    def get_param(self, param_char):
        """
        :param param_char: parameter character to search for in g-code command
        :type param_char: str
        :return: value of parameter character stored in g-code command
        :rtype: float
        """
        err_msg = "Error in marlin.gcode_command.get_param(): "
        # ensuring param_char is string, and is in self.params
        if isinstance(param_char, str):
            if param_char in self.params:
                return self.params[param_char]
            else:
                raise ValueError("Command does not contain Marlin parameter given in argument 'param_char'")
        else:
            raise TypeError("Argument 'param_char' of non-string type")

    def set_param(self, param_char, param_val):
        """
        sets parameter value

        :param param_char: parameter character to change value
        :type param_char: str
        :param param_val: parameter value to set
        :type param_val: int, float
        """
        err_msg = "Error in marlin.gcode_command.set_param(): "
        # ensuring param_char is string and is in self.params and param_val is number
        if isinstance(param_char, str):
            if isinstance(param_val, (int, float)):
                if param_char in self.params:
                    self.params[param_char] = param_val
                else:
                    raise ValueError("Command does not contain Marlin parameter given in argument 'param_char'")
            else:
                raise TypeError("Argument 'param_val' of non-int/non-float type")
        else:
            raise ValueError("Argument 'param_char' of non-string type")

    def get_string(self):
        """
        :return: entire g-code command in line form
        :rtype: string
        """
        ret_val = self.command
        for param_key in self.params:
            ret_val += " " + param_key + str(self.params[param_key])
        return ret_val


def command_to_arc(curr_pos, command):
    """
    converts G2/G3 Marlin g-code command to Arc object

    :param curr_pos: position of toolhead before given command
    :type curr_pos: list[int, float], tuple(int, float)
    :param command: G2/G3 command
    :type command: Command
    :return: arc toolpath travel corresponding to given g-code command
    :rtype: Arc
    """

    err_msg = "Error in marlin.command_to_arc(): "

    # error checking curr_pos
    if isinstance(curr_pos, (list, tuple)):
        if len(curr_pos) == 2:
            valid_types = True
            for coord in curr_pos:
                if not isinstance(coord, (int, float)):
                    valid_types = False
            if not valid_types:
                raise TypeError("Element in argument 'curr_pos' of non-int/non-float type")
        else:
            raise ValueError("Argument 'curr_pos' does not contain two elements")
    else:
        raise TypeError("Argument 'curr_pos' of non-list/non-tuple type")

    # error checking command - error checking done in Command.__init__(), just need to make sure command is passed
    if not isinstance(command, Command):
        raise TypeError("Argument 'command' of non-Command type")
    if command.get_command() not in ("G2", "G3"):
        raise ValueError("Command must be 'G2' or 'G3' for arc conversion")

    # organizing parameters into list (for error checking)
    param_list =[]
    for letter in "XYIJR":
        if command.has_param(letter):
            param_list.append(letter)

    # setting direction
    direction = "c"
    if command.get_command() == "G3":
        direction = "cc"

    if ("I" in param_list) or ("J" in param_list):  # I and J parameters
        # more error checking
        if "R" in param_list:
            raise ValueError("Command cannot mix parameter 'R' with parameters 'I' and 'J' for arc conversion")
        # if only given I, J, or I and J
        if ("X" not in param_list) and ("Y" not in param_list):
            if param_list == ["I"]:  # I
                I = command.get_param("I")
                center = [curr_pos[0] + I, curr_pos[1]]
                radius = I
                start_angle = angle(center, curr_pos)
                end_angle = angle(center, curr_pos)
                return Arc(center=center,
                           radius=radius,
                           start_angle=start_angle,
                           end_angle=end_angle,
                           direction=direction)
            elif param_list == ["J"]:  # J
                J = command.get_param("J")
                center = [curr_pos[0], curr_pos[1] + J]
                radius = J
                start_angle = angle(center, curr_pos)
                end_angle = angle(center, curr_pos)
                return Arc(center=center,
                           radius=radius,
                           start_angle=start_angle,
                           end_angle=end_angle,
                           direction=direction)
            else:  # I J
                I = command.get_param("I")
                J = command.get_param("J")
                center = [curr_pos[0] + I, curr_pos[1] + J]
                radius = np.sqrt(I**2 + J**2)
                start_angle = angle(center, curr_pos)
                end_angle = angle(center, curr_pos)
                return Arc(center=center,
                           radius=radius,
                           start_angle=start_angle,
                           end_angle=end_angle,
                           direction=direction)
        # if given X and I or Y and J (require more intricate handling)
        if param_list == ["X", "I"]:
            X = command.get_param("X")
            I = command.get_param("I")
            if curr_pos[0] + (2 * I) - X < 0.001:
                center = [curr_pos[0] + I, curr_pos[1]]
                radius = abs(I)
                start_angle = angle(center, curr_pos)
                end_angle = angle(center, [X, curr_pos[1]])
                return Arc(center=center,
                           radius=radius,
                           start_angle=start_angle,
                           end_angle=end_angle,
                           direction=direction)
            else:
                raise ValueError("Invalid Command parameters for arc conversion (cannot create arc from given X and I values)")
        elif param_list == ["Y", "J"]:
            Y = command.get_param("Y")
            J = command.get_param("J")
            if curr_pos[1] + (2 * J) - Y < 0.001:
                center = [curr_pos[0], curr_pos[1] + J]
                radius = abs(J)
                start_angle = angle(center, curr_pos)
                end_angle = angle(center, [curr_pos[0], Y])
                return Arc(center=center,
                           radius=radius,
                           start_angle=start_angle,
                           end_angle=end_angle,
                           direction=direction)
            else:
                raise ValueError("Invalid Command parameters for arc conversion (cannot create arc from given Y and J values)")

        # must have X or Y, I or J
        # setting I parameter
        I = 0
        if "I" in param_list:
            I = command.get_param("I")
        # setting J parameter
        J = 0
        if "J" in param_list:
            J = command.get_param("J")
        # setting X parameter
        X = curr_pos[0]
        if "X" in param_list:
            X = command.get_param("X")
        # setting Y parameter
        Y = curr_pos[1]
        if "Y" in param_list:
            Y = command.get_param("Y")
        # returning arc object
        center = [curr_pos[0] + I, curr_pos[1] + J]
        radius = np.sqrt(I**2 + J**2)
        start_angle = angle(center, curr_pos)
        end_angle = angle(center, [X, Y])
        return Arc(center=center,
                   radius=radius,
                   start_angle=start_angle,
                   end_angle=end_angle,
                   direction=direction)
    elif "R" in param_list:  # R parameter
        if "X" in param_list or "Y" in param_list:
            # setting X parameter
            X = curr_pos[0]
            if "X" in param_list:
                X = command.get_param("X")
            # setting Y parameter
            Y = curr_pos[1]
            if "Y" in param_list:
                Y = command.get_param("Y")
            # setting R parameter
            R = command.get_param("R")
            need_smaller = R > 0  # if smaller angle arc necessary
            R = np.abs(R)
            # creating test arc, if is smaller than 180 deg then return, otherwise choose other center and create and return that arc
            if (np.abs(np.sqrt((X - curr_pos[0])**2 + (Y - curr_pos[1])**2)) / 2) > R:  # distance between points greater than radius
                R = (np.abs(np.sqrt((X - curr_pos[0])**2 + (Y - curr_pos[1])**2)) / 2)
            centers = centers_from_params(curr_pos, (X, Y), R)
            # creating test arc
            test_arc = Arc(center=centers[0],
                           radius=R,
                           start_angle=angle(centers[0], curr_pos),
                           end_angle=angle(centers[0], (X, Y)),
                           direction=direction)
            if need_smaller:
                if test_arc.get_angle() <= 180:
                    return test_arc
                else:
                    return Arc(center=centers[1],
                               radius=R,
                               start_angle=angle(centers[1], curr_pos),
                               end_angle=angle(centers[1], (X, Y)),
                               direction=direction)
            else:
                if test_arc.get_angle() <= 180:
                    return Arc(center=centers[1],
                               radius=R,
                               start_angle=angle(centers[1], curr_pos),
                               end_angle=angle(centers[1], (X, Y)),
                               direction=direction)
                else:
                    return test_arc
        else:
            raise ValueError("Invalid Command parameters for arc conversion (X or Y required with R)")
    else:  # no required parameters
        raise ValueError("Invalid Command parameters for arc conversion (I, J, or R is required)")


def marlin_commands():
    """
    :returns: up-to-date Marlin commands, periodically scraped from the Marlin website
    :rtype: tuple(str)
    """

    """
    The following code should be uncommented, and the main function of this file should be run periodically.
    This will pull commands from the marlin website, which will then be printed to console. This will be
    in a tuple format, which can then be copied and pasted in the return value of the function. If it has
    to pull from the website every time this function is called, it takes an extremely long time and is
    an easy source of a difficult to detect error.
    """

    ## opening site and getting BeautifulSoup object
    # gcode_index_url = "https://marlinfw.org/meta/gcode/"
    # gcode_index_client = urlopen(gcode_index_url)
    # gcode_index_html = gcode_index_client.read()
    # gcode_index_client.close()
    #
    # first_command = "G0"
    # last_command = "T6"
    #
    # # parsing through website and extracting commands into list
    # gcode_index_soup = soup(gcode_index_html, "html.parser")
    # commands = gcode_index_soup.findAll("strong")
    # i = 0
    # while True:
    #     if not isinstance(commands[i], str):  # if isn't already string, get text from tag and convert
    #         commands[i] = str(commands[i].get_text())
    #     # splitting up website entries than encompass multiple commands. Will change as Marlin site is updated
    #     multiple_command_entries = (
    #         (  "G0-G1",      "G2-G3",          "G17-G19",                   "G38.2-G38.5",                                        "G54-G59.3",                                 "M0-M1",         "M7-M9",         "M10-M11",      "M18, M84",                                     "M810-M819",                                                                       "M860-M869",                                      "M993-M994",                   "T0-T6"),
    #         (("G1", "G0"), ("G3", "G2"), ("G19", "G18", "G17"), ("G38.5", "G38.4", "G38.3", "G38.2"), ("G59.3", "G59.2", "G59.1", "G59", "G58", "G57", "G56", "G55", "G54"), ("M1", "M0"), ("M9", "M8", "M7"), ("M11", "M10"), ("M84", "M18"), ("M819", "M818", "M817", "M816", "M815", "M814", "M813", "M812", "M811", "M810"), ("M869", "M868", "M867", "M866", "M865", "M864", "M863", "M862", "M861", "M860"), ("M994", "M993"), ("T6", "T5", "T4", "T3", "T2", "T1", "T0"))
    #     )
    #     if commands[i] in multiple_command_entries[0]:
    #         specific_commands = multiple_command_entries[1][multiple_command_entries[0].index(commands[i])]
    #         for command in specific_commands:
    #             commands.insert(i, command)
    #         commands.pop(i + len(specific_commands))
    #     if (len(commands) > (i + 1)) and commands[i] == last_command:
    #         commands = commands[:(i + 1)]
    #         break
    #     if i >= len(commands) - 1:  # safety measure, in case of unexpected website updates
    #         break
    #     i += 1
    #
    # return (tuple(commands))
    # ________________________________________

    return ("G0",
            "G1",
            "G2",
            "G3",
            "G4",
            "G5",
            "G6",
            "G10",
            "G11",
            "G12",
            "G17",
            "G18",
            "G19",
            "G20",
            "G21",
            "G26",
            "G27",
            "G28",
            "G29",
            "G29",
            "G29",
            "G29",
            "G29",
            "G29",
            "G30",
            "G31",
            "G32",
            "G33",
            "G34",
            "G35",
            "G38.2",
            "G38.3",
            "G38.4",
            "G38.5",
            "G42",
            "G53",
            "G54",
            "G55",
            "G56",
            "G57",
            "G58",
            "G59",
            "G59.1",
            "G59.2",
            "G59.3",
            "G60",
            "G61",
            "G76",
            "G80",
            "G90",
            "G91",
            "G92",
            "G425",
            "M0",
            "M1",
            "M3",
            "M4",
            "M5",
            "M7",
            "M8",
            "M9",
            "M10",
            "M11",
            "M16",
            "M17",
            "M18",
            "M84",
            "M20",
            "M21",
            "M22",
            "M23",
            "M24",
            "M25",
            "M26",
            "M27",
            "M28",
            "M29",
            "M30",
            "M31",
            "M32",
            "M33",
            "M34",
            "M42",
            "M43",
            "M43 T",
            "M48",
            "M73",
            "M75",
            "M76",
            "M77",
            "M78",
            "M80",
            "M81",
            "M82",
            "M83",
            "M85",
            "M92",
            "M100",
            "M104",
            "M105",
            "M106",
            "M107",
            "M108",
            "M109",
            "M110",
            "M111",
            "M112",
            "M113",
            "M114",
            "M115",
            "M117",
            "M118",
            "M119",
            "M120",
            "M121",
            "M122",
            "M125",
            "M126",
            "M127",
            "M128",
            "M129",
            "M140",
            "M141",
            "M143",
            "M145",
            "M149",
            "M150",
            "M154",
            "M155",
            "M163",
            "M164",
            "M165",
            "M166",
            "M190",
            "M191",
            "M192",
            "M193",
            "M200",
            "M201",
            "M203",
            "M204",
            "M205",
            "M206",
            "M207",
            "M208",
            "M209",
            "M211",
            "M217",
            "M218",
            "M220",
            "M221",
            "M226",
            "M240",
            "M250",
            "M256",
            "M260",
            "M261",
            "M280",
            "M281",
            "M282",
            "M290",
            "M300",
            "M301",
            "M302",
            "M303",
            "M304",
            "M305",
            "M350",
            "M351",
            "M355",
            "M360",
            "M361",
            "M362",
            "M363",
            "M364",
            "M380",
            "M381",
            "M400",
            "M401",
            "M402",
            "M403",
            "M404",
            "M405",
            "M406",
            "M407",
            "M410",
            "M412",
            "M413",
            "M420",
            "M421",
            "M422",
            "M425",
            "M428",
            "M430",
            "M486",
            "M500",
            "M501",
            "M502",
            "M503",
            "M504",
            "M510",
            "M511",
            "M512",
            "M524",
            "M540",
            "M569",
            "M575",
            "M600",
            "M603",
            "M605",
            "M665",
            "M665",
            "M666",
            "M666",
            "M672",
            "M701",
            "M702",
            "M710",
            "M808",
            "M810",
            "M811",
            "M812",
            "M813",
            "M814",
            "M815",
            "M816",
            "M817",
            "M818",
            "M819",
            "M851",
            "M852",
            "M860",
            "M861",
            "M862",
            "M863",
            "M864",
            "M865",
            "M866",
            "M867",
            "M868",
            "M869",
            "M871",
            "M876",
            "M900",
            "M906",
            "M907",
            "M908",
            "M909",
            "M910",
            "M911",
            "M912",
            "M913",
            "M914",
            "M915",
            "M916",
            "M917",
            "M918",
            "M928",
            "M951",
            "M993",
            "M994",
            "M995",
            "M997",
            "M999",
            "M7219",
            "T0",
            "T1",
            "T2",
            "T3",
            "T4",
            "T5",
            "T6")


# station to pull commands periodically, to update return value of marlin_commands
if __name__ == "__main__":
    commands = marlin_commands()
    print("(", sep="", end="")
    for item in commands[:-1]:
        print("\"" + item + "\", ")
    print("\"" + commands[-1] + "\")")
