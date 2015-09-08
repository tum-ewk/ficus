.. currentmodule:: ficus

.. _tutorial:

Tutorial
========

The README file contains `installation notes`__. This tutorial
expands on the steps that follow this installation.

.. __: https://github.com/yabata/ficus/blob/master/README.md#installation

This tutorial describes how to create the data input and run your own model based on an example.

Run from Excel
--------------

For an easy first run of ficus without using any python enviroment a small macro in VBA allows running the 
optimization directly from Excel.

* Open the file `example_fromexcel.xlsm`_
* Go to the ``RUN`` sheet and choose a solver. If you chosse any other than the ``neos`` solver, the solver hast to be installed locally on your computer. Choosing ``neos`` uses the ``cbc`` solver from the `NEOS Server for Optimization`_ (no installation required)
* Push the ``RUN OPTIMIZATION`` button. 

A cmd window should appear showing the actual status and a few minutes later six result figures should show up. The subfolder ``result`` should contain the saved result figures as well as a resultfile. 

Using this way of running the model, the function :func:`run_from_excel` from the `ficus.py`_  script is within VBA. This requires, that `ficus.py`_ can be found by python. To make sure this is the case, before the first time of running the model, use the :func:`install` function, by just double clicking on `ficus.py`_  or run it with python. Then continue with ``y``.  

Run from Python
--------------

Running the model from python (e.g. Ipython or Spyder) gives you more options for running the optimisation and plotting the results. 



Run from Ipython
^^^^^^^^
* Open Ipython 
* Change the working directory to the folder where the `runficus.py`_ script is: 

::

    import os
    os.chdir("C:\YOUR\FOLDER")
* Run the script:

::

    run runficus
    
The shell should show the actual status and a few minutes later six result figures should show up. The subfolder ``result`` should contain the saved result figures as well as a resultfile. 

Run from Spyder
^^^^^^^^
* Open Spyder 
* Open the `runficus.py`_ script within Spyder
* Run the script with ``F5``

The shell should show the actual status and a few minutes later six result figures should show up. The subfolder ``result`` should contain the saved result figures as well as a resultfile. 

runficus.py
^^^^^^^^

Here the `runficus.py`_ script is explained step by step, so you can change it and use it for your own model.

::

    import os
    import ficus

Two packages are included.

* `os`_ is a builtin Python module, included here for its `os.path`_ submodule
  that offers operating system independent path manipulation routines. 
  
* `ficus`_ is the module whose functions are used mainly in this script. These
  are :func:`prepare_result_directory`, :func:`run_ficus`, :func:`report` and
  :func:`result_figures`.
  
To import ficus, `ficus.py`_ hast to be either in the same directory than `runficus.py`_ or in any directory, that is searched by python.  To copy `ficus.py`_` to the ``\Lib\site-packages`` folder of python, use the :func:`install` function, by just running `ficus.py`_ ones and continue with ``y``.

::

    input_file = 'example.xlsx'


Gives the path to the ``input_file`` used for model creation. If the file is not in the same folder than `ficus.py`_, give the FULL PATH (e.g. C:\YOUR\INPUT\FILE.xlsx)

::

    result_folder = 'result'
    result_name = os.path.splitext(os.path.split(input_file)[1])[0]
    result_dir = ficus.prepare_result_directory(result_folder,result_name)

Creates a time stamped folder ``result_name-TIME`` within the ``result_folder`` directory and saves the full path to ``result_dir``.
Give FULL PATH for ``result_folder``, if it should not be in the same directory, than `runficus.py`_`

::

    prob = ficus.run_ficus(input_file, opt = 'cbc', neos=True)

The :func:`run_ficus` function, is the "work horse", where most computation and time is spent. The
optimization problem is first defined and filled with values from the ``input_file``. Then the solver ``opt`` is called to solve the model.  If ``neos`` is set to ``True``, the problem is sent to the 'NEOS Server for Optimization'_ to solve the problem (Note, that using some solvers on NEOS require a license). If ``neos`` is set to false, the locally installed solver is used (if installed). After solving the problem the results are read back to  the ``prob`` object.

