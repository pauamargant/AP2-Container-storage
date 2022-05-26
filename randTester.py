import sys
import curses
import time
from random import *
# from termcolor import colored
from store import *
from simple import Strategy


def generateContainers(l: int):
    now = 0
    containers = []
    for i in range(l):
        size = randrange(1, 5)
        value = 1 + int(expovariate(1/10))  # media 11
        step = 1 + int(expovariate(1/24))  # media 25
        eTicks = (l-i)/5
        esperanza = randrange(1000, 6000)
        begin = now + int(expovariate(1/(esperanza+eTicks)))
        end = begin + int(expovariate(1/(esperanza+eTicks)))+1
        c = Container(i, size, value, TimeRange(
            now, now+step), TimeRange(begin, end))
        containers.append(c)
        now += step
    return containers


def execute_strategy(containers_path: str, log_path: str, width: int, resFile):
    """Execute the strategy on an empty store of a certain width reading containers from containers_path and logging to log_path."""

    containers = generateContainers(int(containers_path))
    strategy = Strategy(width, log_path)
    money = 0
    contSizes = [0, 0, 0, 0]
    for container in containers:
        if container.delivery.start < containers[-1].arrival.end:
            #contSizes[container.size-1] += 1
            money += container.value
        strategy.exec(container)
    #print('cont sizes: ', contSizes)
    print(containers_path, str(width), ':', str(
        strategy.cash()) + '$. Total money:', money, end=' | ')


def testFunction(fName, execList, resFile):
    print('=====Test for '+fName+'=====')
    for exec in execList:
        containers_path = exec[0]
        width = int(exec[1])
        begin = time.time()
        execute_strategy(containers_path, 'log.txt', width, resFile)
        end = time.time()
        print('elapsed time:', end-begin)
    print()


def main():
    """main script"""

    #path = sys.argv[1]
    #resFile = open(path, 'w')
    resFile = 0

    # 200 tests aleatorios
    sizeList = [1000 for i in range(100)] + [i for i in range(950, 1050)]
    execList = [[str(x), 35] for x in sizeList]
    testFunction(' simple strategy ', execList, resFile)


# start main script when program executed
if __name__ == '__main__':
    main()
