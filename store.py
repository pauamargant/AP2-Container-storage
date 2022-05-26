"""
Template file for store.py module.
"""

from dataclasses import dataclass
from typing import Optional, TextIO, List, Tuple, Dict
import curses
import time


TimeStamp = int


Position = int


Location = Tuple[int, int]


@dataclass
class TimeRange:
    start: TimeStamp
    end: TimeStamp


@dataclass
class Container:
    """
        Class used to represent Containers

        Attributes:
        -----------
        identifier : int
        size: int
        value: int
        arrival: TimeRange
        delivery: TImeRange

        Methods:
        --------
        expired(time)
            Returns in a boolean whether a Container is expired (True) or not (False).
        deliverable(time)
            Returns in a boolean whether a Container can be delivered (True) or not (False).
    """
    identifier: int
    size: int
    value: int
    arrival: TimeRange
    delivery: TimeRange

    def expired(self, time: int) -> bool:
        '''
            Given the time returns in a boolean whether the Container is expired.

            A Container is expired if the time is equal or greater than the end of the delivery
            time of the Container.

            Parameters
            ----------
            time:int

            Returns
            -------
            bool
                True if the Container is expired, False otherwise
        '''

        if not isinstance(time, int):
            raise TypeError("time must be a positive integer")
        elif time < 0:
            raise ValueError("time must be a positive integer")
        if time >= self.delivery.end:
            return True
        else:
            return False

    def deliverable(self, time: int) -> bool:
        '''
            Given the time returns in a boolean whether the Container can be delivered.

            A Container can be delivered if the Time is equal or greater than the start
            of the delivery and smaller than the end of the delivery

            Parameters
            ----------
            time:int

            Returns
            -------
            bool
                True if the Container can be delivered, False otherwise
        '''
        if not isinstance(time, int):
            raise TypeError("time must be a positive integer")
        elif time < 0:
            raise ValueError("time must be a positive integer")
        if time >= self.delivery.start and time < self.delivery.end:
            return True
        else:
            return False

    # The following methods are not used in the current implementation of the Strategy

    def __eq__(self, other):
        return isinstance(other, Container) and self.identifier == other.identifier

    def __hash__(self):
        return self.identifier

    def __lt__(self, other):
        return self.delivery.end < self.delivery.start


