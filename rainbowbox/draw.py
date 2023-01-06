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

import os, sys
from collections import defaultdict

from rainbowbox.model import *
from rainbowbox.model import _get_property_weight
from rainbowbox.order_elements import *
from rainbowbox.order_boxes    import *
import rainbowbox.color

_ID_BASE_NAME = "rainbowboxID%s"

if sys.version_info.minor < 4:
  _min = min
  _max = max
  def min(args, default = None):
    if not args: return default
    return _min(args)
  def max(args, default = None):
    if not args: return default
    return _max(args)

class Box(object):
  def __init__(self, ids, weighted, interactive):
    self.ids         = ids
    self.properties  = []
    self.color       = None
    self.weighted    = weighted
    self.interactive = interactive
    
  def finished(self, order, property_2_element_2_relation):
    # Holes
    self.holes = []
    in_hole = False
    for i in range(min(self.ids, default = 0), max(self.ids, default = 0) + 1):
      if i in self.ids:
        in_hole = False
      else:
        if in_hole: self.holes[-1][1] += 1
        else:
          self.holes.append([i, 1])
          in_hole = True
          
    # Weight
    if self.weighted:
      if len(self.properties) > 1: raise ValueError
      self.weight = _get_property_weight(self.properties[0], property_2_element_2_relation)
      if isinstance(self.weight, float):
        self.min_weight = self.weight
        self.max_weight = self.weight
      else:
        self.min_weight = min(self.weight)
        self.max_weight = max(self.weight)
        
    else:
      self.weight = None
      
    # Extra irregular weights
    if isinstance(self.weight, set):
      element_2_relation = property_2_element_2_relation[self.properties[0]]
      if self.interactive: self.min_weight = 1.0
      self.extra_irregular_weights = []
      for i in range(min(self.ids, default = 0), max(self.ids, default = 0) + 1):
        if i in self.ids:
          r = element_2_relation[order[i]]
          weight = element_2_relation[order[i]].weight
          self.extra_irregular_weights.append(weight - self.min_weight)
        else: # Hole
          self.extra_irregular_weights.append(0)
    else:
      self.extra_irregular_weights = None
      
  def get_x    (self): return min(self.ids, default = 0)
  def get_width(self): return max(self.ids, default = 0) - min(self.ids, default = 0) + 1
  def get_x2   (self): return max(self.ids, default = 0)
  
  def get_approx_height(self):
    if self.weight: return self.max_weight
    
    height = len(self.properties) + 0.1
    for i in self.ids:
      if i + 1 in self.ids: break
    else:
      height += 0.5 # Small size for label
    return height
  
  def __repr__(self): return """Box(%s)""" % list(self.ids)

  def has_bottom_property(self):
    for property in self.properties:
      if property.at_bottom: return True
    return False
  
def group_properties_no_group(property_groups, properties, property_2_element_2_relation):
  return [ [prop] for prop in properties]

def group_properties(property_groups, properties, property_2_element_2_relation):
  r = []
  group_2_properties = defaultdict(list)
  for property in properties:
    group_2_properties[property.group].append(property)
    
  for group in property_groups + [None]:
    if group in group_2_properties:
      widget_properties = []
      for property in list(group_2_properties[group]):
        for relation in property_2_element_2_relation[property].values():
          if relation.widget:
            widget_properties.append(property)
            group_2_properties[group].remove(property)
            break
          
      hatch_2_properties = defaultdict(list)
      for property in group_2_properties[group]:
        hatches  = tuple(property_2_element_2_relation[property][element].hatch for element in property_2_element_2_relation[property])
        hatches += tuple(property_2_element_2_relation[property][element].color for element in property_2_element_2_relation[property])
        hatch_2_properties[hatches].append(property)
      for hatches, hatches_properties in sorted(hatch_2_properties.items()):
        hatches_properties.sort(key = lambda property: property.order_key)
        r.append(hatches_properties)
        
      for widget_property in widget_properties:
        r.append([widget_property])
        
  return r
  
def group_properties_by_color(property_groups, properties, property_2_element_2_relation):
  group_2_priority = { None : 0 }
  i = 1
  for group in property_groups:
    group_2_priority[group] = i
    i += 1
    
  colors_2_properties = defaultdict(list)
  for property in properties:
    color = tuple(relation.color for relation in  property_2_element_2_relation[property].values())
    colors_2_properties[color].append(property)
    
  colors = list(colors_2_properties.keys())
  colors.sort()
  colors.reverse()
  
  r = []
  for color in colors:
    properties2 = colors_2_properties[color]
        
    properties2_2_priority = {}
    for property in properties2:
      properties2_2_priority[property] = (group_2_priority[property.group], property.order_key)
      
    widget_properties2 = []
    for property in properties2:
      for relation in property_2_element_2_relation[property].values():
        if relation.widget:
          widget_properties2.append(property)
          properties2.remove(property)
          break
        
    properties2.sort(key = lambda property: properties2_2_priority[property])
    r.append(properties2)
    
    widget_properties2.sort(key = lambda property: properties2_2_priority[property])
    for widget_property in widget_properties2:
      r.append([widget_property])
    
  return r


