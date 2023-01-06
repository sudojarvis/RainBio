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

from rainbowbox.order_base import *


def best_elements_order(relations, elements = None, filter_order = None):
  return best_elements_order_heuristic(relations, elements, filter_order)

def best_elements_order_np(relations, elements = None, filter_order = None, additional_criteria = None):
  present_elements, present_element_groups, properties, property_groups, element_2_property_2_relation, property_2_element_2_relation = relations_2_model(relations)
  if not elements: elements = present_elements
  if not additional_criteria: additional_criteria = lambda order: 0
  
  element_groups = []
  element_group_set = { None }
  for element in elements:
    if not element.group in element_group_set:
      element_groups.append(element.group)
      element_group_set.add(element.group)
      
  if len(elements) == 1: return elements
  for property in properties[:]:
    nb = len(property_2_element_2_relation[property])
    if   nb <= 1:             properties.remove(property) # Present for one element  => does not influence best order
    elif nb == len(elements): properties.remove(property) # Present for all elements => does not influence best order
    
  coocurrences = {}
  for subset in all_subsets(elements):
    if (len(subset) <= 1) or (len(subset) == len(elements)): continue
    subset = frozenset(subset)
    coocurrences[subset] = 0
    for property in properties:
      for element in subset:
        if not element in property_2_element_2_relation[property]: break
      else: coocurrences[subset] += 1
      
  if element_groups: elements_by_group = [all_orders(group.children) for group in element_groups]
  else:              elements_by_group = [all_orders(elements)]
  
  orders = all_combinations(elements_by_group)
  
  best_score = -1
  for order in orders:
    if filter_order and not filter_order(order): continue
    
    score = 0
    for sublist in all_sublists(order):
      if (len(sublist) <= 1) or (len(sublist) == len(elements)): continue
      subset = frozenset(sublist)
      score += coocurrences[subset]
    if score > best_score:
      best_score = score
      best_order = order
      
  return best_order

def best_elements_order_np_hole(relations, elements = None, filter_order = None, custom_score_order = None):
  present_elements, present_element_groups, properties, property_groups, element_2_property_2_relation, property_2_element_2_relation = relations_2_model(relations)
  if not elements: elements = present_elements
  
  if len(elements) == 1: return elements
  for property in properties[:]:
    nb = len(property_2_element_2_relation[property])
    if   nb <= 1:             properties.remove(property) # Present for one element  => does not influence best order
    elif nb == len(elements): properties.remove(property) # Present for all elements => does not influence best order
    
  def score_order(order):
    nb_hole           = 0
    length            = 0
    for property in properties:
      start   = None
      end     = None
      in_hole = False
      for i, element in enumerate(order):
        if in_hole: length += 1
        if element in property_2_element_2_relation[property]:
          if start is None: start = i
          end = i
          in_hole = False
        else:
          if (not start is None) and (not in_hole):
            in_hole = True
            nb_hole += property.weight or 1
            
      if not end is None:
        if end != i: nb_hole -= property.weight or 1 # After end, it is not a hole!
        
    return -nb_hole
    #return -length

  if custom_score_order:
    combined_score_order = lambda order: custom_score_order(order, score_order)
  else:
    combined_score_order = score_order
    
  best_score = None
  best_order = None
  for order in all_orders(elements):
    if filter_order and not filter_order(order): continue
    score = combined_score_order(order)
    if (best_score is None) or (score > best_score):
      best_score = score
      best_order = order
      
  # Optimize alphabetical order
  order = best_order
  def get_hatches(property_2_relation):
    return [(property_2_relation[p].hatch, property_2_relation[p].color) for p in properties if p in property_2_relation]
    
  i = 0
  while True:
    if i >= len(order): break
    current_memberships  = frozenset(element_2_property_2_relation[order[i]])
    current_hatches      = get_hatches(element_2_property_2_relation[order[i]])
    nb_identical_element = 1
    while True:
      if i + nb_identical_element >= len(order): break
      new_element = order[i + nb_identical_element]
      if order[i].group != new_element.group: break
      new_memberships = frozenset(element_2_property_2_relation[new_element])
      if current_memberships != new_memberships: break
      new_hatches = get_hatches(element_2_property_2_relation[new_element])
      if current_hatches != new_hatches:
        break
      nb_identical_element += 1
      
    if nb_identical_element > 1:
      order[i : i + nb_identical_element] = sorted(order[i : i + nb_identical_element], key = lambda e: e.order_key)
      
    i += nb_identical_element
    
  return order


