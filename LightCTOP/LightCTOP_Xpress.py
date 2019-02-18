# -*- coding: utf-8 -*-
"""
Created on Sun May 06 17:13:11 2018

@author: Guodong
"""

import xpress as xp
import numpy as np
from time import time, gmtime, strftime, localtime
from IPython.utils import io
from Global_Variables import *

def LightCTOPModel( M, N, Q, Ti, PhiT, SigmaT, Sigma, Route_ID):
    """
    1 This function use Python Xpress packaged and optimize the weighted reroute cost and capcity violation cost
    2 In the later version, three objectives will be optimized sequentially

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
    Objective function can also consider the taxi-in time
    """
    prob = xp.problem("LightCTOP")
    M2   = Vio_Penalty

    deltaIndex = [(i, j) for i in range(len(N)) for j in range(N[i])]
    delta = {(i, j): xp.var(vartype=xp.binary, name='delta{0}_{1}'.format(i, j)) for (i, j) in deltaIndex}

    tauIndex = [(i, k) for i in range(len(N)) for k in FCAs if i in PhiT[k]]
    tau = {(i, k): xp.var(vartype=xp.integer, name='tau{0}_{1}'.format(i, k)) for (i, k) in tauIndex}

    BIndex = [(i, k, t) for i in range(len(N)) for k in FCAs if i in PhiT[k] for t in TIME]
    B = {(i, k, t): xp.var(vartype=xp.binary, name='B{0}_{1}_{2}'.format(i, k, t)) for (i, k, t) in BIndex}

    EIndex = [(k, t) for t in TIME for k in FCAs]
    E = {(k, t): xp.var(vartype=xp.integer, name='E{0}_{1}'.format(k, t)) for (k, t) in EIndex}

    prob.addVariable(delta, tau, B, E)

    """Define the objective function"""
    prob.setObjective(xp.Sum(( Q[i, j] * delta[i, j] ) for (i, j) in deltaIndex ) + \
                      xp.Sum( M2 * E[t, k] for (t, k) in EIndex), sense=xp.minimize)

    """Define the constraints"""
    for i in range(len(N)):
        prob.addConstraint(xp.Sum(delta[i, j] for j in range(N[i])) == 1)  # only one route can be chosen

    """ETA Constraints"""
    for i in range(len(N)):
        for k in SigmaT[i]:
            prob.addConstraint(
                tau[(i, k)] == xp.Sum(Ti[(i, j, k)] * delta[i, j] for j in range(N[i]) if k in Sigma[i, j]))

    """Two Constraints for B, See the paper"""
    for k in FCAs:
        for i in range(len(N)):
            if i in PhiT[k]:
                prob.addConstraint(xp.Sum(B[i, k, t] for t in TIME) <= 1)
                prob.addConstraint(xp.Sum(t * B[i, k, t] for t in TIME) == tau[(i, k)])
                # t must starts from 1!!
                # this constraint make sure flight will exit the PCA system

    """Capacity Constraints"""
    for t in TIME:
        for k in FCAs:
            prob.addConstraint(xp.Sum(B[i, k, t] for i in range(len(N)) if i in PhiT[k]) <= M[k][t - 1] + E[k, t])

    start = time()
    prob.setControl( 'outputlog',  0 )
    prob.solve()
    end   = time()

    log = open( Report_File , "a+")

    print('-' * 100)
    print ("Problem Status             : %s"% prob.getProbStatus())
    print ("Problem Status, Explained  : %s"% prob.getProbStatusString())
    print('-' * 100)
    print ("Solving This Instance Takes: %3.2f seconds" % (end - start))
    print ("Optimal Objective Value    : %s"% prob.getObjVal())
    print ("Total # of FCA Violations  : %s"% sum( prob.getSolution( E[t, k] ) for (t, k) in EIndex ))
    print ("Total # of Rerouted Flights: %s"% sum( prob.getSolution( delta[i, j] ) for (i, j) in deltaIndex if j!=0 ))
    print ("Total Reroute Mileages     : %4d  miles" % sum(
        Q[i, j] * prob.getSolution(delta[i, j]) for (i, j) in deltaIndex ))

    log.write('-' * 100 + '\n')
    log.write("Problem Status             ::%s\n" % prob.getProbStatus())
    log.write("Problem Status, Explained  : %s\n"% prob.getProbStatusString() )
    log.write('-' * 100 + '\n')
    log.write("Solving This Instance Takes: %3.2f seconds\n" % (end - start) )
    log.write("Optimal Objective Value    : %s\n"% prob.getObjVal() )
    log.write("Total # of FCA Violations  : %s\n"% sum( prob.getSolution( E[t, k] ) for (t, k) in EIndex ) )
    log.write("Total # of Rerouted Flights: %s\n"% sum( prob.getSolution( delta[i, j] ) for (i, j) in deltaIndex if j!=0 ) )
    log.write("Total Reroute Mileages     : %4d  miles\n" % sum(
        Q[i, j] * prob.getSolution(delta[i, j]) for (i, j) in deltaIndex ) )

    log.close()
    return (prob, delta, B, E)

