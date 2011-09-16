#!/usr/bin/env python
# -*- coding: utf-8 -*-
import sys
from  optparse import OptionParser
import math
import time
import datetime
import signal
from collections import deque
import string

MAXIMUM_HISTORY_SIZE = 1000000 * 5 * 4
RESET_LOOP_COUNT = 3 ** 8

class TimeoutException(Exception):
    pass

def timeout(timeout_duration_sec, default):
    def timeout_function(func):
        def _func(*args):
            def timeout_handler(signum, frame):
                raise TimeoutException()
            old_handler = signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(timeout_duration_sec)
            try:
                ret = func(*args)
            except TimeoutException:
                return default
            finally:
                signal.signal(signal.SIGALRM, old_handler)
            signal.alarm(0)
            return ret
        return _func
    return timeout_function

class ProblemManager:
    def __init__(self, file_name):
        if not file:
            return
        lines = open(file_name).readlines()
        self.maxl, self.maxr, self.maxu, self.maxd = [int(x) for x in lines[0].split(' ')]
        self.num_of_problem = int(lines[1])
        self.problems = lines[2:]

    def get_max(self):
        return self.maxl, self.maxr, self.maxu, self.maxd
    
    def get_num_of_problem(self):
        return self.num_of_problem

    def get_problem(self, index):
        if index is None or index < 0 or index > self.num_of_problem - 1:
            return ''
        line = self.problems[index]
        w, h, pattern = line.split(',')
        return int(w), int(h), pattern.replace('\n', '')

class ReferenceManager:
    def __init__(self, file_name):
        if not file_name:
            return
        self.lines = open(file_name).readlines()

    def get_result(self, idx):
        if idx >= 0 and idx < len(self.lines):
            return self.lines[idx].replace('\n', '')
        else:
            return ''

def calc_score(w, h, pattern1, pattern2):
    score = 0
    for i1 in range(0, w * h):
        s = pattern1[i1]
        if s == '=' or s == '0':
            continue
        i2 = pattern2.find(s)
        x1 = i1 % w
        y1 = i1 / w
        x2 = i2 % w
        y2 = i2 / w
        score += abs(x1 - x2) + abs(y1 - y2)
        #score += math.sqrt((x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2))
        #score += (x1 - x2) * (x1 - x2) + (y1 - y2) * (y1 - y2)
    return score

def swap_pattern(pattern, i1, i2):
    if i1 == i2:
        return pattern
    if i1 > i2:
        i1, i2 = i2, i1
    return pattern[:i1] + pattern[i2] + pattern[i1 + 1:i2] + pattern[i1] + pattern[i2 + 1:]

class Board:
    def __init__(self, w, h, pattern, index, move):
        self.w = w
        self.h = h
        self.pattern = pattern
        self.index = index; # = pattern.find('0')
        self.move = move

    def create_next_board_list(self):
        w = self.w
        h = self.h
        index = self.index
        move = self.move
        pattern = self.pattern
        next_board_list = []
        x = index % w
        y = index / w
        # L
        next_index = index - 1
        if ((len(move) == 0 or move[-1] != 'R') and 0 < x and pattern[next_index] != '='):
            next_board_list.append(Board(w, h, swap_pattern(pattern, index, next_index),
                                         next_index, move + 'L'))
        # R
        next_index = index + 1
        if ((len(move) == 0 or move[-1] != 'L') and x < w - 1 and pattern[next_index] != '='):
            next_board_list.append(Board(w, h, swap_pattern(pattern, index, next_index),
                                         next_index, move + 'R'))
        # U
        next_index = index - w
        if ((len(move) == 0 or move[-1] != 'D') and 0 < y and pattern[next_index] != '='):
            next_board_list.append(Board(w, h, swap_pattern(pattern, index, next_index),
                                         next_index, move + 'U'))
        # D
        next_index = index + w
        if ((len(move) == 0 or move[-1] != 'U') and y < h - 1 and pattern[next_index] != '='):
            next_board_list.append(Board(w, h, swap_pattern(pattern, index, next_index),
                                       next_index, move + 'D'))
        return next_board_list
        
def print_pattern(w, h, pattern):
    for i in range(0, h):
        print pattern[i * w:i * w + w]

def create_pattern(w, h, pattern, move):
    index0 = pattern.find('0');
    if (index0 == -1):
        return ''
    for m in move:
        if m == "L":
            index1 = index0 - 1
        elif m == "R":
            index1 = index0 + 1
        elif m == "U":
            index1 = index0 - w
        elif m == "D":
            index1 = index0 + w
        # check
        if index1 > w * h - 1 or index1 < 0 or pattern[index1] == '=':
            return ''
        new_pattern = swap_pattern(pattern, index0, index1)
        index0 = index1
        pattern = new_pattern
    return pattern

