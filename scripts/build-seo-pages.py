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

    # ── Southern Gold Coast ───────────────────────────────────────────────
    {
        'slug':       'coolangatta',
        'name':       'Coolangatta',
        'median':     1_400_000,
        'blurb':      "Coolangatta sits at the southern tip of the Gold Coast right on the QLD-NSW border. Beachfront apartments, direct airport access and proximity to Rainbow Bay and Kirra keep it a year-round market of owner-occupiers, sea-changers and holiday-home buyers.",
        'why':        "Coolangatta buyers often live interstate and buy sight-unseen after a remote inspection. Our 3D walkthroughs, floor plans and honest virtual staging let them transact with confidence — and let you sell without endless open-home weekends.",
    },
    {
        'slug':       'kirra',
        'name':       'Kirra',
        'median':     1_900_000,
        'blurb':      "Kirra is one of the most recognised surf breaks in the world and a tight beachfront pocket where apartment stock rarely sits. The strip between Coolangatta and Bilinga consistently attracts cashed-up interstate buyers chasing a lock-and-leave lifestyle.",
        'why':        "Kirra units compete on view, light and how the photography captures the ocean aspect. We shoot at the right time of day with the right equipment — and sell on the first open home more often than not.",
    },
    {
        'slug':       'tugun',
        'name':       'Tugun',
        'median':     1_300_000,
        'blurb':      "Tugun is a quieter coastal pocket just north of Gold Coast Airport — beach walks, the Tugun bypass and a steady stock of 3-and-4 bedroom family homes. A strong pick for buyers who want the southern lifestyle without Coolangatta's tourist traffic.",
        'why':        "Tugun is a family-home market first. We price with real data — recent comparable sales, not a round-number guess — so your listing lands realistically and invites competitive offers rather than sitting.",
    },
    {
        'slug':       'currumbin',
        'name':       'Currumbin',
        'median':     1_800_000,
        'blurb':      "Currumbin blends a surfable beach, the Currumbin Creek estuary and the Wildlife Sanctuary precinct. Demand comes from long-term families, inter-state sea-changers, and increasingly from younger buyers pushed south of the Burleigh premium.",
        'why':        "Currumbin homes sell on lifestyle — creek, beach, walkability. Our campaigns lead with that context (drone where the block warrants it, location-aware copy, lifestyle-cut photography), not the usual cookie-cutter listing shots.",
    },
    {
        'slug':       'mermaid-beach',
        'name':       'Mermaid Beach',
        'median':     2_400_000,
        'blurb':      "Mermaid Beach anchors the luxury stretch of the Gold Coast — Hedges Avenue (Millionaire's Row) and the beachfront townhouse strip pull cash buyers from interstate and overseas. At the top end, presentation is everything.",
        'why':        "Premium Mermaid listings deserve more than a standard agency campaign. We produce at the quality a $3m-plus home requires — without the 2.5% commission that's customary at that price bracket. The saved commission is usually more than the marketing cost.",
    },
    {
        'slug':       'miami',
        'name':       'Miami',
        'median':     1_600_000,
        'blurb':      "Miami has become one of the most desirable lifestyle pockets on the coast — the Miami Marketta strip, walkable beach access and quality schools attract young families from Brisbane and Sydney. Well-presented 3- and 4-bedroom homes consistently outperform.",
        'why':        "Miami's buyer pool is national. A strong listing needs to translate to the phone screen of a Brisbane buyer scrolling realestate.com.au on Wednesday night. Our photography, floor plan and Matterport option are designed exactly for that.",
    },
    {
        'slug':       'bilinga',
        'name':       'Bilinga',
        'median':     1_500_000,
        'blurb':      "Bilinga sits between Tugun and Kirra, quiet, beachfront, and one of the last genuinely affordable southern pockets for a walk-to-sand lifestyle. Stock is tightly held, so when something comes up presentation really does decide the sale.",
        'why':        "In a low-turnover market, your listing is the benchmark buyers compare against. We produce it as the benchmark it should be — premium photography, proper floor plans, clean copy — all included in the 1%.",
    },
]