def LightCTOPModel_Main( M, N, Q, Ti, PhiT, SigmaT, Sigma, Route_ID, Message = True ):
    """
    This function is coded using FICO Xpress Python API and minimize 1 FCA violation 2 # of rerouted flights 3 reroute miles, sequentially
    """

    if True == Message:
        print('-'*100)
        print("Models 1-3 Will be Solved Sequentially to Minimize Our Three Objectives, Whose Importances Are in Decreasing Order")

        log = open( Report_File , "a+")
        log.write('-'*100 + '\n')
        log.write("Models 1-3 Will be Solved Sequentially to Minimize Our Three Objectives, Whose Importances Are in Decreasing Order\n")
        log.close()

    FCA_Violations = LightCTOPModel_Model_1(M, N, Q, Ti, PhiT, SigmaT, Sigma, Message )
    Route_Changes  = LightCTOPModel_Model_2(M, N, Q, Ti, PhiT, SigmaT, Sigma, FCA_Violations, Message )
    Solution       = LightCTOPModel_Model_3(M, N, Q, Ti, PhiT, SigmaT, Sigma, FCA_Violations, Route_Changes, Message )

    return Solution

def LightCTOPModel_Model_1(M, N, Q, Ti, PhiT, SigmaT, Sigma, Message = True ):
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
    prob = xp.problem("LightCTOP_Minimize_Num_of_FCA_Violation")

    deltaIndex = [(i, j) for i in range(len(N)) for j in range(N[i])]
    delta = {(i, j): xp.var(vartype=xp.binary, name='delta{0}_{1}'.format(i, j)) for (i, j) in deltaIndex}

    tauIndex = [(i, k) for i in range(len(N)) for k in FCAs if i in PhiT[k]]
    tau = {(i, k): xp.var(vartype=xp.integer, name='tau{0}_{1}'.format(i, k)) for (i, k) in tauIndex}

    BIndex = [(i, k, t) for i in range(len(N)) for k in FCAs if i in PhiT[k] for t in TIME]
    B = {(i, k, t): xp.var(vartype=xp.binary, name='B{0}_{1}_{2}'.format(i, k, t)) for (i, k, t) in BIndex}

    EIndex = [(k, t) for t in TIME for k in FCAs]
    E = {(k, t): xp.var(vartype=xp.integer, name='E{0}_{1}'.format(k, t)) for (k, t) in EIndex}

    prob.addVariable(delta, tau, B, E)

    """Define the objective function"""
    prob.setObjective( xp.Sum( E[t, k] for (t, k) in EIndex), sense=xp.minimize )

    """Define the constraints"""
    for i in range(len(N)):
        prob.addConstraint(xp.Sum(delta[i, j] for j in range(N[i])) == 1)  # only one route can be chosen

    """ETA Constraints"""
    for i in range(len(N)):
        for k in SigmaT[i]:
            prob.addConstraint(
                tau[(i, k)] == xp.Sum(Ti[(i, j, k)] * delta[i, j] for j in range(N[i]) if k in Sigma[i, j]))

    """Two Constraints for B, See the paper"""
    for k in FCAs:
        for i in range(len(N)):
            if i in PhiT[k]:
                prob.addConstraint(xp.Sum(B[i, k, t] for t in TIME) <= 1)
                prob.addConstraint(xp.Sum(t * B[i, k, t] for t in TIME) == tau[(i, k)])
                # t must starts from 1!!
                # this constraint make sure flight will exit the PCA system

    """Capacity Constraints"""
    for t in TIME:
        for k in FCAs:
            prob.addConstraint(xp.Sum(B[i, k, t] for i in range(len(N)) if i in PhiT[k]) <= M[k][t - 1] + E[k, t])

    start = time()
    prob.setControl('outputlog', 0)
    prob.solve()
    end = time()

    if True == Message:
        print('-' * 100)
        print("Model 1: Miminize # of FCA Violations")
        print ("Problem Status             :", prob.getProbStatus())
        print ("Problem Status, Explained  :", prob.getProbStatusString())
        print ("Solving This Instance Takes: %3.2f seconds" % (end - start))
        print ("# of FCA Violations        : %4d" % ( prob.getObjVal() ))
        print("# of Rerouted Flights      : %4d" % sum( prob.getSolution( delta[i, j] ) for (i, j) in deltaIndex if j!=0 ) )
        print("# of Reroute Mileages      : %4d  miles" % sum(
                                                        Q[i, j] * prob.getSolution(delta[i, j]) for (i, j) in deltaIndex ) )
        # print(" " % () )
        print('-' * 100)

        log = open( Report_File , "a+")
        log.write('-'*100 + '\n')
        log.write("Model 1: Miminize # of FCA Violations\n")
        log.write("Problem Status             : %s\n"% prob.getProbStatus() )
        log.write("Problem Status, Explained  : %s\n"% prob.getProbStatusString() )
        log.write("Solving This Instance Takes: %3.2f seconds\n" % (end - start) )
        log.write("# of FCA Violations        : %4d\n" % ( prob.getObjVal() ) )
        log.write("# of Rerouted Flights      : %4d\n" % sum( prob.getSolution( delta[i, j] ) for (i, j) in deltaIndex if j!=0 ) )
        log.write("# of Reroute Mileages      : %4d  miles\n" % sum(
                                                        Q[i, j] * prob.getSolution(delta[i, j]) for (i, j) in deltaIndex ) )

        log.write('-'*100 + '\n')
        log.close()

    return prob.getObjVal()

