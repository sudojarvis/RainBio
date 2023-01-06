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

import random

from rainbowbox.order_base import *
from metaheuristic_optimizer.artificial_feeding_birds import *




def best_boxes_order_heuristic(boxes, nb_col):
  bottom_boxes = []
  top_boxes    = []
  priority_2_boxes1 = defaultdict(list)
  for box in boxes:
    if   box.has_bottom_property(): continue
    if   len(box.ids) == nb_col:    bottom_boxes.append(box)
    elif len(box.ids) ==      1:    top_boxes   .append(box)
  for box in boxes:
    if   box.has_bottom_property(): bottom_boxes.append(box)
    elif 1 < len(box.ids) < nb_col:
      priority_2_boxes1[nb_col - box.get_width()].append(box)
      
  boxes_by_priority = [boxes for (priority, boxes) in sorted(list(priority_2_boxes1.items()))]
  
  
  
  orders_by_priority = []
  for boxes in boxes_by_priority:
    if len(boxes) < 5:
      orders_by_priority.append(all_orders(boxes))
    else:
      orders_by_priority.append([list(boxes), list(reversed(boxes))])
      


  
  #orders_by_priority = [all_orders(boxes) for boxes in boxes_by_priority]
  orders = all_combinations(orders_by_priority)
  print("Testing %s box orders..." % len(orders), file = sys.stderr)
  
  orders = [order + top_boxes for order in orders]
  
  def score_boxes_order(order):
    heights = [0] * nb_col
    nb_consecutive_boxes_of_same_nb = 0
    last_box = None
    for box in order:
      ids = list(range(box.get_x(), box.get_x() + box.get_width()))
      box_y = max(heights[col] for col in ids)
      for col in ids:
        heights[col] = box_y + box.get_approx_height()
      if last_box and (len(box.ids) == len(last_box.ids)):
        nb_consecutive_boxes_of_same_nb += 1
      last_box = box
    return -max(heights), -sum(heights), nb_consecutive_boxes_of_same_nb
  
  order, score = best(orders, score_boxes_order, score0 = (-sys.maxsize, -sys.maxsize))

  return bottom_boxes + (order or top_boxes)
  




class BoxGroup(object):
  def __init__(self, boxes):
    self.boxes    = boxes
    self.ids      = boxes[0].ids
    self.x        = boxes[0].get_x()
    self.width    = boxes[0].get_width()
    self.height   = sum(box.get_approx_height() for box in boxes)
    
class Heuristic(MetaHeuristic):
  def __init__(self, box_groupss, nb_col, top_boxes_heights):
    self.box_groupss       = box_groupss
    self.nb_col            = nb_col
    self.top_boxes_heights = top_boxes_heights
    self.random_2_box_group = {}
    x = 0
    for i in range(len(self.box_groupss)):
      if self.box_groupss[i][0].width == 1: continue # Ordering box of width 1 does not change anything!
      for j in range(len(box_groupss[i]) - 1):
        self.random_2_box_group[x] = i
        x += 1
    self.max_random = x - 1
    MetaHeuristic.__init__(self, self.cost, 20)
    
  def fly(self):
    r = []
    for box_groups in self.box_groupss:
      box_groups = list(box_groups)
      random.shuffle(box_groups)
      r.append(box_groups)
    return r
    
  def walk(self, bird):
    x = list(bird.position)
    modified_group_id = self.random_2_box_group[random.randint(0, self.max_random)]
    box_groups = x[modified_group_id] = list(x[modified_group_id])
    
    i = random.randint(0, len(box_groups) - 1)
    j = random.randint(0, len(box_groups) - 1)
    while i == j:
      j = random.randint(0, len(box_groups) - 1)
    box_groups[i], box_groups[j] = box_groups[j], box_groups[i]
    return x
  
  def cost(self, ordered_box_groupss):
    heights = [0] * self.nb_col
    last_box_group = None
    nb_consecutive_boxes_of_same_nb = 0
    #print(len(ordered_box_groupss))
    for box_groups in ordered_box_groupss:
      #print(len(box_groups), box_groups)
      for box_group in box_groups:
        #print(box_group.ids)
        ids = range(box_group.x, box_group.x + box_group.width)
        box_y = max(heights[col] for col in ids) + box_group.height
        for col in ids:
          heights[col] = box_y
          
        if last_box_group and (len(box_group.ids) == len(last_box_group.ids)):
          nb_consecutive_boxes_of_same_nb += 1
        last_box_group = box_group
        
    for i in range(self.nb_col): heights[i] += self.top_boxes_heights[i]
    
    return max(heights), sum(heights), -nb_consecutive_boxes_of_same_nb
    
    
    
