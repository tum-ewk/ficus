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

    Time,elec, heat
    1, **0.15**, **0.05**
    2, **0.15**, **0.05**
    3, **0.15**, **0.05**
    4, **0.15**, **0.05**
    5, **0.15**, **0.05**
    6, **0.15**, **0.05**
    7, ...,...

Ext-Export
^^^^^^^^
Timeseries: Revenues for every commodity that can be exported for every timestep (in Euro/kWh). 

**Note**: Postive values mean, that you **RECEIVE MONEY** for exported energy.

*Edit Example*:
Set the revenues for electricty export to 0.01 Euro/kWh. Gas can not be exported because we limited the maximal power export to zero. So no timeseries is needed.

.. csv-table:: Sheet **Ext-Export**
   :header-rows: 1
   :stub-columns: 1

    Time, elec
    1, **0.01**
    2, **0.01**
    3, **0.01**
    4, **0.01**
    5, **0.01**
    6, **0.01**
    7, ...
    
    
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

    Time,elec,gas
    1,1,1
    2,1,1
    3,1,1
    4,1,1
    5,1,1
    6,1,1
    7,...,...


.. _Process_ref:
Process
^^^^^^^^

* **Process**: Name of the process
* **Num**: Number of identical processes
* **class**: assign process to a Process Class, which allows to consider addtitional fees/subsidies for inputs or outputs of this class and total power/energy limits for the whole class
* **cost-inv**: Specific investment costs for new capacities (in Euro/kW)
* **cost-fix**: Specific annual fix costs (in Euro/kW/a)
* **cost-var**: Specific variable costs per energy throughput (in Euro/kWh)
* **cap-installed**: Already installed capacity of process (no additional investment costs) (in kW)
* **cap-new-min**: Minimum capacity of process to be build, if process is built. It is allways possible that the process isn't built at all. (in kW) (**Note**: only considered if ``Min-Cap`` in ``MIP-Settings`` is ``True``)
* **cap-new-max**: Maximum new process capacity
* **partload-min**: Specific minimum partload of process (normalized to 1 = max). (**Note**: only considered if ``Partload`` in ``MIP-Settings`` is ``True``)
* **start-up-energy**: Specific additional energy consumed by the process for strat-up (in kWh/kW). For each input commodity this value is multiplied by the ``ratio`` in ``Process-Commodity`` (**Note**: only considered if ``Partload`` in ``MIP-Settings`` is ``True``)
* **initial-power**: Initial Power throughput of process for timestep t=0 (in kW)
* **depreciation**: Depreciation period. Economic lifetime (more conservative than technical lifetime) of a process investment in years (a). Used to calculate annuity factor for investment costs.
* **wacc**: Weighted average cost of capital. Percentage (%/100) of costs for capital after taxes. Used to calculate annuity factor for investment costs.

**Note**: All specific costs and capacities refer to the commoditis with input or output ratios of ``1``! For a process *Turbine* defined by the following table, all specific costs (e.g. Specific Investment Costs) corespond to the installed electric power. So if specific investment costs of 10 Euro/kW are given and a turbine with 10 kW electric output power is built, the investment costs are 100 Euro. The maximum input power of the commodity gas though is 300 kW!

.. csv-table:: Example for input/output ratios of a process
   :header-rows: 1
   :stub-columns: 3

    Process,Commodity,Direction,ratio
    Turbine,gas,In,3
    Turbine,elec,Out,1



*Edit Example*:
Delete all existing processes and add the new processes **chp**, **wind_1**, **wind_2** and **boiler**. Set the parameters as shown in the table.

.. csv-table:: Sheet **Process**
   :header-rows: 1
   :stub-columns: 3

    Process,Num,class,cost-inv,cost-fix,cost-var,cap-installed,cap-new-min,cap-new-max,partload-min,start-up-energy,initial-power,depreciation,wacc
    chp,1,CHP,700,0,0.01,0,0,inf,0,0.0,0,10,0.05
    wind_1,1,WIND,1000,0,0.005,0,0,inf,0,0.0,0,10,0.05
    wind_2,1,WIND,1000,0,0.005,0,0,inf,0,0.0,0,10,0.05
    boiler,1,,100,0,0.001,0,0,inf,0,0.0,0,10,0.05


Process-Commodity
^^^^^^^^
Define input and output commodities and the conversion efficiencies between them for eacht process. Each commodities can have multiple inputs and outputs.

* **Process**: Name of the Process. Make sure that you use exactly the same name, than in sheet ``Process``
* **Commodity**: Name of commodity that is used/produced by the process.
* **Direction**:  *In* if the commodity is used by the process, *Out* if the commodity is produced. 
* **ratio**: input/output ratios for the commodities of the process at full load.
* **partload-ratio**: input/output ratios for the commodities of the process at minimum partload (``partload-min``) given in sheet ``Process`` (**Note**: only considered if ``Partload`` in ``MIP-Settings`` is ``True`` and ``partload-min`` is between 0 and 1)


Let's assume we defined a :ref:`Process_ref` **chp** (combined heat and power) and set the minimum partload to 50% (``partload-min=0.5``):

.. csv-table:: Sheet **Process**
   :header-rows: 1
   :stub-columns: 3

    Process,Num,class,...,partload-min,...
    chp,1,CHP,...,0.5,...