def _build_tree(elements, properties, property_2_element_2_relation):
  from Bio.Phylo.TreeConstruction import _DistanceMatrix as DistanceMatrix, DistanceTreeConstructor
  
  distances = {}
  for e1 in elements:
    for e2 in elements:
      if (e1 is e2) or (id(e1) > id(e2)): continue
      d = 0
      for property in properties[:]:
        if   (e1 in property_2_element_2_relation[property]) != (e2 in property_2_element_2_relation[property]):
          d += 1.0
      distances[e1, e2] = distances[e2, e1] = d
        
  dm = DistanceMatrix([element.label for element in elements])
  for e1 in elements:
    for e2 in elements:
      if (e1 is e2) or (id(e1) > id(e2)): continue
      dm[e1.label, e2.label] = distances[e1, e2]
        
  treebuilder = DistanceTreeConstructor(None)
  tree = treebuilder.nj(dm)
  #tree = treebuilder.upgma(dm)
  return tree


def best_elements_order_tree(relations, elements = None, filter_order = None, tree = None):
  present_elements, present_element_groups, properties, property_groups, element_2_property_2_relation, property_2_element_2_relation = relations_2_model(relations)
  if not elements: elements = present_elements
  
  label_2_element = { element.label.replace("_", " ") : element for element in elements }
  print(label_2_element)
  
  if not tree: tree = _build_tree(elements, properties, property_2_element_2_relation)
  
  def score_order(order):
    nb_hole           = 0
    nb_prop_with_hole = 0
    total_hole_length = 0
    for property in properties:
      start   = None
      end     = None
      in_hole = False
      for i, element in enumerate(order):
        if element in property_2_element_2_relation[property]:
          if start is None: start = i
          end = i
          in_hole = False
        else:
          if (not start is None) and (not in_hole):
            in_hole = True
            nb_hole += 1
            
      # After end, it is not a hole!
      if end != i: nb_hole -= 1
      
      if not end is None:
        length = end - start + 1
        
        if length > len(property_2_element_2_relation[property]):
          total_hole_length += length - len(property_2_element_2_relation[property])
          nb_prop_with_hole += 1
          
    return (-nb_prop_with_hole, -nb_hole * 2 + -total_hole_length)

  if len(elements) < 15:
    def walker(clade):
      if clade.clades:
        results = []
        partss  = [walker(child) for child in clade.clades]
        for ordered_parts in all_orders(partss):
          combinations = all_combinations(ordered_parts)
          results.extend(combinations)
        return results
      else:
        element = label_2_element[clade.name.replace("_", " ")]
        return [ [element] ]
      
    orders = walker(tree.root)
    order, score = best(orders, score_order, score0 = (-sys.maxsize, -sys.maxsize))
    
  else:
    def get_clades(clade):
      if clade.name: clade.element = label_2_element[clade.name.replace("_", " ")]
      if len(clade.clades) > 1:
        yield clade, len(clade.clades)
      if clade.clades:
        for subclade in clade.clades:
          yield from get_clades(subclade)
          
    clades = list(get_clades(tree.root))
    for i, (clade, nb) in enumerate(clades):
      clade.i = i
    
    def factorial(x):
      if x == 1: return 1
      return x * factorial(x - 1)
    
    i_2_nb_fact = [ (nb, factorial(nb)) for (clade, nb) in clades ]
    
    nb_r_2_order = {}
    for nb in { nb for (clade, nb) in clades }:
      for r, order in enumerate(all_orders(list(range(nb)))):
        nb_r_2_order[nb, r] = order
        
    def get_order(p):
      order = []
      
      def walk_clade(clade):
        if clade.name: order.append(clade.element)
        
        if clade.clades:
          if len(clade.clades) == 1:
            walk_clade(clade.clades[0])
          else:
            nb, fact = i_2_nb_fact[clade.i]
            clade_order = nb_r_2_order[nb, p[clade.i]]
            for j in clade_order:
              walk_clade(clade.clades[j])

      walk_clade(tree.root)
      return order

    def cost(p):
      order = get_order(p)
      return [-x for x in score_order(order)]
    
    import metaheuristic_optimizer.artificial_feeding_birds as optim_module
    class Algo(optim_module.MetaHeuristic):
      def fly(self):
        return [ random.randint(0, fact - 1) for (nb, fact) in i_2_nb_fact ]
    
      def walk(self, bird):
        p2 = bird.position[:]
        i = random.randint(0, len(clades) - 1)
        
        nb, fact = i_2_nb_fact[i]
        p2[i] = random.randint(0, fact - 1)
        return p2
      
      
    algo  = Algo(cost)
    algo.run(nb_tested_solution = 3000)
    
    # def fly(): return [ random.randint(0, fact - 1) for (nb, fact) in i_2_nb_fact ]
    
    # best = fly()
    # best_score = cost(best)
    # for i in range(3000):
    #   p = fly()
    #   score = cost(p)
    #   if score > best_score:
    #     best = p
    #     best_score = score
        
    # print(best_score)
    # return get_order(best)
      
    order = get_order(algo.get_best_position())
    print(order)
    
  return order


