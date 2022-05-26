"""
Template file for expert.py module.
"""

from store import *
import curses
import sys
T = 2995


class Strategy:

    """Implementation of the expert strategy.

        The expert strategy conssit on dividing the Store in the parts:
        -Working area: 
            -Divided in two parts: Positions [s1,...,s2-1] and Positions [s2...s3-1]
        -Waiting area:
            -Positions [s3,....s4-1]

        We divide the time of operation of the strategy in Stages. When the first container arrives
        we "activate" the first stage and set the end time of the stage "end" to time T.
        While the time is less than the end of the stage, each time a container arrives we do the following actions:
        -If the containers can be delivered before the end of the stage, it's added to the Working area.
         Otherwise it's added to the working area.
        -While we have time (before the end of the arrival), we continuously check and move containers
        between the two parts of the working area. If we detect an expired or deliverable container se remove or sell it.
        If we detect a container which should be in the waiting area we move it.
        When a new container arrives and we area "near" the end of the stage, we create a new stage by resetting
        the end of the stage (end=time+T) and doing the following actions:
         -We check (and try to remove) all containers in the working area
         -We now move all containers in the waiting area:
            -COntainers which will be able to be delivered before the end of the current stage are
            moved to positions s1...s2. Containers which still have to wait will be moved to s2...s3
            -When the waiting area is empty we return containers from s2...s3 to the waiting area.
    """

    def __init__(self, width: int, log_path: str):
        self._width = width
        self.log = Logger(log_path, "expert", width)
        self._store: Store = Store(width)
        self._time: int = 0
        self._next_time: int = 0  # end of the arrival of the current container
        # Positions which divide the Store
        self.s1: int = 0
        self.s2: int = 15
        self.s3: int = 25
        self.s4: int = width
        # End of the current "etapa"
        self.end: int = 0
        self.emptied: bool = False
        self.moved: bool = True

    def cash(self) -> int:
        '''
            Returns tha cash of the Store in the Strategy

            Returns
            -------
            cash: int
        '''
        return self._store.cash()

    def time_increment(self):
        '''
            Increments by one unit the time in the Strategy
        '''
        self._time += 1

    def minheight(self, p0: int, pf: int) -> int:
        '''
            Returns the minimum height in the Positions [p0,...,p0-1]

            Parameters
            ----------
            p0: int
            pf: int

            Returns
            -------
            min: int
        '''
        min: int = self._store.get_column_height(p0)
        for i in range(p0+1, pf):
            h = self._store.get_column_height(i)
            if h < min:
                min = h
        return min

    def maxheight(self, p0: int, pf: int) -> int:
        '''
            Returns the maximum height in the Positions [p0,...,p0-1]

            Parameters
            ----------
            p0: int
            pf: int

            Returns
            -------
            max: int
        '''
        max: int = self._store.get_column_height(p0)
        for i in range(p0+1, pf):
            h = self._store.get_column_height(i)
            if h > max:
                max = h
        return max

    def add_container(self, c: Container, d0: Position, df: Position) -> None:
        '''
            adds, if possible, a container to the lowest possible (in height) place between in
            the positions [d0,...,df-1]

            Parameters
            ----------
            c: Container
            d0: Position
                Lower Position limit
            df: Position
                Upper Position limit
        '''
        if(c is None or not (self._time < self._next_time)):
            return
        p: Optional[Position] = self.movable(c, d0, df)
        if p is not None:
            self.check_top(p)
            self._store.add(c, p)
            self.log.add(self._time, c, p)
            self.time_increment()

    def movable(self, c: Container, d0: int, df: int) -> Optional[Position]:
        '''
            Given a Container c and the Positions d0, df returns a the Position in
            [d0,...,df-1] where c can be added and has the minimum height Possible.
            If c can not be added in the given positions returns None.

            Parameters
            ----------
            c: Container
            d0:int
            df:int

            Returns
            -------
            p: Optional[Position]
                Position where c can be added (None if not possible)

        '''
        first: bool = True
        for i in range(df-1, d0-1, -1):
            if(self._store.can_add(c, i) and (i+(c.size-1) < df)):
                h = self._store.get_column_height(i)
                if(first):
                    first = False
                    hmin = h
                    p = i
                elif(h < hmin):
                    hmin = h
                    p = i

        if(not first):
            return p
        else:
            return None

    def can_move(self, p0: int, pf: int, d0: int, df: int) -> Optional[Tuple[Container, Position]]:
        '''
            Returns a Container located between p0 and pf which can be moved between d0 and df
            and the Position to where it can be moved.

            Selects a Container located in [p0,...pf-1] which can be moved to a suitable Position in
            [d0,...,df-1]. Returns a tuple with the Container and the Position where it can be added.

            Parameters
            ----------
            p0: Position
            pf: Position
            d0: Position
            df: Position

            Returns
            -------
            Optional[Tuple[Container,Position]]
        '''
        for i in range(p0, pf):
            top: Optional[Container] = self._store.top_container(i)
            if(top is not None and self._store.can_remove(top)):
                # if(top.delivery.start > self.end and top.delivery.start > self._next_time):
                #     destiny: Optional[Position] = self.movable(
                #         top, self.s3, self.s4)
                #     if(destiny is None):
                #         destiny = self.movable(top, d0, df)
                # else:
                destiny: Optional[Position] = self.movable(top, d0, df)
                if(destiny is not None):
                    return (top, destiny)
        return None

    def check(self, c: Container):
        '''
            Checks if a Container c is expired or can be delivered and acts on it. Returns False if
            if c is expired or can be delviered and True otherwise.

            If c can be expired it is removed from the Store and if c can be delivered it is delivered

            Parameters
            ----------
            c: Container

            Returns
            -------
            bool:
                True if the Container can not be delivered and is not expired.
                False if the container is expired (and is removed) or is deliverable (and is delivered)

        '''
        if(c is not None and self._time < self._next_time):
            if(c.expired(self._time)):
                self.remove_container(c)
                return False
            elif(c.deliverable(self._time)):
                self.deliver_container(c)
                return False
        return True

    def check_top(self, p: Optional[Position]):
        '''
            Checks the top Container at a Position p

            Parameters
            ----------
            p: Position
        '''
        if(p is not None):
            c = self._store.top_container(p)
            if(c is not None):
                self.check(c)

    def check_all(self):
        '''
        Checks all the top containers in the Store
        '''
        for i in range(0, self.s3):
            top = self._store.top_container(i)
            if(top is not None):
                self.check(top)

    def check_all2(self):
        '''
        Checks all the top containers in the Store
        '''
        for i in range(self.s3, self.s4):
            top = self._store.top_container(i)
            if(top is not None):
                self.check(top)

    def accept(self, c: Container) -> bool:
        '''
        Decides wether a Container should or not be accepted in the Store
        '''
        if(c.value//c.size < 1 and c.delivery.start > self.end):
            return False
        # if(c.delivery.start < self.end+4*T+1):  # or (c.value//c.size > 1)):
        #     return True
        return True

    def next_pos(self, next_c: Optional[Tuple[Container, Position]]) -> Optional[Position]:
        '''
        Checks a next_c and modifies its move position if it has to be moved to the waiting area
        '''
        if(next_c is not None):
            p: Position = next_c[1]

            if(next_c[0].delivery.start > self.end):
                newpos: Optional[Position] = self.movable(
                    next_c[0], self.s3, self.s4)
                if(newpos is not None):
                    p = newpos
            return p
        else:
            return None

    def exec(self, c: Container):
        '''
        We divide the store in three areas.
        We define an stage time.
        Every time a Container arrives, if its delivery time is later than the stage time
        it is added to the left part of the Store (between positions s3 and 4)
        Otherwise it's added between positions 1 and 3.
        When we reach the end of the stage, we update the time of the new stage and we move all containers
        in the stage are which will be delivered to the end of the new stage to the area between s1 and s3

        While we have time we move containers from s1-s2 to s3-s3 and check them (and viceversa)

        '''
        self._next_time = c.arrival.end
        if(self.accept(c)):  # We decide whether we accept or not the container
            if(self.end <= min(self._next_time, self._time+self.maxheight(self.s3, self.s4)*(self.s4-self.s3))):
                self.end = self._time+T
                self.emptied = False
                self.moved = False
            # We add the new container on different positions depending on its delivery time
            if(c.delivery.start < self.end):
                self.add_container(c, self.s1, self.s2)
            else:
                self.add_container(c, self.s3, self.s4)

            # In case we haven't been able to add it, we try to add it anywhere
            if(self._store.location(c) == (-1, -1)):
                self.add_container(c, self.s1, self.s4)

        # We do some things when the "etapa" changes to reorganize the Store
        if not self.emptied:
            self.empty()

        if not self.moved:
            self.move_all(self.s3, self.s4)

        self.check_all()

        # We calculate two containers to be moved, one in s1...s2 and one in s2...s3 in case on of
        # two areas is empty. While we have times containers are checked and moved from one area to
        # the other
        candidate_1: Optional[Tuple[Container, Position]] = self.can_move(
            self.s1, self.s2, self.s2, self.s3)
        candidate_2: Optional[Tuple[Container, Position]] = self.can_move(
            self.s2, self.s3, self.s1, self.s2)
        next_c: Optional[Tuple[Container, Position]] = candidate_1
        pos: Optional[Position] = None
        while(self._time < self._next_time and (candidate_1 is not None or candidate_2 is not None)):
            if(candidate_1 is not None):

                next_c = candidate_1
                # We check the position in which to move the container, in case the container
                # has to be moved to the staging area
                pos = self.next_pos(next_c)
                # While there are containers in s1...s2 which can be moved to s2...s3 we check and move them
                while(next_c is not None and self._time < self._next_time):
                    while(next_c is not None and self._time < self._next_time):
                        self.move_container(next_c[0], pos)
                        next_c = self.can_move(
                            self.s1, self.s2, self.s2, self.s3)
                        # We check the position in which to move the container, in case the container
                    # has to be moved to the staging area
                        pos = self.next_pos(next_c)
                        self.check_all()

                # We do the same as before moving them back from s2...s3 to s1..s2 and checking them
                    self.check_all()
                    next_c = self.can_move(self.s2, self.s3, self.s1, self.s2)
                    pos = self.next_pos(next_c)
                    while(next_c is not None and self._time < self._next_time):
                        self.move_container(next_c[0], pos)
                        next_c = self.can_move(
                            self.s2, self.s3, self.s1, self.s2)
                        pos = self.next_pos(next_c)
                        self.check_all()

                    self.check_all()
                    next_c = self.can_move(self.s1, self.s2, self.s2, self.s3)
                    pos = self.next_pos(next_c)
            # Same procedure as before but in the case there are no containers in s1...s2 to move to s2...s3
            # BUT there are containers in s2...s3 to move to s1...s2
            elif candidate_2 is not None:
                next_c = candidate_2
                pos = self.next_pos(next_c)
                while(next_c is not None and self._time < self._next_time):
                    while(next_c is not None and self._time < self._next_time):
                        self.move_container(next_c[0], pos)
                        next_c = self.can_move(
                            self.s2, self.s3, self.s1, self.s2)
                        pos = self.next_pos(next_c)
                        self.check_all()

                    self.check_all()
                    next_c = self.can_move(self.s1, self.s2, self.s2, self.s3)
                    pos = self.next_pos(next_c)
                    while(next_c is not None and self._time < self._next_time):
                        self.move_container(next_c[0], pos)
                        next_c = self.can_move(
                            self.s1, self.s2, self.s2, self.s3)
                        pos = self.next_pos(next_c)
                        self.check_all()

                    self.check_all()
                    next_c = self.can_move(self.s2, self.s3, self.s1, self.s2)
                    pos = self.next_pos(next_c)

            candidate_1 = self.can_move(
                self.s1, self.s2, self.s2, self.s3)
            candidate_2 = self.can_move(
                self.s2, self.s3, self.s1, self.s2)
        # If there is still time we increment it until we reach the end of the arrival time
        while(self._time < self._next_time):
            self.check_all()
            self.time_increment()

    def next_pos_1(self, next_c: Optional[Tuple[Container, Position]]) -> Optional[Position]:
        '''
        Calculate the appropiate position for a container c in the function move_all
        If the container can be delivered before the next end_time, the position is the same
        as the one passed as a parameters. Otherwise we calculate a position in the waiting area
        s3....s4.      
        '''
        if(next_c is not None):
            pos: Position = next_c[1]
            if(next_c[0].delivery.start > self.end):
                newpos: Optional[Position] = self.movable(
                    next_c[0], self.s2, self.s3)
                if(newpos is not None):
                    pos = newpos
            return pos
        return None

    def move_all(self, p0: Position, pf: Position) -> None:
        '''
        Moves all the containers from positions p0.....pf after an stage change

        After an stage change all containers from p0....pf (which is the waiting area) are 
        moved. Containers which are deiverable before the next end time, are moved to positions s1...s2
        Containers which will not be able to be delivered before the next endtime are put back in positions
        s3....s4
        '''
        next_c = self.can_move(p0, pf, self.s1, self.s2)
        pos = self.next_pos_1(next_c)
        while(next_c is not None and self._time < self._next_time):
            self.move_container(next_c[0], pos)
            self.check_all2()
            self.check_all()
            next_c = self.can_move(p0, pf, self.s1, self.s2)
            pos = self.next_pos_1(next_c)

        next_c = self.can_move(self.s2, self.s3, self.s3, self.s4)
        while(next_c is not None and self._time < self._next_time):
            self.check_all2()
            self.check_all()

            self.move_container(next_c[0], next_c[1])
            next_c = self.can_move(self.s2, self.s3, self.s3, self.s4)
        if(self._time < self._next_time):
            self.check_all2()
            self.check_all()

            self.moved = True

    def empty(self) -> None:
        '''
        Empties de working area of the Store after an stage change
        When the working area has been emptied records it in a boolean 
        '''
        if(self._time < self._next_time):
            self.check_all()
        if(self._time < self._next_time):
            self.emptied = True

    def move_container(self, c: Container, p: Optional[Position]) -> None:
        '''
            Moves a Container c to the Position p.

            Parameters
            ----------
            c: Container
            p: Position
        '''

        if(self.check(c)):  # We check if the container can be sold or is expired
            # We check the top container at the position p before putting the Container c on top of it.
            self.check_top(p)

            if(self._time < self._next_time and c is not None and p is not None and self._store.can_remove(c)):
                self._store.move(c, p)
                self.log.move(self._time, c, p)
                self.time_increment()

    def deliver_container(self, c: Container) -> None:
        '''
        Delivers a Container c

        Parameters
        ----------
        c: Container
        '''
        if(self._time < self._next_time and self._store.can_remove(c) and c.deliverable(self._time)):
            self._store.add_cash(c.value)
            self._store.remove(c)
            self.log.remove(self._time, c)
            self.log.cash(self._time, self.cash())
            self.time_increment()

    def remove_container(self, c: Container) -> None:
        '''
        Removes a Container c from the Store

        Parameters
        ----------
        c: Container
        '''
        if(self._time < self._next_time and self._store.can_remove(c)):
            self._store.remove(c)
            self.log.remove(self._time, c)
            self.log.cash(self._time, self.cash())
            self.time_increment()


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