# --------------------------------------------------------------------------
# Blog posts. Each post maps to one suburb photo for its hero; reuse
# pool intentional to keep imagery consistent with the site's imagery.
# --------------------------------------------------------------------------
POSTS = [
    {
        'slug':     'cheap-doesnt-mean-bad-it-means-fair',
        'title':    "Cheap doesn't mean bad. It means fair.",
        'excerpt':  "Why a 1% commission is the right price for real work — not a discount on the service, but a correction to a fee that was set before technology did half the job.",
        'date':     '2026-04-08',
        'read_min': 6,
        'hero':     '/images/suburbs/palm-beach.jpg',
        'body': [
            ("The word 'cheap' does a lot of work in real estate", [
                "Ask a traditional agent what they think of a 1% commission and the first word you tend to hear is <em>cheap</em>. It's a deliberate choice. In a market where most people sell a home once or twice in a lifetime, planting the idea that a lower fee must mean a lower-quality outcome is one of the most effective ways to protect a 2% to 3% baseline.",
                "But cheap and fair are not the same thing. Cheap usually implies something has been taken out to get the price down. Fair means the price matches what the work actually costs to deliver well. Those are different arguments, and the difference matters to every seller on the Gold Coast.",
            ]),
            ("What the 2–3% commission was actually buying in 2002", [
                "The fee structure most agencies still run on was normalised in an era of newspaper real-estate sections, glossy printed brochures, shopfront window displays, and a fax machine. Every listing came with real, manual cost: typesetting, offset print runs, couriers, walk-in enquiries that needed to be handed a stapled booklet.",
                "On top of that, the agent themselves was your main source of market information. Comparable sales data wasn't on your phone. You had no independent way to check whether the price was realistic. So the agent's time, knowledge and relationships were genuinely rare resources, and the price reflected that.",
                "A lot of that world is gone, and the rest of it has changed beyond recognition. What hasn't changed — across most agencies — is the headline fee.",
            ]),
            ("What it's actually buying in 2026", [
                "Today the buyer journey lives on realestate.com.au and Domain. Listings are built once, syndicated automatically, and maintained from a browser tab. Photography, floor plans and 3D walkthroughs are produced by specialists who shoot hundreds of properties a year at a known, predictable unit cost. Enquiries route to a phone that lives in your pocket and return email alerts push pre-qualified buyers to you without a mail-merge.",
                "The genuinely scarce resources — the things you <em>should</em> be paying well for — are narrower than they used to be. They are: a licensed agent who can price your property realistically using recent comparable sales, who will be honest when the offer on the table is the right one, and who will manage the contract through to settlement without you having to chase them. That is skilled, accountable work, and it deserves a real fee.",
                "What doesn't deserve a fee any more is the shopfront on the main road, the franchise percentage skimmed off the top, the middle-manager who never meets a buyer, and the marketing budget that pays for the agency's next listing pitch instead of yours.",
            ]),
            ("Fair pricing, run the math", [
                "A $1.5M Gold Coast home at 2.5% commission plus a conservative $8,000 marketing bill is $45,500 out of the seller's pocket. At 1% plus the same marketing it's $23,000. The difference — $22,500 — is enough to pay for a full year of private-school fees, or to clear 15% of a typical first-home deposit for the sellers' adult children.",
                "The agency doing the 2.5% version isn't doing twice the work. They're often outsourcing to the same photographer, the same floor-plan draughtsperson, the same virtual-staging provider. The 2.5% is the price of the storefront, not the price of the result.",
            ]),
            ("What fair does not mean", [
                "Fair doesn't mean stripping out the campaign. We include professional photography with AI enhancement, accurate floor plans, full syndication across the major portals, signage, and experienced negotiation as standard — the same things you'd expect from a premium agency, because those things are what actually move a house.",
                "Fair also doesn't mean that every agent at 1% is the right choice. There are franchised discount models that pay their agents per-transaction and treat listings as volume. That's a race to the bottom on service and it will cost you on the sale price. Being cheap on the wrong thing is false economy. Being fair on the right thing is just discipline.",
                "The test is simple: ask any agent you're interviewing what their campaign includes, how many comparable sales their proposed price is based on, how they'll keep you informed during the campaign, and what happens if the first four weeks don't produce the offer you want. If the answers are confident, specific and written down, you are probably talking to someone fair. The number on the invoice is secondary.",
            ]),
        ],
    },
    {
        'slug':     'cost-to-sell-a-house-gold-coast-2026',
        'title':    "How much does it cost to sell a house on the Gold Coast in 2026?",
        'excerpt':  "A full breakdown of commission, marketing, conveyancing and the line items most sellers forget — and why the agent's fee is rarely the biggest number on the page.",
        'date':     '2026-02-14',
        'read_min': 8,
        'hero':     '/images/suburbs/surfers-paradise.jpg',
        'body': [
            ("Start with the numbers that actually leave your account", [
                "Selling a home on the Gold Coast in 2026 is, at minimum, a five-figure exercise, and for homes above $1.5M it almost always sits in the low six figures once every bill is on the table. The reason it surprises people is that the individual costs arrive at different times — some before the campaign even starts, some only at settlement — so there isn't one moment where you see the total lined up in a single row.",
                "This guide lines them up. Conservative range, realistic range, and the levers that actually move the number up or down.",
            ]),
            ("Agent commission", [
                "Traditional Gold Coast agents sit between 2% and 3% commission. On a $1,000,000 sale that's $20,000 to $30,000; on a $2,000,000 sale it's $40,000 to $60,000. The higher rates are more common in boutique and luxury agencies; the lower rates are more common in franchise models that pay agents per-listing.",
                "Commission is almost always paid at settlement, not up-front, and it's usually deducted from the sale proceeds by your conveyancer. That is useful for cashflow, but it also means the number doesn't feel real until after the deal is done — which is part of why sellers under-price it in their planning.",
                "The One Club's fee is 1%. On the same $1,000,000 home, that's $10,000; on the $2,000,000 home, $20,000. Same campaign, half to a third of the commission.",
            ]),
            ("Marketing package", [
                "With most traditional agencies, marketing is billed <em>separately</em> from commission. A typical Gold Coast mid-tier campaign runs $4,000 to $8,000. Premium campaigns with auction, drone, Matterport and stronger portal placement run $8,000 to $15,000. Luxury campaigns with dedicated landing pages, print, and out-of-home media run $15,000 to $35,000.",
                "Most of that money is spent in the first two weeks of the campaign, so if the property sits, you're still paying for a second round of portal upgrades whether the first one worked or not.",
                "With The One Club, photography, floor plans, digital remarketing and the full campaign itself sit inside the 1% commission. The only separate marketing line is your chosen realestate.com.au and Domain listing tier — which you decide based on price bracket and visibility — plus an optional Matterport walkthrough if you want one.",
            ]),
            ("Conveyancing", [
                "A Queensland conveyancer or solicitor typically charges between $1,000 and $2,500 for a standard residential sale, with complexity (off-the-plan, body corporate, split titles, duplex arrangements) pushing it higher. For a luxury or off-market deal, expect the upper end and potentially more if there are trust or company structures involved.",
                "Conveyancing is worth paying for properly. Mistakes in contracts at settlement cost far more than the saving from using the cheapest option.",
            ]),
            ("Mortgage discharge, bank fees, adjustments", [
                "Most lenders charge a mortgage discharge fee of around $350 to $600, plus any unregistered penalty interest or break costs if you're on a fixed loan. If you'd prepaid council rates, water, or strata — those are adjusted at settlement in your favour or against you.",
                "Title registration fees and transfer fees for <em>the sale side</em> are usually minimal ($200 to $500 range), but confirm with your conveyancer.",
            ]),
            ("Preparation: styling, repairs, clean", [
                "This is the line that varies most, and the line that pays back most reliably when you spend on the right things. Budget conservatively $2,000 to $5,000 for a good deep clean, minor repairs, a touch-up paint job in the highest-traffic rooms, and a few strategically placed styling pieces. Full virtual or physical staging for a premium property can add $3,000 to $12,000 and routinely returns multiples of that back.",
                "What rarely pays back: full kitchen or bathroom renovations undertaken in the last six weeks before listing. Photography and staging will do more, faster, for a fraction of the money.",
            ]),
            ("A realistic worked example", [
                "Consider a $1,500,000 Palm Beach home going to market in autumn 2026. Traditional path: 2.5% commission ($37,500) + $8,000 marketing + $1,800 conveyancing + $500 discharge + $3,500 prep = <strong>$51,300</strong>.",
                "The One Club path: 1% commission ($15,000) including campaign + $2,200 portal tier + $400 optional Matterport + $1,800 conveyancing + $500 discharge + $3,500 prep = <strong>$23,400</strong>.",
                "Same campaign quality, same negotiation at the finish. A saving of roughly $27,900 — enough to cover one full year of the average Gold Coast private school, or to meaningfully accelerate the deposit on the next property.",
            ]),
        ],
    },
    {
        'slug':     'best-suburbs-to-buy-gold-coast-2026',
        'title':    "Best suburbs to buy on the Gold Coast in 2026",
        'excerpt':  "Where buyers are actually moving this year — broken down by lifestyle, value and growth potential, from the southern end up to the hinterland.",
        'date':     '2026-03-02',
        'read_min': 9,
        'hero':     '/images/suburbs/burleigh-heads.jpg',
        'body': [
            ("A quick 2026 market orientation", [
                "The Gold Coast market has behaved like two separate cities for the last 18 months. The southern end — roughly Burleigh down to Coolangatta — has kept appreciating at a steady mid-single-digit clip, pulled by Sydney and Melbourne cash buyers chasing lifestyle. The central strip (Broadbeach through Surfers) has been flatter and more price-sensitive, reflecting higher apartment volume and tighter owner-occupier demand.",
                "The north (Hope Island, Coomera, the canal estates) and the hinterland (Mudgeeraba, Tallai) have tracked somewhere between those two — strong where the stock is new and well-presented, soft where older product hasn't been repositioned.",
                "What follows is a working guide by buyer type, not a ranked league table. The right suburb depends entirely on what you're actually trying to buy.",
            ]),
            ("For lifestyle and long-term hold", [
                "<strong>Palm Beach.</strong> The past decade's quiet out-performer. A walkable café strip, surfable beaches, and a genuine young-professional community have turned it into the suburb that buyers who <em>would</em> have bought Burleigh five years ago now gravitate towards. New-build product is strong; older brick walk-ups are being renovated aggressively. Expect to pay a premium for anything with direct beach access.",
                "<strong>Mermaid Beach.</strong> Still the luxury stronghold of the coast. Hedges Avenue and the beachfront townhouse strip continue to draw cash buyers from interstate and overseas. Turnover is low, so when product does come up, the campaign and presentation matter more than almost anywhere else on the coast.",
                "<strong>Burleigh Heads.</strong> The established benchmark. If you want the full Gold Coast lifestyle — world-class point break, beach precinct, boutique dining — and you're prepared to pay for it, Burleigh is the safe choice. The challenge in 2026 is finding product: very little comes up, and most of it sells within two weeks.",
            ]),
            ("For value on a family budget", [
                "<strong>Robina.</strong> The commuter-belt sweet spot. Strong schools (Somerset, Kings Christian), easy M1 access, and a genuine mix of 3- and 4-bedroom family homes under $1.3M. Robina is where buyers priced out of Palm Beach and Burleigh land when schools matter more than salt spray.",
                "<strong>Varsity Lakes.</strong> Anchored by Bond University, Varsity has a disciplined pricing market because buyers and investors cross-shop aggressively. Lake-frontage townhouses hold value better than identical stock on a through street. Rental yield is typically stronger than the coast strip, which keeps investor interest healthy.",
                "<strong>Coomera and the northern growth corridor.</strong> Newer stock, larger blocks, genuinely more value per square metre. The tradeoff is distance: you're 15 to 25 minutes from the strip, and the lifestyle pitch is different. A good pick for families who prioritise space and newer build over beach walks.",
            ]),
            ("For the interstate cash buyer", [
                "<strong>Hope Island</strong> remains the go-to for lock-and-leave retirees and second-home buyers from Sydney and Melbourne. Golf course, canals, gated precincts, easy airport transfers. Listings with strong 3D walkthroughs and drone coverage consistently outperform — a disproportionate share of buyers never visit before contract.",
                "<strong>Sanctuary Cove and Paradise Point.</strong> Similar profile to Hope Island, skewed slightly more towards luxury single-dwelling stock. Price bracket starts higher.",
            ]),
            ("For the southern-end sea-changer", [
                "<strong>Currumbin.</strong> Creek, beach, and the Wildlife Sanctuary precinct. Pulls families priced out of Palm Beach who still want the southern-end lifestyle. Acreage pockets around Currumbin Valley are separately interesting to horse-and-hobby buyers.",
                "<strong>Kirra.</strong> Iconic surf break, tightly held beachfront apartment strip. Low turnover means presentation decides the sale more than anywhere else in the south. Buyers are overwhelmingly interstate.",
                "<strong>Coolangatta.</strong> The value pick at the very southern tip. Airport-side apartments, views across to Rainbow Bay, and a growing owner-occupier base that had previously been dominated by holiday rentals.",
            ]),
            ("What most buyer-ranking lists get wrong", [
                "Headline median prices are the most misleading data point in the market. A $2.4M Mermaid Beach median is dragged up by a handful of trophy beachfront sales and doesn't reflect what a family-sized 4-bedroom home actually transacts at. Similarly, Robina's apparent discount versus Burleigh looks stark on paper but narrows considerably once you're comparing like-for-like blocks.",
                "The right way to use this guide is to identify the two or three suburbs where the <em>lifestyle</em> matches you first, and then look at comparable sales within a 500m radius of specific blocks you'd actually live on. That is how buyers who don't overpay do it — and how agents who aren't chasing listings price their own vendor clients.",
            ]),
        ],
    },
    {
        'slug':     'how-to-prepare-your-home-for-sale',
        'title':    "How to prepare your Gold Coast home for sale",
        'excerpt':  "A pragmatic two-week checklist for Gold Coast sellers: where presentation money pays back, and where it almost never does.",
        'date':     '2026-03-18',
        'read_min': 7,
        'hero':     '/images/suburbs/mermaid-beach.jpg',
        'body': [
            ("Start with the two-week rule", [
                "Give yourself at minimum two clear weeks between listing decision and photography day. Not because that's how long the work takes — most of it can be done in three or four days — but because compressed timelines force mistakes: you skip the parts that move needles and keep the parts that don't, because those were the ones you already knew how to do.",
                "The goal of preparation isn't to renovate. It's to remove every frictional reason a buyer has to say no to your home on the portal in the three seconds they spend looking at the main photo.",
            ]),
            ("Week one: the triage", [
                "Walk the whole house with a notebook, outside first. Write down every thing that, if a buyer were to notice it, would subtract a percentage point of confidence from their interest. Peeling paint on the front door. Chipped tile by the entry. A dead plant in the front yard. A garage door that doesn't sit flush.",
                "Fix them. Most cost under $100 and take an afternoon. The ones that don't — major landscape work, driveway cracking, window frames with rot — are worth getting two quotes on before you decide whether to repair, disclose, or absorb the discount.",
                "Now do the inside. Dripping taps, squeaky doors, broken light fittings, chipped tiles, dead bulbs, drawers that don't close. Any single one of these noticed in an open home turns your property from 'move-in ready' to 'needs work' in the buyer's head — and it is very hard to unwind that.",
            ]),
            ("Week two: the edit, not the renovation", [
                "Clutter is the single biggest photographable cost most sellers pay. Benches, mantels, bedside tables, bathroom shelves — clear them. A coffee maker and a fruit bowl is a kitchen. A coffee maker, fruit bowl, toaster, four loose cords, and a stack of unopened mail is a life, and buyers cannot see past it to the property underneath.",
                "Take down personal photography, religious imagery, sporting memorabilia. Leave art and plants. The goal is to let the buyer imagine their own life here, not to showcase yours.",
                "Book a professional deep-clean for the day before photography. Pay for windows inside <em>and</em> out. The photography day itself should cost you nothing except turning lights on.",
            ]),
            ("Photography day", [
                "Open every blind and every curtain. Turn on every light, including under-bench kitchen LEDs and range hoods with a warm bulb. Natural light is better than any expensive light kit, but it needs to be let in.",
                "Park cars off the property a street away, and make sure the neighbours know the photographer will be there. A boat trailer in frame is a subtraction.",
                "Style the main bedroom and one living space to a very high standard — matching linen, folded throws, one good piece of art, a single styled tray on the bedside. The photographer will move from there. Resist over-styling every room. Two beautifully composed shots are worth six average ones.",
            ]),
            ("Where the money pays back — and where it does not", [
                "Pays back consistently: deep clean, touch-up paint in high-traffic areas, styling of the main bedroom and living room, landscaping of the street-facing yard (the first 10 metres a buyer sees), replaced cabinet handles, replaced door hardware.",
                "Pays back inconsistently: partial room renovations, new carpet (buyers usually want to pick their own), solar panels added immediately before sale.",
                "Rarely pays back in a six-week campaign: full kitchen renovation, full bathroom renovation, extensions, pool resurfacing, fresh landscaping in the back yard that buyers won't see until after contract.",
                "If you are tempted by a big renovation, the test is simple: would you do this if you were staying for another five years? If yes, you're doing it for you, not for resale, and the economics of that are completely different. Most sellers regret the ones they did and very few regret the ones they didn't.",
            ]),
        ],
    },
    {
        'slug':     'why-1-percent-commission-doesnt-mean-less-service',
        'title':    "Why 1% commission doesn't mean less service",
        'excerpt':  "The traditional 2–3% agency model was built for a different era. Here's how lower overheads, better tools and a tighter team actually improve the seller experience — not degrade it.",
        'date':     '2026-04-01',
        'read_min': 6,
        'hero':     '/images/suburbs/broadbeach.jpg',
        'body': [
            ("The argument being made against 1%", [
                "The most common criticism of a 1% commission, made politely at dinner parties and less politely on listing pitches, is that you cannot possibly get the same quality of campaign, the same experience of agent, or the same negotiation outcome at a third of the fee. The implication is that a traditional 2–3% commission is what quality costs, and any fee below that is a signal that quality has been removed to chase a headline.",
                "It's a neat argument. It is also mostly wrong — but the reasons why are worth unpacking, because they point to why the old fee structure persisted so long after the market it was designed for stopped existing.",
            ]),
            ("What the 2–3% fee was actually paying for in 1995", [
                "In the late 1990s, listing a Gold Coast home meant paying for: a half-page full-colour spot in the Saturday edition of the Gold Coast Bulletin, a run of glossy printed brochures, a shopfront window display, a photocopied briefing pack couriered to every competing agent in the network, and an auctioneer's time for a Saturday on-site call-up. Each of those was a real, hard, per-listing cost.",
                "The agent themselves was also the gatekeeper of information. There were no public comparable sales databases, no portal browsing history, no buyer remarketing. Their time, their relationships, and their access to the under-the-radar buyer pool were genuinely rare resources.",
                "A 2.5% commission in that world was probably about right. It priced in hard printing costs, genuine information asymmetry, and a much larger relationship-driven business model.",
            ]),
            ("What changed, in order", [
                "First, the portals. realestate.com.au and Domain moved the buyer journey online, and over fifteen years turned what had been expensive print marketing into a syndicated feed that takes an agent ten minutes to publish. Print advertising became optional and, for most price brackets, measurably less effective than its digital equivalent.",
                "Second, photography and presentation as a specialist trade. Independent photographers, floor-plan draughts, virtual staging and 3D walkthrough services priced those parts of the campaign as predictable units of work. A premium photography + floor plan + drone package that agencies used to budget at $3,000 can now be delivered for a fraction of that — and at higher quality, because the specialists shoot hundreds of homes a year.",
                "Third, data. Recent comparable sales are a few clicks away. Buyers arrive at inspections knowing what the last three similar sales were, sometimes better than the junior agent who is showing them through. The information asymmetry that supported a big fee is gone.",
                "Fourth, software. CRMs that used to belong to the biggest franchises now come monthly and per-agent. Enquiry qualification, buyer remarketing, contract management all sit inside tools a single licensed agent can run from a laptop in Palm Beach.",
            ]),
            ("Where our 1% actually goes", [
                "Professional photography, AI enhancement of those photographs for portal performance, accurate floor plans, optional 3D Matterport walkthroughs, a syndicated listing across the major portals at whatever tier you choose, a targeted digital remarketing campaign for buyers who've viewed comparable homes, signage, and a full four- to six-week campaign of buyer enquiry handling, open homes, inspections, negotiation and contract management through to settlement.",
                "Nothing is outsourced to a call centre. Nothing is handed to an intern. The agent you meet at the appraisal is the agent running the campaign, taking the offers, and sitting across the table negotiating the final price.",
            ]),
            ("What we removed, and why that improves service rather than degrading it", [
                "Shopfront overhead. The second and third tier of franchise margin. Per-listing ad spend that was designed to win the <em>next</em> listing more than to sell yours. The institutional pressure to talk a vendor into a price 5–10% above realistic so the agency can \"win\" the listing, then spend the following four weeks walking you back down to the number you should have launched at.",
                "None of those things were serving you. They were serving the agency's business model. Removing them doesn't subtract from the campaign — it subtracts from what the <em>agency</em> was getting out of it, which is a very different sentence.",
                "A smaller business, with less overhead, with a single licensed agent accountable for your campaign end to end, can spend more time on your property and less time chasing the next one. That is how a 1% model improves service, not degrades it.",
            ]),
        ],
    },
    {
        'slug':     'why-we-dont-inflate-appraisals',
        'title':    "Why we don't inflate appraisals to win listings",
        'excerpt':  "The most common trick in the Australian real estate playbook — and the single biggest reason honest sellers end up selling for less than they should.",
        'date':     '2026-04-15',
        'read_min': 5,
        'hero':     '/images/suburbs/hope-island.jpg',
        'body': [
            ("The pitch", [
                "Three agents appraise your home. Two of them quote a range of $1.3M to $1.4M. The third one confidently quotes $1.55M. You pick the third.",
                "Four weeks into the campaign, with two open homes done and no written offers, the third agent suggests a price adjustment. \"The market's not where we hoped. We should reset at $1.42M.\" Six weeks in you've dropped again. Eight weeks in you're at $1.35M, your listing has \"new price\" badges on the portals, and every buyer who looks at it assumes it has a problem.",
                "You sell at $1.32M, with a stale listing.",
            ]),
            ("What happened", [
                "The third agent never actually thought your property was worth $1.55M. The purpose of that number was to win the listing. Once your contract is signed and the property is on the market, the agent's incentive flips — every day on market costs them money, so they need to bring you down to the realistic price they knew all along.",
                "This isn't a rare event. In most major Australian markets, surveys put the rate of significant over-quoting of vendors in the 30-50% range. The Gold Coast is no exception. If three agents appraise a property, at least one of them is quoting high to win.",
            ]),
            ("Why it costs you more than just the difference", [
                "Over-quoted listings sell for <em>less</em> than honestly-priced ones, not the same. Three reasons.",
                "<strong>Launch momentum is everything.</strong> The first 10 days on a portal produce the largest buyer audience any listing ever gets. If the asking price filters you out of the searches that real buyers are running, you burn that audience on nobody. By the time the price has been dropped twice, the most active buyers have already seen and dismissed the listing.",
                "<strong>Multiple price reductions signal weakness.</strong> Buyers are extremely good at reading \"new price\" badges and days-on-market counters. A listing that's been on for 75 days with three reductions will attract only bargain hunters.",
                "<strong>The psychological anchor moves the wrong way.</strong> A vendor who started at $1.55M and has been walked down to $1.35M will often accept an offer at $1.32M — because the distance from $1.35M to $1.32M feels smaller than the distance from $1.4M (the real number) to $1.32M would have felt from day one.",
            ]),
            ("How we appraise", [
                "We give you a range backed by three to six genuinely comparable recent sales — same suburb, similar size, similar condition, sold in the last 90 days. Not auction clearance rates from two years ago, not \"my gut feeling\", not what the agency needs the number to be.",
                "If you tell us you want a higher number than the comparables support, we will tell you so — and we'll tell you what the statistical likelihood of getting that number looks like based on the recent data. If you want to price optimistically with eyes open, that's your call. But the number isn't a winning-the-pitch fabrication, and you'll always know which part is realistic and which part is reach.",
            ]),
            ("What to ask any agent you're interviewing", [
                "Ask for their three comparable sales in writing. Ask when each of them sold and what condition it was in. Ask what the median days-on-market is for properties in your bracket in your suburb in the last 90 days. Ask what price reduction strategy they'd recommend if the first two opens don't produce serious enquiry.",
                "If you can't get specific, written answers to those four questions, you're being pitched a number rather than offered an appraisal. That's a warning, and it has nothing to do with what commission the agent charges.",
            ]),
        ],
    },
    {
        'slug':     'gold-coast-portals-realestate-vs-domain',
        'title':    "What Gold Coast sellers get wrong about listing portals",
        'excerpt':  "realestate.com.au, Domain and Homely sit at the top of most campaign budgets — here's how their pricing tiers actually work, which ones matter on the Gold Coast, and where the money is usually wasted.",
        'date':     '2026-04-22',
        'read_min': 7,
        'hero':     '/images/suburbs/coolangatta.jpg',
        'body': [
            ("The portal tier system, plainly", [
                "Every major Australian real-estate portal operates a tiered listing model. Your property can be shown as a standard listing (cheapest, least visible), or upgraded up to a \"premiere\" or \"gold\"-level placement that gets photo carousels, larger tiles in search results, priority placement at the top of the search page, and boosted email alerts to active buyers in your price bracket.",
                "For a Gold Coast home in 2026, a mid-tier realestate.com.au upgrade is typically $900 to $1,400 depending on suburb. A top-tier placement is $2,500 to $3,500. Domain runs comparably. Multi-portal upgrades at premium tier can run your campaign's portal line alone to $4,500 to $6,500.",
            ]),
            ("Why the portal is usually the highest-leverage spend", [
                "Roughly 75% of buyers will see your property first on a portal. The portal is the equivalent of the shop-front window, the Saturday ad, and the agency sign all fused into one — except the decision a buyer makes to click through your listing in their three-second scan is informed almost entirely by the thumbnail, the headline number, and the property's position in the search result page.",
                "Position is bought. A premiere-tier listing from a private vendor sits above a standard-tier listing from a franchise agency. That's how the economics of the portal works.",
                "For most Gold Coast brackets — $800K to $2.5M — the incremental spend from mid-tier to top-tier is one of the highest-return line items in the whole campaign. It's the difference between being seen by the buyer who will pay your asking price and being skipped.",
            ]),
            ("When it's wasted money", [
                "Very low price bracket (under $650K). At this level the buyer audience on the portals is broad and price-sensitive. Position matters less; presentation and price matter more. Save the upgrade budget for styling.",
                "Ultra-premium ($4M+). At this level buyer discovery often happens off-portal — through specific agents, interstate buyer's agents, or private buyer lists. The portal is still used, but the incremental return from premiere placement drops sharply.",
                "Short-campaign or off-market strategies. If you're testing a price for two weeks before a formal launch, the portal upgrade won't have time to amortise. Soft-launch first, upgrade at full launch.",
            ]),
            ("How to read a portal upgrade quote from an agency", [
                "The most common portal-spend problem is not that the tier was wrong — it's that the agency chose the tier that suits <em>their</em> business model (premium = higher commission on the listing pitch) rather than the one that suits the property.",
                "Ask every agent you interview to show you, in writing, the specific package they're recommending (realestate.com.au tier, Domain tier, Homely inclusion, social boost), the cost of each line, and the reason they chose that tier for your property specifically based on recent comparable listings in your bracket.",
                "If the reply is \"we always run premiere on everything above $1M\", you are being sold the agency's default, not a campaign.",
            ]),
            ("How we handle portals", [
                "Portal spend is the only significant \"extra\" cost outside our 1% commission. We explain the tiers, show you what comparable listings in your bracket are running at, and recommend the tier that maximises your visibility for your bracket. You choose.",
                "If mid-tier is right, we say mid-tier. If premiere is justified, we say premiere and show you why. What we will not do is talk you into a premiere tier for a $750K apartment because the commission math makes it easier on our end.",
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
    hero = post.get('hero', '/images/suburbs/burleigh-heads.jpg')
    return f"""
    <a class="guide-card" href="/blog/{post['slug']}/">
      <div class="guide-card-img" style="background-image:url('{hero}');background-size:cover;background-position:center"></div>
      <div class="guide-card-body">
        <div class="guide-card-kicker">{post['date']} · {post['read_min']} min read</div>
        <div class="guide-card-title">{post['title']}</div>
        <div class="guide-card-meta">{post['excerpt']}</div>
      </div>
    </a>"""

def build_blog_index():
    cards = ''.join(blog_card(p) for p in POSTS)
    canonical = f"{SITE_URL}/blog/"
    title = "Gold Coast Real Estate Guides | The One Club"
    descr = "Long-form guides on selling your Gold Coast home, commission, cost, presentation, auction vs private treaty, and where the 2026 market is actually moving."
    jsonld = f"""<script type="application/ld+json">
{{"@context":"https://schema.org","@type":"Blog","name":"The One Club Journal","url":"{canonical}","publisher":{{"@id":"{SITE_URL}/#business"}}}}
</script>"""
    content = f"""<div class="page active">
<section class="sec" style="padding-top:140px;padding-bottom:40px">
  <div class="page-label" data-reveal>The One Club Journal</div>
  <h1 class="serif" data-reveal style="margin-top:16px;font-size:clamp(48px,6.5vw,100px);letter-spacing:-2.5px;line-height:1;font-weight:300">Gold Coast property,<br/><em>written plainly.</em></h1>
  <p class="body" data-reveal style="max-width:620px;font-size:17px;margin-top:24px">Long-form guides on what selling actually costs, how to price a home so buyers respond, how agencies structure fees, and where the 2026 market is moving — written to be useful whether you sell with us or not.</p>
</section>

<section class="sec" style="padding-top:20px;padding-bottom:120px">
  <div data-reveal style="display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:24px">{cards}
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
        # Render as <ul> only if ALL paragraphs are short + strong-led bullets.
        looks_listy = (
            len(paragraphs) > 2
            and all(len(p) < 260 and p.startswith('<strong>') for p in paragraphs)
        )
        if looks_listy:
            items = ''.join(f'<li>{p}</li>' for p in paragraphs)
            body_sections += f'<h2>{heading}</h2><ul>{items}</ul>'
        else:
            ps = ''.join(f'<p>{p}</p>' for p in paragraphs)
            body_sections += f'<h2>{heading}</h2>{ps}'

    hero = post.get('hero','/images/suburbs/burleigh-heads.jpg')
    content = f"""<div class="page active">
<section style="position:relative;width:100%;height:clamp(280px,46vh,520px);overflow:hidden;margin-top:0">
  <div style="position:absolute;inset:0;background-image:url('{hero}');background-size:cover;background-position:center"></div>
  <div style="position:absolute;inset:0;background:linear-gradient(180deg,rgba(0,0,0,.35) 0%,rgba(0,0,0,.45) 60%,rgba(0,0,0,.92) 100%)"></div>
  <div style="position:absolute;inset:auto 0 0 0;padding:0 24px 48px;max-width:900px;margin:0 auto;color:#fff">
    <nav aria-label="Breadcrumb" style="font-size:12px;color:rgba(255,255,255,.65);margin-bottom:18px"><a href="/" style="color:inherit">Home</a> · <a href="/blog/" style="color:inherit">Journal</a></nav>
    <div class="page-label" style="color:var(--gold)">{post['date']} · {post['read_min']} min read</div>
    <h1 class="serif" style="margin-top:12px;font-size:clamp(32px,5vw,58px);letter-spacing:-1.3px;line-height:1.08;font-weight:400;color:#fff">{post['title']}</h1>
  </div>
</section>

<article class="art">
  <p style="font-size:19px;line-height:1.65;color:var(--fg);font-weight:400;margin-bottom:24px;font-family:'Fraunces',Georgia,serif;font-style:italic">{post['excerpt']}</p>
  <div style="display:flex;align-items:center;gap:14px;padding:16px 0;border-top:1px solid var(--subtle);border-bottom:1px solid var(--subtle);margin-bottom:28px;font-size:13px;color:var(--muted)">
    <span>By <strong style="color:var(--fg);font-weight:500">The One Club</strong></span>
    <span style="opacity:.4">·</span>
    <span>Published {post['date']}</span>
  </div>
  {body_sections}

  <aside style="margin-top:64px;padding:32px;border:1px solid rgba(196,168,74,.25);border-radius:14px;background:rgba(196,168,74,.05)">
    <div class="page-label">Ready to sell?</div>
    <div class="serif" style="margin-top:12px;font-size:24px;line-height:1.3;letter-spacing:-.4px">Get a free appraisal for your Gold Coast home.</div>
    <p style="margin-top:10px;font-size:15px;color:var(--muted);line-height:1.65">Realistic price range, recommended strategy, full 1% fee breakdown — within 24 hours.</p>
    <div style="margin-top:20px"><a class="btn btn-gold btn-lg" href="/#valuation">Request a free valuation</a></div>
  </aside>
</article>

<section class="sec" style="padding-top:80px;padding-bottom:120px;border-top:1px solid var(--subtle)">
  <div class="sec-head">
    <div class="sec-head-l">
      <div class="page-label">More from the journal</div>
      <h2 class="serif">Keep reading.</h2>
    </div>
    <a class="more" href="/blog/">All guides →</a>
  </div>
  <div class="carousel" data-reveal>{related_cards}
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
