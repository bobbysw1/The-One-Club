#!/usr/bin/env python3
"""
build-seo-pages.py — Generate suburb landing pages and blog pages for SEO.

Reads:  about/index.html (used as the chrome template — smallest MPA page
        with all the shared nav, footer, preloader, chat, admin, scripts).
Writes: <suburb>/index.html for each suburb, /blog/index.html for the blog
        index, /blog/<slug>/index.html for each blog post, and rewrites
        sitemap.xml with the new URLs.

The chrome is taken verbatim from about/index.html. Only the <main> block,
<title>, description meta, and canonical are rewritten per page.
"""
import re
from pathlib import Path
from datetime import date

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / 'about' / 'index.html'
SITE_URL = 'https://www.theoneclub.com.au'
TODAY = date.today().isoformat()

# --------------------------------------------------------------------------
# Suburb data. Median prices are approximate and reflect the Gold Coast
# market in 2026 — edit manually to match your internal estimates.
# --------------------------------------------------------------------------
SUBURBS = [
    {
        'slug':       'burleigh-heads',
        'name':       'Burleigh Heads',
        'median':     2_200_000,
        'blurb':      "Burleigh Heads combines a world-class point break, boutique beachfront dining and a tight-knit coastal village feel. Properties here routinely draw interstate and international buyers, so premium presentation is the difference between one offer and five.",
        'why':        "Burleigh buyers are discerning — they compare every listing on feel, not just price. Our photography, floor plans and optional 3D walkthrough make sure your home reads as premium from the first thumbnail.",
    },
    {
        'slug':       'surfers-paradise',
        'name':       'Surfers Paradise',
        'median':     1_300_000,
        'blurb':      "Surfers Paradise is a fast-moving, high-volume market with strong demand from owner-occupiers, investors and overseas buyers. Apartments and mixed-density homes move on the quality of the listing, not the address alone.",
        'why':        "In a crowded portal like Surfers, the top 5% of listings get the bulk of enquiries. We list every home with enhanced photography, AI staging and a digital campaign that targets active buyers on realestate.com.au and Domain.",
    },
    {
        'slug':       'broadbeach',
        'name':       'Broadbeach',
        'median':     1_800_000,
        'blurb':      "Broadbeach blends beachfront towers, lifestyle dining and easy access to Pacific Fair and the light rail. Stock turns quickly when marketing is strong; listings that look flat tend to sit.",
        'why':        "Broadbeach properties compete on lifestyle, not square metres. We shoot at the right time of day, grade for that golden-hour feel, and position the listing around the walk-everywhere convenience that buyers actually pay for.",
    },
    {
        'slug':       'hope-island',
        'name':       'Hope Island',
        'median':     1_900_000,
        'blurb':      "Hope Island is a premier golf-and-waterways precinct attracting sea-change families, retirees and interstate cash buyers. The suburb rewards listings that showcase lifestyle — the canal, the course, the lock-and-leave resort feel.",
        'why':        "Buyers coming from interstate often inspect remotely first. Our 3D Matterport walkthroughs let them tour every room before flying up — and several recent Hope Island sellers closed deals to buyers who never visited in person.",
    },
    {
        'slug':       'robina',
        'name':       'Robina',
        'median':     1_200_000,
        'blurb':      "Robina is Gold Coast's commuter-belt sweet spot — strong schools, central location, and easy Pacific Motorway access make it one of the most consistently active family-home markets on the coast.",
        'why':        "Robina homes sell on presentation and campaign reach, not guesswork. Traditional agents charge 2%–3% on a typical $1.2M home — that's $24,000–$36,000 in commission. At 1% plus marketing, you keep the difference.",
    },
    {
        'slug':       'varsity-lakes',
        'name':       'Varsity Lakes',
        'median':     1_100_000,
        'blurb':      "Varsity Lakes centres on Bond University and a series of linked lake estates. Owner-occupiers, investors, and academic families drive consistent demand; price-per-square-metre discipline is what separates a quick sale from a long one.",
        'why':        "Varsity buyers cross-shop hard. Our data-informed valuation gives you a realistic launch price with comparable-sales backup — no inflated appraisal that just means a price reduction four weeks later.",
    },
    {
        'slug':       'palm-beach',
        'name':       'Palm Beach',
        'median':     1_900_000,
        'blurb':      "Palm Beach has transformed into one of the coast's fastest-appreciating suburbs — surfable beach, walkable cafe strip, and rapidly improving stock. Well-presented homes consistently attract multiple offers.",
        'why':        "Palm Beach is a premium-presentation market. Our photography, floor plans and virtual styling bring out the coastal feel buyers are chasing — and get you into the top portal positions that drive real enquiries.",
    },
    {
        'slug':       'mudgeeraba',
        'name':       'Mudgeeraba',
        'median':     1_300_000,
        'blurb':      "Mudgeeraba offers hinterland acreage, respected schools and quick motorway access to the coast strip — a lifestyle pitch that families out-of-state increasingly want. Listings benefit from space-and-privacy-focused presentation.",
        'why':        "Acreage properties need wide-angle shots, drone coverage and floor plans that show the land. We include all of that in the 1% commission — no add-on invoices, no renegotiating halfway through the campaign.",
    },
]