If locally installed solver `gurobi`_ or `cplex`_ are used, the parameter ``Threads`` allows to set the maximal number of simultaneous CPU threads.

::

    ficus.report(prob, result_dir)
    
Saves the reults from the object ``prob`` to an excel file in the directory ``result_dir``.

::

    ficus.result_figures(result_dir,prob=prob, show=True)
    
Reads and plots the results from the object ``prob`` and saves them in the directory ``result_dir``.
Can also be used to plot data from a given resultfile with the Paraneter ``resultfile=PATH\TO\RESULTFILE.xlsx`` instead of giving ``prob``.
``show`` turns on/off showing the plots.


Create Input File
--------------
The following tutorial is a step by step explanation of how to create your own input file.

For the sake of an example, assume you want to build a new factory named *NewFactory* and cover its energy demand cost optimal. You have the (predicted) demand timeseries in 15 minute time resolution for electricity (``elec``) and heat (``heat``) for 7 days (672 timesteps). 
You can import electricty and gas through the given infrastructure and export electricity back to the grid.
You consider following processes/storages for converting/storing energy:

* A combined heat and power plant (``chp``) to convert gas to electricity and heat, unlimited in size
* Two different wind turbines (``wind_1`` and ``wind_2``), limited to 2000 kW total
* A gas boiler (``boiler``) to convert gas to heat, unlimited in size
* A heat storages (``heat_storage``) to store heat, limited to XXX kWh
* A battery storage (``battery``) to store electricity, unlimited in size

First make a copy of `example.xlsx`_ or `example_fromexcel.xlsm`_ depending on how you want to run the model and give it the name ``NewFactory.xlsx`` or ``NewFactory.xlsm``. Now edit the new file step by step following the instructions.

Time-Settings
^^^^^^^^
Set timebase of time dependent Data and timesteps to be optimized

* **timebase**: time-interval between timesteps of all given timeseries data.
* **start**: First timestep to use for the optimisation
* **end**: Last timestep to use for the optimisation

*Edit Example*:
Keep the timebase at 900s (=15 minutes), the start timestep at 1 and the end timestep at 672 (optimise the whole 7 days)

.. csv-table:: Sheet **Time-Settings**;
   :header-rows: 1
   :stub-columns: 1

    Info,timebase,start,end
    Time,900,1,672


MIP-Settings
^^^^^^^^
Activate/deactivate specific equations.
If all settings are set to ``no``, the problem will be a linear optimisation problem without integer variables. This will result and less computation time for solving of the problem.
Activating one/more of the settings will activate equations, that allow additional restriction but may lead to longer claculation of the model because integer variable have to be used. The problem will then become a mixed integer linear optimisation problem.

* **Storage In-Out**: Prevents storages from charging and discharging one commodity at the same time, if activated. This can happen, when dumping energy of one commodity will lead to lower total costs. The model then uses the efficiency of the storage to dump the energy with no dumping costs.
* **Partload**: Consider minimum partload settings, partload efficiencies as well as start-up costs of processes.
* **Min-Cap**: Consider minimal installed capacities of processes and storages. This allows to set a minimum capacity of processes and storages, that has to be build, if the process is built at all (it still can not be built at all). Setting minimal and maximal cpapcities of processes/storages to the same level, this allows invetigating if buidling a specific process/storage with a specific size is cost efficient.

*Edit Example*:
Keep all settings deactivated.

.. csv-table:: Sheet **MIP-Settings**
   :header-rows: 1
   :stub-columns: 1

    Settings,Active
    Storage In-Out, no
    Partload, no
    Min-Cap, no

Ext-Commodities
^^^^^^^^
List of all commodities than can be imported/exported. Set demand charge, time interval for demand charge, import/export limits and minimum operating hours.

For every commodity that can be imported/exported:

* **demand rate**: demand rate (in Euro/kW/a) to calculate the 'peak demand charge'_ of one commodity. The highest imported power during a specific time period (``time-interval-demand-rate``) of highest use in the year is used to calculate the demand charges by multiplication with the demand rate
* **time-interval-demand-rate**: time period or time interval used to determine the highest imported power use in the year for calculating the peak demnd charge
* **p-max-initial**: Initial value of highest imported power use in the year. Sets the minimum for demand charges to ``demand-rate`` * ``p-max-initial``
* **import-max**: maximum power of commodity that can be imported per timestep
* **export-max**: maximum power of commodity that can be exported per timestep
* **operating-hours-min**: Minimum value for "operating hours" of import. Operating hours are calculated by dividing the total energy imported during one year by the highest imported power during a specific time period (``time-interval-demand-rate``) in the year. The highest possible value is the number of hours of one year (8760), which would lead to a constant import over the whole year (smooth load). This parameter can be used to model special demand charge tariffs, that require a minimum value for the operatimg hours for energy import. Set the value to zero to ignore this constraint.

*Edit Example*:
The commodities ``gas`` and ``elec`` that can be imported/exported are already defined. 
Change the Value for the demand rate of the commodity ``elec`` to 100. Keep the other inputs as they are.

.. csv-table:: Sheet **Ext-Commodities**
   :header-rows: 1
   :stub-columns: 1

    Commodity, demand-rate,time-interval-demand-rate,p-max-initial,import-max,export-max,operating-hours-min
    elec, **100**, 900, 0, inf, inf, 0
    heat, 0, 900, 0, inf, 0,0

Ext-Import
^^^^^^^^
Timeseries: Costs for every commodity that can be imported for every timestep (in Euro/kWh). 

**Note**: Postive values mean, that you have to **PAY** for imported energy 

*Edit Example*:
Set the costs for electricty import to 0.15 Euro/kWh and for gas import to 0.05 Euro/kWh for very timestep

.. csv-table:: Sheet **Ext-Import**
   :header-rows: 1
   :stub-columns: 1

    elec, heat
    **0.15**, **0.05**
    **0.15**, **0.05**
    **0.15**, **0.05**
    **0.15**, **0.05**
    **0.15**, **0.05**
    **0.15**, **0.05**
    ...,...

Ext-Export
^^^^^^^^
Timeseries: Revenues for every commodity that can be exported for every timestep (in Euro/kWh). 

**Note**: Postive values mean, that you **RECEIVE MONEY** for exported energy.

*Edit Example*:
Set the revenues for electricty export to 0.01 Euro/kWh. Gas can not be exported because we limited the maximal power export to zero. So no timeseries is needed.

.. csv-table:: Sheet **Ext-Export**
   :header-rows: 1
   :stub-columns: 1

    elec
    **0.01**
    **0.01**
    **0.01**
    **0.01**
    **0.01**
    **0.01**
    ...
    
    
Demand-Rate-Factor
^^^^^^^^

Timeseries: Factor to be multiplied with the demand rate to calculate demand charges for every timestep.

This allows to raise, reduce or turn off the demand rate for specific timesteps to consider special tariff systems.
Set all values to ``1``, for a constant demand rate

*Edit Example*:
Keep all values at ``1`` for constant demand rates.

.. csv-table:: Sheet **Demand-Rate-Factor**
   :header-rows: 1
   :stub-columns: 1

    elec
    1
    1
    1
    1
    1
    1
    ...

Process
^^^^^^^^

Process-Commodity
^^^^^^^^

Process Class
^^^^^^^^

Storage
^^^^^^^^

Demand
^^^^^^^^

SupIm
^^^^^^^^




.. _NEOS Server for Optimization:
    http://www.neos-server.org/neos/
.. _gurobi: https://en.wikipedia.org/wiki/Gurobi
.. _cplex.py: https://en.wikipedia.org/wiki/CPLEX
.. _ficus: https://github.com/yabata/ficus
.. _ficus.py: https://github.com/yabata/ficus/blob/master/ficus.py
.. _runficus.py.py: https://github.com/yabata/ficus/blob/master/runficus.py
.. _example_fromexcel.xlsm https://github.com/yabata/ficus/blob/master/example_fromexcel.xlsm
.. _example.xlsx https://github.com/yabata/ficus/blob/master/example.xlsx