def best_elements_order_heuristic(relations, elements = None, filter_order = None):
  present_elements, present_element_groups, properties, property_groups, element_2_property_2_relation, property_2_element_2_relation = relations_2_model(relations)
  if not elements: elements = present_elements
  elements = set(elements)
  for e in elements:
    if not e in element_2_property_2_relation: element_2_property_2_relation[e] = {} # Element with no relation are not present
  for p in properties:
    if not p in property_2_element_2_relation: property_2_element_2_relation[p] = {} # Property with no relation are not present

  # This is the heuristic algorithm published, with a few additional optimizations (commented below).
    
  def get_number_of_relation(e0):
    return len([prop for prop in element_2_property_2_relation[e0] if len(property_2_element_2_relation[prop]) > 1])
  candidate_first_elements, best_score = bests(elements, get_number_of_relation)
  
  orders_being_constructed         = { (e0,) for e0 in candidate_first_elements }
  partial_orders_already_processed = set()
  candidate_orders                 = set()
  
  properties_with_more_than_one_element = [
    property for property in properties
    if len(property_2_element_2_relation[property]) > 1
  ]
  
  def insertion_score(element, position, order):
    if   position == "beginning": neighbor = order[ 0]
    elif position == "end":       neighbor = order[-1]
    score = 0
    
    for x in element_2_property_2_relation[element]:
      if x in element_2_property_2_relation[neighbor]: score += 2
    
    for y in properties_with_more_than_one_element:
      if ((not y in element_2_property_2_relation[element]) and
          set(property_2_element_2_relation[y]).isdisjoint(order)): score += 1
      
    #remnants = set(elements) - set(order)
    #for x in element_2_property_2_relation[neighbor]:
    #  if not x in element_2_property_2_relation[element]:
    #    for remnant in remnants:
    #      if x in element_2_property_2_relation[remnant]:
    #        score -= 1
    #        break
    
    return score
  
  while orders_being_constructed:
    #print(len(orders_being_constructed), file = sys.stderr)
    order = orders_being_constructed.pop()
    remnant = elements.difference(order)
    possible_insertions = { (e, "beginning") for e in remnant } | { (e, "end") for e in remnant }
    choosen_insertions, best_score = bests(possible_insertions, lambda pair: insertion_score(pair[0], pair[1], order))

    already = set()
    for (e, position) in choosen_insertions:
      # Additional optimization (not in the published algorithm):
      # for elements with identical set membership,
      # test only one of them
      key = (position, frozenset(element_2_property_2_relation[e]))
      if key in already: continue
      already.add(key)
      if   position == "beginning": new_order = (e,) + order
      elif position == "end":       new_order = order + (e,)
      if len(new_order) == len(elements):
        candidate_orders.add(new_order)
      else:
        if not new_order in partial_orders_already_processed:
          # Additional optimization (not in the published algorithm):
          # do not add in orders_being_constructed
          # orders that have already been added before (and then processed and removed).
          orders_being_constructed.add(new_order)
          partial_orders_already_processed.add(new_order)
          
  # Now, tests all orders in candidate_orders
  
  def score_order(order):
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
            nb_hole += 1
            
      if not end is None:
        # After end, it is not a hole!
        if end != i: nb_hole -= 1
        
        length = end - start + 1
        
        if length > len(property_2_element_2_relation[property]):
          total_hole_length += length - len(property_2_element_2_relation[property])
          nb_prop_with_hole += 1

    # Favor orders maintaining groups
    groups_preserved = 0
    for i in range(len(order) - 1):
      if order[i].group == order[i + 1].group: groups_preserved += 1

    # Favor orders maintaining alphabetical order
    order_keys_preserved = 0
    for i in range(len(order) - 1):
      if order[i].order_key <= order[i + 1].order_key: order_keys_preserved += 1
      
    return (-nb_prop_with_hole, -nb_hole * 3 + -total_hole_length, sum_of_hatch_pos, groups_preserved, order_keys_preserved)
  
  print("Testing %s element orders..." % len(candidate_orders), file = sys.stderr)
  order, score = best(candidate_orders, score_order, score0 = (-sys.maxsize, -sys.maxsize, -sys.maxsize))
  
  # Reorder alphabetically consecutive sublist or identical elements (due to optimization, only one order is tested)
  order = list(order)
  i = 0
  while True:
    if i >= len(order): break
    nb_identical_element = 1
    while True:
      if i + nb_identical_element >= len(order): break
      if order[i].group != order[i + nb_identical_element].group: break
      if frozenset(element_2_property_2_relation[order[i]]) != frozenset(element_2_property_2_relation[order[i + nb_identical_element]]): break
      nb_identical_element += 1
      
    if nb_identical_element > 1:
      order[i : i + nb_identical_element] = sorted(order[i : i + nb_identical_element], key = lambda e: e.order_key)
      
    i += nb_identical_element
    
  return order
  

