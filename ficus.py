"""ficus: A (mixed integer) linear optimisation model for local energy systems

ficus minimises total cost for providing energy in form of desired commodities
to satisfy a given demand in form of timeseries. The
model contains commodities (e.g. electricity, heat, gas...),
processes that convert one commodity to another
and storage for saving/retrieving commodities.

https://github.com/yabata/ficus
dennis.atabay@gmail.com
"""
try:
	import pyomo.environ as pyen
	from pyomo.opt import SolverFactory
	from pyomo.opt import SolverManagerFactory
	import pandas as pd
	import numpy as np
	import time
	import os
except ImportError:
	pass



############################################################################################	
#RUN FUNCTIONS
############################################################################################

def run_ficus (input_file, opt = 'glpk', Threads = 2,neos=False):
	"""Read input data, create a model and solve it

	Args:
		opt: Solver to be used
		Threads: number of simultaneous CPU threads (only for gurobi and cplex)
		neos: set to TRUE, if solver from neos server should be used

	Returns:
		prob: model instance containing results
	"""
	# Optimizer
	# ============
	optimizer = SolverFactory(opt) #set optimizer	
	if optimizer.name == 'gurobi' and not neos:
		# reference with list of option names
        # http://www.gurobi.com/documentation/5.6/reference-manual/parameters
		optimizer.set_options("Threads="+str(Threads))  # number of simultaneous CPU threads

	elif optimizer.name == 'cplex' and not neos:
		optimizer.options["threads"] = Threads # number of simultaneous CPU threads
	else:
		print '\n Setting number of simultaneous CPU threads only available for locally installed "gurobi" and "cplex"\n'
	
	# RUN MODEL
	# ============
	#read model data	
	print 'Read Data ...\n'
	t0 = time.time()
	xls_data = read_xlsdata(input_file) 
	print 'Data Read. time: '+"{:.1f}".format(time.time()-t0)+' s\n'	
	
	#prepare data for model from xls_data
	print 'Prepare Data ...\n'
	t = time.time()
	data = prepare_modeldata(xls_data)
	print 'Data Prepared. time: '+"{:.1f}".format(time.time()-t)+' s\n'
	
	#define optimisation problem
	print 'Define Model ...\n'
	t = time.time()
	prob = create_model(data) 
	print 'Model Defined. time: '+"{:.1f}".format(time.time()-t)+' s\n'
	
	# solve the problem
	print 'Solve Model ...\n'
	t = time.time()
	if neos:
		solver_manager = SolverManagerFactory('neos')
		result = solver_manager.solve(prob,opt=optimizer,tee=True) 
	else:
		result = optimizer.solve(prob,tee=True) 
	print 'Model Solved. time: '+"{:.1f}".format(time.time()-t)+' s\n'
	
	print 'Load Results ...\n'
	t = time.time()
	prob.solutions.load_from(result) # load result back to model instance
	print 'Results Loaded. time: '+"{:.1f}".format(time.time()-t)+' s\n'
	print 'Total Time: '+"{:.1f}".format(time.time()-t0)+' s\n'
		
	return prob
		
def run_from_excel(input_file,opt):
	"""Run Model directly from excel with makro 

	Args:
		input_file: path of input file
		opt: solver
	"""
	import sys
	
	#create new time stamp folder in subfolder "result" with name of inputfile 
	result_name = os.path.splitext(os.path.split(input_file)[1])[0]
	result_folder = os.path.join(os.path.split(input_file)[0],'result')
	result_dir = prepare_result_directory(result_folder,result_name)

	#Use "cbc" or "mosek" solver from Neos server, if selected
	if 'neos' in opt:
		neos = True
		if 'cbc' in opt:
			opt = 'cbc'
		elif 'mosek' in opt:
			opt = 'mosek'
	else:
		neos = False
		
	#create and solve model from inputfile	
	prob = run_ficus(input_file, opt = opt,neos=neos)

	#save results
	report(prob, result_dir)
	#save figures	
	result_figures(result_dir,prob=prob, show=True)
	
	raw_input("Press Enter to close figures and cmd window...\n")
	
	return		
				
############################################################################################	
#Model
############################################################################################

