# -*- coding: utf-8 -*-
# RainbowBox
# Copyright (C) 2018 Jean-Baptiste LAMY
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

import os.path, math, urllib.parse
from collections import defaultdict

from rainbowbox import *
from rainbowbox.color import hsv2rgb
from rainbowbox.order_base import all_subsets
from rainbowbox.order_elements import *
from rainbowbox.order_boxes import *


class GeneList(object):
  def __init__(self, name, genes):
    self.name  = name
    self.genes = genes
    
  def __repr__(self): return "<GeneList %s>" % self.name

class ExclusiveIntersection(object):
  def __init__(self, id, subset):
    self.id         = id
    self.subset     = frozenset(subset)
    self.genes      = set()
    self.orig_genes = set()
    self.includes   = {self}
    self.pruned     = False
    
  def __repr__(self): return "<ExclusiveIntersection %s, %s genes>" % (self.subset, len(self.genes))
  
  def add_include(self, ex_inter):
    self.includes.update(ex_inter.includes)
    self.genes   .update(ex_inter.genes)
    
class PruneLevel(object):
  def __init__(self, selected_ex_inters, compute_height, prop_2_box, gene_list_id_2_nb_inter_shown):
    self.min_nb_gene_per_box = min((len(x.orig_genes) for x in selected_ex_inters if len(x.subset) > 1), default = 0)
    self.nb_box              = len(selected_ex_inters)
    self.box_nbs             = {}
    self.box_includes        = {}
    self.gene_list_id_2_nb_inter_shown = gene_list_id_2_nb_inter_shown
    
    for prop, box in prop_2_box.items():
      if prop.ex_inter.pruned: self.box_nbs    [box.html_id] = 0
      else:                    self.box_nbs    [box.html_id] = len(prop.ex_inter.genes)
      self.box_includes[box.html_id] = [ex_inter.id for ex_inter in sorted(prop.ex_inter.includes, key = lambda x: len(x.subset))]
      
  def __repr__(self):
    return """PruneLevel(%s, %s, %s, %s, %s)""" % (self.min_nb_gene_per_box, self.nb_box, self.box_nbs, self.box_includes, self.gene_list_id_2_nb_inter_shown)
  
   
def reads_interactivenn(s):
  if isinstance(s, bytes): s = s.decode("utf8")
  
  all_genes  = set()
  gene_lists = []
  for line in s.split("\n"):
    if line:
      name, genes = line.split(":", 1)
      if genes.endswith(";"): genes = genes[:-1]
      genes = genes.split(",")
      gene_list = GeneList(name, genes)
      gene_lists.append(gene_list)
      all_genes.update(gene_list.genes)
  gene_2_gene_list = defaultdict(set)
  
  return all_genes, gene_lists
 
def read_interactivenn(file):
  if isinstance(file, str): file = open(file)
  s = file.read()
  return reads_interactivenn(s)
  
def prune(ex_inters, max_nb_box):
  for ex_inter in ex_inters: # Reset pruning
    ex_inter.genes    = set(ex_inter.orig_genes)
    ex_inter.includes = { ex_inter }
    ex_inter.pruned   = False
    
  selected_ex_inters = [x for x in ex_inters if len(x.subset) == 1]
  ex_inters.sort(key = lambda ex_inter: -len(ex_inter.genes))
  for x in ex_inters:
    if len(x.subset) == 1: continue
    if len(selected_ex_inters) >= max_nb_box:
      while selected_ex_inters and (len(x.genes) == len(selected_ex_inters[-1].genes)) and (len(selected_ex_inters[-1].subset) > 1):
        del selected_ex_inters[-1]
      break
    else:
      selected_ex_inters.append(x)
      
  fix_pruned(ex_inters, selected_ex_inters)
  return selected_ex_inters

def fix_pruned(ex_inters, selected_ex_inters):
  for pruned_ex_inter in set(ex_inters) - set(selected_ex_inters):
    pruned_ex_inter.pruned = True
    candidates = []
    for selected_ex_inter in selected_ex_inters:
      if selected_ex_inter.subset.issubset(pruned_ex_inter.subset):
        candidates.append(selected_ex_inter)
        
    for candidate in candidates:
      for candidate2 in candidates:
        if (not candidate is candidate2) and candidate.subset.issubset(candidate2.subset): break
      else:
        candidate.add_include(pruned_ex_inter)
        
