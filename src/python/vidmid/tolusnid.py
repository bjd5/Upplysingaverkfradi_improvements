"""Skrifar viðmiðið út sem markdown sem manneskja les.

vidmid.json er fyrir próf; þetta er fyrir þann sem byggir nýju síðuna. Efnið er
það sama. Töflurnar eru klofnar eftir síðum NÝJU síðunnar (docs/endurbygging.md,
kafli 3) fremur en eftir skráaheitum þeirrar gömlu: sá sem byggir
web/sidur/hagstofan.html vill fá viðmiðið sitt í einni skrá, ekki blaðað upp úr
528 línu töflu. Það heldur líka hverri skrá undir 300 línum (regla 6).
"""

from __future__ import annotations

from pathlib import Path

# Hópur = ein síða nýju síðunnar. Fyrsta síðan í hverri röð er kjarnasíðan.
HOPAR: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    ("skjalftavaktin", "Skjálftavaktin — jarðskjálftar á Reykjanesi",
     ("capstone/earthquakes.html",)),
    ("hagstofan", "Hagstofan — brautskráning af háskólastigi",
     ("lotur/vefthjonustur/hagstofan.html",)),
    ("vedurstodvar", "Veðurstöðvar Veðurstofunnar",
     ("lotur/vefthjonustur/vedurstofan.html",)),
    ("mbl-regex", "mbl.is — reglulegar segðir á fréttaforsíðu",
     ("lotur/regex/mbl.html", "lotur/regex/index.html")),
    ("phoebe-tolfraedi", "Phoebe — plass, nærvera og tengsl",
     ("friends/phoebe-statistics.html", "friends/index.html",
      "friends/phoebe-tribute.html")),
    ("phoebe-central-perk", "Phoebe — söngurinn í Central Perk",
     ("phoebe-central-perk.html",)),
)
UTAN = ("utan-umfangs", "Síður utan umfangs nýju síðunnar", ())
HAMARK_SAMHENGI = 110


def _flyja(texti: str | None) -> str:
    """Markdown-tafla brotnar á lóðréttu striki og nýlínu."""
    if not texti:
        return "—"
    return texti.replace("|", "\\|").replace("\n", " ").strip()


def _stytta(texti: str, hamark: int = HAMARK_SAMHENGI) -> str:
    texti = " ".join(texti.split())
    return texti if len(texti) <= hamark else texti[: hamark - 1] + "…"


def _stadur(t: dict) -> str:
    """Hvar talan stóð: töflusella, kaflaheiti eða flokkur."""
    if t["tafla"]:
        hlutar = [h for h in (t["lina"], t["sulka"]) if h]
        return _stytta(" · ".join([_stytta(t["tafla"], 40)] + hlutar), 70)
    if t["kafli"]:
        return _stytta(t["kafli"][-1], 70)
    return t["flokkur"]


def _tolutafla(tolur: list[dict]) -> list[str]:
    linur = ["| Tala | Eining | Tegund | Hvar | Samhengi |",
             "|---|---|---|---|---|"]
    for t in tolur:
        linur.append(
            f"| `{_flyja(t['texti'])}` | {_flyja(t['eining'])} | {t['tegund']} "
            f"| {_flyja(_stadur(t))} | {_flyja(_stytta(t['samhengi']))} |")
    return linur


def _hopaskra(heiti: str, sidur: tuple[str, ...], vidmid: dict) -> list[str]:
    tolur = [t for t in vidmid["gogn"] if t["visst"] and t["sida"] in sidur]
    lotur = {t["sida"]: t["lota"] for t in vidmid["gogn"] if t["sida"] in sidur}
    gagnadrifnar = {g["sida"]: g for g in vidmid["gagnadrifnar_sidur"]}
    linur = [f"# Viðmið — {heiti}", "",
             f"Afleidd skrá. Uppfært {vidmid['uppfaert']} af "
             "`src/python/vidmid/tolur.py`; **ekki handbreytt** (regla 10).",
             "", f"{len(tolur)} efnislegar tölur úr "
             f"{len([s for s in sidur if s in lotur])} síðum gamla verkefnisins.",
             ""]
    for sida in sidur:
        eigin = [t for t in tolur if t["sida"] == sida]
        linur += [f"## `{sida}`", "",
                  f"Byggingarlota `{lotur.get(sida) or 'óþekkt'}`. "
                  f"{len(eigin)} efnislegar tölur.", ""]
        if sida in gagnadrifnar:
            g = gagnadrifnar[sida]
            linur += [f"> **Tölurnar standa ekki í HTML-inu.** {g['skyring']}",
                      ">", "> Viðmiðið fyrir þessa síðu er gagnaskrárnar:", ">"]
            linur += [f"> - `{s}`" for s in g["gagnaskrar"]]
            linur += [""]
        linur += _tolutafla(eigin) if eigin else ["*Engin efnisleg tala.*"]
        linur += [""]
    return linur


