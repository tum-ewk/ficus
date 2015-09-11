Overview
--------

ficus consists of several **model entities**. These are external imported/exported commodities, processes and storages. Demand and intermittent commodity supply are modelled through time series datasets.

The objective of the model is to supply the given demand with minimal costs. The main restriction is the power balance of every commodity for every time-step. Commodities are goods that can be imported/exported, generated, stored and consumed. They are represented by their power flow (in kW) per time-step.

The timebase of the model can be configured depending on the timebase of the given data (demand). For all commodities and entities then the same timebase is used.

External imported/exported commodities
^^^^^^^^^

External imported/exported commodities are goods that can be imported or exported from/to "external sources", e.g. the electric grid. The prices for buying/selling for every time-step are given by a time-series.

Additional a demand rate with an extra time interval can be given, to  consider `peak demand charges`_.  A ``Demand-Rate-Factor`` time-series allows to raise, reduce or turn off the demand rate for specific time-steps to consider special tariff systems.

External imported/exported commodities are defined over the commodity itself ``(commodity)``, for example
``(elec)``  or ``(heat)``.

Process
^^^^^^^
Processes describe conversion technologies from one commodity to another. They
can be visualised like a black box with multiple inputs (commodities) and multiple outputs
(commodities). Conversion efficiencies between inputs and outputs for full load (and optional part-load) are the main
technical parameter. Fixed costs for investment and maintenance (per capacity)
and variable costs for operation (per output) are the economic parameters.

Processes can be assigned to a ``Process Class``, which allows to consider additional fees/subsidies for inputs or outputs of this class (e.g. subsidies for pv generation).

Processes are defined over the tuple  ``(process , number, commodity, direction)`` that specifies the inputs and outputs for that process. The ``number`` variable is needed, if more than one identical process is given
For example, ``(chp, 1, gas, In)``, ``(chp, 1, electricity, Out)`` and ``(chp, 1, heat, Out)``
describes that the process named ``chp`` (combined heat and power) has a single input ``gas``
and two outputs ``electricity`` and ``heat``.


Storage
^^^^^^^
Storage describes the possibility to deposit a deliberate amount of energy in
form of one commodity at one time step, and later retrieving it. Efficiencies
for charging/discharging and self discharge depict losses during input/output. Storage is
characterised by capacities both for energy content (in kWh) and
charge/discharge power (in kW). Both capacities have independent sets of
investment, fixed and variable cost parameters to allow for a very flexible
parametrization of various storage technologies from batteries to hot water
tanks. 

Storage is defined over the tuple ``(storage, number, stored commodity)``. For
example, ``(Li-Ion Battery, 1, electricity)`` represents a Li-Ion Battery that can 
store and retrieve energy in form of electricity.


Timeseries
^^^^^^^^^^

Demand
""""""
Each commodity ``(demand commodity)`` may have one time-series,
describing the (average) power demand (kW) per time-step. They are a crucial
input parameter, as the whole optimisation aims to satisfy these demands with
minimal costs from the given technologies (process, storage, external import/export).

Intermittent Supply
"""""""""""""""""""
A time-series normalised to a maximum value of 1 relative to the installed
capacity of a process using this commodity as input. For example, a wind power
time-series should reach value 1, when the wind speed exceeds the modelled wind
turbine's design wind speed is exceeded. This implies that any non-linear
behaviour of intermittent processes can already be incorporated while preparing
this time-series.


.. _peak demand charges: https://en.wikipedia.org/wiki/Peak_demand
