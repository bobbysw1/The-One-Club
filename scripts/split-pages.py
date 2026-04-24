#!/usr/bin/env python3
"""
split-pages.py — Split the legacy SPA index.html into 5 real HTML files,
one per URL, so each route serves page-specific HTML with exactly one <h1>.

Reads:  index.html (SPA build with <div id="page-X"> blocks for all 5 pages)
Writes: index.html (home only), for-sale/index.html, how-it-works/index.html,
        about/index.html, rentals/index.html

Each output:
  - Same <head>/<nav>/<main>/chat/admin/scripts chrome
  - A single page's content inside <main>
  - A single shared footer (from the home-page version, fullest content)
  - Unique <title>, <meta name="description">, <link rel="canonical">
  - SPA helpers (goTo) kept but simplified to cross-URL navigation
"""
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SRC  = ROOT / 'index.html'

SITE_URL = 'https://www.theoneclub.com.au'

# Per-page metadata. Each "path" maps the URL path that goTo() should navigate
# to; used both for the canonical tag and for rewriting goTo() at the bottom.
PAGES = {
    'home': {
        'slug': '',          # writes to /index.html
        'current_page': 'home',
        'path': '/',
        'title': 'The One Club — 1% Commission. Gold Coast Real Estate.',
        'description': "The One Club helps Gold Coast homeowners sell smarter. 1% commission + marketing, premium presentation, and experienced guidance from appraisal to settlement. No bloated agency overhead.",
    },
    'for-sale': {
        'slug': 'for-sale',
        'current_page': 'for-sale',
        'path': '/for-sale/',
        'title': 'Properties For Sale — Gold Coast | The One Club',
        'description': 'Browse current Gold Coast properties listed for sale with The One Club. Professional photography, floor plans, 3D walkthroughs, and 1% commission selling.',
    },
    'how-it-works': {
        'slug': 'how-it-works',
        'current_page': 'how-it-works',
        'path': '/how-it-works/',
        'title': 'How It Works — Selling for 1% Commission | The One Club',
        'description': 'See exactly how The One Club sells your Gold Coast home for 1% commission plus marketing — from appraisal and photography through negotiation to settlement.',
    },
    'about': {
        'slug': 'about',
        'current_page': 'about',
        'path': '/about/',
        'title': 'About The One Club — Gold Coast Real Estate',
        'description': 'Why The One Club exists: a transparent, technology-first Gold Coast real estate agency built to let sellers keep more of their own money.',
    },
    'rentals': {
        'slug': 'rentals',
        'current_page': 'to-rent',
        'path': '/rentals/',
        'title': 'Rentals — Coming Soon | The One Club',
        'description': "The One Club rental management launches soon: 8% management, 1-week letting fee, all-in-one app for landlords and tenants. Register your interest for priority access.",
    },
}

# -- Read source ---------------------------------------------------------------
lines = SRC.read_text().splitlines(keepends=True)

def line_index(predicate):
    for i, l in enumerate(lines):
        if predicate(l):
            return i
    raise ValueError('line not found')

main_open_idx   = line_index(lambda l: l.rstrip() == '<main id="main-content">')
main_close_idx  = line_index(lambda l: l.rstrip() == '</main>')

PAGE_BLOCKS = {
    'home':         ('<div id="page-home"',         '</div><!-- end page-home -->'),
    'for-sale':     ('<div id="page-for-sale"',     '</div><!-- end page-for-sale -->'),
    'to-rent':      ('<div id="page-to-rent"',      '</div><!-- end page-to-rent -->'),
    'how-it-works': ('<div id="page-how-it-works"', '</div><!-- end page-how-it-works -->'),
    'about':        ('<div id="page-about"',        '</div><!-- end page-about -->'),
}

def find_range(start_text, end_text):
    start = line_index(lambda l: l.lstrip().startswith(start_text))
    end   = line_index(lambda l: l.rstrip() == end_text)
    return start, end

ranges = {k: find_range(a, b) for k, (a, b) in PAGE_BLOCKS.items()}
for k, (s, e) in ranges.items():
    print(f"  {k}: lines {s+1}..{e+1}")

# Slice pieces of the source into named regions we can reassemble.
prefix_lines = lines[:main_open_idx + 1]      # up through <main>
suffix_lines = lines[main_close_idx:]          # from </main> to end

def extract_page_content(key):
    """Return the inner content of the page div with its internal <footer> stripped."""
    start, end = ranges[key]
    inner = lines[start + 1:end]
    out = []
    in_footer = False
    for l in inner:
        s = l.lstrip()
        if s.startswith('<footer>'):
            in_footer = True
            continue
        if in_footer:
            if l.rstrip().endswith('</footer>'):
                in_footer = False
            continue
        out.append(l)
    return ''.join(out).rstrip() + '\n'

# The canonical shared footer: lift it from the home page (the fullest variant).
# Includes everything from the line starting with <footer> through </footer>.
home_start, home_end = ranges['home']
shared_footer_lines = []
in_f = False
for l in lines[home_start:home_end + 1]:
    if l.lstrip().startswith('<footer>'):
        in_f = True
    if in_f:
        shared_footer_lines.append(l)
    if in_f and l.rstrip().endswith('</footer>'):
        break
SHARED_FOOTER = ''.join(shared_footer_lines).rstrip() + '\n'
if not SHARED_FOOTER.strip().startswith('<footer'):
    raise SystemExit('Failed to extract shared footer from home page')

