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

import sys, os, csv, math
from collections import defaultdict

import rainbowbox
#rainbowbox.Element, rainbowbox.Property = rainbowbox.Property, rainbowbox.Element

def _rgb_hatch_color(c): return (1, 1, 1)
rainbowbox.color.rgb_hatch_color = _rgb_hatch_color

from rainbowbox.model import *
from rainbowbox.color import *

from collections import defaultdict


def select_non_zero(x):
  if x == "": return False
  if x ==  0: return False
  return True

def aggregate_mean(x):
  return sum(x) / len(x)

def aggregate_half_mean(x):
  return (sum(x) / len(x)) / 2.0
  
def csv_2_triples(csv_data, select_func = select_non_zero):
  if isinstance(csv_data, str):
    with open(csv_data) as f:
      csv_data = list(csv.reader(f))
      
  items = csv_data[0][1:]
  triples = []
  
  for row in csv_data[1:]:
    for i in range(len(items)):
      if i + 1 > len(row) - 1: break
      s = row[i + 1].strip()
      s = int(s or 0)
      if select_func(s):
        triples.append((row[0], items[i], s))
        
  return triples

def mean(values):
  return int(round(sum(values) / len(values)))

def triples_2_model(triples, Element = None, color1 = (0.7, 0.5, 1.0), color2 = (0.0, 0.5, 1.0), use_hsv_color = True, rotate = None, aggregate_func = min, include_relation_with_self = False, legend_dict = {}, use_weight = True, cluster_ratio = None, cluster_consider_aggregation = True, default_weight = 0.7, colors = None):
  Element = Element or rainbowbox.Element
  item_2_elements = {}
  def new_element(label):
    element = Element(None, label, rotate = rotate)
    elements.append(element)
    item_2_elements[label] = element
    return element
  
  elements   = []
  properties = []
  relations  = []
  
  triples = [(item_2_elements.get(a) or new_element(a), item_2_elements.get(b) or new_element(b), c)
             for (a,b,c) in triples]
  
  pairs    = { frozenset((a,b)) : c for (a,b,c) in triples }
  remnants = set(pairs)
  remnants = list(remnants)
  
  def create_property(prop_elements, hatch_elements = None):
    property = Property(None, """&nbsp""", weight = default_weight)
    property._elements = prop_elements
    property._relations = []
    property._hatch_elements = hatch_elements or []
    properties.append(property)
    for element in prop_elements:
      if 0 and cluster_ratio:
        if include_relation_with_self:
          element_numbers = [int(bool(pairs.get(frozenset((element, other)), 0))) for other in prop_elements]
        else:
          element_numbers = [int(bool(pairs.get(frozenset((element, other)), 0))) for other in prop_elements if not other is element]
      else:
        if include_relation_with_self:
          element_numbers = [pairs.get(frozenset((element, other)), 0) for other in prop_elements]
        else:
          element_numbers = [pairs.get(frozenset((element, other)), 0) for other in prop_elements if not other is element]
          
      relation = Relation(element, property)
      relations.append(relation)
      property._relations.append(relation)

      relation.aggregation = aggregate_func(element_numbers)
    return property
  
  
  already = set()
  while remnants:
    s = list(remnants.pop())
    for other in elements:
      if other in s: continue
      for element in s:
        if not frozenset((element, other)) in pairs: break
      else:
        for element in s:
          if frozenset((element, other)) in remnants: remnants.remove(frozenset((element, other)))
        s.append(other)
        
    if frozenset(s) in already: continue
    already.add(frozenset(s))

    create_property(s)
    
    
  if cluster_ratio:
    already_dones = set()
    removed = set()
    
    def merge(p1, p2, p1_p2_elements):
      properties.remove(p1)
      properties.remove(p2)
      for i in p1._relations: relations.remove(i)
      for i in p2._relations: relations.remove(i)
      removed.add(p1)
      removed.add(p2)
      
      create_property(list(p1_p2_elements))
      
    if cluster_consider_aggregation:
      max_aggregation = max(pairs.values())
      
    def cluster_iteration():
      properties_list = list(properties)
      properties_list.sort(key = lambda p: -len(p._elements))
      best_score = None
      best_props = None
      for p1 in properties_list:
        if p1 in removed: continue
        for p2 in properties_list:
          if p2 in removed: continue
          if id(p1) <= id(p2): continue
          #if (p1, p2) in already_dones: continue
          if not (set(p1._elements) & set(p2._elements)):
            continue
          
          p1_p2_elements = set(p1._elements) | set(p2._elements)
          
          nb = 0
          nb_max = 0
          for e1 in p1_p2_elements:
            for e2 in p1_p2_elements:
              if id(e1) <= id(e2): continue
              nb_max += 1
              if frozenset((e1, e2)) in pairs:
                if cluster_consider_aggregation: nb += pairs[frozenset((e1, e2))] / max_aggregation
                else:                            nb += 1
          score_ensemble = nb / nb_max
          
          nb_max = len(p1_p2_elements) - 1
          element_nbs = []
          for e1 in p1_p2_elements:
            element_nb = 0
            for e2 in p1_p2_elements:
              if e1 is e2: continue
              if frozenset((e1, e2)) in pairs:
                if cluster_consider_aggregation: element_nb += pairs[frozenset((e1, e2))] / max_aggregation
                else:                            element_nb += 1
            element_nbs.append(element_nb)
          score_element = min(element_nbs) / nb_max
          
          score = score_ensemble * score_element
          
          if score >= cluster_ratio ** 2:
            if (best_score is None) or (score > best_score):
              best_score = score
              best_props = p1, p2, p1_p2_elements
              
      if not best_score is None:
        print("Cluster:", best_score, *best_props)
        merge(*best_props)
        return True
        
      return False
    
    cont = True
    while cont:
      cont = cluster_iteration()
      
  numbers = { relation.aggregation for relation in relations }
  
  has_color = len(numbers) > 1
  if has_color:
    for element in elements: element.color = (0.9, 0.9, 0.9)

    if colors:
      print(numbers)
      number_2_color = { i : colors[i - 1] for i in numbers }
    else:
      min_number = min(numbers)
      max_number = max(numbers)
      if use_hsv_color:
        number_2_color = { i : hsv2rgb(*rgb_blend_color(color1, color2, (i - min_number) / (max_number - min_number))) for i in numbers }
      else:
        number_2_color = { i : rgb_blend_color(color1, color2, (i - min_number) / (max_number - min_number)) for i in numbers }
  else:
    number_2_color = defaultdict(lambda: None)
    
  if cluster_ratio:
    c1, c2 = hsv2rgb(*color1), hsv2rgb(*color2)
    for relation in relations:
      relation.color = rgb_blend_color(c1, c2, relation.aggregation)
  else:
    for relation in relations:
      relation.color = number_2_color[relation.aggregation]
      
  if use_weight:
    for property in properties:
      property.aggregation    = 0
      property.aggregation_nb = 0
    for relation in relations:
      relation.property.aggregation    += relation.aggregation
      relation.property.aggregation_nb += 1
    for property in properties:
      property.weight = property.aggregation / property.aggregation_nb
      
  if len(number_2_color) > 1:
    html_legend  = """<br/>\n"""
    html_legend += """<div><center>\n"""
    html_legend += """<table class="rainbowbox_legend_table"><tr>\n"""
    for i in sorted(numbers):
      html_legend += """<td class="rainbowbox_legend_td" style="background-color: %s;">%s</td>\n""" % (rgb2css(*number_2_color[i]), legend_dict.get(i, i))
    html_legend += """</tr></table>\n"""
    html_legend += """</center></div>\n"""
  else:
    html_legend = ""
    
  return elements, properties, relations, html_legend



