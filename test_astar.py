#!/usr/bin/env python
# coding: utf-8
# vim: sts=4 sw=4 ts=4 tw=74 et

import time

from astar import *

graph1 = [[   0,   0,   0, 100,   0,  0],
          [   0,   0,   0, 100, 100,  0],
          [   0,   0,   0,   0, 100,  0],
          [   0, 100,   0,   0, 100,  0],
          [   0, 100, 100, 100, 100,  0],
          [   0,   0,   0,   0,   0,  0]]

graph2 = [[   0,   0,   0,   0,   0,  0],
          [   0,   0,   0, 100, 100,  0],
          [   0,   0,   0,   0, 100,  0],
          [   0, 100,   0,   0, 100,  0],
          [ 100, 100, 100, 100, 100,  0],
          [   0,   0,   0,   0,   0,  0]]

graph3 = [[   0,   0,   0, 100,   0,  0],
          [   0,   0,   0, 100, 100,  0],
          [   0,   0,   0,   0, 100,  0],
          [   0, 100,   0,   0, 100,  0],
          [ 100, 100,   0, 100, 100,  0],
          [   0,   0,   0,   0,   0,  0]]

graph4 = [[42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 10000, 10000, 10000, 4, 3, 2, 10000, 0],
          [43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 10000, 10000, 5, 4, 3, 2, 1],
          [44, 43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 10000, 10000, 10000, 6, 5, 4, 3, 2],
          [45, 44, 43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 10000, 8, 7, 6, 5, 4, 3],
          [10000, 45, 44, 43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 10000, 10000, 10000, 10000, 10000, 6, 10000, 10000],
          [10000, 46, 45, 44, 43, 10000, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10000, 10000, 10000, 10000, 10000, 5],
          [48, 47, 46, 45, 44, 10000, 10000, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7, 6],
          [49, 48, 47, 46, 45, 10000, 10000, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8, 7],
          [50, 49, 48, 47, 46, 10000, 10000, 10000, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9, 8],
          [51, 50, 49, 48, 47, 10000, 10000, 10000, 43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10, 9],
          [52, 51, 50, 49, 48, 10000, 10000, 10000, 44, 43, 42, 41, 40, 39, 38, 37, 36, 35, 34, 33, 32, 31, 30, 29, 28, 27, 26, 25, 24, 23, 22, 21, 20, 19, 18, 17, 16, 15, 14, 13, 12, 11, 10]]

graph5 = [[   0,   0,   0,   0,   0,  0],
          [   0,   0, 100,   0, 100,  0],
          [   0, 100,   0,   0, 100,  0],
          [   0, 100, 100,   0, 100,  0],
          [ 100, 100,   0, 100, 100,  0],
          [   0, 100,   0,   0,   0,  0]]

graph6 = [[ 100,   0,   0, 100,   0, 100],
          [   0,   0, 100,   0, 100,   0],
          [   0, 100,   0,   0,   0,   0],
          [   0, 100, 100,   0, 100,   0],
          [ 100, 100,   0, 100, 100,   0],
          [   0, 100,   0,   0,   0,   0]]

def test():
    #graph, start, goal = graph5, (4,2), (2,2)
    #graph, start, goal, max_path_len = graph3, (0,0), (5,5), None
    #graph, start, goal, max_path_len = graph3, (0,0), (5,5), 5
    graph, start, goal, max_path_len = graph3, (0,0), (0,0), 5

    passable = lambda loc: graph[loc[0]][loc[1]] != 100

    graph_h = len(graph)
    graph_w = len(graph[0])
    rmin, rmax = [f(start[0], goal[0]) for f in [min, max]]
    cmin, cmax = [f(start[1], goal[1]) for f in [min, max]]

    print "rmin, rmax:",rmin,rmax
    print "cmin, cmax:",cmin,cmax
    
    # paths across edges
    def adjacent(node):
        #log.debug("adjacent: %s" % str(node))
        r, c = node
        return filter(passable, [ (r, (c-1) % graph_h),
                                  (r, (c+1) % graph_h),
                                  ((r-1) % graph_w, c),
                                  ((r+1) % graph_w, c) ])

    # paths bounded by edges
    #def adjacent(node):
        #print("adjacent: %s" % str(node))
        #r, c = node
        #in_graph = lambda p: p[0] >= rmin and p[0] <= rmax \
                #and p[1] >= cmin and p[1] <= cmax
        #result = filter(lambda p: in_graph(p) and passable(p),
                #[ (r, c-1), (r, c+1), (r-1, c), (r+1, c) ])
        ##result = []
        ##for p in [ (r, c-1), (r, c+1), (r-1, c), (r+1, c) ]:
            ##print "  p:", p
            ##print "  in graph:", in_graph(p)
            ##print "  passable:", 
            ##try:
                ##print passable(p)
            ##except IndexError, e:
                ##print "out of graph"
            ##if in_graph(p) and passable(p):
                ##result.append(p)
        #return result

    def distance(loc1, loc2):
        'calculate the closest distance between to locations'
        row1, col1 = loc1
        row2, col2 = loc2
        d_col = min(abs(col1 - col2), graph_w - abs(col1 - col2))
        d_row = min(abs(row1 - row2), graph_h - abs(row1 - row2))
        return d_row + d_col

    p = path(graph, start, goal, adjacent, distance,
            h_cross, max_path_len=max_path_len)
    
    print("get_path: path =\n  %s" % str(p))
    print "len(path):", len(p)
    dump_path("path_%s_%s_%s.dat" % (start, goal, time.time()),
            graph, start, goal, p, passable=passable)

if __name__ == '__main__':
    test()
