"""Tester för AI-sökpaketet på nordwikpartners.se (statisk sajt, inget bygge).

  python3 nordwik_aisok_test.py            -> filtester
  python3 nordwik_aisok_test.py --server   -> dessutom en lokal testserver på port 8737

Avslutar med felkod om något test fallerar.
"""
import html, json, random, re, socket, subprocess, sys, time, urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

ROT = Path(__file__).resolve().parent
BAS = "https://nordwikpartners.se"
PORT = 8737
fel = []

TOPPSIDOR = ["index.html", "sa-arbetar-vi.html", "case.html", "insikter.html", "insikt-55plus.html",
             "insikt-datacenter.html", "plattformen.html", "radarnatverket.html"]
KANSLIET = ["kansliet/index.html", "kansliet/checklista.html", "kansliet/register/index.html",
            "kansliet/register/guider/index.html", "kansliet/register/om-dikningsforetag/index.html"]
AI_BOTAR = ["GPTBot", "OAI-SearchBot", "ChatGPT-User", "ClaudeBot", "Claude-User", "Claude-SearchBot",
            "PerplexityBot", "Google-Extended", "Bingbot", "Applebot-Extended"]
TILLATNA_TYPER = {"Organization", "WebSite", "WebPage", "CollectionPage", "Article", "BreadcrumbList", "ListItem",
                  "ProfessionalService", "AccountingService", "Service", "Offer", "UnitPriceSpecification", "Brand",
                  "AdministrativeArea", "Country", "Place", "GeoCoordinates", "Dataset", "FAQPage", "Question", "Answer",
                  "DataDownload", "GovernmentOrganization", "LocalBusiness"}

# Samma förbjudna ord som fabrikskoll.py (läses därifrån om den finns).
try:
    sys.path.insert(0, str(Path.home() / "verket/fabrik"))
    from fabrikskoll import FORBJUDNA
except Exception:
    FORBJUDNA = re.compile(r"\b(bäst i test|testvinnare|vårt val|mest populär\w*|populärast\w*|topprankad\w*|nummer ett)\b", re.I)


def kontroll(villkor, text):
    if not villkor:
        fel.append(text)


def text(h):
    h = re.sub(r"<!--.*?-->|<script.*?</script>|<style.*?</style>", " ", h, flags=re.S | re.I)
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", h)))


def lokal_fil(url):
    """https://nordwikpartners.se/x/ -> Path till x/index.html (None om extern)."""
    if url.startswith(BAS):
        url = url[len(BAS):]
    if re.match(r"^[a-z]+:", url) or url.startswith("//"):
        return None
    url = url.split("#")[0].split("?")[0]
    if not url:
        return None
    p = ROT / url.lstrip("/")
    return p / "index.html" if (url.endswith("/") or p.is_dir()) else p


def noder(obj):
    if isinstance(obj, dict):
        yield obj
        for v in obj.values():
            yield from noder(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from noder(v)


def jsonld(fil):
    h = (ROT / fil).read_text()
    block = re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S)
    ut = []
    for b in block:
        try:
            ut.append(json.loads(b))
        except json.JSONDecodeError as e:
            fel.append(f"{fil}: ogiltig JSON-LD ({e})")
    return ut


def test_jsonld():
    alla_id = {}
    refs = []
    for fil in TOPPSIDOR + KANSLIET:
        data = jsonld(fil)
        kontroll(data, f"{fil}: saknar JSON-LD")
        for d in data:
            for n in noder(d):
                t = n.get("@type")
                for typ in (t if isinstance(t, list) else [t] if t else []):
                    kontroll(typ in TILLATNA_TYPER, f"{fil}: okänd/otillåten schema-typ {typ}")
                    kontroll(typ not in ("Review", "AggregateRating"), f"{fil}: betyg/recension i JSON-LD")
                kontroll("aggregateRating" not in n and "review" not in n, f"{fil}: betyg/recension i JSON-LD")
                if "@id" in n and len(n) > 1:
                    alla_id[n["@id"]] = n
                elif "@id" in n:
                    refs.append((fil, n["@id"]))
                if t == "BreadcrumbList":
                    pos = [i.get("position") for i in n["itemListElement"]]
                    kontroll(pos == list(range(1, len(pos) + 1)), f"{fil}: brödsmulor i fel ordning")
                if t in ("Organization", "AccountingService", "ProfessionalService", "WebSite", "Article", "Service"):
                    kontroll(n.get("name") or n.get("headline"), f"{fil}: {t} saknar namn")
                for k in ("url", "item", "logo", "image"):
                    v = n.get(k)
                    if isinstance(v, str) and v.startswith(BAS):
                        p = lokal_fil(v)
                        kontroll(p is None or p.exists(), f"{fil}: {k} pekar på saknad sida {v}")
    for fil, ref in refs:
        kontroll(ref in alla_id, f"{fil}: hänvisning {ref} saknar definition")
    org = alla_id.get(f"{BAS}/#org", {})
    kontroll(org.get("@type") == "Organization", "index.html: Organization saknas")
    start = text((ROT / "index.html").read_text())
    for nyckel in ("name", "email"):
        kontroll(org.get(nyckel, "") in start, f"Organization.{nyckel} står inte på startsidan")
    kontroll("070-532 36 83" in start, "telefonnumret i Organization står inte på startsidan")
    # Stickprov i registret (byggs av annat verktyg): JSON-LD ska vara giltig JSON.
    reg = list((ROT / "kansliet/register").rglob("index.html"))
    random.seed(17)
    for p in random.sample(reg, min(300, len(reg))):
        jsonld(str(p.relative_to(ROT)))


