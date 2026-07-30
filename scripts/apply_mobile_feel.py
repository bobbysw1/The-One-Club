import os
import re

CSS_APPEND = """
/* ── PREMIUM MOBILE OVERHAUL ── */
.btn:active, .sub-card:active, .guide-card:active, .listing-card:active {
  transform: scale(0.97) !important;
  transition: transform 0.1s cubic-bezier(0.22, 1, 0.36, 1) !important;
}

@media(max-width: 768px) {
  .sub-card, .guide-card {
    width: clamp(270px, 82vw, 340px) !important;
    min-width: 270px !important;
  }
}

.gold-border {
  position: relative;
}
.gold-border::after {
  content: '';
  position: absolute;
  inset: 0;
  border-radius: inherit;
  padding: 1px;
  background: linear-gradient(135deg, rgba(196,168,74,0.4), transparent 60%, rgba(196,168,74,0.1));
  -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0);
  -webkit-mask-composite: xor;
  mask-composite: exclude;
  pointer-events: none;
}
"""

MOBILE_CTA_HTML = """
  <!-- MOBILE CTA BAR -->
  <div class="mobile-cta-bar">
    <div class="row">
      <a href="tel:+61404774272" class="tel" aria-label="Call Bobby" onclick="if(window.trackAction) trackAction('mobile_dock_call')">
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 16.92v3a2 2 0 0 1-2.18 2 19.79 19.79 0 0 1-8.63-3.07 19.5 19.5 0 0 1-6-6 19.79 19.79 0 0 1-3.07-8.67A2 2 0 0 1 4.11 2h3a2 2 0 0 1 2 1.72 12.84 12.84 0 0 0 .7 2.81 2 2 0 0 1-.45 2.11L8.09 9.91a16 16 0 0 0 6 6l1.27-1.27a2 2 0 0 1 2.11-.45 12.84 12.84 0 0 0 2.81.7A2 2 0 0 1 22 16.92z"></path></svg>
      </a>
      <a href="/#valuation" class="btn btn-outline" style="background:var(--surface-1);border-color:rgba(var(--fg-rgb),.12)" onclick="if(window.trackAction) trackAction('mobile_dock_val')">1% Valuation</a>
      <button class="btn btn-gold" onclick="if(window.chatApp && chatApp.toggle) chatApp.toggle(); else document.getElementById('chat-bubble').click(); if(window.trackAction) trackAction('mobile_dock_chat')" style="border:none">Ask AI</button>
    </div>
  </div>
"""

def main():
    root = '/Users/robertsugarman-warner/Downloads/The-One-Club-clone'
    
    # 1. Update style.css
    style_path = os.path.join(root, 'style.css')
    with open(style_path, 'r', encoding='utf-8') as f:
        style_content = f.read()
    if 'PREMIUM MOBILE OVERHAUL' not in style_content:
        with open(style_path, 'a', encoding='utf-8') as f:
            f.write(CSS_APPEND)
        print("Updated style.css")
    
    # 2. Inject Mobile CTA HTML
    for dirpath, dirnames, filenames in os.walk(root):
        if '.git' in dirpath or 'agents' in dirpath or 'scripts' in dirpath or 'images' in dirpath:
            continue
        
        for file in filenames:
            if file.endswith('.html'):
                filepath = os.path.join(dirpath, file)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if '<div class="mobile-cta-bar">' not in content:
                    content = re.sub(r'(</body>)', lambda m: f"{MOBILE_CTA_HTML}\n{m.group(1)}", content, flags=re.IGNORECASE)
                    
                    with open(filepath, 'w', encoding='utf-8') as f:
                        f.write(content)
                    print(f"Injected CTA into {filepath}")

if __name__ == '__main__':
    main()
