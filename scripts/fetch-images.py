#!/usr/bin/env python3
"""
fetch-images.py — Pull a CC-licensed photograph per suburb from Wikimedia
Commons, downsize to 1400px, save to /images/suburbs/<slug>.jpg.

Wikimedia images come in a mix of licenses (mostly CC-BY-SA, some CC0);
use the `--attributions` report this script prints at the end to add
credits in the footer or an /attributions/ page.
"""
import json
import os
import re
import ssl
import subprocess
import sys
import time
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT  = ROOT / 'images' / 'suburbs'
OUT.mkdir(parents=True, exist_ok=True)

UA = {'User-Agent': 'TheOneClub-SiteBuilder/1.0 (https://www.theoneclub.com.au)'}

# Search terms chosen to match real Wikimedia holdings for each suburb.
SEARCHES = {
    'burleigh-heads':   ['Burleigh Heads beach',   'Burleigh Heads Queensland'],
    'surfers-paradise': ['Surfers Paradise Queensland skyline', 'Surfers Paradise beach'],
    'broadbeach':       ['Broadbeach Queensland',  'Broadbeach Gold Coast'],
    'hope-island':      ['Hope Island Queensland', 'Hope Island Gold Coast'],
    'robina':           ['Robina Queensland',      'Robina lake Queensland'],
    'varsity-lakes':    ['Varsity Lakes Queensland','Bond University'],
    'palm-beach':       ['Palm Beach Gold Coast Queensland', 'Palm Beach 4221 Queensland'],
    'mudgeeraba':       ['Mudgeeraba Queensland',  'Gold Coast hinterland'],
    'coolangatta':      ['Coolangatta beach',      'Coolangatta Queensland'],
    'kirra':            ['Kirra Point surf',       'Kirra Beach Queensland'],
    'tugun':            ['Tugun Queensland',       'Tugun beach'],
    'currumbin':        ['Currumbin Beach',        'Currumbin Queensland'],
    'mermaid-beach':    ['Mermaid Beach Queensland','Mermaid Beach Gold Coast'],
    'miami':            ['Miami Gold Coast Queensland', 'Miami 4220 Queensland'],
    'bilinga':          ['Bilinga Queensland',     'Bilinga beach'],
}

API = 'https://commons.wikimedia.org/w/api.php'

def fetch_json(url):
    # Shell out to curl — system Python 3.14's SSL trust store isn't wired
    # up correctly on this box.
    out = subprocess.check_output(
        ['curl', '-s', '-L', '--max-time', '20',
         '-A', UA['User-Agent'], url],
    )
    return json.loads(out.decode())

def search_files(query, limit=15):
    """Return a list of File: titles matching the query, ranked by relevance."""
    params = {
        'action':'query','format':'json','generator':'search',
        'gsrnamespace':'6','gsrlimit':str(limit),'gsrsearch':query,
    }
    url = API + '?' + urllib.parse.urlencode(params)
    data = fetch_json(url)
    pages = data.get('query',{}).get('pages',{})
    # The 'index' field preserves relevance order
    ordered = sorted(pages.values(), key=lambda p: p.get('index', 99))
    return [p['title'] for p in ordered if p.get('title','').startswith('File:')]

def image_info(title, width=1400):
    """Return (direct URL, metadata dict) for a File: title, sized to width."""
    params = {
        'action':'query','format':'json','prop':'imageinfo',
        'iiprop':'url|extmetadata|mime|size',
        'iiurlwidth':str(width),'titles':title,
    }
    url = API + '?' + urllib.parse.urlencode(params)
    data = fetch_json(url)
    pages = data['query']['pages']
    for pid,p in pages.items():
        if pid == '-1': return None,None
        ii = (p.get('imageinfo') or [{}])[0]
        return ii.get('thumburl') or ii.get('url'), ii.get('extmetadata',{})
    return None,None

def download(url, dest):
    subprocess.check_call(
        ['curl', '-s', '-L', '--max-time', '30',
         '-A', UA['User-Agent'], '-o', str(dest), url],
    )

def score_title(t):
    """Heuristic: prefer titles with 'beach', avoid historical photos and
    maps."""
    tl = t.lower()
    if any(b in tl for b in ['1900', '1910', '1920', '1930', '1940', '1950',
                              '1960', '1970', '1980', ' map', '.svg', 'map of',
                              'location map', 'old photo']):
        return -1
    s = 0
    if 'beach' in tl: s += 3
    if 'skyline' in tl: s += 3
    if 'aerial' in tl: s += 2
    if 'looking' in tl: s += 1
    if 'view of' in tl: s += 1
    return s

# Explicit file-title overrides for suburbs where fuzzy search returns
# US/historical false positives.
OVERRIDES = {
    'miami':      'File:Miami Beach, Gold Coast, Queensland seen from Mick Schamburg Park.jpg',
    'palm-beach': 'File:Australian white ibis Palm Beach Gold Coast Queensland IMG 0090.jpg',
}

attributions = []
for slug, queries in SEARCHES.items():
    chosen = OVERRIDES.get(slug)
    if chosen:
        pass
    else:
     for q in queries:
        try:
            titles = search_files(q)
        except Exception as e:
            print(f'  [!] search error "{q}": {e}'); continue
        titles.sort(key=score_title, reverse=True)
        # Filter out obvious non-photographs
        titles = [t for t in titles if not t.lower().endswith(('.svg','.pdf','.webm','.ogv'))]
        if titles:
            chosen = titles[0]
            break
    if not chosen:
        print(f'  [MISS] no image found for {slug}')
        continue
    try:
        url, meta = image_info(chosen)
        if not url:
            print(f'  [MISS] no info for {chosen}')
            continue
        dest = OUT / f'{slug}.jpg'
        download(url, dest)
        size = dest.stat().st_size
        artist = (meta.get('Artist',{}) or {}).get('value','')
        # Strip HTML tags from artist string
        artist_clean = re.sub(r'<[^>]+>','', artist).strip() if artist else '—'
        license_ = (meta.get('LicenseShortName',{}) or {}).get('value','?')
        print(f'  [OK]   {slug:<18} <- {chosen[:70]}  ({size:,} bytes, {license_})')
        attributions.append({
            'slug': slug,
            'source_title': chosen.replace('File:','').replace('.jpg','').replace('.jpeg','').replace('.png','').replace('_',' '),
            'artist': artist_clean[:120],
            'license': license_,
            'url': f'https://commons.wikimedia.org/wiki/{urllib.parse.quote(chosen)}',
        })
        time.sleep(0.4)  # polite delay between Wikimedia calls
    except Exception as e:
        print(f'  [ERR]  {slug}: {e}')

# Write an attributions JSON for use later (footer credit, etc.)
(ROOT / 'images' / 'suburbs' / '_credits.json').write_text(
    json.dumps(attributions, indent=2) + '\n'
)
print(f'\nWrote credits manifest with {len(attributions)} entries.')