def _yfirlit(vidmid: dict) -> list[str]:
    s = vidmid["samantekt"]
    linur = [
        "# Viðmiðstölur gamla verkefnisins", "",
        "Hver tala sem byggða gamla síðan birtir, vélleshæf í "
        "[`vidmid.json`](vidmid.json) og læsileg hér. Þetta er svarið við "
        "spurningunni sem viðmiðið er til fyrir: **sýnir nýja síðan sömu "
        "tölur?** (sjá [`README.md`](README.md) og "
        "[`../endurbygging.md`](../endurbygging.md), kafla 2).", "",
        f"Afleidd skrá. Uppfært {vidmid['uppfaert']} af "
        "`src/python/vidmid/tolur.py`; **ekki handbreytt** (regla 10).", "",
        "## 1. Umfang", "",
        f"| Mæling | Fjöldi |", "|---|---:|",
        f"| Síður lesnar | {s['sidur']} |",
        f"| Síður með tölu í HTML | {s['sidur_med_tolum']} |",
        f"| Tölur alls | {s['tolur_alls']} |",
        f"| **Efnislegar niðurstöður** | **{s['efnislegar']}** |",
        f"| Tölur sem eru ekki niðurstöður | "
        f"{s['tolur_alls'] - s['efnislegar']} |", "",
        "Efnisleg niðurstaða = tala í fyrirsögn, málsgrein, lista, töflu eða "
        "úttaki. Tölur inni í kóðalistun, auðkenni (`0405`), "
        "issue-tilvísanir (`#14`), ISO-dagsetningar og CSS-gildi eru skráðar "
        "áfram í `vidmid.json` en hafa `visst: false` — betra að hafa of mikið "
        "en að missa tölu.", "",
        "**Eftir flokki:** " + ", ".join(
            f"{k} {v}" for k, v in s["eftir_flokki"].items()), "",
        "**Eftir tegund:** " + ", ".join(
            f"{k} {v}" for k, v in s["eftir_tegund"].items()), "",
    ]
    tolulausar = s["sidur_tolulausar"] + s["sidur_an_efnislegra"]
    linur += ["## 2. Síður án efnislegrar tölu", "",
              "| Síða | Ástæða |", "|---|---|"]
    gagnadrifnar = {g["sida"]: g for g in vidmid["gagnadrifnar_sidur"]}
    for sida in sorted(set(tolulausar)):
        astaeda = ("tölurnar reiknaðar í vafra — sjá kafla 4"
                   if sida in gagnadrifnar else
                   "engin tala í HTML-textanum"
                   if sida in s["sidur_tolulausar"] else
                   "aðeins tölur úr kóða, auðkenni eða dagsetningar")
        linur.append(f"| `{sida}` | {astaeda} |")
    return linur + [""]


def _stadfestar(vidmid: dict) -> list[str]:
    linur = ["## 3. Staðfestar tölur", "",
             "Tölurnar sem verklýsing P0.2 telur upp. `Í HTML` segir hvort "
             "talan stendur sem texti í byggðu síðunni; `Úr gagnaskrá` hvort "
             "hún stemmir við `friends/phoebe-stats/_meta.json`.", "",
             "| Heiti | Gildi | Eining | Í HTML | Úr gagnaskrá | Stemmir |",
             "|---|---:|---|:-:|---:|:-:|"]
    for x in vidmid["stadfestar"]:
        linur.append(
            f"| {x['heiti']} | {x['gildi']} | {_flyja(x['eining'])} "
            f"| {'✅' if x['i_html'] else '—'} "
            f"| {x['ur_gagnaskra'] if x['ur_gagnaskra'] is not None else '—'} "
            f"| {'✅' if x['stemmir'] else '❌'} |")
    return linur + [""]


def _samrit(vidmid: dict) -> list[str]:
    linur = ["## 6. Sama tala á fleiri en einni síðu", "",
             "Verklýsingin krefst þess að báðir staðir séu skráðir. Hér eru "
             "aðeins tölur sem birtast á tveimur síðum eða fleiri; fullur "
             "listi með samhengi er í `vidmid.json` undir `samrit`.", "",
             "| Gildi | Eining | Síður |", "|---:|---|---|"]
    for x in vidmid["samrit"][:30]:
        linur.append(f"| {x['gildi']} | {_flyja(x['eining'])} | "
                     + ", ".join(f"`{s}`" for s in x["sidur"]) + " |")
    if len(vidmid["samrit"]) > 30:
        linur.append(f"\n*{len(vidmid['samrit']) - 30} fleiri í `vidmid.json`.*")
    return linur + [""]


