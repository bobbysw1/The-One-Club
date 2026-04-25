#!/usr/bin/env python3
"""
build-editorial.py — Build the /calculators/, /auctions/, /mortgage/ pages
and add an OSM-tile map placeholder to each suburb page. All pages use
about/index.html as the chrome template.
"""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / 'about' / 'index.html'
SITE_URL = 'https://www.theoneclub.com.au'
GMAPS_KEY = 'AIzaSyDyWnJ2ud9rWnBqUY96uankmuUnH-gxIRM'  # restricted to theoneclub.com.au + localhost

# Suburb centres (approx lat,lng) for map placeholders
SUBURB_COORDS = {
    'burleigh-heads':   (-28.098, 153.448, 'Burleigh Heads'),
    'surfers-paradise': (-28.002, 153.430, 'Surfers Paradise'),
    'broadbeach':       (-28.030, 153.430, 'Broadbeach'),
    'hope-island':      (-27.879, 153.348, 'Hope Island'),
    'robina':           (-28.084, 153.392, 'Robina'),
    'varsity-lakes':    (-28.090, 153.417, 'Varsity Lakes'),
    'palm-beach':       (-28.118, 153.470, 'Palm Beach'),
    'mudgeeraba':       (-28.078, 153.369, 'Mudgeeraba'),
    'coolangatta':      (-28.170, 153.535, 'Coolangatta'),
    'kirra':            (-28.166, 153.528, 'Kirra'),
    'tugun':            (-28.146, 153.503, 'Tugun'),
    'currumbin':        (-28.135, 153.490, 'Currumbin'),
    'mermaid-beach':    (-28.043, 153.441, 'Mermaid Beach'),
    'miami':            (-28.062, 153.443, 'Miami'),
    'bilinga':          (-28.158, 153.515, 'Bilinga'),
}

# --- Chrome from about page ---
src = TEMPLATE.read_text().splitlines(keepends=True)
def idx(pred):
    for i,l in enumerate(src):
        if pred(l): return i
    raise ValueError('not found')

main_open  = idx(lambda l: l.rstrip() == '<main id="main-content">')
about_end  = idx(lambda l: l.rstrip() == '</div><!-- end page-about -->')
footer_open = about_end + 1
while not src[footer_open].lstrip().startswith('<footer>'): footer_open += 1
footer_close = footer_open
while not src[footer_close].rstrip().endswith('</footer>'): footer_close += 1
main_close = idx(lambda l: l.rstrip() == '</main>')

PREFIX = ''.join(src[:main_open+1])
FOOTER = ''.join(src[footer_open:footer_close+1])
SUFFIX = ''.join(src[main_close:])

def patch_head(html, title, desc, canonical):
    html = re.sub(r'<title>[^<]*</title>', f'<title>{title}</title>', html, count=1)
    html = re.sub(r'<meta name="description" content="[^"]*"\s*/?>', f'<meta name="description" content="{desc}"/>', html, count=1)
    html = re.sub(r'<link rel="canonical" href="[^"]*"\s*/?>', f'<link rel="canonical" href="{canonical}"/>', html, count=1)
    html = re.sub(r'<meta property="og:url" content="[^"]*"\s*/?>', f'<meta property="og:url" content="{canonical}"/>', html, count=1)
    html = re.sub(r'<meta property="og:title" content="[^"]*"\s*/?>', f'<meta property="og:title" content="{title}"/>', html, count=1)
    html = re.sub(r'<meta name="twitter:title" content="[^"]*"\s*/?>', f'<meta name="twitter:title" content="{title}"/>', html, count=1)
    return html

def wrap(content, page_id='page-generic'):
    return f'<div id="{page_id}" class="page active">\n{content}\n</div>'

def build(content, title, desc, canonical, page_id):
    html = PREFIX + wrap(content, page_id) + FOOTER + SUFFIX
    return patch_head(html, title, desc, canonical)

