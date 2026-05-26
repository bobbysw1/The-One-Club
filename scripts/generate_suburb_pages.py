#!/usr/bin/env python3
"""Regenerate the suburb-specific content block on every suburb page.

The template structure replaces everything from the opening hero <section>
down to (but not including) </div>\n<footer> on each suburb page. Each suburb
gets a multi-section, unique-copy profile: character, buyer profile,
property types, where to look, market notes and lifestyle hooks.
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SUBURBS: list[dict] = [
    {
        "slug": "bilinga",
        "name": "Bilinga",
        "img": "/images/suburbs/bilinga.jpg",
        "intro": "Bilinga is the quiet stretch between Tugun and Kirra — five surf-walk blocks, a working airport behind it, and one of the last genuinely affordable beach pockets in the southern Gold Coast.",
        "character": "Bilinga is unapologetically low-key. There's no shopping strip, no high-rise frontage, and most streets still hold a mix of original three-bedroom beach cottages, brick walk-ups and the occasional new architectural build. The pace is set by the surf at Bilinga Beach and the runway noise pattern of Gold Coast Airport — which keeps prices honest and locals loyal.",
        "buyers": "Owner-occupiers who want walk-to-sand without paying Palm Beach money. Surf-focused families, downsizers from Sydney and Melbourne chasing a permanent-resident lifestyle, and a steady flow of FIFO buyers who like being 90 seconds from the terminal.",
        "property_types": [
            "Original 60s–70s beach cottages on 405–600m² blocks",
            "Brick walk-up units (2-bed, ground-floor preferred)",
            "Newer townhouses and duplexes in the western pocket",
            "A handful of architecturally rebuilt beachfront homes on Marine Parade",
        ],
        "areas": "Marine Parade and Golden Four Drive are the trophy frontage. Bilinga Avenue, Pacific Parade and the streets either side of the surf club hold the strongest owner-occupier demand. Anything west of the rail line is a different market — quieter, more affordable, but still walking distance to the beach.",
        "market_notes": "Stock is genuinely tight. When a well-presented Bilinga home hits the portals it usually sells inside three weeks at or above guide. Underpresented listings sit — buyers here are picky and many are buying sight-unseen from interstate.",
        "lifestyle": "Surf at Bilinga, coffee at Cubby Bakehouse, walk south to Kirra for the point break, or north to North Kirra for swimming. The Currumbin Creek mouth is a five-minute drive. Gold Coast Airport is the closest infrastructure asset — domestic, international, and great for southerners flying home for the weekend.",
        "median": 1500000,
        "save_low": 22500,
        "save_high": 45000,
        "trad_low": 37500,
        "trad_high": 60000,
        "our_fee": 15000,
        "median_label": "1,500,000",
    },
    {
        "slug": "broadbeach",
        "name": "Broadbeach",
        "img": "/images/suburbs/broadbeach.jpg",
        "intro": "Broadbeach is the high-energy heart of the central Gold Coast — beachfront towers, the light rail, Pacific Fair, The Star casino, and a dining scene that competes with the best of Brisbane.",
        "character": "Broadbeach trades in walkability. Towers face the surf, the dining strip on Victoria Avenue is genuinely good, the G:link light rail runs you north to Surfers or south to Pacific Fair without needing a car, and the precinct is busy seven nights a week. It feels urban in a way most of the Gold Coast deliberately isn't.",
        "buyers": "High-rise downsizers chasing single-level living with a view, investors targeting short-stay or executive rentals, professional couples who want walk-to-everything without owning a car, and a steady stream of cashed-up southerners buying their first Gold Coast pad.",
        "property_types": [
            "Beachfront apartments — 2 and 3-bed sub-penthouse stock is the hottest segment",
            "Sub-penthouses and full-floor penthouses in established towers (Air, Oracle, Soul)",
            "Lifestyle apartments on Victoria Avenue and Surf Parade",
            "A small pocket of Broadbeach Waters family homes on the canals",
        ],
        "areas": "Old Burleigh Road, The Esplanade and Albert Avenue command the strongest sqm rates. Victoria Avenue is the dining heart. Buildings with deep balconies, ocean-view kitchens and direct light-rail proximity (within 300m) outperform on resale.",
        "market_notes": "The premium beachfront apartment market has been the strongest performer on the Gold Coast over the past 24 months. Stock turns quickly when marketed properly — but presentation matters more than ever. A flat photo set on a $2M apartment will cost you weeks on market and 3–5% off the final number.",
        "lifestyle": "Pacific Fair, The Star, Kurrawa Beach patrolled year-round, the Saturday night dining strip on Victoria, Cbus Super Stadium on a Friday night, light rail to anywhere on the coast. If you want one Gold Coast suburb where you genuinely don't need a car, this is it.",
        "median": 1800000,
        "save_low": 27000,
        "save_high": 54000,
        "trad_low": 45000,
        "trad_high": 72000,
        "our_fee": 18000,
        "median_label": "1,800,000",
    },
    {
        "slug": "burleigh-heads",
        "name": "Burleigh Heads",
        "img": "/images/suburbs/burleigh-heads.jpg",
        "intro": "Burleigh Heads is where the Gold Coast properly grew up. A world-class point break, a national park headland, James Street's dining strip, and a property market that's been the coast's most consistent performer for a decade.",
        "character": "Burleigh holds its village identity better than any other central Gold Coast suburb. James Street feels like a small Melbourne high street — independent cafés, wine bars, surf brands — and the headland walk from the Burleigh Hill down to Tallebudgera Creek is still the single best stretch of public coastline in South-East Queensland. That premium is fully baked into pricing.",
        "buyers": "Interstate executive families relocating from Sydney's Northern Beaches and Melbourne's bayside, surf-oriented professionals, downsizers from acreage further south wanting a low-maintenance beach lifestyle, and a small but active luxury market for North Burleigh and West Burleigh hilltop homes.",
        "property_types": [
            "Original 70s beach houses being progressively rebuilt — these are the renovator sweet spot",
            "Architectural new builds on 405–600m² blocks (the dominant new-build typology)",
            "Sub-penthouse apartments on The Esplanade with northeast ocean aspects",
            "West Burleigh acreage and hinterland-fringe family homes",
        ],
        "areas": "The Esplanade north of the headland is trophy beachfront — anything with direct beach access is institutionally tightly held. James Street, Goodwin Terrace and the streets between James and the beach are the village-walkable sweet spot. West Burleigh and Tallebudgera Valley are the prestige acreage end.",
        "market_notes": "Burleigh routinely draws multiple-buyer competition on well-presented listings. The interstate market is large enough that you need photography, a 3D walkthrough and a floor plan from day one — half your inspections will happen on a phone in Bondi before anyone lands at Coolangatta. Listings without a walkthrough leave money on the table.",
        "lifestyle": "Burleigh Point on a clean southerly, breakfast at Borough Barista, the Burleigh Hill walk, James Street on a Friday night, the Burleigh Brewing Co, Tallebudgera Creek for the kids, Gold Coast Marathon course out the front door. Schools (Burleigh Heads State, Marymount) draw families specifically for the catchments.",
        "median": 2200000,
        "save_low": 33000,
        "save_high": 66000,
        "trad_low": 55000,
        "trad_high": 88000,
        "our_fee": 22000,
        "median_label": "2,200,000",
    },
    {
        "slug": "coolangatta",
        "name": "Coolangatta",
        "img": "/images/suburbs/coolangatta.jpg",
        "intro": "Coolangatta sits at the southern tip of the Gold Coast — the airport, the border with Tweed Heads, a beach at the end of every street, and a price point that still surprises people the first time they look.",
        "character": "Coolangatta is the Gold Coast's twin-town hub with Tweed Heads. Two states meet on Boundary Street, the airport hums in the background, and the lifestyle is unapologetically beach-oriented. The Strand and Marine Parade hold the trophy frontage; the back streets remain genuinely working-coast Australia.",
        "buyers": "Downsizers buying their last permanent home, retirees relocating from Sydney and Melbourne, FIFO workers using the airport, surf-focused families, and an active short-stay investment market driven by Gold Coast Airport arrivals.",
        "property_types": [
            "1970s low-rise apartment stock (3 to 6-storey, sea-spray patina, big balconies)",
            "Beachfront and ocean-view units on Marine Parade and The Strand",
            "Original cottages on small blocks — strong knock-down rebuild market",
            "Newer townhouses and duplexes through the inland pocket",
        ],
        "areas": "Marine Parade, The Strand and Eden Avenue are the prestige frontage. Greenmount, Rainbow Bay and Snapper Rocks at the southern end have the best surf-walk apartments. Anything within 400m of the headland walks at a premium.",
        "market_notes": "Coolangatta is in a multi-year revaluation. The airport upgrade, the Tweed Valley Hospital opening across the border, and the southern Gold Coast's emerging foodie credentials are pulling capital south. Quality apartment stock that was $700K five years ago now clears $1.2M+. Presentation lifts results materially — most local agents still under-shoot the marketing.",
        "lifestyle": "Greenmount, Snapper, Kirra and Rainbow Bay surf breaks. The Coolangatta Surf Club for sunset, the Gold Coast Airport for weekend escapes (or a weekend job, FIFO buyers know exactly what we mean), the Tweed border for the NSW lifestyle 60 seconds away, and the marathon-loop walk around Point Danger.",
        "median": 1100000,
        "save_low": 16500,
        "save_high": 33000,
        "trad_low": 27500,
        "trad_high": 44000,
        "our_fee": 11000,
        "median_label": "1,100,000",
    },
    {
        "slug": "currumbin",
        "name": "Currumbin",
        "img": "/images/suburbs/currumbin.jpg",
        "intro": "Currumbin runs from the beach inland along Currumbin Creek and up into the hinterland-fringe valley. It's the family-beach answer to Burleigh — slightly more space, slightly less density, and an estuary that turns it into a permanent holiday in school holidays.",
        "character": "Currumbin has three distinct identities. Currumbin Beach (the eastern strip) is surf, sand and walkable cafés. Currumbin Waters is the canal and family pocket. Currumbin Valley climbs into the hinterland — acreage, rainforest, and one of the best swimming holes on the coast at Currumbin Rock Pools. They sell to very different buyers.",
        "buyers": "Young families looking for school catchments (Palm Beach-Currumbin SHS is a draw), surf-oriented professionals, downsizers from Sydney's North Shore, and an acreage market in the Valley pulling in lifestyle buyers from Brisbane and northern NSW.",
        "property_types": [
            "Original beach cottages on 600–800m² blocks (Beach pocket)",
            "Canal-front family homes with pontoons (Currumbin Waters)",
            "Acreage and hinterland lifestyle homes (Currumbin Valley)",
            "Newer architectural rebuilds clustered around Pacific Parade and Thrower Drive",
        ],
        "areas": "Pacific Parade is beachfront trophy. Currumbin Beach Vikings Surf Club end is the family heart. In Currumbin Waters, the streets off the main estuary canals — Sunshine Boulevard side — hold value best. In the Valley, anything with creek frontage or a north aspect to the rainforest is institutionally tightly held.",
        "market_notes": "The school catchment effect is real and shows up in transaction patterns every January and June. The Valley acreage market is thin but active — listings often go to off-market sales. On the Beach, the renovator market has compressed: good unrenovated stock is a rare buy now.",
        "lifestyle": "Currumbin Beach, the Alley surf break, Currumbin Wildlife Sanctuary, the Vikings Surf Club for Sunday afternoons, Currumbin Rock Pools for summer, Elephant Rock for the Cooly Rocks weekend, and the Tomewin road into the hinterland for the Sunday drive.",
        "median": 1700000,
        "save_low": 25500,
        "save_high": 51000,
        "trad_low": 42500,
        "trad_high": 68000,
        "our_fee": 17000,
        "median_label": "1,700,000",
    },
    {
        "slug": "hope-island",
        "name": "Hope Island",
        "img": "/images/suburbs/hope-island.jpg",
        "intro": "Hope Island is the northern Gold Coast's resort-and-marina playground — golf, gated estates, deepwater canals, and a buyer demographic that skews older, wealthier, and overwhelmingly from southern states.",
        "character": "Hope Island is master-planned in a way most of the Gold Coast isn't. Three championship golf courses (Hope Island, Sanctuary Cove and The Glades are within a short drive), the marina precinct at Hope Harbour, gated communities with security, and the M1 north for a 50-minute Brisbane commute. The lifestyle is golf, boating, restaurants and grandkid visits.",
        "buyers": "Retirees and pre-retirees from Sydney and Melbourne, golf-oriented downsizers, executives commuting to Brisbane, boating families wanting deepwater access to the Broadwater, and a small but active luxury market in the gated estates (Cova, Sanctuary Cove fringe, Hope Island Resort).",
        "property_types": [
            "Single-level gated-estate homes on 600–900m² blocks",
            "Canal-front family homes with pontoons and Broadwater access",
            "Resort-style apartments and townhouses inside the Hope Island Resort gates",
            "Luxury estates on the golf course frontage",
        ],
        "areas": "Hope Island Resort, Cova, and the Hope Island Golf frontage are the prestige addresses. Anything with deepwater (12m+ pontoon) is a different market again — boating buyers will travel for it. The eastern canal pockets toward Paradise Point have crossover appeal with both Hope Island and Sovereign Islands buyers.",
        "market_notes": "Hope Island is a southern-buyer market — most inspections are done remotely first. A 3D walkthrough isn't a nice-to-have here, it's a qualification tool. Listings without one routinely lose interstate buyers to ones that have one. The luxury end (>$3M) trades on quality of marketing as much as quality of stock.",
        "lifestyle": "Hope Island Marketplace, Sanctuary Cove for Sunday markets, three of the best golf courses in Queensland, Hope Harbour for boat owners, the M1 north to Brisbane, the M1 south to the southern coast, and a 35-minute drive to Gold Coast Airport.",
        "median": 1600000,
        "save_low": 24000,
        "save_high": 48000,
        "trad_low": 40000,
        "trad_high": 64000,
        "our_fee": 16000,
        "median_label": "1,600,000",
    },
    {
        "slug": "kirra",
        "name": "Kirra",
        "img": "/images/suburbs/kirra.jpg",
        "intro": "Kirra is small, sharp and surf-defined — one of the most famous right-hand point breaks on the planet, a tight grid of beachfront streets, and a holiday-let market that has reshaped pricing over the past five years.",
        "character": "Kirra is essentially three streets wide. Marine Parade fronts the beach, Musgrave Street runs the parallel back-block, and the streets between hold a mix of 60s walk-up apartments, original cottages, and progressively newer rebuilds. The Kirra Surf Club anchors the social end; Coolangatta's airport behind keeps the price honest.",
        "buyers": "Surf-focused buyers (many of them returning from years of holiday visits), short-stay investors targeting the Bondi-of-the-north positioning, downsizers chasing apartment living with a view, and a quiet but active high-net-worth market for Marine Parade beachfront houses.",
        "property_types": [
            "Beachfront apartments in 1970s low-rise blocks (the bulk of stock)",
            "Original beach cottages on 405m² blocks (rare, snapped up by rebuilders)",
            "A small handful of architectural beachfront houses on Marine Parade",
            "Newer townhouses on Musgrave Street",
        ],
        "areas": "Marine Parade is the trophy. Any unit with a north or northeast aspect over the Kirra point break commands a premium that has nothing to do with size and everything to do with the swell window. Musgrave Street and the Garrick Street pocket are the affordable entry. Anything within 200m of the surf club is institutionally tight.",
        "market_notes": "Kirra reprices on swell events — the World Surf League stops bring international attention, and serious buyers fly in within weeks. Stock genuinely sells fast when presented well. Underpresented listings on a beachfront in Kirra are a missed opportunity worth tens of thousands.",
        "lifestyle": "Kirra Point on a swell, the Kirra Surf Club for sunset, walks south to Coolangatta and north to North Kirra and Bilinga, Cooly Rocks for the rockabilly weekend, Greenmount and Snapper at the southern tip, and the airport for everything that isn't the beach.",
        "median": 1400000,
        "save_low": 21000,
        "save_high": 42000,
        "trad_low": 35000,
        "trad_high": 56000,
        "our_fee": 14000,
        "median_label": "1,400,000",
    },
    {
        "slug": "mermaid-beach",
        "name": "Mermaid Beach",
        "img": "/images/suburbs/mermaid-beach.jpg",
        "intro": "Mermaid Beach is home to Hedges Avenue — Millionaires' Row — and one of the most concentrated luxury beachfront markets in Australia. It's also one of the Gold Coast's most genuinely walkable family suburbs.",
        "character": "Mermaid Beach has two parallel lives. Hedges Avenue is institutional-grade Australian luxury real estate — the prestige beachfront strip from Nobby Beach to Broadbeach is one of the most expensive sqm in the country. One street back, the suburb returns to being a beach-village with surf clubs, original homes, walkable cafés and a strong primary school. Same postcode, very different markets.",
        "buyers": "Hedges Avenue trades to a tight buyer pool of high-net-worth families and developers. The non-beachfront market is owner-occupier driven — established Gold Coast families, professional couples upgrading from apartments, and downsizers from canal-front pockets nearby. Strong interstate interest at every price point.",
        "property_types": [
            "Beachfront luxury homes on Hedges Avenue (sub-divisions of 600m² and 1,200m² blocks)",
            "Original 60s–70s beach cottages on the second and third row (renovator gold)",
            "Architectural rebuilds — the dominant new-build typology",
            "Low-rise beachfront apartments on the southern end approaching Nobby Beach",
        ],
        "areas": "Hedges Avenue is the trophy strip, full stop. The Esplanade behind it, Beachcomber Court, Albatross Avenue and Markeri Street are the prestige second-row streets. Nobby Beach end has a younger, café-culture energy; the Broadbeach end is more urbanised. Mermaid Waters (canal pocket inland) is a different market segment again.",
        "market_notes": "Hedges Avenue listings sell on private campaigns as often as portals — buyers are pre-qualified and the discretion premium is real. The second and third row to the beach is where the strongest competition happens publicly. Marketing budgets need to match the address; a tight 1% campaign with proper photography and 3D outperforms a generic $20K marketing spend.",
        "lifestyle": "Walk to the surf at Nobby Beach, breakfast at one of the strip's cafés, Pacific Fair within minutes, light rail at Mermaid Waters station, Mermaid Beach State School for families, and direct beach access at the end of every street between Heron and Markeri.",
        "median": 2400000,
        "save_low": 36000,
        "save_high": 72000,
        "trad_low": 60000,
        "trad_high": 96000,
        "our_fee": 24000,
        "median_label": "2,400,000",
    },
    {
        "slug": "miami",
        "name": "Miami",
        "img": "/images/suburbs/miami.jpg",
        "intro": "Miami is the Gold Coast's quiet success story — original beach houses being progressively rebuilt, a growing dining and café scene (Marketta, Burleigh Pavilion-adjacent), and pricing that's caught up fast.",
        "character": "Miami sits between Nobby Beach and Burleigh Heads and has absorbed pricing pressure from both. It's still got the original Gold Coast beach-suburb DNA — small blocks, beach-walk streets, low-rise apartment stock — but the rebuild rate is accelerating. The Marketta night-market scene and the Pizzey Park sports precinct give it a real community anchor.",
        "buyers": "Families priced out of Burleigh Heads but unwilling to move further from the beach, young professional couples buying their first house, builders and architects targeting the renovator and rebuild market, and a steady short-stay investor segment around the beachfront strip.",
        "property_types": [
            "Original 60s–70s beach cottages on 405–600m² blocks (the renovator sweet spot)",
            "Architectural new builds and rebuilds (the dominant new-build typology)",
            "Low-rise beachfront apartments (3 to 6-storey, big balconies)",
            "Townhouses and duplexes through the inland pocket toward the highway",
        ],
        "areas": "Hedges Avenue (yes, Miami too — the strip continues), Pacific Parade, and Cypress Terrace are the trophy frontage. The streets between the highway and the beach hold the strongest owner-occupier demand. West of the highway is a different value proposition — quieter, more affordable, but no longer cheap.",
        "market_notes": "Miami has compressed the gap to Burleigh Heads materially over the past three years. Renovator stock that was $1.4M is now $1.8M+; rebuilt architectural homes on the beach side regularly clear $3M+. Marketing matters — Miami buyers are increasingly the same buyers as Burleigh buyers, and they compare presentation directly.",
        "lifestyle": "Miami Beach, the surf at Pacific Parade, Pizzey Park for sport, Marketta on a Wednesday or Friday night, the cafés along the Gold Coast Highway, Burleigh Heads to the south for the headland walk, and the M1 nearby for the airport run.",
        "median": 1700000,
        "save_low": 25500,
        "save_high": 51000,
        "trad_low": 42500,
        "trad_high": 68000,
        "our_fee": 17000,
        "median_label": "1,700,000",
    },
    {
        "slug": "mudgeeraba",
        "name": "Mudgeeraba",
        "img": "/images/suburbs/mudgeeraba.jpg",
        "intro": "Mudgeeraba is hinterland-fringe Gold Coast — rural blocks, larger family homes, established schools, and a 20-minute drive to either the beach or the M1. It's where Gold Coast families move when they want space.",
        "character": "Mudgeeraba is the Gold Coast's family-acreage answer. It's not the beach. It's not the city. It's a village centre (proper old-pub Mudgeeraba), surrounded by acreage homes, mid-density family estates, and the rural-residential roads that climb up into the Hinterland behind. Equestrian properties, big sheds, and three-car garages are baseline.",
        "buyers": "Established Gold Coast families upgrading from coastal townhouses, equestrian and hobby-farm buyers, families chasing the King's Christian / Somerset / Hillcrest school catchments, and Brisbane-relocators wanting hinterland lifestyle without losing the M1 commute.",
        "property_types": [
            "Acreage homes on 1–5 acre blocks (the prestige segment)",
            "Established family homes on 600–1,200m² blocks in the central pocket",
            "Newer master-planned estates (Reedy Creek fringe, Robina fringe)",
            "Equestrian and lifestyle properties along Worongary Road and beyond",
        ],
        "areas": "The acreage roads west of the village (Hardys Road, Worongary Road, Quinns Hill) are the prestige addresses. The central pocket around the village and the primary school holds the strongest family-home demand. Anything along Boomerang Road has fast M1 access and trades as a commuter premium.",
        "market_notes": "Mudgeeraba's market is school-catchment and commute-driven. Buyers shortlist on those two filters before they shortlist on house. Acreage properties need proper drone work, video walkthroughs and accurate land-use marketing — most local agents undercook this. The rural-residential market is forgiving of stock condition but unforgiving of bad marketing.",
        "lifestyle": "The Mudgeeraba Pub, the old village strip with its weekend markets, riding trails through the hinterland, Springbrook within 25 minutes for the waterfalls, Robina Town Centre 10 minutes east for shopping, and the M1 ramp for everything else.",
        "median": 1300000,
        "save_low": 19500,
        "save_high": 39000,
        "trad_low": 32500,
        "trad_high": 52000,
        "our_fee": 13000,
        "median_label": "1,300,000",
    },
    {
        "slug": "palm-beach",
        "name": "Palm Beach",
        "img": "/images/suburbs/palm-beach.jpg",
        "intro": "Palm Beach has had the most dramatic five years of any Gold Coast suburb. Original beach cottages are being rebuilt at scale, the Tallebudgera Creek end is now one of the most desirable family addresses on the coast, and the café scene rivals Burleigh.",
        "character": "Palm Beach is long — it runs from Currumbin Creek in the south to Tallebudgera Creek in the north, with four to five distinct micro-pockets along the way. The northern end (Palm Beach North) feels like an extension of Burleigh. The southern end (toward Currumbin Estuary) is quieter and more family-driven. The middle holds the genuinely original beach-village heart of the suburb.",
        "buyers": "Sydney and Melbourne family relocators (this is genuinely the loudest interstate-buyer segment on the coast right now), builders and architects buying renovators, downsizers from Burleigh and Mermaid wanting more space, and an active luxury market at the Tallebudgera Creek mouth.",
        "property_types": [
            "Original 60s beach cottages on 405–600m² blocks (the renovator goldmine)",
            "Architectural rebuilds (the dominant new-build typology — Palm Beach has the highest rebuild rate on the coast)",
            "Creek-front and creek-adjacent family homes at the Tallebudgera end",
            "Newer townhouses and small infill developments through the central pocket",
        ],
        "areas": "Jefferson Lane and Palm Beach Avenue at the Tallebudgera Creek end are trophy frontage. 19th Avenue, 11th Avenue and the streets between the highway and the beach in central Palm Beach hold the strongest demand. The Currumbin end (south of Tallebudgera) crosses over with Currumbin Beach buyers and trades accordingly.",
        "market_notes": "Palm Beach is the most-watched suburb on the coast for the past 24 months. Every well-presented listing draws interstate competition. The rebuild market is the most active in Queensland — original cottages with 'rebuild potential' marketing routinely clear in 10–14 days. Marketing isn't optional here; it's what separates a market-clearing result from a sit.",
        "lifestyle": "Palm Beach itself is the asset — long, swimmable, walkable from anywhere in the suburb. Tallebudgera Creek mouth for paddleboarding, the Palm Beach SLSC at the central pocket, the cafés (Café D'Bah, Lock and Key, Etsu) clustered along the strip, and the M1 ramp at the southern end for the airport.",
        "median": 1900000,
        "save_low": 28500,
        "save_high": 57000,
        "trad_low": 47500,
        "trad_high": 76000,
        "our_fee": 19000,
        "median_label": "1,900,000",
    },
    {
        "slug": "robina",
        "name": "Robina",
        "img": "/images/suburbs/robina.jpg",
        "intro": "Robina is the Gold Coast's master-planned family centre — Robina Town Centre, Bond University, Cbus Super Stadium, Robina Hospital, and a settled grid of family homes on quiet streets. It's the suburb people choose with their kids' schools in mind.",
        "character": "Robina is purpose-built — laid out in the 1980s and 90s around the town centre, the train station and the universities. Quiet residential streets, well-established parks and lake systems, a hospital, a train line to Brisbane, and the M1 immediately accessible. It's not flashy. It's reliably family.",
        "buyers": "Owner-occupier families chasing schools (Robina State High, All Saints, Somerset), Bond University academic and medical professional families, healthcare workers from Robina Hospital, and a steady commuter market into Brisbane on the train line.",
        "property_types": [
            "Established family homes on 500–800m² blocks (the dominant typology)",
            "Newer townhouses and small infill projects in the eastern pockets",
            "Lake-front and lake-adjacent family homes (Lake Orr, Lake Glenelg) at a premium",
            "Bond University-adjacent rentals and investment stock",
        ],
        "areas": "The Lake Orr precinct and Bond University-adjacent streets are the prestige end. The eastern pockets toward the highway hold the strongest owner-occupier demand. Anything within walking distance of Robina Town Centre or the train station trades at a measurable premium on lifestyle and resale.",
        "market_notes": "Robina is a school-catchment market — and it's increasingly an interstate-relocator market too, as Sydney and Melbourne families realise the lifestyle-to-price ratio. Quality family homes in good catchments sell quickly. Stock that's not in a catchment, or that needs work, takes longer and needs sharper marketing to find the right buyer.",
        "lifestyle": "Robina Town Centre, Cbus Super Stadium for the Titans, Bond University events, the lake walks, Robina Hospital for the health precinct, the train line to Brisbane in under an hour, and the M1 ramps for the southern Gold Coast beaches in 15 minutes.",
        "median": 1100000,
        "save_low": 16500,
        "save_high": 33000,
        "trad_low": 27500,
        "trad_high": 44000,
        "our_fee": 11000,
        "median_label": "1,100,000",
    },
    {
        "slug": "surfers-paradise",
        "name": "Surfers Paradise",
        "img": "/images/suburbs/surfers-paradise.jpg",
        "intro": "Surfers Paradise is the high-rise heart of the Gold Coast — the beach, the towers, the tourism, and an apartment market that operates on different rules to the rest of the coast.",
        "character": "Surfers is a high-density tourism and lifestyle market. Cavill Avenue, the beachfront towers (Q1, Soul, Circle on Cavill, Hilton), the SkyPoint observation deck, the Schoolies week culture, and a permanent-resident population that mostly lives in apartments. It's the only Gold Coast suburb that functions like a small CBD.",
        "buyers": "Investor-heavy market — short-stay (Airbnb-style), executive rental and student rental — alongside a growing permanent owner-occupier base in sub-penthouse stock. Strong interstate and offshore interest, particularly Asian-buyer activity in the towers, and a quiet but real market for the 'best-of-Surfers' high-floor apartments.",
        "property_types": [
            "High-rise apartments in iconic towers (Q1, Soul, Circle on Cavill, Hilton, Orchid)",
            "Sub-penthouses and penthouses (the prestige segment)",
            "Lifestyle apartments away from the absolute beachfront (better value per sqm)",
            "A small handful of canal homes on the Isle of Capri and adjacent precincts",
        ],
        "areas": "The Esplanade north of Cavill Avenue, Old Burleigh Road south, and the streets immediately around the Hilton precinct are the trophy strip. Buildings with strong amenity (gym, pool, sky lounge), genuine ocean aspect (not 'partial'), and live-in management outperform on resale. Isle of Capri and Cypress Avenue are the canal-home alternatives.",
        "market_notes": "Surfers operates on yields as much as growth. Investors buy on rental return and capital growth potential, owner-occupiers buy on view and amenity. The same apartment with two different marketing approaches sells to two different buyer pools at two different prices. Strategy matters as much as price.",
        "lifestyle": "The beach (patrolled 365), Cavill Avenue, SkyPoint, the Esplanade jogging strip, the Gold Coast Convention Centre, light rail to anywhere on the coast, Marina Mirage for the upmarket dining, and Indy week / Schoolies / Magic Millions for the calendar peaks.",
        "median": 950000,
        "save_low": 14250,
        "save_high": 28500,
        "trad_low": 23750,
        "trad_high": 38000,
        "our_fee": 9500,
        "median_label": "950,000",
    },
    {
        "slug": "tugun",
        "name": "Tugun",
        "img": "/images/suburbs/tugun.jpg",
        "intro": "Tugun is the southern Gold Coast's quiet, salt-air pocket between Currumbin and Bilinga — small village centre, surf-walk beaches, and one of the last suburbs where a renovator under $1.5M still appears.",
        "character": "Tugun is small. The village strip on Golden Four Drive has a handful of cafés (the Tugun Bakery is the institution), the surf club anchors the south end of the beach, and the streets behind hold a mix of original beach cottages, low-rise walk-ups and progressively newer rebuilds. The airport behind keeps prices honest — but the surf and the lifestyle are first-class.",
        "buyers": "Owner-occupier families and downsizers chasing southern Gold Coast lifestyle without Palm Beach or Burleigh pricing, surf-focused buyers, FIFO workers using the airport, and a growing rebuild and renovator market driven by Sydney and Melbourne relocators.",
        "property_types": [
            "Original beach cottages on 405–600m² blocks (the renovator end of the market)",
            "Architectural rebuilds (rising fast in number)",
            "Low-rise beachfront apartments, mostly 70s and 80s",
            "Newer townhouses and duplexes through the western pocket",
        ],
        "areas": "Toolona Street and the streets between Golden Four Drive and the beach are the prestige pocket. Anything within walking distance of the Tugun Surf Club is institutionally tight. The western side of Golden Four Drive is quieter and more affordable but still walks to the beach.",
        "market_notes": "Tugun has had a quieter run than Palm Beach but is following the same playbook on a 12–18 month lag. The renovator market is the fastest-moving segment — original homes with rebuild potential routinely sell on first or second inspection. Underpresented listings sit; well-presented listings clear fast.",
        "lifestyle": "Tugun Beach, the Tugun Bakery (yes, really), the surf club for sunset, Currumbin Wildlife Sanctuary 5 minutes south, the airport for weekend escapes (or arrivals), and the M1 ramp 90 seconds away for the rest of the coast.",
        "median": 1500000,
        "save_low": 22500,
        "save_high": 45000,
        "trad_low": 37500,
        "trad_high": 60000,
        "our_fee": 15000,
        "median_label": "1,500,000",
    },
    {
        "slug": "varsity-lakes",
        "name": "Varsity Lakes",
        "img": "/images/suburbs/varsity-lakes.jpg",
        "intro": "Varsity Lakes is master-planned around the lake system at the southern end of Robina — Bond University, family streets, lake-front estates, and a growing dining strip on Varsity Parade.",
        "character": "Varsity Lakes was planned from scratch in the late 90s. The lake is the centrepiece, Bond University and Varsity College anchor the eastern edge, and the residential grid runs in tidy curves around it. Family-oriented, walkable, and increasingly attractive to professional couples who don't want apartment living but want lifestyle close at hand.",
        "buyers": "Owner-occupier families chasing Varsity College and Bond University catchments, academic and medical professional families, healthcare workers from Robina Hospital, and a growing premium market for lake-front and lake-adjacent homes.",
        "property_types": [
            "Established family homes on 500–700m² blocks (the dominant typology)",
            "Lake-front family homes with private jetties (the prestige segment)",
            "Newer townhouses and duplexes through the eastern infill pockets",
            "A small Bond University-adjacent rental and investment market",
        ],
        "areas": "Lake-front streets (Lakeview Boulevard and the curves immediately around the lake system) are the prestige addresses. The streets close to Varsity College and the Varsity Parade dining strip hold the strongest owner-occupier demand. Anything walking distance to Bond University trades at a measurable premium.",
        "market_notes": "Varsity is a quietly strong market — settled, family-driven, with very low turnover in the lake-front pockets. When a quality lake-front listing comes up, the buyer pool is deep but specific. Marketing it generically misses the buyer who's been waiting for it; targeted lifestyle marketing is what closes the gap.",
        "lifestyle": "The lake walks and weekend rowing, Varsity Parade for the dining strip, Bond University for the events calendar, Varsity College for the family routine, Robina Town Centre 5 minutes north, Burleigh Heads 8 minutes east, and the M1 immediately accessible for the rest of the coast.",
        "median": 1200000,
        "save_low": 18000,
        "save_high": 36000,
        "trad_low": 30000,
        "trad_high": 48000,
        "our_fee": 12000,
        "median_label": "1,200,000",
    },
]


def build_content(s: dict) -> str:
    """Build the replacement HTML block for a suburb."""
    name = s["name"]
    slug = s["slug"]
    img = s["img"]
    items_html = "\n".join(
        f'        <li style="padding:14px 0;border-bottom:1px solid rgba(var(--fg-rgb),.06);font-size:15px;color:rgba(var(--fg-rgb),.82);line-height:1.55">{item}</li>'
        for item in s["property_types"]
    )
    return f"""<section style="padding:140px 24px 32px;max-width:1100px;margin:0 auto">
  <div class="page-label" style="color:var(--gold)" data-reveal>{name} real estate</div>
  <h1 class="serif" data-reveal style="font-size:clamp(44px,6.5vw,88px);letter-spacing:-2px;line-height:1;font-weight:300;margin-top:18px">Real estate agent in<br/><em>{name}</em></h1>
  <p class="body" data-reveal style="font-size:18px;max-width:760px;margin-top:28px;line-height:1.65">{s["intro"]}</p>
  <div data-reveal style="margin-top:28px;display:flex;gap:12px;flex-wrap:wrap">
    <a class="btn btn-gold btn-lg" href="/#valuation">Get Your Free Valuation</a>
    <a class="btn btn-outline btn-lg" href="/for-sale/">See current listings</a>
  </div>