# -- Per-page rewrites ---------------------------------------------------------
def patch_head(html, meta):
    """Rewrite <title>, description meta, canonical link for one page."""
    html = re.sub(
        r'<title>[^<]*</title>',
        f'<title>{meta["title"]}</title>',
        html, count=1,
    )
    html = re.sub(
        r'<meta name="description" content="[^"]*"\s*/?>',
        f'<meta name="description" content="{meta["description"]}"/>',
        html, count=1,
    )
    html = re.sub(
        r'<link rel="canonical" href="[^"]*"\s*/?>',
        f'<link rel="canonical" href="{SITE_URL}{meta["path"]}"/>',
        html, count=1,
    )
    # og:url and og:title should also match
    html = re.sub(
        r'<meta property="og:url" content="[^"]*"\s*/?>',
        f'<meta property="og:url" content="{SITE_URL}{meta["path"]}"/>',
        html, count=1,
    )
    html = re.sub(
        r'<meta property="og:title" content="[^"]*"\s*/?>',
        f'<meta property="og:title" content="{meta["title"]}"/>',
        html, count=1,
    )
    html = re.sub(
        r'<meta name="twitter:title" content="[^"]*"\s*/?>',
        f'<meta name="twitter:title" content="{meta["title"]}"/>',
        html, count=1,
    )
    return html

def strip_spa_onclicks(html):
    """Nav links on each page already carry the right href="/for-sale/" etc.,
    plus onclick="goTo(...);return false;" that blocks the default nav. The
    onclick is what makes every URL serve the same HTML in the SPA — remove
    it so the browser performs a real page load.
    """
    html = re.sub(
        r' onclick="goTo\(\'([^\']+)\'\);return false;"',
        '', html,
    )
    html = re.sub(
        r' onclick="goTo\(\'([^\']+)\'\);toggleMenu\(\);return false;"',
        ' onclick="toggleMenu()"',
        html,
    )
    # Mobile menu "Home" link: onclick was goTo('home'); just strip it.
    html = re.sub(
        r' onclick="goTo\(\'home\'\);toggleMenu\(\);return false;"',
        ' onclick="toggleMenu()"',
        html,
    )
    return html

def rewrite_goto_js(html, current_page):
    """Simplify the SPA router JS to: set currentPage per file, and make goTo()
    a cross-URL navigator (no DOM swap, no pushState, no popstate). Preserves
    anchor-scroll behaviour inside the current page.
    """
    page_urls_obj = (
        "var pageUrls = {"
        "'home':'/',"
        "'for-sale':'/for-sale/',"
        "'how-it-works':'/how-it-works/',"
        "'about':'/about/',"
        "'to-rent':'/rentals/'"
        "};"
    )
    # The entire legacy SPA router block spans from the GitHub-Pages SPA 404
    # redirect handler down through the popstate listener. Replace it with a
    # compact cross-URL goTo() keyed off the static currentPage for this file.
    new_router = (
        f'var currentPage = "{current_page}";\n'
        f'{page_urls_obj}\n'
        'function goTo(page, anchor) {\n'
        '  if (page === currentPage) {\n'
        '    if (anchor) {\n'
        '      var el = document.getElementById(anchor);\n'
        '      if (el) el.scrollIntoView({behavior:"smooth", block:"start"});\n'
        '    } else { window.scrollTo({top:0, behavior:"smooth"}); }\n'
        '    return;\n'
        '  }\n'
        '  var url = pageUrls[page] || "/";\n'
        '  if (anchor) url += "#" + anchor;\n'
        '  window.location.href = url;\n'
        '}\n'
        'function toggleMenu() { document.getElementById("mobileMenu").classList.toggle("open"); }\n'
    )
    html = re.sub(
        r'var pageUrls = \{[\s\S]*?\};\s*'
        r'// ── GitHub Pages SPA 404 redirect handler ──[\s\S]*?'
        r'window\.addEventListener\(\'popstate\',[\s\S]*?\}\);',
        new_router,
        html, count=1,
    )
    return html

def prune_compare_inits(html, page_key):
    """initCompare() is called for every slider across both home and HIW. On a
    single-page MPA file only that page's IDs exist, so drop the irrelevant
    calls to silence noisy "Element not found" warnings.
    """
    home_ids   = ['cmp1', 'cmp2', 'cmp3', 'cmp4']
    hiw_ids    = ['hiw-cmp1', 'hiw-cmp2', 'hiw-cmp3', 'hiw-cmp4']
    keep = set()
    if page_key == 'home':
        keep = set(home_ids)
    elif page_key == 'how-it-works':
        keep = set(hiw_ids)
    for cid in home_ids + hiw_ids:
        if cid not in keep:
            html = re.sub(
                rf"\n\s*initCompare\('{re.escape(cid)}'\s*,\s*'[^']+'\s*,\s*'[^']+'\)\s*;",
                '', html,
            )
    return html

def assemble(page_key, meta):
    current_page = meta['current_page']
    page_content = extract_page_content(current_page)

    wrapper_open  = f'<div id="page-{current_page}" class="page active">\n'
    wrapper_close = f'</div><!-- end page-{current_page} -->\n'

    body = (
        ''.join(prefix_lines)
        + wrapper_open
        + page_content
        + wrapper_close
        + SHARED_FOOTER
        + ''.join(suffix_lines)
    )

    body = patch_head(body, meta)
    body = strip_spa_onclicks(body)
    body = rewrite_goto_js(body, current_page)
    body = prune_compare_inits(body, page_key)
    return body

# -- Write outputs -------------------------------------------------------------
for key, meta in PAGES.items():
    out_path = (
        ROOT / 'index.html' if key == 'home'
        else ROOT / meta['slug'] / 'index.html'
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    html = assemble(key, meta)
    out_path.write_text(html)
    print(f"  wrote {out_path.relative_to(ROOT)}  ({len(html):,} bytes)")

print("done.")