class HTMLPage(object):
  def __init__(self, title = "Rainbow Boxes", force_vertical_scrollbar = False, static_url = "", has_brython = False):
    self.title            = title
    self._next_id         =  0
    self.html             = ""
    self.element_2_color  = {}
    self.div_opened       = False
    if not static_url:
      try:
        from flask import url_for
        static_url = url_for("rainbowbox.static", filename = '')
      except: pass
    self.static_url       = static_url
    self.force_vertical_scrollbar = force_vertical_scrollbar
    self.javascripts      = ["%srainbowbox.js"  % static_url]
    self.css_sheets       = ["%srainbowbox.css" % static_url]
    self.has_brython      = has_brython
    self.hatch_white_size = 8
    self.box_vertical_sep = 2
    self.extra_head       = ""
    
    self.parent_id_2_height_ids     = {}
    self.parent_id_2_group_ids      = {}
    self.parent_id_2_title_ids      = {}
    self.parent_id_2_titles         = {}
    self.parent_id_2_div_ids        = {}
    self.parent_id_2_nb_cols        = {}
    self.parent_id_2_box_ids        = {}
    self.parent_id_2_sel_box_ids    = {}
    self.parent_id_2_sel_box_colors = {}
    self.group_id_2_cols            = {}
    self.box_id_2_cols              = {}
    self.box_id_2_heights           = {}
    self.box_id_2_y                 = {}
    
  def gen_id(self):
    self._next_id += 1
    return _ID_BASE_NAME % self._next_id
  
  def get_script(self):
    script  = """parent_id_2_height_ids     = %s;\n""" % repr(self.parent_id_2_height_ids)
    script += """parent_id_2_group_ids      = %s;\n""" % repr(self.parent_id_2_group_ids)
    script += """parent_id_2_title_ids      = %s;\n""" % repr(self.parent_id_2_title_ids)
    script += """parent_id_2_titles         = %s;\n""" % repr(self.parent_id_2_titles)
    script += """parent_id_2_div_ids        = %s;\n""" % repr(self.parent_id_2_div_ids)
    script += """parent_id_2_nb_cols        = %s;\n""" % repr(self.parent_id_2_nb_cols)
    script += """parent_id_2_box_ids        = %s;\n""" % repr(self.parent_id_2_box_ids)
    script += """parent_id_2_sel_box_ids    = %s;\n""" % repr(self.parent_id_2_sel_box_ids)
    script += """parent_id_2_sel_box_colors = %s;\n""" % repr(self.parent_id_2_sel_box_colors)
    script += """group_id_2_cols            = %s;\n""" % repr(self.group_id_2_cols)
    script += """box_id_2_cols              = %s;\n""" % repr(self.box_id_2_cols)
    script += """box_id_2_heights           = %s;\n""" % repr(self.box_id_2_heights)
    script += """box_id_2_y                 = %s;\n""" % repr(self.box_id_2_y)
    script += """box_vertical_sep           = %s;\n""" % repr(self.box_vertical_sep)
    script  = """<script type="text/javascript">
<!--
%s

%s
 -->
</script>
""" % (script, "")
    return script
  
  def get_script_brython(self):
    script  = """from browser import window\n"""
    script += """window.parent_id_2_height_ids     = %s\n""" % repr(self.parent_id_2_height_ids)
    script += """window.parent_id_2_group_ids      = %s\n""" % repr(self.parent_id_2_group_ids)
    script += """window.parent_id_2_title_ids      = %s\n""" % repr(self.parent_id_2_title_ids)
    script += """window.parent_id_2_titles         = %s\n""" % repr(self.parent_id_2_titles)
    script += """window.parent_id_2_div_ids        = %s\n""" % repr(self.parent_id_2_div_ids)
    script += """window.parent_id_2_nb_cols        = %s\n""" % repr(self.parent_id_2_nb_cols)
    script += """window.parent_id_2_box_ids        = %s\n""" % repr(self.parent_id_2_box_ids)
    script += """window.parent_id_2_sel_box_ids    = %s\n""" % repr(self.parent_id_2_sel_box_ids)
    script += """window.parent_id_2_sel_box_colors = %s\n""" % repr(self.parent_id_2_sel_box_colors)
    script += """window.group_id_2_cols            = %s\n""" % repr(self.group_id_2_cols)
    script += """window.box_id_2_cols              = %s\n""" % repr(self.box_id_2_cols)
    script += """window.box_id_2_heights           = %s\n""" % repr(self.box_id_2_heights)
    script += """window.box_id_2_y                 = %s\n""" % repr(self.box_id_2_y)
    script += """window.box_vertical_sep           = %s\n""" % repr(self.box_vertical_sep)
    return script
  
  def get_html(self): return self.html
  
  def get_html_with_header(self):
    if self.force_vertical_scrollbar:
      html_extra = ' style="overflow-y: scroll;"'
    else:
      html_extra = ""
      
    html= """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html%s>
<head>
<title>%s</title>
<meta charset="utf-8"/>""" % (html_extra, self.title)
    
    for i in self.css_sheets:
      html += """
<link rel="stylesheet" type="text/css" href="%s"/>""" % i
    for i in self.javascripts:
      if i.endswith(".py"):
        self.has_brython = True
        html += """
<script type="text/javascript" src="%s" type="text/python"></script>""" % i
      else:
        html += """
<script type="text/javascript" src="%s"></script>""" % i
    html += """
%s
</head>
<body style="margin: 0px; padding: 0px;" onload="move_boxes();%s" onresize="move_boxes();">
%s
%s
</body>
</html>""" % (self.extra_head, " brython(1);" if self.has_brython else "", self.get_script(), self.get_html())
    return html
  
  def show(self, sleep_time = 5.0):
    import os, os.path, webbrowser, tempfile, time
    tmpdir = tempfile.TemporaryDirectory(prefix = "tmp_rainbowbox_")
    
    for filename in ["rainbowbox.css", "rainbowbox.js", "rainbowbox_max_2_elements.js"]:
      f = open(os.path.join(tmpdir.name, filename), "w")
      f.write(open(os.path.join(os.path.dirname(__file__), "static", filename)).read())
      f.close()
      
    filename = os.path.join(tmpdir.name, "rainbowbox.html")
    f = open(filename, "wb")
    f.write(self.get_html_with_header().encode("utf8"))
    f.close()
    webbrowser.open_new_tab("file://%s" % filename)
    if sleep_time: time.sleep(sleep_time)
    return tmpdir
    
  def html_popup(self, label, details, tag = "div", classname = "", style = ""):
    if not details:
      if classname:
        return """<%s %s%s>%s</%s>""" % (tag, classname and ('class="%s" ' % classname) or "", style and ('style="%s" ' % style) or "", label, tag)
      else:
        return label
    return """<%s %s%sonMouseEnter="popup_enter(this, event);" onMouseOut="popup_exit(this, event);">%s<div class="rainbowbox_popup">%s</div></%s>""" % (tag, classname and ('class="%s" ' % classname) or "", style and ('style="%s" ' % style) or "", label, details, tag)
  
  def rainbowbox(self, relations, elements = None, order = None, colors = None, keep_previous_colors = False, empty_text = "(empty)", use_element_details_in_relation = False, optimize_box_order = True, sort_relation_by_color = False, interactive_boxes = False, black_and_white = False, property_order = None, versus = False, hideable_element = False, clickable_properties = False, has_vertical_pos = False, max_2_elements = False, grid = "background", display_border = True, large_padding = False):
    present_elements, element_groups, properties, property_groups, element_2_property_2_relation, property_2_element_2_relation = relations_2_model(relations)
    
    if max_2_elements:
      self.javascripts = ["%srainbowbox_max_2_elements.js"  % self.static_url]
      
    for prop in properties:
      if not prop.weight is None:
        weighted = True
        break
      else: weighted = False

    if not elements: elements = present_elements
    if not order:    order    = best_elements_order_optim(relations, elements)
    if not colors:
      if keep_previous_colors:
        colors = [self.element_2_color[element] for element in order]
      else:
        if black_and_white:
          colors = [rainbowbox.color.hsv2rgb(0.0, 0.0, 0.9)] * len(elements)
        else:
          colors = rainbowbox.color.rainbow_colors(len(elements) + 1)[:-1]
          
    if not keep_previous_colors:
      for i in range(len(order)):
        if not order[i].color: self.element_2_color[order[i]] = order[i].color = colors[i]
        else:                  self.element_2_color[order[i]] = colors[i] = order[i].color
        
    # Fix required if ordering removed some elements
    if len(order) != len(elements):
      for i in list(elements):
        if not i in order: elements.remove(i)
      for i in list(element_2_property_2_relation.keys()):
        if not i in order: del element_2_property_2_relation[i]
      for property in properties:
        for i in list(property_2_element_2_relation[property].keys()):
          if not i in order: del property_2_element_2_relation[property][i]
          
    total_element_weight = sum(element.weight for element in elements)
    x = 0.0
    for element in order:
      element.x     = x
      element.width = element.weight / total_element_weight
      x += element.width
      
    html = ""

    if large_padding == True:
      large_padding = 100.0 / (4 * len(order))
      
    parent_id = self.gen_id()
    self.parent_id_2_div_ids       [parent_id] = col_div_ids = [self.gen_id() for element in order]
    if interactive_boxes:
      self.parent_id_2_sel_box_ids [parent_id] = []
    self.parent_id_2_sel_box_colors[parent_id] = {}
    
    if has_vertical_pos:
      html += """<div style="margin-left: 4em;">"""
      
    html += """<table cellspacing="0" class="rainbowbox_header_table">\n"""
    html += """<tr class="rainbowbox_header_element_group">\n"""
    
    x = 0
    self.parent_id_2_group_ids[parent_id] = []
    current_group = None
    for i in range(len(order)):
      element = order[i]
      if not element.group is current_group:
        current_group = element.group
        group_id = self.gen_id()
        width    = 1
        while True:
          if i + width >= len(order): break
          if not order[i + width].group is current_group: break
          width += 1
        self.parent_id_2_group_ids[parent_id].append(group_id)
        self.group_id_2_cols[group_id] = list(range(x, x + width))
        html += """<td id="%s" colspan="%s"><div>""" % (group_id, width)
        html += self.html_popup(current_group.label, current_group.details)
        html += """</div></td>"""
        x += width

    if display_border:
      html += """<tr class="rainbowbox_header_element">\n"""
    else:
      html += """<tr class="rainbowbox_header_element_no_border">\n"""
      
    for element in elements:
      if element.border_color:
        has_border_color = True
        break
    else:
      has_border_color = False
      
    self.parent_id_2_title_ids[parent_id] = []
    self.parent_id_2_titles   [parent_id] = []
    for i, element in enumerate(order):
      title_id = element.html_id = self.gen_id()
      self.parent_id_2_title_ids[parent_id].append(title_id)
      self.parent_id_2_titles[parent_id].append(element.label)
      style = """width: %s%%; background-color: %s;""" % (100.0 * element.width, rainbowbox.color.rgb2web(*element.color))
      if element.border_color:
        style += " border-top: 0.8em solid %s;" % rainbowbox.color.rgb2web(*element.border_color)
      elif has_border_color:
        style += " border-top: 0.8em solid transparent;" # Border takes some place
      if   i == len(order) - 1:                     extra_class = ""
      elif element.group is not order[i + 1].group: extra_class = """ rainbowbox_header_element_td_border2"""
      else:                                         extra_class = """ rainbowbox_header_element_td_border1"""
      if versus:
        extra = """ onClick="select_comparator('%s', 0, %s); event.stopPropagation();" """ % (parent_id, i)
      else:
        extra = ""
      html += """<td id="%s" class="%s_class%s" onMouseEnter="on_element_enter(this, event);" onMouseOut="on_element_exit(this, event);" style="%s"%s>""" % (title_id, title_id, extra_class, style, extra)
      
      element_label = element.get_html()
      if hideable_element:
        element_label = """<input type="checkbox" onchange="toggle_column(%s, this.checked);"/> %s""" % (i, element_label)
      html += self.html_popup(element_label, element.details)
      html += """</td>"""
    html += """</tr>\n"""
    
    height_id = self.gen_id()
    self.parent_id_2_height_ids[parent_id] = [height_id]
    html += """<tr>\n"""

    for i in range(len(order)):
      if (i < len(order) - 1) and (order[i].group != order[i + 1].group):
        html += """<td class="rainbowbox_lined_td" """
      else:
        if   display_border and ((grid == "background") or ((not grid) and (i == len(order) - 1))):
          html += """<td class="rainbowbox_dashed_td" """
        elif display_border and (not grid) and (i == 0):
          html += """<td class="rainbowbox_lined_td_left" """
        else:
          html += """<td """
      if i == 0: html += """id="%s" """ % height_id
      html += """>"""
      if (i == 0) and not properties: html += """<div style="margin: 1em;" class="soc">%s</span>""" % empty_text
      html += """</td>\n"""
      
    html += """</tr></table>\n"""
    
    
    html += """<div class="rainbowbox_parent_0" style="height: 0px;" id="%s">\n""" % col_div_ids[0]
    html += """<div class="rainbowbox_parent_1" style="position: relative" id="%s">\n""" % parent_id
    
    self.parent_id_2_nb_cols[parent_id] = len(order)
    
    cols = list(range(len(order)))
    sublists = all_sublists(cols)
    sublists.sort(key = lambda x: -len(x))
    
    for property in properties:
      property.ids             = { i for i in cols if order[i] in property_2_element_2_relation[property] }
      property.non_hatched_ids = { i for i in cols if order[i] in property_2_element_2_relation[property] and not property_2_element_2_relation[property][order[i]].hatch }
      
    box = None
    def end_box(): box.finished(order, property_2_element_2_relation)
    def new_box(sublist):
      nonlocal box
      if box: end_box()
      return Box(sublist, weighted, interactive_boxes)
    boxes         = []
    sublist_2_box = {}
    sorted_properties = list(sorted(properties, key = lambda property: -len(property.ids)))
    for property in properties:
      sublist = frozenset(property.ids)
      if not sublist: continue
      if property.at_bottom:
        box = new_box(sublist)
        box.properties.append(property)
        box.color = property.color
        boxes.append(box)
        continue
      if weighted or (not sublist in sublist_2_box) or property.start_new_box or (sublist_2_box[sublist].color and (sublist_2_box[sublist].color != property.color)):
        box = sublist_2_box[sublist] = new_box(sublist)
        box.color = property.color
        boxes.append(box)
      sublist_2_box[sublist].properties.append(property)
    if box: end_box()
    boxes.reverse() # Needed to keep the box order right when start_new_box is used.
    
    self.parent_id_2_box_ids[parent_id] = []

    if property_order:
      prop2prio = { property_order[i] : -i  for i in range(len(property_order)) }
      boxes.sort(key = lambda box: min(prop2prio[prop] for prop in box.properties))
      
    elif optimize_box_order:
      if isinstance(optimize_box_order, bool): optimize_box_order = best_boxes_order
      boxes = optimize_box_order(boxes, len(order))
    else:
      boxes.sort(key = lambda box: (-box.get_width(), box.get_x()))
      
    if has_vertical_pos:
      scale = generate_vertical_pos_scale(boxes)
      html += scale
      
    self.boxes = boxes
    for box in boxes:
      box_html_id    = box.html_id = self.gen_id()
      box_x_i        = box.get_x()
      box_w_i        = box.get_width()
      box_x          = 100.0 * order[box_x_i].x
      box_w          = 0.0
      for i in range(box_x_i, box_x_i + box_w_i):
        box_w += 100.0 * order[i].width

      if max_2_elements and len(box.ids) == 2:
        box_x += 100.0 * 0.5 / len(order)
        box_w -= 100.0 * 1.0 / len(order)
        
        
      box_color      = box.color
      if not box_color:
        if isinstance(box.weight, set):
          element_2_relation = property_2_element_2_relation[box.properties[0]]
          box_color = rainbowbox.color.rgb_weighted_mean([colors[i] for i in box.ids], [element_2_relation[order[i]].weight for i in box.ids])
        else:
          if black_and_white:
            box_color = rainbowbox.color.hsv2rgb(0.0, 0.0, 0.9 - 0.25 * ((len(box.ids) - 1) / len(elements)))
          else:
            box_color = rainbowbox.color.box_color_mean([colors[i] for i in box.ids], len(elements))
      if interactive_boxes:
        self.parent_id_2_sel_box_colors[parent_id][box_html_id] = rainbowbox.color.rgb2css(*box_color)
        box_color = (0.9, 0.9, 0.9)
        
      holes = box.holes
      #print(holes)
      #for x in range(box_x_i + 1, box_x_i + box_w_i):
      #  holes.append([x, 0])
      #print(holes)
      #print()
      
      extra_style    = ""
      if box_x == 0:                 extra_style += " padding-left: 0px;"
      if box_x + box_w >= 99.999:    extra_style += " padding-right: 0px;"
      if box is boxes[0]:            extra_style += " padding-bottom: 0px;"
      
      box_has_hatch = False
      for property in box.properties:
        for id in sorted(box.ids):
          if property_2_element_2_relation[property][order[id]].hatch:
            box_has_hatch = True
            break
        else: continue
        break
      
      n_box_label       = 0
      background_color  = rainbowbox.color.rgb2web(*box_color)
      background_color2 = rainbowbox.color.rgb2web(*rainbowbox.color.rgb_lighten(box_color))
      
      self.parent_id_2_box_ids[parent_id].append(box_html_id)
      self.box_id_2_cols      [box_html_id] = sorted(box.ids)
      
      if box_has_hatch:
        hatch_color = rainbowbox.color.rgb2web(*rainbowbox.color.rgb_hatch_color(box_color))
        background  = """background-image: repeating-linear-gradient(135deg, %s, %s 12px, %s 12px, %s %spx);""" % (background_color, background_color, hatch_color, hatch_color, 12 + self.hatch_white_size)
      else:
        background  = "background-color: %s;" % background_color
      if interactive_boxes:
        extra = ''' onclick="on_box_click('%s', '%s');"''' % (parent_id, box_html_id)
      else:
        extra = ""

      extra_classes = " %s_class" % box_html_id
      if hideable_element:
        #extra_classes += " %s" % "".join(" rainbowbox_box_with_element_%s" % id for id in box.ids)
        extra_classes += " %s" % "".join(" rainbowbox_box_without_element_%s" % id for id in set(range(len(elements))) - box.ids)
      #html += """<div class="rainbowbox_box%s" id="%s" style="position: absolute; left: %s%%; width: %s%%;%s"%s>\n""" % (extra_classes, box_html_id, 100.0 * box_x / len(cols), 100.0 * box_w / len(cols), extra_style, extra)

      if large_padding:
        extra_style += "padding-left:%s%%; padding-right:%s%%;" % (large_padding, large_padding)
      html += """<div class="rainbowbox_box%s" id="%s" style="position: absolute; left: %s%%; width: %s%%;%s"%s>\n""" % (extra_classes, box_html_id, box_x, box_w, extra_style, extra)
        
      if box.extra_irregular_weights:
        td_width = 100.0 / len(box.extra_irregular_weights)
        if interactive_boxes:
          def html_extra_weight_table(is_bottom = False):
            h = ""
            h += """<div>"""
            h += """<table cellpadding="0" cellspacing="0" class="rainbowbox_extra_irregular_weights%s" width="100%%"><tr>\n""" % ("_bottom" * is_bottom)
            
            extra_height_ids = []
            for i in range(len(box.extra_irregular_weights)):
              if is_bottom: extra_weight = 0.0
              else:         extra_weight = box.extra_irregular_weights[i]
              h += """<td width="%s%%">\n""" % td_width
              
              extra_height_id = self.gen_id()
              extra_height_ids.append(extra_height_id)
              
              h += """<div id="%s" style="height: %sem; %s"></div>\n""" % (extra_height_id, extra_weight, background)
              h += """</td>\n"""
            h += """</tr></table>\n"""
            h += """</div>"""
            
            return h, extra_height_ids
          
          h, extra_height_ids = html_extra_weight_table()
          html += h
          height_id2 = self.gen_id()
          html += """<div id="%s" class="rainbowbox_box2" style="%s">\n""" % (height_id2, background)
          self.box_id_2_heights[box_html_id] = [height_id2, extra_height_ids]
          
        else: # non interactive
          def td_for_weight(weight, width = None, id = None):
            if weight == -1:      return ""
            if not width is None: td = """<td width="%s">""" % width
            else:                 td = """<td>"""
            td += """<div """
            if id: td += """id="%s" """ % id
            td += """style="height: %sem; %s"></div></td>\n""" % (weight, background)
            return td
          
          html += """<div style="margin-left: -2px; margin-right: -3px;">"""
          html += """<table cellpadding="0" cellspacing="0" class="rainbowbox_extra_irregular_weights" width="100%"><tr>\n"""
          
          extra_height_ids = []
          for i in range(len(box.extra_irregular_weights)):
            extra_weight = box.extra_irregular_weights[i]
            if i == 0: previous_extra_weight = 0.0
            else:      previous_extra_weight = min(extra_weight, box.extra_irregular_weights[i - 1])
            if i == len(box.extra_irregular_weights) - 1: next_extra_weight = 0.0
            else:                                         next_extra_weight = min(extra_weight, box.extra_irregular_weights[i + 1])
            html += """<td width="%s%%">\n""" % td_width
            
            extra_height_id = self.gen_id()
            extra_height_ids.append(extra_height_id)
            
            html += """<table cellpadding="0" cellspacing="0" class="rainbowbox_extra_irregular_weight" width="100%"><tr>\n"""
            html += td_for_weight(previous_extra_weight, 2)
            html += td_for_weight(extra_weight, id = extra_height_id)
            html += td_for_weight(next_extra_weight, 3)
            html += """</tr></table>\n"""
            
            html += """</td>\n"""
          html += """</tr></table>\n"""
          html += """</div>"""
          
          height_id2       = self.gen_id()
          extra_height_ids = extra_height_ids
          self.box_id_2_heights[box_html_id] = [height_id2, extra_height_ids]
          html += """<div id="%s" class="rainbowbox_box2" style="%s">\n""" % (height_id2, background)
          
      else: # regular
        if clickable_properties:
          html += """<div class="rainbowbox_box2" style="%s" onClick="window.on_box_click_user('%s');  event.stopPropagation();">\n""" % (background, box.html_id)
        else:
          html += """<div class="rainbowbox_box2" style="%s">\n""" % background
          
      if holes:
        if box.extra_irregular_weights: # Move the hole down
          h2 = 100.0 * max(.1, .45 * box.min_weight / box.max_weight)
          d = max(1.5, 5.0 * box.min_weight / box.max_weight)
          extra = [" height: %s%%;" % (100.0 - h2 - d),
                   " top: %s%%; height: %s%%;" % (100.0 - h2 + d, h2 - d) ]
        else:
          if box.weighted:
            if   box.min_weight < 0.5:
              extra = [" height: 35%;",
                       " top: 65%; height: 35%;"]
            elif box.min_weight < 1.0:
              extra = [" height: 40%;",
                       " top: 60%; height: 40%;"]
            else:
              extra = ["", ""]
          else: extra = ["", ""]
          
        for hole_x, hole_w in holes:
          for j in [1, 2]:
            hole_x2 = 100.0 * order[hole_x].x
            hole_w2 = 0.0
            hole_steps = []
            for k in range(hole_x, hole_x + hole_w):
              hole_steps.append(100.0 * order[k].width)
              hole_w2 += 100.0 * order[k].width
            if hole_w == 0:
              html += """<div class="rainbowbox_hole%s" style="left: %s%%; width: 0.6%%;%s">\n""" % (j, 100.0 * (hole_x2 - box_x) / box_w - 0.3, extra[j-1])
            else:
              if large_padding:
                hole_x2 -= large_padding
                hole_w2 += large_padding * 2.0
              html += """<div class="rainbowbox_hole%s" style="left: %s%%; width: %s%%;%s">\n""" % (j, 100.0 * (hole_x2 - box_x) / box_w, 100.0 * hole_w2 / box_w, extra[j-1])
            if (hole_w > 1) and (grid == "background"):
              html += """<table class="rainbowbox_hole_dashed_table" cellspacing="0"><tr>\n"""
              for i in range(hole_w):
                html += """<td style="width: %s%%;"></td>\n""" % (100.0 * hole_steps[i] / hole_w2)
              html += """</tr></table>\n"""
            html += """</div>\n"""
            
            
      # DIv opener / closer
      div_opened      = False
      has_region_div  = False
      previous_colors = []
      #details_div     = ""
      
      def open_div(property, has_color, has_hatch, label = None, details = None):
        nonlocal div_opened, has_region_div, previous_colors, n_box_label, html#, details_div
        if not div_opened:
          div_opened = True
          
          region_x, region_w = compute_best_region(property.ids)

          if max_2_elements and (len(property.ids) >= 2):
            region_x = box_x
            region_w = 100.0 * 1.0 / len(order)
            
          
          n_box_label += 1
          if n_box_label % 2 == 0: div_background_color = background_color2
          else:                    div_background_color = background_color

          add_color_separation_border = False
          if   has_color:
            colors = []
            div_background = "background-image: linear-gradient(90deg"
            x2 = 0
            for i in range(box_x_i, box_x_i + box_w_i):
              x1  = x2
              x2 += order[i].width * 100.0
              if order[i] in property_2_element_2_relation[groupped_properties[0]]:
                color = property_2_element_2_relation[groupped_properties[0]][order[i]].color or background_color
                colors.append(color)
                if isinstance(color, tuple) or isinstance(color, list): color = rainbowbox.color.rgb2web(*color)
              else: continue
              if x1 == 0: div_background += """, %s %s%%"""  % (color, 0)
              else:       div_background += """, %s %s%%"""  % (color, ((x1 + 0.2) / box_w) * 100.0)
              if i == box_x_i + box_w_i - 1: div_background += """, %s %s%%"""  % (color, 100)
              else:                          div_background += """, %s %s%%"""  % (color, ((x2 - 0.2) / box_w) * 100.0)
            div_background += """);"""
            if colors != previous_colors:
              for color1, color2 in zip(colors, previous_colors):
                if color1 == color2:
                  add_color_separation_border = True
                  div_background = "border-top: 1px solid white; " + div_background
                  break
              previous_colors = colors
            
          elif has_hatch:
            if n_box_label % 2 == 0: div_background = "background-image: linear-gradient(0deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0.2) 100%), linear-gradient(90deg"
            else:                    div_background = "background-image: linear-gradient(90deg"
            x2 = 0
            for i in range(box_x_i, box_x_i + box_w_i):
              x1  = x2
              x2 += order[i].width * 100.0
              if order[i] in property_2_element_2_relation[groupped_properties[0]]:
                hatch = property_2_element_2_relation[groupped_properties[0]][order[i]].hatch
              else:
                hatch = 0
              if x1 == 0: x1_ = 0
              else:       x1_ = ((x1 + 0.2) / box_w) * 100.0
              if i == box_x_i + box_w_i - 1: x2_ = 100
              else:                          x2_ = ((x2 - 0.2) / box_w) * 100.0
              if hatch:
                div_background += """, transparent %s%%, transparent %s%%""" % (x1_, x2_)
              else:
                div_background += """, %s %s%%, %s %s%%"""          % (background_color, x1_, background_color, x2_)
            div_background += """);"""
          else:
            div_background = "background-color: %s;" % div_background_color
            
          if details:  extra = ''' onMouseEnter="on_box_enter(this, event);" onMouseOut="on_box_exit(this, event);"'''
          else:        extra = ""
          
          if weighted: html += """<div class="rainbowbox_box_label_weighted" style="%s"%s>""" % (div_background, extra)
          else:        html += """<div class="rainbowbox_box_label" style="%s"%s>""" % (div_background, extra)
            
          #if details:  html += """<div class="rainbowbox_popup" style="display: none; top: 1em;">%s</div>\n""" % details
          #else:        html += "\n"
          if details: html += """<div class="rainbowbox_popup" style="display: none; top: 1em;">%s</div>\n""" % details
          else:       html += "\n"
          #html += "\n"
          #if details: details_div = """<div class="rainbowbox_popup2">%s</div>\n""" % details
          
          if (region_x != box_x_i) or (region_w != box_w_i): # Restrict to the biggest region
            has_region_div = True
            if region_x != box_x: padding = " padding-left: 0.2em;"
            else:                 padding = ""
            html += """<div style="position: relative; left: %s%%; width: %s%%;%s">\n""" % (100.0 * (region_x - box_x) / box_w, 100.0 * region_w / box_w, padding)
            
      def compute_best_region(ids):
        best_x = best_w = 0
        x = -1
        for i in range(min(ids), max(ids) + 2): # +2 pour dépasser au-delà
          if i in ids:
            if x == -1: x = order[i].x
          elif x != -1:
            if i == len(order): w = 1.0        - x
            else:               w = order[i].x - x
            if w > best_w:
              best_w = w
              best_x = x
            x = -1
        return 100.0 * best_x, 100.0 * best_w
      
      def close_div():
        nonlocal div_opened, has_region_div, n_box_label, html#, details_div
        if div_opened:
          if has_region_div:
            has_region_div = False
            html += """</div>"""
            
          #if details_div:
          #  html += details_div
            
          html += """</div>\n"""
          div_opened = False

      if weighted:                 group_properties_func = group_properties_no_group
      else:
        if sort_relation_by_color: group_properties_func = group_properties_by_color
        else:                      group_properties_func = group_properties
        
      for groupped_properties in group_properties_func(property_groups, box.properties, property_2_element_2_relation):
        # Already grouped by hatches => only look at groupped_properties[0]
        has_color       = False
        has_hatch       = False
        hatched_regions = [] # x, hatch, width
        current_hatch   = "nonexistentvalue"
        for id in sorted(box.ids):
          relation = property_2_element_2_relation[groupped_properties[0]][order[id]]
          if relation.color: has_color = True
          if relation.hatch: has_hatch = True
          if relation.hatch != current_hatch:
            current_hatch = relation.hatch
            hatched_regions.append([id, relation.hatch, 1])
          else:
            hatched_regions[-1][2] += 1
            
        has_hatch = (len(hatched_regions) > 1) or (hatched_regions[0][1] != 0)
        
        for property in groupped_properties:
          details = []
          for element in order:
            if element in property_2_element_2_relation[property]:
              relation = property_2_element_2_relation[property].get(element)
              if relation:
                if use_element_details_in_relation: detail = element.details
                else:                               detail = element.label
                if relation.details:
                  details.append("%s : %s<br/>" % (detail, relation.details))
                else:
                  details.append("%s<br/>" % detail)
          if   property.details:
            details = property.details
          elif details:
            details = """<div class="rainbowbox_popup_title">%s</div>\n%s""" % (property.label, "\n".join(details))
          else:
            details = ""
          
          label = property.label
          if (box.weight is None) and (len(properties) > 15) and (len(groupped_properties) > 1) and ((len(groupped_properties[0].ids) > 1) or (len(order) < 6)) and (not "<div" in property.label):
            #if div_opened: html += """&nbsp;&nbsp;&nbsp;&nbsp; """
            if div_opened: html += """, """
            else:          open_div(property, has_color, has_hatch)
            html += self.html_popup(label, details, "span")
          else:
            close_div() # Ensure div is closed (no-op if already closed)
            open_div(property, has_color, has_hatch, details = details)
            if   box.weight is None: style = ""
            elif box.min_weight <= 1.0:
              style = "margin-top: 0.0em; margin-bottom: 0.0em; height: %sem;" % box.min_weight
              #label = """<div style="line-height: %sem; font-size: 80%%;">%s</div>""" % (box.min_weight, label)
              label = """<div style="line-height: %sem; font-size: 80%%;" onmouseenter="box_popup_enter(this.parentNode.parentNode.parentNode, event);" onmouseout="event.stopPropagation();">%s</div>""" % (box.min_weight, label)
            else:
              style = "margin-top: 0.0em; margin-bottom: 0.0em; height: %sem; display: flex;" % box.min_weight
              #label = """<div style="overflow-x: hidden; margin-top: auto; margin-bottom: auto;">%s</div>""" % label
              label = """<div style="overflow-x: hidden; margin-top: auto; margin-bottom: auto;" onmouseenter="box_popup_enter(this.parentNode.parentNode.parentNode, event);" onmouseout="event.stopPropagation();">%s</div>""" % label
              
            html += """<div%s>%s</div>\n""" % (style and (' style="%s"' % style), label)
            
            has_widget = False
            for element in order:
              if element in property_2_element_2_relation[property]:
                if property_2_element_2_relation[property][element].widget:
                  has_widget = True
                  break
                
            if has_widget:
              if has_region_div:
                html += """</div>\n"""
                has_region_div = False
                
              html += """<table class="rainbowbox_widget_table" cellspacing="0"><tr>\n"""
              for element in order[box_x : box_x + box_w]:
                if element in property_2_element_2_relation[property]:
                  html += """<td>%s</td>\n""" % property_2_element_2_relation[property][element].widget
                else:
                  html += """<td></td>\n"""
              html += """</tr></table>\n"""
              
            close_div()
        close_div()
      
      html += """</div>\n""" # rainbowbox_box2

      if interactive_boxes and box.extra_irregular_weights:
        h, extra_height_ids = html_extra_weight_table(is_bottom = True)
        html += h
        self.box_id_2_heights[box_html_id] += [extra_height_ids]
        
      html += """</div>\n""" # rainbowbox_box

    if grid == "overlay":
      for i in range(len(order) + 1):
        line_id = self.gen_id()
        if (i == 0) or (i == len(order)): line_style = "solid" ; line_color = "#888"
        else:                             line_style = "dashed"; line_color = "#555"
        if i == len(order): margin = ""
        else:               margin = "margin-left: -1px; "
        html += """<div id="%s" style="%spointer-events: none; border-left: 1px %s %s; width: 0px; height: 25em; position: absolute; left: %s%%; bottom: 0px;"></div>""" % (line_id, margin, line_style, line_color, 100.0 / len(order) * i)
        self.parent_id_2_height_ids[parent_id].append(line_id)
        
    
    html += """</div>\n""" # rainbowbox_parent_1
    html += """</div>\n""" # rainbowbox_parent_0
    if display_border: html += """<div class="rainbowbox_bottom"></div>\n"""
    
    if has_vertical_pos:
      html += """</div>"""
      for box in boxes:
        self.box_id_2_y      [box.html_id] = box.y
        self.box_id_2_heights[box.html_id] = box.max_weight
        
        
    if versus:
      # 2 by 2 comparisons
      def compute_2by2_hatch_background(element, color0 = None, for_properties = None):
        has_hatch = has_color = False
        if isinstance(element, tuple): elements = list(element)
        else:                          elements = [element]
        for prop in for_properties:
          for el in elements:
            relation = property_2_element_2_relation[prop][el]
            if relation.hatch: has_hatch = True
            if relation.color: has_color = True

        if has_hatch:
          hatch_color = rgb2web(*rgb_hatch_color(color0))
          return """background-image: repeating-linear-gradient(135deg, %s, %s 12px, %s 12px, %s 20px);""" % (rgb2web(*color0), rgb2web(*color0), hatch_color, hatch_color)

        #if has_color:
        #  return "background-color: white;"

        return ""

      previous_colors = [None, None]
      def compute_2by2_background(element, property, color0 = None, i = 0, for_properties = None):
        nonlocal previous_colors
        #color0 = rgb_mean([color for i, color in enumerate(colors) if i in property.ids])
        
        has_hatch = has_color = False
        if for_properties:
          if isinstance(element, tuple): elements = list(element)
          else:                          elements = [element]
          for prop in for_properties:
            for el in elements:
              relation = property_2_element_2_relation[prop][el]
              if relation.hatch: has_hatch = True
              if relation.color: has_color = True

        if has_hatch:
          hatch_color = rgb2web(*rgb_hatch_color(color0))
          return """background-image: repeating-linear-gradient(135deg, %s, %s 12px, %s 12px, %s 20px);""" % (rgb2web(*color0), rgb2web(*color0), hatch_color, hatch_color)

        if isinstance(element, tuple):
          element1, element2 = element
          relation1 = property_2_element_2_relation[property][element1]
          relation2 = property_2_element_2_relation[property][element2]
          if i % 2 == 0:   default_color = color0
          else:            default_color = rgb_lighten(color0)
          color1 = relation1.color or default_color
          color2 = relation2.color or default_color
          hatch1 = relation1.hatch
          hatch2 = relation2.hatch
          if hatch1 or hatch2:
            bg = "background-image: "
            if i % 2 == 1:
              bg += "linear-gradient(0deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0.2) 100%), "
            if hatch1: bg += "linear-gradient(90deg, %s 0%%, transparent 35%%, transparent 47%%, " % (rgb2web(*color0))
            else:      bg += "linear-gradient(90deg, %s 0%%, %s 47%%, " % (rgb2web(*color0), rgb2web(*color0))
            if hatch2: bg += "transparent 52%, transparent 100%);"
            else:      bg += "%s 52%%, %s 100%%);" % (rgb2web(*color0), rgb2web(*color0))
            return bg

          bg = ""
          colors = color1, color2
          if colors != previous_colors:
            if (color1 == previous_colors[0]) or (color2 == previous_colors[1]):
              bg = "border-top: 1px solid white; "
            previous_colors = colors

          if color1 == color2:
            return bg + "background-color: %s;" % rgb2web(*color1)
          else:
            return bg + "background-image: linear-gradient(90deg, %s 0%%, %s 47%%, %s 52%%, %s 100%%);" % (rgb2web(*color1), rgb2web(*color1), rgb2web(*color2), rgb2web(*color2))

        else:
          relation = property_2_element_2_relation[property][element]
          if relation.color: color = relation.color
          else:
            if relation.hatch:
              bg = "background-image: "
              if i % 2 == 1:
                bg += "linear-gradient(0deg, rgba(255,255,255,0.2) 0%, rgba(255,255,255,0.2) 100%), "
              return bg + "linear-gradient(90deg, %s 0%%, transparent 70%%, transparent 100%%);" % (rgb2web(*color0))

            if i % 2 == 0:   color = color0
            else:            color = rgb_lighten(color0)
          if for_properties: return "background-color: white;"
          return "background-color: %s;" % rgb2web(*color)

      def show_properties(element, properties, color0 = None, i = 0):
        nonlocal html
        if not color0: color0 = (0.9, 0.9, 0.9)
        for property in properties:
          i += 1
          background = compute_2by2_background(element, property, color0, i)

          html += """<div class="rainbowbox_table_2by2_cell" style="%s">%s""" % (background, property.label)
          if isinstance(element, tuple):
            relation0 = property_2_element_2_relation[property][element[0]]
            relation1 = property_2_element_2_relation[property][element[1]]
            if relation0.widget or relation1.widget:
              html += """<table class="rainbowbox_widget_table" cellspacing="0"><tr><td>%s</td><td>%s</td></tr></table>\n""" % (relation0.widget, relation1.widget)
          else:
            relation = property_2_element_2_relation[property][element]
            if relation.widget:
              html += """<table class="rainbowbox_widget_table" cellspacing="0"><tr><td>%s</td></tr></table>\n""" % relation.widget
          html += """</div>\n"""

      for col in cols[1:]:
        html += """<div id="%s" style="display: none;">\n""" % col_div_ids[col]
        html += """<div class="rainbowbox_buttonx" onClick="select_comparator('%s', 0, 0); event.stopPropagation();">X</div>\n""" % (parent_id)

        html += """<table class="rainbowbox_table_2by2" cellspacing="0">\n"""
        html += """<tr class="rainbowbox_table_2by2_header">\n"""
        html += """<td></td>\n"""
        html += """<td class="rainbowbox_table_2by2_left" style="background-color: %s;"><b>%s</b></td>\n""" % (rgb2web(*colors[  0]), order[  0].label)
        html += """<td class="rainbowbox_table_2by2_right" style="background-color: %s;">%s</td>\n"""        % (rgb2web(*colors[col]), order[col].label)
        html += """</tr>\n"""

        i0 = i1 = 0
        common_properties = []
        for property_group in property_groups or [None]:
          color0 = rgb_mean([colors[  0], (0.9, 0.9, 0.9)])
          color1 = rgb_mean([colors[col], (0.9, 0.9, 0.9)])

          if property_group: groupped_properties = property_group.children
          else:              groupped_properties = properties
          properties0 = [property for property in groupped_properties if hasattr(property, "ids") and (0   in property.ids) and (not col in property.ids)]
          properties1 = [property for property in groupped_properties if hasattr(property, "ids") and (col in property.ids) and (not 0   in property.ids)]
          properties2 = [property for property in groupped_properties if hasattr(property, "ids") and (col in property.ids) and (    0   in property.ids)]
          if properties2: common_properties.append((property_group, properties2))
          if (not properties0) and (not properties1): continue
          background0 = compute_2by2_hatch_background(order[  0], color0, properties0)
          background1 = compute_2by2_hatch_background(order[col], color1, properties1)

          html += """<tr class="rainbowbox_table_2by2_row">\n"""
          html += """<td class="rainbowbox_table_2by2_group">\n"""
          if property_group: html += property_group.label
          html += """</td>\n"""

          html += """<td class="rainbowbox_table_2by2_left">\n"""
          if background0: html += """<div style="%s">""" % background0
          show_properties(order[  0], properties0, color0, i = i0)
          if background0: html += """</div>"""
          html += """</td>\n"""
          html += """<td class="rainbowbox_table_2by2_right">\n"""
          if background1: html += """<div style="%s">""" % background1
          show_properties(order[col], properties1, color1, i = i1)
          if background1: html += """</div>"""
          html += """</td>\n"""
          html += """</tr>\n"""

          i0 += len(properties0)
          i1 += len(properties1)

        html += """<tr class="rainbowbox_table_2by2_row">"""
        html += """<td class="rainbowbox_table_2by2_sep"></td><td colspan="2" class="rainbowbox_table_2by2_both" style="height: 4px;"></td>"""
        html += """</tr>"""
        
        i = 0
        for property_group, groupped_properties in common_properties:
          background2 = compute_2by2_background((order[0], order[col]), groupped_properties[-1], (0.9, 0.9, 0.9), 0, groupped_properties)
          html += """<tr class="rainbowbox_table_2by2_row">"""

          html += """<td class="rainbowbox_table_2by2_group">\n"""
          if property_group: html += property_group.label
          html += """</td>\n"""

          html += """<td colspan="2" class="rainbowbox_table_2by2_both" style="%s">\n""" % background2
          properties2 = [property for property in groupped_properties if hasattr(property, "ids") and (0 in property.ids) and (col in property.ids)]
          show_properties((order[0], order[col]), properties2, i = i)
          html += """</td>\n"""
          html += """</tr>\n"""

          i += len(properties2)
        
      html += """<tr><td></td><td colspan="2" class="rainbowbox_bottom"></td></tr>\n"""
      html += """</table>\n"""
      html += """</div>\n"""

    self.html += html
    return html


    