</section>

<section style="padding:0 24px 56px;max-width:1100px;margin:0 auto">
  <figure data-reveal style="margin:0;border-radius:18px;overflow:hidden;aspect-ratio:21/9;background:#0a0a0a">
    <img src="{img}" alt="{name}, Gold Coast" loading="lazy" decoding="async" style="width:100%;height:100%;object-fit:cover;display:block"/>
  </figure>
</section>

<section class="sec" style="padding-top:0;padding-bottom:40px">
  <div class="sec-head">
    <div class="sec-head-l">
      <div class="page-label">Find your way around</div>
      <h2 class="serif" style="font-size:clamp(30px,3.8vw,46px)">Where is <em>{name}?</em></h2>
      <p class="body" style="font-size:15px">Pinned to the centre of the suburb. Drag, zoom, or open in Google Maps for full directions and street view.</p>
    </div>
  </div>
  <div class="map-placeholder">
    <iframe title="{name} map" loading="lazy" src="https://www.google.com/maps/embed/v1/place?key=AIzaSyDyWnJ2ud9rWnBqUY96uankmuUnH-gxIRM&q={name.replace(' ', '+')}%2C+QLD%2C+Australia&zoom=14&maptype=roadmap" referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe>
    <div class="map-placeholder-overlay">{name}, Gold Coast · QLD</div>
  </div>
