.. currentmodule:: ficus

.. _examples:

Examples
========

In the ``examples`` folder several examples of input files are given. This section gives a short description of the examples.


example.xls and example_from_excel.xlsm
----------------------------------------

The input file ``example.xls`` and ``example_from_excel.xlsm`` are used within the :ref:`create-input-ref <tutorial>` explaining how to create an own input file by editing a given one.

The factory described in this example has given demand time-series for electricity (*elec*) and *heat*, that have to be covered. While *elec* can be imported and exported, *heat* has to be produced inside the factory. Therefore an electric heater, a gas boiler and/or chp unit can be used. Since the chp and the gas boiler require *gas* as an input, *gas* can be imported as well. To model a *pv* system, the intermittend supply time-series *solar* is given. Additionally a battery storage for *elec* and a heat storage for *heat* are defined.

The processed chp, booiler and el. heater have given installed capaities that can not be expanded any more. Only the process pv and the battery and heat storage can be built. The result of this model will be an optimal cpacity expansion of this three technologies and an optimal operation of all defined and built processes and storages.

.. csv-table:: Commodities defined in example.xls
   :header-rows: 1
   :stub-columns: 1

    Commodity,defined as,description
    elec,import; export; demand, electricity
    heat,demand, heat
	gas,import, gas
	solar,intermittend supply, time-series representing normalized output of a pv system


.. csv-table:: Processes defined in example.xls
   :header-rows: 1
   :stub-columns: 1

    Process,inputs,outputs,intalled capacity, max new capacity
    chp,gas, elec; heat, 5000 kW, 0 kW
    boiler ,gas, heat, 15000 kW, 0 kW
	pv,solar, elec, 0 kW, 50000 kW
	el. heater,elec, heat, 500 kW, 0 kW
	
.. csv-table:: Storages defined in example.xls
   :header-rows: 1
   :stub-columns: 1

    Storage,commodity ,intalled capacity, max new capacity
    battery, elec, 0 kW; 0 kWh, 1000000 kW; 1000000 kWh
    heat storage, heat, 0 kW; 0 kWh, 20000 kW; 20000 kWh


cover_heat+elec_xxx.xls
----------------------------------------

The input files ``cover_heat+elec_automotive.xls``, ``cover_heat+elec_carbon.xls``, ``cover_heat+elec_iron.xls`` and ``cover_heat+elec_steel.xls`` all have the same structure of defined commodities, processes and storages. But each factory has different demand time-series for electricity and heat. Since the time-series are given in a 15-minute resolution for one year, solving these problems might take a few hours (depending on the use solver).

The factories described in this example have given demand time-series for electricity (*elec*) and *heat*, that have to be covered. While *elec* can be imported and exported, *heat* has to be produced inside the factory. Therefore an immersion heater (im heater), a gas boiler and/or chp unit can be used. Since the chp and the gas boiler require *gas* as an input, *gas* can be imported as well. To model capacity specific investment costs, several chp units with different investment costs and different minimum new capacities are defined. Additionally three battery storages, *RedoxFlow*, Li-Ionen-1C* and *Li-Ionen-2C* for the commodity *elec* and a heat storage *TES* for *heat* are defined.

In these examples no processes and storages have installed capacities. The result of this model will be an optimal cpacity expansion and operation of all defined and built processes and storages. For importimg electricity here time-sensitive prices are used.

.. csv-table:: Commodities defined in cover_heat+elec_xxx.xls
   :header-rows: 1
   :stub-columns: 1

    Commodity,defined as,description
    elec,import; demand, electricity
    heat,demand, heat
	gas,import, gas
	solar,intermittend supply, time-series representing normalized output of a pv system


.. csv-table:: Processes defined in cover_heat+elec_xxx.xls
   :header-rows: 1
   :stub-columns: 1

    Process,inputs,outputs,intalled capacity, max new capacity
    chp 10-1000,gas, elec; heat, 0 kW, 50000 kW
    boiler ,gas, heat, 0 kW, 50000 kW
	el. heater,elec, heat, 0 kW, 50000 kW
	
.. csv-table:: Storages defined in cover_heat+elec_xxx.xls
   :header-rows: 1
   :stub-columns: 1

    Storage,commodity ,intalled capacity, max new capacity
    battery, elec, 0 kW; 0 kWh, 500000 kW; 5000000 kWh
    heat storage, heat, 0 kW; 0 kWh, 500000 kW; 5000000 kWh


	
steel_mill_example.xls
----------------------------------------

The factory described in this example describes an examplary steel mill. The steel mill has given demand time-series for electricity (*elec*), *heat* and *steel*, that have to be covered. While *elec* can be imported and exported, *heat* and *steel* have to be produced inside the factory. 

For producing *heat* an immersion heater (im heater), a gas boiler and/or chp unit can be used. Since the chp and the gas boiler require *gas* as an input, *gas* can be imported as well. Both processes also are defined to produce *CO2* as an output commodity. Since the produced *CO2* has to be "used" somewhere, it is defined as an export commodity. By defining negative costs for exporting *CO2*, cost for *CO2* production is applyed here.

A battery storage for *elec* and a heat storage for *heat* are defined.

For producing steel, a electric arc furnace is defined. It consumes *iron*, which can be imported and *elec* to produce steel. Since there is a demand for *steel* only at the end of each working day, the steel could either produced at exactly at this time, or it can be produced during the whole day and stored in the defined stock. This leads to a smaller capacity of the furnace.

Additionally a battery storage for *elec* and a heat storage for *heat* are defined.

In these examples no processes and storages have installed capacities. The result of this model will be an optimal cpacity expansion and operation of all defined and built processes and storages. For importimg electricity here time-sensitive prices are used.

.. csv-table:: Commodities defined in steel_mill_example.xls
   :header-rows: 1
   :stub-columns: 1

    Commodity,defined as,description
    elec,import; export; demand, electricity
    heat,demand, heat
	gas,import, gas
	solar,intermittend supply, time-series representing normalized output of a pv system
	iron,import, iron ore used for steel production
	steel, demand, steel that has to be produced
	CO2, export, CO2 produced by the processes


.. csv-table:: Processes defined in steel_mill_example.xls
   :header-rows: 1
   :stub-columns: 1

    Process,inputs,outputs,intalled capacity, max new capacity
    chp,gas, elec; heat, 0 kW, 50000 kW
    boiler ,gas, heat, 0 kW, 50000 kW
	pv,solar, elec, 0 kW, 200 kW
	im heater,elec, heat, 0 kW, 50000 kW
	furnace,elec;iron,steel, 0 kW, 50000 kW
	
.. csv-table:: Storages defined in steel_mill_example.xls
   :header-rows: 1
   :stub-columns: 1

    Storage,commodity ,intalled capacity, max new capacity
	battery, elec, 0 kW; 0 kWh, 500000 kW; 5000000 kWh
    heat storage, heat, 0 kW; 0 kWh, 500000 kW; 5000000 kWh
	stock, steel, 0 kW; 0 kWh, 500000 kW; 5000000 kWh
	
	
	