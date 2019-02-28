# -*- coding: utf-8 -*-
from __future__ import print_function

import copy
import os
import random
import subprocess
import sys

LIVE_CELL = '⬛'
DEAD_CELL = '⬜'
OUTPUT_FILE = 'output.txt'


def showNote():
    print('''
    The game of Life 是由英国数学家 John H. Conway 发明的，它能模拟生物群落的兴衰更替。
    该游戏可用来观察一个复杂的系统或模式如何能从一组简单的规则演化而来。

    游戏规则
    该游戏使用一个不限大小的矩形网格，其中的每个单元格要么是空的，要么被一个有机体占据。
    被占据的单元格被视作是活的，而空的单元格被视作是死的。
    游戏的每次演进，都会基于当前的单元格布局，创造新的“一代”。

    下一代中的每个单元格状态是根据以下规则确定的：
    若某单元格是活的，并且有 2 或 3 个活的邻居，那么它在下一代也保持活。每个单元格有 8 个邻居。
    若某单元格是活的，但它没有活的邻居，或只有一个活邻居，它在下一代会死于孤立。
    一个活单元格，若有 4 个或更多个活邻居，它在下一代会死于人口过剩。
    一个死单元格，当且仅当只有 3 个活邻居时，会在下一代重生。
    用户先初始化配置，即指定哪些单元格是活的，然后运用以上的规则，生成下一代。
    可以看到，一些系统可能最终会消亡，而有些最终会进化成 “稳定” 状态。
    ''')


def showGrid(grid, islife=False):
    """展示网格"""

    f = open(OUTPUT_FILE, 'a+')
    for x in range(len(grid)):
        for y in range(len(grid[x])):
            if islife:
                c = LIVE_CELL if grid[x][y] else DEAD_CELL
            else:
                c = str(grid[x][y])
            print(c, end='', file=f)
        print(file=f)
    print(file=f)
    f.close()


# TODO 只能扩展，不能收缩，不完美。
def peripheryExpand(grid, val=None, maxRow=100, maxCol=100):
    """保证网格四周的行列的值全部为0"""

    sTop = sum([grid[0][c] for c in range(len(grid[0]))])
    if sTop > 0 and len(grid) < maxRow:
        zero = [[val] * len(grid[0])]
        zero.extend(grid)
        grid = copy.deepcopy(zero)

    sDown = sum([grid[-1][c] for c in range(len(grid[-1]))])
    if sDown > 0 and len(grid) < maxRow:
        grid.extend([[0] * len(grid[-1])])

    sLeft = sum([grid[r][0] for r in range(len(grid))])
    if sLeft > 0:
        for r in range(len(grid)):
            if len(grid[r]) < maxCol:
                zero = [0]
                zero.extend(grid[r])
                grid[r] = zero

    sRight = sum([grid[r][-1] for r in range(len(grid))])
    if sRight > 0:
        for r in range(len(grid)):
            if len(grid[r]) < maxCol:
                grid[r].append(0)

    return grid


# noinspection PyUnresolvedReferences
def letsDoIt():
    print('''
    按照如下格式输入参数
    演化次数,初始网格长度,初始网格宽度
    例：100,4,4   (表示在4x4网格中随机生成一个群落，然后持续演化100次)
    PS：
        1.不输入参数，默认以"100,4,4"参数运行。
        2.输入"note"，查看规则介绍
        3.输入"bye"，退出
    ''')

    while True:
        if sys.version > '3':
            # python 3
            inputs = input("请输入指令: ").strip()
        else:
            # 兼容python 2
            inputs = raw_input("请输入指令: ").strip()

        if inputs == 'note':
            showNote()
        elif inputs == 'bye':
            break
        elif inputs == '':
            LifeGrid().updateGrid()
        elif len(inputs.split(',')) == 3:
            params = inputs.split(',')
            LifeGrid(int(params[1]), int(params[2])).updateGrid(int(params[0]))
        else:
            print('未能识别指令！')


class FifoQueue:
    """先进先出、定长队列"""

    def __init__(self, size=10, maxHead=10):
        """队列初始化、默认长度：10"""
        self._queue = []
        self._head = 0
        self._size = size
        self._maxHead = maxHead

    def add(self, item):
        self._queue.append(copy.deepcopy(item))
        if len(self._queue) > self._size:
            self._head += 1
            self.clean()

    def clean(self):
        """避免队列过长或频繁截断数组"""
        if self._head > self._maxHead:
            self._queue = self._queue[self._head:]
            self._head = 0

    def __contains__(self, item):
        return item in self._queue[self._head:]

    def getQueue(self):
        return self._queue


class LifeGrid:
    """生物群组对象"""

    ''' 
    1. 若某单元格是活的，并且有 2 或 3 个活的邻居，那么它在下一代也保持活。每个单元格有 8 个邻居。
    2. 若某单元格是活的，但它没有活的邻居，或只有一个活邻居，它在下一代会死于孤立。
    3. 一个活单元格，若有 4 个或更多个活邻居，它在下一代会死于人口过剩。
    4. 一个死单元格，当且仅当只有 3 个活邻居时，会在下一代重生。
    '''
    RULE_DICT = {0: 0, 1: 0, 2: 0, 3: 1, 4: 1, 5: 0, 6: 0, 7: 0, 8: 0, 9: 0}

    def __init__(self, rowCnt=4, colCnt=4):

        # 使用随机值初始化二维数组
        self._grid = peripheryExpand([[random.randint(0, 1) for c in range(colCnt)] for r in range(rowCnt)], val=0)

        # 使用-1，初始化二维数组
        self._gridNew = [[-1] * len(self._grid[0]) for i in range(len(self._grid))]

        # 使用固定长度的先进先出队列保留历史状态，用于分析生命网格是否存现平衡（循环的稳定状态）
        self._history = FifoQueue(20)

    def updateCell(self, r, c):

        # 当前单元格及其所有邻居
        nbr = [self._grid[r + x][c + y] for x in (-1, 0, 1) for y in (-1, 0, 1) if
               -1 < r + x < len(self._grid) and -1 < c + y < len(self._grid[x])]

        # 根据当前单元格及其所有邻居的总人口，推算当前单元格的生存状态
        self._gridNew[r][c] = LifeGrid.RULE_DICT.get(sum(nbr))

    def updateGrid(self, iterCnt=100):

        # 删除输出文件
        if os.path.exists(OUTPUT_FILE):
            os.remove(OUTPUT_FILE)

        for it in range(iterCnt):
            # 保存网格历史状态，以便分析生命网格是否存现平衡（循环的稳定状态）
            self._history.add(self._gridNew)

            # 逐个推算当前单元格的生存状态
            for r in range(len(self._grid)):
                for c in range(len(self._grid[r])):
                    self.updateCell(r, c)

            # 将推算结果更新到网格
            self._gridNew = peripheryExpand(self._gridNew, val=0)
            self._grid = copy.deepcopy(self._gridNew)

            # 打印网格
            showGrid(self._grid, islife=True)

            # 鉴别异常
            if not self.isGridLive():
                print('nothing left.')
                break
            elif self.isGridBalance():
                print('get balance.')
                break

        # 打开输出文件
        subprocess.call(['open', OUTPUT_FILE])

    def isGridLive(self):

        # 计算二维数组的和
        return sum(map(sum, self._grid)) > 0

    def isGridBalance(self):
        return self._grid in self._history


letsDoIt()