</section>

<!-- SUBURB PROFILE — UNIQUE CHARACTER -->
<section style="padding:40px 24px 0;max-width:1100px;margin:0 auto">
  <div data-reveal style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:32px;align-items:start">
    <div>
      <div class="page-label" style="color:var(--gold)">What makes it unique</div>
      <h2 class="serif" style="font-size:clamp(26px,3.2vw,40px);margin-top:14px;line-height:1.1">The character<br/>of <em>{name}.</em></h2>
    </div>
    <div>
      <p class="body" style="font-size:16px;line-height:1.75;color:rgba(var(--fg-rgb),.82)">{s["character"]}</p>
    </div>
  </div>
</section>

<!-- BUYER PROFILE -->
<section style="padding:64px 24px 0;max-width:1100px;margin:0 auto">
  <div data-reveal style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:32px;align-items:start">
    <div>
      <div class="page-label" style="color:var(--gold)">Who buys here</div>
      <h2 class="serif" style="font-size:clamp(26px,3.2vw,40px);margin-top:14px;line-height:1.1">The {name}<br/><em>buyer profile.</em></h2>
    </div>
    <div>
      <p class="body" style="font-size:16px;line-height:1.75;color:rgba(var(--fg-rgb),.82)">{s["buyers"]}</p>
    </div>
  </div>