def LightCTOPModel_Model_2(M, N, Q, Ti, PhiT, SigmaT, Sigma, FCA_Violations, Message = True ):
    prob = xp.problem("LightCTOP_Minimize_Num_of_Reroutes")

    deltaIndex = [(i, j) for i in range(len(N)) for j in range(N[i])]
    delta = {(i, j): xp.var(vartype=xp.binary, name='delta{0}_{1}'.format(i, j)) for (i, j) in deltaIndex}

    tauIndex = [(i, k) for i in range(len(N)) for k in FCAs if i in PhiT[k]]
    tau = {(i, k): xp.var(vartype=xp.integer, name='tau{0}_{1}'.format(i, k)) for (i, k) in tauIndex}

    BIndex = [(i, k, t) for i in range(len(N)) for k in FCAs if i in PhiT[k] for t in TIME]
    B = {(i, k, t): xp.var(vartype=xp.binary, name='B{0}_{1}_{2}'.format(i, k, t)) for (i, k, t) in BIndex}

    EIndex = [(k, t) for t in TIME for k in FCAs]
    E = {(k, t): xp.var(vartype=xp.integer, name='E{0}_{1}'.format(k, t)) for (k, t) in EIndex}

    prob.addVariable(delta, tau, B, E)

    """Define the objective function"""
    prob.setObjective(xp.Sum( delta[i, j] for (i, j) in deltaIndex if j!=0 ) , sense=xp.minimize)

    """Define the constraints"""
    for i in range(len(N)):
        prob.addConstraint(xp.Sum(delta[i, j] for j in range(N[i])) == 1)  # only one route can be chosen

    """ETA Constraints"""
    for i in range(len(N)):
        for k in SigmaT[i]:
            prob.addConstraint(
                tau[(i, k)] == xp.Sum(Ti[(i, j, k)] * delta[i, j] for j in range(N[i]) if k in Sigma[i, j]))

    """Two Constraints for B, See the paper"""
    for k in FCAs:
        for i in range(len(N)):
            if i in PhiT[k]:
                prob.addConstraint(xp.Sum(B[i, k, t] for t in TIME) <= 1)
                prob.addConstraint(xp.Sum(t * B[i, k, t] for t in TIME) == tau[(i, k)])
                # t must starts from 1!!
                # this constraint make sure flight will exit the PCA system

    """Capacity Constraints"""
    for t in TIME:
        for k in FCAs:
            prob.addConstraint(xp.Sum(B[i, k, t] for i in range(len(N)) if i in PhiT[k]) <= M[k][t - 1] + E[k, t])

    """FCA Violation Constraints"""
    prob.addConstraint( xp.Sum( E[ k, t ] for (k, t) in EIndex ) <= FCA_Violations )

    start = time()
    prob.setControl('outputlog', 0)
    prob.solve()
    end = time()

    if True == Message:
        print("Model 2: Miminize # of Rerouted Flights")
        print ("Problem Status             :", prob.getProbStatus())
        print ("Problem Status, Explained  :", prob.getProbStatusString())
        print ("Solving This Instance Takes: %3.2f seconds" % (end - start))
        print ("# of FCA Violations        : %4d" % sum( prob.getSolution( E[t, k] ) for (t, k) in EIndex ))
        print("# of Rerouted Flights      : %4d" % prob.getObjVal() )
        print("# of Reroute Mileages      : %4d  miles" % sum(
                                                        Q[i, j] * prob.getSolution(delta[i, j]) for (i, j) in deltaIndex ) )


        print('-' * 100)

        log = open( Report_File , "a+")
        log.write("Model 2: Miminize # of Rerouted Flights\n")
        log.write("Problem Status             : %s\n" % prob.getProbStatus() )
        log.write("Problem Status, Explained  : %s\n" % prob.getProbStatusString() )
        log.write("Solving This Instance Takes: %3.2f seconds\n" % (end - start) )
        log.write("# of FCA Violations        : %4d\n" % sum(prob.getSolution(E[t, k]) for (t, k) in EIndex) )
        log.write("# of Rerouted Flights      : %4d\n" % prob.getObjVal() )
        log.write("# of Reroute Mileages      : %4d  miles\n" % sum(
                                                        Q[i, j] * prob.getSolution(delta[i, j]) for (i, j) in deltaIndex ) )
        log.write('-'*100 + '\n')


    return prob.getObjVal()