class Store:
    """
        Class used to represent a Store

        The Store is represented as a list of lists of Containers.
        In order to Store Containers of size greater than 1, we represent a Container as a
        "main" Container at the position of the left corner of the Container and the corresponding "simple" Containers
        next to it (Containers with the same attributes but value -1).
        Simple containers are only used in the implementation of the class and do not affect its public methods

        Methods
        -------
        width()
            Returns the width of the Store.
        height()
            Returns the height of the Store.
        cash()
            Returns the cash of the Store.
        add_cash(amount)
            Adds an amount of cash to the cash of the Store.
        add(c,p)
            Adds a Container c to the Position p of the Store.
        remove(c)
            Removes Container c from the Store.
        def move(c,p)
            Moves Container c to the Position p of the Store.
        def containers()
            Returns a list with all the Containers in the Store.
        def removable_containers()
            Returns a list with all the removable containers in the Store.
        def top_container(p)
            Returns the top container at Position p.
        def location(c)
            Returns the Location of Container c
        def can_add(c,p)
            Returns in a boolean whether Container c can be added to Position p.
        def can_remove(c)
            Returns in a boolean whether Container c can be removed.
        def get_column(p)
            Returns in a list the containers at Position p
        def column_height(p)
            Returns the height of position p

    """

    def __init__(self, width: int):
        """
        Parameters
        ----------
        width : int
            The width of the Store
        """
        if not isinstance(width, int):
            raise TypeError("width must be positive integer")
        elif width <= 0:
            raise ValueError("width must be an integer greater than 0")
        self._width: int = width
        self._cash: int = 0
        # Containers are stored as a list in which element of the list is a column of containers
        self._containers: List[List[Container]] = [[] for _ in range(width)]
        # We store each container location in a dictionary which uses container identifiers as key
        self._container_loc: Dict[int, Location] = dict()

    def width(self) -> int:
        """
            Returns the width of the Store

            Returns
            -------
            int
                width of the Store

        """
        return self._width

    def height(self) -> int:
        """
            Returns the height of the Store

            Returns
            -------
            int
                height of the Store
        """
        max_height: int = 0
        col: List
        for col in self._containers:
            if len(col) > max_height:
                max_height = len(col)
        return max_height

    def cash(self) -> int:
        """
            Returns the amount of cash of the Store

            Returns
            -------
            int
                cash of the Store
        """
        return self._cash

    def add_cash(self, amount: int) -> None:
        """
            Increases by a given amount the cash of the Store

            Parameters
            ----------
            amount: int
                Amount of cash to add to the Store
        """
        if not isinstance(amount, int):
            raise TypeError('Amount must be an integer')
        self._cash += amount

    def add(self, c: Container, p: Position) -> None:
        """
            Adds a given Container c to the position p of the Store

            Checks if a container C can be added to the Position p and if it's possible ads
            the container and its simple containers to the Positions [p,...,p+size-1].
                For example, if a container of size 4 is added to Position p, a main container
                will be added to position p and three simple containers will be added to positions p+1,
                p+2 and p+3.

            Precondition
            ------------
            c is a container with value != -1

            Parameters
            ----------
            c: Container
                The Container which has to be (if possible) added
            p: Position
                The position to which the container has to be (if possible) added

        """
        # We check the parameters
        if not isinstance(c, Container):
            raise TypeError('c must be a Container')
        if not isinstance(p, Position):
            raise TypeError('p must be a Position')

        if self.can_add(c, p):  # We check if it can be added
            self._containers[p].append(c)  # We add the main Container
            self._container_loc.update({c.identifier: (
                len(self._containers[p])-1, p)})
            for i in range(p+1, p+c.size):  # We add the simple Containers
                dumb_container: Container = Container(
                    c.identifier, 1,  -1, c.arrival, c.delivery)
                self._containers[i].append(dumb_container)

    def remove(self, c: Container) -> None:
        '''
        Removes, if possible, a Container c.

        Given a Container c, if it can be removed the container and its simple containers
        are removed.

        Parameters
        ----------
        c: Container
            The Container which has to be (if possible) removed
        '''
        # We check the parameters
        if not isinstance(c, Container):
            raise TypeError('c must be a Container')

        if (c is not None and c.value > -1):
            if self.can_remove(c):  # We check if it can be removed
                loc: Location = self.location(c)
                for i in range(loc[1], loc[1]+c.size):  # We remove it
                    self._containers[i].pop()
                self._container_loc.pop(c.identifier)

    def move(self, c: Container, p: Position) -> None:
        '''
            Given a Container C and a Position p, the Container C is (if possible) moved to
            the Position p

            Given a Container C we check that its value >-1. If it can be removed and added to Position
            p we remove it and then add it again to Position p.

            Parameters
            ----------
            c: Container
                The Container which has to be moved
            p: Position
                The Position to which the Container has to be moved

        '''
        # We check the parameters
        if not isinstance(c, Container):
            raise TypeError('c must be a Container')
        if not isinstance(p, Position):
            raise TypeError('p must be a Position')
        if (p < 0 or p >= self.width()):
            raise ValueError('p must be >= 0 and < width')

        if(c is not None and c.value != -1):  # We check that c is valid
            if(self.can_remove(c) and self.can_add(c, p)):  # We check that it can be removed and added
                self.remove(c)
                self.add(c, p)

    def containers(self) -> List[Container]:
        '''
            Returns a list with all the Containers (main containers)

            Returns
            -------
            List[Container]
                List with all the Containers in the Store

        '''

        containers: List = []
        for column in self._containers:
            for c in column:
                if c.value != -1:  # We add only the main containers
                    containers.append(c)
        return containers

    def removable_containers(self) -> List[Container]:
        '''
            Returns a list with all the removable Containers in the Store

            Returns
            -------
            List[Containers]
        '''
        removable: List = []
        for i in range(self.width()):
            top = self.top_container(i)
            if top is not None:
                if self.can_remove(top):
                    removable.append(top)
        return removable

    def top_container(self, p: Position) -> Optional[Container]:
        ''''
            Returns the top Container in Position p

            Given a Position p, returns the top Container at that Position.
            If there are no Containers at position P, returns None.

            If at Position p we find a simple container, we return the corresponding main
            container (simple containers are only used in the implementation of the class).

            Parameters
            ----------
            p: Position

            Returns
            -------
            Optional[Container]
                Top Container at Position p (None if there is no Container)

        '''
        if not isinstance(p, Position):
            raise TypeError('p must be a Position')
        if (p < 0 or p >= self.width()):
            raise ValueError('p must be >= 0 and < width')

        # We check if there are no containers (height 0) at position p
        if len(self._containers[p]) != 0:
            # we find the left corner of the Container (the corresponding main container)
            while self._containers[p][-1].value == -1 and p >= 0:
                p -= 1
            return self._containers[p][-1]
        else:  # If there are no containers in the Position we return None
            return None

    def location(self, c: Container) -> Location:
        '''
            Returns the Location of a Container C
            Returns (-1,-1) if c not in Store

            Parameters
            ----------
            c: Container

            Returns
            -------
            Location
                Location of c, (-1,-1) if c is not in the Store

        '''
        if not isinstance(c, Container):
            raise TypeError('c must be a Container')
        # We return the container location. If it is not found in the dictionary we return (-1,-1)
        return self._container_loc.get(c.identifier, (-1, -1))

    def can_add(self, c: Container, p: Position) -> bool:
        '''
        Checks if a Conainter c can be added to the Position p and returns a Boolean

        Given a Container C checks if C can be added to Position p. Checks whether it has a
        valid base (it needs a flat base) and fits in the Store (p+c.size<= Store width).
        Returns True if c can be added, False otherwise

        Parameters
        ----------
        c: Container
        p: Position

        Returns
        -------
        bool
            True if c can be added to p, False otherwise

        '''
        if not isinstance(c, Container):
            raise TypeError('c must be a Container')
        if not isinstance(p, Position):
            raise TypeError('p must be a Position')
        if p < 0:
            raise ValueError('p must be >= 0')

        # We check that it fits in the Container
        if p+c.size > self.width():
            return False
        else:
            height: int = len(self._containers[p])
            # We check that it has a flat base by checking the heights
            for i in range(p+1, p+c.size):
                if len(self._containers[i]) != height:
                    return False
            return True

    def can_remove(self, c: Container) -> bool:
        '''
            Given a container checks whether it can be removed and returns a boolean.

            Given a Container we find its location and check if there are no containers on
            top of it and therefore it can be removed. 

            Precondition
            ------------
            c is in the Store

            Parameters
            ----------
            c: Container
                The Container we want to check

            Returns
            -------
            bool
                True if c can be removed, False otherwise
        '''
        if not isinstance(c, Container):
            raise TypeError('c must be a Container')
        # We find the location of c. If c is not in the store l will be (-1,-1)
        l: Location = self.location(c)

        # We check if c is a valid container to be removed
        if c is None or c.value == -1 or l == (-1, -1):
            return False
        for i in range(l[1], l[1]+c.size):
            #  We check that there are not other containers on top of c.
            #  If there are other containers, height at position p isn't the heigt of c.
            if len(self._containers[i])-1 is not l[0]:
                return False
        return True

    ######################
    ### CUSTOM METHODS ###
    ######################

    def get_column(self, p: Position) -> list[Container]:
        '''
            Returns a list with the Containers at Position p

            Given a Position p, returns a list with the containers at Poisiton
            p. The containers appear from bottom to top

            Preconditions
            -------------
            p must be a valid Position (0<=p<width)
            Parameters
            ----------
            p: Position

            Returns
            -------
            List[Containers]
        '''
        if not isinstance(p, Position):
            raise TypeError('p must be a Position')
        if(p < 0 or p >= self.width()):
            raise ValueError('p must be a valid Position (0<=p<width)')
        return self._containers[p]

    def get_column_height(self, p: Position) -> int:
        '''
            Returns the height of the Column of Containers at Position p

            Parameters
            ----------
            p: Position

            Returns
            -------
            height: int
        '''
        if not isinstance(p, Position):
            raise TypeError('p must be a Position')
        if(p < 0 or p >= self.width()):
            raise ValueError('p must be a valid Position (0<=p<width)')
        return len(self._containers[p])

    # Already implemented methods

    def write(self, stdscr: curses.window, caption: str = ''):

        maximum = 15  # maximum number of rows to write
        delay = 0.05  # delay after writing the state
        # start: clear screen
        stdscr.clear()

        # write caption
        stdscr.addstr(0, 0, caption)
        # write floor
        stdscr.addstr(maximum + 3, 0, '—' * 2 * self.width())
        # write cash
        stdscr.addstr(maximum + 4, 0, '$: ' + str(self.cash()))

        # write containers
        for c in self.containers():
            row, column = self.location(c)
            if row < maximum:
                # some random color depending on the identifier of the container
                p = 1 + c.identifier * 764351 % 250
                stdscr.addstr(maximum - row + 2, 2 * column,
                              '  ' * c.size, curses.color_pair(p))
                stdscr.addstr(maximum - row + 2, 2 * column,
                              str(c.identifier % 100), curses.color_pair(p))

        # done
        stdscr.refresh()
        time.sleep(delay)


