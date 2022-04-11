# functions dealing with the autoupload process for the smart robot edit software.

from .FisnarCSVParameterExtension import FisnarCSVParameterExtension

def chunk_commands(fisnar_commands, command lim):
    # given a 2D list of fisnar commands, return a list of sub-2d arrays
    # that are standalong 'chunks' that can be uploaded to the printer
    # one by one
    pass


def open_smart_robot():
    # open the smart robot edit software (and bring to the front of the screen)
    pass


def maximize_smart_robot():
    # maximize the smart robot edit software window
    pass


def paste_chunk(chunk):
    # given a 2d list of fisnar commands, copy them to the clipboard and
    # paste into the necessary spot in the fisnar smart robot edit software
    # screen
    pass


def show_waiting_window():
    pass
