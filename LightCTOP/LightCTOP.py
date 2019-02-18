# -*- coding: utf-8 -*-
"""
Created on Sun May 06 17:13:11 2018

@author: Guodong
"""

from pulp import LpProblem, LpMinimize, LpVariable, lpSum, GUROBI, CPLEX, GLPK, value, LpStatus, solvers, XPRESS
import numpy as np
from time import time, gmtime, strftime, localtime
from IPython.utils import io
from Global_Variables import *

def LightCTOPModel( M, N, Q, Ti, PhiT, SigmaT, Sigma, Route_ID):
    """
    N          : Number of flights, N is a dictionary N[i] = # of TOSs for flight i
    Z          : Number of FCAs
    Q          : Q_ij cost of the route j of flight i, in minutes
    Ti         : #ETA at which route r_ij is planned to cross PCA c k, i is short for interval
    SigmaT     : A set of indices of the FCAs which flight f_i crosses at any route
    Phi        : Phi is a dictionary, Phi[k] is the set of indices of the routes which are planned to cross PCA k
    PhiT       : A set of indices of flights which might cross FCA c k at any of their routes
    M          : Capacity Constraints M[k][t]
    Solver     :
    
    Comments:
    The planning horizion, the exempted flights should always be carefully thought
    Objective function also considers the taxi in time
    """
    prob = LpProblem("LightCTOP", LpMinimize)
    M1         = 0
    M2         = 500
    
    deltaIndex = [ (i,j) for i in range( len(N) ) for j in range( N[i] ) ]
    delta      = LpVariable.dicts("delta", deltaIndex, cat="Binary")
    
    tauIndex   = [(i,k) for i in range( len(N) ) for k in FCAs if i in PhiT[k]]
    tau        = LpVariable.dicts("tau", tauIndex, lowBound=0., cat="Integer") 
    
    BIndex     = [(i,k,t) for i in range( len(N) ) for k in FCAs if i in PhiT[k] for t in TIME]
    B          = LpVariable.dicts("B", BIndex, cat="Binary")
    
    EIndex     = [(k,t) for t in TIME for k in FCAs]
    E          = LpVariable.dicts("E", EIndex, lowBound=0., cat="Integer") 
    
    """Define the objective function"""
    prob += lpSum( ( Q[i,j]*delta[i,j]  ) for (i,j) in deltaIndex ) + \
            lpSum( M2 * E[t,k] for (t,k) in EIndex )
    
    """Define the constraints"""
    for i in range( len(N) ):
        prob += lpSum( delta[i,j] for j in range( N[i] ) ) == 1 #only one route can be chosen
            
    """ETA Constraints"""
    for i in range( len(N) ):
        for k in SigmaT[i]:
            prob += tau[(i,k)] == lpSum( Ti[(i,j,k)]*delta[i,j] for j in range(N[i]) if k in Sigma[i,j] )
    
    """Two Constraints for B, See the paper"""
    for k in FCAs:
        for i in range( len(N) ):
            if i in PhiT[k]:
                prob += lpSum( B[i,k,t] for t in TIME  )  <= 1
                prob += lpSum( t*B[i,k,t] for t in TIME ) == tau[(i,k)] 
                # t must starts from 1!!
                # this constraint make sure flight will exit the PCA system 
    
    """Capacity Constraints"""
    for t in TIME:
        for k in FCAs:
            prob += lpSum( B[i,k,t] for i in range( len(N) ) if i in PhiT[k] ) <= M[k][t-1] + E[k,t]
    
    start = time()
    prob.solve(GUROBI())
    #prob.solve(CPLEX())
    #prob.solve(GLPK() )
    #prob.solve( solvers.PULP_CBC_CMD(fracGap=0.0001))
    end   = time()
    
    #for v in prob.variables():
    #    if v.varValue!=0:
    #        print(v.name, "=", v.varValue)

    print("Status:", LpStatus[prob.status])
    print('-' * 80)
    print "Solving this instance takes: %3.2f seconds"% (end - start)
    print "Optimal Objective Value    :", value(prob.objective)
    print "Total reroute cost         : %3d  miles" % sum( Q[i,j]*delta[i,j].varValue for (i,j) in deltaIndex )
    print('-' * 80)

    return (delta, B, E)







