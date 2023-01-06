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

from rainbowbox.model import *
from rainbowbox.color import *

from collections import defaultdict
import math, numpy

import matplotlib
matplotlib.use('Agg')

from matplotlib.mlab import PCA
from matplotlib import pylab

def principal_component_analysis(t, n = 2):
  samples, features = t.shape
  mean_vec = t.mean(axis = 0)
  data_c = (t - mean_vec).T
  covar = numpy.cov(data_c)
  evals, evecs = numpy.linalg.eig(covar)
  indices = evals.argsort()[::-1]
  evecs = evecs[:, indices]
  basis = evecs[:,:n]
  energy = evals[:n].sum()
  new_t = t.dot(basis)
  return new_t, basis, evals

def amplify(x):
  return 0.5 + math.sin((x * 2.0 - 1.0) * math.pi / 2.0) / 2.0

MARKERS = "osp^Dhv*<>"

def create_glyph(relations, order, elements = None, t = None, ref_element = None, size = 4.0, wireframe = True):
  present_elements, present_element_groups, properties, property_groups, element_2_property_2_relation, property_2_element_2_relation = relations_2_model(relations)
  elements = elements or present_elements
  
  #for i in range(len(properties)): properties[i]._glyph_id = i

  current_marker = -1
  def new_marker():
    nonlocal current_marker
    current_marker += 1
    return MARKERS[current_marker]
  color_2_marker = defaultdict(new_marker)
  for element in elements: element.marker = color_2_marker[element.color]
  
  
  if t is None:
    for i in range(len(order     )): order     [i]._glyph_id = i
    t = numpy.zeros((len(elements), len(properties)))
    for element in elements:
      for property in element_2_property_2_relation.get(element) or ():
        #relation = element_2_property_2_relation[element][property]
        t[element._glyph_id, property._glyph_id] = 1.0#relation.get_weight_or_default()
  else:
    for i in range(len(elements  )): elements  [i]._glyph_id = i
        
  if  ref_element is None: ref_element = order[(len(order) - 1) // 2]
  if (ref_element is order[0]) or (ref_element is order[-1]): ref_element = None
  
  new_t, basis, variances = principal_component_analysis(t)
  
  # Mirror horizontally if the PCA is mirrored compared to order, at the ref_element position
  if ref_element:
    i = order.index(ref_element)
    if new_t[order[i - 1]._glyph_id, 0] > new_t[order[i + 1]._glyph_id, 0]:
      new_t[:,0] *= -1.0
      
  fig = pylab.figure()
  if   variances[1] < 0.25:
    fig.set_size_inches(size, size * 0.25)
  elif variances[0] == 0.0:
    fig.set_size_inches(0.25, 0.25)
  else:
    fig.set_size_inches(size, max(size * variances[1] / variances[0], size / 10.0))
    
  sub_fig = fig.add_subplot(111)
  sub_fig.axis("off")
  
  #for i in range(len(order) - 1):
  #  e1 = order[i]
  #  e2 = order[i + 1]
  #  p1 = new_t[e1._glyph_id, 0], new_t[e1._glyph_id, 1]
  #  p2 = new_t[e2._glyph_id, 0], new_t[e2._glyph_id, 1]
  #  
  #  sub_fig.plot([p1[0], p2[0]], [p1[1], p2[1]], color = (0,0,0), linewidth = 5.5)
  
  nb_step = 10
  if wireframe:
    for i in range(len(order) - 1):
      e1 = order[i]
      e2 = order[i + 1]
      p1 = new_t[e1._glyph_id, 0], new_t[e1._glyph_id, 1]
      p2 = new_t[e2._glyph_id, 0], new_t[e2._glyph_id, 1]

      sub_fig.plot([p1[0], p2[0]], [p1[1], p2[1]], color = (0.5,0.5,0.5), linewidth = 6.0)

      if e1.color == e2.color:
        sub_fig.plot([p1[0], p2[0]], [p1[1], p2[1]], color = e1.color, linewidth = 4.0)
      else:
        step1 = p1
        for i in range(nb_step):
          f     = (i+1) / nb_step
          g     = 1.0 - f
          step2 = (p1[0] * g + p2[0] * f, p1[1] * g + p2[1] * f)

          f     = amplify(i / (nb_step - 1))
          color = rgb_blend_color(e1.color, e2.color, f)

          sub_fig.plot([step1[0], step2[0]], [step1[1], step2[1]], color = color, linewidth = 4.0)
          step1 = step2
        
        
  #pos_2_elements = defaultdict(list)
  #for e in order:
  #  e._glyph_pos = p = new_t[e._glyph_id, 0], new_t[e._glyph_id, 1]
  #  pos_2_elements[p].append(e)

  pos_elements = []
  for e in order:
    e._glyph_pos_acp = e._glyph_pos = numpy.array([new_t[e._glyph_id, 0], new_t[e._glyph_id, 1]])
    if not(pos_elements) or (e._glyph_pos_acp[0] != pos_elements[-1][0]._glyph_pos_acp[0]) or (e._glyph_pos_acp[1] != pos_elements[-1][0]._glyph_pos_acp[1]):
      pos_elements.append([e])
    else:
      pos_elements[-1].append(e)
      
  for els in pos_elements:
    e = els[0]
    x, y = e._glyph_pos
    sub_fig.plot([x], [y], e.marker, color = (0,0,0), markersize = 9)
    if e.color != (1,1,1): sub_fig.plot([x], [y], e.marker, color = e.color)
    
  a = sub_fig.axes.transData.transform_point((0.0, 0.0))
  b = sub_fig.axes.transData.transform_point((1.0, 1.0))
  to_pixel = numpy.array([b[0] - a[0], b[1] - a[1]])
  
  if (len(pos_elements) > 1):
    for els in pos_elements:
      if len(els) > 1:
        if   els[0]._glyph_id == 0:
          vec = order[els[-1]._glyph_id + 1]._glyph_pos_acp - els[0]._glyph_pos_acp
        elif els[-1]._glyph_id == len(order) - 1:
          vec = order[els[ 0]._glyph_id - 1]._glyph_pos_acp - els[0]._glyph_pos_acp
        else:
          vec1 = order[els[ 0]._glyph_id - 1]._glyph_pos_acp - els[0]._glyph_pos_acp
          vec2 = order[els[-1]._glyph_id + 1]._glyph_pos_acp - els[0]._glyph_pos_acp
          #vec1 = vec1 / numpy.linalg.norm(vec1)
          #vec2 = vec2 / numpy.linalg.norm(vec2)
          #vec  = - vec1 - vec2
          if numpy.linalg.norm(vec1) > numpy.linalg.norm(vec2): vec = vec1; els.reverse()
          else:                                                 vec = vec2
          
        vec = vec / numpy.linalg.norm(vec)
        #vec = (vec / to_pixel) * 7.5
        vec = vec / numpy.linalg.norm(to_pixel)
        vec = vec * 11.0
        
        for i, e in enumerate(els):
          #if i == 0: continue
          x, y = e._glyph_pos = e._glyph_pos_acp + i * vec
          sub_fig.plot([x], [y], e.marker, color = (0,0,0), markersize = 9)
          if e.color != (1,1,1): sub_fig.plot([x], [y], e.marker, color = e.color)
          
  fig.subplots_adjust(left=0.0, right=1.0, top=1.0, bottom=0.0)
  return fig