# --------------------------------------------------------------------------
# Blog posts. Content kept short and honest — meant as seed content the
# user can expand later without changing structure.
# --------------------------------------------------------------------------
POSTS = [
    {
        'slug':     'cost-to-sell-a-house-gold-coast-2026',
        'title':    "How much does it cost to sell a house on the Gold Coast in 2026?",
        'excerpt':  "A breakdown of commission, marketing, conveyancing and other costs — and why the headline agent fee usually isn't the biggest line item.",
        'date':     '2026-02-14',
        'read_min': 6,
        'body': [
            ("What you actually pay to sell", [
                "Traditional Gold Coast agents typically charge between 2% and 3% commission on the sale price, on top of a separate marketing bill that can run from $4,000 to $15,000 depending on your suburb and chosen portal tier.",
                "On a $1,200,000 home, that's $24,000–$36,000 in commission <em>plus</em> roughly $6,000–$10,000 in marketing costs — so $30,000 to $46,000 before you've paid conveyancing, styling, or moving.",
            ]),
            ("The other costs most sellers forget", [
                "Conveyancing: $1,200–$2,500 depending on complexity.",
                "Styling and minor repairs: $2,000–$8,000 if you want to present at the top end of your price bracket.",
                "Auction fees (if you go that route): usually $500–$1,500 for the auctioneer on the day.",
                "Mortgage discharge and bank fees: $350–$600.",
            ]),
            ("Where The One Club comes in", [
                "We charge 1% commission — and that 1% already includes professional photography, floor plans, full digital marketing, and experienced negotiation. The only additional costs are your REA + Domain portal listing level, and an optional Matterport 3D walkthrough if you want one.",
                "On that same $1,200,000 home: our commission is $12,000. Add say $2,500 in portal costs and you're at $14,500 — a saving of $15,500 to $31,500 over the traditional model, for the same premium campaign.",
            ]),
        ],
    },
    {
        'slug':     'best-suburbs-to-buy-gold-coast-2026',
        'title':    "Best suburbs to buy in Gold Coast 2026",
        'excerpt':  "Where buyers are actually moving this year, broken down by lifestyle, value, and growth potential.",
        'date':     '2026-03-02',
        'read_min': 7,
        'body': [
            ("For lifestyle and long-term hold", [
                "<strong>Palm Beach</strong> has quietly become one of the coast's fastest-appreciating suburbs. The cafe strip, walkable beach access, and new-build stock are pulling buyers that would have gone to Burleigh five years ago.",
                "<strong>Mermaid Beach</strong> remains a stronghold for boutique houses with genuine beach frontage or a short walk to the sand. Low turnover keeps prices firm.",
            ]),
            ("For value on a family budget", [
                "<strong>Robina</strong> and <strong>Varsity Lakes</strong> still offer central locations with strong schools under $1.3M for well-presented 4-bedroom homes.",
                "<strong>Coomera</strong> and the northern growth corridor continue to reward buyers willing to be 15 minutes from the strip but close to new infrastructure.",
            ]),
            ("For the cash-buyer interstate market", [
                "<strong>Hope Island</strong> and the northern waterways precincts continue to attract lock-and-leave retirees and second-home buyers from Sydney and Melbourne. Listings with strong 3D walkthroughs and drone coverage consistently outperform.",
            ]),
        ],
    },
    {
        'slug':     'how-to-prepare-your-home-for-sale',
        'title':    "How to prepare your home for sale on the Gold Coast",
        'excerpt':  "A pragmatic 2-week checklist: what's worth spending on, and what buyers genuinely don't care about.",
        'date':     '2026-03-18',
        'read_min': 5,
        'body': [
            ("Two weeks out", [
                "Declutter surfaces first — benches, mantels, bedside tables. Cleanliness reads as care; clutter reads as compromise.",
                "Fix the five things: dripping taps, squeaky doors, broken light fittings, chipped tiles, peeling paint on high-traffic corners.",
                "Book a professional clean for the day before photography.",
            ]),
            ("Photography week", [
                "Open every blind and curtain. Turn on every light. Soft, abundant light is worth more than a renovation.",
                "Style the primary bedroom and the living room to feel hotel-calm — less is more. Remove personal photos.",
                "Clear the driveway; park cars a street away during the shoot and open-home hours.",
            ]),
            ("Where not to overspend", [
                "Full kitchen renovations almost never recoup their cost at sale. Instead: replace the cabinet handles, paint the walls, and let the photography do the work.",
                "Expensive landscaping pays off at the <em>curb</em>, not the backyard. Focus on the first 10 metres a buyer sees.",
            ]),
        ],
    },
    {
        'slug':     'why-1-percent-commission-doesnt-mean-less-service',
        'title':    "Why 1% commission doesn't mean less service",
        'excerpt':  "The traditional 2–3% agency model was built for a different era. Here's how lower overheads and better tools actually improve the seller experience.",
        'date':     '2026-04-01',
        'read_min': 4,
        'body': [
            ("The fee was set when marketing was manual", [
                "Agency commissions of 2–3% were normalised in a world of newspaper ads, printed brochures, and shopfront window displays. Every listing meant real, manual cost.",
                "Today the campaign lives on realestate.com.au, Domain, and a targeted digital buy. The photography and floor plans can be produced to premium standard at predictable unit cost.",
            ]),
            ("Where our 1% goes", [
                "Professional photography, AI enhancement, floor plans, and an optional 3D walkthrough — all produced by people who do this every week, not outsourced to the cheapest option.",
                "A real agent running the campaign: inspections, enquiries, buyer qualification, negotiation, contract management through to settlement. Nothing outsourced to a call centre.",
            ]),
            ("What we removed", [
                "Shopfront overhead, multiple layers of franchise margin, and the pressure to inflate appraisals to win listings. Those costs were never in the seller's interest.",
            ]),
        ],
    },
]