def make_answer_pattern(pattern):
    answer = '123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ0'
    answer = answer[:len(pattern)]
    index = pattern.find('=')
    while index != -1:
        answer = answer[:index] + '=' + answer[index + 1:]
        index = pattern.find('=', index + 1)
    return answer[:-1] + '0'

def flip_move(move):
    move = move[::-1]
    return move.translate(string.maketrans('RLUD', 'LRDU'))

def connect_move_back(ahead, back):
    if ahead == '':
        return flip_move(back)
    if back == '':
        return ahead
    while ahead[-1] == back[-1]:
        ahead = ahead[:-1]
        back = back[:-1]
        if ahead == '' or back == '':
            break
    return ahead + flip_move(back)

def connect_move(ahead1, ahead2):
    move = ahead1 + ahead2
    while True:
        move_len = len(move)
        move = move.replace('RL', '')
        move = move.replace('LR', '')
        move = move.replace('UD', '')
        move = move.replace('DU', '')
        if move_len == len(move):
            break
    return move

def solve_all(w, h, pattern, answer, reset_loop_count=RESET_LOOP_COUNT):
    loop_count = 0
    # to answer
    board = Board(w, h, pattern, pattern.find('0'), '')
    board_list = deque()
    board_history = {}
    # from answer
    board_back = Board(w, h, answer, answer.find('0'), '')
    board_back_list = deque()
    board_back_history = {}
    board_back_history[answer] = ''
    # check function
    def _process(board, self_queue, self_history, another_history):
        if board.pattern in another_history:
            return True
        if board.pattern not in self_history:
            self_history[board.pattern] = board.move
            self_queue.append(board)
        return False
    # solve loop
    while board.pattern != answer:
        # to answer
        next_board_list = board.create_next_board_list()
        for board in next_board_list:
            if _process(board, board_list, board_history, board_back_history):
                return connect_move_back(board.move,
                                         board_back_history[board.pattern])
        # from answer
        next_board_back_list = board_back.create_next_board_list()
        for board_back in next_board_back_list:
            if _process(board_back, board_back_list, board_back_history, board_history):
                return connect_move_back(board_history[board_back.pattern],
                                         board_back.move)
        # reset
        if reset_loop_count > 0 and loop_count > reset_loop_count:
            loop_count = 0
            ave = 0
            listLen = len(board_list)
            for l in board_list:
                ave += float(calc_score(w, h, l.pattern, answer)) / listLen
            board_list = deque([b for b in board_list if calc_score(w, h, b.pattern, answer) < ave])
        # increment
        board = board_list.popleft() if len(board_list) else None
        board_back = board_back_list.popleft() if len(board_back_list) else None
        if len(board_history) + len(board_back_history) > MAXIMUM_HISTORY_SIZE:
            return None
        if (not board) or (not board_back):
            return None
        loop_count += 1
    return board.move

def solve_partial(w, h, pattern, answer, fix_num, solve_num, reset_loop_count=RESET_LOOP_COUNT):
    trans_str_wall = answer[:fix_num]
    trans_table_wall = string.maketrans(trans_str_wall, 
                                        '=' * len(trans_str_wall))
    trans_str_asta = answer[fix_num + solve_num:-1].replace('=', '')
    trans_table_asta = string.maketrans(trans_str_asta,
                                        '*' * len(trans_str_asta))
    pattern_rep = pattern.translate(trans_table_wall)
    pattern_rep = pattern_rep.translate(trans_table_asta)
    answer_rep = answer.translate(trans_table_wall)
    answer_rep = answer_rep.translate(trans_table_asta)

    ####### debug #######
    print '--------- pattern_rep'
    print_pattern(w, h, pattern_rep)
    print '--------- answer_rep'
    print_pattern(w, h, answer_rep)
    ####### debug #######

    move = solve_all(w, h, pattern_rep, answer_rep, reset_loop_count)

    ####### debug #######
    if move:
        pattern_work = create_pattern(w, h, pattern, move)
        print '--------- succeeded'
        print_pattern(w, h, pattern_work)
    else:
        print '--------- not succeeded'
    ####### debug #######
    return move

@timeout(60, None)
def solve_partial_timeout_60(w, h, pattern, answer, fix_num, solve_num, reset_loop_count=RESET_LOOP_COUNT):
    return solve_partial(w, h, pattern, answer, fix_num, solve_num, reset_loop_count)