def LightCTOPModel_Model_3(M, N, Q, Ti, PhiT, SigmaT, Sigma, FCA_Violations, Route_Changes, Message = True ):
    prob = xp.problem("LightCTOP_Minimize_Mileage")
    deltaIndex = [(i, j) for i in range(len(N)) for j in range(N[i])]
    delta = {(i, j): xp.var(vartype=xp.binary, name='delta{0}_{1}'.format(i, j)) for (i, j) in deltaIndex}

    tauIndex = [(i, k) for i in range(len(N)) for k in FCAs if i in PhiT[k]]
    tau = {(i, k): xp.var(vartype=xp.integer, name='tau{0}_{1}'.format(i, k)) for (i, k) in tauIndex}

    BIndex = [(i, k, t) for i in range(len(N)) for k in FCAs if i in PhiT[k] for t in TIME]
    B = {(i, k, t): xp.var(vartype=xp.binary, name='B{0}_{1}_{2}'.format(i, k, t)) for (i, k, t) in BIndex}

    EIndex = [(k, t) for t in TIME for k in FCAs]
    E = {(k, t): xp.var(vartype=xp.integer, name='E{0}_{1}'.format(k, t)) for (k, t) in EIndex}

    prob.addVariable(delta, tau, B, E)

    """Define the objective function"""
    prob.setObjective(xp.Sum((Q[i, j] * delta[i, j]) for (i, j) in deltaIndex) , sense=xp.minimize)

    """Define the constraints"""
    for i in range(len(N)):
        prob.addConstraint(xp.Sum(delta[i, j] for j in range(N[i])) == 1)  # only one route can be chosen

    """ETA Constraints"""
    for i in range(len(N)):
        for k in SigmaT[i]:
            prob.addConstraint(
                tau[(i, k)] == xp.Sum(Ti[(i, j, k)] * delta[i, j] for j in range(N[i]) if k in Sigma[i, j]))

    """Two Constraints for B, See the paper"""
    for k in FCAs:
        for i in range(len(N)):
            if i in PhiT[k]:
                prob.addConstraint(xp.Sum(B[i, k, t] for t in TIME) <= 1)
                prob.addConstraint(xp.Sum(t * B[i, k, t] for t in TIME) == tau[(i, k)])
                # t must starts from 1!!
                # this constraint make sure flight will exit the PCA system

    """Capacity Constraints"""
    for t in TIME:
        for k in FCAs:
            prob.addConstraint(xp.Sum(B[i, k, t] for i in range(len(N)) if i in PhiT[k]) <= M[k][t - 1] + E[k, t])

    """FCA Violation Constraints"""
    prob.addConstraint( xp.Sum( E[ k, t ] for (k, t) in EIndex ) <= FCA_Violations )

    """# of Rerouted Flights Constraints"""
    prob.addConstraint( xp.Sum( delta[i, j] for (i, j) in deltaIndex if j!=0 ) <= Route_Changes )

    start = time()
    prob.setControl('outputlog', 0)
    prob.solve()
    end = time()

    if True == Message:
        print("Model 3: Miminize Total Reroute Mileages")
        print ("Problem Status             :", prob.getProbStatus())
        print ("Problem Status, Explained  :", prob.getProbStatusString())
        print ("Solving This Instance Takes: %3.2f seconds" % (end - start))
        print ("# of FCA Violations        : %4d" % sum( prob.getSolution( E[t, k] ) for (t, k) in EIndex ))
        print("# of Rerouted Flights      : %4d" % sum(prob.getSolution(delta[i, j]) for (i, j) in deltaIndex if j != 0))
        print ("# of Reroute Mileages      : %4d  miles" % prob.getObjVal())

        log = open( Report_File , "a+")
        log.write("Model 3: Miminize Total Reroute Mileages\n")
        log.write("Problem Status             : %s\n"% prob.getProbStatus() )
        log.write("Problem Status, Explained  : %s\n"% prob.getProbStatusString() )
        log.write("Solving This Instance Takes: %3.2f seconds\n" % (end - start) )
        log.write("# of FCA Violations        : %4d\n" % sum(prob.getSolution(E[t, k]) for (t, k) in EIndex) )
        log.write("# of Rerouted Flights      : %4d\n" % sum( prob.getSolution( delta[i, j] ) for (i, j) in deltaIndex if j!=0 ) )
        log.write("# of Reroute Mileages      : %4d  miles\n" % prob.getObjVal() )

    return (prob, delta, B, E)