def prune_rec(ex_inters, max_nb_box):
  for ex_inter in ex_inters: # Reset pruning
    ex_inter.genes    = set(ex_inter.orig_genes)
    ex_inter.includes = set()
    ex_inter.pruned   = False
    
  selected_ex_inters = list(ex_inters)
  while len(selected_ex_inters) > max_nb_box:
    for ex_inter in ex_inters: # Reset
      ex_inter.includes = set()
      
    selected_ex_inters = _prune_rec(selected_ex_inters)
    
    for ex_inter in ex_inters: # Reset
      ex_inter.genes    = set(ex_inter.orig_genes)
      
    fix_pruned(ex_inters, selected_ex_inters)
    
  return selected_ex_inters


def _prune_rec(ex_inters):
  ex_inters.sort(key = lambda ex_inter: len(ex_inter.genes))  
  selected_ex_inters = [x for x in ex_inters if len(x.genes) > len(ex_inters[0].genes)]
  return selected_ex_inters


def gene_lists_2_html_page(genes, gene_lists, height_unit = None, max_nb_box = 64, static_url = "", height_factor = 30.0, detail_on_demand = True, dynamic_clustering = True, nb_tested_solution = 3000, inter_2_nb_removed = None, use_exclusive_intersection = True):
  relations = []
  ex_inters = []
  subset_2_ex_inter = {  }
  prune_levels = []
  
  gene_2_gene_list = defaultdict(set)
  for gene_list in gene_lists:
    for gene in gene_list.genes:
      gene_2_gene_list[gene].add(gene_list)
  gene_2_gene_list = { gene : frozenset(subset) for gene, subset in gene_2_gene_list.items() }
  
  if not height_unit:
    height_unit = height_factor / len(genes)
    
  def compute_height(nb_gene): return max(height_unit * nb_gene, 0.25)
  
  next_id = 1
  if use_exclusive_intersection:
    for gene in genes:
      subset   = gene_2_gene_list[gene]
      ex_inter = subset_2_ex_inter.get(subset)
      if ex_inter is None:
        ex_inter = subset_2_ex_inter[subset] = ExclusiveIntersection(next_id, subset)
        ex_inters.append(ex_inter)
        next_id += 1
      ex_inter.genes     .add(gene)
      ex_inter.orig_genes.add(gene)
  else:
    for gene in genes:
      subset0 = gene_2_gene_list[gene]
      for subset in all_subsets(subset0):
        subset = frozenset(subset)
        ex_inter = subset_2_ex_inter.get(subset)
        if ex_inter is None:
          ex_inter = subset_2_ex_inter[subset] = ExclusiveIntersection(next_id, subset)
          ex_inters.append(ex_inter)
          next_id += 1
        ex_inter.genes     .add(gene)
        ex_inter.orig_genes.add(gene)
      
  for gene_list in gene_lists:
    subset = frozenset([gene_list])
    if not subset in subset_2_ex_inter:
      ex_inter = subset_2_ex_inter[subset] = ExclusiveIntersection(next_id, subset)
      ex_inters.append(ex_inter)
      next_id += 1

  if inter_2_nb_removed:
    for ex_inter in ex_inters[:]:
      nb = inter_2_nb_removed[len(ex_inter.subset)]
      if len(ex_inter.genes) <= nb:
        ex_inters.remove(ex_inter)
      else:
        for i in range(nb): ex_inter.genes.pop()
        
  if len(ex_inters) > max_nb_box:
    selected_ex_inters = prune(ex_inters, max_nb_box)
  else:
    selected_ex_inters = ex_inters

  selected_ex_inters_set = set(selected_ex_inters)
  
  if len(gene_lists) <= 15: rotate = None
  else:                     rotate = 10.0
  gene_list_id_2_nb_inter_shown = {}
  for i, gene_list in enumerate(gene_lists):
    nb_inter = nb_inter_shown = 0
    for subset, ex_inter in subset_2_ex_inter.items():
      if (gene_list in subset) and (ex_inter.orig_genes):
        nb_inter += 1
        if ex_inter in selected_ex_inters_set: nb_inter_shown += 1
    gene_list_id_2_nb_inter_shown[i] = nb_inter_shown
    label = "%s (%s)" % (gene_list.name, len(gene_list.genes))
    gene_list.element = Element(None, label,
                                color = (0.85, 0.85, 0.85), rotate = rotate)
    gene_list.element.details = """<b>%s</b><br/>%s elements<br/>%s intersections (<span id="nb_inter_shown_%s">%s</span> shown)""" % (
                                   gene_list.name, len(gene_list.genes), nb_inter, i, nb_inter_shown)
    
    
  properties = []
  next_id = 1
  
  max_nb_set = max((len(ex_inter.subset) for ex_inter in selected_ex_inters), default = 0)
  for ex_inter in selected_ex_inters:
    if (not ex_inter.genes) and (len(ex_inter.subset) != 1):
      ex_inter.id = next_id
      next_id += 1
    else:
      weight = compute_height(len(ex_inter.genes))
      
      #weight = weight / 2# HACK
      #weight = weight / sum(gene_list.element.weight for gene_list in ex_inter.subset) * 1.5# HACK
      
      if weight <= 0.7: name = " "
      else:             name = "%s" % len(ex_inter.genes)
      
      if len(ex_inter.genes) == len(ex_inter.orig_genes):
        nb_box  = str(len(ex_inter.genes))
      else:
        nb_box  = "%s (%s after clustering)" % (len(ex_inter.orig_genes), len(ex_inter.genes))
        
      details = """<span class="nbel">%s</span>&nbsp;elements in box %s<br/>(click to view them)<br/>""" % (nb_box, " & ".join(sorted(gene_list.name for gene_list in ex_inter.subset)))
      
      color = hsv2rgb(0.65 * (1.0 - (len(ex_inter.subset) - 1) / (max_nb_set - 1)), 0.30, 0.95)
      
      prop = Property(None, name, weight = weight, details = details, color = color)
      properties.append(prop)
      prop.ex_inter = ex_inter
      for gene_list in ex_inter.subset:
        relation = Relation(prop, gene_list.element)
        relations.append(relation)
        
  nb_box0 = len(selected_ex_inters)
  
  import random
  random.seed(1)
  
  if len(gene_lists) < 10:
    order = best_elements_order_np_hole(relations)
  else:
    order = best_elements_order_optim(relations, nb_tested_solution = nb_tested_solution)
    #order = best_elements_order_optim(relations, nb_tested_solution = None)


  #order = [gene_list.element for gene_list in gene_lists] # HACK
  
    
  html_page = HTMLPage("RainBio", has_brython = True, static_url = static_url)
  html_page.html += """
<style>
.rainbowbox_box { overflow-y: visible; }
.nbel { font-weight: bold; }
</style>
"""
  
  html_page.html += """
<table style="margin-top: 0.5em; width: 100%;"><tr><td valign="top" style="width: 82%;">
"""
  
  html_page.rainbowbox(relations,
                       order = order,
                       optimize_box_order = best_boxes_order_by_cardinality,
                       hideable_element = True,
                       clickable_properties = True,
                       grid = "overlay",
  )
  
  html_page.html += """
</td><td valign="top">
"""
  
  prop_2_box = { prop : box  for box in html_page.boxes for prop in box.properties }
  for prop, box in prop_2_box.items():
    prop.ex_inter.id = box.html_id
    
  box_2_elements = { ex_inter.id : list(ex_inter.orig_genes) for ex_inter in ex_inters }
  if detail_on_demand:
    box_2_name = { ex_inter.id : " &amp; ".join(sorted(i.name for i in ex_inter.subset)) for ex_inter in ex_inters }
  else:
    box_2_name = {}
    
  prune_levels.append(PruneLevel(selected_ex_inters, compute_height, prop_2_box, gene_list_id_2_nb_inter_shown))
  
  if prune_levels[-1].nb_box == len(ex_inters):
    prune_levels[-1].min_nb_gene_per_box = 1

  if dynamic_clustering:
    while prune_levels[-1].nb_box > len(gene_lists):
      selected_ex_inters = prune(ex_inters, prune_levels[-1].nb_box - 1)
      #print("PRUNE", selected_ex_inters)
      if not selected_ex_inters: break
      
      selected_ex_inters_set = set(selected_ex_inters)
      gene_list_id_2_nb_inter_shown = {}
      for i, gene_list in enumerate(gene_lists):
        gene_list_id_2_nb_inter_shown[i] = 0
        for subset, ex_inter in subset_2_ex_inter.items():
          if (gene_list in subset) and (ex_inter.orig_genes):
            if ex_inter in selected_ex_inters_set: gene_list_id_2_nb_inter_shown[i] += 1
      
      prune_levels.append(PruneLevel(selected_ex_inters, compute_height, prop_2_box, gene_list_id_2_nb_inter_shown))
      
  if not detail_on_demand:
    for prune_level in prune_levels:
      prune_level.box_includes = {}
      
  html_page.html += """
<h3 style="margin-top: 0px;">RainBio</h3>
<i>Visualizing sets in biology<br/> with rainbow boxes</i>
<br/><br/>
<b>%s</b> sets<br/><br/>
<b>%s</b> distinct elements<br/><br/>
<b>%s</b> non-empty exclusive intersections<br/><br/>

Box clustering: <input type="button" onmouseup="window.on_stop_timer(); event.stopPropagation();" onmousedown="window.on_change_min_nb_gene_per_box(-1); event.stopPropagation();" value="-"/><input type="button" onmouseup="window.on_stop_timer(); event.stopPropagation();" onmousedown="window.on_change_min_nb_gene_per_box(1); event.stopPropagation();" value="+"></input><br/><br/>
<span id="nb_box" style="font-weight: bold;">%s</span> boxes shown<br/>
At least <span id="min_nb_gene_per_box" style="font-weight: bold;">%s</span> elements per box<br/><br/>


""" % (len(gene_lists), len(genes), len(ex_inters), nb_box0, prune_levels[0].min_nb_gene_per_box)
  
  html_page.html += """
<script type="text/python">
from browser import document, alert, window, timer

class PruneLevel(object):
  def __init__(self, min_nb_gene_per_box, nb_box, box_nbs, box_includes, gene_list_id_2_nb_inter_shown):
    self.min_nb_gene_per_box = min_nb_gene_per_box
    self.nb_box              = nb_box
    self.box_nbs             = box_nbs
    self.box_includes        = box_includes
    self.gene_list_id_2_nb_inter_shown = gene_list_id_2_nb_inter_shown

prune_levels = %s
box_2_elements = %s
box_2_name = %s
current_prune_level = 0
max_nb_set = %s

def compute_height(nb_gene): return max(%s * nb_gene, 0.25)

""" % (prune_levels, box_2_elements, box_2_name, max_nb_set, height_unit)
    
  html_page.html += """
timer_id = None
def on_change_min_nb_gene_per_box(delta):
  global timer_id
  change_min_nb_gene_per_box(delta)
  timer_id = timer.set_timeout(lambda : change_min_nb_gene_per_box(delta), 100)

def on_stop_timer():
  global timer_id
  timer.clear_timeout(timer_id)
  timer_id = None
window.on_stop_timer = on_stop_timer

def on_change_min_nb_gene_per_box(delta):
  global timer_id
  global current_prune_level
  if current_prune_level + delta < 0: return
  if current_prune_level + delta >= len(prune_levels): return
  
  current_prune_level += delta
  prune_level = prune_levels[current_prune_level]
  
  if prune_level.min_nb_gene_per_box == 0:  document["min_nb_gene_per_box"].innerHTML = "-"
  else: document["min_nb_gene_per_box"].innerHTML = str(prune_level.min_nb_gene_per_box)

  nb_box = 0
  for box_id, nb in prune_level.box_nbs.items():
    box = box0 = document[box_id]
    while box.lastElementChild: box = box.lastElementChild
    size_box = box.parentNode
    if nb == 0:
      box0.style.display = "none"
    else:
      nb_box += 1
      if box0.style.display == "none":
        box0.style.display = "block"
      height = compute_height(nb)
      new_height = "%sem" % height
      if new_height != size_box.style.height:
        size_box.style.height = "%sem" % height
      if height <= 0.7: box.innerHTML = " "
      else:
        box.innerHTML = str(nb)
        if height <= 1.0:
          box.style.marginTop = ""
          box.style.marginBottom = ""
          box.style.fontSize = "80%"
          box.style.lineHeight = height
          size_box.style.display = ""
        else:
          box.style.marginTop = "auto"
          box.style.marginBottom = "auto"
          box.style.fontSize = ""
          box.style.lineHeight = ""
          size_box.style.display = "flex"
    
    box_detail = box0.firstElementChild.lastElementChild.firstElementChild.firstElementChild
    nb0 = len(box_2_elements[box_id])
    if nb == nb0:
      box_detail.innerHTML = str(nb)
    else:
      box_detail.innerHTML = "%s (%s after clustering)" % (nb0, nb)
    
  document["nb_box"].innerHTML = str(nb_box)

  for k,v in prune_level.gene_list_id_2_nb_inter_shown.items():
    document["nb_inter_shown_%s" % k].innerHTML = v
  
  window.move_boxes()

  colorize_boxes()
  
  timer_id = timer.set_timeout(lambda : on_change_min_nb_gene_per_box(delta), 100)
  
window.on_change_min_nb_gene_per_box = on_change_min_nb_gene_per_box

# Hide empty boxes
for box_id, nb in prune_levels[current_prune_level].box_nbs.items():
  box = box0 = document[box_id]
  while box.lastElementChild: box = box.lastElementChild
  size_box = box.parentNode
  if nb == 0: box0.style.display = "none"


def on_box_click_user(box_id):
  p = window.open("", "_blank")
  html  = "<html><body>"
  prune_level = prune_levels[current_prune_level]
  
  if prune_level.box_nbs[box_id] == 1: s = ""
  else: s ="s"
  html += "# <b>%s</b> element%s in total<br/><br/>" % (prune_level.box_nbs[box_id], s)
  
  for included_id in prune_level.box_includes[box_id]:
    if len(box_2_elements[included_id]) == 1: s = ""
    else: s ="s"
    html += "# <b>%s</b> element%s in %s<br/>%s<br/><br/>" % (len(box_2_elements[included_id]), s, box_2_name[included_id], "<br/>".join(box_2_elements[included_id]))
    
  html += "</body></html>"
  p.document.write(html)
  p.document.close()


window.on_box_click_user = on_box_click_user



def hsv2rgb(h, s, v):
  if s == 0.0: return v, v, v
  i = int(h*6.0)
  f = (h*6.0) - i
  p = v*(1.0 - s)
  q = v*(1.0 - s*f)
  t = v*(1.0 - s*(1.0-f))
  i = i%6
  if i == 0: return v, t, p
  if i == 1: return q, v, p
  if i == 2: return p, v, t
  if i == 3: return p, q, v
  if i == 4: return t, p, v
  if i == 5: return v, p, q
  raise ValueError
def rgb2css(r, g, b):
  return "rgb(%s, %s, %s)" % (int(round(255 * r)), int(round(255 * g)), int(round(255 * b)))

def colorize_boxes():
  gray = rgb2css(0.82, 0.82, 0.82)
  prune_level = prune_levels[current_prune_level]
  if prune_level.min_nb_gene_per_box == 1:
    for box_id in window.box_id_2_cols:
      cols = window.box_id_2_cols[box_id]
      box = document[box_id]
      color = rgb2css(*hsv2rgb(0.65 * (1.0 - (len(cols) - 1) / (max_nb_set - 1)), 0.30, 0.95))
      box.firstElementChild.style.background = color
  else:
    for box_id in window.box_id_2_cols:
      nb0 = len(box_2_elements[box_id])
      nbclust = prune_level.box_nbs[box_id]
      if nbclust == 0: continue
      cols = window.box_id_2_cols[box_id]
      box = document[box_id]
      dark = rgb2css(*hsv2rgb(0.65 * (1.0 - (len(cols) - 1) / (max_nb_set - 1)), 0.40, 0.75))
      if nb0 == nbclust:
        box.firstElementChild.style.background = dark
      else:
        color = rgb2css(*hsv2rgb(0.65 * (1.0 - (len(cols) - 1) / (max_nb_set - 1)), 0.30, 0.95))
        r = 100.0 * nb0 / nbclust
        box.firstElementChild.style.background = "linear-gradient(0deg, %s, %s %s%%, %s %s%%)" % (dark, dark, r, color, r)

colorize_boxes()
for box_id in window.box_id_2_cols:
  box = document[box_id]
  box.firstElementChild.lastElementChild.style.marginRight = "0.3em"
  box.firstElementChild.lastElementChild.style.paddingLeft = "0.5em"

</script>"""
    
  html_page.html += """
</td><tr></table>
"""
  
  return html_page