def best_boxes_order_by_size_optim(boxes, nb_col):
  bottom_boxes = []
  bottom_boxes2= []
  top_boxes    = []
  priority_2_boxes = defaultdict(list)
  for box in boxes:
    if   box.has_bottom_property():    bottom_boxes2.append(box)
    if   box.get_width() == nb_col:    bottom_boxes .append(box)
    elif len(box.ids) == 1:            top_boxes    .append(box)
    else: priority_2_boxes[nb_col - box.get_width()].append(box)
    
  top_boxes_heights = [0] * nb_col
  for top_box in top_boxes:
    top_boxes_heights[top_box.get_x()] += top_box.get_approx_height()
    
  box_groupss = []
  for (priority, same_size_boxes) in sorted(list(priority_2_boxes.items())):
    box_groupss.append([])
    ids_2_boxes = defaultdict(list)
    for box in same_size_boxes: ids_2_boxes[box.ids].append(box)
    for similar_boxes in ids_2_boxes.values():
      box_group = BoxGroup(similar_boxes)
      box_groupss[-1].append(box_group)
      
  algo = Heuristic(box_groupss, nb_col, top_boxes_heights)
  if algo.max_random > 0:
    algo.run(nb_tested_solution = 1000)
  ordered_box_groupss = algo.get_best_position()
  
  bottom_boxes.sort(key = lambda box: -len(box.ids))
  
  order = bottom_boxes + bottom_boxes2
  
  for box_groups in ordered_box_groupss:
    for box_group in box_groups:
      for box in box_group.boxes:
        order.append(box)
        
  order.extend(top_boxes)
  
  return order


def best_boxes_order_by_cardinality(boxes, nb_col):
  bottom_boxes2= []
  middle_boxes = []
  for box in boxes:
    if   box.has_bottom_property():    bottom_boxes2.append(box)
    else:                              middle_boxes .append(box)
    

  #middle_boxes.sort(key = lambda box: (-box.get_width(), -len(box.ids), -sum(box.ids)))
  middle_boxes.sort(key = lambda box: (-len(box.ids), -box.get_width(), -sum(box.ids)))
    
  order = bottom_boxes2 + middle_boxes
  
  assert len(order) == len(boxes)
  
  return order


def best_boxes_order_by_cardinality(boxes, nb_col):
  bottom_boxes = []
  bottom_boxes2= []
  top_boxes    = []
  priority_2_boxes = defaultdict(list)
  for box in boxes:
    if   box.has_bottom_property(): bottom_boxes2.append(box)
    #if   len(box.ids) == nb_col: bottom_boxes .append(box)
    if   len(box.ids) > nb_col / 2: bottom_boxes .append(box)
    elif len(box.ids) == 1:         top_boxes    .append(box)
    else: priority_2_boxes[nb_col - len(box.ids)].append(box)
    
  top_boxes_heights = [0] * nb_col
  for top_box in top_boxes:
    top_boxes_heights[top_box.get_x()] += top_box.get_approx_height()
    
  box_groupss = []
  for (priority, same_size_boxes) in sorted(list(priority_2_boxes.items())):
    box_groupss.append([])
    ids_2_boxes = defaultdict(list)
    for box in same_size_boxes: ids_2_boxes[box.ids].append(box)
    for similar_boxes in ids_2_boxes.values():
      box_group = BoxGroup(similar_boxes)
      box_groupss[-1].append(box_group)
      
  algo = Heuristic(box_groupss, nb_col, top_boxes_heights)
  if algo.max_random > 0:
    algo.run(nb_tested_solution = 1000)
  ordered_box_groupss = algo.get_best_position()
  
  bottom_boxes.sort(key = lambda box: -len(box.ids))
  
  #box_sorted = lambda box: 
  #order = sorted(bottom_boxes, key = box_sorter)
  order = bottom_boxes + bottom_boxes2
  
  for box_groups in ordered_box_groupss:
    for box_group in box_groups:
      for box in box_group.boxes:
        order.append(box)

  order.extend(top_boxes)

  assert len(order) == len(boxes)
  
  return order

def best_boxes_order_optim(boxes, nb_col, nb_tested_solution = 1000):
  bottom_boxes = []
  bottom_boxes2= []
  other_boxes  = []
  for box in boxes:
    if   box.has_bottom_property(): bottom_boxes2.append(box)
    if   len(box.ids) == nb_col:    bottom_boxes .append(box)
    else: other_boxes.append(box)
    
  def cost(order):
    heights = [0] * nb_col
    nb_consecutive_boxes_of_same_nb = 0
    last_box = None
    for box in order:
      ids = list(range(box.get_x(), box.get_x() + box.get_width()))
      box_y = max(heights[col] for col in ids)
      for col in ids:
        heights[col] = box_y + box.get_approx_height()
      if last_box and (len(box.ids) == len(last_box.ids)):
        nb_consecutive_boxes_of_same_nb += 1
      last_box = box
    return max(heights), sum(heights), -nb_consecutive_boxes_of_same_nb
  
  algo = OrderingAlgorithm(other_boxes, cost)
  algo.run(nb_tested_solution = nb_tested_solution)
  order = bottom_boxes + bottom_boxes2 + algo.get_best_position()
  
  assert len(order) == len(boxes)

  return order


best_boxes_order = best_boxes_order_by_size_optim

V_DELTA = 0.12

def _split_by_box_header(boxes):
  if not [b for b in boxes if b.header_box]: return [boxes]
  boxess  = defaultdict(list)
  headers = []
  for box in boxes:
    header = box.header_box
    if isinstance(header, int):
      header = box.properties[0]
      headers.append(header)
    boxess[header].append(box)
  headers.sort(key = lambda box: -box.header_box)
  return [boxess[header] for header in headers]