Now we want to define, that the chp unit consumes ``gas`` and produces elecricity (``elec``) and ``heat``. We want to set the electric efficiency to **40%** at full load and to **30%** at minimmum partload. The efficinecy for 
generating heat should be **50%** at full load and **55%** at partload.

Because specific costs and power outputs for chp units are usually given refered to the electric power output, we set the ``ratio`` **ans** ``ratio-partload`` of ``(chp,elec,Out)`` to **1**.
(**Note**: All specific costs and capacities given in the ``Process`` sheet refer to the commoditis with input or output ratios of ``1``! See :ref:`Process_ref`)

Now we can calculate the ratios of the other commodities based on the efficiencies, so we get:

.. csv-table:: Sheet **Process-Commodity**
   :header-rows: 1
   :stub-columns: 3
   
    Process,Commodity,Direction,ratio,ratio-partload
    chp,gas,In,2.50,4.00
    chp,elec,Out,**1.00**,**1.00**
    chp,heat,Out,1.25,2.20

So with setting the ratios for full load and minimum partload we defined the partload performance curve of our process. Points between full load and minimum partload are approximated as a linear function between them. (**Note**: If ``Partload`` in ``MIP-Settings`` is set to ``False``, partload behaviour is not considered and the efficiencies defined by ``ratio`` are constant for all operating points. The values in ``ratio-partload`` are ignored).

The following figure shows the power inputs/outputs and eiffiencies of a 10 kW (elec!) chp unit with the parameters used in this example with and without considering partload behaviour.

.. image:: img/process_commodity_partload_example.*
   :width: 95%
   :align: center
 
 
*Edit Example*:
Delete all existing processes and add the new processes **chp**, **wind_1**, **wind_2** and **boiler**. Set the ratios as shown in the table. Because partload behaviour is not considered in this example, we can leave the ``ratio-partload`` column empty or set to any abritary value.

.. csv-table:: Sheet **Process-Commodity**
   :header-rows: 1
   :stub-columns: 3
   
    Process,Commodity,Direction,ratio,ratio-partload
    chp,gas,In,2.00,
    chp,elec,Out,1.00,	
    chp,heat,Out,1.00,	
    wind_1,wind1,In,1.00,	
    wind_1,elec,Out,1.00,	
    wind_2,wind2,In,1.00,	
    wind_2,elec,Out,1.00,	
    boiler,gas,In,1.10,
    boiler,heat,Out,1.00,	



Process Class
^^^^^^^^
Define a Process Class and add fees/subsidies for a produced/consumed commodity or capacity and energy limits for this class.

Processes can be assigned to a process class in the columns ``class`` in the ``Process`` sheet (See :ref:`Process_ref`). Make sure you use exactly the same names. 

*   **Class**: Name of the Process Class
*   **Commodity**: Commodity of the processes within the class
*   **Direction**: Direction of the commodity within the processes of this class (*In* or  *Out*)
*   **fee**: additional fee for produced/consumed energy in this class. (Postive values: Pay Money; Negative Values: Receive Money)
*   **cap-max**: Maximum value for the sum of all process capacities of this class (Independent from ``Commodity``)
*   **energy-max**: Maximum value for the sum of energy of the specified commodity that can be produced/consumed by the class within one year


*Edit Example*:
Delete all existing processes classes and add the new classes **CHP** and **WIND** with Commodity ``elec`` and Direction ``Out``. Set the ratios as shown in the table.
This sets a maximum of **20000 kW** for the total capacity of wind turbines, a subsidy of **0.05 Euro/kWh** for produced electricity of the wind turbines (weather sold to the grid or used to cover the demand) and a fee of **0.02 Euro/kWh** for produced electricity out of our chp unit.

.. csv-table:: Sheet **Process-Class**
   :header-rows: 1
   :stub-columns: 2
   
    Class,Commodity	Direction,fee,cap-max,energy-max
    CHP,elec,Out,0.02,inf,inf
    WIND,elec,Out,-0.05,20000,inf


Storage
^^^^^^^^

.. csv-table:: Sheet **Process-Class**
   :header-rows: 1
   :stub-columns: 3
   
    Storage,Commodity,Num,cost-inv-p,cost-inv-e,cost-fix-p,cost-fix-e,cost-var
    battery	elec,1,0,1000,0,0,0
    heat storage,heat,1,0,10,0,0,0

.. csv-table:: Sheet **Process-Class**
   :header-rows: 1
   :stub-columns: 3
   
    Storage,Commodity,Num,cap-installed-p,cap-new-min-p,cap-new-max-p,cap-installed-e,cap-new-min-e,cap-new-max-e,max-p-e-ratio
    battery,elec,1,0,0,inf,0,0,100000,2
    heat storage,heat,1,0,0,inf,0,0,20000,1


.. csv-table:: Sheet **Process-Class**
   :header-rows: 1
   :stub-columns: 3
   
Storage	Commodity	Num	eff-in	eff-out	self-discharge	cycles-max	DOD	initial-soc	depreciation	wacc
battery	elec	1,0.900	0.900	0.0001	10000	1	0	10	0.05
heat storage	heat,0.950	0.950	0.0001	1000000	1	0	10	0.05






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









