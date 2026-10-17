"""AI-sökpaketet för nordwikpartners.se – lägger in strukturerad data (JSON-LD) och canonical.

Sajten är statisk HTML utan bygge. Skriptet kan köras om hur många gånger som helst:
blocket mellan <!-- ai-sok:start --> och <!-- ai-sok:slut --> skrivs om varje gång.

  python3 nordwik_aisok_bygg.py

Bara uppgifter som redan står synligt på sajten används. Registret under kansliet/register
byggs av ett annat verktyg och rörs inte här.
"""
import json, re, subprocess
from datetime import date
from pathlib import Path

ROT = Path(__file__).resolve().parent
BAS = "https://nordwikpartners.se"
ORG_ID = f"{BAS}/#org"
WEB_ID = f"{BAS}/#webbplats"

ORG = {
    "@type": "Organization",
    "@id": ORG_ID,
    "name": "Nordwik Partners",
    "url": f"{BAS}/",
    "logo": f"{BAS}/logo.svg",
    "description": "Nordwik Partners tar avstannade detaljplaner i mål, väcker outnyttjade byggrätter "
                   "och driver nya planbesked i Stockholms län.",
    "email": "kontakt@nordwikpartners.se",
    "telephone": "+46-70-532 36 83",
    "areaServed": {"@type": "AdministrativeArea", "name": "Stockholms län"},
    "knowsLanguage": "sv",
}
WEBSITE = {
    "@type": "WebSite",
    "@id": WEB_ID,
    "name": "Nordwik Partners",
    "url": f"{BAS}/",
    "inLanguage": "sv",
    "publisher": {"@id": ORG_ID},
}
REF_ORG = {"@id": ORG_ID}


def smula(*led):
    """BreadcrumbList. Sista ledet saknar adress (den aktuella sidan)."""
    items = []
    for i, (namn, url) in enumerate(led, 1):
        it = {"@type": "ListItem", "position": i, "name": namn}
        if url:
            it["item"] = url
        items.append(it)
    return {"@type": "BreadcrumbList", "itemListElement": items}


def sida(fil, namn, typ="WebPage"):
    return {"@type": typ, "@id": f"{BAS}/{fil}#sida", "url": f"{BAS}/{fil}", "name": namn,
            "inLanguage": "sv", "isPartOf": {"@id": WEB_ID}, "publisher": REF_ORG}


START = ("Startsida", f"{BAS}/")

