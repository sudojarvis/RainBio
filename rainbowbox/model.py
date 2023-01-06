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


class Element(object):
  def __init__(self, group, label, details = "", order_key = None, color = None, weight = 1.0, rotate = None, border_color = None):
    self.group      = group
    self.label      = label
    self.details    = details
    self.order_key  = order_key or label
    self.color      = color
    self.rotate     = rotate
    self.weight     = weight
    self.border_color = border_color
    if group: group.children.append(self)
    
  def clone(self): return Element(self.group, self.label, self.details, self.order_key, getattr(self, "color", None), self.weight)
  
  def get_html(self):
    if self.rotate:
      if self.details:
        event = """ onMouseEnter="popup_enter(this.parentNode.parentNode, event);" onmouseout="event.stopPropagation();" """
      else:
        event = ""
      return """
<div style="width: 1em; height: %sem;">
<div style="width: %sem; height: 1em; transform: rotate(270deg); transform-origin: %sem %sem; text-align: left;" %s>
%s
</div>
</div>""" % (self.rotate, self.rotate, self.rotate / 2.0, self.rotate / 2.0, event, self.label)
    else:
      return self.label
    
  def __repr__(self): return "<Element %s>" % self.label

class ElementGroup(object):
  def __init__(self, label, details = ""):
    self.label    = label
    self.details  = details
    self.children = []
    
  def clone(self): return ElementGroup(self.label, self.details)
  
  def __repr__(self): return "<ElementGroup %s>" % self.label
  

IRREGULAR = "irregular"

class Property(object):
  def __init__(self, group, label, order_key = 0, details = "", weight = None, start_new_box = False, at_bottom = False, color = None, ellipsis = True, rotate = None, vertical_pos = None, header_box = False):
    self.group         = group
    self.label         = label
    self.order_key     = order_key
    self.details       = details
    self.weight        = weight # Minimum weight : 0.75
    self.start_new_box = start_new_box
    self.at_bottom     = at_bottom
    self.color         = color
    self.ellipsis      = ellipsis
    self.vertical_pos  = vertical_pos
    self.header_box    = header_box
    if group: group.children.append(self)
     
  def clone(self): return Property(self.group, self.label, self.order_key, self.details, self.weight, self.start_new_box, self.at_bottom, self.color, self.ellipsis, None, self.vertical_pos, self.header_box)
  
  def __repr__(self): return "<Property %s>" % self.label

  def get_html(self):
    return self.label
  
      
class PropertyGroup(object):
  def __init__(self, label, order_key = 0):
    self.label     = label
    self.order_key = order_key
    self.children  = []
    
  def clone(self): return ElementGroup(self.label, self.order_key)
  
  def __repr__(self): return "<PropertyGroup %s>" % self.label


class Relation(object):
  def __init__(self, element, property, hatch = 0, color = None, details = "", widget = "", weight = None):
    if isinstance(element, Property): element, property = property, element
    self.element  = element
    self.property = property
    self.hatch    = hatch
    self.color    = color
    self.details  = details
    self.widget   = widget
    self.weight   = weight

  def get_weight_or_default(self):
    return self.weight or self.property.weight or 1.0
    
  def __repr__(self): return "<Relation %s - %s>" % (self.element.label, self.property.label)
  
  
def relations_2_model(relations, element_group = None):
  elements = []
  elements_set = set()
  element_groups = []
  element_groups_set = { None }
  properties = []
  properties_set = set()
  property_groups = []
  property_groups_set = { None }
  element_2_property_2_relation = {}
  property_2_element_2_relation = {}
  
  for relation in relations:
    if element_group and not relation.element.group is element_group: continue
    
    if not relation.element in elements_set:
      elements.append (relation.element)
      elements_set.add(relation.element)
    if not relation.element.group in element_groups_set:
      element_groups.append (relation.element.group)
      element_groups_set.add(relation.element.group)
    if not relation.property in properties_set:
      properties.append (relation.property)
      properties_set.add(relation.property)
    if not relation.property.group in property_groups_set:
      property_groups.append (relation.property.group)
      property_groups_set.add(relation.property.group)
      
    if not relation.element in element_2_property_2_relation: element_2_property_2_relation[relation.element] = {}
    if relation.property in element_2_property_2_relation[relation.element]: raise ValueError("Dupplicated property %s for element %s!" % (relation.property, relation.element))
    element_2_property_2_relation[relation.element][relation.property] = relation
    
    if not relation.property in property_2_element_2_relation: property_2_element_2_relation[relation.property] = {}
    property_2_element_2_relation[relation.property][relation.element] = relation
    
  return elements, element_groups, properties, property_groups, element_2_property_2_relation, property_2_element_2_relation


# def simplified_model(elements, element_groups, properties, property_groups, element_2_property_2_relation, property_2_element_2_relation):
#   s_properties = {}
#   for property in properties:
#     if len(property_2_element_2_relation[property]) <= 1: continue
#     s_properties[property] = property.clone()
      
#   s_element_groups = {}
#   for element_group in element_groups:
#     s_element_groups[element_group] = element_group.clone()
    
#   s_elements = {}
#   props_2_s_element = {}
#   s_relations = []
  
#   for element in elements:
#     props = set()
#     for property in element_2_property_2_relation[element]:
#       if property in s_properties: props.add(s_properties[property])
#     if not props: continue
    
#     if props in props_2_s_element:
#       s_elements[element] = props_2_s_element[props]
#     else:
#       e = s_elements[element] = props_2_s_element[props] = element.clone()
#       e.group = s_element_groups.get(element.group, None)
#       for property in props:
#         s_relations.append(Relation(e, property))
  
#   return relations_2_model(s_relations)

  


def _get_property_weight(prop, property_2_element_2_relation):
  if prop.weight is IRREGULAR:
    weights = []
    element_2_relation = property_2_element_2_relation[prop]
    for relation in element_2_relation.values():
      if not relation.weight is None: weights.append(relation.weight)
    if not weights: return None
    weights = set(weights)
    if len(weights) == 1: return weights.pop()
    return weights
  return prop.weight


def model_2_python(elements, properties, relations):
  s = """
elements = []
properties = []
"""
  element_2_index  = {}
  property_2_index = {}
  
  for i, element in enumerate(elements):
    element_2_index[element] = i
    s += '''element_%s = Element(None, """%s""")\n''' % (i, element.label)
  s += "\n"

  for i, property in enumerate(properties):
    property_2_index[property] = i
    s += '''property_%s = Property(None, """%s""")\n''' % (i, property.label)
  s += "\n"
  
  s += "relations = [\n"
  for relation in relations:
    s += '''  Relation(element_%s, property_%s),\n''' % (element_2_index[relation.element], property_2_index[relation.property])
  s += "]"
  
  return s