# -------- /calculators/ --------
CALC_BODY = '''
<section class="sec" style="padding-top:140px;padding-bottom:40px">
  <div class="page-label" data-reveal>Calculators</div>
  <h1 class="serif" data-reveal style="font-size:clamp(44px,6vw,80px);letter-spacing:-2px;margin:16px 0 16px">Run the numbers.<br/><em>Decide with clarity.</em></h1>
  <p class="body" data-reveal style="font-size:16px;max-width:620px">Three straightforward tools built for the Queensland market — monthly repayments, transfer duty, and an honest borrowing-power estimate. No logins, no sales pitch.</p>
</section>

<section class="sec" style="padding-top:20px;padding-bottom:100px">
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:24px">
    <!-- Mortgage repayment -->
    <div class="calc-card" data-reveal>
      <div class="page-label">Mortgage repayments</div>
      <h2 class="serif" style="font-size:26px;margin-top:10px;margin-bottom:18px;letter-spacing:-.5px">What will this loan cost<br/><em>per month?</em></h2>
      <div class="calc-field"><label for="m-amount">Loan amount</label><input id="m-amount" type="number" value="800000" min="50000" step="10000"/></div>
      <div class="calc-field"><label for="m-rate">Interest rate (% p.a.)</label><input id="m-rate" type="number" value="6.2" min="0" step="0.01"/></div>
      <div class="calc-field"><label for="m-term">Loan term (years)</label><input id="m-term" type="number" value="30" min="1" max="40" step="1"/></div>
      <div class="calc-output">
        <div class="calc-out-row"><span class="calc-out-label">Monthly repayment</span><span class="calc-out-value big" id="m-monthly">—</span></div>
        <div class="calc-out-row"><span class="calc-out-label">Total interest over life of loan</span><span class="calc-out-value" id="m-interest">—</span></div>
        <div class="calc-out-row"><span class="calc-out-label">Total cost</span><span class="calc-out-value" id="m-total">—</span></div>
      </div>
    </div>
    <!-- QLD transfer duty -->
    <div class="calc-card" data-reveal>
      <div class="page-label">QLD transfer duty</div>
      <h2 class="serif" style="font-size:26px;margin-top:10px;margin-bottom:18px;letter-spacing:-.5px">How much "stamp<br/><em>duty" will I pay?</em></h2>
      <div class="calc-field"><label for="s-price">Purchase price</label><input id="s-price" type="number" value="900000" min="1000" step="5000"/></div>
      <div class="calc-field"><label for="s-type">Buyer type</label>
        <select id="s-type">
          <option value="investor">Investor / standard rate</option>
          <option value="home" selected>Principal residence (home concession)</option>
          <option value="first">First home buyer</option>
        </select>
      </div>
      <div class="calc-output">
        <div class="calc-out-row"><span class="calc-out-label">Transfer duty payable</span><span class="calc-out-value big" id="s-duty">—</span></div>
        <div class="calc-out-row"><span class="calc-out-label">Effective rate</span><span class="calc-out-value" id="s-rate">—</span></div>
        <div style="font-size:11px;color:var(--muted);margin-top:10px;line-height:1.65">Estimate only, based on published Queensland rates. Confirm with Queensland Revenue Office or a licensed conveyancer before relying on this number.</div>
      </div>
    </div>
    <!-- Borrowing power -->
    <div class="calc-card" data-reveal>
      <div class="page-label">Borrowing power</div>
      <h2 class="serif" style="font-size:26px;margin-top:10px;margin-bottom:18px;letter-spacing:-.5px">How much could<br/><em>I borrow?</em></h2>
      <div class="calc-field"><label for="b-income">Combined gross annual income ($)</label><input id="b-income" type="number" value="150000" min="30000" step="5000"/></div>
      <div class="calc-field"><label for="b-expenses">Monthly living expenses ($)</label><input id="b-expenses" type="number" value="3500" min="500" step="100"/></div>
      <div class="calc-field"><label for="b-liabilities">Existing monthly debt repayments ($)</label><input id="b-liabilities" type="number" value="500" min="0" step="50"/></div>
      <div class="calc-field"><label for="b-rate">Assessment rate (% p.a.)</label><input id="b-rate" type="number" value="8.2" min="0" step="0.1"/></div>
      <div class="calc-output">
        <div class="calc-out-row"><span class="calc-out-label">Estimated borrowing capacity</span><span class="calc-out-value big" id="b-capacity">—</span></div>
        <div class="calc-out-row"><span class="calc-out-label">Max monthly repayment</span><span class="calc-out-value" id="b-max-repay">—</span></div>
        <div style="font-size:11px;color:var(--muted);margin-top:10px;line-height:1.65">Rough guide only. Lenders add buffers, factor in dependants, credit history, and loan type. Talk to a licensed broker for a formal assessment.</div>
      </div>
    </div>
  </div>
</section>

<section class="sec" style="padding-top:40px;padding-bottom:120px;text-align:center">
  <div style="max-width:640px;margin:0 auto;padding:36px 32px;border:1px solid rgba(196,168,74,.2);border-radius:14px;background:rgba(196,168,74,.04)">
    <div class="page-label">Next step</div>
    <h2 class="serif" style="font-size:30px;margin-top:14px;margin-bottom:14px;letter-spacing:-.6px">Numbers looking good?</h2>
    <p class="body" style="margin:0 auto 26px;font-size:15px">Get a free appraisal on your property — realistic price range, recommended strategy, clear 1% fee breakdown.</p>
    <a class="btn btn-gold btn-lg" href="/#valuation">Request a free valuation</a>
  </div>
</section>

<script>
(function(){
  function fmt(n){ return '$' + Math.round(n).toLocaleString('en-AU'); }
  function fmtP(n){ return n.toFixed(2) + '%'; }

  // Mortgage repayment
  function updMortgage(){
    var P = +document.getElementById('m-amount').value || 0;
    var r = (+document.getElementById('m-rate').value || 0) / 100 / 12;
    var n = (+document.getElementById('m-term').value || 0) * 12;
    if (!P || !n) return;
    var m = r === 0 ? P / n : P * (r * Math.pow(1+r,n)) / (Math.pow(1+r,n) - 1);
    var total = m * n;
    document.getElementById('m-monthly').textContent = fmt(m);
    document.getElementById('m-interest').textContent = fmt(total - P);
    document.getElementById('m-total').textContent = fmt(total);
  }

  // QLD transfer duty — 2024/25 published rates.
  // Standard rates (investor / absentee):
  //   $0–$5,000: Nil
  //   $5,001–$75,000: $1.50 per $100 over $5,000
  //   $75,001–$540,000: $1,050 + $3.50 per $100 over $75,000
  //   $540,001–$1,000,000: $17,325 + $4.50 per $100 over $540,000
  //   $1,000,001+: $38,025 + $5.75 per $100 over $1,000,000
  // Home concession (principal place of residence):
  //   $0–$350,000: $1.00 per $100
  //   $350,001–$540,000: $3,500 + $3.50 per $100 over $350,000
  //   $540,001+: as standard
  // First home concession (FY2024-25): exempt up to $700k, phased to $800k.
  function standardDuty(p){
    if (p <= 5000) return 0;
    if (p <= 75000) return (p - 5000) * 0.015;
    if (p <= 540000) return 1050 + (p - 75000) * 0.035;
    if (p <= 1000000) return 17325 + (p - 540000) * 0.045;
    return 38025 + (p - 1000000) * 0.0575;
  }
  function homeDuty(p){
    if (p <= 350000) return p * 0.01;
    if (p <= 540000) return 3500 + (p - 350000) * 0.035;
    return standardDuty(p); // tapers to the standard schedule above $540k
  }
  function firstHomeDuty(p){
    if (p <= 700000) return 0;
    if (p >= 800000) return homeDuty(p);
    var full = homeDuty(p);
    var pctRemoved = (800000 - p) / 100000;
    return full * (1 - pctRemoved);
  }
  function updStamp(){
    var p = +document.getElementById('s-price').value || 0;
    var t = document.getElementById('s-type').value;
    var d = t === 'home' ? homeDuty(p) : t === 'first' ? firstHomeDuty(p) : standardDuty(p);
    document.getElementById('s-duty').textContent = fmt(d);
    document.getElementById('s-rate').textContent = p > 0 ? fmtP(d / p * 100) : '—';
  }

  // Borrowing power — simplified. Net monthly surplus -> reverse-amortisation.
  function updBorrow(){
    var income   = +document.getElementById('b-income').value || 0;
    var expenses = +document.getElementById('b-expenses').value || 0;
    var liab     = +document.getElementById('b-liabilities').value || 0;
    var rate     = (+document.getElementById('b-rate').value || 0) / 100 / 12;
    // Crude take-home estimate: 30% tax drag over $18,200, 45% over $135k
    var gross = income / 12;
    var tax;
    if (income <= 18200) tax = 0;
    else if (income <= 45000) tax = (income - 18200) * 0.16;
    else if (income <= 135000) tax = (45000 - 18200) * 0.16 + (income - 45000) * 0.30;
    else if (income <= 190000) tax = (45000 - 18200) * 0.16 + (135000 - 45000) * 0.30 + (income - 135000) * 0.37;
    else tax = (45000 - 18200) * 0.16 + (135000 - 45000) * 0.30 + (190000 - 135000) * 0.37 + (income - 190000) * 0.45;
    var netMonthly = (income - tax) / 12;
    var surplus = Math.max(0, netMonthly - expenses - liab);
    var maxRepay = surplus * 0.9; // lender buffer
    var n = 30 * 12;
    var capacity = rate === 0 ? maxRepay * n : maxRepay * (1 - Math.pow(1+rate, -n)) / rate;
    document.getElementById('b-max-repay').textContent = fmt(maxRepay);
    document.getElementById('b-capacity').textContent = fmt(capacity);
  }

  function hook(ids, fn){ ids.forEach(function(id){ var el=document.getElementById(id); if(el) el.addEventListener('input', fn); }); fn(); }
  hook(['m-amount','m-rate','m-term'], updMortgage);
  hook(['s-price','s-type'], updStamp);
  hook(['b-income','b-expenses','b-liabilities','b-rate'], updBorrow);
})();
</script>
'''

