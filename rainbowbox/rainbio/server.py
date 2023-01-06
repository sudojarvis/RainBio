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

from functools import lru_cache
import os, sqlite3, flask, hashlib
from flask import Blueprint, request, url_for, Response

from rainbowbox.rainbio import *

app = Blueprint("rainbio", __name__, static_folder = "static")


DATABASE = os.path.join(os.path.dirname(__file__), "counter%s.sqlite3" % ("_localhost" * flask.IS_LOCALHOST))
if not os.path.exists(DATABASE):
  db = sqlite3.connect(DATABASE)
  print("* RainBio * Create database")
  db.execute("""CREATE TABLE counter (h TEXT UNIQUE)""")
  db.execute("""CREATE TABLE visit   (nb INTEGER)""")
  db.execute("""INSERT INTO visit VALUES (0)""")
  db.commit()
else:
  db = sqlite3.connect(DATABASE)


@lru_cache(maxsize=32)
def dataset_2_html_page(dataset):
  genes, gene_lists = reads_interactivenn(dataset)
  
  if not flask.IS_LOCALHOST:
    if (len(gene_lists) > 15) or (len(genes) > 40000): return None
    
  html_page = gene_lists_2_html_page(genes, gene_lists)
  html_page.javascripts.append(url_for("rainbio.static", filename = "brython.js"))
  html_page.javascripts.append(url_for("rainbio.static", filename = "brython_stdlib.js"))
  
  return html_page.get_html_with_header()


@app.route("/results.html", methods = ["GET", "POST"])
def page_visu():
  preload_dataset = request.args.get("preload_dataset")
  if preload_dataset and preload_dataset.endswith(".ivenn") and (not ".." in preload_dataset):
    file_data = open(os.path.join(os.path.dirname(__file__), "static", preload_dataset)).read()
    
  else:
    file_data = request.files["dataset"].read()

  encoded_data = file_data
  if isinstance(encoded_data, str): encoded_data = encoded_data.encode("utf8")
  h = hashlib.sha1(encoded_data).hexdigest()
  cursor = db.cursor()
  cursor.execute("""INSERT OR IGNORE INTO counter VALUES (?)""", (h,))
  cursor.execute("""UPDATE visit SET nb = (SELECT nb + 1 FROM visit LIMIT 1)""")
  db.commit()
  
  html = dataset_2_html_page(file_data)
  
  if not html: html = """<html><body>
RainBio is currently limited to 15 sets and 40000 elements (<i>e.g.</i> genes)
</body></html>"""
  
  return html


@app.route("/counter.html")
def page_counter():
  cursor = db.cursor()
  nb_visit   = cursor.execute("""SELECT nb FROM visit;""").fetchall()[0][0]
  nb_dataset = cursor.execute("""SELECT COUNT(*) FROM counter;""").fetchall()[0][0]
  
  html = """<html><body>
%s visits.<br/>
%s datasets visualized.
</body></html>""" % (nb_visit, nb_dataset)
  
  r = Response(html)
  r.cache_control.no_cache = True
  return r


