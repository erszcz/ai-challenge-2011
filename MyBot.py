#!/usr/bin/env python
# coding: utf-8
# vim: sts=4 sw=4 ts=4 tw=74 et
from random import randrange, shuffle
from ants import *

from math import atan
import astar
from math import sqrt

import logging as log
log.basicConfig(format='%(message)s',
                filename='debug.log',
                level=log.DEBUG)

DIRECTIONS = ['n', 's', 'w', 'e']

def rand(seq):
    return seq[randrange(0, len(seq))]

def v2add(a, b):
    return a[0] + b[0], a[1] + b[1]

def v2sub(a, b):
    return a[0] - b[0], a[1] - b[1]

class MyBot:
    def __init__(self):
        self.ants_straight = {}
        self.ants_lefty = {}
        self.ants_tracking = {}
        self.ants_guarding = {}
        self.ants_adhoc = set()
        self.leaving = set()
        self.turns = 0
        self.enemy_hills = set()
        self.enemy_ants  = set()
        self.food        = set()
        self.my_ants     = set()
        self.my_hills    = set()
        self.ants = None
        self.guard_threshold = 0.0

    def do_setup(self, ants):
        # initialize data structures after learning the game settings
        log.info("setup")
        log.info("  viewradius2: %d", ants.viewradius2)
        log.info("  attackradius2: %d", ants.attackradius2)
        log.info("  spawnradius2: %d", ants.spawnradius2)
        pass

        self.viewradius = int(sqrt(ants.viewradius2)) + 1
        self.attackradius = int(sqrt(ants.attackradius2)) + 1

    def start_turn(self, ants):
        self.ants = ants
        self.enemy_hills = set( ( loc
                for loc, owner in ants.hill_list.items()
                if owner != MY_ANT) )
        self.enemy_ants  = set( ( (row, col)
                for (row, col), owner in ants.ant_list.items()
                if owner != MY_ANT ) )
        self.food        = set(ants.food())
        self.my_ants     = set(ants.my_ants())
        self.my_hills    = set(ants.my_hills())
        
        self.destinations = []
        self.new_straight = {}
        self.new_lefty = {}
        self.new_tracking = {}
        self.new_guarding = {}
        self.leaving.clear()

        self.turns += 1

        x = self.turns / ants.turns
        self.guard_threshold = atan(2.0 * x) / 3.0

    def end_turn(self):
        self.ants_straight = self.new_straight
        self.ants_lefty = self.new_lefty
        self.ants_tracking = self.new_tracking
        self.ants_guarding = self.new_guarding
        self.ants_adhoc.clear()

    def scan(self, ant):
        ehills, enemies, food, allies, hills = [], [], [], [], []
        for loc in self.field_of_view(ant):
            if loc in self.enemy_hills:
                ehills.append(loc)
            elif loc in self.enemy_ants:
                enemies.append(loc)
            elif loc in self.food:
                food.append(loc)
            elif loc in self.my_ants and loc != ant:
                allies.append(loc)
            elif loc in self.my_hills:
                hills.append(loc)
        distance_to = lambda target: self.ants.distance(ant, target)
        for list in (ehills, enemies, food, allies, hills):
            list.sort(key=distance_to)
        result = ehills, enemies, food, allies, hills
        log.debug("  scan: %s" % str(result))
        return ehills, enemies, food, allies, hills

    def do_turn(self, ants):
        self.start_turn(ants)

        for ant in ants.my_ants():
            distance_to = lambda target: ants.distance(ant, target)
            a_row, a_col = ant
            log.info("turn %d: ant %s" % (self.turns, ant))
            log.debug("  time remaining: %d" % ants.time_remaining())

            # scan for what's in the vicinity
            ehills, enemies, food, allies, hills = self.scan(ant)

            # look for dangers
            # - hill is to be razed? defend
            if hills and enemies:
                log.debug("  defending")
                if ant == hills[0]:
                    log.debug("    blocking the hill")
                    self.cancel_action(ant)
                else:
                    path = self.get_path(ant, hills[0], unoccupied=True)
                    if path:
                        log.debug("    found path to hill")
                        self.cancel_action(ant)
                        self.ants_tracking[ant] = path[1:]
                    else:
                        log.debug("    can't reach hill")
            # - too much enemies to cope with? flee
            elif enemies:
                log.debug("  enemies (%s) in view" % len(enemies))
                close_allies = filter( \
                    lambda a: distance_to(a) < self.attackradius, allies)
                close_enemies = filter( \
                    lambda a: distance_to(a) < self.attackradius, enemies)
                log.debug("    close enemies: %s" % close_enemies)
                log.debug("    close allies: %s" % close_allies)
                if len(close_enemies) >= len(close_allies) and \
                        distance_to(enemies[0]) < self.attackradius:
                    # let's try to flee
                    log.debug("  fleeing")
                    directions = ants.direction(enemies[0], ant)
                    done = False
                    for d in directions:
                        dest = ants.destination(ant, d)
                        if self.move(ant, dest, d):
                            done = True
                            self.cancel_action(ant)
                            self.ants_adhoc.add(ant)
                            break
                    # can't flee? try to step on enemy ant so both die
                    if not done:
                        log.debug("  can't flee")
                        directions = ants.direction(ant, enemies[0])
                        for d in directions:
                            dest = ants.destination(ant, d)
                            if dest == enemies[0]:
                                if self.move(ant, dest, d):
                                    self.cancel_action(ant)
                                    self.ants_adhoc.add(ant)
                                break
                else:
                    close_allies = filter( \
                        lambda a: distance_to(a) < self.attackradius, allies)
                    if close_allies:
                        log.debug("  attacking")
                        done = False
                        directions = ants.direction(ant, enemies[0])
                        for d in directions:
                            dest = ants.destination(ant, d)
                            if self.move(ant, dest, d):
                                done = True
                                self.cancel_action(ant)
                                self.ants_adhoc.add(ant)
                                break
            elif ehills:
                log.debug("  razing")
                path = None
                while not path and ehills:
                    self.cancel_action(ant)
                    path = self.track(ant, ehills[0], "enemy hill")
                    ehills = ehills[1:]
            elif food:
                log.debug("  harvesting")
                path = None
                while not path and food:
                    self.cancel_action(ant)
                    path = self.track(ant, food[0], "food")
                    food = food[1:]

            # new (or free) ants:
            if (not ant in self.ants_straight and
                    not ant in self.ants_lefty and
                    not ant in self.ants_tracking and
                    not ant in self.ants_guarding and
                    ant not in self.ants_adhoc):
                distance_to = lambda target: ants.distance(ant, target)
                choice = random.random()
                if choice < self.guard_threshold:
                    # guard the hill
                    log.info("  starts guarding")
                    hill = min(self.my_hills, key=distance_to)
                    self.ants_guarding[ant] = hill
                else:
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

            # tracking a path?
            if ant in self.ants_tracking:
                log.info("  is tracking")
                path = self.ants_tracking[ant]
                dest, path_tail = path[0], path[1:]
                log.debug("  dest: %s, tail: %s", dest, path_tail)
                if ants.passable(dest):
                    log.debug("  dest is passable")
                    if self.unoccupied(dest) and not dest in self.destinations:
                        direction = ants.direction(ant, dest)[0]
                        ants.issue_order((ant, direction))
                        self.leaving.add(ant)
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

            # send ants going in a straight line in the same direction
            if ant in self.ants_straight:
                log.info("  goes straight")
                direction = self.ants_straight[ant]
                n_row, n_col = ants.destination(ant, direction)
                if ants.passable((n_row, n_col)):
                    if (self.unoccupied((n_row, n_col)) and
                            not (n_row, n_col) in self.destinations):
                        ants.issue_order((ant, direction))
                        self.leaving.add(ant)
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
                            if (self.unoccupied((n_row, n_col))
                                    and not (n_row, n_col) in self.destinations):
                                ants.issue_order((ant, new_direction))
                                self.leaving.add(ant)
                                self.new_lefty[(n_row, n_col)] = new_direction
                                self.destinations.append((n_row, n_col))
                                break
                            else:
                                # have ant wait until it is clear
                                self.new_straight[ant] = RIGHT[direction]
                                self.destinations.append(ant)
                                break

        self.end_turn()

    def unoccupied(self, loc):
        owner = self.ants.ant_list.get(loc, MY_ANT-1)
        if owner == MY_ANT and loc in self.leaving:
            return True
        return self.ants.unoccupied(loc)

    def move(self, ant, dest, direction=None, skip_unoccupied=False):
        if (skip_unoccupied or self.unoccupied(dest)) \
                and not dest in self.destinations:
            d = direction if direction else self.ants.direction(ant, dest)[0]
            self.ants.issue_order((ant, d))
            self.leaving.add(ant)
            self.destinations.append(dest)
            return True
        return False

    def field_of_view(self, ant):
        vr = self.viewradius
        ar, ac = ant
        for r in xrange(ar - vr, ar + vr + 1):
            for c in xrange(ac - vr, ac + vr + 1):
                yield (r,c)

    def get_path(self, start, goal, unoccupied=False):
        #log.debug("get_path: g =\n  %s" % str(g))

        graph_h = self.ants.rows
        graph_w = self.ants.cols
        rmin, rmax = [f(start[0], goal[0]) for f in [min, max]]
        cmin, cmax = [f(start[1], goal[1]) for f in [min, max]]

        in_graph = lambda p: p[0] >= rmin and p[0] <= rmax \
            and p[1] >= cmin and p[1] <= cmax

        passable = self.ants.passable if not unoccupied else \
            lambda p: self.ants.passable(p) and self.ants.unoccupied(p)

        def adjacent(node):
            #log.debug("adjacent: %s" % str(node))
            r, c = node
            return filter(lambda p: in_graph(p) and passable(p),
                    [ (r, c-1), (r, c+1), (r-1, c), (r+1, c) ])

        p = astar.path(self.ants.map, start, goal, adjacent, self.ants.distance,
                astar.h_cross)
        
        #log.debug("get_path: path =\n  %s" % str(p))
        #dump_path("path_%s_%s_%s.dat" % (start, goal, time.time()),
                #graph, start, goal, p, passable=passable)
        return p

    def track(self, ant, target, name="target"):
        path = self.get_path(ant, target)
        if path:
            log.debug("    found path to %s" % name)
            self.ants_tracking[ant] = path[1:]
        else:
            log.debug("    can't reach %s" % name)
        return path

    def cancel_action(self, ant):
        dicts = [ self.ants_straight, self.ants_lefty, self.ants_tracking,
                  self.ants_guarding ]
        for d in dicts:
            if ant in d:
                d.pop(ant)
        if ant in self.ants_adhoc:
            self.ants_adhoc.remove(ant)

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
        
