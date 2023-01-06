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


from rainbowbox import *
from rainbowbox.order_elements import *

#import rainbowbox
#Element, Property = rainbowbox.Property, rainbowbox.Element


# element_A = Element(None, "Ala", "Alanine")
# element_R = Element(None, "Arg", "Arginine")
# element_N = Element(None, "Asn", "Asparagine")
# element_D = Element(None, "Asp", "Aspartate")
# element_C = Element(None, "Cys", "Cystéine")
# element_E = Element(None, "Glu", "Glutamate")
# element_Q = Element(None, "Gln", "Glutamine")
# element_G = Element(None, "Gly", "Glycine")
# element_H = Element(None, "His", "Histidine")
# element_I = Element(None, "Ile", "Isoleucine")
# element_L = Element(None, "Leu", "Leucine")
# element_K = Element(None, "Lys", "Lysine")
# element_M = Element(None, "Mét", "Méthionine")
# element_F = Element(None, "Phé", "Phénylalanine")
# element_P = Element(None, "Pro", "Proline")
# element_S = Element(None, "Sér", "Sérine")
# element_T = Element(None, "Thr", "Thréonine")
# element_W = Element(None, "Trp", "Tryptophane")
# element_Y = Element(None, "Tyr", "Tyrosine")
# element_V = Element(None, "Val", "Valine")

element_A = Element(None, "<b>A</b>", "Alanine")
element_R = Element(None, "<b>R</b>", "Arginine")
element_N = Element(None, "<b>N</b>", "Asparagine")
element_D = Element(None, "<b>D</b>", "Aspartate")
element_C = Element(None, "<b>C</b>", "Cystéine")
element_E = Element(None, "<b>E</b>", "Glutamate")
element_Q = Element(None, "<b>Q</b>", "Glutamine")
element_G = Element(None, "<b>G</b>", "Glycine")
element_H = Element(None, "<b>H</b>", "Histidine")
element_I = Element(None, "<b>I</b>", "Isoleucine")
element_L = Element(None, "<b>L</b>", "Leucine")
element_K = Element(None, "<b>K</b>", "Lysine")
element_M = Element(None, "<b>M</b>", "Méthionine")
element_F = Element(None, "<b>F</b>", "Phénylalanine")
element_P = Element(None, "<b>P</b>", "Proline")
element_S = Element(None, "<b>S</b>", "Sérine")
element_T = Element(None, "<b>T</b>", "Thréonine")
element_W = Element(None, "<b>W</b>", "Tryptophane")
element_Y = Element(None, "<b>Y</b>", "Tyrosine")
element_V = Element(None, "<b>V</b>", "Valine")

property_petit       = Property(None, "Petit")
property_minuscule   = Property(None, "Minuscule")
property_hydrophobe  = Property(None, "Hydrophobe")
property_aliphatique = Property(None, "Aliphatique")
property_aromatique  = Property(None, "Aromatique")
property_polaire     = Property(None, "Polaire")
property_charge      = Property(None, "Chargé")
property_charge_p    = Property(None, "Positif")
property_charge_m    = Property(None, "Négatif")
property_soufre      = Property(None, "Soufré")
property_essentiel   = Property(None, "Essentiel")

relations = [
  Relation(element_P, property_petit),
  Relation(element_A, property_petit),
  Relation(element_G, property_petit),
  Relation(element_C, property_petit),
  Relation(element_S, property_petit),
  Relation(element_N, property_petit),
  Relation(element_T, property_petit),
  Relation(element_D, property_petit),
  Relation(element_V, property_petit),

  Relation(element_A, property_minuscule),
  Relation(element_G, property_minuscule),
  Relation(element_C, property_minuscule),
  Relation(element_S, property_minuscule),

  Relation(element_A, property_hydrophobe),
  Relation(element_G, property_hydrophobe),
  Relation(element_C, property_hydrophobe),
  Relation(element_T, property_hydrophobe),
  Relation(element_V, property_hydrophobe),
  Relation(element_I, property_hydrophobe),
  Relation(element_L, property_hydrophobe),
  Relation(element_M, property_hydrophobe),
  Relation(element_F, property_hydrophobe),
  Relation(element_Y, property_hydrophobe),
  Relation(element_W, property_hydrophobe),
  Relation(element_H, property_hydrophobe),
  Relation(element_K, property_hydrophobe),
  
  Relation(element_I, property_aliphatique),
  Relation(element_V, property_aliphatique),
  Relation(element_L, property_aliphatique),
  
  Relation(element_F, property_aromatique),
  Relation(element_Y, property_aromatique),
  Relation(element_W, property_aromatique),
  Relation(element_H, property_aromatique),

  Relation(element_C, property_polaire),
  Relation(element_S, property_polaire),
  Relation(element_N, property_polaire),
  Relation(element_T, property_polaire),
  Relation(element_D, property_polaire),
  Relation(element_E, property_polaire),
  Relation(element_Q, property_polaire),
  Relation(element_Y, property_polaire),
  Relation(element_H, property_polaire),
  Relation(element_K, property_polaire),
  Relation(element_R, property_polaire),
  Relation(element_W, property_polaire),
  
  #Relation(element_D, property_charge),
  #Relation(element_E, property_charge),
  #Relation(element_H, property_charge),
  #Relation(element_K, property_charge),
  #Relation(element_R, property_charge),
  
  Relation(element_H, property_charge_p),
  Relation(element_K, property_charge_p),
  Relation(element_R, property_charge_p),
  
  Relation(element_D, property_charge_m),
  Relation(element_E, property_charge_m),

  
 Relation(element_C, property_soufre),
 Relation(element_M, property_soufre),
  
# Relation(element_F, property_essentiel),
# Relation(element_L, property_essentiel),
# Relation(element_M, property_essentiel),
# Relation(element_K, property_essentiel),
# Relation(element_I, property_essentiel),
# Relation(element_V, property_essentiel),
# Relation(element_T, property_essentiel),
# Relation(element_W, property_essentiel),
# Relation(element_H, property_essentiel),
# Relation(element_C, property_essentiel, hatch = True, details = "semi-essentiel"),
# Relation(element_G, property_essentiel, hatch = True, details = "semi-essentiel"),
# Relation(element_Y, property_essentiel, hatch = True, details = "semi-essentiel"),
]


#order = best_elements_order_heuristic(relations)
order = best_elements_order_optim(relations, nb_tested_solution = 1000)
#order = best_elements_order_hybrid(relations, nb_tested_solution = 50)

#import random
#order = list({r.element for r in relations})
#random.shuffle(order)

html_page = HTMLPage()
html_page.rainbowbox(relations, order = order, use_element_details_in_relation = True)

#import rainbowbox.glyph
#import base64
#from io import BytesIO
#
#fig = rainbowbox.glyph.create_glyph(relations, order)
#png = BytesIO()
#fig.savefig(png, format = "png")
#png = png.getvalue()
#html_page.html += """<br/><center><img width="300" src="data:image/png;base64,%s"/></center><br/>\n""" % base64.b64encode(png).decode("latin")

html_page.show()
