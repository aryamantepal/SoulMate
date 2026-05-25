from app.sources.base import Shoe

# Placeholder helper — generates a colored placeholder image with the shoe name
def _p(color: str, name: str) -> str:
    slug = name.replace(" ", "+").replace("'", "")
    return f"https://placehold.co/400x300/{color}/ffffff?text={slug}"


CATALOG: list[Shoe] = [
    # ── Originals (hand-tuned) ──────────────────────────────────────────────
    Shoe(
        id="nb-550-au-lait",
        name="NB 550 'Au Lait'",
        brand="New Balance",
        notes="The grail: creamy vintage court energy with soft suede warmth.",
        image_url="/shoes/nb-550-au-lait.png",
        v={"chunk": 0.55, "retro": 0.92, "warm": 0.88, "minimal": 0.72, "earthy": 0.82, "loud": 0.28, "techy": 0.08},
    ),
    Shoe(
        id="asics-gel-kayano-14-cream-black",
        name="ASICS Gel-Kayano 14 Cream Black",
        brand="ASICS",
        image_url="/shoes/asics-gel-kayano-14-cream-black.png",
        v={"chunk": 0.68, "retro": 0.62, "warm": 0.46, "minimal": 0.35, "earthy": 0.28, "loud": 0.48, "techy": 0.74},
    ),
    Shoe(
        id="salomon-xt-6-safari",
        name="Salomon XT-6 Safari",
        brand="Salomon",
        image_url="/shoes/salomon-xt-6-safari.png",
        v={"chunk": 0.62, "retro": 0.22, "warm": 0.74, "minimal": 0.30, "earthy": 0.76, "loud": 0.58, "techy": 0.92},
    ),
    Shoe(
        id="nike-air-max-1-crepe-hemp",
        name="Nike Air Max 1 Crepe Hemp",
        brand="Nike",
        image_url="/shoes/nike-air-max-1-crepe-hemp.png",
        v={"chunk": 0.50, "retro": 0.84, "warm": 0.82, "minimal": 0.58, "earthy": 0.90, "loud": 0.34, "techy": 0.22},
    ),
    Shoe(
        id="adidas-samba-wales-bonner-fox-brown",
        name="adidas Samba Wales Bonner Fox Brown",
        brand="adidas",
        image_url="/shoes/adidas-samba-wales-bonner-fox-brown.png",
        v={"chunk": 0.16, "retro": 0.90, "warm": 0.86, "minimal": 0.70, "earthy": 0.74, "loud": 0.42, "techy": 0.05},
    ),
    Shoe(
        id="reebok-club-c-85-vintage-chalk",
        name="Reebok Club C 85 Vintage Chalk",
        brand="Reebok",
        image_url="/shoes/reebok-club-c-85-vintage-chalk.png",
        v={"chunk": 0.22, "retro": 0.88, "warm": 0.68, "minimal": 0.88, "earthy": 0.54, "loud": 0.10, "techy": 0.02},
    ),
    Shoe(
        id="mizuno-wave-rider-10-silver-cloud",
        name="Mizuno Wave Rider 10 Silver Cloud",
        brand="Mizuno",
        image_url="/shoes/mizuno-wave-rider-10-silver-cloud.png",
        v={"chunk": 0.58, "retro": 0.52, "warm": 0.30, "minimal": 0.34, "earthy": 0.20, "loud": 0.44, "techy": 0.80},
    ),
    Shoe(
        id="hoka-tor-ultra-low-oat-milk",
        name="Hoka Tor Ultra Low Oat Milk",
        brand="Hoka",
        image_url="/shoes/hoka-tor-ultra-low-oat-milk.png",
        v={"chunk": 0.86, "retro": 0.28, "warm": 0.78, "minimal": 0.42, "earthy": 0.84, "loud": 0.36, "techy": 0.72},
    ),
    Shoe(
        id="clarks-wallabee-maple-suede",
        name="Clarks Wallabee Maple Suede",
        brand="Clarks",
        image_url="/shoes/clarks-wallabee-maple-suede.png",
        v={"chunk": 0.34, "retro": 0.82, "warm": 0.92, "minimal": 0.76, "earthy": 0.96, "loud": 0.16, "techy": 0.00},
    ),
    Shoe(
        id="on-cloudmonster-undyed-white",
        name="On Cloudmonster Undyed White",
        brand="On",
        image_url="/shoes/on-cloudmonster-undyed-white.png",
        v={"chunk": 0.78, "retro": 0.08, "warm": 0.36, "minimal": 0.64, "earthy": 0.22, "loud": 0.30, "techy": 0.88},
    ),
    Shoe(
        id="new-balance-9060-sea-salt",
        name="New Balance 9060 Sea Salt",
        brand="New Balance",
        image_url="/shoes/new-balance-9060-sea-salt.png",
        v={"chunk": 0.84, "retro": 0.56, "warm": 0.60, "minimal": 0.48, "earthy": 0.54, "loud": 0.40, "techy": 0.42},
    ),
    Shoe(
        id="nike-acg-mountain-fly-low-brown-basalt",
        name="Nike ACG Mountain Fly Low Brown Basalt",
        brand="Nike ACG",
        image_url="/shoes/nike-acg-mountain-fly-low-brown-basalt.png",
        v={"chunk": 0.72, "retro": 0.20, "warm": 0.80, "minimal": 0.28, "earthy": 0.88, "loud": 0.54, "techy": 0.86},
    ),
    Shoe(
        id="puma-palermo-vine-clementine",
        name="Puma Palermo Vine Clementine",
        brand="Puma",
        image_url="/shoes/puma-palermo-vine-clementine.png",
        v={"chunk": 0.20, "retro": 0.86, "warm": 0.76, "minimal": 0.54, "earthy": 0.46, "loud": 0.66, "techy": 0.04},
    ),
    Shoe(
        id="merrell-moab-3-taupe",
        name="Merrell Moab 3 Taupe",
        brand="Merrell",
        image_url="/shoes/merrell-moab-3-taupe.png",
        v={"chunk": 0.66, "retro": 0.38, "warm": 0.78, "minimal": 0.46, "earthy": 0.92, "loud": 0.18, "techy": 0.58},
    ),
    Shoe(
        id="maison-margiela-replica-gat-cream",
        name="Maison Margiela Replica GAT Cream",
        brand="Maison Margiela",
        image_url="/shoes/maison-margiela-replica-gat-cream.png",
        v={"chunk": 0.18, "retro": 0.78, "warm": 0.64, "minimal": 0.82, "earthy": 0.48, "loud": 0.20, "techy": 0.02},
    ),

    # ── New Balance ─────────────────────────────────────────────────────────
    Shoe(
        id="nb-574-grey-day",
        name="New Balance 574 Grey Day",
        brand="New Balance",
        notes="The everyday classic. Low-key, warm, eternally correct.",
        image_url=_p("8a7f72", "NB+574+Grey+Day"),
        v={"chunk": 0.48, "retro": 0.84, "warm": 0.62, "minimal": 0.66, "earthy": 0.58, "loud": 0.14, "techy": 0.10},
    ),
    Shoe(
        id="nb-993-grey-made-in-usa",
        name="New Balance 993 Grey Made in USA",
        brand="New Balance",
        notes="Dad shoe royalty. The shoe Steve Jobs wore daily.",
        image_url=_p("9e9e9e", "NB+993+Grey"),
        v={"chunk": 0.76, "retro": 0.72, "warm": 0.52, "minimal": 0.44, "earthy": 0.42, "loud": 0.12, "techy": 0.22},
    ),
    Shoe(
        id="nb-2002r-sea-salt",
        name="New Balance 2002R Sea Salt",
        brand="New Balance",
        notes="Protection Pack vibes. Muted, technical, deeply wearable.",
        image_url=_p("d4cfc4", "NB+2002R+Sea+Salt"),
        v={"chunk": 0.70, "retro": 0.60, "warm": 0.56, "minimal": 0.52, "earthy": 0.50, "loud": 0.22, "techy": 0.62},
    ),
    Shoe(
        id="nb-1906r-forest-green",
        name="New Balance 1906R Forest Green",
        brand="New Balance",
        notes="Gorpcore-adjacent runner with serious presence.",
        image_url=_p("4a6741", "NB+1906R+Forest"),
        v={"chunk": 0.74, "retro": 0.48, "warm": 0.60, "minimal": 0.38, "earthy": 0.78, "loud": 0.36, "techy": 0.74},
    ),

    # ── Nike ────────────────────────────────────────────────────────────────
    Shoe(
        id="nike-dunk-low-panda",
        name="Nike Dunk Low Panda",
        brand="Nike",
        notes="The silhouette that broke the internet. Clean, iconic.",
        image_url=_p("1a1a1a", "Dunk+Low+Panda"),
        v={"chunk": 0.38, "retro": 0.78, "warm": 0.30, "minimal": 0.72, "earthy": 0.20, "loud": 0.42, "techy": 0.12},
    ),
    Shoe(
        id="nike-air-force-1-triple-white",
        name="Nike Air Force 1 '07 Triple White",
        brand="Nike",
        notes="The blank canvas. Timeless in a way that defies logic.",
        image_url=_p("f5f5f5", "AF1+Triple+White"),
        v={"chunk": 0.50, "retro": 0.82, "warm": 0.40, "minimal": 0.86, "earthy": 0.22, "loud": 0.10, "techy": 0.08},
    ),
    Shoe(
        id="nike-air-max-97-silver-bullet",
        name="Nike Air Max 97 Silver Bullet",
        brand="Nike",
        notes="Ripple waves and visible air. Loud in the best way.",
        image_url=_p("c0c0c0", "Air+Max+97+Silver"),
        v={"chunk": 0.58, "retro": 0.72, "warm": 0.44, "minimal": 0.22, "earthy": 0.18, "loud": 0.82, "techy": 0.56},
    ),
    Shoe(
        id="nike-killshot-2-leather",
        name="Nike Killshot 2 Leather",
        brand="Nike",
        notes="Quiet, preppy, clean. The anti-hype sneaker.",
        image_url=_p("e8e0d4", "Killshot+2"),
        v={"chunk": 0.18, "retro": 0.86, "warm": 0.62, "minimal": 0.90, "earthy": 0.44, "loud": 0.06, "techy": 0.04},
    ),
    Shoe(
        id="nike-pegasus-trail-5-gore-tex",
        name="Nike Pegasus Trail 5 GORE-TEX",
        brand="Nike",
        notes="Weatherproof trail runner. All-terrain, no excuses.",
        image_url=_p("3d5a3e", "Peg+Trail+5+GTX"),
        v={"chunk": 0.60, "retro": 0.12, "warm": 0.56, "minimal": 0.36, "earthy": 0.72, "loud": 0.30, "techy": 0.92},
    ),

    # ── adidas ──────────────────────────────────────────────────────────────
    Shoe(
        id="adidas-samba-og-white-gum",
        name="adidas Samba OG White Gum",
        brand="adidas",
        notes="Football flats turned cult streetwear staple.",
        image_url=_p("f0ece4", "Samba+OG+White+Gum"),
        v={"chunk": 0.14, "retro": 0.92, "warm": 0.72, "minimal": 0.78, "earthy": 0.58, "loud": 0.18, "techy": 0.04},
    ),
    Shoe(
        id="adidas-gazelle-bold-collegiate-green",
        name="adidas Gazelle Bold Collegiate Green",
        brand="adidas",
        notes="Platform Gazelle. Retro silhouette, elevated stance.",
        image_url=_p("2d5016", "Gazelle+Bold+Green"),
        v={"chunk": 0.44, "retro": 0.88, "warm": 0.62, "minimal": 0.64, "earthy": 0.52, "loud": 0.46, "techy": 0.04},
    ),
    Shoe(
        id="adidas-sl-72-og-cream",
        name="adidas SL 72 OG Cream",
        brand="adidas",
        notes="Pre-NMD running heritage. Slim, fast-looking, understated.",
        image_url=_p("e8e2d6", "SL+72+OG+Cream"),
        v={"chunk": 0.24, "retro": 0.90, "warm": 0.68, "minimal": 0.76, "earthy": 0.44, "loud": 0.14, "techy": 0.16},
    ),
    Shoe(
        id="adidas-campus-00s-wonder-white",
        name="adidas Campus 00s Wonder White",
        brand="adidas",
        notes="Low profile suede. Skate-adjacent, effortlessly cool.",
        image_url=_p("ede8e0", "Campus+00s+White"),
        v={"chunk": 0.20, "retro": 0.86, "warm": 0.64, "minimal": 0.74, "earthy": 0.48, "loud": 0.20, "techy": 0.02},
    ),

    # ── ASICS ───────────────────────────────────────────────────────────────
    Shoe(
        id="asics-gel-nimbus-9-sage",
        name="ASICS Gel-Nimbus 9 Sage",
        brand="ASICS",
        notes="Muted olive runner. The shoe that started the vintage ASICS wave.",
        image_url=_p("7a8c6e", "Gel+Nimbus+9+Sage"),
        v={"chunk": 0.64, "retro": 0.68, "warm": 0.58, "minimal": 0.38, "earthy": 0.64, "loud": 0.32, "techy": 0.70},
    ),
    Shoe(
        id="asics-gel-1130-cream-white",
        name="ASICS Gel-1130 Cream White",
        brand="ASICS",
        notes="Y2K runner energy. Chunky, creamy, very right now.",
        image_url=_p("d8d2c4", "Gel+1130+Cream"),
        v={"chunk": 0.72, "retro": 0.66, "warm": 0.58, "minimal": 0.34, "earthy": 0.38, "loud": 0.40, "techy": 0.68},
    ),
    Shoe(
        id="asics-gt-2160-birch-forest",
        name="ASICS GT-2160 Birch Forest",
        brand="ASICS",
        notes="Outdoor-coded colourway on a clean 2000s running silhouette.",
        image_url=_p("5c6b4a", "GT-2160+Forest"),
        v={"chunk": 0.54, "retro": 0.60, "warm": 0.66, "minimal": 0.46, "earthy": 0.72, "loud": 0.28, "techy": 0.62},
    ),

    # ── Vans ────────────────────────────────────────────────────────────────
    Shoe(
        id="vans-old-skool-black-white",
        name="Vans Old Skool Black White",
        brand="Vans",
        notes="The OG skate shoe. Never not in style.",
        image_url=_p("1c1c1c", "Vans+Old+Skool"),
        v={"chunk": 0.24, "retro": 0.84, "warm": 0.30, "minimal": 0.76, "earthy": 0.28, "loud": 0.18, "techy": 0.04},
    ),
    Shoe(
        id="vans-vault-og-era-lx-khaki",
        name="Vans Vault OG Era LX Khaki",
        brand="Vans",
        notes="Premium suede Era. Low-key flex, military-adjacent tone.",
        image_url=_p("b5a882", "Vans+Era+LX+Khaki"),
        v={"chunk": 0.18, "retro": 0.82, "warm": 0.74, "minimal": 0.78, "earthy": 0.68, "loud": 0.10, "techy": 0.02},
    ),

    # ── Converse ────────────────────────────────────────────────────────────
    Shoe(
        id="converse-chuck-70-natural-ivory",
        name="Converse Chuck 70 Natural Ivory",
        brand="Converse",
        notes="Aged canvas high-top. The original minimalist sneaker.",
        image_url=_p("f2ede0", "Chuck+70+Ivory"),
        v={"chunk": 0.16, "retro": 0.92, "warm": 0.66, "minimal": 0.90, "earthy": 0.48, "loud": 0.08, "techy": 0.00},
    ),
    Shoe(
        id="converse-chuck-70-de-luxe-heel-black",
        name="Converse Chuck 70 De Luxe Heel Black",
        brand="Converse",
        notes="Platform sole, premium leather. Chuck for the fashion crowd.",
        image_url=_p("1a1a1a", "Chuck+70+Platform"),
        v={"chunk": 0.42, "retro": 0.86, "warm": 0.28, "minimal": 0.72, "earthy": 0.26, "loud": 0.38, "techy": 0.02},
    ),

    # ── Salomon ─────────────────────────────────────────────────────────────
    Shoe(
        id="salomon-xt-6-vanilla-ice",
        name="Salomon XT-6 Vanilla Ice",
        brand="Salomon",
        notes="Tonal cream on a technical trail chassis. Gorpcore at its cleanest.",
        image_url=_p("e8e0d0", "XT-6+Vanilla+Ice"),
        v={"chunk": 0.64, "retro": 0.18, "warm": 0.70, "minimal": 0.56, "earthy": 0.58, "loud": 0.30, "techy": 0.94},
    ),
    Shoe(
        id="salomon-speedcross-6-black",
        name="Salomon Speedcross 6 Black",
        brand="Salomon",
        notes="Aggressive trail lug. Built for mud, worn on city streets.",
        image_url=_p("1a1a1a", "Speedcross+6"),
        v={"chunk": 0.68, "retro": 0.06, "warm": 0.24, "minimal": 0.28, "earthy": 0.50, "loud": 0.52, "techy": 0.96},
    ),

    # ── Birkenstock ─────────────────────────────────────────────────────────
    Shoe(
        id="birkenstock-boston-suede-mocha",
        name="Birkenstock Boston Suede Mocha",
        brand="Birkenstock",
        notes="The clog that conquered fashion week.",
        image_url=_p("8b6f4e", "Boston+Mocha"),
        v={"chunk": 0.46, "retro": 0.70, "warm": 0.90, "minimal": 0.62, "earthy": 0.96, "loud": 0.12, "techy": 0.00},
    ),
    Shoe(
        id="birkenstock-arizona-big-buckle-shearling",
        name="Birkenstock Arizona Big Buckle Shearling",
        brand="Birkenstock",
        notes="Cozy, earthy, anti-trend. The shoe your therapist wears.",
        image_url=_p("c9a87c", "Arizona+Shearling"),
        v={"chunk": 0.40, "retro": 0.66, "warm": 0.94, "minimal": 0.58, "earthy": 0.98, "loud": 0.08, "techy": 0.00},
    ),

    # ── Fear of God / Essentials ─────────────────────────────────────────────
    Shoe(
        id="fog-athletics-runner-off-white",
        name="Fear of God Athletics Runner Off White",
        brand="Fear of God",
        notes="Deconstructed luxury runner. Elevated and muted.",
        image_url=_p("e0dbd2", "FOG+Runner"),
        v={"chunk": 0.72, "retro": 0.30, "warm": 0.58, "minimal": 0.68, "earthy": 0.40, "loud": 0.24, "techy": 0.66},
    ),

    # ── Hoka ────────────────────────────────────────────────────────────────
    Shoe(
        id="hoka-clifton-9-eggnog",
        name="Hoka Clifton 9 Eggnog",
        brand="Hoka",
        notes="Max cushion road runner. Feels like running on a cloud.",
        image_url=_p("d4c9b0", "Clifton+9+Eggnog"),
        v={"chunk": 0.88, "retro": 0.14, "warm": 0.72, "minimal": 0.50, "earthy": 0.48, "loud": 0.22, "techy": 0.80},
    ),
    Shoe(
        id="hoka-speedgoat-5-wide-beet",
        name="Hoka Speedgoat 5 Beet Root",
        brand="Hoka",
        notes="Trail burner. Maximum grip, aggressive colorway.",
        image_url=_p("8b2252", "Speedgoat+5"),
        v={"chunk": 0.80, "retro": 0.08, "warm": 0.48, "minimal": 0.24, "earthy": 0.54, "loud": 0.72, "techy": 0.88},
    ),

    # ── On Running ──────────────────────────────────────────────────────────
    Shoe(
        id="on-cloudstratus-meadow-sage",
        name="On Cloudstratus Meadow Sage",
        brand="On",
        notes="Double cloud layer. Earthy green, borderline trail-coded.",
        image_url=_p("6b8c6b", "Cloudstratus+Sage"),
        v={"chunk": 0.82, "retro": 0.10, "warm": 0.54, "minimal": 0.44, "earthy": 0.60, "loud": 0.26, "techy": 0.90},
    ),

    # ── Saucony ─────────────────────────────────────────────────────────────
    Shoe(
        id="saucony-shadow-6000-tan-gum",
        name="Saucony Shadow 6000 Tan Gum",
        brand="Saucony",
        notes="80s running archive. The sleeper pick among vintage runners.",
        image_url=_p("c4a97a", "Shadow+6000+Tan"),
        v={"chunk": 0.54, "retro": 0.86, "warm": 0.76, "minimal": 0.48, "earthy": 0.66, "loud": 0.28, "techy": 0.42},
    ),
    Shoe(
        id="saucony-jazz-original-cream-navy",
        name="Saucony Jazz Original Cream Navy",
        brand="Saucony",
        notes="Original 1981 running silhouette. Clean, retro, unpretentious.",
        image_url=_p("2a3f6b", "Jazz+Original"),
        v={"chunk": 0.36, "retro": 0.90, "warm": 0.56, "minimal": 0.62, "earthy": 0.44, "loud": 0.22, "techy": 0.18},
    ),

    # ── Brooks ──────────────────────────────────────────────────────────────
    Shoe(
        id="brooks-ghost-15-oyster-black",
        name="Brooks Ghost 15 Oyster Black",
        brand="Brooks",
        notes="The ghost of sensible running shoes. Quiet and reliable.",
        image_url=_p("c8c0b8", "Ghost+15+Oyster"),
        v={"chunk": 0.60, "retro": 0.30, "warm": 0.48, "minimal": 0.54, "earthy": 0.36, "loud": 0.14, "techy": 0.72},
    ),

    # ── Puma ────────────────────────────────────────────────────────────────
    Shoe(
        id="puma-suede-classic-deep-olive",
        name="Puma Suede Classic Deep Olive",
        brand="Puma",
        notes="Suede-and-gum combo. The OG B-boy sneaker, now gorpcore.",
        image_url=_p("4a5c3a", "Puma+Suede+Olive"),
        v={"chunk": 0.22, "retro": 0.88, "warm": 0.70, "minimal": 0.68, "earthy": 0.64, "loud": 0.20, "techy": 0.02},
    ),
    Shoe(
        id="puma-speedcat-og-black-gold",
        name="Puma Speedcat OG Black Gold",
        brand="Puma",
        notes="Racing flat energy. Low and sleek with motorsport DNA.",
        image_url=_p("1a1a1a", "Speedcat+OG"),
        v={"chunk": 0.12, "retro": 0.84, "warm": 0.48, "minimal": 0.72, "earthy": 0.22, "loud": 0.52, "techy": 0.36},
    ),

    # ── Common Projects ──────────────────────────────────────────────────────
    Shoe(
        id="common-projects-achilles-low-white",
        name="Common Projects Achilles Low White",
        brand="Common Projects",
        notes="The benchmark for minimalism. $500 of barely-there shoe.",
        image_url=_p("f5f5f0", "Achilles+Low"),
        v={"chunk": 0.12, "retro": 0.60, "warm": 0.44, "minimal": 0.98, "earthy": 0.26, "loud": 0.04, "techy": 0.02},
    ),

    # ── Merrell ─────────────────────────────────────────────────────────────
    Shoe(
        id="merrell-jungle-moc-espresso",
        name="Merrell Jungle Moc Espresso",
        brand="Merrell",
        notes="Slip-on trail hybrid. The comfort shoe that got cool.",
        image_url=_p("5c3d1e", "Jungle+Moc"),
        v={"chunk": 0.48, "retro": 0.56, "warm": 0.84, "minimal": 0.58, "earthy": 0.90, "loud": 0.10, "techy": 0.38},
    ),

    # ── Reebok ──────────────────────────────────────────────────────────────
    Shoe(
        id="reebok-freestyle-hi-chalk",
        name="Reebok Freestyle Hi Chalk",
        brand="Reebok",
        notes="The original aerobics shoe. Quiet, feminine, retro.",
        image_url=_p("f0ece6", "Freestyle+Hi+Chalk"),
        v={"chunk": 0.26, "retro": 0.90, "warm": 0.62, "minimal": 0.84, "earthy": 0.40, "loud": 0.10, "techy": 0.02},
    ),
    Shoe(
        id="reebok-answer-iv-og-allen-iverson",
        name="Reebok Answer IV OG",
        brand="Reebok",
        notes="Allen Iverson's signature. Maximum 2000s energy.",
        image_url=_p("1a2a6b", "Answer+IV+OG"),
        v={"chunk": 0.58, "retro": 0.76, "warm": 0.36, "minimal": 0.22, "earthy": 0.14, "loud": 0.84, "techy": 0.60},
    ),

    # ── Mizuno ──────────────────────────────────────────────────────────────
    Shoe(
        id="mizuno-sky-medal-white-silver",
        name="Mizuno Sky Medal White Silver",
        brand="Mizuno",
        notes="Track-inspired, minimal, slightly futuristic.",
        image_url=_p("c8ccd4", "Sky+Medal+Silver"),
        v={"chunk": 0.38, "retro": 0.56, "warm": 0.28, "minimal": 0.72, "earthy": 0.16, "loud": 0.36, "techy": 0.74},
    ),

    # ── New Balance (more) ───────────────────────────────────────────────────
    Shoe(
        id="nb-530-white-silver",
        name="New Balance 530 White Silver",
        brand="New Balance",
        notes="The 90s runner making its comeback. Techy meets retro.",
        image_url=_p("dde0e4", "NB+530+Silver"),
        v={"chunk": 0.60, "retro": 0.66, "warm": 0.36, "minimal": 0.44, "earthy": 0.24, "loud": 0.44, "techy": 0.70},
    ),
    Shoe(
        id="nb-610v1-mushroom",
        name="New Balance 610v1 Mushroom",
        brand="New Balance",
        notes="Trail-meets-street in the most muted colorway possible.",
        image_url=_p("a89880", "NB+610+Mushroom"),
        v={"chunk": 0.68, "retro": 0.50, "warm": 0.76, "minimal": 0.46, "earthy": 0.82, "loud": 0.16, "techy": 0.60},
    ),

    # ── Nike (more) ──────────────────────────────────────────────────────────
    Shoe(
        id="nike-air-max-dn-black-volt",
        name="Nike Air Max DN Black Volt",
        brand="Nike",
        notes="Dynamic Air system. Future-facing, loud, unapologetic.",
        image_url=_p("1a1a1a", "Air+Max+DN+Volt"),
        v={"chunk": 0.74, "retro": 0.08, "warm": 0.22, "minimal": 0.18, "earthy": 0.10, "loud": 0.90, "techy": 0.92},
    ),
    Shoe(
        id="nike-air-huarache-white-crimson",
        name="Nike Air Huarache White Crimson",
        brand="Nike",
        notes="The neoprene sock runner. Weird and iconic since 1991.",
        image_url=_p("cc2200", "Huarache+Crimson"),
        v={"chunk": 0.42, "retro": 0.74, "warm": 0.46, "minimal": 0.34, "earthy": 0.20, "loud": 0.68, "techy": 0.50},
    ),

    # ── Salehe Bembury ───────────────────────────────────────────────────────
    Shoe(
        id="nb-2002r-salehe-bembury-yurt",
        name="New Balance 2002R Salehe Bembury 'Yurt'",
        brand="New Balance",
        notes="Salehe's fingerprint ripple outsole on a muted earth palette.",
        image_url=_p("c4a882", "2002R+Yurt"),
        v={"chunk": 0.72, "retro": 0.58, "warm": 0.82, "minimal": 0.46, "earthy": 0.88, "loud": 0.40, "techy": 0.54},
    ),
    Shoe(
        id="crocs-salehe-bembury-pollex-clog-urchin",
        name="Crocs x Salehe Bembury Pollex Clog 'Urchin'",
        brand="Crocs",
        notes="The collaboration that shouldn't work and absolutely does.",
        image_url=_p("7a8c7a", "Pollex+Clog+Urchin"),
        v={"chunk": 0.70, "retro": 0.20, "warm": 0.62, "minimal": 0.30, "earthy": 0.74, "loud": 0.56, "techy": 0.18},
    ),

    # ── Yeezy ────────────────────────────────────────────────────────────────
    Shoe(
        id="adidas-yeezy-350-v2-natural",
        name="adidas Yeezy Boost 350 V2 Natural",
        brand="adidas",
        notes="Primeknit meets Boost. Divisive, influential, everywhere.",
        image_url=_p("d4c9b4", "Yeezy+350+Natural"),
        v={"chunk": 0.52, "retro": 0.22, "warm": 0.68, "minimal": 0.54, "earthy": 0.62, "loud": 0.36, "techy": 0.76},
    ),

    # ── Keen / Outdoor ───────────────────────────────────────────────────────
    Shoe(
        id="keen-jasper-bison-tortoise-shell",
        name="Keen Jasper Bison Tortoise Shell",
        brand="Keen",
        notes="Hiker-turned-street. The original ugly-cute outdoor shoe.",
        image_url=_p("7a5c3a", "Keen+Jasper"),
        v={"chunk": 0.62, "retro": 0.44, "warm": 0.80, "minimal": 0.28, "earthy": 0.92, "loud": 0.30, "techy": 0.48},
    ),

    # ── Clarks (more) ────────────────────────────────────────────────────────
    Shoe(
        id="clarks-desert-boot-beeswax",
        name="Clarks Desert Boot Beeswax",
        brand="Clarks",
        notes="The boot that Ivy League and hip-hop agreed on.",
        image_url=_p("a08060", "Desert+Boot+Beeswax"),
        v={"chunk": 0.28, "retro": 0.88, "warm": 0.90, "minimal": 0.74, "earthy": 0.94, "loud": 0.10, "techy": 0.00},
    ),
]