URBS
--------------



::

    import coopr.environ
    import os
    import urbs
    from coopr.opt.base import SolverFactory
    from datetime import datetime
    
Several packages are included.

* `coopr.environ` is not used, but required for compatibility with future 
  releases of `coopr`_.

* `os`_ is a builtin Python module, included here for its `os.path`_ submodule
  that offers operating system independent path manipulation routines. The 
  following code creates the path string ``'result/foo'`` or ``'result\\foo'``
  (depending on the operating system),checks whether it exists and creates the
  folder(s) if needed. This is used to prepare a new directory for generated
  result file::
      
      result_dir = os.path.join('result', 'foo')
      if not os.path.exists(result_dir):
          os.makedirs(result_dir)
  
* `urbs`_ is the module whose functions are used mainly in this script. These
  are :func:`read_excel`, :func:`create_model`, :func:`report` and
  :func:`plot`. More functions can be found in the document :ref:`API`.

* `coopr.opt.base`_ is a utility package by `coopr`_ and provides the function
  ``SolverFactory`` that allows creating a ``solver`` object. This objects 
  hides the differences in input/output formats among solvers from the user.
  More on that in section `Solving`_ below.
  
* `datetime` is used to append the current date and time to the result
  directory name (used in :func:`prepare_result_directory`)

Settings
^^^^^^^^

From here on, the script is best read from the back.::

    if __name__ == '__main__':
        input_file = 'mimo-example.xlsx'
        result_name = os.path.splitext(input_file)[0]  # cut away file extension
        result_dir = prepare_result_directory(result_name)  # name + time stamp
    
        (offset, length) = (4000, 5*24)  # time step selection
        timesteps = range(offset, offset+length+1)

Variable ``input_file`` defines the input spreadsheet, from which the
optimization problem will draw all its set/parameter data.
   
Variable ``timesteps`` is the list of timesteps to be simulated. Its members
must be a subset of the labels used in ``input_file``'s sheets "Demand" and
"SupIm". It is one of the two function arguments to :func:`create_model` and
accessible directly, because one can quickly reduce the problem size by
reducing the simulation ``length``, i.e. the number of timesteps to be
optimised. 

:func:`range` is used to create a list of consecutive integers. The argument
``+1`` is needed, because ``range(a,b)`` only includes integers from ``a`` to
``b-1``:: 
    
    >>> range(1,11)
    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

The following section deals with the definition of different scenarios.
Starting from the same base scenarios, defined by the data in ``input_file``,
they serve as a short way of defining the difference in input data. If needed,
completely separate input data files could be loaded as well.

In addition to defining scenarios, the ``scenarios`` list allows to select a
subset to be actually run.

Scenario functions
^^^^^^^^^^^^^^^^^^

A scenario is simply a function that takes the input ``data`` and modifies it
in a certain way. with the required argument ``data``, the input
data :class:`dict`.::
    
    # SCENARIOS
    def scenario_base(data):
        # do nothing
        return data
    
The simplest scenario does not change anything in the original input file. It
usually is called "base" scenario for that reason. All other scenarios are
defined by 1 or 2 distinct changes in parameter values, relative to this common
foundation.::
    
    def scenario_stock_prices(data):
        # change stock commodity prices
        co = data['commodity']
        stock_commodities_only = (co.index.get_level_values('Type') == 'Stock')
        co.loc[stock_commodities_only, 'price'] *= 1.5
        return data
    
For example, :func:`scenario_stock_prices` selects all stock commodities from
the :class:`DataFrame` ``commodity``, and increases their *price* value by 50%.
See also pandas documentation :ref:`Selection by label <pandas:indexing.label>`
for more information about the ``.loc`` function to access fields. Also note
the use of `Augmented assignment statements`_ (``*=``) to modify data 
in-place.::
    
    def scenario_co2_limit(data):
        # change global CO2 limit
        hacks = data['hacks']
        hacks.loc['Global CO2 limit', 'Value'] *= 0.05
        return data

