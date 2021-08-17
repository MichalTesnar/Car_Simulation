# Overview
Python code for a selfdriving car. Can be used for both real-life and simulation purposes <br/>
I (thijs) made this branch becuase of the major overhaul i did (in july 2021). The code in the 'thijs-update' is largely similar, but far more single-core (and a few more bugs, hopefully). This version does everything it used to (coneconnecting, pathfinding, pathplanning (simple auto-driving and making splines)) and more (lidar, 3Dish rendering (over a camera frame(?), bugfixes), while making as much use of the python multiprocessing library as possible (for true multicore (not just multithread singlecore) performance). The downside of this is that python is really not meant for any of it. Switching to another (faster) language is mostly hindered by the need to find an alternative to pygame. The speed of the code is now hampered by the fact that it needs to spend a lot of time on inter-core communications (which all involve pickling, because python won't let you share objects directly).
Python 3.8 or higher is required, because shared_memory is used.
numba is recommended, but there are backup files in case you're having difficulty installing it (understandable on a Rpi/Jetson)
use the "july.py" file to launch the whole thing (the rest are only components of it)

requirements:
 - python 3.8+ (must be 3.8+ for shared_memory (multiprocessing))
 - numpy 
 - pandas (for map_loader)
 - pygame 2.0.1 (for map visualization)
 - pyserial (only for real-life, not for simulations) (note: used as "import serial")
 - scipy (for cubic splines (pathPlanning))
 - PIL (a.k.a. Python Image Library, a.k.a. Pillow, only used for rendering headlights)
 - numba (used to make some code faster, there are usually NoNumba versions of things though)
