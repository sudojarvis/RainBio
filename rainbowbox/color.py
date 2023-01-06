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


def rgb2hsv(r, g, b):
  maxc = max(r, g, b)
  minc = min(r, g, b)
  v = maxc
  if minc == maxc:
    return 0.0, 0.0, v
  s = (maxc-minc) / maxc
  rc = (maxc-r) / (maxc-minc)
  gc = (maxc-g) / (maxc-minc)
  bc = (maxc-b) / (maxc-minc)
  if r == maxc:
    h = bc-gc
  elif g == maxc:
    h = 2.0+rc-bc
  else:
    h = 4.0+gc-rc
  h = (h/6.0) % 1.0
  return h, s, v

def luminance(r, g, b): return 0.2126 * r + 0.7152 * g + 0.0722 * b

def set_luminance(l, r, g, b):
  ratio = l / luminance(r, g, b)
  r *= ratio
  g *= ratio
  b *= ratio
  print(luminance(r, g, b))
  #m = max(r, g, b)
  #if m > 1.0:
  #  m -= 1.0
  #  r -= m
  #  g -= m
  #  b -= m
  if r > 1.0: r = 1.0
  if g > 1.0: g = 1.0
  if b > 1.0: b = 1.0
  return r, g, b

def hsv2rgb(h, s, v):
  if s == 0.0: return v, v, v
  i = int(h*6.0) # XXX assume int() truncates!
  f = (h*6.0) - i
  p = v*(1.0 - s)
  q = v*(1.0 - s*f)
  t = v*(1.0 - s*(1.0-f))
  i = i%6
  if i == 0:
    return v, t, p
  if i == 1:
    return q, v, p
  if i == 2:
    return p, v, t
  if i == 3:
    return p, q, v
  if i == 4:
    return t, p, v
  if i == 5:
    return v, p, q
  raise ValueError

def rgb2web(r, g, b):
  return "#%02X%02X%02X" % (int(round(255 * r)), int(round(255 * g)), int(round(255 * b)))

def rgb2css(r, g, b):
  return "rgb(%s, %s, %s)" % (int(round(255 * r)), int(round(255 * g)), int(round(255 * b)))

def rgb_mean(rgbs, nb = None):
  if not rgbs: return (0, 0, 0)
  r = g = b = 0
  for rgb in rgbs:
    r += rgb[0]
    g += rgb[1]
    b += rgb[2]
  return r / len(rgbs), g / len(rgbs), b / len(rgbs)

def rgb_weighted_mean(rgbs, weights):
  if not rgbs: return (0, 0, 0)
  r = g = b = 0
  for rgb, weight in zip(rgbs, weights):
    r += weight * rgb[0]
    g += weight * rgb[1]
    b += weight * rgb[2]
  t = sum(weights)
  return r / t, g / t, b / t

def rgb_blend_color(rgb1, rgb2, f):
  g = 1.0 - f
  return (rgb1[0] * g + rgb2[0] * f, rgb1[1] * g + rgb2[1] * f, rgb1[2] * g + rgb2[2] * f)

def rgb_lighten(rgb, p_white = 0.2):
  return p_white + rgb[0] * (1 - p_white), p_white + rgb[1] * (1 - p_white), p_white + rgb[2] * (1 - p_white)

def rgb_hatch_color(rgb):
  h, s, v = rgb2hsv(*rgb)
  return rgb_lighten(rgb, 0.6 - (s - 0.1) * 0.6)

def rainbow_colors(nb):
  return [hsv2rgb(i / (nb - 1), 0.25, 1.0) for i in range(nb)]

#def rainbow_colors(nb):
#  return [hsv2rgb(0.7 * i / (nb - 1), 0.25, 1.0) for i in range(nb)]

box_color_mean = rgb_mean

#def box_color_mean(rgbs, nb):
#  if not rgbs: return (0, 0, 0)
#  if len(rgbs) == 1: return rgbs[0]
#  
#  hsvs = [rgb2hsv(*rgb) for rgb in rgbs]
#  h = sum(hsv[0] for hsv in hsvs) / len(hsvs)
#
#  ratio = (len(hsvs) - 1) / (nb - 1)   
#  return hsv2rgb(h, 0.25 - 0.25 * ratio, 1.0 - 0.15 * ratio)