Scenario :func:`scenario_co2_limit` shows the simple case of changing a single
input data value. In this case, a 95% CO2 reduction compared to the base
scenario must be accomplished. This drastically limits the amount of coal and
gas that may be used by all three sites.::
    
    def scenario_north_process_caps(data):
        # change maximum installable capacity
        pro = data['process']
        pro.loc[('North', 'Hydro plant'), 'cap-up'] *= 0.5
        pro.loc[('North', 'Biomass plant'), 'cap-up'] *= 0.25
        return data
    
Scenario :func:`scenario_north_process_caps` demonstrates accessing single
values in the ``process`` :class:`~pandas.DataFrame`. By reducing the amount of
renewable energy conversion processes (hydropower and biomass), this scenario
explores the "second best" option for this region to supply its demand.::
    
    def scenario_all_together(data):
        # combine all other scenarios
        data = scenario_stock_prices(data)
        data = scenario_co2_limit(data)
        data = scenario_north_process_caps(data)
        return data 

Scenario :func:`scenario_all_together` finally shows that scenarios can also be
combined by chaining other scenario functions, making them dependent. This way,
complex scenario trees can written with any single input change coded at a
single place and then building complex composite scenarios from those.

Scenario selection
^^^^^^^^^^^^^^^^^^
   
::
    
    # select scenarios to be run
    scenarios = [
        scenario_base,
        scenario_stock_prices,
        scenario_co2_limit,
        scenario_north_process_caps,
        scenario_all_together]
    scenarios = scenarios[:1]  # select by slicing 

In Python, functions are objects, so they can be put into data structures just
like any variable could be. In the following, the list ``scenarios`` is used to
control which scenarios are being actually computed. 
   
Run scenarios
-------------

::

    for scenario in scenarios:
        prob = run_scenario(input_file, timesteps, scenario, result_dir)

Having prepared settings, input data and scenarios, the actual computations
happen in the function :func:`run_scenario` of the script. It is executed 
``for`` each of the scenarios included in the scenario list. The following
sections describe the content of function :func:`run_scenario`. In a nutshell,
it reads the input data from its argument ``input_file``, modifies it with the
supplied ``scenario``, runs the optimisation for the given ``timesteps`` and
writes report and plots to ``result_dir``.

Reading input
^^^^^^^^^^^^^

::

    # scenario name, read and modify data for scenario
    sce = scenario.__name__
    data = urbs.read_excel(input_file)
    data = scenario(data)

Function :func:`read_excel` returns a dict ``data`` of six pandas DataFrames
with hard-coded column names that correspond to the parameters of the
optimization problem (like ``eff`` for efficiency or ``inv-cost-c`` for
capacity investment costs). The row labels on the other hand may be freely
chosen (like site names, process identifiers or commodity names). By
convention, it must contain the six keys ``commodity``, ``process``,
``storage``, ``transmission``, ``demand``, and ``supim``. Each value must be a
:class:`pandas.DataFrame`, whose index (row labels) and columns (column labels)
conforms to the specification given by the example dataset in the spreadsheet
:file:`mimo-example.xlsx`.

``data`` is then modified by applying the :func:`scenario` function to it.


Solving
^^^^^^^

::

    # create model, solve it, read results
    model = urbs.create_model(data, timesteps)
    prob = model.create()
    optim = SolverFactory('glpk')  # cplex, glpk, gurobi, ...
    result = optim.solve(prob, tee=True)
    prob.load(result)

This section is the "work horse", where most computation and time is spent. The
optimization problem is first defined (:func:`create_model`), then filled with
values (``create``). The ``SolverFactory`` object is an abstract representation
of the solver used. The returned object ``optim`` has a method
:meth:`set_options` to set solver options (not used in this tutorial).

The remaining two lines call the solver and read the ``result`` object back
into the ``prob`` object, which is queried to for variable values in the
remaining script file. Argument ``tee=True`` enables the realtime console
output for the solver. If you want less verbose output, simply set it to
``False`` or remove it.
   
Reporting
^^^^^^^^^

