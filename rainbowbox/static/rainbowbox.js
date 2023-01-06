
function move_boxes() {
  for (var parent in parent_id_2_nb_cols) {
    if (box_id_2_y[parent_id_2_box_ids[parent][0]] == undefined) {
      move_boxes1(parent, true);
    }
    else {
      move_boxes2(parent, true);
    }
  }
}


function move_boxes1(parent, update_height) {
  var ys     = new Array();
  var box_y  = new Array();
  var boxes  = parent_id_2_box_ids[parent];
  var nb_col = parent_id_2_nb_cols[parent];
  var best_y;
  for (var i = 0; i < nb_col; i++) { ys[i] = 0; }
  
  var sel_boxes_id = parent_id_2_sel_box_ids[parent];
  
  if (sel_boxes_id == undefined) { // Non interactive
    for (var c in boxes) {
      c = boxes[c];
      move_box(c, ys, box_y, box_vertical_sep);
    }
  }
  else { // Interactive
    for (var c in boxes) {
      c = boxes[c];
      if (sel_boxes_id.includes(c)) {
        move_box_encastred(c, ys, box_y, 0);
      }
    }
    
    var max_y = 0;
    for (var i = 0; i < nb_col; i++) { if (ys[i] > max_y) max_y = ys[i]; }
    max_y = max_y + 100;
    for (var i = 0; i < nb_col; i++) { ys[i] = max_y; }
    
    for (var c in boxes) {
      c = boxes[c];
      if ( ! sel_boxes_id.includes(c)) {
        move_box(c, ys, box_y, 1);
      }
    }
  }
  best_y = 0;
  for (var i = 0; i < nb_col; i++) {
    if (best_y < ys[i]) best_y = ys[i];
  }
  best_y = best_y + 8;
  
  height = document.getElementById(parent_id_2_height_ids[parent][0]);
  var current_height;
  if (height.style.height == "") current_height = 0;
  else                           current_height = parseInt(height.style.height);
  if (update_height && (best_y > current_height)) {
    for (var i in parent_id_2_height_ids[parent]) {
      document.getElementById(parent_id_2_height_ids[parent][i]).style.height = best_y + "px";
    }
  }
  
  for (var c in boxes) {
    c = boxes[c];
    box_element = document.getElementById(c);
    if (box_element.style.display != "none") {
      box_element.style.top = (-box_y[c] - box_element.offsetHeight) + "px";
    }
    box_element.style.transition = "top 0.6s";
  }

}

function move_box(c, ys, box_y, extra) {
  var best_y = 0;
  var cols = box_id_2_cols[c];
  var box_element = document.getElementById(c);
  if(box_element.style.display == "none") return;
  if (extra != 0) {
    if (box_element.offsetHeight < 5) extra = 0.75;
  }
  
  for (col = cols[0]; col <= cols[cols.length - 1]; col++) {
    if (best_y < ys[col]) best_y = ys[col];
  }
  if (best_y != 0) best_y = best_y + extra;
  box_y[c] = best_y;
  
  best_y = best_y + extra;
  
  box_heights = box_id_2_heights[c];
  if (box_heights == undefined) {
    best_y = best_y + box_element.offsetHeight;
    for (col = cols[0]; col <= cols[cols.length - 1]; col++) ys[col] = best_y;
  }
  else {
    var box2_element = document.getElementById(box_heights[0]);
    best_y = best_y + box2_element.offsetHeight;
    for (col = cols[0]; col <= cols[cols.length - 1]; col++) {
      var box_extra1 = document.getElementById(box_heights[1][col - cols[0]]);
      var box_extra2 = document.getElementById(box_heights[2][col - cols[0]]);
      ys[col] = best_y + box_extra1.offsetHeight + box_extra2.offsetHeight;
    }
  }
}

function move_boxes2(parent, update_height) {
  var boxes  = parent_id_2_box_ids[parent];
  var nb_col = parent_id_2_nb_cols[parent];
  var box_y  = new Array();
  var box_element;
  var best_y = 0;
  
  for (var c in boxes) {
    c = boxes[c];
    box_y[c] = box_id_2_y[c] //+ box_id_2_heights[c];
    if (box_y[c] + box_id_2_heights[c] > best_y) best_y = box_y[c] + box_id_2_heights[c]
  }
  best_y += 0.5 - box_id_2_heights[boxes[0]]
  
  height = document.getElementById(parent_id_2_height_ids[parent][0]);
  var current_height;
  if (height.style.height == "") current_height = 0;
  else                           current_height = parseInt(height.style.height);
  if (update_height && (best_y > current_height)) {
    height.style.height = best_y + "em";
  }
  
  for (var c in boxes) {
    c = boxes[c];
    box_element = document.getElementById(c);
    if (box_element.style.display != "none") {
      box_element.style.top = (-box_y[c]) + "em";
    }
    box_element.style.transition = "top 0.6s";
  }
}