def create_model(data):

	# Preparations
	# ============
	
	#Model Data
	time_settings = data['time-settings']
	mip_equations = data['mip-equations']
	ext_co = data['ext-co']
	ext_import = data['ext_import']
	ext_export = data['ext_export']
	demandrate_factor = data['demandrate_factor']
	process = data['process']
	process_commodity = data['process_commodity']
	process_class = data['process_class']
	storage = data['storage']
	demand = data['demand']
	supim = data['supim']

	
	#TIME PARAMETERS
	timesteps = np.arange (int(time_settings.loc['Time']['start']) - 1 , \
						int(time_settings.loc['Time']['end']) + 1)
	tb=int(time_settings.loc['Time']['timebase']) #timebase of time dependent data
	year_factor = float(timesteps.size-1) * tb / (365 * 24 * 60 * 60) # multiple of a year: opt_time[s] / year [s]
	p2e = float(tb) / 3600 # factor for converting power [kW] to energy [kWh] for one timestep
	
	
	# Flags
	# ============
	
	#Partload
	if process['partload-min'].any() == 0:
		mip_equations.loc['Partload']['Active']='no' #partload equations are irrelevant if "partload-min" = 0 for all processes
	if mip_equations.loc['Partload']['Active']=='no':
		#if "Partload" is deactivated, adjust process parameters
		process['partload-min']=0
		process['start-up-energy']=0
		process_commodity['ratio-partload']=process_commodity['ratio']
	elif mip_equations.loc['Partload']['Active']=='yes':
		if process_commodity['ratio-partload'].isnull().any():
			raise NotImplementedError("'ratio-partload' in sheet 'Process-Commodity' contains invalid values")
	
	#Min-Cap
	if (process['cap-new-min'].any() or storage['cap-new-min-p'].any() or storage['cap-new-min-e'].any()) == 0:
		mip_equations.loc['Min-Cap']['Active']='no' #partload equations are irrelevant if "partload-min" = 0 for all processes
	if mip_equations.loc['Min-Cap']['Active']=='no':
		#if "Min-Cap" is deactivated, adjust minimum capacity parameters
		process['cap-new-min']=0
		storage['cap-new-min-p']=0
		storage['cap-new-min-e']=0
	
	#=========
	#MODEL
	#=========

	m = pyen.ConcreteModel()
	m.name = 'ficus'
	m.inputfile = data['input_file']
	
	##Sets##
	########	
	#commodity
	m.commodity = pyen.Set(
		initialize=demand.columns | supim.columns | pd.Index(set(process_commodity.index.get_level_values(2))) | ext_import.columns,
		doc='Commodities')
		
	m.co_consumed = pyen.Set(
		within=m.commodity, 
		initialize=demand.columns | get_pro_inputs(process_commodity),
		doc='Commodities that are consumed by processes or demand')
		
	m.co_produced = pyen.Set(
		within=m.commodity, 
		initialize = get_pro_outputs(process_commodity),
		doc='Commodities that are produced by processes')
			
	m.co_ext_in = pyen.Set(
		within=m.commodity, 
		initialize=ext_import.columns,
		doc='Commodities in External-Supply-Price')
		
	m.co_ext_out = pyen.Set(
		within=m.commodity, 
		initialize=ext_export.columns,
		doc='Commodities in Feed-In-Price')
		
	m.co_ext = pyen.Set(
		within=m.commodity, 
		initialize=ext_export.columns | ext_import.columns,
		doc='Commodities in External Supply or Feed-In-Price')
		
	m.co_demand = pyen.Set(
		within=m.commodity, 
		initialize=demand.columns,
		doc='Commodities in Demand')

	m.co_storage = pyen.Set(
		within=m.commodity, 
		initialize=pd.Index(set(storage.index.get_level_values(1))),
		doc='Commodities stored in Storage')
		
	m.co_supim = pyen.Set(
		within=m.commodity, 
		initialize=supim.columns,
		doc='Commodities in supim')
		
	m.co_proclass = pyen.Set(
		within=m.commodity, 
		initialize=pd.Index(set(process_class.index.get_level_values(1))),
		doc='Commodities in Process Class')
		
	#process

	m.pro_name = pyen.Set(
		initialize=pd.Index(set(process.index.get_level_values(0))),
		doc='Name of Process')

	m.pro_num = pyen.Set(
		initialize=pd.Index(set(process.index.get_level_values(1))),
		doc='Num of Process')

	m.pro_tuples = pyen.Set(
		within=m.pro_name*m.pro_num,
		initialize=process.index.get_values(),
		doc='Processes, converting commodities')	
		
	m.pro_input_tuples = pyen.Set(
		within=m.pro_name*m.pro_num*m.commodity, 
		initialize = process_commodity.xs('In',level='Direction').index.get_values(),
		doc='Commodities consumed by processes')

	m.pro_output_tuples = pyen.Set(
		within=m.pro_name*m.pro_num*m.commodity, 
		initialize=process_commodity.xs('Out',level='Direction').index.get_values(),
		doc='Commodities emitted by processes')
		
	#Process Class
	
	m.proclass_name = pyen.Set( 
		initialize=pd.Index(set(process_class.index.get_level_values(0))),
		doc='Process Classes')
		
	m.proclass_tuples = pyen.Set( 
		within=m.proclass_name*m.commodity,
		initialize=process_class.index.get_values(),
		doc='Process Class tuples')

	#Storage

	m.storage_name = pyen.Set(
		initialize=pd.Index(set(storage.index.get_level_values(0))),
		doc='Name of Storage')
		
		
	m.storage_num = pyen.Set(
		initialize=pd.Index(set(storage.index.get_level_values(2))),
		doc='Num of Storage')

	m.sto_tuples = pyen.Set(
		within=m.storage_name*m.co_storage*m.storage_num,
		initialize=storage.index.get_values(),
		doc='storage name with stored commodity and num')

	# time
	m.t0 = pyen.Set(
		ordered=True,
		initialize=timesteps, 
		doc='Timesteps with zero')
		
	m.t = pyen.Set(
		within=m.t0,
		ordered=True,
		initialize=timesteps[1:], 
		doc='Timesteps for model')	

	# costs
	m.cost_type = pyen.Set(
		initialize=['Import', 'Export','Demand charges','Invest','Fix costs', 'Var costs','Process fee','Pro subsidy'],
		doc='Types of costs')	

		
	##Parameters##
	##############

	# process input/output ratios	
	m.r_in = process_commodity.xs('In', level='Direction')['ratio']
	m.r_in_partl = process_commodity.xs('In', level='Direction')['ratio-partload']
	m.r_out = process_commodity.xs('Out', level='Direction')['ratio']
	m.r_out_partl = process_commodity.xs('Out', level='Direction')['ratio-partload']
	
	#Calculate slope and offset for process input and output equations
	#For calculating power input/output p for each commodity dependent on power throughput "flow"
	# p = slope * flow + offset	
	m.pro_p_in_slope = pd.Series(index=m.r_in.index)
	m.pro_p_in_offset_spec = pd.Series(index=m.r_in.index)
	for idx in m.pro_p_in_slope.index:
		m.pro_p_in_slope.loc[idx] = (m.r_in.loc[idx] - m.r_in_partl.loc[idx]*process.loc[idx[0:2]]['partload-min'])/(1-process.loc[idx[0:2]]['partload-min'])
		m.pro_p_in_offset_spec[idx] = m.r_in.loc[idx]-m.pro_p_in_slope.loc[idx]	
	m.pro_p_out_slope = pd.Series(index=m.r_out.index)
	m.pro_p_out_offset_spec = pd.Series(index=m.r_out.index)
	for idx in m.pro_p_out_slope.index:
		m.pro_p_out_slope.loc[idx] = (m.r_out.loc[idx] - m.r_out_partl.loc[idx]*process.loc[idx[0:2]]['partload-min'])/(1-process.loc[idx[0:2]]['partload-min'])
		m.pro_p_out_offset_spec[idx] = m.r_out.loc[idx]-m.pro_p_out_slope.loc[idx]
	
	
	m.demand = demand
	m.supim = supim
	m.tb = tb
	
	
	##Variables##
	##############
	
	#Commodity Energy Balance
	m.co_e_consumed = pyen.Var(
			m.co_consumed, within=pyen.NonNegativeReals,
			doc='total energy consumed of commodity')
	m.co_e_produced = pyen.Var(
			m.co_produced, within=pyen.NonNegativeReals,
			doc='total energy produced of commodity')
	

	#Commodity Power flow

	m.pro_p_flow= pyen.Var(
			m.pro_tuples,m.t0, within=pyen.NonNegativeReals,
			doc='power flow (kW) through process')
	m.pro_p_in = pyen.Var(
			m.pro_input_tuples,m.t, within=pyen.NonNegativeReals,
			doc='power flow (kW) of commodity into process')
	m.pro_p_out = pyen.Var(
			m.pro_output_tuples,m.t, within=pyen.NonNegativeReals,
			doc='power flow (kW) of commodity out of process')
			
	m.ext_p_in= pyen.Var(
			m.co_ext_in,m.t, within=pyen.NonNegativeReals,
			doc='power flow (kW) of commodity from extern source')
	m.ext_p_out= pyen.Var(
			m.co_ext_out,m.t, within=pyen.NonNegativeReals,
			doc='power flow (kW) of commodity to extern (export)')

	m.ext_demandrate_in= pyen.Var(
			m.co_ext_in,m.t, within=pyen.NonNegativeReals,
			doc=' power flow (kW) of imported commodity in one timestep based in demand rate time interval')		
	m.ext_demandrate_out= pyen.Var(
			m.co_ext_out,m.t, within=pyen.NonNegativeReals,
			doc='power flow (kW) of exported commodity in one timestep based in demand rate time interval')		
	m.ext_demandrate_max= pyen.Var(
			m.co_ext_in, within=pyen.NonNegativeReals,
			doc='max power flow (kW) of imported or exported commodity in one timestep based in demand rate time interval')
			
	m.sto_p_in= pyen.Var(
			m.sto_tuples, m.t, within=pyen.NonNegativeReals,
			doc='power flow (kW) in storage')
	m.sto_p_out= pyen.Var(
			m.sto_tuples, m.t, within=pyen.NonNegativeReals,
			doc='power flow (kW) out of storage')


	#Process

	m.pro_cap = pyen.Var(
			m.pro_tuples, within=pyen.NonNegativeReals,
			doc='Capacity (kW) of process')
	m.pro_cap_new = pyen.Var(
			m.pro_tuples, within=pyen.NonNegativeReals,
			doc='New additional Capacity (kW) of process')								

	if mip_equations.loc['Min-Cap']['Active']=='yes':
		m.pro_cap_build = pyen.Var(
				m.pro_tuples, within=pyen.Boolean,
				doc='Boolean: True if new capacity is build. Needed for minimum new capacity')
	elif mip_equations.loc['Min-Cap']['Active']=='no':
		m.pro_cap_build = pyen.Param(
				m.pro_tuples, initialize=1,
				doc='No Min-Cap: Build = 1')
	else:
		raise NotImplementedError("For mip_equations only 'yes' or 'no' are valid inputs")
			
	if mip_equations.loc['Partload']['Active']=='yes':
		m.pro_p_in_offset= pyen.Var(
			m.pro_input_tuples,m.t, within=pyen.Reals,
			doc='offset for calculating process input (kW)')
		m.pro_p_out_offset= pyen.Var(
			m.pro_output_tuples,m.t, within=pyen.Reals,
			doc='offset for calculating process output (kW)')	
		m.pro_mode_run= pyen.Var(
			m.pro_tuples,m.t0, within=pyen.Boolean,
			doc='booelan : true if process in run mode')
		m.pro_mode_startup= pyen.Var(
			m.pro_tuples,m.t, within=pyen.NonNegativeReals,
			doc='1 if process is "switched" on, 0 else')
		m.pro_p_startup = pyen.Var(
			m.pro_input_tuples,m.t, within=pyen.NonNegativeReals,
			doc='switch on power losses (kW)')
	elif mip_equations.loc['Partload']['Active']=='no':
		m.pro_p_in_offset= pyen.Param(
			m.pro_input_tuples,m.t, initialize=0,
			doc='No Partload: offset is zero')
		m.pro_p_out_offset= pyen.Param(
			m.pro_output_tuples,m.t, initialize=0,
			doc='No Partload: offset is zero')	
		m.pro_mode_run= pyen.Param(
				m.pro_tuples,m.t0, initialize=1,
				doc='No Partload: run=1')
		m.pro_mode_startup= pyen.Param(
			m.pro_tuples,m.t, initialize=0,
			doc='No Partload: startup=0')
		m.pro_p_startup= pyen.Param(
			m.pro_input_tuples,m.t, initialize=0,
			doc='No Partload: startup_loss=0')
	else:
		raise NotImplementedError("For mip_equations only 'yes' or 'no' are valid inputs")
		
		
	#PROCESS CLASS
	m.proclass_cap = pyen.Var(
			m.proclass_tuples, within=pyen.NonNegativeReals,
			doc='Capacity (kW) of all processes in class and commodity')
			
	m.proclass_e_out = pyen.Var(
			m.proclass_tuples, within=pyen.NonNegativeReals,
			doc='Energy output (kWh) of all processes in class and commodity')
			
	m.proclass_e_in = pyen.Var(
			m.proclass_tuples, within=pyen.NonNegativeReals,
			doc='Energy input (kWh) of all processes in class and commodity')
				
	
	#STORAGE
	m.sto_cap_e = pyen.Var(
			m.sto_tuples, within=pyen.NonNegativeReals,
			doc='Energy Capacity (kWh) ofstorage')
	m.sto_cap_e_new = pyen.Var(
			m.sto_tuples, within=pyen.NonNegativeReals,
			doc='New additional Energy Capacity (kW) of storage')
			
	m.sto_cap_p = pyen.Var(
			m.sto_tuples, within=pyen.NonNegativeReals,
			doc='Power Capacity (kW) of storage')
	m.sto_cap_p_new = pyen.Var(
			m.sto_tuples, within=pyen.NonNegativeReals,
			doc='New additional Power Capacity (kW) of storage')
			
	m.sto_e_cont = pyen.Var(
			m.sto_tuples, m.t0, within=pyen.NonNegativeReals,
			doc='Energy content in storage')
			
	if mip_equations.loc['Min-Cap']['Active']=='yes':
		m.sto_cap_build = pyen.Var(
			m.sto_tuples, within=pyen.Boolean,
			doc='Boolean: True if new capacity is build. Needed for minimum new capacity')	
	elif mip_equations.loc['Min-Cap']['Active']=='no':
			m.sto_cap_build = pyen.Param(
				m.sto_tuples, initialize=1,
				doc='Boolean: True if new capacity is build. Needed for minimum new capacity')
	else:
		raise NotImplementedError("For mip_equations only 'yes' or 'no' are valid inputs")
			
	if mip_equations.loc['Storage In-Out']['Active'] == 'yes':
		m.sto_charge = pyen.Var(
				m.co_storage, m.t, within=pyen.Boolean,
				doc='Bool Variable, 1 if charging')	
	elif mip_equations.loc['Storage In-Out']['Active'] == 'no':
		pass
	else:
		raise NotImplementedError("For mip_equations only 'yes' or 'no' are valid inputs")
	
	
	#COSTS
	m.costs = pyen.Var(
			m.cost_type, within=pyen.Reals,
			doc='cost by cost types') 
	
	##Equations##
	##############

	"""COMMODITY"""
	
	def co_energy_consumption_rule(m, co):
		return m.co_e_consumed[co] ==  energy_consumption(m, co) * p2e
	m.co_energy_consumption = pyen.Constraint(
		m.co_consumed,
		rule = co_energy_consumption_rule,
		doc='commodity: total energy consumed ')
		
	def co_energy_production_rule(m, co):
		return m.co_e_produced[co] ==  energy_production(m, co) * p2e
	m.co_energy_production = pyen.Constraint(
		m.co_produced,
		rule = co_energy_production_rule,
		doc='commodity: total energy produced ')
	
	def co_power_balance_rule(m, co, t):
		co_balance =  commodity_balance(m, co, t)
		return co_balance  == 0
	m.co_power_balance = pyen.Constraint(
		m.commodity, m.t,
		rule=co_power_balance_rule,
		doc='power balance must be zero for every timestep')

	""" PROCESS """

	#initial
	def pro_p_flow_init_rule(m,pro,num,t):
		if t == m.t0[1]:
			return m.pro_p_flow[pro,num,t] == process.loc[pro,num]['initial-power']
		else:
			return pyen.Constraint.Skip
	m.pro_p_flow_init = pyen.Constraint(
		m.pro_tuples,m.t0,
		rule = pro_p_flow_init_rule,
		doc='initial p_flow')
	
	if mip_equations.loc['Partload']['Active']=='yes':
		def pro_mode_run_init_rule(m,pro,num,t):
			if t == m.t0[1]:
				return m.pro_mode_run[pro,num,t] == process.loc[pro,num]['initial-run']
			else:
				return pyen.Constraint.Skip
		m.pro_mode_run_init = pyen.Constraint(
			m.pro_tuples,m.t0,
			rule = pro_mode_run_init_rule,
			doc='initial run mode')

		
	# capacity		
	def pro_cap_abs_rule(m,pro,num):
		return m.pro_cap[pro,num] == m.pro_cap_new[pro,num] + process.loc[pro,num]['cap-installed']
	m.pro_cap_abs = pyen.Constraint(
		m.pro_tuples,
		rule = pro_cap_abs_rule,
		doc='capacity = cap_new + cap_installed')
		

	def pro_cap_new_max_rule(m,pro,num):
		return m.pro_cap_new[pro,num] <= m.pro_cap_build[pro,num] * process.loc[pro,num]['cap-new-max']
	m.pro_cap_new_max = pyen.Constraint(
		m.pro_tuples,
		rule = pro_cap_new_max_rule,
		doc='limit max new capacity of process')
		
	def pro_cap_new_min_rule(m,pro,num):
		return m.pro_cap_new[pro,num] >= m.pro_cap_build[pro,num] * process.loc[pro,num]['cap-new-min']
	m.pro_cap_new_min = pyen.Constraint(
		m.pro_tuples,
		rule=pro_cap_new_min_rule,
		doc='limit min new capacity of process, if it is built')
	
	#flow
	def pro_p_flow_max_rule(m,pro,num,t):
		return m.pro_p_flow[pro,num,t] <= \
			m.pro_cap[pro,num]
	m.pro_p_flow_max = pyen.Constraint(
		m.pro_tuples,m.t,
		rule = pro_p_flow_max_rule,
		doc='p_flow <= capacity of process')
	
	#Supim
	def pro_p_supim_input_rule(m,pro,num,co,t):
		if co in m.co_supim:
			return m.pro_p_in[pro,num,co,t] <= \
				m.pro_cap[pro,num] * supim.loc[t][co]*m.r_in[pro,num,co]
		else:
			return pyen.Constraint.Skip
	m.pro_p_supim_input = pyen.Constraint(
		m.pro_input_tuples,m.t,
		rule=pro_p_supim_input_rule,
		doc='Limit power input from "supim" to installed capacity')
	# in	
	def pro_p_input_rule(m,pro,num,co,t):
		return m.pro_p_in[pro,num,co,t] == \
				m.pro_p_flow[pro,num,t] * m.pro_p_in_slope[pro,num,co]\
				+ m.pro_p_in_offset[pro,num,co,t]\
				+ m.pro_p_startup[pro,num,co,t]
	m.pro_p_input = pyen.Constraint(
		m.pro_input_tuples,m.t,
		rule=pro_p_input_rule,
		doc='Calculate input power for every commodity dependent on ratios\
			p_in = p_flow * p_slope_in + p_offset_in + startup * E_startup/t*r_in;')
	
	#out	
	def pro_p_output_rule(m,pro,num,co,t):
		return m.pro_p_out[pro,num,co,t] == m.pro_p_flow[pro,num,t] * m.pro_p_out_slope[pro,num,co]\
											+ m.pro_p_out_offset[pro,num,co,t] 
	m.pro_p_output = pyen.Constraint(
		m.pro_output_tuples, m.t,
		rule=pro_p_output_rule,
		doc='Calculate output power for every commodity dependent on ratios\
			p_out = p_flow  *  p_slope_out + p_offset_out')		

	if mip_equations.loc['Partload']['Active']=='yes':
		#offset in	
		def pro_p_in_offset_lt_rule(m,pro,num,co,t):
			return m.pro_p_in_offset[pro,num,co,t] \
					- (m.pro_p_in_offset_spec[pro,num,co] * m.pro_cap[pro,num]) \
					<= (1 - m.pro_mode_run[pro,num,t]) * process.loc[pro,num]['cap-abs-max']*m.r_in[pro,num,co]
		m.pro_p_in_offset_lt = pyen.Constraint(
			m.pro_input_tuples,m.t,
			rule = pro_p_in_offset_lt_rule,
			doc='offset must be (lower) equal to offset_spec*cap , when run = 1\
			p_offset - (offset_spec*cap) <= (1-run) * cap-max -> p_offset <= (offset_spec*cap) if run=1. ')
			
		def pro_p_in_offset_gt_rule(m,pro,num,co,t):
			return m.pro_p_in_offset[pro,num,co,t] - (m.pro_p_in_offset_spec[pro,num,co] * m.pro_cap[pro,num])\
			>= -(1 - m.pro_mode_run[pro,num,t]) * process.loc[pro,num]['cap-abs-max']*m.r_in[pro,num,co]
		m.pro_p_in_offset_gt = pyen.Constraint(
			m.pro_input_tuples,m.t,
			rule = pro_p_in_offset_gt_rule,
			doc='offset must be (greater) equal to offset_spec*cap , when run = 1\
			p_offset - (offset_spec*cap) >= -(1-run) * cap-max -> p_offset >= (offset_spec*cap) if run=1')	

		def pro_p_offset_in_ltzero_when_off_rule(m,pro,num,co,t):
			return m.pro_p_in_offset[pro,num,co,t] <= \
				(m.pro_mode_run[pro,num,t]) * \
				process.loc[pro,num]['cap-abs-max']*m.r_in[pro,num,co]
		m.pro_p_offset_in_ltzero_when_off = pyen.Constraint(
			m.pro_input_tuples,m.t,
			rule = pro_p_offset_in_ltzero_when_off_rule,
			doc='p_offset must be (lower) equal to zero when run=0\
				p_offset <= run * cap_max')	
				
		def pro_p_offset_in_gtzero_when_off_rule(m,pro,num,co,t):
			return m.pro_p_in_offset[pro,num,co,t] >= \
				-(m.pro_mode_run[pro,num,t]) * \
				process.loc[pro,num]['cap-abs-max']*m.r_in[pro,num,co]
		m.pro_p_offset_in_gtzero_when_off = pyen.Constraint(
			m.pro_input_tuples,m.t,
			rule = pro_p_offset_in_gtzero_when_off_rule,
			doc='p_offset must be (greater) equal to zero when run=0\
				p_offset >= run * cap_max')		
					
		#offset out		
		def pro_p_out_offset_lt_rule(m,pro,num,co,t):
			return m.pro_p_out_offset[pro,num,co,t] - (m.pro_p_out_offset_spec[pro,num,co] * m.pro_cap[pro,num])\
			<= (1 - m.pro_mode_run[pro,num,t]) * process.loc[pro,num]['cap-abs-max']*m.r_out[pro,num,co]
		m.pro_p_out_offset_lt = pyen.Constraint(
			m.pro_output_tuples,m.t,
			rule = pro_p_out_offset_lt_rule,
			doc='offset must be (lower) equal to offset_spec*cap , when run = 1\
			p_offset - (offset_spec*cap) <= (1-run) * cap-max -> p_offset <= (offset_spec*cap) if run=1. ')
			
		def pro_p_out_offset_gt_rule(m,pro,num,co,t):
			return m.pro_p_out_offset[pro,num,co,t] - (m.pro_p_out_offset_spec[pro,num,co] * m.pro_cap[pro,num])\
			>= -(1 - m.pro_mode_run[pro,num,t]) * process.loc[pro,num]['cap-abs-max']*m.r_out[pro,num,co]
		m.pro_p_out_offset_gt = pyen.Constraint(
			m.pro_output_tuples,m.t,
			rule = pro_p_out_offset_gt_rule,
			doc='offset must be (greater) equal to offset_spec*cap , when run = 1\
			p_offset - (offset_spec*cap) >= -(1-run) * cap-max -> p_offset >= (offset_spec*cap) if run=1')
		
		def pro_p_offset_out_ltzero_when_off_rule(m,pro,num,co,t):
			return m.pro_p_out_offset[pro,num,co,t] <= \
				(m.pro_mode_run[pro,num,t]) * \
				process.loc[pro,num]['cap-abs-max']*m.r_out[pro,num,co]
		m.pro_p_offset_out_ltzero_when_off = pyen.Constraint(
			m.pro_output_tuples,m.t,
			rule = pro_p_offset_out_ltzero_when_off_rule,
			doc='p_offset is zero when mode not "run"')
			
		def pro_p_offset_out_gtzero_when_off_rule(m,pro,num,co,t):
			return m.pro_p_out_offset[pro,num,co,t] >= \
				-(m.pro_mode_run[pro,num,t]) * \
				process.loc[pro,num]['cap-abs-max']*m.r_out[pro,num,co]
		m.pro_p_offset_out_gtzero_when_off = pyen.Constraint(
			m.pro_output_tuples,m.t,
			rule = pro_p_offset_out_gtzero_when_off_rule,
			doc='p_offset is zero when mode not "run"')	
		
		# mode	
		def pro_p_flow_zero_when_off_rule(m,pro,num,t):
			return m.pro_p_flow[pro,num,t] <= \
				(m.pro_mode_run[pro,num,t]) * \
				process.loc[pro,num]['cap-abs-max']
		m.pro_p_flow_zero_when_off = pyen.Constraint(
			m.pro_tuples,m.t,
			rule=pro_p_flow_zero_when_off_rule,
			doc='p_flow is zero when run = 0')

			
		def pro_p_gt_partload_rule(m,pro,num,t):
			return (m.pro_p_flow[pro,num,t] - m.pro_cap[pro,num] * process.loc[pro,num]['partload-min']) >= -(1 - m.pro_mode_run[pro,num,t]) * process.loc[pro,num]['cap-abs-max']		
		m.pro_p_gt_partload = pyen.Constraint(
			m.pro_tuples,m.t,
			rule = pro_p_gt_partload_rule,
			doc='p_flow >= capacity * partload if run =1 ')
		
		#switch on losses			
		def pro_mode_start_up1_rule(m,pro,num,t):
			return m.pro_mode_startup[pro,num,t] >= \
				m.pro_mode_run[pro,num,t] - \
				(m.pro_mode_run[pro,num,t-1])
		m.pro_mode_start_up1 = pyen.Constraint(
			m.pro_tuples,m.t,
			rule=pro_mode_start_up1_rule,
			doc='switch on >=  run[t] - run[t-1]')
			
		def pro_mode_start_up2_rule(m,pro,num,t):
			return m.pro_mode_startup[pro,num,t] <= \
				m.pro_mode_run[pro,num,t]
		m.pro_mode_start_up2 = pyen.Constraint(
			m.pro_tuples,m.t,
			rule=pro_mode_start_up2_rule,
			doc='switch on <= run[t]')
			
		def pro_mode_start_up3_rule(m,pro,num,t):
			return m.pro_mode_startup[pro,num,t] <= \
				1 - m.pro_mode_run[pro,num,t-1]
		m.pro_mode_start_up3 = pyen.Constraint(
			m.pro_tuples,m.t,
			rule=pro_mode_start_up3_rule,
			doc='switch on <= run[t-1]')
			
		def pro_p_startup_lt_rule(m,pro,num,co,t):
			return (m.pro_p_startup[pro,num,co,t]\
					- (process.loc[pro,num]['start-up-energy'] / p2e \
						* m.r_in[pro,num,co]*m.pro_cap[pro,num]))\
					<= ((1 - m.pro_mode_startup[pro,num,t]) \
						* (process.loc[pro,num]['start-up-energy'] / p2e\
						* m.r_in[pro,num,co]*process.loc[pro,num]['cap-abs-max']))
		m.pro_p_startup_lt = pyen.Constraint(
			m.pro_input_tuples,m.t,
			rule = pro_p_startup_lt_rule,
			doc='switch on loss must be (lower) equal to p_startup_spec*cap , when startup = 1\
			p_startup - (startup_spec*cap) <= (1-startup) * cap-max -> p_startup <= (p_startup_spec*cap) if startup=1. ')
			
		def pro_p_startup_gt_rule(m,pro,num,co,t):
			return (m.pro_p_startup[pro,num,co,t]\
					- (process.loc[pro,num]['start-up-energy'] / p2e\
						* m.r_in[pro,num,co]*m.pro_cap[pro,num]))\
					>= -((1 - m.pro_mode_startup[pro,num,t]) \
						* (process.loc[pro,num]['start-up-energy'] / p2e\
						* m.r_in[pro,num,co]*process.loc[pro,num]['cap-abs-max']))
		m.pro_p_startup_gt = pyen.Constraint(
			m.pro_input_tuples,m.t,
			rule = pro_p_startup_gt_rule,
			doc='switch on loss must be (greater) equal to p_startup_spec*cap , when startup = 1\
			p_startup - (startup_spec*cap) >= -(1-startup) * cap-max -> p_startup >= (p_startup_spec*cap) if startup=1. ')
			
		def pro_p_startup_zerowhenoff_rule(m,pro,num,co,t):
			return m.pro_p_startup[pro,num,co,t]\
					<= m.pro_mode_startup[pro,num,t] \
						* (process.loc[pro,num]['start-up-energy'] / p2e\
						* m.r_in[pro,num,co]*process.loc[pro,num]['cap-abs-max'])
		m.pro_p_startup_zerowhenoff = pyen.Constraint(
			m.pro_input_tuples,m.t,
			rule = pro_p_startup_zerowhenoff_rule,
			doc='switch on loss must be zerowhen startup = 0')
					
	
	"""PROCESS CLASS"""
	# CALCULATIONS		
	def proclass_cap_sum_rule(m,cl,co):			
		return m.proclass_cap[cl,co] == \
				sum(m.pro_cap[p[0:2]] * m.r_out[p]\
					for p in m.pro_output_tuples
					if co in p
					if cl == process.loc[p[0:2]]['class'])\
				+ sum(m.pro_cap[p[0:2]] * m.r_in[p]\
					for p in m.pro_input_tuples
					if co in p
					if cl == process.loc[p[0:2]]['class'])
	m.proclass_cap_sum = pyen.Constraint(
		m.proclass_tuples,
		rule=proclass_cap_sum_rule,
		doc='Calculate total capacity of class and commodity') 
				
	def proclass_e_out_sum_rule(m,cl,co):			
		return m.proclass_e_out[cl,co] == \
				sum(m.pro_p_out[p,t] * p2e\
					for t in m.t
					for p in m.pro_output_tuples\
					if co in p
					if cl == process.loc[p[0:2]]['class'])
	m.proclass_e_out_sum = pyen.Constraint(
		m.proclass_tuples,
		rule=proclass_e_out_sum_rule,
		doc='Calculate total energy outpout of class and commodity') 
		
	def proclass_e_in_sum_rule(m,cl,co):			
		return m.proclass_e_in[cl,co] == \
				sum(m.pro_p_in[p,t] * p2e\
					for t in m.t
					for p in m.pro_input_tuples\
					if co in p
					if cl == process.loc[p[0:2]]['class'])
	m.proclass_e_in_sum = pyen.Constraint(
		m.proclass_tuples,
		rule=proclass_e_in_sum_rule,		
		doc='Calculate total energy outpout of class and commodity') 
			
	# CONSTRAINTS
		
	def proclass_cap_max_rule(m, cl, co):
		return m.proclass_cap[cl,co] <= \
				process_class.loc[cl,co]['cap-max']
	m.proclass_cap_max = pyen.Constraint(
		m.proclass_tuples,
		rule=proclass_cap_max_rule,
		doc='limitmax capacity of class and commodity')
		
	def proclass_e_max_rule(m, cl, co):
		if process_class.loc[cl,co]['Direction'] == 'In':
			return m.proclass_e_in[cl,co] <= \
					process_class.loc[cl,co]['energy-max'] * year_factor
		if process_class.loc[cl,co]['Direction'] == 'Out':
			return m.proclass_e_out[cl,co] <= \
					process_class.loc[cl,co]['energy-max'] * year_factor
	m.proclass_e_max = pyen.Constraint(
		m.proclass_tuples,
		rule=proclass_e_max_rule,
		doc='limitmax energy output of class and commodity')

	"""STORAGE"""
	#initial
	def sto_e_cont_init_rule(m,sto,co,num,t):
		if t == m.t0[1]:
			return m.sto_e_cont[sto,co,num,t] == \
				storage.loc[sto,co,num]['initial-soc'] *  m.sto_cap_e[sto,co,num]
		elif t == m.t0[-1]:
			return m.sto_e_cont[sto,co,num,t] == \
				storage.loc[sto,co,num]['initial-soc'] *  m.sto_cap_e[sto,co,num]
		else:
			return pyen.Constraint.Skip
	m.sto_e_cont_init = pyen.Constraint(
		m.sto_tuples,m.t0,
		rule=sto_e_cont_init_rule,
		doc='initial and minimum final content of energy storage')
		
		
	# capacity		
	def sto_cap_e_abs_rule(m,sto,co,num):
		return m.sto_cap_e[sto,co,num] == \
				m.sto_cap_e_new[sto,co,num] + storage.loc[sto,co,num]['cap-installed-e']
	m.sto_cap_e_abs = pyen.Constraint(
		m.sto_tuples,
		rule=sto_cap_e_abs_rule,
		doc='Energy Capacity: capacity = cap_new + cap_installed')

	def sto_cap_e_new_max_rule(m,sto,co,num):
		return m.sto_cap_e_new[sto,co,num] <= \
				m.sto_cap_build[sto,co,num] * storage.loc[sto,co,num]['cap-new-max-e']
	m.sto_cap_e_new_max = pyen.Constraint(
		m.sto_tuples,
		rule=sto_cap_e_new_max_rule,
		doc='Energy Capacity:: limit max new capacity of storage')
		
	def sto_cap_e_new_min_rule(m,sto,co,num):
		return m.sto_cap_e_new[sto,co,num] >= \
				m.sto_cap_build[sto,co,num] * storage.loc[sto,co,num]['cap-new-min-e']
	m.sto_cap_e_new_min = pyen.Constraint(
		m.sto_tuples,
		rule=sto_cap_e_new_min_rule,
		doc='Energy Capacity:: limit min new capacity of storage')
			
	def sto_cap_p_abs_rule(m,sto,co,num):
		return m.sto_cap_p[sto,co,num] == \
				m.sto_cap_p_new[sto,co,num] + storage.loc[sto,co,num]['cap-installed-p']
	m.sto_cap_p_abs = pyen.Constraint(
		m.sto_tuples,
		rule=sto_cap_p_abs_rule,
		doc='Power Capacity: capacity = cap_new + cap_installed')

	def sto_cap_p_new_max_rule(m,sto,co,num):
		return m.sto_cap_p_new[sto,co,num] <= \
				m.sto_cap_build[sto,co,num] * storage.loc[sto,co,num]['cap-new-max-p']
	m.sto_cap_p_new_max = pyen.Constraint(
		m.sto_tuples,
		rule=sto_cap_p_new_max_rule,
		doc='Power Capacity:: limit max new capacity of storage')
		
	def sto_cap_p_new_min_rule(m,sto,co,num):
		return m.sto_cap_p_new[sto,co,num] >= \
				m.sto_cap_build[sto,co,num] * storage.loc[sto,co,num]['cap-new-min-p']
	m.sto_cap_p_new_min = pyen.Constraint(
		m.sto_tuples,
		rule=sto_cap_p_new_min_rule,
		doc='Power Capacity:: limit min new capacity of storage')
			
	def sto_cap_p_c_relation_rule(m,sto,co,num):
		return m.sto_cap_p[sto,co,num] <= \
				m.sto_cap_e[sto,co,num] * storage.loc[sto,co,num]['max-p-e-ratio']
	m.sto_cap_p_c_relation = pyen.Constraint(
		m.sto_tuples,
		rule=sto_cap_p_c_relation_rule,
		doc='max ratio between power and energy capacity of storage, if not independent')
	
	#in-out
	def sto_p_in_max_rule(m,sto,co,num,t):
		return m.sto_p_in[sto,co,num,t] <= \
				m.sto_cap_p[sto,co,num]
	m.sto_p_in_max = pyen.Constraint(
		m.sto_tuples, m.t,
		rule=sto_p_in_max_rule,
		doc='max charge power')

	def sto_p_out_max_rule(m,sto,co,num,t):
		return m.sto_p_out[sto,co,num,t] <= \
				m.sto_cap_p[sto,co,num]
	m.sto_p_out_max = pyen.Constraint(
		m.sto_tuples, m.t,
		rule=sto_p_out_max_rule,
		doc='max discharge power')
		

	if mip_equations.loc['Storage In-Out']['Active'] == 'yes':
		def sto_p_in_not_out_rule(m,sto,co,num,t):
			return m.sto_p_in[sto,co,num,t] <= \
					m.sto_charge[co,t]*\
					(storage.loc[sto,co,num]['cap-new-max-p']+storage.loc[sto,co,num]['cap-installed-p'])
		m.sto_p_in_not_out = pyen.Constraint(
			m.sto_tuples, m.t,
			rule = sto_p_in_not_out_rule,
			doc='only charge, when not discharging')
		
		def sto_p_out_not_in_rule(m,sto,co,num,t):
			return m.sto_p_out[sto,co,num,t] <= \
					(1-m.sto_charge[co,t])*\
					(storage.loc[sto,co,num]['cap-new-max-p']+storage.loc[sto,co,num]['cap-installed-p'])
		m.sto_p_out_not_in = pyen.Constraint(
			m.sto_tuples, m.t,
			rule = sto_p_out_not_in_rule,
			doc='only discharge, when not charging')
		
		
	#Energy Content
	def sto_e_cont_def_rule(m,sto,co,num,t):
		return m.sto_e_cont[sto,co,num,t] == \
				m.sto_e_cont[sto,co,num,t-1] \
					* (1 - storage.loc[sto,co,num]['self-discharge'] * p2e)\
				+ m.sto_p_in[sto,co,num,t] * storage.loc[sto,co,num]['eff-in'] *p2e\
				- m.sto_p_out[sto,co,num,t] / storage.loc[sto,co,num]['eff-out'] * p2e
	m.sto_e_cont_def = pyen.Constraint(
		m.sto_tuples, m.t,
		rule=sto_e_cont_def_rule,
		doc='Energy Content of Storage: E(t) = E(t-1)*(1 - self_disch) + P_in*eff_in - P_out/eff_out')
			
	def sto_e_cont_max_rule(m,sto,co,num,t):
		return m.sto_e_cont[sto,co,num,t] <= m.sto_cap_e[sto,co,num] * storage.loc[sto,co,num]['DOD']
	m.sto_e_cont_max = pyen.Constraint(
		m.sto_tuples, m.t,
		rule=sto_e_cont_max_rule,
		doc='Energy Content of Storage lower than energy capacity of storage')
		
	# CHARGE CYCLES
	
	def sto_max_cycle_rule(m,sto,co,num):
		return sum( m.sto_p_in[sto,co,num,t] * p2e for t in m.t) <=\
				m.sto_cap_e[sto,co,num] \
				* storage.loc[sto,co,num]['DOD'] * storage.loc[sto,co,num]['cycles-max']\
				* year_factor/storage.loc[sto,co,num]['lifetime']
	m.sto_max_cycle= pyen.Constraint(
		m.sto_tuples,
		rule=sto_max_cycle_rule,
		doc='sum(P_in*tb) <= cap_E *DOD* Z_max (similar to Z*cap<=Z_max*cap)')
	
		
	"""GRID"""
	def ext_p_in_max_rule(m, co, t):
		return m.ext_p_in[co,t] <= ext_co.loc[co]['import-max']
	m.ext_p_in_max = pyen.Constraint(
		m.co_ext_in, m.t,
		rule=ext_p_in_max_rule,
		doc='max power import(kW) for every timestep ')

	def ext_p_out_max_rule(m, co, t):
		return m.ext_p_out[co,t] <= ext_co.loc[co]['export-max']
	m.ext_p_out_max = pyen.Constraint(
		m.co_ext_out, m.t,
		rule=ext_p_out_max_rule,
		doc='max power export (kW) for every timestep ')			
	
	
	def demandrate_initial_max_rule(m, co, t):
		return m.ext_demandrate_max[co] >= ext_co.loc[co]['p-max-initial']
	m.demandrate_initial_max = pyen.Constraint(
		m.co_ext_in, m.t,
		rule=demandrate_initial_max_rule,
		doc='p-max for demand charge calculation dependent on initial p-max')

	def demandrate_in_def_max_rule(m, co, t):
		return m.ext_demandrate_max[co] >= m.ext_demandrate_in[co,t]#
	m.demandrate_in_def_max = pyen.Constraint(
		m.co_ext_in, m.t,
		rule=demandrate_in_def_max_rule,
		doc='p-max for demand charge calculation dependent on p_ext_in')
	
	
	def demandrate_in_tb_rule(m, co, t):
		t_rel=ext_co.loc[co]['time-interval-demand-rate']/tb #relation of power price and opt timebase
		if (t%t_rel) == 0:
			return m.ext_demandrate_in[co,t] == \
				sum(\
					m.ext_p_in[co,tg]\
					for tg in np.arange(t-t_rel+1,t+1))\
				/t_rel *  demandrate_factor.loc[t][co]
		else:
			return m.ext_demandrate_in[co,t] == 0
	m.demandrate_in_tb = pyen.Constraint(
		m.co_ext_in, m.t,
		rule=demandrate_in_tb_rule,
		doc='adapt p_ext_in to timbase of demand rate and consider demand-rate-factor')
		
	def ext_min_operation_hours_rule(m, co):
		return sum(m.ext_demandrate_in[co,t]*p2e for t in m.t) >= \
				ext_co.loc[co]['operating-hours-min'] * m.ext_demandrate_max[co] * year_factor
	m.ext_min_operation_hours = pyen.Constraint(
		m.co_ext_in,
		rule=ext_min_operation_hours_rule,
		doc='limit min "operating hours" E_in/P_max_in >= "op-hours-min" in hours per year')
	
	"""Cost Function"""

	def cost_sum_rule(m, cost_type):
		#Investment costs for new capacity = new_cap * inv_costs
		if cost_type == 'Invest':
			return m.costs[cost_type] == \
				sum(m.pro_cap_new[p] * \
					process.loc[p]['cost-inv'] * \
					process.loc[p]['annuity_factor']\
					for p in m.pro_tuples)\
				+sum(m.sto_cap_p_new[s] * 
						storage.loc[s]['cost-inv-p'] * 
						storage.loc[s]['annuity_factor']\
					+m.sto_cap_e_new[s] * 
						storage.loc[s]['cost-inv-e'] * 
						storage.loc[s]['annuity_factor']\
					for s in m.sto_tuples)
		
		#operation independent costs = capacity * cost_fix
		elif cost_type == 'Fix costs':
			return m.costs[cost_type] == \
				sum(m.pro_cap[p] * process.loc[p]['cost-fix']\
					for p in m.pro_tuples)\
				+sum(m.sto_cap_p[s] * storage.loc[s]['cost-fix-p']
					+m.sto_cap_e[s] * storage.loc[s]['cost-fix-e'] 
					for s in m.sto_tuples)
		
		# Variable costs dependent on energy through process/storage = sum(t)[cost_var * energy(t)] 
		elif cost_type == 'Var costs':
			return m.costs[cost_type] == \
				sum(m.pro_p_flow[p,t] * p2e \
					*process.loc[p]['cost-var']\
					for t in m.t for p in m.pro_tuples)/year_factor\
				+sum((m.sto_p_in[s,t] + m.sto_p_out[s,t]) * p2e * storage.loc[s]['cost-var']
					for t in m.t for s in m.sto_tuples)/year_factor
		
		#costs for external import = sum(t) [ p_ext) * price(t)]
		elif cost_type == 'Import':	
			return m.costs[cost_type] == \
				sum(m.ext_p_in[c,t]*p2e \
					* (ext_import.loc[t][c])\
					for t in m.t for c in m.co_ext_in)/year_factor
		
		#costs for export = sum(t) [- p_ext_export(t) * price(t)]
		elif cost_type == 'Export':	
			return m.costs[cost_type] == \
				-sum( m.ext_p_out[c,t] * p2e * ext_export.loc[t][c]\
					for t in m.t for c in m.co_ext_out)/year_factor
		
		# Costs for grid use = p_max * power_price
		elif cost_type == 'Demand charges':
			return m.costs[cost_type] == \
				sum(m.ext_demandrate_max[c] * ext_co.loc[c]['demand-rate']\
					for c in m.co_ext_in )
					
		# Costs for process fee
		elif cost_type == 'Process fee':
				return m.costs[cost_type] == \
					sum(m.proclass_e_in[procl] * process_class.loc[procl]['fee']\
						for procl in m.proclass_tuples\
						if process_class.loc[procl]['Direction']=='In'\
						if process_class.loc[procl]['fee']>0)/year_factor\
					+sum(m.proclass_e_out[procl] * process_class.loc[procl]['fee']
						for procl in m.proclass_tuples\
						if process_class.loc[procl]['Direction']=='Out'\
						if process_class.loc[procl]['fee']>0)/year_factor
		# Costs for process subsidies
		elif cost_type == 'Pro subsidy':
				return m.costs[cost_type] == \
					sum(m.proclass_e_in[procl] * process_class.loc[procl]['fee']\
						for procl in m.proclass_tuples\
						if process_class.loc[procl]['Direction']=='In'\
						if process_class.loc[procl]['fee']<0)/year_factor\
					+sum(m.proclass_e_out[procl] * process_class.loc[procl]['fee']
						for procl in m.proclass_tuples\
						if process_class.loc[procl]['Direction']=='Out'\
						if process_class.loc[procl]['fee']<0)/year_factor			
		else:
			raise NotImplementedError("Unknown cost type!")					
	m.cost_sum = pyen.Constraint(
		m.cost_type,
		rule=cost_sum_rule,
		doc='Calculate Costs per cost type')
		
	#OBJECTIVE	
	def obj_rule(m):
	# Return sum of total costs over all cost types.
	# Simply calculates the sum of m.costs over all m.cost_types.
		return pyen.summation(m.costs)		
	m.obj = pyen.Objective(
		sense=pyen.minimize,
		rule=obj_rule,
		doc='Sum costs by cost type')	
			
	return m
			   