if __name__ == "__main__":  
  #gene_lists = read_interactivenn("./rainbowbox/doc/generated_dataset.ivenn")
  #gene_lists = read_interactivenn("./rainbowbox/doc/dataset_3.ivenn")
  #gene_lists = read_interactivenn("./rainbowbox/doc/prostate_dataset.ivenn")
  #gene_lists = read_interactivenn("./rainbowbox/doc/banana_dataset.ivenn")
  #gene_lists = read_interactivenn("./rainbowbox/doc/golub_8.ivenn")
  #gene_lists = read_interactivenn("./rainbowbox/doc/golub_20.ivenn")
  #gene_lists = read_interactivenn("./rainbowbox/doc/golub_38.ivenn")
  #gene_lists = read_interactivenn("./rainbowbox/doc/leuco_21.ivenn")
  #genes, gene_lists = read_interactivenn("/home/jiba/tmp/movie_28.ivenn")
  #genes, gene_lists = read_interactivenn("./rainbowbox/doc/trivial_dataset.ivenn")
  
  html_page = gene_lists_2_html_page(genes, gene_lists,
                                     max_nb_box = 96,
                                     height_factor = 75.0,
                                     detail_on_demand = False,
                                     dynamic_clustering = False,
                                     nb_tested_solution = None,
  )
  
  html_page.javascripts.append("brython.js")
  html_page.javascripts.append("brython_stdlib.js")
  
  open("/tmp/rainbio.html", "w").write(html_page.get_html_with_header())
  
  
