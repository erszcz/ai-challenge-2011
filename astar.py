#!/usr/bin/env python
# coding: utf-8
# vim: sts=4 sw=4 ts=4 tw=74 et

import heapq

import logging as log

class priority_set:
    def __init__(self, values=None):
        self.s = set()
        self.q = []

    def add(self, priority, key):
        if key in self.s:
            raise Exception("item already in set")
        self.s.add(key)
        heapq.heappush(self.q, (priority, key))

    def remove(self, key):
        self.s.remove(key)
        items = [i for i in self.q if i[1] == key]
        self.q.remove(items[0])
        heapq.heapify(self.q)

    def pop(self):
        #log.debug("pop: %d", len(self.q))
        #print("pop: %d" % len(self.q))
        _, i = heapq.heappop(self.q)
        self.s.remove(i)
        return i

    def __contains__(self, key):
        return key in self.s

    def __str__(self):
        # print just the queue, sorted by priority
        return "%s" % (sorted(self.q, key=lambda i: i[0]))
        # print both set and queue, sorting by coords
        #return "(%s,\n %s)" % (str(sorted(self.s)),
            #str(sorted(self.q, key=lambda i: i[1])))
        # print just the queue, sorting by priority
        #return str(sorted(self.q))

    def empty(self):
        return len(self.q) == 0

def distance(a, b):
    return abs(a[0] - b[0]) + abs(a[1] - b[1])

def make_adjacent(graph, passable_p=lambda p: True):
    def adjacent(node):
        in_graph = lambda p: p[0] >= 0 and p[0] < len(graph) \
            and p[1] >= 0 and p[1] < len(graph[0])
        r, c = node
        return filter(lambda p: in_graph(p) and passable_p(p),
            [(r, c-1), (r, c+1), (r-1, c), (r+1, c)])
    return adjacent

def path(graph, start, goal, distance=distance, passable_p=lambda p: True):
    #print "path", start, goal
    adjacent = make_adjacent(graph, passable_p=passable_p)

    g_score = {}
    h_score = {}
    f_score = {}

    h_cost = lambda loc: graph[loc[0]][loc[1]]

    g_score[start] = 0
    h_score[start] = h_cost(start)
    f_score[start] = g_score[start] + h_score[start]

    closed = set()
    frontier = priority_set()
    frontier.add(f_score[start], start)
    came_from = {}

    while not frontier.empty():
        x = frontier.pop()
        if x == goal:
            return reconstruct_path(came_from, goal)

        closed.add(x)
        #log.debug("%s, %s", x, adjacent(x))
        #print x, adjacent(x)
        for y in adjacent(x):
            if y in closed:
                continue
            tentative_g_score = g_score[x] + distance(x,y)

            if not y in frontier or tentative_g_score < g_score[y]:
                came_from[y] = x
                #print x, came_from[x] if came_from.has_key(x) else "", "\n"
                g_score[y] = tentative_g_score
                h_score[y] = h_cost(y)
                f_score[y] = g_score[y] + h_score[y]
                if not y in frontier:
                    #print y, f_score[y]
                    frontier.add(f_score[y], y)
                #else:
                    #frontier.remove(y)
                    #frontier.add(f_score[y], y)

        #print frontier, "\n"
        #print x, came_from[x] if came_from.has_key(x) else "", "\n"
        #print "  ", y, f_score[y], "\n  ", frontier, "\n"
        #print distance(x,y)
        #print tentative_g_score

    return []

def reconstruct_path(came_from, current_node):
    if came_from.has_key(current_node):
        p = reconstruct_path(came_from, came_from[current_node])
        p.append(current_node)
        return p
    else:
        return [current_node]

def h_simple(start, goal, p, distance):
    return distance(p, goal)

def h_cross(start, goal, p, distance):
    dx1 = p[0] - goal[0]
    dy1 = p[1] - goal[1]
    dx2 = start[0] - goal[0]
    dy2 = start[1] - goal[1]
    cross = abs(dx1*dy2 - dx2*dy1)
    return 0.001 * cross + distance(p, goal)

def build_graph(start, goal, distance=distance,
        passable_p=lambda p: True, h_cost=h_cross):
    rmin, rmax = [f(start[0], goal[0]) for f in (min,max)]
    cmin, cmax = [f(start[1], goal[1]) for f in (min,max)]
    w = cmax - cmin + 1
    h = rmax - rmin + 1
    unpassable = 10000
    graph = []
    for i in xrange(h):
        row = []
        for j in xrange(w):
            p = (rmin + i, cmin + j)
            if passable_p(p):
                row.append(h_cost(start, goal, p, distance))
            else:
                row.append(unpassable)
        graph.append(row)
    return (rmin, cmin), graph

def dump_path(filename, graph, start, goal, path):
    with file(filename, 'w') as f:
        f.write("# gray  - passable\n")
        f.write("# black - impassable\n")
        f.write("# white - path\n")
        f.write("# start - green\n")
        f.write("# goal  - red\n")
        f.write("color 120 120 120\n")
        for i in xrange(len(graph)):
            for j in xrange(len(graph[0])):
                if graph[i][j] == 10000:
                    f.write("color 0 0 0\n")
                    f.write("point %d %d\n" % (j,i))
                    f.write("color 120 120 120\n")
                else:
                    f.write("point %d %d\n" % (j,i))
        for r,c in path:
            f.write("color 255 255 255\n")
            f.write("point %d %d\n" % (c,r))
        f.write("color 0 255 0\n")
        f.write("point %d %d\n" % (start[1], start[0]))
        f.write("color 255 0 0\n")
        f.write("point %d %d\n" % (goal[1], goal[0]))
