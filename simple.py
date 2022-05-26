"""
Template file for simple.py module.
"""
from store import *
import curses
import sys


class Strategy:

    """
        Implementation of the simple strategy.

        For each size of containers (1,2,3,4) we have two stacks of containers.
        Each times a Container arrives and while the time is less than the
        end of the arrival of that container, the following actions are executed:
        1. We add the new container to the corresponding position (which depends on its size)
        2. While there is time left, for each size:
            i. All the containers in the first stack of its size are moved to the second column
               (from top to bottom). If we find any container which is expired we remove it, if any
               can be sold it is sold.
            ii.We move (from top to bottom) all the containers in the second pile to the first pile.
              If we find any container which is expired we remove it, if any can be sold it is sold.
        3. If there is time left we go back to step 2. If there is time left but the Store is empty
           we advance the time to the end of the arrival.

        In order to execute the strategy we have the following attributes:

        Attributes
        ----------
        log: Logger
            Used to log the actions in a file.
        _store: Store
            The Store in which we execute the Strategy.
        _time: int
            The current time
        _arrival_end: int
            The arrival.end time of the incoming container

        Methods
        -------
        cash()
            Returns the cash in the Store of the Strategy
        calc_position(s)
            Calculates the position in which to add a new Container of size s, according
            to how the simple strategy works.
        time_increment()
            Increments by one unit of time the time in the Strategy
        exec()
            Executes the strategy each time a new container arrives
        deliver_container(c)
            Delivers a Container  c
        remove_container(c)
            Removes (without delivering) a container c
        move_column(p1,p2)
            Moves all the containers at Position p1 to Position p2

        Preconditions
        -------------
        -Assumes width is at least 20


    """

    def __init__(self, width: int, log_path: str):
        # We initialize the log, store, time and arrival_end
        self.log = Logger(log_path, "simple_strategy", width)
        self._store: Store = Store(width)
        self._time: int = 0
        self._arrival_end: int = 0

    def cash(self) -> int:
        '''
        Returns the cash of the Store

        Returns
        -------
        cash: int
        '''
        return self._store.cash()

    def calc_position(self, s: int) -> int:
        '''
        Calculates the position in which to add a new Container depending on its size
        accordint to the simple strategy.

        Parameters
        ----------
        s: int

        Returns
        -------
        Position


        '''
        if not isinstance(s, int):
            raise TypeError("s must be an Integer")
        if(not s > 0 and s <= 4):
            raise ValueError("Size must be 0<s<5")
        if s == 1:
            return 0
        elif s == 2:
            return 2
        elif s == 3:
            return 6
        elif s == 4:
            return 12

        return -1

    def time_increment(self):
        '''
        Increments the time of the Strategy by one unit of time
        '''
        self._time += 1

    def exec(self, c: Container):
        '''
        Executes the simple Strategy each time a new Container arrives.

        The simple strategy consist in:

        1. We add the new container to the corresponding position (which depends on its size)
        2. While there is time left, for each size:
            i. All the containers in the first stack of its size are moved to the second column
               (from top to bottom). If we find any container which is expired we remove it, if any
               can be sold it is sold.
            ii.We move (from top to bottom) all the containers in the second pile to the first pile.
              If we find any container which is expired we remove it, if any can be sold it is sold.
        3. If there is time left we go back to step 2. If there is time left but the Store is empty
           we advance the time to the end of the arrival.

        Parameters
        ----------
        c: Container
            The Container to be added 


        '''
        if not isinstance(c, Container):
            raise TypeError("c must be a Container")
        # We add the new Container
        self._arrival_end = c.arrival.end
        s = c.size
        p = self.calc_position(s)
        self._store.add(c, p)

        self.log.add(self._time, c, p)
        self.time_increment()

        # While we have time we move each container size column to the other column
        # of the same size
        while self._time < self._arrival_end and self._store.height() != 0:
            for i in range(1, 4+1):  # We move the piles for all sizes
                p = self.calc_position(i)
                if self._time < self._arrival_end:
                    self.move_column(p, p+i)
                    if self._time < self._arrival_end:
                        self.move_column(p+i, p)
        # If the Store is empty we increment the time until the time of arrival of the
        # next container
        while self._time < self._arrival_end:
            self.time_increment()

    def deliver_container(self, c: Container) -> None:
        '''
        Delivers a Container and logs the time and cash 

        -Preconditions: The Container c can be removed and delivered

        Parameters
        ----------
        c: Container
        '''
        if not isinstance(c, Container):
            raise TypeError("c must be a Container")

        self._store.add_cash(c.value)
        self._store.remove(c)
        self.log.remove(self._time, c)
        self.log.cash(self._time, self.cash())
        self.time_increment()

    def remove_container(self, c: Container) -> None:
        '''
        Removes a Container and logs the time and cash

        -Preconditions: The Container c can be removed

        Parameters
        ----------
        c: Container

        '''
        if not isinstance(c, Container):
            raise TypeError("c must be a Container")
        self._store.remove(c)
        self.log.remove(self._time, c)
        self.log.cash(self._time, self.cash())
        self.time_increment()

    def move_column(self, p1: Position, p2: Position):
        '''
        Moves all the containers of the column p1 to the column p2 while time<arrival_end.
        The containers are moved from top to bottom.

        Parameters: 
        -----------
        p1: Position
        p2: Position
        '''
        # We check the parameters
        if not isinstance(p1, int):
            raise TypeError("p1 must be an integer")
        if not isinstance(p2, int):
            raise TypeError("p2 must be an integer")
        if (not(p2 >= 0 and p1 >= 0) and not(p2 < self._store.width() and p1 < self._store.width())):
            raise ValueError("p1 and p2 must be valid positions")
        # We find the top container at p1
        top: Optional[Container] = self._store.top_container(p1)
        while top is not None and self._time < self._arrival_end:
            # We first check if the container can be delivered or is expired
            if top.expired(self._time):
                self.remove_container(top)
            elif top.deliverable(self._time):
                self.deliver_container(top)
            else:
                # We move the container to Position p2
                self._store.move(top, p2)
                self.log.move(self._time, top, p2)
                self.time_increment()
            # We find the current top container at p1
            top = self._store.top_container(p1)


def init_curses():
    """Initializes the curses library to get fancy colors and whatnots."""

    curses.curs_set(0)
    curses.start_color()
    curses.use_default_colors()
    for i in range(0, curses.COLORS):
        curses.init_pair(i + 1, curses.COLOR_WHITE, i)


def execute_strategy(containers_path: str, log_path: str, width: int):
    """Execute the strategy on an empty store of a certain width reading containers from containers_path and logging to log_path."""

    containers = read_containers(containers_path)
    strategy = Strategy(width, log_path)
    for container in containers:
        strategy.exec(container)


def main(stdscr: curses.window):
    """main script"""

    init_curses()

    containers_path = sys.argv[1]
    log_path = sys.argv[2]
    width = int(sys.argv[3])

    execute_strategy(containers_path, log_path, width)
    check_and_show(containers_path, log_path, stdscr)


# start main script when program executed
if __name__ == '__main__':
    curses.wrapper(main)