def solve(w, h, pattern, answer, no_timeout=False, no_loop_limit=False):
    area = w * h
    reset_loop_count = RESET_LOOP_COUNT
    if no_loop_limit:
        reset_loop_count = -1

    for i in [area,] +  range(1, area):
        print '\n# STEP 1 : %d / %d #' % (i, area)
        if not no_timeout:
            move1 = solve_partial_timeout_60(w, h, pattern, answer, 0, i, reset_loop_count)
        else:
            move1 = solve_partial(w, h, pattern, answer, 0, i, reset_loop_count)
        if i == area:
            return move1 if move1 else ''
        if move1 is None:
            continue

        print '\n# STEP 2 : %d / %d #' % (i, area)
        new_pattern = create_pattern(w, h, pattern, move1)
        if not no_timeout:
            move2 = solve_partial_timeout_60(w, h, new_pattern, answer, i, area - i, reset_loop_count)
        else:
            move2 = solve_partial(w, h, new_pattern, answer, i, area - i, reset_loop_count)
        if move2:
            return connect_move(move1, move2)

        print '\n# STEP 3 : %d / %d #' % (i, area)
        if not no_timeout:
            move3 = solve_partial_timeout_60(w, h, new_pattern, answer, 0, area, reset_loop_count)
        else:
            move3 = solve_partial(w, h, new_pattern, answer, 0, area, reset_loop_count)
        if move3:
            return connect_move(move1, move3)
    return ''

def rotate_90(w, h, pattern, answer):
    new_answer = ''
    new_pattern = ''
    for index in range(len(answer)):
        x = index % h
        y = index / h
        x, y = y, x
        old_index = y * w + x
        new_answer += answer[old_index]
        new_pattern += pattern[old_index]
    return h, w, new_pattern, new_answer

def back_convert_move_from_rotate_90(move):
    return move.translate(string.maketrans('LRUD', 'UDLR'))

def main():
    # argument check
    usage = '%prog -i <problem_file> [Options]';
    op = OptionParser(usage=usage)
    op.add_option('-i', type='string', dest='program_file', metavar='FILE', help='input problem file')
    op.add_option('-r', type='string', dest='reference_file', metavar='FILE', help='reference file. you can skip already solved problem')
    op.add_option('-o', type='string', dest='result_file', metavar='FILE', help='output result file')
    op.add_option('-s', type='int', dest='start_idx', metavar='INT', default=0, help='start problem index (>= 0)')
    op.add_option('-e', type='int', dest='end_idx', metavar='INT', default=4999, help='end problem index (< num_of_problem)')
    op.add_option('-f', '--notimeout', action='store_true', dest='no_timeout', default=False, help='flag of no_timeout')
    op.add_option('-1', '--noqueuelimit', action='store_true', dest='no_loop_limit', default=False, help='flag of no_loop_limit(no branch cutter)')
    op.add_option('-2', '--rotate', action='store_true', dest='solve_rotate_90', default=False, help='flag of solving after rotate')
    opts, args = op.parse_args(sys.argv)

    # load problem
    program_file_name = opts.program_file
    if not program_file_name:
        op.print_help()
        return
    pm = ProblemManager(program_file_name)
    num = pm.get_num_of_problem()

    # loop setting
    start_idx = opts.start_idx
    end_idx = opts.end_idx
    if start_idx > end_idx:
        start_idx, end_idx = end_idx, start_idx
    start_idx = start_idx if start_idx >=0 else 0
    end_idx = end_idx if end_idx < num else num - 1

    # result file
    result_file_name = opts.result_file
    if result_file_name is None:
        day = datetime.datetime.now()
        item = [program_file_name, start_idx, end_idx, day.day, day.hour, day.minute]
        item = [str(d) for d in item]
        result_file_name = 'result_' + '_'.join(item) + '.txt'
        skip_solved_problem = False

    # reference file
    reference_file_name = opts.reference_file
    skip_solved_problem = False
    if reference_file_name is not None:
        skip_solved_problem = True
    rm = ReferenceManager(reference_file_name)

    # other flags
    no_timeout = opts.no_timeout
    no_loop_limit = opts.no_loop_limit
    solve_rotate_90 = opts.solve_rotate_90

    # start solve
    start_time = time.time()
    for i in range(0, num):
        if i < start_idx or i > end_idx or (skip_solved_problem and rm.get_result(i) != ''):
            f = open(result_file_name, 'a')
            f.write('\n');
            f.close();
            continue
            
        w, h, pattern = pm.get_problem(i)
        answer = make_answer_pattern(pattern)
        if solve_rotate_90:
            w, h, pattern, answer = rotate_90(w, h, pattern, answer)

        print '========================='
        print str(i) + ' : ' + str(w) + 'x' + str(h)
        print_pattern(w, h, pattern)

        t1 = time.time()
        result_move = solve(w, h, pattern, answer, no_timeout, no_loop_limit)
        t2 = time.time()

        if not result_move:
            result_move = ''

        if solve_rotate_90:
            result_move = back_convert_move_from_rotate_90(result_move)

        # result output
        numl = result_move.count('L')
        numr = result_move.count('R')
        numu = result_move.count('U')
        numd = result_move.count('D')
        print '(L, R, U, D) = (%d, %d, %d, %d) = %d' % (numl, numr, numu, numd, len(result_move))
        print result_move
        print t2 - t1, 'sec'
        f = open(result_file_name, 'a')
        f.write(result_move + '\n');
        f.close();
    end_time = time.time()
    print end_time - start_time, 'sec'

if __name__ == '__main__':
    main()
