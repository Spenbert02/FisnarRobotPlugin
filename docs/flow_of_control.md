# Cura plugin flow of control
This document describes the flow of control of Cura plugins, and how they are
structured.

## What is a 'plugin'?
As far as Cura is concerned, a plugin is just a class that inherits from one of
Uranium's built-in plugin types. To learn more about Uranium's built in plugin
classes, look [here](https://github.com/Ultimaker/Uranium/wiki/Plugin-Types).
As far as files go, there are at least three files that are needed for any
plugin: an \_\_init\_\_.py file, a plugin.json file, and a python file for the
actual plugin class. These files will be described below, but I would recommend
reading [Uranium's documentation](https://github.com/Ultimaker/Uranium/wiki/Creating-plugins) about plugins first.

## plugin.json
The plugin.json file is pretty simple - basically it holds information about the
plugin that Cura can show to the user to describe it. This information includes
the plugin name, author, version, language, and Cura version.

## \_\_init\_\_.py file
This is the initialization file that Cura knows to look for, that it uses
to get access to the plugin class. As noted in the [Uranium documentation](https://github.com/Ultimaker/Uranium/blob/main/docs/plugins.md), the init file must have two functions: getMetaData()
and register(). The getMetaData() function returns information about the plugin
that is dependent upon what type it is. Actually, it returns information about
all plugin classes - I haven't mentioned it yet, but this plugin actually uses
two plugin classes: FisnarCSVWriter (which extends the MeshWriter class) and
FisnarCSVParameterExtension (which extensions the Extension class). The former
deals with saving the slicer output in the form of a CSV of Fisnar commands, and
the latter deals with setting up the menus and windows for the user to interact
with.

Anyway, the getMetaData() function returns information about both of these. The
register function is what actually 'creates' the plugin inside of Cura. When Cura
boots up, it will go through the list of plugins that have been installed (the
plugin registry) and instantiate a 'singleton' object for the plugin classes
associated with each. In the case of this plugin, when Cura calls the register()
function, an object of type FisnarCSVWriter and an object of type FisnarCSVParameterExtension
will be returned. Cura then holds on to these and does what it needs to with
them (usually, the classes will have certain methods that cura knows to look
for that it will call on the object, depending on the type of plugin).

## Plugin python file
As mentioned, this plugin is actually two plugin classes. Each of these has their
own class definition file, and the name of that file is the same as the name of
the plugin. Different plugin types will have very different looking plugin classes.
In the case of this plugin, the FisnarCSVWriter class is a MeshWriter, so it must have a
write() function, which Cura will call when it wants to save the slicer output
into a Fisnar CSV. The FisnarCSVParameterExtension class, on the other hand, is
an Extension, so it has quite a few functions that deal with setting up elements
of the user interface and giving information to/taking information from the user
interface.