# This is an equivalent heuristic, but implemented differently (and more hard-to-read) than the published version.
# Performance are similar.
def best_elements_order_heuristic_old(relations, elements = None, filter_order = None):
  present_elements, present_element_groups, properties, property_groups, element_2_property_2_relation, property_2_element_2_relation = relations_2_model(relations)
  if not elements: elements = present_elements
  
  #def score_pair(pair):
  #  score = 0
  #  for property in properties[:]:
  #    aprop0 = pair[0] in property_2_element_2_relation[property]
  #    aprop1 = pair[1] in property_2_element_2_relation[property]
  #    if   aprop0 and aprop1: score += 1
  #  return score
  #
  #best_pairs, best_score = bests([(e1, e2) for e1 in elements for e2 in elements if id(e1) < id(e2)], score_pair)

  def score_first_element(first_element):
    return len(element_2_property_2_relation.get(first_element) or [])
  
  best_first_elements, best_score = bests(elements, score_first_element)
  
  def score_remnant(element_pos):
    element, pos = element_pos
    score = 0
    for property in properties:
      aprop0 = element    in property_2_element_2_relation[property]
      aprop1 = order[pos] in property_2_element_2_relation[property]
      for other in order:
        if other in property_2_element_2_relation[property]:
          apropn = True; break
      else: apropn = False
      #for other in remnants:
      #  if other is element: continue
      #  if other in property_2_element_2_relation[property]:
      #    apropr = True; break
      #else: apropr = False
      
      if aprop0 and aprop1: score += 2
      
      elif (not apropn) and (not aprop0) and (not aprop1): score += 1
      #elif (not aprop0) and (not aprop1): score += 1
      
      #elif apropn and apropr and (not aprop0) and aprop1: score -= 1
      
      #elif apropn and (aprop0) and (not aprop1): score += 1
      
    #score += len(element_2_property_2_relation[element]) / len(properties)
    return score
  
  
  def do_step(remnants, order):
    best_elements_pos, score = bests([(element, pos) for element in remnants for pos in [-1, 0]], score_remnant)
    results = set()
    already = set()
    for element, pos in best_elements_pos:
      props = frozenset(element_2_property_2_relation.get(element) or [])
      if (props, pos) in already: continue
      already.add((props, pos))
      new_remnants = set(remnants)
      new_remnants.remove(element)
      if pos == -1: results.add((frozenset(new_remnants), order + (element, )))
      else:         results.add((frozenset(new_remnants), (element, ) + order))
    return results
  

  results = set()
  for first_element in best_first_elements:
    results.add((frozenset(elements) - frozenset([first_element]), (first_element, )))

  nb = 1
  while True:
    finished = True
    new_results = set()
    for (remnants, order) in results:
      if remnants:
        finished = False
        new_results.update(do_step(remnants, order))
      else:
        new_results.add((remnants, order))
    results = new_results
    print(nb, len(results), file = sys.stderr)
    nb += 1
    if finished: break
    
  def score_order(order):
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
            nb_hole += 1
            
      if not end is None:
        # After end, it is not a hole!
        if end != i: nb_hole -= 1
        
        length = end - start + 1
        
        if length > len(property_2_element_2_relation[property]):
          total_hole_length += length - len(property_2_element_2_relation[property])
          nb_prop_with_hole += 1
          
    return (-nb_prop_with_hole, -nb_hole * 3 + -total_hole_length, sum_of_hatch_pos)
  
  orders = [order for (remnants, order) in results]
  print("Testing %s element orders..." % len(orders), file = sys.stderr)
  order, score = best(orders, score_order, score0 = (-sys.maxsize, -sys.maxsize, -sys.maxsize))

  return list(order)





def best_elements_order_pca(relations, elements = None, filter_order = None):
  present_elements, present_element_groups, properties, property_groups, element_2_property_2_relation, property_2_element_2_relation = relations_2_model(relations)
  if not elements: elements = present_elements

  import numpy
  from matplotlib.mlab import PCA
  
  array = []
  for element in elements:
    array.append([])
    for property in properties:
      if property in element_2_property_2_relation[element]:
        array[-1].append(1.0)
      else:
        array[-1].append(0.0)
  array = numpy.array(array)
  
  pca = PCA(array)
  
  element_2_x = { elements[i] : pca.Y[i, 0] for i in range(len(elements)) }
  
  orders = list(elements)
  orders.sort(key = lambda element: element_2_x[element])
  return orders



