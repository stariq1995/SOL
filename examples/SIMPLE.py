""" This script sets up and executes the optimization for SIMPLE [#c1]_


[#c1] Qazi, Z. et al. 2013. SIMPLE-fying Middlebox Policy Enforcement Using SDN. SIGCOMM (2013).
"""

if __name__ == '__main__':

	# Setup the basic config

	# Generate the formulation
	problem = generateFormulation(config)

	# Solve the formulation:
	problem.solve()

	# Get the solution
	
	# Put it on the network using OpenDaylight (mediocre implementation)