.. currentmodule:: ficus

.. _run_ficus:

Run ficus
========


.. _run-python-ref:

Run from Python
--------------

Running the model from python gives you more options for running the optimisation and plotting the results. Simply run the ``runficus.py`` script in the ``examples`` folder using e.g. python, ipython or spyder. After running the script, the shell should show the actual status and a few minutes later six result figures should show up. The sub-folder ``result`` should contain the saved result figures as well as a result-file.
 

runficus.py
^^^^^^^^

Here the ``runficus.py`` script is explained step by step, so you can change it and use it for your own model.

::

    import os
    import ficus

Two packages are included.

* `os`_ is a builtin Python module, included here for its `os.path`_ submodule
  that offers operating system independent path manipulation routines. 
  
* `ficus`_ is the module whose functions are used mainly in this script. These
  are :func:`prepare_result_directory`, :func:`run_ficus`, :func:`report` and
  :func:`result_figures`.
  
To import ficus, ``ficus.py`` hast to be either in the same directory than ``runficus.py`` or in any directory, that is searched by python.  To make sure this is the case, follow step 4 of the :ref:`install-ref <installation>`.

::

    input_file = 'example.xlsx'


Gives the path to the ``input_file`` used for model creation. If the file is not in the same folder than ``ficus.py``, give the FULL PATH (e.g. C:\\YOUR\\INPUT\\FILE.xlsx). To run one of the other examples, just change the name of the input file.

::

    result_folder = 'result'
    result_name = os.path.splitext(os.path.split(input_file)[1])[0]
    result_dir = ficus.prepare_result_directory(result_folder,result_name)

Creates a time stamped folder ``result_name-TIME`` within the ``result_folder`` directory and saves the full path to ``result_dir``.
Give FULL PATH for ``result_folder``, if it should not be in the same directory, than ``runficus.py``

::

    prob = ficus.run_ficus(input_file, opt = 'cbc', neos=True)

The :func:`run_ficus` function, is the "work horse", where most computation and time is spent. The
optimization problem is first defined and filled with values from the ``input_file``. Then the solver ``opt`` is called to solve the model.  If ``neos`` is set to ``True``, the problem is sent to the 'NEOS Server for Optimization'_ to solve the problem (Note, that using some solvers on NEOS require a license). If ``neos`` is set to false, the locally installed solver is used (if installed). After solving the problem the results are read back to  the ``prob`` object.

If locally installed solver `gurobi`_ or `cplex`_ are used, the parameter ``Threads`` allows to set the maximal number of simultaneous CPU threads.

::

    ficus.report(prob, result_dir)
    
Saves the results from the object ``prob`` to an excel file in the directory ``result_dir``.

::

    ficus.result_figures(result_dir,prob=prob, show=True)
    
Reads and plots the results from the object ``prob`` and saves them in the directory ``result_dir``.
Can also be used to plot data from a given result-file with the Parameter ``resultfile=PATH\\TO\\RESULTFILE.xlsx`` instead of giving ``prob``.
``show`` turns on/off showing the plots.

Run from Excel
--------------

For an easy first run of ficus without using any python environment a small macro in VBA allows running the 
optimization directly from Excel. Still python an all needed packages have to be installed on the computer.

* Open the file ``example_fromexcel.xlsm`` in the ``examples`` folder
* Go to the ``RUN`` sheet and choose a solver. If you choose any other than a ``neos-...`` solver, the solver hast to be installed locally on your computer. With me only the ``mosek`` and the ``cbc`` solver from `NEOS Server for Optimization`_ are working (no installation of solvers required)
* Push the ``RUN OPTIMIZATION`` button. 

A cmd window should appear showing the actual status and a few minutes later six result figures should show up. The sub-folder ``result`` should contain the saved result figures as well as a result-file.

Using this way of running the model, the function :func:`run_from_excel` from the ``ficus.py``  script is called within VBA. This requires, that ``ficus.py`` can be found by python. To make sure this is the case, follow step 4 of the :ref:`install-ref <installation>`.


  
.. _NEOS Server for Optimization:
    http://www.neos-server.org/neos/
.. _gurobi: https://en.wikipedia.org/wiki/Gurobi
.. _cplex: https://en.wikipedia.org/wiki/CPLEX
.. _ficus: https://github.com/yabata/ficus
.. _ficus.py: https://github.com/yabata/ficus/blob/master/ficus.py
.. _runficus.py.py: https://github.com/yabata/ficus/blob/master/runficus.py
.. _example_fromexcel.xlsm: https://github.com/yabata/ficus/blob/master/example_fromexcel.xlsm
.. _example.xlsx: https://github.com/yabata/ficus/blob/master/example.xlsx
.. _intermittent_supply_wind.xlsx: https://github.com/yabata/ficus/blob/master/doc/NewFactory/intermittent_supply_wind.xlsx
.. _os: https://docs.python.org/2/library/os.html
.. _os.path: https://docs.python.org/2/library/os.path.html
.. _screenshots: https://github.com/yabata/ficus/blob/master/README.md#screenshots