(ROOT / 'calculators').mkdir(exist_ok=True)
(ROOT / 'calculators' / 'index.html').write_text(build(
    CALC_BODY,
    'Property & Mortgage Calculators | The One Club',
    'Free Queensland property calculators — mortgage repayments, transfer (stamp) duty, and borrowing-power estimate. No logins, no catch.',
    f'{SITE_URL}/calculators/',
    'page-calculators',
))
print('wrote calculators/index.html')

# -------- /auctions/ --------
AUCT_BODY = '''
<section class="sec" style="padding-top:140px;padding-bottom:20px">
  <div class="page-label" data-reveal>Auctions</div>
  <h1 class="serif" data-reveal style="font-size:clamp(44px,6vw,80px);letter-spacing:-2px;margin:16px 0 16px">Transparent bidding.<br/><em>Clear outcomes.</em></h1>
  <p class="body" data-reveal style="font-size:16px;max-width:620px">An auction doesn't suit every property — but when it does, it is the most competitive, time-bound way to surface the strongest buyer. Our auctions are run by independent auctioneers, marketed the same premium way our private-treaty listings are, and sit inside the same 1% commission.</p>
</section>

<section class="sec" style="padding-top:20px;padding-bottom:60px">
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px" data-reveal>
    <div style="padding:28px 26px;border:1px solid rgba(var(--fg-rgb),.08);border-radius:12px"><div class="page-label">01</div><h3 class="serif" style="font-size:22px;margin:10px 0 10px;letter-spacing:-.4px">Does auction suit you?</h3><p style="font-size:14px;line-height:1.7;color:var(--muted)">Unique homes, waterfront, hinterland acreage, luxury beachfront — anywhere buyer-value is genuinely subjective — do well at auction. Cookie-cutter stock usually does not.</p></div>
    <div style="padding:28px 26px;border:1px solid rgba(var(--fg-rgb),.08);border-radius:12px"><div class="page-label">02</div><h3 class="serif" style="font-size:22px;margin:10px 0 10px;letter-spacing:-.4px">Four-week campaign</h3><p style="font-size:14px;line-height:1.7;color:var(--muted)">Three weekends of open homes, weekly digital and portal buyer updates, a Saturday on-site or in-rooms auction. Registered bidders only.</p></div>
    <div style="padding:28px 26px;border:1px solid rgba(var(--fg-rgb),.08);border-radius:12px"><div class="page-label">03</div><h3 class="serif" style="font-size:22px;margin:10px 0 10px;letter-spacing:-.4px">Included in 1%</h3><p style="font-size:14px;line-height:1.7;color:var(--muted)">Auctioneer fee, photography, floor plans, campaign ads and contract management sit inside the usual 1% commission. No surprise auctioneer invoices.</p></div>
  </div>
</section>

<section class="sec" style="padding-top:40px;padding-bottom:60px">
  <div class="sec-head">
    <div class="sec-head-l">
      <div class="page-label">Upcoming auctions</div>
      <h2 class="serif">Saturday sales<br/><em>to watch.</em></h2>
      <p class="body">Our auction calendar will go live here as campaigns open. Register below and we will email you the auction book each Monday.</p>
    </div>
  </div>
  <div style="padding:48px 32px;border:1px dashed rgba(var(--fg-rgb),.14);border-radius:12px;text-align:center;color:var(--muted)">
    <div style="font-family:'Fraunces',Georgia,serif;font-size:22px;color:var(--fg);letter-spacing:-.4px">No auctions scheduled right now.</div>
    <div style="margin-top:8px;font-size:14px">Register interest and we will be in touch as soon as the next campaign opens.</div>
    <div style="margin-top:24px"><a class="btn btn-gold" href="/#valuation">Register interest</a></div>
  </div>
</section>

<section class="sec" style="padding-top:40px;padding-bottom:120px;text-align:center">
  <div style="max-width:640px;margin:0 auto;padding:36px 32px;border:1px solid rgba(196,168,74,.2);border-radius:14px;background:rgba(196,168,74,.04)">
    <div class="page-label">Thinking of auctioning?</div>
    <h2 class="serif" style="font-size:30px;margin-top:14px;margin-bottom:14px;letter-spacing:-.6px">Ask us honestly whether it's right for your home.</h2>
    <p class="body" style="margin:0 auto 26px;font-size:15px">Not every property should go to auction. We will tell you straight, and recommend private treaty if that is what will actually serve you best.</p>
    <a class="btn btn-gold btn-lg" href="/#valuation">Request a free valuation</a>
  </div>
</section>
'''
(ROOT / 'auctions').mkdir(exist_ok=True)
(ROOT / 'auctions' / 'index.html').write_text(build(
    AUCT_BODY,
    'Gold Coast Property Auctions | The One Club',
    'Transparent, campaign-style property auctions run across the Gold Coast — auctioneer fee included in the 1% commission. Registered bidders only.',
    f'{SITE_URL}/auctions/',
    'page-auctions',
))
print('wrote auctions/index.html')