SIDOR = {
    "index.html": {"canonical": f"{BAS}/", "graf": [ORG, WEBSITE, {
        "@type": "ProfessionalService",
        "@id": f"{BAS}/#detaljplaner",
        "name": "Nordwik Partners – detaljplaner och byggrätter",
        "url": f"{BAS}/",
        "description": "Avstannade detaljplaner, outnyttjade byggrätter och nya planbesked i Stockholms län. "
                       "Första steget är ett kostnadsfritt samtal.",
        "parentOrganization": REF_ORG,
        "areaServed": {"@type": "AdministrativeArea", "name": "Stockholms län"},
        "email": "kontakt@nordwikpartners.se",
        "telephone": "+46-70-532 36 83",
        "logo": f"{BAS}/logo.svg",
        "image": f"{BAS}/img/hero.jpg",
    }]},
    "sa-arbetar-vi.html": {"graf": [
        sida("sa-arbetar-vi.html", "Så arbetar vi"),
        smula(START, ("Så arbetar vi", None)),
        {"@type": "Service", "name": "Samtal", "serviceType": "Muntlig bedömning av detaljplan eller mark",
         "description": "En muntlig bedömning: är stoppet en räknefråga eller en förhandlingsfråga, och vad säger kommunens egna tal.",
         "provider": REF_ORG, "areaServed": {"@type": "AdministrativeArea", "name": "Stockholms län"},
         "offers": {"@type": "Offer", "price": "0", "priceCurrency": "SEK"}},
        {"@type": "Service", "name": "Stoppdiagnos", "serviceType": "Skriftligt underlag om stoppad detaljplan",
         "description": "Ett skriftligt underlag: vad stoppet beror på, kommunens uppmätta plandöd, vad marken bär och vad som krävs. "
                        "Fast pris. Avgiften räknas av om vi går vidare.",
         "provider": REF_ORG, "areaServed": {"@type": "AdministrativeArea", "name": "Stockholms län"}},
        {"@type": "Service", "name": "Partnerskap", "serviceType": "Projektledning av detaljplan till antagande",
         "description": "Vi driver planen i mål, med låst budget och rätt för båda parter att kliva av före samrådet. "
                        "Arvode och vinstdelning.",
         "provider": REF_ORG, "areaServed": {"@type": "AdministrativeArea", "name": "Stockholms län"}},
    ]},
    "case.html": {"graf": [sida("case.html", "Case"), smula(START, ("Case", None))]},
    "insikter.html": {"graf": [sida("insikter.html", "Insikter", "CollectionPage"), smula(START, ("Insikter", None))]},
    "plattformen.html": {"graf": [sida("plattformen.html", "Plattformen"), smula(START, ("Plattformen", None))]},
    "radarnatverket.html": {"graf": [sida("radarnatverket.html", "Radarnätverket"), smula(START, ("Radarnätverket", None))]},
    "insikt-55plus.html": {"graf": [
        {"@type": "Article", "@id": f"{BAS}/insikt-55plus.html#artikel", "url": f"{BAS}/insikt-55plus.html",
         "headline": "1,8 miljoner svenskar över 55 bor i eget hus. Nästan ingen av dem flyttar",
         "inLanguage": "sv", "author": REF_ORG, "publisher": REF_ORG, "image": f"{BAS}/img/hero.jpg",
         "isPartOf": {"@id": WEB_ID}},
        smula(START, ("Insikter", f"{BAS}/insikter.html"), ("Bostäder 55+", None))]},
    "insikt-datacenter.html": {"graf": [
        {"@type": "Article", "@id": f"{BAS}/insikt-datacenter.html#artikel", "url": f"{BAS}/insikt-datacenter.html",
         "headline": "Datacenteretableringar – vad krävs, var och till vilket pris",
         "inLanguage": "sv", "author": REF_ORG, "publisher": REF_ORG, "image": f"{BAS}/img/hero.jpg",
         "isPartOf": {"@id": WEB_ID}},
        smula(START, ("Insikter", f"{BAS}/insikter.html"), ("Datacenteretableringar", None))]},
    "kansliet/checklista.html": {"graf": [
        {"@type": "Article", "@id": f"{BAS}/kansliet/checklista.html#artikel", "url": f"{BAS}/kansliet/checklista.html",
         "headline": "Kassörens checklista inför stämman",
         "description": "Nitton punkter från årsskiftet till avierna efter stämman, med hänvisningar till lagen (1973:1150) "
                        "om förvaltning av samfälligheter.",
         "inLanguage": "sv", "author": {"@type": "Organization", "name": "Kansliet – Nordwik Partners"}},
        smula(("Kansliet", f"{BAS}/kansliet/"), ("Kassörens checklista inför stämman", None))]},
}


def offer(namn, pris, enhet, beskr):
    return {"@type": "Offer", "name": namn, "description": beskr, "priceCurrency": "SEK",
            "priceSpecification": {"@type": "UnitPriceSpecification", "price": pris, "priceCurrency": "SEK",
                                   "unitText": enhet, "valueAddedTaxIncluded": False}}


# Kansliet: samma uppgifter som förut, plus koppling till Nordwik Partners och priserna som står på sidan.
KANSLIET = {
    "@context": "https://schema.org",
    "@type": "AccountingService",
    "name": "Kansliet",
    "url": f"{BAS}/kansliet/",
    "description": "Bokföring och kansli för vägföreningar, samfälligheter, lantbruk, skog och hyreshus. "
                   "AI-agenter bokför varje natt, tre modeller granskar, en människa ansvarar.",
    "provider": {"@type": "Organization", "name": "Foodbergs Stockholm AB", "url": f"{BAS}/",
                 "taxID": "559518-4457", "email": "kansliet@nordwikpartners.se"},
    "brand": {"@type": "Brand", "name": "Nordwik Partners"},
    "areaServed": {"@type": "Country", "name": "Sverige"},
    "inLanguage": "sv",
    "makesOffer": [
        offer("Vägföreningar och samfälligheter", "2400", "per år",
              "Bokföring, avgiftsavier med OCR, avprickning av inbetalningar, påminnelser och ett färdigt stämmopaket. "
              "Upp till 100 medlemmar, därefter 10 kr per medlem."),
        offer("Lantbruk och skog", "625", "per månad", "Bokföringen gratis. Årsavslut, NE-bilaga och moms ingår."),
        offer("Hyreshus och lokaler", "625", "per månad", "Bokföringen gratis. Årsavslut och deklarationsbilaga ingår."),
    ],
}

BLOCK = re.compile(r"\n?<!-- ai-sok:start -->.*?<!-- ai-sok:slut -->\n?", re.S)


def jsonld(obj):
    return '<script type="application/ld+json">' + json.dumps(obj, ensure_ascii=False) + "</script>"


def skriv_block(fil, inre):
    p = ROT / fil
    h = BLOCK.sub("\n", p.read_text())
    h = h.replace("</head>", f"<!-- ai-sok:start -->\n{inre}\n<!-- ai-sok:slut -->\n</head>", 1)
    p.write_text(h)


