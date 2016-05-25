=================
rhodo-plot-mapper
=================

Python code to drive an LTI TruPulse 360R laser range finder for mapping trees and bushes in a Rhododendron study plot.

Runs on a laptop than connects to the range finder.

::

  USDA Forest Service 
  Southern Research Station
  Coweeta Hydrologic Laboratory

  Dave Hawthorne


Typical Usage Sequence
======================

#. Define one or more anchor points and specify their fixed coordinates.
#. Define names and types of other points in the plot (trees, bushes, instruments)
#. Standing at one point take distance and bearing to other points that are visible
#. Move to another point and repeat
#. Run the solver to determine coordinates of point  from the web of beaing measurements.
#. Save the coordinates to spreadsheet

Various Features
================

* designed for this device: http://www.lasertech.com/TruPulse-Laser-Rangefinder.aspx
* uses pyttsx (https://github.com/parente/pyttsx) for voice output
* Range finder is driven from the Bluetooth interface
* Readings and map points are saved to XLSX files