# -------- /mortgage/ --------
MORT_BODY = '''
<section class="sec" style="padding-top:140px;padding-bottom:20px">
  <div class="page-label" data-reveal>Mortgage advice</div>
  <h1 class="serif" data-reveal style="font-size:clamp(44px,6vw,80px);letter-spacing:-2px;margin:16px 0 16px">Borrow with<br/><em>your eyes open.</em></h1>
  <p class="body" data-reveal style="font-size:16px;max-width:620px">Straightforward home-loan guidance for Gold Coast buyers and sellers — what to ask, what to compare, and where independent brokers add real value over a single bank.</p>
</section>

<section class="sec" style="padding-top:20px;padding-bottom:80px">
  <div style="max-width:720px;margin:0 auto">
    <h2 class="serif" style="font-size:32px;letter-spacing:-.6px;margin-bottom:20px">The questions worth asking before you borrow</h2>
    <p style="font-size:17px;line-height:1.75;color:rgba(var(--fg-rgb),.82);margin-bottom:14px">Most borrowers fixate on the headline rate. Rate matters, but the real cost of a loan over 25–30 years comes out of four other levers you can pull before you sign.</p>
    <ul style="font-size:17px;line-height:1.75;color:rgba(var(--fg-rgb),.82);margin:10px 0 26px 22px">
      <li style="margin-bottom:10px"><strong>Comparison rate, not headline rate.</strong> The AAPR / comparison rate rolls in fees and blended product costs, and is a much better apples-to-apples number.</li>
      <li style="margin-bottom:10px"><strong>Offset account with 100% linkage.</strong> A fully offset savings buffer can shave years off a loan at no cost versus a pure redraw facility.</li>
      <li style="margin-bottom:10px"><strong>Fixed-vs-variable, and how much.</strong> Fixing for certainty is fine, but watch break fees and whether the fixed portion allows extra repayments.</li>
      <li style="margin-bottom:10px"><strong>LMI threshold.</strong> Getting to 20% deposit (or using a family guarantor / government scheme) usually saves more than any rate negotiation could.</li>
    </ul>
    <h2 class="serif" style="font-size:28px;letter-spacing:-.5px;margin:34px 0 14px">Bank or broker?</h2>
    <p style="font-size:17px;line-height:1.75;color:rgba(var(--fg-rgb),.82);margin-bottom:14px">Your bank can only offer you your bank's products. A licensed broker compares 25–40 lenders and is paid a standardised commission by the winning lender — so it does not cost you more to use one. Where a broker earns their keep is understanding which lender actually approves your specific situation (self-employed, investors, foreign income) at the best terms.</p>
    <h2 class="serif" style="font-size:28px;letter-spacing:-.5px;margin:34px 0 14px">How we help</h2>
    <p style="font-size:17px;line-height:1.75;color:rgba(var(--fg-rgb),.82);margin-bottom:14px">We do not hold a credit licence ourselves. We are building a short, vetted panel of independent Gold Coast brokers we can introduce you to — brokers who will give you a written comparison of at least three lenders and whose initial consultation we have negotiated to be free. Register your interest and we will reach out when the panel goes live.</p>
    <div style="padding:28px 30px;border:1px solid rgba(196,168,74,.2);border-radius:12px;background:rgba(196,168,74,.04);margin-top:28px">
      <div class="page-label">Need the numbers first?</div>
      <h3 class="serif" style="font-size:22px;margin:10px 0 10px;letter-spacing:-.4px">Run your monthly repayments and borrowing power.</h3>
      <p style="font-size:14px;line-height:1.7;color:var(--muted);margin-bottom:18px">Our calculators give you a realistic cost of borrowing and a rough borrowing capacity based on Australian assessment rates — before you talk to anyone.</p>
      <a class="btn btn-gold" href="/calculators/">Open the calculators →</a>
    </div>
  </div>
</section>

<section class="sec" style="padding-top:20px;padding-bottom:120px;text-align:center">
  <div style="max-width:640px;margin:0 auto;padding:36px 32px;border:1px solid rgba(196,168,74,.2);border-radius:14px;background:rgba(196,168,74,.04)">
    <h2 class="serif" style="font-size:30px;margin-bottom:14px;letter-spacing:-.6px">Get introduced when we launch</h2>
    <p class="body" style="margin:0 auto 26px;font-size:15px">Register your interest and we will email you as soon as our Gold Coast broker panel is live.</p>
    <a class="btn btn-gold btn-lg" href="/#valuation">Register interest</a>
  </div>
</section>
'''
(ROOT / 'mortgage').mkdir(exist_ok=True)
(ROOT / 'mortgage' / 'index.html').write_text(build(
    MORT_BODY,
    'Mortgage Advice for Gold Coast Buyers | The One Club',
    'Straightforward home-loan guidance for Gold Coast buyers — comparison rate, offset, LMI, and when a broker beats a bank. No up-sells.',
    f'{SITE_URL}/mortgage/',
    'page-mortgage',
))
print('wrote mortgage/index.html')