# --------------------------------------------------------------------------
# Load the chrome template from about/index.html. We split it into:
#   prefix  = everything up to (and including) `<main id="main-content">`
#   footer  = the <footer>…</footer> shared block after the page div
#   suffix  = everything from `</main>` to </html>
# --------------------------------------------------------------------------
src_lines = TEMPLATE.read_text().splitlines(keepends=True)

def line_idx(pred):
    for i, l in enumerate(src_lines):
        if pred(l):
            return i
    raise ValueError('not found')

main_open  = line_idx(lambda l: l.rstrip() == '<main id="main-content">')
about_end  = line_idx(lambda l: l.rstrip() == '</div><!-- end page-about -->')
footer_open  = about_end + 1
while not src_lines[footer_open].lstrip().startswith('<footer>'):
    footer_open += 1
footer_close = footer_open
while not src_lines[footer_close].rstrip().endswith('</footer>'):
    footer_close += 1
main_close = line_idx(lambda l: l.rstrip() == '</main>')

PREFIX = ''.join(src_lines[:main_open + 1])
FOOTER = ''.join(src_lines[footer_open:footer_close + 1])
SUFFIX = ''.join(src_lines[main_close:])

def patch_head(html, title, description, canonical_url, extra_jsonld=None):
    html = re.sub(r'<title>[^<]*</title>',
                  f'<title>{title}</title>', html, count=1)
    html = re.sub(r'<meta name="description" content="[^"]*"\s*/?>',
                  f'<meta name="description" content="{description}"/>',
                  html, count=1)
    html = re.sub(r'<link rel="canonical" href="[^"]*"\s*/?>',
                  f'<link rel="canonical" href="{canonical_url}"/>',
                  html, count=1)
    html = re.sub(r'<meta property="og:url" content="[^"]*"\s*/?>',
                  f'<meta property="og:url" content="{canonical_url}"/>',
                  html, count=1)
    html = re.sub(r'<meta property="og:title" content="[^"]*"\s*/?>',
                  f'<meta property="og:title" content="{title}"/>', html, count=1)
    html = re.sub(r'<meta name="twitter:title" content="[^"]*"\s*/?>',
                  f'<meta name="twitter:title" content="{title}"/>', html, count=1)
    html = re.sub(r'<meta property="og:description" content="[^"]*"\s*/?>',
                  f'<meta property="og:description" content="{description}"/>', html, count=1)
    html = re.sub(r'<meta name="twitter:description" content="[^"]*"\s*/?>',
                  f'<meta name="twitter:description" content="{description}"/>', html, count=1)
    if extra_jsonld:
        html = html.replace(
            '<link rel="preload" href="/style.css" as="style"/>',
            extra_jsonld + '\n<link rel="preload" href="/style.css" as="style"/>',
            1,
        )
    return html

