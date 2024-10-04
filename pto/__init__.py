#### PTO user interface ####

# PTO has a layered architecture with each level building on the previous one.
# There are four access points to solve a problem at different levels. 
#  
# 1) core.core_run: manual names, coarse distributions
# 2) fine_distribution.run: manual names, fine distributions
# 3) automatic_name.name_run: manual or automatic names linear and structured 
#    with manual annotations, fine or coarse distributions
# 4) automatic_name.name_trans_run: manual or automatic names linear and structured
#    with automatic annotations, fine or coarse distributions
#
# The user of the package should access PTO from level 4 only, 
# which works as an interface to the package.

from pto.core import run, rnd

