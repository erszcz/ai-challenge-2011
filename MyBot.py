#!/usr/bin/env python
# coding: utf-8
# vim: sts=4 sw=4 ts=4 tw=74 et
from random import randrange, shuffle
from ants import *

from math import atan
import astar

import logging as log
log.basicConfig(format='%(message)s',
                filename='debug.log',
                level=log.DEBUG)

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
    loc, g = astar.build_graph(start, goal, passable_p=ants.passable)
    #log.debug("get_path: g =\n  %s" % str(g))
    passable_p = lambda p: ants.passable(v2add(p, loc))
    #path = astar.path(g, start, goal, distance=ants.distance)
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
        self.ants_tracking = {}
        self.ants_guarding = {}
        self.turns = 0
        self.food = []
        self.enemy_hills = []
        self.my_hills = []
        self.ants = None
        self.guard_threshold = 0.0

    def do_setup(self, ants):
        # initialize data structures after learning the game settings
        log.info("setup")
        log.info("  viewradius2: %d", ants.viewradius2)
        log.info("  attackradius2: %d", ants.attackradius2)
        log.info("  spawnradius2: %d", ants.spawnradius2)
        pass

    def start_turn(self, ants):
        self.ants = ants
        self.food = ants.food()
        self.enemy_hills = ants.enemy_hills()
        self.my_hills = ants.my_hills()
        
        self.destinations = []
        self.new_straight = {}
        self.new_lefty = {}
        self.new_tracking = {}
        self.new_guarding = {}

        self.turns += 1

        x = self.turns / ants.turns
        self.guard_threshold = atan(2.0 * x) / 3.0

    def end_turn(self):
        self.ants_straight = self.new_straight
        self.ants_lefty = self.new_lefty
        self.ants_tracking = self.new_tracking
        self.ants_guarding = self.new_guarding

    def do_turn(self, ants):
        self.start_turn(ants)

        for ant in ants.my_ants():
            a_row, a_col = ant
            log.info("turn %d: ant %s" % (self.turns, ant))
            log.debug("  time remaining: %d" % ants.time_remaining())

            # tracking a path?
            if ant in self.ants_tracking:
                log.info("  is harvesting")
                path = self.ants_tracking[ant]
                dest, path_tail = path[0], path[1:]
                log.debug("  dest: %s, tail: %s", dest, path_tail)
                if ants.passable(dest):
                    log.debug("  dest is passable")
                    if ants.unoccupied(dest) and not dest in self.destinations:
                        direction = ants.direction(ant, dest)[0]
                        ants.issue_order((ant, direction))
                        self.destinations.append(dest)
                        # path unfinished?
                        if path_tail:
                            self.new_tracking[dest] = path_tail
                        # that was the last step, do something else
                        else:
                            self.new_straight[ant] = direction
                    else:
                        log.debug("  dest is occupied or in destinations")
                        path.insert(0, ant)
                        shuffle(DIRECTIONS)
                        for d in DIRECTIONS:
                            dest = ants.destination(ant, d)
                            if self.move(ant, dest):
                                self.new_tracking[dest] = path
                                break
                    continue

            # enemy hills?
            if not ant in self.ants_tracking and self.enemy_hills:
                hill, _ = min(self.enemy_hills,
                    key=lambda h: ants.distance(h[0], ant))
                if ants.distance(ant, hill) <= ants.viewradius2:
                    path = get_path(ant, hill, ants)
                    log.info("  found %s hill: %s" %
                        ("reachable" if path else "unreachable", hill))
                    if path:
                        log.info("  starts tracking hill")
                        self.new_tracking[ant] = path[1:]
                        continue # to next ant

            # food found? find a path to it
            if not ant in self.ants_tracking and self.food:
                food = min(self.food, key=lambda f: ants.distance(f, ant))
                if ants.distance(ant, food) <= ants.viewradius2:
                    path = get_path(ant, food, ants)
                    log.info("  found %s food: %s" %
                        ("reachable" if path else "unreachable", food))
                    if path:
                        log.info("  starts harvesting")
                        self.new_tracking[ant] = path[1:]
                        self.food.remove(food)
                        continue # to next ant

            # new (or free) ants:
            if (not ant in self.ants_straight and
                    not ant in self.ants_lefty and
                    not ant in self.ants_tracking and
                    not ant in self.ants_guarding):
                distance_to = lambda target: ants.distance(ant, target)
                choice = random.random()
                if choice < self.guard_threshold:
                    # guard the hill
                    log.info("  starts guarding")
                    hill = min(self.my_hills, key=distance_to)
                    self.ants_guarding[ant] = hill
                else:
                    # scout/straight/gather food
                    log.info("  starts going straight")
                    direction = rand(DIRECTIONS)
                    self.ants_straight[ant] = direction

            # guarding - random walk in vicinity of a hill
            if ant in self.ants_guarding:
                hill = self.ants_guarding[ant]
                if ants.distance(ant, hill) > ants.spawnradius2 + 2:
                    d = rand(ants.direction(ant, hill))
                    directions = [d, RIGHT[d], LEFT[d]]
                else:
                    directions = DIRECTIONS
                    shuffle(directions)
                done = False
                for d in directions:
                    dest = ants.destination(ant, d)
                    if ants.passable(dest) \
                            and self.move(ant, dest, direction=d):
                        self.new_guarding[dest] = hill
                        done = True
                        break
                if not done and not ant in self.destinations:
                    self.new_guarding[ant] = hill
                    self.destinations.append(ant)

            # send ants going in a straight line in the same direction
            if ant in self.ants_straight:
                log.info("  goes straight")
                direction = self.ants_straight[ant]
                n_row, n_col = ants.destination(ant, direction)
                if ants.passable((n_row, n_col)):
                    if (ants.unoccupied((n_row, n_col)) and
                            not (n_row, n_col) in self.destinations):
                        ants.issue_order((ant, direction))
                        self.new_straight[(n_row, n_col)] = direction
                        self.destinations.append((n_row, n_col))
                    else:
                        # pause ant, turn and try again next turn
                        self.new_straight[ant] = LEFT[direction]
                        self.destinations.append(ant)
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
                                    and not (n_row, n_col) in self.destinations):
                                ants.issue_order((ant, new_direction))
                                self.new_lefty[(n_row, n_col)] = new_direction
                                self.destinations.append((n_row, n_col))
                                break
                            else:
                                # have ant wait until it is clear
                                self.new_straight[ant] = RIGHT[direction]
                                self.destinations.append(ant)
                                break
        self.end_turn()

    def move(self, ant, dest, direction=None):
        if self.ants.unoccupied(dest) and not dest in self.destinations:
            d = direction if direction else self.ants.direction(ant, dest)[0]
            self.ants.issue_order((ant, d))
            self.destinations.append(dest)
            return True
        return False

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
        