def fmt_dollars(n):
    return f"${n:,}"

def suburb_content(s):
    median = s['median']
    trad_low  = int(median * 0.02)
    trad_high = int(median * 0.03)
    our_fee   = int(median * 0.01)
    save_low  = trad_low  - our_fee
    save_high = trad_high - our_fee

    return f"""<div class="page active">
<section class="hero" style="min-height:unset;padding:140px 24px 60px">
  <div class="hero-glow"></div>
  <div class="hero-grid"></div>
  <div class="hero-label" data-reveal>{s['name']} real estate</div>
  <h1 class="hero-headline" data-reveal style="font-size:clamp(44px,6vw,76px);letter-spacing:-1.5px;max-width:1000px">Real estate agent in<br/><em>{s['name']}</em></h1>
  <p class="hero-sub" data-reveal>{s['blurb']}</p>
  <div class="hero-actions" data-reveal>
    <a class="btn btn-gold btn-lg" href="/#valuation">Get Your Free Valuation</a>
    <a class="btn btn-outline btn-lg" href="/for-sale/">See current listings</a>
  </div>
</section>

<section style="padding:60px 24px 100px;max-width:1100px;margin:0 auto">
  <div data-reveal style="max-width:720px;margin:0 auto 48px;text-align:center">
    <div class="page-label">Why sell with us in {s['name']}</div>
    <div class="display" style="margin-top:18px;font-size:clamp(36px,4.5vw,58px)">1% commission.<br/><em>Keep the difference.</em></div>
    <div class="gold-rule" style="margin:26px auto"></div>
    <p class="body" style="font-size:16px">{s['why']}</p>
  </div>

  <div data-reveal style="background:rgba(var(--fg-rgb),.025);border:1px solid rgba(var(--fg-rgb),.07);border-radius:18px;padding:40px 28px;max-width:720px;margin:0 auto">
    <div style="text-align:center;font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--muted)">Savings on a typical {s['name']} home</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:28px;text-align:center">
      <div>
        <div style="font-size:11px;color:var(--muted);letter-spacing:1.5px;text-transform:uppercase">Traditional (2–3%)</div>
        <div style="font-size:clamp(28px,3.5vw,40px);font-weight:400;color:rgba(255,80,80,.75);letter-spacing:-1px;margin-top:8px">{fmt_dollars(trad_low)} – {fmt_dollars(trad_high)}</div>
      </div>
      <div>
        <div style="font-size:11px;color:var(--muted);letter-spacing:1.5px;text-transform:uppercase">The One Club (1%)</div>
        <div style="font-size:clamp(28px,3.5vw,40px);font-weight:400;color:var(--gold);letter-spacing:-1px;margin-top:8px">{fmt_dollars(our_fee)}</div>
      </div>
    </div>
    <div style="text-align:center;margin-top:24px;padding-top:24px;border-top:1px solid rgba(var(--fg-rgb),.06)">
      <div style="font-size:11px;color:var(--muted);letter-spacing:1.5px;text-transform:uppercase">You save</div>
      <div style="font-size:clamp(34px,4vw,48px);font-weight:400;color:#4ade80;letter-spacing:-1px;margin-top:8px">{fmt_dollars(save_low)} – {fmt_dollars(save_high)}</div>
      <div style="font-size:12px;color:var(--muted);margin-top:6px">Based on an approximate median sale of {fmt_dollars(median)}. Your result will vary with final sale price and chosen portal level.</div>
    </div>
    <div style="text-align:center;margin-top:28px">
      <a class="btn btn-gold btn-lg" href="/#valuation">Get a free valuation for your {s['name']} home</a>
    </div>
  </div>
</section>

<section style="padding:40px 24px 120px;max-width:1100px;margin:0 auto;text-align:center">
  <div data-reveal>
    <div class="page-label">Included with every {s['name']} listing</div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-top:28px;max-width:900px;margin-inline:auto;text-align:left">
      <div style="padding:20px;border:1px solid rgba(var(--fg-rgb),.07);border-radius:12px"><div style="font-weight:600;margin-bottom:6px">Professional photography</div><div style="font-size:13px;color:var(--muted)">Shot at golden hour, AI-enhanced, virtually staged where helpful.</div></div>
      <div style="padding:20px;border:1px solid rgba(var(--fg-rgb),.07);border-radius:12px"><div style="font-weight:600;margin-bottom:6px">Accurate floor plans</div><div style="font-size:13px;color:var(--muted)">Ground floor and level 1 drawn separately; formatted for every portal.</div></div>
      <div style="padding:20px;border:1px solid rgba(var(--fg-rgb),.07);border-radius:12px"><div style="font-weight:600;margin-bottom:6px">Digital marketing campaign</div><div style="font-size:13px;color:var(--muted)">realestate.com.au + Domain + targeted buyer remarketing.</div></div>
      <div style="padding:20px;border:1px solid rgba(var(--fg-rgb),.07);border-radius:12px"><div style="font-weight:600;margin-bottom:6px">Experienced negotiation</div><div style="font-size:13px;color:var(--muted)">From first enquiry through contract signing and to settlement.</div></div>
    </div>
    <div style="margin-top:40px">
      <a class="btn btn-gold btn-lg" href="/#valuation">Request a free {s['name']} valuation</a>
    </div>
  </div>
</section>
</div>
"""

