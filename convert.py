from .gcodeBuddy.marlin import Command
from UM.Logger import Logger


# # this will be implemented later on. TODO!
# def updateUnits(gcode_commands, factor):
#     # convert all units to mm, mm/s, and mm/s^2 (what fisnar printers accept)
#     pass


def getStrippedCommands(gcode_lines):
    # convert a list of gcode lines (in string form) to a list of gcode Command objects
    # commands a subsequently stripped of comments and empy lines. Only commands are interpreted
    ret_command_list = []  # list to hold Command objects
    for line in gcode_lines:
        line = line.strip()  # removing whitespace from both ends of string
        if len(line) > 0 and line[0] != ";":  # only considering non comment and non empty lines
            if ";" in line:
                line = line[:line.find(";")]  # removing comments
            line = line.strip()  # removing whitespace from both ends of string
            ret_command_list.append(Command(line))

    return ret_command_list


def getExtrudersInGcode(gcode_str):
    # get the extruders used in the gcode file in a list of bools [extruder 1, extruder 2, extruder3, extruder 4]

    gcode_commands = getStrippedCommands(gcode_str.split("\n"))

    # log_command_str = ""  # test
    # for command in gcode_commands:
    #     log_command_str += ", " + command.get_string()
    # Logger.log("i", "***** in convert.getExtrudersInGcode: gcode commands are: " + log_command_str)

    ret_extruders = [False, False, False, False]
    for command in gcode_commands:
        if command.get_command()[0] == "T":
            ret_extruders[int(command.get_command()[1])] = True

    return ret_extruders  # extruder 1 is T0, extruder 2 is T1, etc etc so the max T is one less than the number of extruders


def getFirstExtrudingCommandIndex(gcode_commands):
    # get the index of the first g0/g1 command that extrudes.
    # this command must be g0/g1, have an x or y or z parameter, and have a non-zero e parameter.
    for i in range(len(gcode_commands)):
        command = gcode_commands[i]
        if command.get_command() in ("G0", "G1"):
            if command.has_param("X") or command.has_param("Y") or command.has_param("Z"):
                if command.has_param("E") and (command.get_param("E") > 0):
                    return i
    return None  # no extruding commands. Don't know how a gcode file wouldn't have an extruding command but just in case


def getFirstPositionalCommandIndex(gcode_commands):
    # get the index of the command that is the start of the first extruding movement.
    # this is the last command before the first extruding movement command that doesn't extrude
    # this command must have no e parameter (or zero e parameter), and have an x and y and z parameter
    first_extruding_index = getFirstExtrudingCommandIndex(gcode_commands)
    if first_extruding_index is None:
        return None  # shouldn't ever happen in a reasonable gcode file

    for i in range(first_extruding_index, -1, -1):
        command = gcode_commands[i]
        if command.get_command() in ("G0", "G1"):
            if command.has_param("X") and command.has_param("Y") and command.has_param("Z"):
                if not (command.has_param("E") and command.get_param("E") > 0):
                    return i
    return None  # this could be for a variety of reasons, some of which aren't that unlikely. This way of doing things is kind of ghetto. Ultimately, a more sophisticated solution should be enacted.


def getLastExtrudingCommandIndex(gcode_commands):
    # get the last command that extrudes material - the last command that needs to be converted.
    # this command must have an x and/or y and/or z parameter, and have a nonzero e parameter
    for i in range(len(gcode_commands) - 1, -1, -1):
        command = gcode_commands[i]
        if command.get_command() in ("G0", "G1"):
            if command.has_param("X") or command.has_param("Y") or command.has_param("Z"):
                if command.has_param("E") and command.get_param("E") > 0:
                    return i
    return None  # this should never happen in any reasonable gcode file.


def optimize_fisnar_commands(fisnar_commands):
    # remove any redundant commands from fisnar command list
    pass


def g0_g1(command, curr_output, curr_pos):
    # turn a g0 or g1 command into a list of the corresponding fisnar commands
    # update the given curr_pos list
    ret_commands = []

    if command.has_param("E") and command.get_param("E") > 0:  # turn output on
        ret_commands.append(["Output", curr_output, 1])
    else:  # turn output off
        ret_commands.append(["Output", curr_output, 0])

    x, y, z = curr_pos[0], curr_pos[1], curr_pos[2]
    if command.has_param("X"):
        x = command.get_param("X")
    if command.has_param("Y"):
        y = command.get_param("Y")
    if command.has_param("Z"):
        z = command.get_param("Z")

    curr_pos = [x, y, z]
    ret_commands.append(["Dummy Point", x, y, z])

    return ret_commands


def invert_coords(commands):
    # invert all coordinate directions for dummy points (modifies the given list)

    for i in range(len(commands)):
        command = commands[i]
        if command[0] == "Dummy Point":
            command[1] = 200 - command[1]
            command[2] = 200 - command[2]
            command[3] = 100 - command[3]


def offset_z(commands, offset):
    # apply the specified offset to all z coordinates of dummy points (modifies the given list)
    for i in range(len(commands)):
        command = commands[i]
        if command[0] == "Dummy Point":
            command[3] = command[3] + offset


def convert(gcode_commands, extruder_outputs, z_max):
    # convert gcode to fisnar command 2d list. Assumes the extruder outputs given are valid.
    # returns tuple(False, "error message string") if conversion goes awry. It shouldn't tho.
    # currently (3/31), error checking will not be thoroughly implemented, as this should all
    # occur before the parameters are passed to this function

    gcode_commands = getStrippedCommands(gcode_commands.split("\n"))
    first_relevant_command_index = getFirstPositionalCommandIndex(gcode_commands)
    last_relevant_command_index = getLastExtrudingCommandIndex(gcode_commands)

    # # test
    # ret_string = ""
    # for i in range(first_relevant_command_index, last_relevant_command_index + 1):
    #     ret_string += "," + gcode_commands[i].get_string()
    # Logger.log("i", "relevant_commands: " + ret_string)

    # default fisnar initial commands
    fisnar_commands = [["Line Speed", 30], ["Z Clearance", 3, 1]]

    # finding first extruder used in gcode
    curr_extruder = 0
    for command in gcode_commands:
        if command.get_command()[0] == "T":
            curr_extruder = int(command.get_command()[1])
            break

    curr_pos = [0, 0, 0]
    curr_speed = 30
    for i in range(len(gcode_commands)):
        command = gcode_commands[i]

        if command.has_param("F") and command.get_param("F") != curr_speed:  # line speed change
            fisnar_commands.append(["Line Speed", command.get_param("F")])
            curr_speed = command.get_param("F")

        if (first_relevant_command_index <= i <= last_relevant_command_index):  # command needs to be converted
            if command.get_command() in ("G0", "G1"):
                new_commands = g0_g1(command, extruder_outputs[curr_extruder], curr_pos)
                for command in new_commands:
                    fisnar_commands.append(command)
            elif command.get_command() in ("G2", "G3"):
                pass  # might implement eventually. probably not, these are _rarely_ used.
            elif command.get_command() == "G90":
                pass  # assuming all commands are absolute coords for now.
            elif command.get_command() == "G91":
                pass  # assuming all commands are absolute coords for now.
            elif command.get_command()[0] == "T":
                curr_extruder = int(command.get_command()[1])

    fisnar_commands.append(["End Program"])

    # inverting and shifting coordinate system from gcode to fisnar
    invert_coords(fisnar_commands)
    offset_z(fisnar_commands, -(100 - z_max))

    return fisnar_commands