"""Help Functions"""

def commodity_balance(m, co, t):
# Calculate commodity balance at given timestep.
# TO factory Grid = USED Energy = NEGATIVE - (process-out; storage-out, ext_in..)
# FROM factory Grid = provided Energy = POSITIVE + (process-in; storage-in, ext_out, demand..)
	
	balance = 0

	if co in m.co_demand:
		# demand increases balance
		balance += m.demand.loc[t][co]			
	for p in m.pro_input_tuples:
		if co in p:
			#usage as input for process increases balance
			balance += m.pro_p_in[p,t]	
			if co in m.co_supim:
				balance -= m.pro_p_in[p,t] # commodities in supim do not count for balance
	for p in m.pro_output_tuples:
		if co in p:
		# output from processes decreases balance
			balance -= m.pro_p_out[p,t]			
	if co in m.co_ext_in:
		# additional external import decreases balance
		balance -= m.ext_p_in[co,t]	
	if co in m.co_ext_out:
		# external export in increases balance
		balance += m.ext_p_out[co,t]	     			
	for s in m.sto_tuples:
        # usage as input for storage increases consumption
        # output from storage decreases consumption
		if co in s:
			balance += m.sto_p_in[s,t]
			balance -= m.sto_p_out[s,t]
	return balance

def energy_consumption(m, co):
# Calculate energy consumption of each commodity
# sum up demand + process in puts + storage losses over tim 
	
	consumption = 0

	if co in m.co_demand:
		# demand increases consumption
		consumption += sum(m.demand.loc[t][co] for t in m.t)					
	for p in m.pro_input_tuples:
		if co in p:
		# input processes 
			consumption += sum(m.pro_p_in[p,t] for t in m.t)		     			
	for s in m.sto_tuples:
        # usage as input for storage increases consumption
        # output from storage decreases consumption
		if co in s:
			consumption += sum(m.sto_p_in[s,t] for t in m.t)
			consumption -= sum(m.sto_p_out[s,t] for t in m.t)
	
	return consumption	

