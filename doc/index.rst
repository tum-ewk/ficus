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
   tutorial
   workflow
   
More technical documents deal with the internal workings:   
   
.. toctree::
   :maxdepth: 1
   
   report
   api


Features
--------
* ficus is a (mixed integer) linear programming model for multi-commodity energy systems.
* It finds the minimum cost energy system to satisfy given demand timeseries for possibly multiple commodities (e.g. electricity, heat)
* It considers given cost timeseries for external obtained commodities as well as peak demand charges with configurable timebase for each commodity
* It allows to deactivate specific equations, so the model becomes a linear programming model without integer variables
* It supports multiple-input and multiple-output energy conversion technologies with load dependent efficiencies
* Thanks to `pandas`_, complex data analysis code is short and extensible.
* The model itself is quite small thanks to relying on the `Pyomo`_ packages.
* ficus includes reporting and plotting functions


Screenshots
-----------

This is a typical result plot created by :func:`ficus.plot_timeseries`, showing electricity
generation, consumption and storage levels over 7 days:

.. image:: img/elec-timeseries.*
   :width: 95%
   :align: center
   
Dependencies
------------

* `pyomo`_ interface to optimisation solvers (CPLEX, GLPK, Gurobi, ...).
* `matplotlib`_ for plotting
* `pandas`_ for input and result data handling, report generation 
* `pyomo`_ for the model equations

   
.. _pyomo: https://pyomo.org
.. _Institute for Energy Economy and Application Technology: http://www.ewk.ei.tum.de/
.. _matplotlib: http://matplotlib.org
.. _pandas: https://pandas.pydata.org
.. _pyomo: https://software.sandia.gov/trac/coopr/wiki/Pyomo
.. _ficus: https://github.com/yabata/ficus