def suburb_jsonld(s):
    return f"""<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"RealEstateAgent","name":"The One Club — {s['name']}","url":"{SITE_URL}/{s['slug']}/","areaServed":{{"@type":"Place","name":"{s['name']}, Gold Coast, QLD"}},"provider":{{"@id":"{SITE_URL}/#business"}},"priceRange":"1% commission"}}
</script>"""

def build_suburb(s):
    canonical = f"{SITE_URL}/{s['slug']}/"
    title     = f"Real Estate Agent in {s['name']} | 1% Commission | The One Club"
    descr     = f"Sell your {s['name']} home with The One Club. 1% commission, premium photography, floor plans, and a full digital campaign — included. Free valuation in 24 hours."
    html = PREFIX + suburb_content(s) + FOOTER + SUFFIX
    html = patch_head(html, title, descr, canonical, extra_jsonld=suburb_jsonld(s))
    return html

# --------------------------------------------------------------------------
# Blog listing page
# --------------------------------------------------------------------------
def blog_card(post):
    return f"""
    <a class="listing-card" href="/blog/{post['slug']}/" style="display:flex;flex-direction:column;gap:14px;padding:28px;border:1px solid rgba(var(--fg-rgb),.08);border-radius:18px;background:rgba(var(--fg-rgb),.02);text-decoration:none;color:inherit;transition:all .3s var(--ease)">
      <div style="font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--gold)">{post['date']} · {post['read_min']} min read</div>
      <div style="font-size:22px;font-weight:500;letter-spacing:-.5px;line-height:1.25;color:var(--fg)">{post['title']}</div>
      <div style="font-size:14px;color:var(--muted);line-height:1.6">{post['excerpt']}</div>
      <div style="margin-top:6px;font-size:13px;font-weight:600;color:var(--gold);letter-spacing:.3px">Read article →</div>
    </a>"""