def energy_production(m, co):
# Calculate energy productio of each commodity
# sum up process outputs over time
	
	production = 0
				
	for p in m.pro_output_tuples:
		if co in p:
			production += sum(m.pro_p_out[p,t] for t in m.t)		     			
			
	return production

def annuity_factor(n, i):
# Calculate annuity factor from depreciation and interest.
# n: depreciation period (years)
# i: interest rate (percent, e.g. 0.06 means 6 %)
    return (1+i)**n * i / ((1+i)**n - 1)

def get_pro_inputs(process_commodity):
	#get commodities with direction "in" in process_commodity
	if process_commodity.index.values.size>0:
		inputs = tuple()
		input_tuples = process_commodity.xs('In',level='Direction').index.get_values()
		for i in range(0,input_tuples.size):
			inp = tuple([input_tuples[i][2]])
			inputs = inputs + inp
		
		inputs = pd.Index(set(inputs))
	else:
		inputs = pd.Index([])
	return inputs
	
def get_pro_outputs(process_commodity):
	#get commodities with direction "out" in process_commodity
	if process_commodity.index.values.size>0:
		outputs = tuple()
		output_tuples = process_commodity.xs('Out',level='Direction').index.get_values()
		for i in range(0,output_tuples.size):
			outp = tuple([output_tuples[i][2]])
			outputs = outputs + outp
		
		outputs = pd.Index(set(outputs))
	else:
		outputs = pd.Index([])
	return outputs	
	
