#!/usr/bin/python3
# -*- coding: utf-8 -*-

# geklaut von https://www.geeksforgeeks.org/minimize-cash-flow-among-given-set-friends-borrowed-money/


def getMin(arr):
    N = len(arr)

    minInd = 0
    for i in range(1, N):
        if (arr[i] < arr[minInd]):
            minInd = i
    return minInd

# A utility function that returns
# index of maximum value in arr[]
def getMax(arr):
    N = len(arr)

    maxInd = 0
    for i in range(1, N):
        if (arr[i] > arr[maxInd]):
            maxInd = i
    return maxInd

# A utility function to
# return minimum of 2 values
def minOf2(x, y):

    return x if x < y else y

# amount[p] indicates the net amount to
# be credited/debited to/from person 'p'
# If amount[p] is positive, then i'th
# person will amount[i]
# If amount[p] is negative, then i'th
# person will give -amount[i]
# user is dict of the format {0: "name", 1:"name2"}
def minCashFlowRec(amount, user, results):

    # Find the indexes of minimum
    # and maximum values in amount[]
    # amount[mxCredit] indicates the maximum
    # amount to be given(or credited) to any person.
    # And amount[mxDebit] indicates the maximum amount
    # to be taken (or debited) from any person.
    # So if there is a positive value in amount[],
    # then there must be a negative value
    mxCredit = getMax(amount)
    mxDebit = getMin(amount)

    # If both amounts are 0,
    # then all amounts are settled
    if (amount[mxCredit] < 0.001 and amount[mxDebit] < 0.001):
        return 0

    # Find the minimum of two amounts
    min = minOf2(-amount[mxDebit], amount[mxCredit])
    amount[mxCredit] -=min
    amount[mxDebit] += min

    # If minimum is the maximum amount to be
    results.append("{} zahlt {} {}€".format(user[mxDebit], user[mxCredit], round(min,2)))

    # Recur for the amount array. Note that
    # it is guaranteed that the recursion
    # would terminate as either amount[mxCredit]
    # or amount[mxDebit] becomes 0
    minCashFlowRec(amount, user, results)

# Given a set of persons as graph[] where
# graph[i][j] indicates the amount that
# person i needs to pay person j, this
# function finds and prints the minimum
# cash flow to settle all debts.
def minCashFlow(graph, user):
    N = len(graph)

    # Create an array amount[],
    # initialize all value in it as 0.
    amount = [0 for i in range(N)]

    # Calculate the net amount to be paid
    # to person 'p', and stores it in amount[p].
    # The value of amount[p] can be calculated by
    # subtracting debts of 'p' from credits of 'p'
    for p in range(N):
        for i in range(N):
            amount[p] += (graph[i][p] - graph[p][i])

    results = []
    minCashFlowRec(amount, user, results)
    return results


def calc_graph(N, gezahlt):
    # initialize graph
    graph = [[0 for j in range(N)] for i in range(N)]
    zahlt_jeder = sum(gezahlt)/N

    # fill graph
    for i in range(N):
        for j in range(N):
            if i==j:
                graph[j][i] = 0.
            else:
                graph[j][i] = (gezahlt[i]-zahlt_jeder)/N

    return graph