::
    
    # write report to spreadsheet
    urbs.report(
        prob,
        os.path.join(result_dir, '{}-{}.xlsx').format(sce, now),
        ['Elec'], ['South', 'Mid', 'North'])
   
The :func:`urbs.report` function creates a spreadsheet from the main results.
Summaries of costs, emissions, capacities (process, transmissions, storage) are
saved to one sheet each. For timeseries, each combination of the given
``sites`` and ``commodities`` are summarised both in sum (in sheet "Energy
sums") and as individual timeseries (in sheet "... timeseries"). See also
:ref:`report-function` for a detailed explanation of this function's implementation.
   
Plotting
^^^^^^^^

::
    
    # add or change plot colors
    my_colors = {
        'South': (230, 200, 200),
        'Mid': (200, 230, 200),
        'North': (200, 200, 230)}
    for country, color in my_colors.iteritems():
        urbs.COLORS[country] = color
   
First, the use of the module constant :data:`COLORS` for customising plot
colors is demonstrated. All plot colors are user-defineable by adding color 
:func:`tuple` ``(r, g, b)`` or modifying existing tuples for commodities and 
plot decoration elements. Here, new colors for displaying import/export are
added. Without these, pseudo-random colors are generated in 
:func:`to_color`.::

    # create timeseries plot for each demand (site, commodity) timeseries
    for sit, com in prob.demand.columns:
        # create figure
        fig = urbs.plot(prob, com, sit)
        
        # change the figure title
        ax0 = fig.get_axes()[0]
        nice_sce_name = sce.replace('_', ' ').title()
        new_figure_title = ax0.get_title().replace(
            'Energy balance of ', '{}: '.format(nice_sce_name))
        ax0.set_title(new_figure_title)
        
        # save plot to files 
        for ext in ['png', 'pdf']:
            fig_filename = os.path.join(
                result_dir, '{}-{}-{}-{}.{}').format(sce, com, sit, now, ext)
            fig.savefig(fig_filename, bbox_inches='tight')
   
Finally, for each demand commodity (only ``Elec`` in this case), a plot over
the whole optimisation period is created. If ``timesteps`` were longer, a
shorter plotting period could be defined and given as an optional argument to
:func:`plot`.

The paragraph "change figure title" shows exemplarily how to use matplotlib
manually to modify some aspects of a plot without having to recreate the
plotting function from scratch. For more ideas for adaptations, look into
:func:`plot`'s code or the `matplotlib documentation`_.

The last paragraph uses the :meth:`~matplotlib.figure.Figure.savefig` method
to save the figure as a pixel ``png`` (raster) and ``pdf`` (vector) image. The
``bbox_inches='tight'`` argument eliminates whitespace around the plot.

.. note:: :meth:`~matplotlib.figure.Figure.savefig` has some more interesting
   arguments. For example ``dpi=600`` can be used to create higher resolution
   raster output for use with printing, in case the preferable vector images
   cannot be used. The filename extension or the optional ``format`` argument
   can be used to set the output format. Available formats depend on the used
   `plotting backend`_. Most backends support png, pdf, ps, eps and svg.
   
.. _augmented assignment statements:
    http://docs.python.org/2/reference/\
    simple_stmts.html#augmented-assignment-statements
.. _coopr: https://software.sandia.gov/trac/coopr
.. _coopr.opt.base: 
    https://projects.coin-or.org/Coopr/browser/coopr.opt/trunk/coopr/opt/base
.. _matplotlib documentation:
    http://matplotlib.org/contents.html
.. _os: https://docs.python.org/2/library/os.html
.. _os.path: https://docs.python.org/2/library/os.path.html
.. _pandas: https://pandas.pydata.org
.. _plotting backend: 
    http://matplotlib.org/faq/usage_faq.html#what-is-a-backend
.. _pyomo: https://software.sandia.gov/trac/coopr/wiki/Pyomo
.. _urbs: https://github.com/tum-ens/urbs
.. _urbs.py: https://github.com/tum-ens/urbs/blob/master/urbs.py