############################################################################################	
#DATA PREPARE
############################################################################################	
	
def read_xlsdata(input_file):
# read sheets of excel file and put them in one dictionary xls_data
	xls = pd.ExcelFile(input_file) # read excel file
	
	xls_data = {} # create dictionary
	
	xls_data.update({'input_file' : input_file})
	xls_data.update({'time-settings' : xls.parse('Time-Settings', index_col=[0]) })
	xls_data.update({'mip-equations' : xls.parse('MIP-Equations', index_col=[0]) })
	xls_data.update({'ext-co' : xls.parse('Ext-Commodities', index_col=[0]) })
	xls_data.update({'ext_import' : xls.parse('Ext-Import', index_col=[0]) })
	xls_data.update({'ext_export' : xls.parse('Ext-Export', index_col=[0]) })
	xls_data.update({'demandrate_factor' : xls.parse('Demand-Rate-Factor', index_col=[0]) })
	xls_data.update({'process' : xls.parse('Process', index_col=[0]) })
	xls_data.update({'process_commodity' : xls.parse('Process-Commodity', index_col=[0,1,2]) })
	xls_data.update({'process_class' : xls.parse('Process-Class', index_col=[0,1]) })
	xls_data.update({'storage' : xls.parse('Storage', index_col=[0,1]) })
	xls_data.update({'demand' : xls.parse('Demand', index_col=[0]) })
	xls_data.update({'supim' : xls.parse('SupIm', index_col=[0]) })
	
	return xls_data

def prepare_modeldata(xls_data):
#prepare data for model
		
	data=xls_data
	
	#process: add/delete rows dependent on "num" index
	data.update({'process' : num_index(xls_data['process'])})
	
	#process_commodity: delete columns not in 'process'
	data.update({'process_commodity' : del_processes(xls_data['process_commodity'],data['process'])})

	#storage: add/delete rows dependent on "num" index
	data.update({'storage' : num_index(xls_data['storage'])})
	
	#calculate abs max capacity
	data['process']['cap-abs-max'] = (data['process']['cap-installed'] + data['process']['cap-new-max'])
	
	#calculate initial mode run and start
	data['process']['initial-run'] = (data['process']['initial-power'] >= (data['process']['cap-installed'] * data['process']['partload-min'])) *1
	data['process']['initial-start'] = (data['process']['initial-power'] < data['process']['cap-installed'] * data['process']['partload-min']) & (data['process']['initial-power']>0) *1
	
	return data	

		
def num_index(df_data):
	#Create DataFrame"output" with additional rows dependent on new index 1 to "Num"
		
	# df_data = dataframe with data of sheet, index columns without num!!!	
	df_0 = df_data	#only index columns without num
	df_1 = df_data.set_index('Num',True,True) # add'num' to index columns	
	output=pd.DataFrame()	#empty Dataframe to be filled
	mxn=0
	for i in range(0,len(df_0.index),1): #for every index tuple
		maxnum = int(df_0.loc[df_0.index[i]]['Num'])
		mxn=max(mxn,maxnum)
		for n in range(1,maxnum+1,1): #from 1 to "Num" 			
			if len(df_0.index.names)==1:  #only one index column
				newindex=df_0.index[i]
				newindex=(newindex,n)
			else:					# more than one index columns
				newindex=list(df_0.index[i])
				newindex.append(n)
			newindex=tuple([newindex])
			values=df_1.ix[df_1.index[i]]
			values=np.matrix(values)
			df=pd.DataFrame(values,index=newindex,columns=df_1.columns) # new row
			output=output.append(df)		# add row to output
	if output.empty == False:	
		output.index=pd.MultiIndex.from_tuples(tuple(output.index), names=df_1.index.names) #adding multiindex and index names
		# derive annuity factor for process and storage
	else:
		output = df_1.ix[0:0]
		# output = pd.DataFrame(columns = df_data.columns[1:])
	output['annuity_factor'] = annuity_factor(output['depreciation'], output['wacc'])
	return output

def del_processes(process_commodity, process):
# Delete non used processes in process_commodity
	if process.index.values.size>0:
		pro_co=pd.DataFrame()
		pro_type = process.index.get_level_values(0)
		for i in range(0,len(process_commodity)):		
			if process_commodity[i:i+1].index[0][0] in pro_type:
				for n in range(0,max(process.loc[process_commodity.index[i][0]].index)):
					df_temp = pd.DataFrame(process_commodity[i:i+1].values, \
						index = [pd.Index(tuple([(process_commodity[i:i+1].index.get_values()[0][0], n+1, process_commodity[i:i+1].index.get_values()[0][1], process_commodity[i:i+1].index.get_values()[0][2])]))] )
					pro_co=pro_co.append(df_temp)
						
		pro_co.index=pd.MultiIndex.from_tuples(tuple(pro_co.index),names=process_commodity.index.names[0:1]+['Num'] +process_commodity.index.names[1:3])	
		pro_co.columns = process_commodity.columns
	else:
		pro_co=process_commodity.ix[0:0]

	return pro_co
	
############################################################################################	
#GET RESULTS	
############################################################################################

def get_entity(prob, name):
    """ Return a DataFrame for an entity in model instance.

    Args:
        prob: a Pyomo ConcreteModel instance
        name: name of a Set, Param, Var, Constraint or Objective

    Returns:
        a single-columned Pandas DataFrame with domain as index
    """

    # retrieve entity, its type and its onset names
    entity = prob.__getattribute__(name)
    labels = get_onset_names(entity)

    # extract values		
    if isinstance(entity, pyen.Set):
        # Pyomo sets don't have values, only elements
		
		if len(entity.value) == 0:
			results = 0
			return results
			
		else:
			results = pd.DataFrame([[v] for v in entity.value])
			# for unconstrained sets, the column label is identical to their index
			# hence, make index equal to entity name and append underscore to name
			# (=the later column title) to preserve identical index names for both
			# unconstrained supersets
			if not labels:
				labels = [name]
				name = name+'_'
			results.columns = [name]
			return results
		
			

    elif len(entity.items()) == 0:
		#entity is empty
		results = pd.DataFrame()
		return results
		
    elif isinstance(entity, pyen.Param):
        if entity.dim() > 1:
            results = pd.DataFrame([v[0]+(v[1],) for v in entity.iteritems()])
        else:
            results = pd.DataFrame(entity.iteritems())
	
	
    else:
        # create DataFrame
        if entity.dim() > 1:
            # concatenate index tuples with value if entity has
            # multidimensional indices v[0]
            results = pd.DataFrame(
                [v[0]+(v[1].value,) for v in entity.iteritems()])
        else:
            # otherwise, create tuple from scalar index v[0]
            results = pd.DataFrame(
                [(v[0], v[1].value) for v in entity.iteritems()])

    # check for duplicate onset names and append one to several "_" to make
    # them unique, e.g. ['sit', 'sit', 'com'] becomes ['sit', 'sit_', 'com']
    for k, label in enumerate(labels):
        if label in labels[:k]:
            labels[k] = labels[k] + "_"

    # name columns according to labels + entity name
    results.columns = labels + [name]
    results.set_index(labels, inplace=True)

    return results
	
def get_entities(prob, names):
    """ Return one DataFrame with entities in columns and a common index.

    Works only on entities that share a common domain (set or set_tuple), which
    is used as index of the returned DataFrame.

    Args:
        prob: a Pyomo ConcreteModel instance
        names: list of entity names (as returned by list_entities)

    Returns:
        a Pandas DataFrame with entities as columns and domains as index
    """

    df = pd.DataFrame()
    for name in names:
        other = get_entity(prob, name)

        if df.empty:
            df = other
        else:
			index_names_before = df.index.names
			if not other.empty:
				df = df.join(other, how='outer')

			if index_names_before != df.index.names:
				df.index.names = index_names_before

    return df


