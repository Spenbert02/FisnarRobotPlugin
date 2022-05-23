# Functional classes
Included in this plugin are several custom-written python classes. The plugin itself
is just two classes - once Cura is started, it creates 'singleton' instances
of these classes that represent the plugin (to read more about this, refer to the
documentation describing the [flow of control](flow_of_control.md) in Cura plugins).
Aside from these classes that 'are' the plugin, a few classes were written to
help with different tasks within the plugin. These are described below.

## AutoUploader
The AutoUploader class handles execution of the auto upload process. The
FisnarCSVParameterExtension object creates an instance of an AutoUploader
when instantiated. When the 'Start auto upload process' menu item is clicked,
an AutoUploader method is called that starts the auto upload process. The
AutoUploader object then begins an internal process where the auto upload
procedure is executed.

Most of the methods in this class deal with setting the user interface during
the auto-upload process. There are also methods for sub-tasks in the auto-upload
process - for example, opening the 'Smart Robot Edit' app. This class also contains
a few static utility methods. One of these methods takes in a list of Fisnar
commands and returns the commands in a copyable CSV string format (this allows
the AutoUploader to copy the commands into the Smart Robot Edit software). The
other static method takes a list of Fisnar commands and segments them into 'chunks'
of 4000 or less commands. It then returns the segments in a list, that can be
sequentially uploaded during the auto upload process.

## handledPolygon
The handledPolygon class is a simple child class of Uranium's Polygon class.
This class doesn't do anything crazy, and exists only for identification purposes.
When the 'Set print area' menu item is clicked and specific printable coordinates
are entered, the FisnarCSVParameterExtension instantiation calls a method on the
main CuraApplication instance (which is also a 'singleton', as described above) that sets
the disallowed areas on the build plate. This method takes a Polygon object,
which is pretty much just a set of x and y coordinates describing a shape on the
build plate. Internally, the CuraApplication instance stores these Polygon objects
and uses the areas they define to 'grey out' certain areas on the build plate.
The problem arises when trying to change the user-set printable area. If coordinates
have already been entered, a Polygon object will exist in the CuraApplication
that defines the user-set greyed-out areas. However, there is no way to know
which of these Polygon objects was created because of the plugin. Therefore,
there is no way to know which Polygon object needs to be deleted before implementing
the new one. This class solves the issue - instead of passing a Polygon object
to the CuraApplication instance, it passes a handledPolygon object instead (which
works because of polymorphism). Then, if the user enters different coordinates,
the plugin will know which disallowed area to delete - any handledPolygon objects
could only have been set by the plugin, so they need to be cleared before
setting new ones.