def build_blog_index():
    cards = ''.join(blog_card(p) for p in POSTS)
    canonical = f"{SITE_URL}/blog/"
    title = "Gold Coast Real Estate Blog | The One Club"
    descr = "Practical guides on selling your Gold Coast home, suburb buying guides and cost breakdowns — written by The One Club."
    jsonld = f"""<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Blog","name":"The One Club Blog","url":"{canonical}","publisher":{{"@id":"{SITE_URL}/#business"}}}}
</script>"""
    content = f"""<div class="page active">
<section class="page-hero" style="padding-bottom:60px">
  <div class="page-label" data-reveal>The One Club Journal</div>
  <h1 class="display" data-reveal style="margin-top:16px;font-size:clamp(48px,6vw,86px);letter-spacing:-2px">Gold Coast<br/><em>real estate, written plainly.</em></h1>
  <div class="gold-rule" data-reveal></div>
  <p class="body" data-reveal style="max-width:580px;font-size:16px">Straightforward guides on commission, cost, presentation and where the Gold Coast market is actually moving in 2026.</p>
</section>

<section style="padding:0 24px 120px;max-width:1100px;margin:0 auto">
  <div data-reveal style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:20px">{cards}
  </div>
</section>
</div>
"""
    html = PREFIX + content + FOOTER + SUFFIX
    html = patch_head(html, title, descr, canonical, extra_jsonld=jsonld)
    return html

# --------------------------------------------------------------------------
# Blog post pages
# --------------------------------------------------------------------------
def build_blog_post(post):
    canonical = f"{SITE_URL}/blog/{post['slug']}/"
    title = f"{post['title']} | The One Club"
    descr = post['excerpt']
    related = [p for p in POSTS if p['slug'] != post['slug']][:3]
    related_cards = ''.join(blog_card(p) for p in related)

    article_jsonld = f"""<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Article","headline":"{post['title']}","description":"{post['excerpt']}","datePublished":"{post['date']}","dateModified":"{post['date']}","author":{{"@type":"Organization","name":"The One Club","url":"{SITE_URL}"}},"publisher":{{"@id":"{SITE_URL}/#business"}},"mainEntityOfPage":{{"@type":"WebPage","@id":"{canonical}"}}}}
</script>"""

    body_sections = ''
    for heading, paragraphs in post['body']:
        paras_html = ''.join(
            f'<li style="margin-bottom:10px;line-height:1.65">{p}</li>' if p.startswith('<strong>') or '•' in p or len(p) < 140 else ''
            for p in paragraphs
        )
        # Decide between <ul> and <p> based on whether all paragraphs look list-shaped
        looks_listy = all(len(p) < 220 and (p.startswith('<strong>') or p.endswith('.')) for p in paragraphs) and len(paragraphs) > 1 and paragraphs[0].count('.') <= 2
        if looks_listy and any(p.startswith('<strong>') for p in paragraphs):
            items = ''.join(f'<li style="margin-bottom:10px;line-height:1.65">{p}</li>' for p in paragraphs)
            body_sections += f"""
    <h2 style="font-size:clamp(22px,3vw,30px);font-weight:500;letter-spacing:-.5px;margin-top:48px;margin-bottom:18px">{heading}</h2>
    <ul style="padding-left:22px;color:rgba(var(--fg-rgb),.82);font-size:16px">{items}</ul>"""
        else:
            ps = ''.join(f'<p style="margin-bottom:16px;line-height:1.75;color:rgba(var(--fg-rgb),.82);font-size:16px">{p}</p>' for p in paragraphs)
            body_sections += f"""
    <h2 style="font-size:clamp(22px,3vw,30px);font-weight:500;letter-spacing:-.5px;margin-top:48px;margin-bottom:18px">{heading}</h2>
    {ps}"""

    content = f"""<div class="page active">
<article style="max-width:760px;margin:0 auto;padding:140px 24px 80px">
  <nav aria-label="Breadcrumb" style="font-size:12px;color:var(--muted);margin-bottom:32px"><a href="/" style="color:inherit">Home</a> · <a href="/blog/" style="color:inherit">Blog</a> · <span style="color:var(--fg)">{post['date']}</span></nav>
  <div class="page-label" style="color:var(--gold)" data-reveal>The One Club Journal · {post['read_min']} min read</div>
  <h1 class="display" data-reveal style="margin-top:18px;font-size:clamp(36px,5vw,60px);letter-spacing:-1.2px;line-height:1.1">{post['title']}</h1>
  <div class="gold-rule" data-reveal></div>
  <div data-reveal style="font-size:13px;color:var(--muted)">By <strong style="color:var(--fg);font-weight:500">The One Club</strong> · Published {post['date']}</div>
  <div style="margin-top:40px">{body_sections}</div>

  <aside style="margin-top:64px;padding:28px;border:1px solid rgba(196,168,74,.2);border-radius:16px;background:rgba(196,168,74,.04)">
    <div style="font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--gold)">Ready to sell?</div>
    <div style="margin-top:10px;font-size:18px;line-height:1.5">Request a free appraisal. Clear price range, recommended strategy, full 1% fee breakdown — within 24 hours.</div>
    <div style="margin-top:18px"><a class="btn btn-gold btn-lg" href="/#valuation">Get your free valuation</a></div>
  </aside>
</article>

<section style="max-width:1100px;margin:60px auto;padding:0 24px 120px;border-top:1px solid var(--subtle);padding-top:60px">
  <div class="page-label" data-reveal>More from the journal</div>
  <div data-reveal style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:16px;margin-top:24px">{related_cards}
  </div>
</section>
</div>
"""
    html = PREFIX + content + FOOTER + SUFFIX
    html = patch_head(html, title, descr, canonical, extra_jsonld=article_jsonld)
    return html