def list_entities(prob, entity_type):
    """ Return list of sets, params, variables, constraints or objectives

    Args:
        prob: a Pyomo ConcreteModel object
        entity_type: "set", "par", "var", "con" or "obj"

    Returns:
        DataFrame of entities

    Example:
        >>> data = read_excel('data-example.xlsx')
        >>> model = create_model(data, range(1,25))
        >>> list_entities(model, 'obj')  #doctest: +NORMALIZE_WHITESPACE
                                         Description Domain
        Name
        obj   minimize(cost = sum of all cost types)     []
        [1 rows x 2 columns]

    """

    iter_entities = prob.__dict__.iteritems()

    if entity_type == 'set':
        entities = sorted(
            (x, y.doc, get_onset_names(y)) for (x, y) in iter_entities
            if isinstance(y, pyen.Set) and not y.virtual)

    elif entity_type == 'par':
        entities = sorted(
            (x, y.doc, get_onset_names(y)) for (x, y) in iter_entities
            if isinstance(y, pyen.Param))

    elif entity_type == 'var':
        entities = sorted(
            (x, y.doc, get_onset_names(y)) for (x, y) in iter_entities
            if isinstance(y, pyen.Var))

    elif entity_type == 'con':
        entities = sorted(
            (x, y.doc, get_onset_names(y)) for (x, y) in iter_entities
            if isinstance(y, pyen.Constraint))

    elif entity_type == 'obj':
        entities = sorted(
            (x, y.doc, get_onset_names(y)) for (x, y) in iter_entities
            if isinstance(y, pyen.Objective))

    else:
        raise ValueError("Unknown parameter entity_type")

    entities = pd.DataFrame(entities,
                            columns=['Name', 'Description', 'Domain'])
    entities.set_index('Name', inplace=True)
    return entities


def get_onset_names(entity):
    """
        Example:
            >>> data = read_excel('data-example.xlsx')
            >>> model = create_model(data, range(1,25))
            >>> get_onset_names(model.e_co_stock)
            ['t', 'sit', 'com', 'com_type']
    """
    # get column titles for entities from domain set names
    labels = []

    if isinstance(entity, pyen.Set):
        if entity.dimen > 1:
            # N-dimensional set tuples, possibly with nested set tuples within
            if isinstance(entity.domain, pyen.base.sets._SetProduct):
                domains = entity.domain.set_tuple
            else:
                domains = entity.set_tuple

            for domain_set in domains:
                labels.extend(get_onset_names(domain_set))

        elif entity.dimen == 1:
            if entity.domain:
                # 1D subset; add domain name
                labels.append(entity.domain.name)
            else:
                # unrestricted set; add entity name
                labels.append(entity.name)
        else:
            # no domain, so no labels needed
            pass

    elif isinstance(entity, (pyen.Param, pyen.Var, pyen.Constraint,
                    pyen.Objective)):
        if entity.dim() > 0 and entity._index:
            labels = get_onset_names(entity._index)
        else:
            # zero dimensions, so no onset labels
            pass

    else:
        raise ValueError("Unknown entity type!")

    return labels
	
def get_constants(prob):
	"""Return summary DataFrames for important variables

	Usage:
		costs, cpro, csto = get_constants(prob)

	Args:
		prob: a ficus model instance
		
	Returns:
		costs, cpro, csto)
	"""
	costs = get_entity(prob, 'costs')
	cpro = get_entities(prob, ['pro_cap', 'pro_cap_new'])
	csto = get_entities(prob, ['sto_cap_p', 'sto_cap_p_new','sto_cap_e', 'sto_cap_e_new'])
   
    # better labels
	# if not cpro.empty:
		# cpro.columns = ['Total', 'New']
	# if not csto.empty:
		# csto.columns = ['C Total', 'C New', 'P Total', 'P New']

    
	return costs, cpro, csto

def get_timeseries(prob, timesteps=None):
	"""Return DataFrames of all timeseries referring to given commodity

	Usage:
		demand, ext, pro, sto = get_timeseries(prob)

	Args:
		prob: a picus model instance
		timesteps: optional list of timesteps, defaults to modelled timesteps
		
	Returns:
		demand: timeseries of all demands
		ext: timeseries of all external in and outputs
		pro: timeseries of all process inputs and outputs
		sto: timeseries of all stotage inputs, outputs and energy contents
	"""
	if timesteps is None:
        # default to all simulated timesteps
		timesteps = sorted(get_entity(prob, 't')['t'])
        
    # DEMAND
	demand = prob.demand.loc[timesteps]
	demand.name = 'Demand'
    
    # EXT
	ext = get_entities(prob, ['ext_p_in','ext_p_out'])
	ext.name = 'Ext'

    # PROCESS
	pro = get_entities(prob, ['pro_p_in', 'pro_p_out'])

    # STORAGE
	sto = get_entities(prob, ['sto_e_cont','sto_p_in', 'sto_p_out'])
    
	return demand, ext, pro, sto

############################################################################################	
#SAVE RESULTS
############################################################################################

def prepare_result_directory(result_folder,result_name):
	""" create a time stamped directory within the result folder 
		
	Args:
		result_folder: directory in which the new dir is created
		result_name: name of created result_dir

	Returns:
		result_dir: time stamped directory ("name-TIMESTAMP")

	"""
	
	from datetime import datetime
	
	# timestamp for result directory
	now = datetime.now().strftime('%Y%m%dT%H%M')

	# create result directory if not existent
	result_dir = os.path.join(result_folder, '{}-{}'.format(result_name, now))
	if not os.path.exists(result_dir):
		os.makedirs(result_dir)

	return result_dir
	
def report(prob, dir):
	from datetime import datetime
	"""Write result summary to a spreadsheet file in dir

	Args:
		prob: a picus model instance
		dir: directory, where Report File will be saved
	Returns:
		resultfile: Path of Resultfile
	"""
	print 'Save Results to Reportfile...\n'
	t0 = time.time()
	
	# Create Name of Resultfile
	inputfilename = os.path.splitext(os.path.split(prob.inputfile)[1])[0]
	now = datetime.now().strftime('%Y%m%dT%H%M')
	resultfile = os.path.join(dir, 'result-{}-{}.xlsx'.format(inputfilename, now))
	writer = pd.ExcelWriter(resultfile)


	#Create Information sheet
	info = pd.DataFrame(index = ['Date', 'Input File Name','timebase' ], columns = ['Data'])
	info.loc['Date']['Data'] = time.asctime()
	info.loc['Input File Name']['Data'] = prob.inputfile
	info.loc['timebase']['Data'] = prob.tb

	# get the data
	costs, cpro, csto = get_constants(prob)
	demand, ext, pro, sto = get_timeseries(prob)

	# write to excel
	info.to_excel(writer, 'Info', merge_cells = False)
	costs.to_excel(writer, 'Costs', merge_cells = False)
	cpro.to_excel(writer, 'Process caps', merge_cells = False)
	csto.to_excel(writer, 'Storage caps', merge_cells = False)
	ext.to_excel(writer, 'External timeseries', merge_cells = False)
	pro.to_excel(writer, 'Process timeseries', merge_cells = False)
	sto.to_excel(writer, 'Storage timeseries', merge_cells = False)
	demand.to_excel(writer, 'Demand timeseries', merge_cells = False)
		
	writer.save() #save

	print 'Results Saved. time: '+"{:.1f}".format(time.time()-t0)+' s\n'
	
	return resultfile
	
def result_figures(dir, prob = None, resultfile = None, timesteps = None, fontsize=16, show=False):
	"""Create all plots for given instance/resultfile and save to dir

	Args:
		dir: directory, where the plots are saved
		prob: a ficus model instance
		resultfile: a stored ficus resultfile
		fontsize: fontsize for labels/legend in figure
		
	"""
	import matplotlib.pyplot as plt
	import matplotlib as mpl	
	plt.ion()
	
	#Get demand commodities from instance or resultfile
	if prob:
		if resultfile:
			raise NotImplementedError('please specify EITHER "prob" or "resultfile"!')	
		else:
			commodities = prob.demand.columns
	elif resultfile:
		commodities = pd.ExcelFile(resultfile).parse('Demand timeseries',index_col=[0]).columns
	else:
		raise NotImplementedError('please specify either "prob" or "resultfile"!')

	
	for co in commodities:
		#plot and save timeseries for every commodity in demand
		fig = plot_timeseries(	co,\
								prob = prob, resultfile = resultfile,\
								timesteps=timesteps,fontsize=fontsize,show=show)
		fig.savefig(dir + '\\'+co+'-timeseries.png')
		if not show:
			plt.close(fig)
		
		#plot and save energy balance for every commodity in demand
		fig = plot_energy(	co,\
								prob = prob, resultfile = resultfile,\
								timesteps=timesteps,fontsize=fontsize,show=show)
		fig.savefig(dir + '\\'+co+'-energy.png')
		if not show:
			plt.close(fig)
	
	#plot and save installed and new capacities of processes and storages
	fig = plot_cap(prob = prob, resultfile = resultfile, fontsize=fontsize,show=show)
	fig.savefig(dir + '\\capacities.png')
	if not show:
		plt.close(fig)
	
	#plot and save costs
	fig = plot_costs(prob = prob, resultfile = resultfile, fontsize=fontsize,show=show)
	fig.savefig(dir + '\\costs.png')
	if not show:
		plt.close(fig)
	
	return 

############################################################################################	
#PLOT	
############################################################################################

COLOURS = {
    0: 'lightsteelblue',
    1: 'cornflowerblue',
    2: 'royalblue',
    3: 'lightgreen',   
    4: 'salmon',
    5: 'mediumseagreen',
    6: 'orchid', 
    7: 'burlywood',
    8: 'palegoldenrod', 
    9: 'sage', 
    10: 'lightskyblue', 
    11: 'firebrick',
    12: 'blue',
	13: 'darkgreen'}

	
def get_plot_data(co, prob, resultfile, timesteps):
	"""Get Result Data for plotting

	Reads data either from given instance or given resultfile and prepares data for plotting

	Args:
		co: commodity to plot
		prob: a ficus model instance
		resultfile: a stored ficus resultfile
		timesteps: list of modelled timesteps to plot 
	
	Returns:
		demand: demand timeseries
		ext: external timeseries
		pro: process timeseries
		sto: storage timeseries
		timesteps: timesteps
		tb: timebase of data
		created: timeseries of commodity produced/imported 
		consumed: timeseries of commodity consumed/exported 
		storage: timeseries of commodity stored
		colours: colours for elements in created/consumed
	"""
	if (prob is None) and (resultfile is None):
		#either prob or resultfile must be given
		raise NotImplementedError('please specify either "prob" or "resultfile"!')
	elif (prob is not None) and (resultfile is not None):
		#either prob or resultfile must be given
		raise NotImplementedError('please specify EITHER "prob" or "resultfile"!')	
	elif resultfile is None:
		# prob is given, get timeseries from prob
		if timesteps is None:
		# default to all simulated timesteps
			timesteps = sorted(get_entity(prob, 't')['t'])
		demand, ext, pro, sto = get_timeseries(prob,timesteps)
		tb = prob.tb		
	else:
		# resultfile is given, get timeseries from resultfile
		xls = pd.ExcelFile(resultfile) # read resultfile
		if timesteps is None:
		# default to all simulated timesteps
			timesteps = sorted( xls.parse('Demand timeseries', index_col = [0]).index)
		
		#read demand sheet and reduce to timesteps
		demand = xls.parse('Demand timeseries', index_col = [0]).loc[timesteps]
		
		#read External timeseries sheet and reduce to timesteps
		ext = xls.parse('External timeseries', index_col = [0,1])
		indexer = [ slice(None) ] * len(ext.index.levels)
		indexer[ext.index.names.index('t0')] = timesteps
		ext = ext.loc[tuple(indexer),:]
		
		#read Process timeseries sheet and reduce to timesteps
		try :
			pro = xls.parse('Process timeseries', index_col = [0,1,2,3])
		except ValueError:
			pro = xls.parse('Process timeseries', index_col = [0])
		indexer = [ slice(None) ] * len(pro.index.levels)
		indexer[pro.index.names.index('t0')] = timesteps
		pro = pro.loc[tuple(indexer),:]
		
		#read Storage timeseries sheet and reduce to timesteps
		sto = xls.parse('Storage timeseries', index_col = [0,1,2,3])
		indexer = [ slice(None) ] * len(sto.index.levels)
		indexer[sto.index.names.index('t0')] = timesteps
		sto = sto.loc[tuple(indexer),:]
		
		#read timebase
		tb = xls.parse('Info', index_col = [0]).loc['timebase'].values[0]
	
	##Prepare Data##
	##############		
	
	timesteps = np.array(timesteps) # make array for xticks
		
	#Demand Timeseries for co
	try:
		demand = demand[co]
	except KeyError:
		demand = pd.Series(0,index=timesteps)
	
	#sum identical processes/ 
	try:
		sto = sto.groupby(level=['storage_name','commodity','t0']).sum()
		sto_names = sto.index.levels[0]
	except ValueError:
		sto_names = ['']
	try:
		pro = pro.groupby(level=['pro_name','commodity','t0']).sum()
		pro_names = pro.index.levels[0]
	except ValueError:
		pro_names = ['']
	prosto_names = pro_names|sto_names

	
	#Timeseries of all created/consumed/storage
	try:		
		created = pd.DataFrame(ext.xs(co, level='commodity')['ext_p_in'])
		created.rename(columns={'ext_p_in':'Import'}, inplace=True)
	except (KeyError, AttributeError):
		created = pd.DataFrame(index=timesteps)
	try:
		created = created.join(pro.xs(co, level='commodity')['pro_p_out'].unstack(['pro_name']))
	except (KeyError, AttributeError):
		created = created
	try:
		created = created.join(sto.xs(co, level='commodity')['sto_p_out'].unstack(['storage_name']))
	except (KeyError, AttributeError):
		created = created

	#Timeseries of all consumed/exported/stored 
	try:		
		consumed = pd.DataFrame(ext.xs(co, level='commodity')['ext_p_out'])
		consumed.rename(columns={'ext_p_out':'Export'}, inplace=True)
	except (KeyError, AttributeError):
		consumed = pd.DataFrame(index=timesteps)
	try:
		consumed = consumed.join(pro.xs(co, level='commodity')['pro_p_in'].unstack(['pro_name']))
	except (KeyError, AttributeError):
		consumed = consumed
	try:
		consumed = consumed.join(sto.xs(co, level='commodity')['sto_p_in'].unstack(['storage_name']))
	except (KeyError, AttributeError):
		consumed = consumed
	
	#Storage Energy Content
	try:
		storage = pd.DataFrame(index=timesteps)
		storage = storage.join(sto.xs(co, level='commodity')['sto_e_cont'].unstack(['storage_name']))
	except (KeyError, AttributeError):
		storage = pd.DataFrame(index=timesteps)
	
	# remove all columns from created which are all-zeros in both created and 
	# consumed (except the last one, to prevent a completely empty frame)
	for col in created.columns:
		if ((not created[col].any()) or (created[col].isnull().sum() == created[col].size) \
		or (created[col].max()<1e-1)):# and len(created.columns) > 1:
			created.pop(col)
			try:
				storage.pop(col)
			except KeyError:
				storage = storage
	# set all columns fron consumed to zero, which are nan
	for col in consumed.columns:
		if ((not consumed[col].any()) or (consumed[col].isnull().sum() == consumed[col].size) \
		or (consumed[col].max()<1e-1)):#and len(consumed.columns) > 1:
			consumed.pop(col)
	
	##ASSIGN COLOR##
	##############
	colours = {
    'Demand': COLOURS[0],
    'Import' : COLOURS[1],
    'Export' : COLOURS[2],
	'edgecolor': 'slategray'}
	
	for i,name in enumerate(prosto_names):
		colours.update({name : COLOURS[i+3]})
		
		
	return demand, ext, pro, sto, timesteps, tb, created, consumed, storage, colours
	
	
	