def gen_matrice(elements, properties, relations):
  p2nom = {}
  for p in properties:
    p2nom[p] = "".join(e.label[0] for e in p._elements)


  s = "nom,%s\n" % ",".join(p2nom[p] for p in properties)
  
  for e in elements:
    s += "%s," % e.label
    for p in properties:
      if e in p._elements: s += "1.0,"
      else:                s += "0.0,"
    s = s[:-1] + "\n"
  
  open("/tmp/m.csv", "w").write(s)

  """
import pandas, numpy, matplotlib.pylab as pylab, sklearn.manifold, sklearn.metrics

pylab.plot(*t2.T, "bx")

deja = set()
for i in range(21):
  x, y = round(t2[i,0], 3), round(t2[i,1] + 0.08, 3)
  while (x, y) in deja:
    y += 0.1
  pylab.text(x, y, t0.nom[i], horizontalalignment='center', verticalalignment='center')
  deja.add((x, y))

pylab.show()
"""


def from_cb(s):
  l = []
  for i in s.strip().split("\n"):
    r, g, b = [int(j) for j in i.split(",")]
    l.append((r/255.0, g/255.0, b/255.0))
  return l

colors5 = from_cb("""
199,233,180
127,205,187
65,182,196
44,127,184
37,52,148
""")