def best_elements_order_optim(relations, elements = None, filter_order = None, nb_tested_solution = 10000, optim_module = None, bench = False):
  if optim_module is None: import metaheuristic_optimizer.artificial_feeding_birds as optim_module
  
  present_elements, present_element_groups, properties, property_groups, element_2_property_2_relation, property_2_element_2_relation = relations_2_model(relations)
  if not elements: elements = present_elements
  elements = set(elements)
  for e in elements:
    if not e in element_2_property_2_relation: element_2_property_2_relation[e] = {} # Element with no relation are not present
  for p in properties:
    if not p in property_2_element_2_relation: property_2_element_2_relation[p] = {} # Property with no relation are not present
    
  def score_order(*order):
    nb_hole           = 0
    nb_prop_with_hole = 0
    total_hole_length = 0
    hatch_diff        = 0
    for property in properties:
      if isinstance(property.weight, str): 
        prop_weight = 1
      else:
        prop_weight = property.weight or 1
      
      start    = None
      end      = None
      in_hole  = False
      in_hatch = None
      for i, element in enumerate(order):
        if element in property_2_element_2_relation[property]:
          if start is None: start = i
          end = i
          in_hole = False
          relation = property_2_element_2_relation[property][element]
          new_in_hatch = relation.hatch, relation.color
          if new_in_hatch != in_hatch:
            hatch_diff += 1 # property.weight or 1
            in_hatch = new_in_hatch
        else:
          if (not start is None) and (not in_hole):
            in_hole = True
            nb_hole += prop_weight * element.weight
            in_hatch = None
            
      if not end is None:
        if end != i: nb_hole -= prop_weight  # After end, it is not a hole!
        
        length = end - start + 1
        
        if length > len(property_2_element_2_relation[property]):
          total_hole_length += (length - len(property_2_element_2_relation[property])) * prop_weight
          nb_prop_with_hole += prop_weight
          
    # Favor orders maintaining groups
    #groups_preserved = 0
    #for i in range(len(order) - 1):
    #  if order[i].group == order[i + 1].group: groups_preserved += 1
    
    # Favor orders maintaining alphabetical order
    #order_keys_preserved = 0
    #for i in range(len(order) - 1):
    #  if order[i].order_key <= order[i + 1].order_key: order_keys_preserved += 1
    
    #return (nb_prop_with_hole, nb_hole * 3 + -total_hole_length, -sum_of_hatch_pos, -groups_preserved, -order_keys_preserved)
    #return (nb_prop_with_hole * 5 + nb_hole * 3 + total_hole_length)
    #return nb_hole, nb_prop_with_hole, total_hole_length
    #return nb_prop_with_hole, total_hole_length, nb_hole
    #return nb_prop_with_hole + nb_hole + total_hole_length
    #return nb_prop_with_hole, nb_hole, total_hole_length, hatch_diff
    #return nb_hole, total_hole_length, hatch_diff
    return nb_hole + nb_prop_with_hole + 4 * total_hole_length / len(elements), nb_prop_with_hole, nb_hole, total_hole_length, hatch_diff
    
  def cost(ranks):
    pairs = sorted(zip(ranks, elements), key = lambda a: a[0])
    order = [element for (rank, element) in pairs]
    return score_order(*order)
  
  #import optim.artificial_bee_colony as optim_module
  #import optim.artificial_feeding_birds as optim_module
  #algo  = optim_module.NumericAlgorithm(cost, nb_dimension = len(elements))
  
  #algo.run(nb_tested_solution = nb_tested_solution)
  #ranks = algo.get_best_position()
  #pairs = sorted(zip(ranks, elements), key = lambda a: a[0])
  #order = [element for (rank, element) in pairs]
  
  #import optim.ant_colony_optimization as optim_module
  #algo  = optim_module.OrderingAlgorithm(list(elements), lambda a: score_order(*a),
  #                                       nb_ant = 8,
  #                                       evaporation_rate =  0.01,
  #                                       pheromon_default =  0.1,
  #                                       pheromon_min     =  0.1,
  #                                       pheromon_max     = 10.0,
  #)
  
  #import optim.genetic_algorithm as optim_module
  
  algo  = optim_module.OrderingAlgorithm(list(elements), lambda a: score_order(*a))
  
  #x = algo.multiple_run(250, nb_tested_solution = 10000)
  #print(x, file = sys.stderr)

  algo.run(nb_tested_solution = nb_tested_solution)
  
  # ACO-pants
  # import pants
  # max_shared = max(
  #   len(set(element_2_property_2_relation[e1]) & set(element_2_property_2_relation[e2]))
  #   for e1 in elements
  #   for e2 in elements
  #   if not(e1 is e2)
  # )
  # def lfunc(e1, e2):
  #   return (max_shared - len(set(element_2_property_2_relation[e1]) & set(element_2_property_2_relation[e2]))) * 2.0
  # def cfunc(indexes):
  #   return score_order(*[world.data(i) for i in indexes])
  # world    = pants.World(list(elements), lfunc, cfunc)
  # solver   = pants.Solver(limit = 2000, ant_count = 5)
  # solution = solver.solve(world)
  # print(list(elements))
  # print(solution.visited)
  # print(cfunc(solution.visited))
  # return solution.distance
  
  
  if bench: return algo.get_lowest_cost()
  
  order = algo.get_best_position()

  # Optimize alphabetical order
  def get_hatches(property_2_relation):
    return [(property_2_relation[p].hatch, property_2_relation[p].color) for p in properties if p in property_2_relation]
    
  i = 0
  while True:
    if i >= len(order): break
    current_memberships  = frozenset(element_2_property_2_relation[order[i]])
    current_hatches      = get_hatches(element_2_property_2_relation[order[i]])
    nb_identical_element = 1
    while True:
      if i + nb_identical_element >= len(order): break
      new_element = order[i + nb_identical_element]
      if order[i].group != new_element.group: break
      new_memberships = frozenset(element_2_property_2_relation[new_element])
      if current_memberships != new_memberships: break
      new_hatches = get_hatches(element_2_property_2_relation[new_element])
      if current_hatches != new_hatches:
        break
      nb_identical_element += 1
      
    if nb_identical_element > 1:
      order[i : i + nb_identical_element] = sorted(order[i : i + nb_identical_element], key = lambda e: e.order_key)
      
    i += nb_identical_element
    
  return order

















