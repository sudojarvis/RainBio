
import rainbowbox
from rainbowbox import *
from rainbowbox.order_elements import *
from rainbowbox.color import *

#import rainbowbox
#Element, Property = rainbowbox.Property, rainbowbox.Element

element_A = Element(None, "<b>A</b>", "Alanine")
element_R = Element(None, "<b>R</b>", "Arginine")
element_N = Element(None, "<b>N</b>", "Asparagine")
element_D = Element(None, "<b>D</b>", "Aspartate")
element_C = Element(None, "<b>C</b>", "Cysteine")
element_E = Element(None, "<b>E</b>", "Glutamate")
element_Q = Element(None, "<b>Q</b>", "Glutamine")
element_G = Element(None, "<b>G</b>", "Glycine")
element_H = Element(None, "<b>H</b>", "Histidine")
element_I = Element(None, "<b>I</b>", "Isoleucine")
element_L = Element(None, "<b>L</b>", "Leucine")
element_K = Element(None, "<b>K</b>", "Lysine")
element_M = Element(None, "<b>M</b>", "Methionine")
element_F = Element(None, "<b>F</b>", "Phenylalanine")
element_P = Element(None, "<b>P</b>", "Proline")
element_S = Element(None, "<b>S</b>", "Serine")
element_T = Element(None, "<b>T</b>", "Threonine")
element_W = Element(None, "<b>W</b>", "Tryptophan")
element_Y = Element(None, "<b>Y</b>", "Tyrosine")
element_V = Element(None, "<b>V</b>", "Valine")

"""
element_A = Element(None, "Ala", "Alanine")
element_R = Element(None, "Arg", "Arginine")
element_N = Element(None, "Asn", "Asparagine")
element_D = Element(None, "Asp", "Aspartate")
element_C = Element(None, "Cys", "Cysteine")
element_E = Element(None, "Glu", "Glutamate")
element_Q = Element(None, "Gln", "Glutamine")
element_G = Element(None, "Gly", "Glycine")
element_H = Element(None, "His", "Histidine")
element_I = Element(None, "Ile", "Isoleucine")
element_L = Element(None, "Leu", "Leucine")
element_K = Element(None, "Lys", "Lysine")
element_M = Element(None, "Met", "Methionine")
element_F = Element(None, "Phe", "Phenylalanine")
element_P = Element(None, "Pro", "Proline")
element_S = Element(None, "Ser", "Serine")
element_T = Element(None, "Thr", "Threonine")
element_W = Element(None, "Trp", "Tryptophan")
element_Y = Element(None, "Tyr", "Tyrosine")
element_V = Element(None, "Val", "Valine")
"""

property_small      = Property(None, "Small")
property_tiny       = Property(None, "Tiny")
property_hydrophobe = Property(None, "Hydrophobic")
property_aliphatic  = Property(None, "Aliphatic")
property_aromatic   = Property(None, "Aromatic")
property_polar      = Property(None, "Polar")
property_charged    = Property(None, "Charged")
property_positive   = Property(None, "Positive")
property_negative   = Property(None, "Negative")
property_with_S     = Property(None, "Sulfur")
property_essential  = Property(None, "Essential")
property_c_beta     = Property(None, "C-β branching")
property_func       = Property(None, "Functional")
property_buried     = Property(None, "Buried")
#property_metal      = Property(None, "Metal-ion binding")
#property_ca2      = Property(None, "Ca2+ binding")
#property_cu2      = Property(None, "Cu2+ binding")
#property_mg2      = Property(None, "Mg2+ binding")
#property_fe3      = Property(None, "Fe3+ binding")
#property_mn2      = Property(None, "Mn2+ binding")
#property_zn2      = Property(None, "Zn2+ binding")