</section>

<!-- PROPERTY TYPES -->
<section style="padding:64px 24px 0;max-width:1100px;margin:0 auto">
  <div data-reveal>
    <div class="page-label" style="color:var(--gold)">Property types</div>
    <h2 class="serif" style="font-size:clamp(26px,3.2vw,40px);margin-top:14px;line-height:1.1">What sells in <em>{name}.</em></h2>
    <ul style="list-style:none;padding:0;margin:28px 0 0;max-width:760px">
{items_html}
    </ul>
  </div>
</section>

<!-- WHERE TO LOOK -->
<section style="padding:64px 24px 0;max-width:1100px;margin:0 auto">
  <div data-reveal style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:32px;align-items:start">
    <div>
      <div class="page-label" style="color:var(--gold)">Where to look</div>
      <h2 class="serif" style="font-size:clamp(26px,3.2vw,40px);margin-top:14px;line-height:1.1">Streets and<br/><em>pockets.</em></h2>
    </div>
    <div>
      <p class="body" style="font-size:16px;line-height:1.75;color:rgba(var(--fg-rgb),.82)">{s["areas"]}</p>
    </div>
  </div>
</section>

<!-- MARKET NOTES -->
<section style="padding:64px 24px 0;max-width:1100px;margin:0 auto">
  <div data-reveal style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:32px;align-items:start">
    <div>
      <div class="page-label" style="color:var(--gold)">Market notes</div>
      <h2 class="serif" style="font-size:clamp(26px,3.2vw,40px);margin-top:14px;line-height:1.1">How {name}<br/><em>actually trades.</em></h2>
    </div>
    <div>
      <p class="body" style="font-size:16px;line-height:1.75;color:rgba(var(--fg-rgb),.82)">{s["market_notes"]}</p>
    </div>
  </div>