def plot_timeseries(co, prob = None, resultfile = None, timesteps=None,fontsize=16,show=True):
	"""Stacked timeseries of commodity balance 

	Creates a stackplot of the power balance of a given commodity, together
	with stored energy in a second subplot. 

	Args:
		co: commodity to plot
		prob: a ficus model instance
		resultfile: a stored ficus resultfile
		timesteps: optional list of modelled timesteps to plot
		fontsize: fontsize for labels/legend in figure
		
	Returns:
		fig: figure handle
	"""
	import matplotlib.pyplot as plt
	import matplotlib as mpl
	plt.ion()
	
	##Get Data and Prepare Data##
	##############
	demand, ext, pro, sto, timesteps, tb, created, consumed, storage, colours \
		= get_plot_data(co, prob, resultfile, timesteps)
	#change order
	try:
		imp = created['Import']
		created.pop('Import')
		created['Import'] = imp
	except KeyError:
		pass
	try:
		exp = consumed['Export']
		consumed.pop('Export')
		consumed['Export'] = exp
	except KeyError:
		pass

	
	##PLOT##
	##############		
	# FIGURE
	fig = plt.figure(figsize=(11,7))	
	if storage.empty:
		gs = mpl.gridspec.GridSpec(1, 2, width_ratios = [5,1])
	else:
		gs = mpl.gridspec.GridSpec(2, 2, height_ratios=[2, 1], width_ratios = [5,1])
	ax0 = plt.subplot(gs[0])	
	
	# Unfortunately, stackplot does not support multi-colored legends by itself.
	# Therefore, a so-called proxy artist - invisible objects that have the 
	# correct color for the legend entry - must be created. Here, Rectangle 
	# objects of size (0,0) are used. The technique is explained at 
	# http://stackoverflow.com/a/22984060/2375855
	proxy_artists = []
	
	# PLOT DEMAND
	dp = ax0.plot(step_edit_x(demand.index), step_edit_y(demand.values), linewidth=1.6, color='k')
	# Demand in Legend
	proxy_artists.append(mpl.lines.Line2D([0,0], [0,0], linewidth=2, color='k')) 
	legend_entries = ['Demand']
	
	# PLOT CREATED
	if not created.empty:
		sp_crtd = ax0.stackplot(step_edit_x(created.index), step_edit_y(created.as_matrix().T), linewidth=0.15)		
		for k, pro_sto in enumerate(created.columns):
			this_color = to_color(pro_sto,colours) #get color for pro or sto 			
			sp_crtd[k].set_facecolor(this_color) #set color of stackplot
			sp_crtd[k].set_edgecolor((.5,.5,.5))
			legend_entries.append(pro_sto)			
			proxy_artists.append(mpl.patches.Rectangle((0,0), 0,0, facecolor=this_color)) #add proxy artist for legend

	# PLOT CONSUMED
	if not consumed.empty:
		sp_csmd = ax0.stackplot(step_edit_x(consumed.index), step_edit_y(-consumed.as_matrix().T), linewidth=0.15)
		for k, pro_sto in enumerate(consumed.columns):
			this_color = to_color(pro_sto,colours) #get color for pro or sto 			
			sp_csmd[k].set_facecolor(this_color) #set color of stackplot
			sp_csmd[k].set_edgecolor((.5,.5,.5))
			if pro_sto not in (legend_entries):
				legend_entries.append(pro_sto)
				proxy_artists.append(mpl.patches.Rectangle((0,0), 0,0, facecolor=this_color)) #add proxy artist for legend


	# PLOT STORAGE
	if not storage.empty:
		ax1 = plt.subplot(gs[2], sharex=ax0)
		sp_sto = ax1.stackplot(step_edit_x(storage.index), step_edit_y(storage.as_matrix().T), linewidth=0.15)
		#color
		for k, sto in enumerate(storage.columns):
			this_color = to_color(sto,colours) #get color for sto 			
			sp_sto[k].set_facecolor(this_color) #set color of stackplot
			sp_sto[k].set_edgecolor((.5,.5,.5))	

		# labels
		ax1.set_ylabel('Energy (kWh)',fontsize=fontsize)
		axes = [ax0, ax1]
	else:
		axes = [ax0] 

	
	##LEGEND##
	##############
		
	lg = ax0.legend(proxy_artists, 
					legend_entries,
					frameon=False,
					ncol=1,
					loc = 2, 
					bbox_to_anchor = (1.0, 0.5),
					borderaxespad=0.,
					fontsize=fontsize-2)
	
	ax0.set_title('Power balance of commodity {}'.format(co),fontsize=fontsize)
	ax0.set_ylabel('Power (kW)',fontsize=fontsize)
	for ax in axes:
		ax.set_frame_on(True)
		ax.set_xlim((timesteps[0], timesteps[-1]))
		ax.set_ylim(np.array(ax.get_ylim())*1.05)
		ax.grid()
		ax.tick_params(labelsize=fontsize-2)
		# group 1,000,000 with commas
		group_thousands = mpl.ticker.FuncFormatter(
			lambda x, pos: '{:0,d}'.format(int(x)))
		ax.yaxis.set_major_formatter(group_thousands)
		
		if ax == axes[-1]:
			ax.set_xlabel('Time in year (h)', fontsize=fontsize)
			# ax.set_xticklabels(ax.get_xticks()/4)
			group_thousandsx = mpl.ticker.FuncFormatter(
			lambda x, pos: '{:0,d}'.format(int(x/4)))
			ax.xaxis.set_major_formatter(group_thousandsx)
		else:
			plt.setp(ax.get_xticklabels(), visible=False)
	
	
	fig.tight_layout()
	if show:
		plt.show(block=False)
	return fig
	
def plot_energy(co, prob = None, resultfile = None, timesteps=None,fontsize=16,show=True):
	"""Energy Balance

	Creates a barplot with two subplots of produced/imported and consumed/imported energy balance for
	commodity "co"

	Args:
		co: commodity to plot
		prob: a ficus model instance
		resultfile: a stored ficus resultfile
		timesteps: optional list of modelled timesteps to plot 
		fontsize: fontsize for labels/legend in figure
		
	Returns:
		fig: figure handle
	"""

	import matplotlib.pyplot as plt
	import matplotlib as mpl
	plt.ion()
	
	##Get Data and Prepare Data##
	##############
	demand, ext, pro, sto, timesteps, tb, created, consumed, storage, colours \
		= get_plot_data(co, prob, resultfile, timesteps)
	
	consumed.insert(0,'Demand',demand) # add demand to consumed
	
	#calculate total energy in kWh
	consumed_e = consumed.sum() * tb /3600.0
	created_e = created.sum() * tb /3600.0
	
	#calculate storage losses
	sto_loss = consumed_e-created_e
	sto_loss = sto_loss[sto_loss.notnull()]

	#remove storage energy from consumed/created 
	for idx in sto_loss.index.values:
		consumed_e.pop(idx)
		created_e.pop(idx)
		
	#remove empty objects from storage losses
	sto_loss = sto_loss[sto_loss>1e-1]
	
	#add storage losses to consumed	
	consumed_e = pd.concat([consumed_e,sto_loss])
	
	
	
	##PLOT##
	##############		
	# FIGURE
	fig = plt.figure(figsize=(11,7))
	gs = mpl.gridspec.GridSpec(2, 2, height_ratios=[0.01,10])
	fig.suptitle('Energy balance of commodity {}'.format(co),fontsize=fontsize)
		
	#PLOT CREATED
	ax0 = plt.subplot(gs[2])
	bottom=0
	for i,idx in enumerate(created_e.index):
		ax0.bar(1,created_e[idx],color=colours[idx],bottom = bottom, label = idx,align='center')
		bottom += created_e[idx] 
	ax0.set_xlabel('produced/imported Energy', fontsize=fontsize)
	ax0.legend(	loc="upper right",
				fontsize=fontsize-2,
				numpoints = 1)
	handles, labels = ax0.get_legend_handles_labels()
	ax0.legend(handles[::-1], labels[::-1]) # reverse the order
	ax0.set_ylabel('Energy (kWh)', fontsize=fontsize)
	
	#PLOT CONSUMED
	ax1 = plt.subplot(gs[3],sharey=ax0)	
	bottom=0
	for i,idx in enumerate(consumed_e.index):
		ax1.bar(1,consumed_e[idx],color=colours[idx],bottom = bottom,label = idx,align='center')
		bottom += consumed_e[idx]
	ax1.set_xlabel('consumed/exported Energy',fontsize=fontsize)
	ax1.legend(	loc="upper right",
				fontsize=fontsize-2,
				numpoints = 1)
	handles, labels = ax1.get_legend_handles_labels()
	ax1.legend(handles[::-1], labels[::-1]) # reverse the order
	plt.setp(ax1.get_yticklabels(), visible=False)


	##AXES Properties##
	##############	
	axes = [ax0, ax1]
	for ax in axes:
		ax.grid(axis='y')
		ax.set_xlim(0.55,2.1)
		ax.tick_params(labelsize=fontsize-2)
		plt.setp(ax.get_xticklabels(), visible=False)
		ax.xaxis.set_tick_params(size=0)
		# group 1,000,000 with commas
		group_thousands = mpl.ticker.FuncFormatter(
			lambda x, pos: '{:0,d}'.format(int(x)))
		ax.yaxis.set_major_formatter(group_thousands)
	ax0.set_ylim(0,created_e.sum()*1.1)
		
	fig.tight_layout()
	if show:
		plt.show(block=False)
	return fig	
		
