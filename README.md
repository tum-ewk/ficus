# ficus

ficus is a ([mixed integer](https://en.wikipedia.org/wiki/Integer_programming)) [linear programming](https://en.wikipedia.org/wiki/Linear_programming) optimization model for capacity expansion planning and unit commitment for local energy systems. Based on [URBS](https://github.com/tum-ens/urbs) and [VICUS](https://github.com/ojdo/vicus) it was developed as a model for optimising energy systems of factories.

[![Documentation Status](https://readthedocs.org/projects/ficus/badge/?version=latest)](https://ficus.readthedocs.org/en/latest/)  [![DOI](https://zenodo.org/badge/18757/yabata/ficus.svg)](https://zenodo.org/badge/latestdoi/18757/yabata/ficus)

## Publication

[D. Atabay: An open-source model for optimal design and operation of industrial energy systems, Energy, 121 (2017), 803–821](http://dx.doi.org/10.1016/j.energy.2017.01.030)

## Features

  * ficus is a (mixed integer) linear programming model for a multi-commodity energy system of a factory.
  * It finds the minimum cost energy system to satisfy given demand time-series for possibly multiple commodities (e.g. electricity, heat)
  * It considers given cost time-series for external obtained commodities as well as peak demand charges with configurable timebase for each commodity
  * It allows to deactivate specific equations, so the model becomes a linear programming model without integer variables
  * It supports multiple-input and multiple-output energy conversion technologies with load dependent efficiencies


## Installation


If you don't already have an existing Python I recommend using the Python distribution Anaconda. It contains all needed packages except Pyomo. 

1.	**[Anaconda (Python 2.7 or Python 3.5)](http://continuum.io/downloads)**. Choose the 64-bit installer if possible.
	1.	During the installation procedure, keep both checkboxes "modify PATH" and "register Python" selected!
2. **[Pyomo](http://www.pyomo.org/installation)**. (pip install pyomo)	
	
3. [download](https://github.com/yabata/ficus/archive/master.zip) or clone (with [git](http://git-scm.com/)) this repository to a directory of your choice.
4.	Copy the `ficus.py` file to a directory which is already in python's search path or add the your folder to python's search path (sys.path) ([how to](http://stackoverflow.com/questions/17806673/where-shall-i-put-my-self-written-python-packages/17811151#17811151))	
	
5.	Install a [solver](#solver) (optional).



## Get started


1. Run the given examples in the `examples` folder. You can run ficus from [a python script](https://ficus.readthedocs.io/en/latest/run_ficus.html#run-from-python) or [directly from the input file using excel](https://ficus.readthedocs.io/en/latest/run_ficus.html#run-from-excel).
2. Read the [documenation](http://ficus.readthedocs.org) and create your own input file following the tutorial

## Solver (optional)<a name="solver"></a>

Pyomo allows using the [NEOS Server for Optimisation](http://www.neos-server.org/neos/) for solving, so it is **not required to install a solver**.

I still recommend to install and use one of the following solvers.

  1. **GLPK** (open source)
       1. Download the latest version (e.g. GLPK-4.55) of [WinGLPK](http://sourceforge.net/projects/winglpk/files/winglpk/)
       2. Extract the contents to a folder, e.g. `C:\GLPK`
       3. Add the sub-folder `w64` to your system path, e.g. `C:\GLPK\w64` ([how](http://geekswithblogs.net/renso/archive/2009/10/21/how-to-set-the-windows-path-in-windows-7.aspx)).
  2. **CPLEX** (commercial)
  
       Download and install IBM's [CPLEX](http://www-01.ibm.com/software/commerce/optimization/cplex-optimizer/) solver. [Free for academics](https://www.ibm.com/developerworks/community/blogs/jfp/entry/cplex_studio_in_ibm_academic_initiative?lang=en)
  3. **Gurobi** (commercial)

       Download and install [Gurobi](http://www.gurobi.com/) solver. [Free for academics](http://www.gurobi.com/academia/for-universities)

## Screenshots

This is a typical result plot created by the function `ficus.plot_timeseries`, showing electricity
generation and consumption over 7 days:

<a href="doc/img/elec-timeseries.png"><img src="doc/img/elec-timeseries.png" alt="Timeseries plot of 7 days of electricity generation and consumption in 15 minute resolution" style="width:300px"></a>

More result plots are given in the [documenation](http://ficus.readthedocs.org).
  
  
## Copyright

Copyright (C) 2015  Dennis Atabay

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>