def _gagnadrifnar(vidmid: dict) -> list[str]:
    linur = ["## 4. Síður sem reikna tölurnar í vafra", "",
             "Tvær síður birta engar tölur í HTML-inu; þær reikna þær í "
             "JavaScript þegar lesandinn opnar síðuna. **Fyrir þær er "
             "gagnaskráin viðmiðið, ekki HTML-ið.** Þetta er ástæða þess að "
             "sex staðfestar tölur í kafla 3 hafa `—` í `Í HTML`.", ""]
    for g in vidmid["gagnadrifnar_sidur"]:
        linur += [f"### `{g['sida']}`", "", g["skyring"], "",
                  "Gagnaskrár:", ""]
        linur += [f"- `{s}`" for s in g["gagnaskrar"]]
        linur += [""]
    return linur


def _visir(vidmid: dict) -> list[str]:
    linur = ["## 7. Viðmið eftir síðum nýju síðunnar", "",
             "Ein skrá á hverja síðu sem á að byggja (sjá "
             "[`../endurbygging.md`](../endurbygging.md), kafla 3).", "",
             "| Síða nýju síðunnar | Viðmið | Tölur | Úr gömlu síðunum |",
             "|---|---|---:|---|"]
    fyrir_hop = _hopa(vidmid)
    for slug, heiti, sidur in HOPAR + (UTAN,):
        tolur = fyrir_hop[slug]
        raunsidur = sorted({t["sida"] for t in tolur})
        linur.append(
            f"| {heiti} | [`vidmid/{slug}.md`](vidmid/{slug}.md) "
            f"| {len(tolur)} | " + ", ".join(f"`{s}`" for s in raunsidur) + " |")
    return linur + [""]


def _hopa(vidmid: dict) -> dict[str, list[dict]]:
    """Raðar efnislegum tölum í hópa; allt sem passar engum hóp fer í UTAN."""
    skipad = {s for _, _, sidur in HOPAR for s in sidur}
    ut: dict[str, list[dict]] = {slug: [] for slug, _, _ in HOPAR}
    ut[UTAN[0]] = []
    for t in vidmid["gogn"]:
        if not t["visst"]:
            continue
        if t["sida"] in skipad:
            for slug, _, sidur in HOPAR:
                if t["sida"] in sidur:
                    ut[slug].append(t)
        else:
            ut[UTAN[0]].append(t)
    return ut


def _osamraemi(vidmid: dict) -> list[str]:
    """Ósamræmi milli síðna — sjálfstæð niðurstaða, ekki lestrarvilla."""
    merki = {"hatt": "🔴 hátt", "midlungs": "🟠 miðlungs", "skrad": "⚪ skráð"}
    linur = ["## 5. Ósamræmi milli síðna", "",
             "Viðmiðið er samsett úr þremur Quarto-byggingum á tveimur dögum "
             "og fjórar síður koma úr grein sem rataði aldrei á `main` (sjá "
             "[`README.md`](README.md), kafla 2). Ósamræmi er því vænt — og "
             "sjálfstæð niðurstaða. Hvert atriði er sannreynt, ekki ætlað.", ""]
    for o in vidmid["osamraemi"]:
        linur += [f"### {o['heiti']}", "", f"**Alvarleiki:** "
                  f"{merki.get(o['alvarleiki'], o['alvarleiki'])}", "",
                  "| Staður | Það sem hann segir |", "|---|---|"]
        linur += [f"| `{_flyja(s['stadur'])}` | {_flyja(s['segir'])} |"
                  for s in o["stadir"]]
        linur += ["", f"**Niðurstaða.** {o['nidurstada']}", "",
                  f"**Sannreynt með.** {o['profun']}", "",
                  f"**Fyrir endurbygginguna.** {o['afleiding']}", ""]
    return linur


def skrifa_markdown(vidmid: dict, leid: Path) -> list[Path]:
    """Skrifar vidmid.md og eina skrá á hvern hóp undir vidmid/."""
    hlutar = (_yfirlit(vidmid) + _stadfestar(vidmid) + _gagnadrifnar(vidmid)
              + _osamraemi(vidmid) + _samrit(vidmid) + _visir(vidmid))
    leid.write_text("\n".join(hlutar).rstrip() + "\n", encoding="utf-8")
    skrifadar = [leid]

    mappa = leid.parent / "vidmid"
    mappa.mkdir(exist_ok=True)
    fyrir_hop = _hopa(vidmid)
    for slug, heiti, sidur in HOPAR + (UTAN,):
        raunsidur = sidur or tuple(sorted({t["sida"]
                                           for t in fyrir_hop[slug]}))
        skra = mappa / f"{slug}.md"
        skra.write_text("\n".join(_hopaskra(heiti, raunsidur, vidmid)).rstrip()
                        + "\n", encoding="utf-8")
        skrifadar.append(skra)
    return skrifadar
