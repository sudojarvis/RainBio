# -*- coding: utf-8 -*-
# Metaheuristic_Optimizer
# Copyright (C) 2016-2017 Jean-Baptiste LAMY
# LIMICS (Laboratoire d'informatique médicale et d'ingénierie des connaissances en santé), UMR_S 1142
# University Paris 13, Sorbonne paris-Cité, Bobigny, France

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.

# You should have received a copy of the GNU Lesser General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import time, math

class Algorithm(object):
  def __init__(self, cost_func):

    def cost_func2(x):
      self.nb_cost_computed += 1
      return cost_func(x)
    
    self.cost_func = cost_func2
    
    self.reset()
    
  def reset(self):
    self.nb_cost_computed = 0
    
  def iterate(self): raise NotImplementedError
  
  def get_best_position(self): raise NotImplementedError
  def get_lowest_cost(self):   raise NotImplementedError
  
  def run(self, nb_iteration = None, nb_tested_solution = None, expected_cost = None, print_func = None):
    try:
      if   not nb_iteration is None:
        for i in range(nb_iteration):
          self.iterate()
        return nb_iteration

      elif not nb_tested_solution is None:
        i = 0
        while self.nb_cost_computed < nb_tested_solution:
          self.iterate()
          i += 1
        return i

      elif not expected_cost is None:
        i = 0
        while self.get_lowest_cost() > expected_cost:
          self.iterate()
          i += 1
        return i

      else:
        i = 0
        lowest_cost = None
        try:
          print("Interactive optimization started, stop with C-c.")
          t0 = time.time()
          while True:
            self.iterate()
            i += 1
            t = time.time()
            if t - t0 > 3.0:
              t0 = t
              print("%s iterations..." % i)
              if print_func: print_func(self)
              else:
                new_lowest_cost = self.get_lowest_cost()
                if (lowest_cost is None) or (new_lowest_cost < lowest_cost):
                  lowest_cost = new_lowest_cost
                  print("Lowest cost:", lowest_cost)

        except KeyboardInterrupt:
          pass
        return i
    except StopIteration:
      return
    
  def run_gevent(self, nb_iteration = None, nb_tested_solution = None, expected_cost = None, print_func = None):
    import gevent
    
    try:
      if   not nb_iteration is None:
        for i in range(nb_iteration):
          self.iterate()
          if i % 100 == 0: gevent.sleep(0.000001)
        return nb_iteration

      elif not nb_tested_solution is None:
        i = 0
        while self.nb_cost_computed < nb_tested_solution:
          self.iterate()
          if i % 100 == 0: gevent.sleep(0.000001)
          i += 1
        return i

      elif not expected_cost is None:
        i = 0
        while self.get_lowest_cost() > expected_cost:
          self.iterate()
          if i % 100 == 0: gevent.sleep(0.000001)
          i += 1
        return i

      else:
        i = 0
        lowest_cost = None
        try:
          print("Interactive optimization started, stop with C-c.")
          t0 = time.time()
          while True:
            self.iterate()
            if i % 100 == 0: gevent.sleep(0.000001)
            i += 1
            t = time.time()
            if t - t0 > 3.0:
              t0 = t
              print("%s iterations..." % i)
              if print_func: print_func(self)
              else:
                new_lowest_cost = self.get_lowest_cost()
                if (lowest_cost is None) or (new_lowest_cost < lowest_cost):
                  lowest_cost = new_lowest_cost
                  print("Lowest cost:", lowest_cost)

        except KeyboardInterrupt:
          pass
        return i
    except StopIteration:
      return
    
  def multiple_run(self, nb, **kargs):
    costs             = []
    nb_cost_computeds = []
    t0 = time.time()
    for i in range(nb):
      self.reset()
      self.run(**kargs)
      costs            .append(self.get_lowest_cost())
      nb_cost_computeds.append(self.nb_cost_computed)
    t = time.time() - t0
    return MultipleRunResults(costs, nb_cost_computeds, t)
  

def median(x):
  x = sorted(x)
  if len(x) % 2 == 1:
    return x[len(x) // 2]
  else:
    return ( x[len(x) // 2 - 1] + x[len(x) // 2] ) / 2.0
    
    
class MultipleRunResults(object):
  def __init__(self, costs, nb_cost_computeds, time):
    self.costs     = [float(x) for x in costs]
    self.mean      = sum(self.costs) / len(self.costs)
    self.median    = median(self.costs)
    self.std       = math.sqrt(sum(((cost - self.mean) ** 2) / len(costs) for cost in costs))
    self.best      = min(self.costs)
    
    self.nb_cost_computeds      = nb_cost_computeds
    self.mean_nb_cost_computeds = sum(nb_cost_computeds) / len(nb_cost_computeds)
    
    self.time      = time
    self.mean_time = time / len(self.costs)
    
  def __repr__(self):
    if isinstance(self.costs[0], int):
      return """Results of %s runs:
mean: %s std: %s best: %s (found %s times)
mean #cost computed: %s
mean time: %.3fs
""" % (len(self.costs), self.mean, self.std, self.best, self.costs.count(self.best), self.mean_nb_cost_computeds, self.mean_time)
    else:
      return """Results of %s runs:
mean: %.3e std: %.3e best: %.3e (found %s times)
mean #cost computed: %s
mean time: %.3fs
""" % (len(self.costs), self.mean, self.std, self.best, self.costs.count(self.best), self.mean_nb_cost_computeds, self.mean_time)
