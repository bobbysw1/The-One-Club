import re
import os

def main():
    root = '/Users/robertsugarman-warner/Downloads/The-One-Club-clone'
    for f in ['index.html', 'cairns/index.html']:
        filepath = os.path.join(root, f)
        if os.path.exists(filepath):
            with open(filepath, 'r') as file:
                content = file.read()
            
            # We add a generic smooth animate function if it's not there
            if 'function animateNum' not in content:
                new_js = """
// Smooth number animation
var _animReqs = {};
function animateNum(el, target, duration) {
  if (!el) return;
  var id = el.id;
  if (_animReqs[id]) cancelAnimationFrame(_animReqs[id]);
  var startStr = el.textContent.replace(/[^0-9.-]+/g,"");
  var start = parseFloat(startStr) || 0;
  var startTime = null;
  function step(timestamp) {
    if (!startTime) startTime = timestamp;
    var progress = Math.min((timestamp - startTime) / duration, 1);
    var current = start + (target - start) * (1 - Math.pow(1 - progress, 3)); // ease-out cubic
    el.textContent = '$' + Math.round(current).toLocaleString('en-AU');
    if (progress < 1) {
      _animReqs[id] = requestAnimationFrame(step);
    }
  }
  _animReqs[id] = requestAnimationFrame(step);
}
"""
                content = content.replace("function calcUpdate(input){", new_js + "\nfunction calcUpdate(input){")
                
                # Replace the simple assignments
                content = content.replace("var pEl = document.getElementById('priceVal'); if (pEl) pEl.textContent = fmtCurrency(v);", "var pEl = document.getElementById('priceVal'); if (pEl) animateNum(pEl, v, 250);")
                content = content.replace("var tEl = document.getElementById('tradVal'); if (tEl) tEl.textContent = fmtCurrency(trad);", "var tEl = document.getElementById('tradVal'); if (tEl) animateNum(tEl, trad, 250);")
                content = content.replace("var oEl = document.getElementById('ourVal');  if (oEl) oEl.textContent = fmtCurrency(ours);", "var oEl = document.getElementById('ourVal'); if (oEl) animateNum(oEl, ours, 250);")
                content = content.replace("var sEl = document.getElementById('saveVal'); if (sEl) sEl.textContent = fmtCurrency(save);", "var sEl = document.getElementById('saveVal'); if (sEl) animateNum(sEl, save, 250);")

                with open(filepath, 'w') as file:
                    file.write(content)
                print("Injected smooth animation in", f)

if __name__ == "__main__":
    main()