def test_llms():
    p = ROT / "llms.txt"
    kontroll(p.exists(), "llms.txt saknas")
    if not p.exists():
        return
    t = p.read_text()
    kontroll(t.startswith("# Nordwik Partners"), "llms.txt ska börja med '# Nordwik Partners'")
    kontroll("<html" not in t.lower() and "<div" not in t.lower(), "llms.txt innehåller HTML")
    kontroll("/data/register-lan.json" in t, "llms.txt länkar inte till flödet")
    for url in re.findall(r"\]\((https?://[^)]+)\)", t):
        lf = lokal_fil(url)
        kontroll(lf is not None and lf.exists(), f"llms.txt: länken {url} finns inte på sajten")
        if lf is not None and lf.suffix == ".html" and lf.exists():
            kontroll('content="noindex' not in lf.read_text(), f"llms.txt länkar till dold sida {url}")
    f = FORBJUDNA.search(t)
    kontroll(not f, f"llms.txt: förbjudet ord {f and f.group(0)}")


def test_robots():
    t = (ROT / "robots.txt").read_text()
    for bot in AI_BOTAR:
        kontroll(re.search(rf"User-agent: {re.escape(bot)}\nAllow: /\n", t), f"robots.txt välkomnar inte {bot}")
    kontroll("Disallow: /demo/" in t, "robots.txt: spärren för /demo/ har försvunnit")
    kontroll(not re.search(r"^Disallow: /\s*$", t, re.M), "robots.txt stänger hela sajten")
    for s in re.findall(r"^Sitemap: (\S+)", t, re.M):
        kontroll(lokal_fil(s).exists(), f"robots.txt: sitemap {s} saknas")


def test_sitemap():
    ns = {"s": "http://www.sitemaps.org/schemas/sitemap/0.9"}
    rot = ET.parse(ROT / "sitemap.xml").getroot()
    locs = rot.findall("s:url", ns)
    kontroll(len(locs) < 50000, "sitemap.xml har över 50 000 adresser")
    for u in locs:
        loc = u.find("s:loc", ns).text
        lm = u.find("s:lastmod", ns)
        kontroll(lm is not None and re.match(r"\d{4}-\d{2}-\d{2}$", lm.text), f"sitemap: {loc} saknar lastmod")
        p = lokal_fil(loc)
        kontroll(p and p.exists(), f"sitemap: {loc} finns inte")
        if p and p.exists():
            kontroll('content="noindex' not in p.read_text(), f"sitemap: {loc} är noindex")
    for fil in TOPPSIDOR:
        loc = f"{BAS}/" if fil == "index.html" else f"{BAS}/{fil}"
        kontroll(any(u.find("s:loc", ns).text == loc for u in locs), f"sitemap saknar {loc}")