def main():
    for fil, cfg in SIDOR.items():
        delar = []
        h = (ROT / fil).read_text()
        canon = cfg.get("canonical", f"{BAS}/{fil}")
        if 'rel="canonical"' not in BLOCK.sub("", h):
            delar.append(f'<link rel="canonical" href="{canon}">')
        delar.append(jsonld({"@context": "https://schema.org", "@graph": cfg["graf"]}))
        skriv_block(fil, "\n".join(delar))

    # Kansliet: byt ut det befintliga AccountingService-blocket mot det utökade.
    p = ROT / "kansliet/index.html"
    h = p.read_text()
    h2 = re.sub(r'<script type="application/ld\+json">\{"@context": "https://schema.org", "@type": "AccountingService".*?</script>',
                lambda m: jsonld(KANSLIET), h, count=1, flags=re.S)
    p.write_text(h2)

    # sitemap.xml: indexerade toppsidor med lastmod från git. Kansliet (noindex) tas inte med.
    rader = []
    for fil in ["index.html", "sa-arbetar-vi.html", "case.html", "insikter.html", "insikt-55plus.html",
                "insikt-datacenter.html", "plattformen.html", "radarnatverket.html"]:
        andrad = subprocess.run(["git", "diff", "--quiet", "HEAD", "--", fil], cwd=ROT).returncode != 0
        d = "" if andrad else subprocess.run(["git", "log", "-1", "--format=%ad", "--date=short", "--", fil],
                                             cwd=ROT, capture_output=True, text=True).stdout.strip()
        d = d or date.today().isoformat()
        loc = f"{BAS}/" if fil == "index.html" else f"{BAS}/{fil}"
        rader.append(f"  <url><loc>{loc}</loc><lastmod>{d}</lastmod></url>")
    (ROT / "sitemap.xml").write_text('<?xml version="1.0" encoding="UTF-8"?>\n'
                                     '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                                     + "\n".join(rader) + "\n</urlset>\n")
    bygg_flode()
    print("klart")


def tal(x):
    x = x.replace(" ", "").replace(" ", "")
    return None if x in ("–", "-", "") else int(x)


def bygg_flode():
    """data/register-lan.json: antal per län, hämtat ur tabellen på kansliet/register/ (samma siffror som sidan visar)."""
    h = (ROT / "kansliet/register/index.html").read_text()
    tabell = re.search(r"<table>.*?</table>", h, re.S).group(0)
    m = re.search(r"SCB:s allmänna företagsregister, hämtade (\d{4}-\d{2}-\d{2})", h)
    scb_datum = m.group(1)
    poster = []
    for slug, lan, samf, vag, dik in re.findall(
            r'<tr><td><a href="([^"]+)/">([^<]+)</a></td><td class="n">([^<]*)</td><td class="n">([^<]*)</td><td class="n">([^<]*)</td></tr>', tabell):
        poster.append({
            "lan": lan,
            "sida": f"{BAS}/kansliet/register/{slug}/",
            "samfallighetsforeningar": tal(samf),
            "vagforeningar": tal(vag),
            "dikningsforetag": tal(dik),
            "kallor": [
                {"uppgift": "samfallighetsforeningar, vagforeningar", "kalla": "SCB:s allmänna företagsregister", "hamtad": scb_datum},
                {"uppgift": "dikningsforetag", "kalla": "Länsstyrelsernas Vattenarkiv (öppna data)", "hamtad": None},
            ],
        })
    flode = {
        "namn": "Register över samfälligheter, vägföreningar och dikningsföretag – antal per län",
        "utgivare": "Kansliet – Nordwik Partners",
        "url": f"{BAS}/kansliet/register/",
        "schema": f"{BAS}/data/register-lan.schema.json",
        "licens_och_ansvar": "Privat tjänst från Nordwik Partners, inte en myndighet. Ingen juridisk rådgivning.",
        "anmarkningar": [
            "Dikningsföretag finns bara för de län där Länsstyrelsen har publicerat Vattenarkivet som öppna data (null = uppgift saknas).",
            "Vägföreningarna är bedömda ur namnet och omfattar alla föreningsformer. De som är samfällighetsföreningar räknas också bland samfälligheterna.",
            "Hämtningsdatum för Vattenarkivet anges inte på sajten och lämnas därför tomt.",
        ],
        "poster": poster,
    }
    (ROT / "data").mkdir(exist_ok=True)
    (ROT / "data/register-lan.json").write_text(json.dumps(flode, ensure_ascii=False, indent=2) + "\n")


if __name__ == "__main__":
    main()