# --------------------------------------------------------------------------
# Write outputs
# --------------------------------------------------------------------------
for s in SUBURBS:
    out = ROOT / s['slug'] / 'index.html'
    out.parent.mkdir(exist_ok=True)
    out.write_text(build_suburb(s))
    print(f"  wrote {out.relative_to(ROOT)}")

blog_dir = ROOT / 'blog'
blog_dir.mkdir(exist_ok=True)
(blog_dir / 'index.html').write_text(build_blog_index())
print(f"  wrote blog/index.html")
for p in POSTS:
    out = blog_dir / p['slug'] / 'index.html'
    out.parent.mkdir(exist_ok=True)
    out.write_text(build_blog_post(p))
    print(f"  wrote blog/{p['slug']}/index.html")

# --------------------------------------------------------------------------
# Rewrite sitemap.xml with new suburb + blog URLs
# --------------------------------------------------------------------------
sitemap_path = ROOT / 'sitemap.xml'
sitemap_entries = [
    ('/',                    '1.0', 'weekly'),
    ('/for-sale/',           '0.9', 'daily'),
    ('/how-it-works/',       '0.8', 'monthly'),
    ('/about/',              '0.7', 'monthly'),
    ('/rentals/',            '0.5', 'monthly'),
    ('/blog/',               '0.7', 'weekly'),
]
for s in SUBURBS:
    sitemap_entries.append((f'/{s["slug"]}/', '0.7', 'monthly'))
for p in POSTS:
    sitemap_entries.append((f'/blog/{p["slug"]}/', '0.6', 'monthly'))

parts = ['<?xml version="1.0" encoding="UTF-8"?>',
         '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
for path, pri, freq in sitemap_entries:
    parts.append(f'''
  <url>
    <loc>{SITE_URL}{path}</loc>
    <lastmod>{TODAY}</lastmod>
    <changefreq>{freq}</changefreq>
    <priority>{pri}</priority>
  </url>''')
parts.append('\n</urlset>\n')
sitemap_path.write_text(''.join(parts))
print(f"  wrote sitemap.xml ({len(sitemap_entries)} URLs)")

print("done.")