# -------- Add map placeholder to each suburb page --------
MAP_INSERT_MARKER = '<section class="sec"'  # we'll insert before the first <section> after the <h1>
for slug, (lat, lng, name) in SUBURB_COORDS.items():
    p = ROOT / slug / 'index.html'
    if not p.exists():
        print(f'  skip {slug} (no page)'); continue
    html = p.read_text()
    if 'map-placeholder' in html:
        continue  # already added
    # Google Maps Embed API — `place` mode drops a labelled pin centred on
    # the query. Key is restricted to theoneclub.com.au + localhost in the
    # Google Cloud Console.
    import urllib.parse
    q = urllib.parse.quote(f'{name}, QLD, Australia')
    map_src = f'https://www.google.com/maps/embed/v1/place?key={GMAPS_KEY}&q={q}&zoom=14&maptype=roadmap'
    map_html = f'''
<section class="sec" style="padding-top:20px;padding-bottom:40px">
  <div class="sec-head">
    <div class="sec-head-l">
      <div class="page-label">Find your way around</div>
      <h2 class="serif" style="font-size:clamp(30px,3.8vw,46px)">Where is <em>{name}?</em></h2>
      <p class="body" style="font-size:15px">Pinned to the centre of the suburb. Drag, zoom, or open in Google Maps for full directions and street view.</p>
    </div>
  </div>
  <div class="map-placeholder">
    <iframe title="{name} map" loading="lazy" src="{map_src}" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
    <div class="map-placeholder-overlay">{name}, Gold Coast · QLD</div>
  </div>
</section>
'''
    # Insert the map block before the second <section> inside the page div
    # (keep the hero first). We find the second occurrence of "<section " in
    # the suburb-page body.
    def insert_after_hero(content):
        count = {'n': 0}
        def replace(m):
            count['n'] += 1
            if count['n'] == 2:
                return map_html + m.group(0)
            return m.group(0)
        return re.sub(r'<section\b', replace, content, count=2)
    new_html = insert_after_hero(html)
    # Our replace above actually inserts before the second <section ...> match
    # but the regex doesn't see the attribute list; re-do properly:
    new_html = html
    # Find all section opens, insert before the 2nd
    positions = [m.start() for m in re.finditer(r'<section\b', new_html)]
    if len(positions) >= 2:
        pos = positions[1]
        new_html = new_html[:pos] + map_html + new_html[pos:]
    p.write_text(new_html)
    print(f'  added map -> {slug}')

print('done.')
