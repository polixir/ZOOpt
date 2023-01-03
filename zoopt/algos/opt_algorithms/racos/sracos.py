"""
This module contains the class SRacos, which is the sequential version of Racos (a classification based optimization algorithm).

Author:
    Yu-ren Liu

Updated by:
    Ze-Wen Li
"""

import time

import numpy as np

from zoopt.algos.opt_algorithms.racos.racos_classification import RacosClassification
from zoopt.algos.opt_algorithms.racos.racos_common import RacosCommon
from zoopt.solution import Solution
from zoopt.utils.tool_function import ToolFunction
from zoopt import Objective


class SRacos(RacosCommon):
    """
    The class SRacos represents Sequential Racos algorithm. It's inherited from RacosCommon.
    """

    def __init__(self):
        """
        Initialization.
        """
        RacosCommon.__init__(self)
        return

    def opt(self, objective, parameter, strategy='WR', ub=1):
        """
        SRacos optimization.

        :param objective: an Objective object
        :param parameter: a Parameter object
        :param strategy: replace strategy
        :param ub: uncertain bits, which is a parameter of SRacos
        :return: Optimization result
        """
        self.clear()
        self.set_objective(objective)
        self.set_parameters(parameter)
        self.init_attribute()
        stopping_criterion = self._parameter.get_stopping_criterion()
        i = 0
        iteration_num = self._parameter.get_budget() - self._parameter.get_train_size()
        time_log1 = time.time()
        max_distinct_repeat_times = 100
        current_not_distinct_times = 0
        while i < iteration_num:
            sampled_data = self._positive_data + self._negative_data
            if np.random.random() < self._parameter.get_probability():
                classifier = RacosClassification(
                    self._objective.get_dim(), self._positive_data, self._negative_data, ub)
                classifier.mixed_classification()
                solution, distinct_flag = self.distinct_sample_classifier(
                    classifier, sampled_data, True, self._parameter.get_train_size())
            else:
                solution, distinct_flag = self.distinct_sample(self._objective.get_dim(), sampled_data)
            # panic stop
            if solution is None:
                ToolFunction.log(" [break loop] because solution is None")
                return self._best_solution
            if distinct_flag is False:
                current_not_distinct_times += 1
                if current_not_distinct_times >= max_distinct_repeat_times:
                    ToolFunction.log(
                        "[break loop] because distinct_flag is false too much times")
                    return self._best_solution
                else:
                    continue
            # evaluate the solution
            objective.eval(solution)
            # show best solution
            times = i + self._parameter.get_train_size() + 1
            self.show_best_solution(parameter.get_intermediate_result(), times, parameter.get_intermediate_freq())
            bad_ele = self.replace(self._positive_data, solution, 'pos')
            self.replace(self._negative_data, bad_ele, 'neg', strategy)
            self._best_solution = self._positive_data[0]
            if i == 4:
                time_log2 = time.time()
                expected_time = (self._parameter.get_budget() - self._parameter.get_train_size()) * \
                                (time_log2 - time_log1) / 5
                if self._parameter.get_time_budget() is not None:
                    expected_time = min(
                        expected_time, self._parameter.get_time_budget())
                if expected_time > 5:
                    m, s = divmod(expected_time, 60)
                    h, m = divmod(m, 60)
                    ToolFunction.log(
                        'expected remaining running time: %02d:%02d:%02d' % (h, m, s))
            # time budget check
            if self._parameter.get_time_budget() is not None:
                if (time.time() - time_log1) >= self._parameter.get_time_budget():
                    ToolFunction.log('time_budget runs out')
                    return self._best_solution
            # terminal_value check
            if self._parameter.get_terminal_value() is not None:
                if self._best_solution.get_value() <= self._parameter.get_terminal_value():
                    ToolFunction.log('terminal function value reached')
                    return self._best_solution
            if stopping_criterion.check(self) is True:
                return self._best_solution
            i += 1
        return self._best_solution

    def replace(self, iset, x, iset_type, strategy='WR'):
        """
        Replace a solution(chosen by strategy) in iset with x.

        :param iset: a solution list
        :param x: a Solution object
        :param iset_type: 'pos' or 'neg'
        :param strategy: 'WR': worst replace or 'RR': random replace or 'LM': replace the farthest solution
        :return: the replaced solution
        """
        if strategy == 'WR':
            return self.strategy_wr(iset, x, iset_type)
        elif strategy == 'RR':
            return self.strategy_rr(iset, x)
        elif strategy == 'LM':
            best_sol = min(iset, key=lambda x: x.get_value())
            return self.strategy_lm(iset, best_sol, x)

    def binary_search(self, iset, x, begin, end):
        """
        Find the first element larger than x.

        :param iset: a solution set
        :param x: a Solution object
        :param begin: begin position
        :param end: end position
        :return: the index of the first element larger than x
        """
        x_value = x.get_value()
        if x_value <= iset[begin].get_value():
            return begin
        if x_value >= iset[end].get_value():
            return end + 1
        if end == begin + 1:
            return end
        mid = begin + (end - begin) // 2
        if x_value <= iset[mid].get_value():
            return self.binary_search(iset, x, begin, mid)
        else:
            return self.binary_search(iset, x, mid, end)

    def strategy_wr(self, iset, x, iset_type):
        """
        Replace the worst solution in iset.

        :param iset: a solution set
        :param x: a Solution object
        :param iset_type: 'pos' or 'neg'
        :return: the worst solution
        """
        if iset_type == 'pos':
            index = self.binary_search(iset, x, 0, len(iset) - 1)
            iset.insert(index, x)
            worst_ele = iset.pop()
        else:
            worst_ele, worst_index = Solution.find_maximum(iset)
            if worst_ele.get_value() > x.get_value():
                iset[worst_index] = x
            else:
                worst_ele = x
        return worst_ele

    def strategy_rr(self, iset, x):
        """
        Replace a random solution in iset.

        :param iset: a solution set
        :param x: a Solution object
        :return: the replaced solution
        """
        len_iset = len(iset)
        replace_index = np.random.randint(0, len_iset)
        replace_ele = iset[replace_index]
        iset[replace_index] = x
        return replace_ele

    #
    def strategy_lm(self, iset, best_sol, x):
        """
        Replace the farthest solution from best_sol

        :param iset: a solution set
        :param best_sol: the best solution, distance between solution in iset and best_sol will be computed
        :param x: a Solution object
        :return: the farthest solution (has the largest margin) in iset
        """
        farthest_dis = 0
        farthest_index = 0
        for i in range(len(iset)):
            dis = self.distance(iset[i].get_x(), best_sol.get_x())
            if dis > farthest_dis:
                farthest_dis = dis
                farthest_index = i
        farthest_ele = iset[farthest_index]
        iset[farthest_index] = x
        return farthest_ele

    @staticmethod
    def distance(x, y):
        """
        Get the distance between the list x and y
        :param x: a list
        :param y: a list
        :return: Euclidean distance
        """
        dis = 0
        for i in range(len(x)):
            dis += (x[i] - y[i])**2
        return np.sqrt(dis)