def best_boxes_order_by_vertical_position(boxes, nb_col):
  for box in boxes: box.header_box = box.properties[0].header_box
  
  boxess = _split_by_box_header(boxes)
  
  ordered_boxes = []
  y = 0
  for boxes in boxess:
    boxes, y2 = _best_boxes_order_by_vertical_position(boxes, nb_col)
    y2 += 0.4
    for box in boxes:
      box.y += y
    ordered_boxes.extend(boxes)
    y += y2
  return ordered_boxes
  
def _best_boxes_order_by_vertical_position(boxes, nb_col):
  for box in boxes:
    box.vertical_pos = box.properties[0].vertical_pos
    box.y  = 0
    box.bottom_boxes = set()
  boxes.sort(key = lambda box: box.vertical_pos)
  
  col_2_last_box = [None] * nb_col
  previous_box = None
  
  for box in boxes:
    box.all_ids = list(range(box.get_x(), box.get_x2() + 1))
    box.top_boxes        = set(col_2_last_box[id] for id in box.all_ids if col_2_last_box[id])
    box.y_min            = max((b.y_min + b.max_weight + V_DELTA for b in box.top_boxes), default = 0)
    box.vertical_pos_min = max((b.vertical_pos for b in box.top_boxes), default = box.vertical_pos)
    
    for id in box.all_ids:
      if col_2_last_box[id]: col_2_last_box[id].bottom_boxes.add(box)
      col_2_last_box[id] = box
      
    if previous_box:
      previous_box.next_box = box
      box.previous_box      = previous_box
    else:
      box.previous_box      = None
    previous_box = box
    previous_box.next_box = None
    
  for box in reversed(boxes):
    if box.bottom_boxes:
      y_max1               = min((b.y_min - (box.max_weight + V_DELTA) for b in box.bottom_boxes))
    else:
      y_max1               = max((b.y_min        for b in boxes))
    if box.next_box:
      y_max2               = box.next_box.y_min
      box.vertical_pos_max = box.next_box.vertical_pos
      if set(box.all_ids) & set(box.next_box.all_ids):
        box.vertical_pos_max -= 1
    else:
      y_max2               = max((b.y_min        for b in boxes))
      box.vertical_pos_max = box.vertical_pos
      
    box.y_max = min(y_max1, y_max2)
    if box.y_max  < box.y_min: box.y_max  = box.y_min
    
    if box.y_max == box.y_min:
      box.y = box.y_min
    else:
      box.y = box.y_min + (box.y_max - box.y_min) * (box.vertical_pos - box.vertical_pos_min) / ((box.vertical_pos_max - box.vertical_pos_min) or 1)

    #print(box.vertical_pos, sorted(box.ids), "vp:", box.vertical_pos_min, box.vertical_pos_max, "y:", box.y_min, box.y_max, "=>", box.y)

  max_y = max(box.y for box in boxes)
  for box in boxes: box.y = max_y - box.y
  for box in boxes: box.y += boxes[-1].max_weight
  
  return boxes, max_y + boxes[-1].max_weight


def _get_y(boxes, vertical_pos):
  previous_box = boxes[0]
  for box in boxes:
    #if box.vertical_pos == vertical_pos: return box.y
    if box.vertical_pos  > vertical_pos:
      #print("    ", box.vertical_pos, previous_box.vertical_pos, box.y, previous_box.y, "  dif", previous_box.y - box.y)
      return previous_box.y - (previous_box.y - box.y) * (vertical_pos - previous_box.vertical_pos) / (box.vertical_pos - previous_box.vertical_pos)
    previous_box = box
    
def generate_vertical_pos_scale(boxes):
  boxess = _split_by_box_header(boxes)
  
  html = ""
  for boxes in boxess:
    html += _generate_vertical_pos_scale(boxes)
  return html
  
def _generate_vertical_pos_scale(boxes, tick = 25):
  html = ""
  vertical_pos = 0
  previous_y = -1000
  for box in boxes:
    if not isinstance(box.header_box, int):
      
      vertical_pos = box.vertical_pos# - box.vertical_pos % tick
      break
    
    
  while True:
    y = _get_y(boxes, vertical_pos or 1)
    if abs(y - previous_y) > 1.5:
      extra = ""
      if vertical_pos % 100 == 0: extra += "font-weight: bold; "
      html += """<div style="%sposition: absolute; left: -4em; width: 3.5em; vertical-align: middle; text-align: right; bottom: %sem;">%s</div>\n""" % (extra, y - 1.0, vertical_pos or 1)
      previous_y = y
    vertical_pos += tick - (vertical_pos % tick)
    if vertical_pos > boxes[-1].vertical_pos: break
    
  y = boxes[-1].y
  html += """<div style="position: absolute; left: -4em; width: 3.5em; vertical-align: middle; text-align: right; bottom: %sem;">%s</div>\n""" % (y - 1.0, boxes[-1].vertical_pos or 1)
  
  return html
  