</section>

<!-- LIFESTYLE -->
<section style="padding:64px 24px 80px;max-width:1100px;margin:0 auto">
  <div data-reveal style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:32px;align-items:start">
    <div>
      <div class="page-label" style="color:var(--gold)">Lifestyle</div>
      <h2 class="serif" style="font-size:clamp(26px,3.2vw,40px);margin-top:14px;line-height:1.1">A weekend<br/>in <em>{name}.</em></h2>
    </div>
    <div>
      <p class="body" style="font-size:16px;line-height:1.75;color:rgba(var(--fg-rgb),.82)">{s["lifestyle"]}</p>
    </div>
  </div>
</section>

<!-- WHY SELL WITH US + SAVINGS -->
<section style="padding:60px 24px 100px;max-width:1100px;margin:0 auto;border-top:1px solid rgba(var(--fg-rgb),.06)">
  <div data-reveal style="max-width:720px;margin:0 auto 48px;text-align:center;padding-top:40px">
    <div class="page-label">Why sell with us in {name}</div>
    <div class="display" style="margin-top:18px;font-size:clamp(36px,4.5vw,58px)">1% commission.<br/><em>Keep the difference.</em></div>
    <div class="gold-rule" style="margin:26px auto"></div>
  </div>

  <div data-reveal style="background:rgba(var(--fg-rgb),.025);border:1px solid rgba(var(--fg-rgb),.07);border-radius:18px;padding:40px 28px;max-width:720px;margin:0 auto">
    <div style="text-align:center;font-size:11px;font-weight:700;letter-spacing:2px;text-transform:uppercase;color:var(--muted)">Savings on a typical {name} home</div>
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:20px;margin-top:28px;text-align:center">
      <div>
        <div style="font-size:11px;color:var(--muted);letter-spacing:1.5px;text-transform:uppercase">Traditional (2–3%)</div>
        <div style="font-size:clamp(28px,3.5vw,40px);font-weight:400;color:rgba(255,80,80,.75);letter-spacing:-1px;margin-top:8px">${s["trad_low"]:,} – ${s["trad_high"]:,}</div>
      </div>
      <div>
        <div style="font-size:11px;color:var(--muted);letter-spacing:1.5px;text-transform:uppercase">The One Club (1%)</div>
        <div style="font-size:clamp(28px,3.5vw,40px);font-weight:400;color:var(--gold);letter-spacing:-1px;margin-top:8px">${s["our_fee"]:,}</div>
      </div>
    </div>
    <div style="text-align:center;margin-top:24px;padding-top:24px;border-top:1px solid rgba(var(--fg-rgb),.06)">
      <div style="font-size:11px;color:var(--muted);letter-spacing:1.5px;text-transform:uppercase">You save</div>
      <div style="font-size:clamp(34px,4vw,48px);font-weight:400;color:#4ade80;letter-spacing:-1px;margin-top:8px">${s["save_low"]:,} – ${s["save_high"]:,}</div>
      <div style="font-size:12px;color:var(--muted);margin-top:6px">Based on an approximate median sale of ${s["median_label"]}. Your result will vary with final sale price and chosen portal level.</div>
    </div>
    <div style="text-align:center;margin-top:28px">
      <a class="btn btn-gold btn-lg" href="/#valuation">Get a free valuation for your {name} home</a>
    </div>
  </div>
