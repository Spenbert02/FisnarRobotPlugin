def get_fisnar_commands(**kwargs):
    """
    get a list of the fisnar commands with a specified filter

    :param xyz: set to True to only return commands that take in x, y, and z coordinates
    :type xyz: bool
    """

    filters = []  # list to store filters
    kwarg_keys = ["xyz"]

    for key in kwargs:  # translating kwargs to filters
        if isinstance(kwargs[key], bool) and kwargs[key]:  # if kwargs was assigned with True
            if key in kwarg_keys:
                filters.append(key)

    # all commands accepted by the fisnar software
    all_commands = {"Arc Point": ["xyz"],
                    "Brush Area": [],
                    "Call Program": [],
                    "Call Subroutine": ["xyz"],
                    "Circle(Lift)": ["xyz"],
                    "Circle(No Lift)": ["xyz"],
                    "Dispense Dot": ["xyz"],
                    "Dispense End Setup": [],
                    "Dispense On/Off": [],
                    "Dispense Output": [],
                    "Display Counter": [],
                    "Dummy Point": ["xyz"],
                    "End Program": [],
                    "GoTo Address": [],
                    "Home Point": [],
                    "Input": [],
                    "Label": [],
                    "Line Dispense": [],
                    "Line End": ["xyz"],
                    "Line Passing": ["xyz"],
                    "Line Speed": [],
                    "Line Start": ["xyz"],
                    "Loop Address": [],
                    "Loop Counter": [],
                    "Output": [],
                    "Point Dispense": [],
                    "Retract": [],
                    "Step and Repeat X": [],
                    "Step and Repeat Y": [],
                    "Stop Point": [],
                    "Wait Point": [],
                    "Z Clearance": []}

    ret_command_list = []  # list to append commands to and return

    for key in all_commands:  # for each command in dictionary
        meets_reqs = True
        for req in filters:
            if req not in all_commands[key]:
                meets_reqs = False
        if meets_reqs:  # if command passes all filters
            ret_command_list.append(key)

    return ret_command_list


# debug station
if __name__ == "__main__":
    print(get_fisnar_commands(xyz=True))