class SRacosTune(RacosCommon):
    """
    The class SRacosTune represents Sequential Racos algorithm for Tune. It's inherited from RacosCommon.
    """

    def __init__(self, dimension, parameter, **kwargs):
        """
        Initialization.

        :param dimension: instance of Dimension2 class
        :param parameter: instance of Parameter class
        """

        RacosCommon.__init__(self)
        self.clear()
        objective = Objective(None, dimension)
        self.set_objective(objective)
        self.set_parameters(parameter)
        self._parameter.set_server_num(kwargs['parallel_num'])

        self.init_num = 0
        self.complete_num = 0
        self.semaphore = 1  # control init
        self.live_num = 0
        self.ub = self._parameter.get_uncertain_bits()
        if self.ub is None:
            self.ub = self.choose_ub(self.get_objective())
        return

    def suggest(self):
        """
        Suggest a trial for Tune, including init trials(decided by `budget`)

        """
        if self.semaphore == 0:
            return

        solution = None

        if self.init_num < self._parameter.get_train_size():  # for init
            solution, distinct_flag = self.tune_init_attribute()
            if distinct_flag is False:
                return "FINISHED"
            self.live_num += 1
        elif self.init_num == self._parameter.get_train_size():
            self.semaphore = 0
            self.init_num += 1
            return
        elif self.live_num < self._parameter.get_server_num():
            solution, distinct_flag = self.sample_solution(self.ub)
            if distinct_flag is False:
                return "FINISHED"
            self.live_num += 1

        self.init_num += 1
        return solution

    def complete(self, solution, result):
        """
        Process results for Tune. Put evaluated result to solution.

        :param solution: a solution without result
        :param result: evaluated result of solution
        :return: best solution so far
        """
        self.complete_num += 1
        self.live_num -= 1

        # Invalid results (nan/inf) should not be added as data
        if np.isnan(result) or np.isinf(result):
            if self.complete_num == self._parameter.get_train_size():
                self.semaphore = 1
            return self._best_solution

        solution.set_value(result)
        if self.complete_num < self._parameter.get_train_size():
            self._data.append(solution)
            self.selection()
        elif self.complete_num == self._parameter.get_train_size():
            best_solution_so_far = self.update_classifier(solution)
            self.semaphore = 1
            return best_solution_so_far
        else:
            best_solution_so_far = self.update_classifier(solution)
            return best_solution_so_far

    def sample_solution(self, ub=1):
        """
        Sample a trial for Tune.

        :param ub: uncertain bits, which is a parameter of SRacos
        :return: a solution containing trial
        """
        sampled_data = self._positive_data + self._negative_data
        if np.random.random() < self._parameter.get_probability():  # exploitation
            classifier = RacosClassification(
                self._objective.get_dim(), self._positive_data, self._negative_data, ub)
            classifier.mixed_classification()
            solution, distinct_flag = self.distinct_sample_classifier(
                classifier, sampled_data, True, self._parameter.get_train_size())
        else:  # exploration
            solution, distinct_flag = self.distinct_sample(self._objective.get_dim(), sampled_data)

        return solution, distinct_flag

    def update_classifier(self, solution, strategy='WR'):
        stopping_criterion = self._parameter.get_stopping_criterion()
        bad_ele = self.replace(self._positive_data, solution, 'pos')
        self.replace(self._negative_data, bad_ele, 'neg', strategy)
        self._best_solution = self._positive_data[0]

        # terminal_value check
        if self._parameter.get_terminal_value() is not None:
            if self._best_solution.get_value() <= self._parameter.get_terminal_value():
                ToolFunction.log('terminal function value reached')
                return self._best_solution
        if stopping_criterion.check(self) is True:
            return self._best_solution

        return self._best_solution

    def replace(self, iset, x, iset_type, strategy='WR'):
        """
        Replace a solution(chosen by strategy) in iset with x.

        :param iset: a solution list
        :param x: a Solution object
        :param iset_type: 'pos' or 'neg'
        :param strategy: 'WR': worst replace or 'RR': random replace or 'LM': replace the farthest solution
        :return: the replaced solution
        """
        if strategy == 'WR':
            return self.strategy_wr(iset, x, iset_type)
        elif strategy == 'RR':
            return self.strategy_rr(iset, x)
        elif strategy == 'LM':
            best_sol = min(iset, key=lambda x: x.get_value())
            return self.strategy_lm(iset, best_sol, x)

    def binary_search(self, iset, x, begin, end):
        """
        Find the first element larger than x.

        :param iset: a solution set
        :param x: a Solution object
        :param begin: begin position
        :param end: end position
        :return: the index of the first element larger than x
        """
        x_value = x.get_value()
        if x_value <= iset[begin].get_value():
            return begin
        if x_value >= iset[end].get_value():
            return end + 1
        if end == begin + 1:
            return end
        mid = begin + (end - begin) // 2
        if x_value <= iset[mid].get_value():
            return self.binary_search(iset, x, begin, mid)
        else:
            return self.binary_search(iset, x, mid, end)

    def strategy_wr(self, iset, x, iset_type):
        """
        Replace the worst solution in iset.

        :param iset: a solution set
        :param x: a Solution object
        :param iset_type: 'pos' or 'neg'
        :return: the worst solution
        """
        if iset_type == 'pos':
            index = self.binary_search(iset, x, 0, len(iset) - 1)
            iset.insert(index, x)
            worst_ele = iset.pop()
        else:
            worst_ele, worst_index = Solution.find_maximum(iset)
            if worst_ele.get_value() > x.get_value():
                iset[worst_index] = x
            else:
                worst_ele = x
        return worst_ele

    def strategy_rr(self, iset, x):
        """
        Replace a random solution in iset.

        :param iset: a solution set
        :param x: a Solution object
        :return: the replaced solution
        """
        len_iset = len(iset)
        replace_index = np.random.randint(0, len_iset)
        replace_ele = iset[replace_index]
        iset[replace_index] = x
        return replace_ele

    def strategy_lm(self, iset, best_sol, x):
        """
        Replace the farthest solution from best_sol

        :param iset: a solution set
        :param best_sol: the best solution, distance between solution in iset and best_sol will be computed
        :param x: a Solution object
        :return: the farthest solution (has the largest margin) in iset
        """
        farthest_dis = 0
        farthest_index = 0
        for i in range(len(iset)):
            dis = self.distance(iset[i].get_x(), best_sol.get_x())
            if dis > farthest_dis:
                farthest_dis = dis
                farthest_index = i
        farthest_ele = iset[farthest_index]
        iset[farthest_index] = x
        return farthest_ele

    @staticmethod
    def distance(x, y):
        """
        Get the distance between the list x and y
        :param x: a list
        :param y: a list
        :return: Euclidean distance
        """
        dis = 0
        for i in range(len(x)):
            dis += (x[i] - y[i])**2
        return np.sqrt(dis)

    @staticmethod
    def choose_ub(objective):
        """
        Choose uncertain_bits according to the dimension size automatically.

        :param objective: an Objective object
        :return: uncertain bits
        """
        dim = objective.get_dim()
        dim_size = dim.get_size()
        is_discrete = dim.is_discrete()
        if is_discrete is False:
            if dim_size <= 100:
                ub = 1
            elif dim_size <= 1000:
                ub = 2
            else:
                ub = 3
        else:
            if dim_size <= 10:
                ub = 1
            elif dim_size <= 50:
                ub = 2
            elif dim_size <= 100:
                ub = 3
            elif dim_size <= 1000:
                ub = 4
            else:
                ub = 5
        return ub