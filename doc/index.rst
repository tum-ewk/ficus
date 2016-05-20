.. ficus documentation master file, created by
   sphinx-quickstart on Mon Sep 07 16:49:19 2015.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

.. module:: ficus

ficus: A (mixed integer) linear optimisation model for local energy systems
================================================================

:Maintainer: Dennis Atabay, <dennis.atabay@tum.de>
:Organization: `Institute for Energy Economy and Application Technology`_,
               Technische Universität München
:Version: |version|
:Date: |today|
:Copyright:
  This documentation is licensed under a `Creative Commons Attribution 4.0 
  International`__ license.

.. __: http://creativecommons.org/licenses/by/4.0/


Contents
--------

This documentation contains the following pages:

.. toctree::
   :maxdepth: 1

   overview
   run_ficus
   tutorial
   examples
   

Features
--------
* ficus is a (mixed integer) linear programming model for multi-commodity energy systems.
* It finds the minimum cost energy system to satisfy given demand time-series for possibly multiple commodities (e.g. electricity, heat)
* It considers given cost time-series for external obtained commodities as well as peak demand charges with configurable timebase for each commodity
* It allows to deactivate specific equations, so the model becomes a linear programming model without integer variables
* It supports multiple-input and multiple-output energy conversion technologies with load dependent efficiencies
* ficus includes reporting and plotting functions

.. _install-ref:

Installation
------------
If you don't already have an existing Python I recommend using the Python distribution Anaconda. It contains all needed packages except Pyomo. 

1.	`Anaconda`_ (Python 2.7 or Python 3.5). Choose the 64-bit installer if possible.
	* During the installation procedure, keep both checkboxes "modify PATH" and "register Python" selected!
2. `Pyomo` (pip install pyomo)	
3. `download`_ or clone (with `git`_) this repository to a directory of your choice.
4. Copy the ``ficus.py`` file in the ``python`` folder to a directory which is already in python's search path or add the ``python`` folder to python's search path (sys.path) (`how to`__)
5.	Install a :ref:`solver-ref <solver>` (optional).

Get started
------------
1. Run the given examples in the `examples` folder. You can run ficus from `a python script`_
4. Follow the :ref:`turorial <tutorial>` to create your own input file.


:ref:`solver-ref <solver>`


.. _solver-ref:

Solver
-----------

Pyomo allows using the `NEOS Server for Optimisation'_ for solving, so it is **not required to install a solver**.

I still recommend to install and use one of the following solvers.

  1. **GLPK** (open source)
       1. Download the latest version (e.g. GLPK-4.55) of `WinGLPK`_
       2. Extract the contents to a folder, e.g. `C:\GLPK`
       3. Add the sub-folder `w64` to your system path, e.g. `C:\GLPK\w64` (`how`_).
  2. **CPLEX** (commercial)
  
       Download and install IBM's `CPLEX <http://www-01.ibm.com/software/commerce/optimization/cplex-optimizer/>`_ solver. (`Free for academics <https://www.ibm.com/developerworks/community/blogs/jfp/entry/cplex_studio_in_ibm_academic_initiative?lang=en>`_)
  3. **Gurobi** (commercial)

       Download and install `Gurobi <http://www.gurobi.com/>`_ solver. (`Free for academics <http://www.gurobi.com/academia/for-universities>`_)


Screenshots
-----------

This is a typical result plot created by :func:`ficus.plot_timeseries`, showing electricity
generation and consumption over 7 days:

.. image:: img/elec-timeseries.*
   :width: 95%
   :align: center
   

   
.. _Institute for Energy Economy and Application Technology: http://www.ewk.ei.tum.de/
.. _matplotlib: http://matplotlib.org
.. _pandas: https://pandas.pydata.org
.. _pyomo: https://software.sandia.gov/trac/coopr/wiki/Pyomo
.. _ficus: https://github.com/yabata/ficus
.. _download: https://github.com/yabata/ficus/archive/master.zip
.. _git: http://git-scm.com/
.. _Anaconda: http://continuum.io/downloads
.. _Pyomo: http://www.pyomo.org/installation
.. _NEOS Server for Optimization:
    http://www.neos-server.org/neos/
.. _WinGLPK: http://sourceforge.net/projects/winglpk/files/winglpk/
.. _how:  http://geekswithblogs.net/renso/archive/2009/10/21/how-to-set-the-windows-path-in-windows-7.aspx))
.. __: http://stackoverflow.com/questions/17806673/where-shall-i-put-my-self-written-python-packages/17811151#17811151) 
.. _how to: http://www.mathworks.com/help/matlab/matlab_env/add-remove-or-reorder-folders-on-the-search-path.html