</section>

<section style="padding:40px 24px 120px;max-width:1100px;margin:0 auto;text-align:center">
  <div data-reveal>
    <div class="page-label">Included with every {name} listing</div>
    <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-top:28px;max-width:900px;margin-inline:auto;text-align:left">
      <div style="padding:20px;border:1px solid rgba(var(--fg-rgb),.07);border-radius:12px"><div style="font-weight:600;margin-bottom:6px">Professional photography</div><div style="font-size:13px;color:var(--muted)">Shot at golden hour, AI-enhanced, virtually staged where helpful.</div></div>
      <div style="padding:20px;border:1px solid rgba(var(--fg-rgb),.07);border-radius:12px"><div style="font-weight:600;margin-bottom:6px">Accurate floor plans</div><div style="font-size:13px;color:var(--muted)">Ground floor and level 1 drawn separately; formatted for every portal.</div></div>
      <div style="padding:20px;border:1px solid rgba(var(--fg-rgb),.07);border-radius:12px"><div style="font-weight:600;margin-bottom:6px">Interactive 3D walkthrough</div><div style="font-size:13px;color:var(--muted)">Captured in-house, viewable on any phone. Built for interstate buyers.</div></div>
      <div style="padding:20px;border:1px solid rgba(var(--fg-rgb),.07);border-radius:12px"><div style="font-weight:600;margin-bottom:6px">Digital marketing campaign</div><div style="font-size:13px;color:var(--muted)">realestate.com.au + Domain + targeted buyer remarketing.</div></div>
    </div>
    <div style="margin-top:40px">
      <a class="btn btn-gold btn-lg" href="/#valuation">Request a free {name} valuation</a>
    </div>
  </div>