def best_elements_order_hybrid(relations, elements = None, filter_order = None, nb_tested_solution = 10000):
  present_elements, present_element_groups, properties, property_groups, element_2_property_2_relation, property_2_element_2_relation = relations_2_model(relations)
  if not elements: elements = present_elements
  elements = set(elements)
  for e in elements:
    if not e in element_2_property_2_relation: element_2_property_2_relation[e] = {} # Element with no relation are not present
  for p in properties:
    if not p in property_2_element_2_relation: property_2_element_2_relation[p] = {} # Property with no relation are not present
    
  def get_number_of_relation(e0):
    return len([prop for prop in element_2_property_2_relation[e0] if len(property_2_element_2_relation[prop]) > 1])
  candidate_first_elements, best_score = bests(elements, get_number_of_relation)
  
  properties_with_more_than_one_element = [
    property for property in properties
    if len(property_2_element_2_relation[property]) > 1
  ]

  
  insertion_score_cache = {}
  def insertion_score(element, position, order, order_set):
    if   position == "beginning": neighbor = order[ 0]
    else:                         neighbor = order[-1]
    score = 0

    for x in element_2_property_2_relation[element]:
      score += 2 * (x in element_2_property_2_relation[neighbor])
      
    for y in properties_with_more_than_one_element:
      if ((not y in element_2_property_2_relation[element]) and
          order_set.isdisjoint(property_2_element_2_relation[y])): score += 1
          
    insertion_score_cache[element, position, order] = score
    return score
  
  
  def cost(priorities): return score_order(priorities_2_order(priorities))
  
  def priorities_2_order(priorities):
    return priorities
    for i in range(len(priorities)): priorities[i]._priority = i
    
    first_element = candidate_first_elements[0]
    for e in candidate_first_elements[1:]:
      if e._priority > first_element._priority: first_element = e
    order = (first_element,)
    
    remnants = list(elements)
    remnants.remove(first_element)
    
    order_set = set(order)
    
    while remnants:
      best_score    = -999
      best_priority = -1
      
      for e in remnants:
        score = insertion_score_cache.get((e, "beginning", order))
        if score is None: score = insertion_score(e, "beginning", order, order_set)
        if ((e._priority > best_priority) and (score >= best_score)) or (score > best_score):
          best_score          = score
          best_priority       = e._priority
          best_element        = e
          best_position       = "beginning"
        score = insertion_score_cache.get((e, "end", order))
        if score is None: score = insertion_score(e, "end", order, order_set)
        if ((e._priority > best_priority) and (score >= best_score)) or (score > best_score):
          best_score          = score
          best_priority       = e._priority
          best_element        = e
          best_position       = "end"
          
          
      remnants.remove(best_element)
      order_set.add(best_element)
      if   best_position == "beginning": order = (best_element,) + order
      else:                              order = order + (best_element,)
      
    return order
  
  def score_order(order):
    nb_hole           = 0
    nb_prop_with_hole = 0
    total_hole_length = 0
    #sum_of_hatch_pos  = 0
    for property in properties:
      start   = None
      end     = None
      in_hole = False
      for i, element in enumerate(order):
        if element in property_2_element_2_relation[property]:
          if start is None: start = i
          end = i
          in_hole = False
          #if property_2_element_2_relation[property][element].hatch: sum_of_hatch_pos += i
        else:
          if (not start is None) and (not in_hole):
            in_hole = True
            nb_hole += 1
            
      if not end is None:
        # After end, it is not a hole!
        if end != i: nb_hole -= 1
        
        length = end - start + 1
        
        if length > len(property_2_element_2_relation[property]):
          total_hole_length += length - len(property_2_element_2_relation[property])
          nb_prop_with_hole += 1
          
          
    #groups_preserved = 0 # Favor orders maintaining groups
    #for i in range(len(order) - 1):
    #  if order[i].group == order[i + 1].group: groups_preserved += 1
    
    
    #order_keys_preserved = 0 # Favor orders maintaining alphabetical order
    #for i in range(len(order) - 1):
    #  if order[i].order_key <= order[i + 1].order_key: order_keys_preserved += 1
    
    #return (-nb_prop_with_hole, -nb_hole * 3 + -total_hole_length, sum_of_hatch_pos, groups_preserved, order_keys_preserved)
    
    #return (nb_prop_with_hole, nb_hole * 3 + total_hole_length, nb_hole)
    #return (total_hole_length, nb_hole)
    return (nb_hole * 3 + total_hole_length, nb_hole, total_hole_length)
    #return (nb_hole, total_hole_length)
    #return (nb_hole, nb_prop_with_hole, total_hole_length)
    #return total_hole_length
    #return (nb_prop_with_hole, nb_hole, total_hole_length)
    
  import metaheuristic_optimizer.artificial_feeding_birds as optim_module
  algo  = optim_module.OrderingAlgorithm(list(elements), cost)
  algo.run(nb_tested_solution = nb_tested_solution)
  
  
  lowest_cost = algo.get_lowest_cost()
  if isinstance(lowest_cost, tuple): lowest_cost = list(lowest_cost)
  
  print("Tested %s element orders..." % algo.nb_cost_computed, file = sys.stderr)
  print("Lowest cost: %s"             % lowest_cost, file = sys.stderr)
  
  order = priorities_2_order(algo.get_best_position())
  
  # Reorder alphabetically consecutive sublist or identical elements (due to optimization, only one order is tested)
  order = list(order)
  i = 0
  while True:
    if i >= len(order): break
    nb_identical_element = 1
    while True:
      if i + nb_identical_element >= len(order): break
      if order[i].group != order[i + nb_identical_element].group: break
      if frozenset(element_2_property_2_relation[order[i]]) != frozenset(element_2_property_2_relation[order[i + nb_identical_element]]): break
      nb_identical_element += 1
      
    if nb_identical_element > 1:
      order[i : i + nb_identical_element] = sorted(order[i : i + nb_identical_element], key = lambda e: e.order_key)
      
    i += nb_identical_element
    
  return order



















