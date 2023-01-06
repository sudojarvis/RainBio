# -*- coding: utf-8 -*-
# RainbowBox
# Copyright (C) 2015-2016 Jean-Baptiste LAMY
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

import sys, random

import metaheuristic_optimizer.artificial_feeding_birds as artificial_feeding_birds

from rainbowbox.order_base import *


def best_grouped_elements_order(relations, elements = None, nb_tested_solution = 10000):
  present_elements, present_element_groups, properties, property_groups, element_2_property_2_relation, property_2_element_2_relation = relations_2_model(relations)
  elements = elements or present_elements
  
  group_2_element = defaultdict(list)
  for e in elements: group_2_element[e.group].append(e)
  groups = list(group_2_element.values())
  
  for e in elements:
    if not e in element_2_property_2_relation: element_2_property_2_relation[e] = {} # Element with no relation are not present
  for p in properties:
    if not p in property_2_element_2_relation: property_2_element_2_relation[p] = {} # Property with no relation are not present
    
  ratios = [max(len(g) ** 2 - 1, 0) for g in groups]
  if   len(groups) <= 2:
    total = sum(ratios)
  elif len(groups) <= 5:
    total = sum(ratios) * 0.9
  else:
    total = sum(ratios) * 0.8
  ratios = [x / total for x in ratios]
  
  def score_order(groups):
    order = []
    for group in groups: order.extend(group)
    
    nb_hole           = 0
    nb_prop_with_hole = 0
    total_hole_length = 0
    sum_of_hatch_pos  = 0
    for property in properties:
      start   = None
      end     = None
      in_hole = False
      for i, element in enumerate(order):
        if element in property_2_element_2_relation[property]:
          if start is None: start = i
          end = i
          in_hole = False
          if property_2_element_2_relation[property][element].hatch: sum_of_hatch_pos += i
        else:
          if (not start is None) and (not in_hole):
            in_hole = True
            nb_hole += property.weight or 1
            
      if not end is None:
        if end != i: nb_hole -= property.weight or 1 # After end, it is not a hole!
        length = end - start + 1
        
        if length > len(property_2_element_2_relation[property]):
          total_hole_length += (length - len(property_2_element_2_relation[property])) * (property.weight or 1)
          nb_prop_with_hole += property.weight or 1
          
    #return total_hole_length, nb_hole, nb_prop_with_hole
    #return nb_hole, nb_prop_with_hole, total_hole_length
    #return nb_prop_with_hole
    #return nb_hole + nb_prop_with_hole + total_hole_length / len(elements), nb_prop_with_hole, nb_hole, total_hole_length
    return nb_hole + nb_prop_with_hole + 4 * total_hole_length / len(elements), nb_prop_with_hole, nb_hole, total_hole_length
  
  algo = GroupedOrderingAlgorithm(score_order, ratios, groups)
  
  algo.run(nb_tested_solution = nb_tested_solution)
  
  
  groups = algo.get_best_position()
  p = []
  for group in groups: p.extend(group)
  
  return p, algo.get_lowest_cost()




class GroupedOrderingAlgorithm(artificial_feeding_birds.MetaHeuristic):
  def __init__(self, cost_func, ratios, groups):
    self.ratios          = ratios
    self.groups          = groups
    
    self.total_ratio = 0
    for group in groups:
      self.total_ratio += len(group) ** 2 - 1
      
    self.reorder_groups_ratio = max(0, len(groups) - 2) ** 2
    self.total_ratio += self.reorder_groups_ratio
    
    artificial_feeding_birds.MetaHeuristic.__init__(self, cost_func)
    
  def fly(self):
    groups = []
    for group in self.groups:
      group = list(group)
      random.shuffle(group)
      groups.append(group)
    random.shuffle(groups)
    return groups
  
  def walk(self, bird):
    groups = list(bird.position)
    
    r = random.uniform(0.0, self.total_ratio)
    
    if r < self.reorder_groups_ratio:
      #print("reorder groups")
      groups = self.two_op(groups)
      return groups    
    r -= self.reorder_groups_ratio
    
    for i in range(len(groups)):
      r -= len(groups[i]) ** 2 - 1
      if r < 0: break
    #print("reorder group", i, "with", len(groups[i]), "element")
    
    group = groups[i]
    
    def bird_2_x(bird):
      for g in bird.position:
        if group[0] in g: return g
    group = self.adaptative_2opt(bird, bird_2_x)
    
    #print(group == bird.position[i], len(group))
    
    
    groups[i] = group
    
    return groups
  
  def two_op(self, p):
    i = random.randint(0, len(p) - 1)
    j = random.randint(i + 1, len(p))
    p[i:j] = reversed(p[i:j])
    return p

  
