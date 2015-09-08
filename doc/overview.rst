Overview
--------

ficus consists of several **model entities**. These are exterrnal imported/exported commodities, processes and storages. Demand and intermittent commodity supply are modelled through time series datasets.

The objective of the model is to supply the given demand with minimal costs. The main restriction is the power balance of every commodity for every timestep. Commodities are goods that can be imported/exported, generated, stored and consumed. They are represented by their power flow (in kW) per timestep.

The timebase of the model can be configured depending on the timebase of the given data (demand). For all commodities and entities then the same timebase is used.

Exterrnal imported/exported commodities
^^^^^^^^^

Exterrnal imported/exported commodities are goods that can be imported or exported from/to "external sources", e.g. the elctric grid.
The prices for buying/selling for every timestep are given by a timeseries. Additional a demand rate with an extra time interval can be given, to  consider `peak demand charges`_. 

Exterrnal imported/exported commodities are defined over the commodity itself ``(commodity)``, for example
``(elec)``  or ``(heat)``.

Process
^^^^^^^
Processes describe conversion technologies from one commodity to another. They
can be visualised like a black box with multiple inputs (commodities) and multiple outputs
(commodities). Conversion efficiencies between inputs and outputs for full load (and optional partload) are the main
technical parameter. Fixed costs for investment and maintenance (per capacity)
and variable costs for operation (per output) are the economic parameters.

Processes are defined over the tuple  ``(process , number, commodity, direction)`` that specifies the inputs and outputs for that process. The ``number`` variable is needed, if more than one identical process is given
For example, ``(chp, 1, gas, In)``, ``(chp, 1, electricity, Out)`` and ``(chp, 1, heat, Out)``
describes that the process named ``chp`` (combined heat and power) has a single input ``gas``
and two outputs ``electricity`` and ``heat``.


Storage
^^^^^^^
Storage describes the possibility to deposit a deliberate amount of energy in
form of one commodity at one time step, and later retrieving it. Efficiencies
for charging/discharging depict losses during input/output. A self-discharge
term is **not** included at the moment, but could be added trivially (one
column, one modification of the storage state equation). Storage is
characterised by capcities both for energy content (in MWh) and
charge/discharge power (in MW). Both capacities have independent sets of
investment, fixed and variable cost parameters to allow for a very flexible
parametrization of various storage technologies from batteries to hot water
tanks.

Storage is defined over the tuple ``(site, storage, stored commodity)``. For
example, ``(Norway, pump storage, electricity)`` represents a pump storage
power plant in Norway that can store and retrieve energy in form of
electricity.


Timeseries
^^^^^^^^^^

Demand
""""""
Each combination ``(site, demand commidty)`` may have one timeseries,
describing the (average) power demand (MWh/h) per timestep. They are a crucial
input parameter, as the whole optimisation aims to satisfy these demands with
minimal costs from the given technologies (process, storage, transmission).

Intermittent Supply
"""""""""""""""""""
Each combination ``(site, supim commodity)`` must be supplied with one
timeseries, normalised to a maximum value of 1 relative to the installed
capacity of a process using this commodity as input. For eample, a wind power
timeseries should reach value 1, when the wind speed exceeds the modelled wind
turbine's design wind speed is exceeded. This implies that any non-linear
behaviour of intermittent processes can already be incorporated while preparing
this timeseries.


.. _peak demand charges: https://en.wikipedia.org/wiki/Peak_demand