def best_elements_order_hybrid2(relations, elements = None, filter_order = None, nb_tested_solution = 10000):
  present_elements, present_element_groups, properties, property_groups, element_2_property_2_relation, property_2_element_2_relation = relations_2_model(relations)
  if not elements: elements = present_elements
  elements = set(elements)
  for e in elements:
    if not e in element_2_property_2_relation: element_2_property_2_relation[e] = {} # Element with no relation are not present
  for p in properties:
    if not p in property_2_element_2_relation: property_2_element_2_relation[p] = {} # Property with no relation are not present
    
  def get_number_of_relation(e0):
    return len([prop for prop in element_2_property_2_relation[e0] if len(property_2_element_2_relation[prop]) > 1])
  candidate_first_elements, best_score = bests(elements, get_number_of_relation)
  
  properties_with_more_than_one_element = [
    property for property in properties
    if len(property_2_element_2_relation[property]) > 1
  ]

  
  insertion_score_cache = {}
  def insertion_score(element, position, order, order_set):
    if   position == "beginning": neighbor = order[ 0]
    else:                         neighbor = order[-1]
    score = 0

    for x in element_2_property_2_relation[element]:
      score += 2 * (x in element_2_property_2_relation[neighbor])
      
    for y in properties_with_more_than_one_element:
      if ((not y in element_2_property_2_relation[element]) and
          order_set.isdisjoint(property_2_element_2_relation[y])): score += 1
          
    insertion_score_cache[element, position, order] = score
    return score
  
  
  def fly():
    if len(candidate_first_elements) == 1:
      first_element = candidate_first_elements[0]
    else:
      first_element = random.choice(candidate_first_elements)
    order = (first_element,)
    
    remnants = list(elements)
    remnants.remove(first_element)
    
    order_set = set(order)
    
    while remnants:
      best_score      = -999
      best_insertions = []
      for e in remnants:
        score = insertion_score(e, "beginning", order, order_set)
        if   score == best_score: best_insertions.append((e, "beginning"))
        elif score >  best_score: best_insertions = [(e, "beginning")]
        
        score = insertion_score(e, "end", order, order_set)
        if   score == best_score: best_insertions.append((e, "end"))
        elif score >  best_score: best_insertions = [(e, "end")]
        
      if len(best_insertions) == 1:
        best_element, best_position = best_insertions[0]
      else:
        best_element, best_position = random.choice(best_insertions)
        
      remnants.remove(best_element)
      order_set.add(best_element)
      if   best_position == "beginning": order = (best_element,) + order
      else:                              order = order + (best_element,)
      
    return list(order)
  
  def cost(order):
    nb_hole           = 0
    nb_prop_with_hole = 0
    total_hole_length = 0
    #sum_of_hatch_pos  = 0
    for property in properties:
      start   = None
      end     = None
      in_hole = False
      for i, element in enumerate(order):
        if element in property_2_element_2_relation[property]:
          if start is None: start = i
          end = i
          in_hole = False
          #if property_2_element_2_relation[property][element].hatch: sum_of_hatch_pos += i
        else:
          if (not start is None) and (not in_hole):
            in_hole = True
            nb_hole += 1
            
      if not end is None:
        # After end, it is not a hole!
        if end != i: nb_hole -= 1
        
        length = end - start + 1
        
        if length > len(property_2_element_2_relation[property]):
          total_hole_length += length - len(property_2_element_2_relation[property])
          nb_prop_with_hole += 1
          
          
    #groups_preserved = 0 # Favor orders maintaining groups
    #for i in range(len(order) - 1):
    #  if order[i].group == order[i + 1].group: groups_preserved += 1
    
    
    #order_keys_preserved = 0 # Favor orders maintaining alphabetical order
    #for i in range(len(order) - 1):
    #  if order[i].order_key <= order[i + 1].order_key: order_keys_preserved += 1
    
    #return (-nb_prop_with_hole, -nb_hole * 3 + -total_hole_length, sum_of_hatch_pos, groups_preserved, order_keys_preserved)
    
    #return (nb_prop_with_hole, nb_hole * 3 + total_hole_length, nb_hole)
    #return (total_hole_length, nb_hole)
    #return (nb_hole * 3 + total_hole_length, nb_hole, total_hole_length)
    #return (nb_hole, total_hole_length)
    #return (nb_hole, nb_prop_with_hole, total_hole_length)
    return total_hole_length, nb_hole, nb_prop_with_hole
    #return (nb_prop_with_hole, nb_hole, total_hole_length)
    
  import metaheuristic_optimizer.artificial_feeding_birds as optim_module
  algo  = optim_module.OrderingAlgorithm(list(elements), cost, nb = 20)
  #algo.fly = fly
  algo.run(nb_tested_solution = nb_tested_solution)
  
  
  lowest_cost = algo.get_lowest_cost()
  if isinstance(lowest_cost, tuple): lowest_cost = list(lowest_cost)
  
  print("Tested %s element orders..." % algo.nb_cost_computed, file = sys.stderr)
  print("Lowest cost: %s"             % lowest_cost, file = sys.stderr)
  
  order = algo.get_best_position()
  
  # Reorder alphabetically consecutive sublist or identical elements (due to optimization, only one order is tested)
  order = list(order)
  i = 0
  while True:
    if i >= len(order): break
    nb_identical_element = 1
    while True:
      if i + nb_identical_element >= len(order): break
      if order[i].group != order[i + nb_identical_element].group: break
      if frozenset(element_2_property_2_relation[order[i]]) != frozenset(element_2_property_2_relation[order[i + nb_identical_element]]): break
      nb_identical_element += 1
      
    if nb_identical_element > 1:
      order[i : i + nb_identical_element] = sorted(order[i : i + nb_identical_element], key = lambda e: e.order_key)
      
    i += nb_identical_element
    
  return order
