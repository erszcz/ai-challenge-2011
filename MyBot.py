#!/usr/bin/env python
# coding: utf-8
# vim: sts=4 sw=4 ts=4 tw=74 et
from random import choice, randrange
from ants import *
import sys
import logging
from optparse import OptionParser

#DEBUG=True
DEBUG=False

def dbg(msg):
    if DEBUG:
        import os
        logfile = os.path.join(os.path.dirname(__file__), 'debug.log')
        with file(logfile, 'a') as f:
            f.write(msg + "\n")

def rand(seq):
    return seq[randrange(0, len(seq))]

class MyBot:
    def __init__(self):
        self.ants_straight = {}
        self.ants_lefty = {}

    def do_setup(self, ants):
        # initialize data structures after learning the game settings
        pass

    def do_turn(self, ants):
        destinations = []
        new_straight = {}
        new_lefty = {}
        for a_row, a_col in ants.my_ants():
            dbg("ant %d,%d" % (a_row, a_col))

            nearby = lambda targets: [ (r,c) for (r,c) in targets \
                 if ((a_row-r)**2 + (a_col-c)**2) < ants.viewradius2 ]

            # look for nearby food
            #food = nearby(ants.food())

            # look for nearby enemies
            #enemies = nearby( ((x,y) for (x,y), owner in ants.enemy_ants()) )

            # send new ants in a straight line
            if (not (a_row, a_col) in self.ants_straight and
                    not (a_row, a_col) in self.ants_lefty):
                direction = rand(['n', 's', 'w', 'e'])
                self.ants_straight[(a_row, a_col)] = direction

            # send ants going in a straight line in the same direction
            if (a_row, a_col) in self.ants_straight:
                direction = self.ants_straight[(a_row, a_col)]
                n_row, n_col = ants.destination((a_row, a_col), direction)
                if ants.passable((n_row, n_col)):
                    if (ants.unoccupied((n_row, n_col)) and
                            not (n_row, n_col) in destinations):
                        ants.issue_order(((a_row, a_col), direction))
                        new_straight[(n_row, n_col)] = direction
                        destinations.append((n_row, n_col))
                    else:
                        # pause ant, turn and try again next turn
                        new_straight[(a_row, a_col)] = LEFT[direction]
                        destinations.append((a_row, a_col))
                else:
                    # hit a wall, start following it
                    self.ants_lefty[(a_row, a_col)] = RIGHT[direction]

            # send ants following a wall, keeping it on their left
            if (a_row, a_col) in self.ants_lefty:
                direction = self.ants_lefty[(a_row, a_col)]
                directions = [LEFT[direction], direction, RIGHT[direction],
                    BEHIND[direction]]
                # try 4 directions in order, attempting to turn left at corners
                for new_direction in directions:
                    n_row, n_col = \
                        ants.destination((a_row, a_col), new_direction)
                    if ants.passable((n_row, n_col)):
                        if (ants.unoccupied((n_row, n_col)) and
                                not (n_row, n_col) in destinations):
                            ants.issue_order(((a_row, a_col), new_direction))
                            new_lefty[(n_row, n_col)] = new_direction
                            destinations.append((n_row, n_col))
                            break
                        else:
                            # have ant wait until it is clear
                            new_straight[(a_row, a_col)] = RIGHT[direction]
                            destinations.append((a_row, a_col))
                            break

        # reset lists
        self.ants_straight = new_straight
        self.ants_lefty = new_lefty

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
        
