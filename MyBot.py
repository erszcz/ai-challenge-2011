#!/usr/bin/env python
# coding: utf-8
# vim: sts=4 sw=4 ts=4 tw=74 et
from random import choice, randrange
from ants import *
import sys
import logging
from optparse import OptionParser

import time
import os
import astar

import logging as log
log.basicConfig(format='%(message)s',
                filename='/dev/null',
                level=logging.DEBUG)

DIRECTIONS = ['n', 's', 'w', 'e']

def rand(seq):
    return seq[randrange(0, len(seq))]

def minmax(seq):
    reduction = lambda acc,e: (min(e,acc[0]), max(e,acc[1]))
    return reduce(reduction, seq, (seq[0],seq[0]))

def v2add(a, b):
    return a[0] + b[0], a[1] + b[1]

def v2sub(a, b):
    return a[0] - b[0], a[1] - b[1]

def get_path(start, goal, ants):
    #g = astar.build_graph(start, goal, passable_p=ants.passable,
            #distance=ants.distance)
    loc, g = astar.build_graph(start, goal, passable_p=ants.passable)
    #log.debug("get_path: g =\n  %s" % str(g))
    #path = astar.path(g, start, goal, distance=ants.distance)
    passable_p = lambda p: ants.passable(v2add(p, loc))
    path = astar.path(g, v2sub(start, loc), v2sub(goal, loc),
            passable_p=passable_p)
    #log.debug("get_path: path =\n  %s" % str(path))
    #astar.dump_path("path_%s_%s.dat" % (start, goal), g,
        #v2sub(start, loc), v2sub(goal, loc), path)
    return map(lambda p1: v2add(p1, loc), path)

class MyBot:
    def __init__(self):
        self.ants_straight = {}
        self.ants_lefty = {}
        self.ants_harvesting = {}
        self.turns = 0

    def do_setup(self, ants):
        # initialize data structures after learning the game settings
        pass

    def do_turn(self, ants):
        destinations = []
        new_straight = {}
        new_lefty = {}
        new_harvesting = {}
        self.turns += 1

        for ant in ants.my_ants():
            a_row, a_col = ant
            log.info("turn %d: ant %s" % (self.turns, ant))
            log.debug("  time remaining: %d" % ants.time_remaining())

            # going for food following a computed path?
            if ant in self.ants_harvesting:
                log.info("  is harvesting")
                path = self.ants_harvesting[ant]
                dest, path_tail = path[0], path[1:]
                log.debug("  dest: %s, tail: %s", dest, path_tail)
                if ants.passable(dest):
                    log.debug("  dest is passable")
                    if ants.unoccupied(dest) and not dest in destinations:
                        ants.issue_order(( ant,
                            ants.direction(ant, dest)[0] ))
                        destinations.append(dest)
                        # path unfinished?
                        if path_tail:
                            new_harvesting[dest] = path_tail
                        # that was the last step, do something else
                        else:
                            new_straight[ant] = rand(DIRECTIONS)
                    else:
                        log.debug("  dest is occupied or in destinations")
                        # have ant wait until it is clear
                        new_harvesting[dest] = path
                        destinations.append(ant)
                    continue

            #nearby = lambda targets: [ (r,c) for (r,c) in targets \
                 #if ((a_row-r)**2 + (a_col-c)**2) < ants.viewradius2 ]
            #food = nearby(ants.food())

            # food found? find a path to it
            if not ant in self.ants_harvesting and ants.food():
                food = min(ants.food(), key=lambda f: ants.distance(f, ant))
                path = get_path(ant, food, ants)
                log.info("  found %s food: %s" %
                    ("reachable" if path else "unreachable", food))
                log.debug("  time remaining: %d" % ants.time_remaining())
                if path:
                    log.info("  starts harvesting")
                    new_harvesting[ant] = path[1:]
                    continue # to next ant

            # send new ants in a straight line
            if (not ant in self.ants_straight and
                    not ant in self.ants_lefty and
                    not ant in self.ants_harvesting):
                log.info("  starts going straight")
                direction = rand(DIRECTIONS)
                self.ants_straight[ant] = direction

            # send ants going in a straight line in the same direction
            if ant in self.ants_straight:
                log.info("  goes straight")
                direction = self.ants_straight[ant]
                n_row, n_col = ants.destination(ant, direction)
                if ants.passable((n_row, n_col)):
                    if (ants.unoccupied((n_row, n_col)) and
                            not (n_row, n_col) in destinations):
                        ants.issue_order((ant, direction))
                        new_straight[(n_row, n_col)] = direction
                        destinations.append((n_row, n_col))
                    else:
                        # pause ant, turn and try again next turn
                        new_straight[ant] = LEFT[direction]
                        destinations.append(ant)
                else:
                    # hit a wall, start following it
                    log.info("  starts going lefty")
                    self.ants_lefty[ant] = RIGHT[direction]

            # send ants following a wall, keeping it on their left
            if ant in self.ants_lefty:
                log.info("  goes lefty")
                direction = self.ants_lefty[ant]
                directions = [LEFT[direction], direction, RIGHT[direction],
                    BEHIND[direction]]
                # try 4 directions in order, attempting to turn left at corners
                for new_direction in directions:
                    n_row, n_col = \
                        ants.destination(ant, new_direction)
                    if ants.passable((n_row, n_col)):
                        if not ants.dead_end((n_row, n_col), new_direction):
                            if (ants.unoccupied((n_row, n_col))
                                    and not (n_row, n_col) in destinations):
                                ants.issue_order((ant, new_direction))
                                new_lefty[(n_row, n_col)] = new_direction
                                destinations.append((n_row, n_col))
                                break
                            else:
                                # have ant wait until it is clear
                                new_straight[ant] = RIGHT[direction]
                                destinations.append(ant)
                                break

        # reset lists
        self.ants_straight = new_straight
        self.ants_lefty = new_lefty
        self.ants_harvesting = new_harvesting

if __name__ == '__main__':
    try:
        import psyco
        psyco.full()
    except ImportError:
        pass
    try:
        Ants.run(MyBot())
    except KeyboardInterrupt:
        print('ctrl-c, leaving ...')
        
