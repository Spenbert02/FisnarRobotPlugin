import copy
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D


def readFisnarCommandsFromFile(file_abspath):
    """
    this will break down if the file doesn't exist. This is for development,
    so just make sure the file exists. Returns a 2D array of fisnar commands in the expected format
    """

    # get the csv cells into a 2D array (again, no error checking)
    csv_file = open(file_abspath, "r")
    command_str = csv_file.read()
    commands = [line.split(",") for line in command_str.split("\n")]

    # converting all 2D array entries into proper types
    i = 0
    while i < len(commands):
        if commands[i][0] == "Output":
            for j in range(1, 3):
                commands[i][j] = int(commands[i][j])
        elif commands[i][0] == "Dummy Point":
            for j in range(1, 4):
                commands[i][j] = float(commands[i][j])
        elif commands[i][0] == "Line Speed":
            commands[i][1] = float(commands[i][1])
        elif commands[i][0] == "Z Clearance":
            commands[i][1] = int(commands[i][1])
        elif commands[i][0] == "End Program":
            pass
        else:
            commands.pop(i)
            i -= 1
            print("Unexpected command: " + str(commands[i][0]))  # for debugging
        i += 1

    # # TEST
    # for command in commands:
    #     print(str(command))

    return copy.deepcopy(commands)


def getFisnarSegmentedExtrusionCoords(fisnar_command_list):
    """
    get a segmented version of the commands, with each sub-list containing a series of coordinates which involve
    extrusion, as well as the output number. Connecting the coordinates gives the material path. The returned list
    is of the form:

    [ [<output int>, [[<x float 1>, <y float 1>, <z float 1>], ... , [<x float n>, <y float n>, <z float n>]] ],
      ...
    ]

    :param fisnar_command_list: 2D list - fisnar commands
    :type fisnar_command_list: list[list[str, int]]
    :return: new list object with all non-extruding movements removed.
    :rtype: list[list[str/int]]
    """

    ret_segments = []
    fisnar_commands_copy = copy.deepcopy(fisnar_command_list)

    i = 0  # iterator
    while i < len(fisnar_commands_copy):
        if fisnar_commands_copy[i][0] == "Output" and fisnar_commands_copy[i][2] == 1:  # until 'output on' found
            sub_segment = [fisnar_commands_copy[i][1], []]

            # finding the most recent travel coords and appending
            prev_coords_ind = i - 1
            while fisnar_commands_copy[prev_coords_ind][0] != "Dummy Point":
                prev_coords_ind -= 1
            sub_segment[1].append([fisnar_commands_copy[prev_coords_ind][1],
                                   fisnar_commands_copy[prev_coords_ind][2],
                                   fisnar_commands_copy[prev_coords_ind][3]])

            # appending all movements until output is turned off
            i += 1
            while not (fisnar_commands_copy[i][0] == "Output" and fisnar_commands_copy[i][2] == 0):
                if fisnar_commands_copy[i][0] == "Dummy Point":
                    sub_segment[1].append([fisnar_commands_copy[i][1],
                                           fisnar_commands_copy[i][2],
                                           fisnar_commands_copy[i][3]])
                i += 1

            # appending segment to return segment list
            ret_segments.append(sub_segment)
        else:  # current command isn't output on, so keep searching
            i += 1

    return ret_segments


def plotCoordinates(coord_segments, coord_limits, window_title):
    """
    given a list of coordinate sequences in the format:
    [
        [ <color int>, [[x1, x2, ...], [y1, y2, ...], [z1, z2, ...]]],
        [ <color int>, [[x1, x2, ...], [y1, y2, ...], [z1, z2, ...]]],
        ...
    ]
    and a list of limit coordinates in the format:
    [xmin, xmax, ymin, ymax, zmin, zmax]
    plots each sub list as a continuous 3d line, effectively showing a preview of the print

    :param window_title: string to put as the title of the plot window
    :type window_title: str
    :param coord_limits: 2d list of coordinate limits (print area boundaries)
    :type coord_limits: list
    :param coord_segments: array of 3d coordinate sequences
    :type coord_segments: list
    :return: none
    :rtype: none
    """

    # setting up figure
    fig = plt.figure(window_title)

    # setting up plot
    ax = fig.add_subplot(projection="3d")

    # adding ranges, entered (max, min) to invert axes
    x_padding = (coord_limits[1] - coord_limits[0]) * .10  # 10% padding
    y_padding = (coord_limits[3] - coord_limits[2]) * .10  # 10% padding
    z_padding = (coord_limits[5] - coord_limits[4]) * .10  # 10% padding
    ax.set_xlim(coord_limits[1] + x_padding, coord_limits[0] - x_padding)
    ax.set_ylim(coord_limits[3] + y_padding, coord_limits[2] - y_padding)
    ax.set_zlim(coord_limits[5], coord_limits[4] - z_padding)

    # adding axis labels
    ax.set_xlabel('x')
    ax.set_ylabel('y')
    ax.set_zlabel('z')

    # plotting build area boundary (front-left, back-left, back-right, front-right, front-left)
    x_bound = np.array([coord_limits[1], coord_limits[1], coord_limits[0], coord_limits[0], coord_limits[1]])
    y_bound = np.array([coord_limits[3], coord_limits[2], coord_limits[2], coord_limits[3], coord_limits[3]])
    z_bound = np.array([coord_limits[5], coord_limits[5], coord_limits[5], coord_limits[5], coord_limits[5]])
    ax.plot(x_bound, y_bound, z_bound, color="#000000")

    # making plots equal scale
    ax.set_box_aspect([lb - ub for lb, ub in (getattr(ax, f'get_{a}lim')() for a in 'xyz')])

    # getting rid of gridlines
    plt.grid("False")

    # figuring out colors
    colors = ["b", "g", "r", "y"]

    # iterating through coordinates and plotting coordinate sequences as lines
    existing_outputs = [False, False, False, False]  # of the form [output 1, output 2, output 3, output 4]
    for segment in coord_segments:
        existing_outputs[segment[0] - 1] = True
        color = colors[segment[0] - 1]
        x = np.array(segment[1][0])  # converting to numpy arrays
        y = np.array(segment[1][1])
        z = np.array(segment[1][2])

        ax.plot(x, y, z, color=color, lw=2)

    # turning off grid lines
    ax.grid(False)
    plt.axis("off")

    # setting up legend
    custom_lines = []
    custom_labels = []
    for i in range(len(existing_outputs)):
        if existing_outputs[i]:
            custom_lines.append(Line2D([0], [0], color=colors[i], lw=3))
            custom_labels.append("Output " + str(i + 1))
    ax.legend(custom_lines, custom_labels)

    # showing plot
    plt.show()


if __name__ == "__main__":
    fisnar_csv_abspath = "C:\gcode2fisnar_tests\cura_plugin_tests\CFFFP_3_18_2022_three_line_test_file.csv"
    fisnar_commands = readFisnarCommandsFromFile(fisnar_csv_abspath)
    fisnar_segmented_coords = getFisnarSegmentedExtrusionCoords(fisnar_commands)

    plot_segments = []
    for i in range(len(fisnar_segmented_coords)):
        coords = [[], [], []]
        for j in range(len(fisnar_segmented_coords[i][1])):
            coords[0].append(fisnar_segmented_coords[i][1][j][0])
            coords[1].append(fisnar_segmented_coords[i][1][j][1])
            coords[2].append(fisnar_segmented_coords[i][1][j][2])
        plot_segments.append([fisnar_segmented_coords[i][0], coords])


    plotCoordinates(plot_segments, [0, 200, 0, 200, 0, 100], "FisnarCSVWriter Developer File Output Testing")