def validera(v, s, vag="$"):
    """Liten JSON Schema-validering (type, required, properties, items, minItems, minimum, pattern)."""
    typer = s.get("type")
    if typer:
        typer = typer if isinstance(typer, list) else [typer]
        ok = {"object": dict, "array": list, "string": str, "null": type(None)}
        passar = any((t == "integer" and isinstance(v, int) and not isinstance(v, bool)) or
                     (t in ok and isinstance(v, ok[t])) for t in typer)
        if not passar:
            return [f"{vag}: fel typ"]
    f = []
    if isinstance(v, dict):
        f += [f"{vag}: saknar {k}" for k in s.get("required", []) if k not in v]
        for k, ss in s.get("properties", {}).items():
            if k in v:
                f += validera(v[k], ss, f"{vag}.{k}")
    if isinstance(v, list):
        if len(v) < s.get("minItems", 0):
            f.append(f"{vag}: för få poster")
        for i, x in enumerate(v):
            f += validera(x, s.get("items", {}), f"{vag}[{i}]")
    if isinstance(v, int) and "minimum" in s and v < s["minimum"]:
        f.append(f"{vag}: under minimum")
    if isinstance(v, str) and "pattern" in s and not re.search(s["pattern"], v):
        f.append(f"{vag}: matchar inte mönstret")
    return f


def test_flode():
    d = json.loads((ROT / "data/register-lan.json").read_text())
    s = json.loads((ROT / "data/register-lan.schema.json").read_text())
    for x in validera(d, s):
        fel.append(f"register-lan.json: {x}")
    sida = text((ROT / "kansliet/register/index.html").read_text())
    for nyckel, ord_ in (("samfallighetsforeningar", "samfällighetsföreningar"), ("vagforeningar", "vägföreningar"),
                         ("dikningsforetag", "dikningsföretag")):
        summa = sum(p[nyckel] or 0 for p in d["poster"])
        siffra = f"{summa:,}".replace(",", " ")
        kontroll(f"{siffra} {ord_}" in sida, f"register-lan.json: summan {nyckel}={summa} stämmer inte med sidan")
    for p in d["poster"]:
        kontroll(lokal_fil(p["sida"]).exists(), f"register-lan.json: {p['sida']} finns inte")


def test_fragor():
    d = json.loads((ROT / "data/ai-fragor.json").read_text())["fragor"]
    kontroll(30 <= len(d) <= 50, f"ai-fragor.json: {len(d)} frågor, ska vara 30–50")
    for q in d:
        kontroll(q.get("fraga") and q.get("avsikt"), "ai-fragor.json: fråga utan text eller avsikt")
        if q["sida"]:
            p = lokal_fil(q["sida"])
            kontroll(p and p.exists(), f"ai-fragor.json: {q['sida']} finns inte")
            if p and p.exists():
                dold = 'content="noindex' in p.read_text()
                kontroll(dold == ("dold" in q["status"]), f"ai-fragor.json: fel status för {q['sida']}")
        else:
            kontroll(q["status"] == "data saknas", f"ai-fragor.json: '{q['fraga']}' saknar sida men har status {q['status']}")
    json.loads((ROT / "data/ai-synlighet.json").read_text())


def test_sidor():
    for fil in TOPPSIDOR + KANSLIET:
        h = (ROT / fil).read_text()
        t = text(h)
        f = FORBJUDNA.search(t)
        kontroll(not f, f"{fil}: förbjudet ord {f and f.group(0)}")
        kontroll(not re.search(r'<input[^>]+type="email"', h, re.I), f"{fil}: e-postfält")
        for href in re.findall(r'(?:href|src)="([^"]+)"', h):
            if href.startswith(("mailto:", "tel:", "#", "javascript:")):
                continue
            p = lokal_fil(href if href.startswith(("/", "http")) else str((ROT / fil).parent.relative_to(ROT) / href))
            kontroll(p is None or p.exists(), f"{fil}: trasig intern länk {href}")


def test_server():
    with socket.socket() as s:
        kontroll(s.connect_ex(("127.0.0.1", PORT)) != 0, f"port {PORT} är upptagen")
    proc = subprocess.Popen([sys.executable, "-m", "http.server", str(PORT), "--bind", "127.0.0.1", "-d", str(ROT)],
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        time.sleep(1)
        for vag in ("/llms.txt", "/robots.txt", "/sitemap.xml", "/data/register-lan.json", "/", "/kansliet/"):
            with urllib.request.urlopen(f"http://127.0.0.1:{PORT}{vag}") as r:
                kontroll(r.status == 200, f"testserver: {vag} gav {r.status}")
    finally:
        proc.terminate()


if __name__ == "__main__":
    tester = [test_jsonld, test_llms, test_robots, test_sitemap, test_flode, test_fragor, test_sidor]
    if "--server" in sys.argv:
        tester.append(test_server)
    for t in tester:
        fore = len(fel)
        t()
        print(f"{'OK ' if len(fel) == fore else 'FEL'} {t.__name__}")
    for f in fel:
        print("  -", f)
    sys.exit(1 if fel else 0)