function move_box_encastred(c, ys, box_y, extra) {
  var best_y = 0;
  var cols = box_id_2_cols[c];
  var box_element = document.getElementById(c);
  for (col = cols[0]; col <= cols[cols.length - 1]; col++) {
    if (best_y < ys[col]) best_y = ys[col];
  }
  if (best_y != 0) best_y = best_y + extra;
  box_y[c] = best_y;
  
  box_heights = box_id_2_heights[c];
  if (box_heights == undefined) {
    best_y = best_y + box_element.offsetHeight;
    for (col = cols[0]; col <= cols[cols.length - 1]; col++) ys[col] = best_y;
  }
  else {
    var max_box_extra2_height = 0.0;
    for (col = cols[0]; col <= cols[cols.length - 1]; col++) {
      available_y_space_beneath = box_y[c] - ys[col];
      var box_extra1 = document.getElementById(box_heights[1][col - cols[0]]);
      var box_extra2 = document.getElementById(box_heights[2][col - cols[0]]);
      extra_height = box_extra1.offsetHeight + box_extra2.offsetHeight;
      // For animation, but cause problem with the position of the boxes.
      //box_extra1.style.transition = "height 0.6s";
      //box_extra2.style.transition = "height 0.6s";
      if (extra_height <= available_y_space_beneath) {
        box_extra1.style.height = "0px";
        box_extra2.style.height = extra_height + "px";
        if (extra_height > max_box_extra2_height) max_box_extra2_height = extra_height;
      }
      else {
        box_extra1.style.height = (extra_height - available_y_space_beneath) + "px";
        box_extra2.style.height = available_y_space_beneath + "px";
        if (available_y_space_beneath > max_box_extra2_height) max_box_extra2_height = available_y_space_beneath;
      }
    }
    box_y[c] -= max_box_extra2_height;
    
    var box2_element = document.getElementById(box_heights[0]);
    best_y = best_y + box2_element.offsetHeight;
    for (col = cols[0]; col <= cols[cols.length - 1]; col++) {
      var box_extra1 = document.getElementById(box_heights[1][col - cols[0]]);
      ys[col] = best_y + box_extra1.offsetHeight;
    }
  }
}

function select_comparator(parent_id, col1, col2) {
  if (col2 == col1) {
    document.getElementById(parent_id_2_height_ids[parent_id][0]).style.display = "";
  }
  else {
    document.getElementById(parent_id_2_height_ids[parent_id][0]).style.display = "none";
  }
  for (var i in parent_id_2_div_ids[parent_id]) {
    document.getElementById(parent_id_2_div_ids[parent_id][i]).style.display = "none";
  }
  document.getElementById(parent_id_2_div_ids[parent_id][col2]).style.display = "block";
}

/*
function em2px(px, element) {
  return px * parseFloat(getComputedStyle(element).fontSize);
} */

function on_box_click(parent, c) {
  box_element = document.getElementById(c);
  sel_boxes_id = parent_id_2_sel_box_ids[parent];
  if (sel_boxes_id.includes(c)) {
    sel_boxes_id.splice(sel_boxes_id.indexOf(c), 1);
    change_color(box_element, parent_id_2_sel_box_colors[parent][c], "rgb(230, 230, 230)");
    
    box_heights = box_id_2_heights[c];
    if (box_heights != undefined) {
      var cols = box_id_2_cols[c];
      for (col = cols[0]; col <= cols[cols.length - 1]; col++) {
        var box_extra1 = document.getElementById(box_heights[1][col - cols[0]]);
        var box_extra2 = document.getElementById(box_heights[2][col - cols[0]]);
        if (box_extra2.offsetHeight > 0.0) {
          box_extra1.style.height = (box_extra1.offsetHeight + box_extra2.offsetHeight) + "px";
          box_extra2.style.height = "0px";
        }
      }
    }
  }
  else {
    sel_boxes_id.push(c);
    change_color(box_element, "rgb(230, 230, 230)", parent_id_2_sel_box_colors[parent][c]);
  }
  move_boxes1(parent, false);
}

function change_color(t, oldcolor, newcolor) {
  if ((t.style != undefined) && (t.style.backgroundColor == oldcolor)) t.style.backgroundColor = newcolor;
  for (var i = 0; i < t.children.length; i++) {
    change_color(t.children.item(i), oldcolor, newcolor);
  }
}

sheets = new Array();

function toggle_column(column, active) {
  if (sheets[column] == undefined) {
    sheets[column] = document.createElement('style');
    document.body.appendChild(sheets[column]);
  }
  if (active) {
    sheets[column].innerHTML = ".rainbowbox_box_without_element_" + column + " { opacity: 0.15; }";
  }
  else {
    sheets[column].innerHTML = "";
  }
}

last_popup = null;
function popup_enter(element, event) {
  if ((last_popup != null) && (last_popup != element)) popup_exit(last_popup, event);
  last_popup = element;
  element.lastChild.style.display = "block"
  event.stopPropagation();
}
function popup_exit(element, event) {
  element.lastChild.style.display = "none"
  event.stopPropagation();
}

last_box_popup = null;
function box_popup_enter(element, event) {
  if ((last_box_popup != null) && (last_box_popup != element)) box_popup_exit(last_box_popup, event);
  last_box_popup = element;
  element.firstChild.style.top = element.offsetHeight + 1 + 'px';
  element.firstChild.style.display = 'block';
  element.parentNode.parentNode.style.overflowY = 'visible';
  event.stopPropagation();
}
function box_popup_exit(element, event) {
  element.firstChild.style.display = 'none';
  element.parentNode.parentNode.style.overflowY = 'hidden';
  event.stopPropagation();
}

// Empty but can be overrided by applications
function on_element_enter(this_element_id, event) {
}
function on_element_exit(event) {
}
function on_box_enter(element, event) {
  box_popup_enter(element, event);
}
function on_box_exit(element, event) {
  box_popup_exit(element, event);
}