relations = [
  Relation(element_P, property_small),
  Relation(element_A, property_small),
  Relation(element_G, property_small),
  Relation(element_C, property_small),
  Relation(element_S, property_small),
  Relation(element_N, property_small),
  Relation(element_T, property_small),
  Relation(element_D, property_small),
  Relation(element_V, property_small),

  Relation(element_A, property_tiny),
  Relation(element_G, property_tiny),
  Relation(element_C, property_tiny),
  Relation(element_S, property_tiny),

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
  
  Relation(element_I, property_aliphatic),
  Relation(element_V, property_aliphatic),
  Relation(element_L, property_aliphatic),
  
  #Relation(element_A, property_aliphatic),
  #Relation(element_P, property_aliphatic),
  #Relation(element_M, property_aliphatic),
  
  Relation(element_F, property_aromatic),
  Relation(element_Y, property_aromatic),
  Relation(element_W, property_aromatic),
  Relation(element_H, property_aromatic),

  Relation(element_C, property_polar),
  Relation(element_S, property_polar),
  Relation(element_N, property_polar),
  Relation(element_T, property_polar),
  Relation(element_D, property_polar),
  Relation(element_E, property_polar),
  Relation(element_Q, property_polar),
  Relation(element_Y, property_polar),
  Relation(element_H, property_polar),
  Relation(element_K, property_polar),
  Relation(element_R, property_polar),
  Relation(element_W, property_polar),
  
  #Relation(element_D, property_charged),
  #Relation(element_E, property_charged),
  #Relation(element_H, property_charged),
  #Relation(element_K, property_charged),
  #Relation(element_R, property_charged),
  
  Relation(element_H, property_positive),
  Relation(element_K, property_positive),
  Relation(element_R, property_positive),
  
  Relation(element_D, property_negative),
  Relation(element_E, property_negative),
  
 #Relation(element_C, property_with_S),
 #Relation(element_M, property_with_S),
  
# Relation(element_V, property_c_beta),
# Relation(element_I, property_c_beta),
# Relation(element_T, property_c_beta),
  
# Relation(element_H, property_func),
# Relation(element_C, property_func),
# Relation(element_S, property_func),
# Relation(element_K, property_func),
# Relation(element_T, property_func),
# Relation(element_N, property_func, hatch = True),
# Relation(element_R, property_func, hatch = True),
# Relation(element_Q, property_func, hatch = True),
# Relation(element_E, property_func, hatch = True),

  
  # Relation(element_D, property_ca2),
  # Relation(element_E, property_ca2),
  # Relation(element_Q, property_ca2),
  # Relation(element_G, property_ca2),

  # Relation(element_H, property_cu2),
  
  # Relation(element_D, property_mg2),
  # Relation(element_E, property_mg2),
  
  # Relation(element_H, property_fe3),
  # Relation(element_D, property_fe3),
  # Relation(element_E, property_fe3),
  # Relation(element_C, property_fe3),
  # Relation(element_W, property_fe3),
  
  # Relation(element_D, property_mn2),
  # Relation(element_H, property_mn2),
  # Relation(element_E, property_mn2),

  # Relation(element_C, property_zn2),
  # Relation(element_H, property_zn2),

  
# Relation(element_F, property_essential),
# Relation(element_L, property_essential),
# Relation(element_M, property_essential),
# Relation(element_K, property_essential),
# Relation(element_I, property_essential),
# Relation(element_V, property_essential),
# Relation(element_T, property_essential),
# Relation(element_W, property_essential),
# Relation(element_H, property_essential),
# Relation(element_C, property_essential, hatch = True, details = "semi-essential"),
# Relation(element_G, property_essential, hatch = True, details = "semi-essential"),
# Relation(element_Y, property_essential, hatch = True, details = "semi-essential"),

# Relation(element_A, property_buried),
# Relation(element_C, property_buried),
# Relation(element_I, property_buried),
# Relation(element_L, property_buried),
# Relation(element_M, property_buried),
# Relation(element_F, property_buried),
# Relation(element_W, property_buried),
# Relation(element_V, property_buried),


]

order = best_elements_order_optim(relations, nb_tested_solution = 100)
#order = best_elements_order_pca(relations)
#order = best_elements_order_tree(relations)
#order = best_elements_order_abc(relations)
#order = [element_P, element_E, element_D, element_N, element_S, element_A, element_G, element_C, element_T, element_V, element_I, element_L, element_M, element_F, element_W, element_Y, element_H, element_K, element_R, element_Q]
#order = [element_Q, element_E, element_D, element_P, element_N, element_S, element_A, element_G, element_C, element_T, element_V, element_I, element_L, element_M, element_F, element_W, element_Y, element_H, element_K, element_R]
#order = [element_E, element_D, element_P, element_N, element_S, element_A, element_G, element_C, element_T, element_V, element_I, element_L, element_M, element_F, element_W, element_Y, element_H, element_K, element_R, element_Q]

def rainbow_colors(nb):
  return [hsv2rgb(0.7 - 0.7 * i / (nb - 1), 0.25, 0.98) for i in range(nb)]
  #return [set_luminance(0.9, *hsv2rgb(0.7 - 0.7 * i / (nb - 1), 0.3, 1.0)) for i in range(nb)]

colors = rainbow_colors(len(order))

def rgb_hatch_color(rgb):
  return (1.0, 1.0, 1.0)

rainbowbox.draw.rgb_hatch_color = rgb_hatch_color


html_page = HTMLPage()
html_page.rainbowbox(relations, colors = colors, order = order, use_element_details_in_relation = True)
html_page.show()