colors4 = from_cb("""
141,160,203
166,216,84
255,217,47
252,141,98
 """)
 
colors4 = from_cb("""
55,126,184
152,78,163
228,26,28
255,127,0
 """)

if __name__ == "__main__":
  if   sys.argv[-1] == "1":
    triples = csv_2_triples("/home/jiba/bouquin/sombre_comme_laurore/visu_perso.csv")
    
    legend_dict = {
      1 : "Avant l'histoire",
      2 : "Partie 1",
      3 : "Partie 2",
      4 : "Partie 3",
      5 : "Partie 4",
      6 : "Partie 5",
      7 : "Partie 6",
    }
    
    legend_dict = {
      1 : "Before the story begins",
      2 : "Part #1",
      3 : "Part #2",
      4 : "Part #3",
      5 : "<span style='color: white;'>Part #4</span>",
      6 : "Part #5",
      7 : "<span style='text-color: white;'>Part #6</span>",
    }
    
    elements, properties, relations, html_legend = triples_2_model(triples, rotate = 9, legend_dict = legend_dict, use_weight = False, default_weight = 1.5, colors = colors5)
    
    from rainbowbox.draw import *
    from rainbowbox.order_elements import *
    
    fixed_order = ["Mabine", "Malfred","Érard","Le Capitann","Rakenn", "Tienn","Alyse","Chéram","Gauve","Méric","Rashkang","Lescantelles","La Rasinne","Werfam","Auguss","Le Lamineur","Nicol","Crépusculine","King Saphir","Auroraline","Thérald"]
    order = []
    for n in fixed_order:
      for e in elements:
        if e.label == n:
          order.append(e)
          break
    #order = best_elements_order_optim(relations, nb_tested_solution = 30000)
    
    gen_matrice(elements, properties, relations)
    
    html_page = HTMLPage()
    html_page.rainbowbox(relations, elements = elements, order = order)
    html_page.html += html_legend
    html_page.show()
    
  elif sys.argv[-1] == "2":
    triples = csv_2_triples("./rainbowbox/doc/pam250.csv")
    
    elements, properties, relations, html_legend = triples_2_model(triples, aggregate_func = min, include_relation_with_self = True)
    
    from rainbowbox.draw import *
    from rainbowbox.order_elements import *
    
    order = best_elements_order_optim(relations, nb_tested_solution = 30000)
    
    
    html_page = HTMLPage()
    html_page.rainbowbox(relations, elements = elements, order = order)
    #html_page.rainbowbox(relations, elements = elements)
    #html_page.html += html_legend
    html_page.show()

  
  elif sys.argv[-1] == "3":
    triples = csv_2_triples("./rainbowbox/doc/nauru_graph.csv")
    
    elements, properties, relations, html_legend = triples_2_model(triples)
    
    from rainbowbox.draw import *
    from rainbowbox.order_elements import *
    
    order = best_elements_order_optim(relations, nb_tested_solution = 10000)
    
    html_page = HTMLPage()
    html_page.rainbowbox(relations, elements = elements, order = order)
    #html_page.rainbowbox(relations, elements = elements)
    html_page.html += html_legend
    html_page.show()
    
  elif sys.argv[-1] == "4":
    
    def select_sup_1(x):
      if x == "": return False
      if x ==  0: return False
      if x ==  1: return False
      return True
    
    triples = csv_2_triples("./rainbowbox/doc/les_miserables.csv") #, select_func = select_sup_1)
    
    elements, properties, relations, html_legend = triples_2_model(triples, rotate = 16, aggregate_func = sum, color1 = (0.7, 0.5, 1.0), color2 = (0.0, 0.5, 1.0))
    
    from rainbowbox.draw import *
    from rainbowbox.order_elements import *
    
    order = best_elements_order_optim(relations, nb_tested_solution = None)
    #order = best_elements_order_hybrid(relations, nb_tested_solution = None)
    
    for property in properties:
      property.weight = None
      
    html_page = HTMLPage()
    html_page.rainbowbox(relations, elements = elements, order = order)
    #html_page.rainbowbox(relations, elements = elements)
    html_page.html += html_legend
    html_page.show()
    
  elif sys.argv[-1] == "5":
    
    def select_sup_1(x):
      if x == "": return False
      if x ==  0: return False
      if x ==  1: return False
      return True
    
    triples = csv_2_triples("./rainbowbox/doc/les_miserables_2.csv") #, select_func = select_sup_1)
    
    elements, properties, relations, html_legend = triples_2_model(triples, rotate = 16, aggregate_func = min, colors = colors4, color1 = (0.7, 0.5, 1.0), color2 = (0.0, 0.5, 1.0))
    
    from rainbowbox.draw import *
    from rainbowbox.order_elements import *
    
    for property in properties:
      property.weight = None

    fixed_order = ['Jacquin Labarre', 'Mme de R', 'Mlle Vaubois', 'Petit Gervais', 'M Scaufflaire', 'Isabeau', 'Mme Pontmercy', 'George Pontmercy',
'Magnon', 'Brevet', 'Champmathieu', 'Chenildieu', 'Cochepaille', 'Judge of Douai', 'M Bamatabois', 'Marguerite',
'Blacheville', 'Dahlia', 'Fameuil', 'Favourite', 'Listolier', 'Zephine', 'Félix Tholomyès', 'Fantine', 
'Sister Simplice', 'Sister Perpétue', 'Gribier', 'Fauchelevent', 'Mother Innocent', 
'Baroness of T', 'Old woman 1', 'Toussaint', 'Old woman 2', 'Lt Theodule Gillenormand', 'Mlle Gillenormand', 'M Gillenormand', 
'Marius', 'Cosette', 'Jean Valjean', 'Javert', 'Mme Thénardier', 'Thénardier', 'Babet', 'Gueulemer', 'Claquesous', 'Eponine', 
'Montparnasse', 'Brujon', 'Anzelma', 'Mme Hucheloup', 'Gavroche','Enjolras', 'Bossuet', 'Courfeyrac', 
'Bahorel', 'Joly', 'Grantaire', 'Jean Prouvaire', 'Combeferre', 'Feuilly', 'M Mabeuf', 'Mother Plutarch', 'Mlle Baptistine',
'Mme Magloire', 'Napoleon', 'M Myriel', 'Count', 'Child 1', 'Child 2', 'Géborand', 'G--', 'Marquis de Champtercier', 'Countess de Lô', 
'Boulatruelle', 'Mme Burgon', 'Jondrette', 'Cravatte'    ]
    order = []
    for n in fixed_order:
      for e in elements:
        if e.label == n:
          order.append(e)
          break
      
    #order = best_elements_order_optim(relations, nb_tested_solution = None)
    
    html_page = HTMLPage()
    html_page.rainbowbox(relations, elements = elements, order = order)
    html_page.html += html_legend
    html_page.show()

  elif sys.argv[-1] == "6":
    triples = csv_2_triples("./rainbowbox/doc/les_miserables.csv")
    
    elements, properties, relations, html_legend = triples_2_model(triples, rotate = 16, aggregate_func = sum, color1 = (0.7, 0.5, 1.0), color2 = (0.0, 0.5, 1.0))
    
    from rainbowbox.draw import *
    from rainbowbox.order_elements import *
    
    fixed_order = ['Jacquin Labarre', 'Mme de R', 'Mlle Vaubois', 'Petit Gervais', 'M Scaufflaire', 'Isabeau', 'Mme Pontmercy', 'George Pontmercy',
'Magnon', 'Brevet', 'Champmathieu', 'Chenildieu', 'Cochepaille', 'Judge of Douai', 'M Bamatabois', 'Marguerite',
'Blacheville', 'Dahlia', 'Fameuil', 'Favourite', 'Listolier', 'Zephine', 'Félix Tholomyès', 'Fantine', 
'Sister Simplice', 'Sister Perpétue', 'Gribier', 'Fauchelevent', 'Mother Innocent', 
'Baroness of T', 'Old woman 1', 'Toussaint', 'Old woman 2', 'Lt Theodule Gillenormand', 'Mlle Gillenormand', 'M Gillenormand', 
'Marius', 'Cosette', 'Jean Valjean', 'Javert', 'Mme Thénardier', 'Thénardier', 'Babet', 'Gueulemer', 'Claquesous', 'Eponine', 
'Montparnasse', 'Brujon', 'Anzelma', 'Mme Hucheloup', 'Gavroche','Enjolras', 'Bossuet', 'Courfeyrac', 
'Bahorel', 'Joly', 'Grantaire', 'Jean Prouvaire', 'Combeferre', 'Feuilly', 'M Mabeuf', 'Mother Plutarch', 'Mlle Baptistine',
'Mme Magloire', 'Napoleon', 'M Myriel', 'Count', 'Child 1', 'Child 2', 'Géborand', 'G--', 'Marquis de Champtercier', 'Countess de Lô', 
'Boulatruelle', 'Mme Burgon', 'Jondrette', 'Cravatte'    ]
    order = []
    for n in fixed_order:
      for e in elements:
        if e.label == n:
          order.append(e)
          break
      
    #order = best_elements_order_optim(relations, nb_tested_solution = None)
    
    for property in properties:
      property.weight = None

    prop_2_rels = defaultdict(list)
    for relation in relations: prop_2_rels[relation.property].append(relation)
    
    triples2 = csv_2_triples("./rainbowbox/doc/les_miserables_2.csv")
    pairs2   = { frozenset((a,b)) : c for (a,b,c) in triples2 }
    for relation in relations:
      relation.chapitre = min( pairs2[frozenset([ relation.element.label, r.element.label ])] for r in prop_2_rels[relation.property] if not r is relation )
      
    min_chapitre = min(relation.chapitre for relation in relations)
    max_chapitre = max(relation.chapitre for relation in relations)
    for relation in relations:
      color          = rgb2hsv(*relation.color)
      red = color[0]
      color = colors4[relation.chapitre - 1]
      #saturation     = 0.8 - 0.6 * (color[0] / 0.7)
      #relation.color = hsv2rgb(hue, saturation, 1.0)
      relation.color = rgb_blend_color(color, (1.0, 1.0, 1.0), red)
      
    html_page = HTMLPage()
    html_page.rainbowbox(relations, elements = elements, order = order)
    html_page.html += html_legend
    html_page.show()
    
    
  elif sys.argv[-1] == "7":
    #triples = csv_2_triples("./rainbowbox/doc/visu_perso_test.csv")
    triples = csv_2_triples("/home/jiba/bouquin/sombre_comme_laurore/visu_perso.csv")
    
    legend_dict = {
      1 : "Before the story begins",
      2 : "Part #1",
    }
    
    elements, properties, relations, html_legend = triples_2_model(triples, cluster_ratio = 0.4, rotate = 9, legend_dict = legend_dict, use_weight = False, )
    
    from rainbowbox.draw import *
    from rainbowbox.order_elements import *
    
    #order = best_elements_order_optim(relations, nb_tested_solution = 30000)
    #l = [i.label for i in order]
    #print(repr(l))
    ORDER = ['Mabine', 'Malfred', 'Érard', 'Méric', 'Rashkang', 'Chéram', 'Rakenn', 'Alyse', 'Tienn', 'Le Capitann', 'Gauve', 'Lescantelles', 'La Rasinne', 'Werfam', 'King Saphir', 'Crépusculine', 'Auroraline', 'Thérald', 'Nicol', 'Auguss', 'Le Lamineur']
    order = []
    label_2_element = { e.label : e for e in elements }
    for i in ORDER: order.append(label_2_element[i])
    
    html_page = HTMLPage()
    html_page.rainbowbox(relations, elements = elements, order = order)
    html_page.html += html_legend
    html_page.show()
    
    
  elif sys.argv[1] == "8":
    cluster_ratio = None 
    if sys.argv[-1] != "8":
      if sys.argv[-2] != "8":
        cluster_ratio = float(sys.argv[-1])
        triples = csv_2_triples("./rainbowbox/doc/dbpedia_%s.csv" % sys.argv[-2])
      else:
        triples = csv_2_triples("./rainbowbox/doc/dbpedia_%s.csv" % sys.argv[-1])
    else:
      triples = csv_2_triples("./rainbowbox/doc/dbpedia_matrice.csv")

    legend_dict = {
      1 : "Unidirectional",
      2 : "Bidirectional",
    }

    if cluster_ratio is None:
      elements, properties, relations, html_legend = triples_2_model(triples, cluster_ratio = cluster_ratio, color1 = (0.0, 0.3, 0.9), color2 = (0.0, 0.6, 0.8), rotate = 30, legend_dict = legend_dict, use_weight = False, aggregate_func = aggregate_mean)
    else:
      elements, properties, relations, html_legend = triples_2_model(triples, cluster_ratio = cluster_ratio, color1 = (0.0, 0.15, 0.95), color2 = (0.0, 0.6, 0.8), rotate = 30, legend_dict = legend_dict, use_weight = False, aggregate_func = aggregate_half_mean)
    
    from rainbowbox.draw import *
    from rainbowbox.order_elements import *
    
    order = best_elements_order_optim(relations, nb_tested_solution = None)
    
    html_page = HTMLPage()
    html_page.hatch_white_size = 2
    html_page.rainbowbox(relations, elements = elements, order = order)
    #html_page.html += html_legend
    html_page.show()