</section>"""


# Pattern to find existing suburb content block (from opening hero section to closing </section> before </div><footer>)
START_RE = re.compile(
    r'<section style="position:relative;width:100%;height:clamp\(460px,65vh,720px\).*',
    re.DOTALL,
)
END_RE = re.compile(r'</section>\s*</div>\s*<footer>', re.DOTALL)


def rewrite(slug: str, html: str) -> str:
    suburb = next(s for s in SUBURBS if s["slug"] == slug)
    new_block = build_content(suburb) + "\n</div>\n<footer>"

    # Find start
    m_start = START_RE.search(html)
    if not m_start:
        raise SystemExit(f"[{slug}] could not find start of content block")
    # Find end (search from start onward)
    m_end = END_RE.search(html, m_start.start())
    if not m_end:
        raise SystemExit(f"[{slug}] could not find end of content block")
    return html[: m_start.start()] + new_block + html[m_end.end():]


def main() -> None:
    for s in SUBURBS:
        path = ROOT / s["slug"] / "index.html"
        if not path.exists():
            print(f"[skip] {path} not found")
            continue
        html = path.read_text(encoding="utf-8")
        new_html = rewrite(s["slug"], html)
        path.write_text(new_html, encoding="utf-8")
        print(f"[ok] {s['slug']}")


if __name__ == "__main__":
    main()