class Logger:

    """Class to log store actions to a file."""

    _file: TextIO

    def __init__(self, path: str, name: str, width: int):
        self._file = open(path, 'w')
        print(0, 'START', name, width, file=self._file)

    def add(self, t: TimeStamp, c: Container, p: Position):
        print(t, 'ADD', c.identifier, p, file=self._file)

    def remove(self, t: TimeStamp, c: Container):
        print(t, 'REMOVE', c.identifier, file=self._file)

    def move(self, t: TimeStamp, c: Container, p: Position):
        print(t, 'MOVE', c.identifier, p, file=self._file)

    def cash(self, t: TimeStamp, cash: int):
        print(t, 'CASH', cash, file=self._file)


def read_containers(path: str) -> List[Container]:
    """Returns a list of containers read from a file at path."""

    with open(path, 'r') as file:
        containers: List[Container] = []
        for line in file:
            identifier, size, value, arrival_start, arrival_end, delivery_start, delivery_end = map(
                int, line.split())
            container = Container(identifier, size, value, TimeRange(
                arrival_start, arrival_end), TimeRange(delivery_start, delivery_end))
            containers.append(container)
        return containers


def check_and_show(containers_path: str, log_path: str, stdscr: Optional[curses.window] = None):
    """
    Check that the actions stored in the log at log_path with the containers at containers_path are legal.
    Raise an exception if not.
    In the case that stdscr is not None, the store is written after each action.
    """

    # get the data
    containers_list = read_containers(containers_path)
    containers_map = {c.identifier: c for c in containers_list}
    log = open(log_path, 'r')
    lines = log.readlines()

    # process first line
    tokens = lines[0].split()
    assert len(tokens) == 4
    assert tokens[0] == "0"
    assert tokens[1] == "START"
    name = tokens[2]
    width = int(tokens[3])
    last = 0
    store = Store(width)
    if stdscr:
        store.write(stdscr)

    # process remaining lines
    for line in lines[1:]:
        tokens = line.split()
        time = int(tokens[0])
        what = tokens[1]
        assert time >= last
        last = time

        if what == "CASH":
            cash = int(tokens[2])
            assert cash == store.cash()

        elif what == "ADD":
            identifier, position = int(tokens[2]), int(tokens[3])
            store.add(containers_map[identifier], position)

        elif what == "REMOVE":
            identifier = int(tokens[2])
            container = containers_map[identifier]
            store.remove(container)
            if container.delivery.start <= time < container.delivery.end:
                store.add_cash(container.value)

        elif what == "MOVE":
            identifier, position = int(tokens[2]), int(tokens[3])
            store.move(containers_map[identifier], position)

        else:
            assert False

        if stdscr:
            store.write(stdscr, f'{name} t: {time}')
