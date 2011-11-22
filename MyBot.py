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

TIME_MARGIN_MEDIUM = 200
TIME_MARGIN_CRITICAL = 0.33 * TIME_MARGIN_MEDIUM
TIME_SEARCH = 0.5 * TIME_MARGIN_MEDIUM

def rand(seq):
    return seq[randrange(0, len(seq))]

def v2add(a, b):
    return a[0] + b[0], a[1] + b[1]

def v2sub(a, b):
    return a[0] - b[0], a[1] - b[1]

def make_in_graph(rmin, rmax, cmin, cmax):
    in_graph = lambda p: p[0] >= rmin and p[0] < rmax \
        and p[1] >= cmin and p[1] < cmax
    return in_graph

def circle(loc, radii):
  if not hasattr(radii, "__iter__"):
    # we got a number, not sequence of them
    radii = [radii]
  for radius in radii:
    r,c = loc
    for c1 in xrange(c - radius, c + radius + 1):
      yield r - radius, c1
    for r1 in xrange(r - radius + 1, r + radius):
      yield r1, c + radius
    for c1 in xrange(c + radius, c - radius - 1, -1):
      yield r + radius, c1
    for r1 in xrange(r + radius - 1, r - radius, -1):
      yield r1, c - radius

class MyBot:
    def __init__(self):
        self.ants_straight = {}
        self.ants_lefty = {}
        self.ants_tracking = {}
        self.ants_guarding = {}
        self.leaving = set()
        self.turn = 0
        self.food = []
        self.enemy_hills = []
        self.my_hills = []
        self.ants = None
        self.guard_threshold = 0.0
        self.paths = {}
        self.__region_c2w = {}
        self.__region_w2c = {}

    def do_setup(self, ants):
        # initialize data structures after learning the game settings
        log.info("setup")
        log.info("  viewradius2  : %d", ants.viewradius2)
        log.info("  attackradius2: %d", ants.attackradius2)
        log.info("  spawnradius2 : %d", ants.spawnradius2)
        log.info("  map.rows     : %d", ants.rows)
        log.info("  map.cols     : %d", ants.cols)

        self.viewradius = int(sqrt(ants.viewradius2)) + 1
        self.attackradius = int(sqrt(ants.attackradius2)) + 1

        self.regions = {}
        self.region_waypoints = set()
        self.regionh = self.regionw = self.viewradius
        for r in xrange(self.regionh // 2, ants.rows, self.regionh):
            for c in xrange(self.regionw // 2, ants.cols, self.regionw):
                self.regions[(r,c)] = self.turn
                self.region_waypoints.add((r,c))
        self.nregions = len(self.regions)

        #self.max_path_len = (ants.rows + ants.cols) / 2 * 3
        self.max_path_len = (ants.rows + ants.cols) / 2

    def start_turn(self, ants):
        self.ants = ants
        self.food = ants.food()
        self.enemy_hills = [loc for loc, owner in ants.enemy_hills()]
        self.my_hills = ants.my_hills()
        
        self.destinations = []
        self.new_straight = {}
        self.new_lefty = {}
        self.new_tracking = {}
        self.new_guarding = {}
        self.leaving.clear()

        self.turn += 1

        x = self.turn / ants.turns
        self.guard_threshold = atan(2.0 * x) / 3.0

        log.debug("start turn: %s" % self.turn)
        log.debug("  time remaining: %d" % ants.time_remaining())
        log.debug("  ants straight: %s" % len(self.ants_straight))
        log.debug("  ants lefty   : %s" % len(self.ants_lefty))
        log.debug("  ants tracking: %s" % len(self.ants_tracking))
        log.debug("  ants guarding: %s" % len(self.ants_guarding))
        log.debug("  my ants      : %s" % len(ants.my_ants()))

    def end_turn(self):
        log.debug("  end turn: %s" % self.turn)
        log.debug("    time remaining: %d" % self.ants.time_remaining())

        self.ants_straight = self.new_straight
        self.ants_lefty = self.new_lefty
        self.ants_tracking = self.new_tracking
        self.ants_guarding = self.new_guarding

        for ant in self.ants.my_ants():
            region = self.region_for(ant)
            # we check it, because some region may have been removed due to
            # its centre being impassable; we don't want to add it again
            if self.regions.has_key(region):
                self.regions[region] = self.turn

    def do_turn(self, ants):
        self.start_turn(ants)

        for ant in ants.my_ants():
            distance_to = lambda target: ants.distance(ant, target)
            a_row, a_col = ant
            log.info("turn %d: ant %s" % (self.turn, ant))
            log.debug("  time remaining: %d" % ants.time_remaining())
            if ants.time_remaining() < TIME_MARGIN_CRITICAL:
                log.info("  time remaining is below %s, skipping all actions"
                        % TIME_MARGIN_CRITICAL)
                break

            targets = self.scan(ant)
            if targets:
                target, targets = targets[0], targets[1:]
                path = self.get_path(ant, target)
                while not path and targets:
                    log.debug("  target %s is unreachable, trying again"
                            % str(target))
                    target, targets = targets[0], targets[1:]
                    path = self.get_path(ant, target)
                if path:
                    log.info("  target chosen: %s" % str(target))
                    log.debug("  time remaining: %d" % ants.time_remaining())
                    if ant in self.ants_tracking:
                        oldtarget = self.ants_tracking[ant][-1]
                        log.debug("  old target present %s" % str(oldtarget))
                        path.extend(self.get_path(target, oldtarget)[1:])
                    self.cancel_actions(ant)
                    self.ants_tracking[ant] = path[1:]
                else:
                    log.info("  no target is reachable")

            # new (or free) ants:
            fallback = False
            if (not ant in self.ants_straight and
                    not ant in self.ants_lefty and
                    not ant in self.ants_tracking and
                    not ant in self.ants_guarding):
                choice = random.random()
                if choice < self.guard_threshold:
                    # guard the hill
                    if self.my_hills:
                        log.info("  starts guarding")
                        hill = min(self.my_hills, key=distance_to)
                        self.ants_guarding[ant] = hill
                    else:
                        log.info("  no hills to guard!")
                        fallback = True
                elif ants.time_remaining() > TIME_MARGIN_MEDIUM:
                    # choose region to reach
                    log.info("  choosing region")
                    regions = self.regions.items()
                    rweight = self.region_weight(ant)
                    log.debug("  regions: %s" % \
                        sorted([(rweight(r), distance_to(r[0]), r) \
                            for r in regions]))
                    start = self.region_for(ant)
                    start = start if start else ant
                    region, t = min(regions, key=rweight)
                    regions.remove((region,t))
                    path = self.get_path(start, region, local=False,
                            max_time=TIME_SEARCH)
                    while not path and regions \
                            and ants.time_remaining() > TIME_MARGIN_MEDIUM:
                        if not ants.passable(region):
                            # if region centre is not passable, don't ever
                            # make it a path destination again
                            log.debug("  region centre impassable: %s"
                                    % str(region))
                            log.debug("  time remaining: %d" % ants.time_remaining())
                        log.debug("  region %s is unreachable, trying again"
                                % str(region))
                        if ants.time_remaining() < TIME_MARGIN_MEDIUM:
                            log.debug("  no time for retry")
                            break
                        region, t = min(regions, key=rweight)
                        regions.remove((region,t))
                        path = self.get_path(start, region, local=False,
                                max_time=TIME_SEARCH)
                    if path:
                        if start != ant and (start, region) not in self.paths:
                            self.paths[(start, region)] = path
                            self.paths[(region, start)] = list(reversed(path))
                        maxdist = self.regionh + self.regionw
                        join_index, _ = \
                            min(zip(xrange(maxdist), path[:maxdist]),
                                key=lambda z: distance_to(z[1]))
                        #log.debug("  join_index: %s" % join_index)
                        #log.debug("  path: %s" % path)
                        #log.debug("  path[join_index]: %s" % \
                                #str(path[join_index]))
                        path1 = self.get_path(ant, path[join_index],
                                local=False, max_path_len=maxdist)
                        log.debug("  path1: %s" % path1)
                        if path1:
                            path = path1 + path[join_index+1:]
                        else:
                            path = []
                        if path:
                            log.info("  region chosen: %s" % str(region))
                            log.debug("  time remaining: %d" % ants.time_remaining())
                            self.cancel_actions(ant)
                            self.ants_tracking[ant] = path[1:]
                        else:
                            fallback = True
                            log.info("  can't reach interregional path")
                    else:
                        fallback = True
                        log.info("  no region selected")
                else:
                    fallback = True
                    log.info("  less than %sms left, skipping pathfinding"
                            % TIME_MARGIN_MEDIUM)
            if fallback:
                log.info("  starts going straight")
                direction = rand(DIRECTIONS)
                self.ants_straight[ant] = direction
                del fallback


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
                if path and (path[-1] in self.food
                             or path[-1] in self.enemy_hills
                             or path[-1] in self.region_waypoints):
                    dest, path_tail = path[0], path[1:]
                    log.debug("  dest: %s, tail: %s", dest, path_tail)
                    log.debug("  path length: %s" % (len(path_tail) + 1))
                    if ants.passable(dest):
                        log.debug("  dest is passable")
                        if self.unoccupied(dest) and dest not in self.destinations:
                            direction = ants.direction(ant, dest)[0]
                            ants.issue_order((ant, direction))
                            log.debug("  move order: %s" % \
                                    str(ants.destination(ant, direction)))
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
                else:
                    log.debug("  path broken, tracking cancelled")

            # send ants going in a straight line in the same direction
            if ant in self.ants_straight:
                log.info("  goes straight")
                direction = self.ants_straight[ant]
                n_row, n_col = ants.destination(ant, direction)
                if ants.passable((n_row, n_col)):
                    if (self.unoccupied((n_row, n_col)) and
                            not (n_row, n_col) in self.destinations):
                        ants.issue_order((ant, direction))
                        log.debug("  move order: %s" % \
                                str(ants.destination(ant, direction)))
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
                                log.debug("  move order: %s" % \
                                    str(ants.destination(ant, new_direction)))
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
        #log.debug("  unoccupied:")
        #log.debug("    owner: %s" % owner)
        #log.debug("    loc in self.leaving: %s" % (loc in self.leaving))
        if owner == MY_ANT and loc in self.leaving:
            return True
        return self.ants.unoccupied(loc)

    def move(self, ant, dest, direction=None):
        if self.unoccupied(dest) and not dest in self.destinations:
            d = direction if direction else self.ants.direction(ant, dest)[0]
            self.ants.issue_order((ant, d))
            log.debug("  move order: %s" % \
                    str(self.ants.destination(ant, d)))
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

    def get_path(self, start, goal, local=True, unoccupied=False,
            max_path_len=None, max_time=None):
        #log.debug("get_path: g =\n  %s" % str(g))

        if (start, goal) in self.paths:
            log.debug("    returning cached path: %s -> %s" % (start, goal))
            return self.paths[(start, goal)]

        graph_h = self.ants.rows
        graph_w = self.ants.cols
        rmin, rmax = [f(start[0], goal[0]) for f in [min, max]]
        cmin, cmax = [f(start[1], goal[1]) for f in [min, max]]

        in_graph = make_in_graph(rmin, rmax+1, cmin, cmax+1)

        passable = self.ants.passable if not unoccupied else \
            lambda p: self.ants.passable(p) and self.ants.unoccupied(p)

        if local:
            def adjacent(node):
                #log.debug("adjacent: %s" % str(node))
                r, c = node
                return filter(lambda p: in_graph(p) and passable(p),
                        [ (r, c-1), (r, c+1), (r-1, c), (r+1, c) ])
        else:
            def adjacent(node):
                #log.debug("adjacent: %s" % str(node))
                r, c = node
                return filter(passable, [ (r, (c-1) % self.ants.cols),
                                          (r, (c+1) % self.ants.cols),
                                          ((r-1) % self.ants.rows, c),
                                          ((r+1) % self.ants.rows, c) ])

        p = astar.path(self.ants.map, start, goal, adjacent, self.ants.distance,
                astar.h_simple, max_path_len=max_path_len,
                max_time=max_time)
                #astar.h_cross)
        
        #log.debug("get_path: path =\n  %s" % str(p))
        #dump_path("path_%s_%s_%s.dat" % (start, goal, time.time()),
                #graph, start, goal, p, passable=passable)
        return p

    def cancel_actions(self, ant):
        dicts = { "going straight": self.ants_straight,
                  "going lefty"   : self.ants_lefty,
                  "tracking"      : self.ants_tracking,
                  "guarding"      : self.ants_guarding }
        for action, d in dicts.items():
            if ant in d:
                log.debug("  cancelled: %s" % action)
                d.pop(ant)

    def region_for(self, loc):
        r,c = loc
        regionr, regionc = (
                r // self.regionh * self.regionh + self.regionh // 2,
                c // self.regionw * self.regionw + self.regionw // 2 )
        if regionr >= self.ants.rows:
            regionr -= self.regionh
        if regionc >= self.ants.cols:
            regionc -= self.regionw
        if (regionr, regionc) in self.__region_c2w:
            return self.__region_c2w[(regionr, regionc)]
        in_graph = make_in_graph(0, self.ants.rows, 0, self.ants.cols)
        if (regionr, regionc) in self.regions \
                and not self.ants.passable((regionr, regionc)):
            waypoint = None
            for p in circle(loc,
                    xrange(1, (self.regionh + self.regionw) // 2 + 1)):
                if in_graph(p) and self.ants.passable(p):
                    waypoint = p
                    break
            if waypoint:
                log.debug("  waypoint %s found for region %s"
                        % (waypoint, (regionr, regionc)))
                self.__region_c2w[(regionr, regionc)] = waypoint
                self.__region_w2c[waypoint] = (regionr, regionc)
                ts = self.regions[(regionr, regionc)]
                self.regions[waypoint] = ts
            log.debug("  deleting impassable region centre: %s"
                    % str((regionr, regionc)))
            del self.regions[(regionr, regionc)]
            return waypoint if waypoint else None
        elif (regionr, regionc) not in self.regions:
            return None
        return regionr, regionc

    def region_weight(self, ant):
        def weight(r):
            loc, ts = r
            return ts, self.ants.distance(ant, loc)
        return weight

    def scan(self, ant):
        targets = []
        for loc in self.field_of_view(ant):
            if loc in self.enemy_hills or loc in self.food:
                targets.append(loc)
        distance_to = lambda target: self.ants.distance(ant, target)
        targets.sort(key=distance_to)
        log.debug("  scan: %s" % str(targets))
        return targets


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
        
