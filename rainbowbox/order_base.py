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

import sys
from collections import defaultdict

from rainbowbox.model import *

def all_subsets(s):
  """returns all the subsets included in this set."""
  r = [set()]
  for i in s:
    for j in r[:]:
      r.append(j | set([i]))
  return r

def all_sublists(l):
  """returns all the sublists included in this list."""
  r = [[]]
  for length in range(1, len(l) + 1):
    for start in range(0, len(l) - length + 1):
      r.append(l[start : start + length])
  return r

def all_orders(l):
  """returns all the orders of the elements in the given list."""
  if len(l) == 1: return [l]
  r = []
  for i in l:
    l2 = l[:]
    l2.remove(i)
    for rest in all_orders(l2):
      r.append([i] + rest)
  return r

def all_combinations(l):
  """returns all the combinations of the sublist in the given list (i.e. l[0] x l[1] x ... x l[n])."""
  if len(l) == 0: return []
  if len(l) == 1: return l[0]
  r = []
  for a in l[0]: r.extend(a + b for b in all_combinations(l[1:]))
  return r


def best(items, score_func, score0 = -sys.maxsize):
  best_item  = None
  best_score = score0
  for item in items:
    score = score_func(item)
    if score > best_score:
      best_score = score
      best_item  = item
  return best_item, best_score

def bests(items, score_func, score0 = -sys.maxsize):
  best_items = None
  best_score = score0
  for item in items:
    score = score_func(item)
    if   score == best_score:
      best_items.append(item)
    elif score >  best_score:
      best_score = score
      best_items = [item]
  return best_items, best_score