def plot_cap(prob = None, resultfile = None,fontsize=16,show=True):
	"""Process and storage capacities

	Creates a horizontal barplot of the new and installed capacities of processes and storages

	Args:
		prob: a ficus model instance
		resultfile: a stored ficus resultfile
		fontsize: fontsize for labels/legend in figure
		
	Returns:
		fig: figure handle
	"""
	import matplotlib.pyplot as plt
	import matplotlib as mpl
	plt.ion()
	
	##Get Data and Prepare Data##
	##############
	
	# Read either form given instance or saved resultfile
	if (prob is None) and (resultfile is None):
		#either prob or resultfile must be given
		raise NotImplementedError('please specify either "prob" or "resultfile"!')
	elif (prob is not None) and (resultfile is not None):
		#either prob or resultfile must be given
		raise NotImplementedError('please specify EITHER "prob" or "resultfile"!')	
	elif resultfile is None:
		# prob is given, get timeseries from prob
		costs, cpro, csto = get_constants(prob)
	else:
		# resultfile is given, get timeseries from resultfile
		xls = pd.ExcelFile(resultfile) # read resultfile
		cpro = xls.parse('Process caps', index_col=[0,1])
		csto = xls.parse('Storage caps', index_col=[0,1,2])

	
	#delete index with zero capacity	
	try:
		csto = csto.groupby(level=['storage_name']).sum()
		csto = csto[csto['sto_cap_e'] > 1e-1]
	except ValueError:
		pass
	try:
		cpro = cpro.groupby(level=['pro_name']).sum()
		cpro = cpro[cpro['pro_cap'] > 1e-1]
	except ValueError:
		pass
	
	##PLOT##
	##############		
	# FIGURE
	fig = plt.figure(figsize=(11,7))	
	if csto.empty:
		gs = mpl.gridspec.GridSpec(1, 1)
	else:
		height_ratio = [cpro.index.size, csto.index.size]
		gs = mpl.gridspec.GridSpec(2, 2, height_ratios=height_ratio)
	
	#PLOT PROCESS
	ax0 = plt.subplot(gs[0])
	yticks = np.arange(len(cpro))
	ax0.barh(yticks,cpro['pro_cap']-cpro['pro_cap_new'],color=COLOURS[1],align='center')
	ax0.barh(yticks,cpro['pro_cap_new'],\
			left=cpro['pro_cap']-cpro['pro_cap_new'],color=COLOURS[3],align='center')
	ax0.set_yticks(yticks)
	ax0.set_yticklabels(cpro.index)
	axes = [ax0]
	

	if csto.empty:
	#If no storage exists, only show process capacities
		ax0.set_xlabel('Power Capacity (kW)', fontsize=fontsize)
		ax0.set_xticks(ax0.get_xticks()[::2])
		ax0.set_xlim(0,ax0.get_xlim()[1]*1.1)
		loc = 'upper right'
	else:
	#PLOT STORAGE
		#Plot Power Capacities
		ax2 = plt.subplot(gs[2],sharex=ax0)
		yticks = np.arange(len(csto))
		ax2.barh(yticks,csto['sto_cap_p']-csto['sto_cap_p_new'],color=COLOURS[1],align='center')
		ax2.barh(yticks,csto['sto_cap_p_new'],\
				left=csto['sto_cap_p']-csto['sto_cap_p_new'],color=COLOURS[3],align='center')
		ax2.set_yticks(yticks)
		ax2.set_yticklabels(csto.index)
		ax2.set_xlabel('Power Capacity (kW)', fontsize=fontsize)
		ax2.set_xticks(ax2.get_xticks()[::2])
		ax2.set_xlim(0,ax2.get_xlim()[1]*1.1)
		axes.append(ax2)
		
		#Plot Energy Capacities
		ax3 = plt.subplot(gs[3])
		ax3.barh(yticks,csto['sto_cap_e']-csto['sto_cap_e_new'],color=COLOURS[1],align='center')
		ax3.barh(yticks,csto['sto_cap_e_new'],\
				left=csto['sto_cap_e']-csto['sto_cap_e_new'],color=COLOURS[3],align='center')
		ax3.set_yticks(yticks)
		ax3.set_yticklabels([],visible=False)
		ax3.set_xlabel('Energy Capacity (kWh)', fontsize=fontsize)		
		ax3.set_xticks(ax3.get_xticks()[::2])
		ax3.set_xlim(0,ax3.get_xlim()[1]*1.1)
		axes.append(ax3)

		plt.setp(ax0.get_xticklabels(), visible=False)
		loc = 'upper left'
		
	##AXES Properties##
	##############	
	for ax in axes:
		ax.grid()
		ax.set_ylim(ax.get_yticks()[0]-0.5,ax.get_yticks()[-1]+0.5)
		ax.tick_params(labelsize=fontsize-2)
		# group 1,000,000 with commas
		group_thousands = mpl.ticker.FuncFormatter(
			lambda x, pos: '{:0,d}'.format(int(x)))
		ax.xaxis.set_major_formatter(group_thousands)

	##LEGEND##
	##############
	
	ax0.plot([],[],color = COLOURS[1], linestyle='None', marker='s', label='Installed',markersize=12)
	ax0.plot([],[],color = COLOURS[3], linestyle='None', marker='s', label='New',markersize=12)
	lg = ax0.legend(frameon=False,
					ncol=1,
					loc = loc, 
					bbox_to_anchor = (1.0, 0.5),
					borderaxespad=0.,
					fontsize=fontsize-2,
					numpoints = 1)

	fig.tight_layout()
	if show:
		plt.show(block=False)
	
	return fig

	
def plot_costs(prob = None, resultfile = None, fontsize=16,show=True):
	"""Costs

	Creates a barplot with three subplots of expenses, revenues and total costs

	Args:
		prob: a ficus model instance
		resultfile: a stored ficus resultfile
		fontsize: fontsize for labels/legend in figure
	
	Returns:
		fig: figure handle
	"""
	import matplotlib.pyplot as plt
	import matplotlib as mpl
	plt.ion()
	
	colours = {
    'Import' : COLOURS[1],
	'Export' : COLOURS[2],
	'Demand charges' : COLOURS[10],
	'Invest' : COLOURS[4],
	'Var costs' : COLOURS[3],
	'Fix costs' : COLOURS[5],
	'Process fee' : COLOURS[7],
	'Pro subsidy' : COLOURS[8],
	'total' : 'steelblue'}
	order = ['Import', 'Export','Demand charges','Invest','Fix costs', 'Var costs','Process fee','Pro subsidy']
	
	##Get Data and Prepare Data##
	##############
	if (prob is None) and (resultfile is None):
		#either prob or resultfile must be given
		raise NotImplementedError('please specify either "prob" or "resultfile"!')
	elif (prob) and (resultfile):
		#either prob or resultfile must be given
		raise NotImplementedError('please specify EITHER "prob" or "resultfile"!')	
	elif prob:
		# prob is given, get timeseries from prob
		costs, cpro, csto = get_constants(prob)
	else:
		# resultfile is given, get timeseries from resultfile
		xls = pd.ExcelFile(resultfile) # read resultfile
		costs = xls.parse('Costs', index_col=[0])
	
	#delete index with zero capacity	
	costs = costs['costs']
	costs = costs[costs!=0]
	
	
	##PLOT##
	##############		
	# FIGURE
	fig = plt.figure(figsize=(11,7))
	gs = mpl.gridspec.GridSpec(2, 3, height_ratios=[0.01,10], width_ratios = [2,2,1])
	fig.suptitle('Annual costs',fontsize=fontsize)
		
	ax0 = plt.subplot(gs[3])
	ax1 = plt.subplot(gs[4],sharey=ax0)
	ax2 = plt.subplot(gs[5],sharey=ax0)
	
	#Plot Expenses to ax0 and revenues to ax1
	bottom1=0
	bottom2=0
	for i,idx in enumerate(order):
		if idx not in costs.index:
			continue
		label = idx
		if idx == 'Demand charges':
			label = 'Demand\ncharges'
		if costs[idx] >0:
			ax0.bar(1,costs[idx],color=colours[idx],bottom = bottom1, label = label,align='center')
			bottom1 += costs[idx]
		elif costs[idx] <0:
			ax1.bar(1,-costs[idx],color=colours[idx],bottom = bottom2, label = label,align='center')
			bottom2 += -costs[idx]
			
	#Set ax0 properties and legend		
	ax0.set_xlabel('expenses', fontsize=fontsize)
	ax0.legend(	loc="upper right",
				fontsize=fontsize-2,
				numpoints = 1)
	handles, labels = ax0.get_legend_handles_labels()
	ax0.legend(handles[::-1], labels[::-1]) # reverse the order
	ax0.set_ylabel('Costs (Euro/a)', fontsize=fontsize-2)
	ax0.set_ylim(0,max(costs[costs>0].sum(),costs[costs<0].sum())*1.1)
	
	#Set ax1 properties and legend	
	ax1.set_xlabel('revenues',fontsize=fontsize)
	ax1.legend(	loc="upper right",
				fontsize=fontsize-2,
				numpoints = 1)
	handles, labels = ax1.get_legend_handles_labels()
	ax1.legend(handles[::-1], labels[::-1]) # reverse the order
	plt.setp(ax1.get_yticklabels(), visible=False)
	
	#Plot Total costs to ax2
	ax2.bar(1,costs.sum(),color=colours['total'],align='center')
	ax2.text(1,costs.sum()*1.02,'{:0,d}'.format(int(costs.sum())),color=colours['total'],fontsize = fontsize-2,ha='center')
	ax2.set_xlabel('total costs',fontsize=fontsize)
	plt.setp(ax2.get_yticklabels(), visible=False)
	
	##AXES Properties##
	##############	
	axes = [ax0, ax1, ax2]
	for ax in axes:
		ax.grid(axis='y')
		ax.set_xlim(0.55,2.45)
		ax.tick_params(labelsize=fontsize-2)
		plt.setp(ax.get_xticklabels(), visible=False)
		ax.xaxis.set_tick_params(size=0)
		# group 1,000,000 with commas
		group_thousands = mpl.ticker.FuncFormatter(
			lambda x, pos: '{:0,d}'.format(int(x)))
		ax.yaxis.set_major_formatter(group_thousands)
	ax2.set_xlim(0.55,1.45)	

	
	fig.tight_layout()
	if show:
		plt.show(block=False)
	return fig	
		
	
def to_color(obj,colours):
	"""Assign a named color to argument.

	If COLORS[obj] is set, return that. Otherwise, create a random color from
	matplotlib.colors.cnames

	Args:
		obj: any hashable object

	Returns:
		color: named color in matplotlib
	"""
	import random
	import matplotlib.colors as mpl_colors

	try:
		color = colours[obj]
	except KeyError:
		color=random.choice(mpl_colors.cnames.keys()) # random deterministic color
	return color
	
def step_edit_x(x):
	"""
	Edit array to be used as x-values for stacked step plot.
	1 2 3 4 5
	becomes
	1 2 2 3 3 4 4 5 5 6

	Args:
		x: array like
	Returns:
		X: edited array
	"""
	X=[]
	for i,ix in enumerate(x):
		if i==0:
			X.append(ix)
		elif i==len(x)-1:
			X.append(ix)
			X.append(ix)
			X.append(ix+1)
		else:
			X.append(ix)
			X.append(ix)
	return X

def step_edit_y(y):
	"""
	Edit 1D or 2D array to be used as y-values for stacked step plot.
	1 2 3 4
	5 6 7 8
	becomes
	1 1 2 2 3 3 4 4
	5 5 6 6 7 7 8 8

	Args:
		y: 1D or 2D numpy array
	Returns:
		Y: edited numpy array
	"""
	for k,yk in enumerate(y):
		Yk=[]
		if y.ndim==1:
			yk=y
		for i,iy in enumerate(yk):
			Yk.append(iy)
			Yk.append(iy)
		if k == 0:
			Y = np.array(Yk)
		else:
			Y = np.vstack([Y,np.array(Yk)])
		if y.ndim==1:
			break
	return Y

	
def install():
	"""
	Install not installed packages and copy "ficus.py" to the 'python27\Scripts' Folder
	"""
	import pip
	import shutil
	import sys
	import os
	
	#install pyomo
	try:
		import pyomo
	except ImportError:
		pip.main(['install', 'pyomo'])
	
	#copy "ficus.py" to pythons 'Scripts' Folder
	shutil.copy(os.path.join(os.path.dirname(os.path.realpath(__file__)),"ficus.py"),os.path.join(sys.exec_prefix,"Lib\\site-packages"))
	raw_input("Installed packages and copied ficus.py to "+os.path.join(sys.exec_prefix,"Lib\\site-packages")+"\nPress Enter to continue...\n")
	
# Example
if __name__ == '__main__':
	x = raw_input("\n\nInstall Pyomo and copy 'ficus.py' to the 'python27\Lib\site-packages' Folder (y/n)?\n")
	if x == 'y':
		print '\ninstalling...\n'
		install()
	else:
		print '\nInstallation aborted\n'
	
