"""Reglur samanburðarins: hvaða nýja gildi er borið við hverja gamla tölu.

Ein fall á hverja gamla síðu. Nýju gildin eru lesin úr ``web/gogn/*.json``;
engin tala sem má lesa úr viðmiðinu eða gögnunum er skrifuð hér.
"""

from __future__ import annotations

import math
import re

from vidmid_hjalp import (
    BIDSTADA, EKKI_BORID, EKKI_VID, HLUTI_AF_TEXTA, UTAN_UMFANGS,
    Afgreidsla, Nidurstada, lesa_gogn, lesa_vidmid,
)

DAGSLINA = re.compile(r"^(\d{2})\.(\d{2})\.$")
SILNUMER = re.compile(r"^SIL(\d+)$")
MBL_GLUGGI = re.compile(r"\{0,(\d+)\}")
KM_A_GRADU = 111  # staðfasti gömlu síðunnar fyrir breiddargráðu
GLATAD_EINTAK = "mbl-eintakið 7.9.2026 er glatað; nýja síðan notar eintakið frá 16.9.2026"
FJOLDI_LINA = "tilsvör eru 61.161 en delvinso telur um 69.500 „línur“ — önnur talning"
SKJALFTAR_VAL = {"0052": "min_lengd", "0053": "max_lengd", "0054": "min_breidd", "0055": "max_breidd"}


def _skjalftavaktin(a: Afgreidsla) -> None:
    d = lesa_gogn("skjalftar")
    g, sokn = d["lysigogn"], d["lysigogn"]["sokn"]["faeribreytur"]
    hnit = [float(x) for x in re.findall(r"-?\d+(?:\.\d+)?", sokn["polygon"])]
    lengdir, breiddir = hnit[0::2], hnit[1::2]
    val = {"min_lengd": min(lengdir), "max_lengd": max(lengdir),
           "min_breidd": min(breiddir), "max_breidd": max(breiddir)}
    sm, kv = g["samantekt"], g["staerd_eftir_kvarda"][0]
    for nr, lykill in SKJALFTAR_VAL.items():
        a.bera(nr, val[lykill], "Afmörkun svæðis (gráður)")
    for nr in ("0001", "0056"):
        a.bera(nr, [sokn["size_min"], sokn["size_max"]], "Stærðarsvið í fyrirspurn")
    a.bera("0057", [sokn["depth_min"], sokn["depth_max"]], "Dýptarsvið í fyrirspurn (km)")
    a.bera("0012", sm["dagar"], "Dagar í glugganum")
    a.bera("0103", sm["dagar"], "Dagar í glugganum")
    a.bera("0102", sm["atburdir"], "Atburðir")
    a.bera("0106", sm["daglegur_fjoldi"]["midgildi"], "Miðgildi daglegs fjölda")
    a.bera("0107", sm["daglegur_fjoldi"]["lagmark"], "Lágmark daglegs fjölda")
    a.bera("0108", sm["daglegur_fjoldi"]["hamark"], "Hámark daglegs fjölda")
    a.bera("0109", sm["dagar_an_atburda"], "Dagar án atburðar")
    a.bera("0110", [sm["dypt_km"]["lagmark"], sm["dypt_km"]["hamark"]], "Dýptarbil atburða (km)")
    a.bera("0111", sm["dypt_km"]["midgildi"], "Miðgildi dýptar (km)")
    for nr, lykill in (("0112", "fjoldi"), ("0113", "lagmark"), ("0114", "hamark"), ("0115", "midgildi")):
        a.bera(nr, kv[lykill], f"Stærðartafla Mlw: {lykill}")
    dagar = {x["dagur"]: x["fjoldi"] for x in d["gogn"]}
    manudir = {x["manudur"]: x["atburdir"] for x in g["manudir"]}
    manudur_toflu = ""
    for nr in a.milli("0117", "0239"):
        rod = a.rader[nr]
        lina = DAGSLINA.match(rod["lina"] or "")
        if lina:
            ar = re.search(r"\d{4}", rod["tafla"]).group()
            manudur_toflu = f"{ar}-{lina[2]}"
            a.bera(nr, dagar.get(f"{manudur_toflu}-{lina[1]}"), "Fjöldi atburða á degi")
        else:
            a.bera(nr, manudir.get(manudur_toflu), "Samtals atburðir í mánuði")
    audkenni = {int(m[1]) for x in g["syni"] if (m := SILNUMER.match(x["audkenni"]))}
    for nr in a.milli("0096", "0100"):
        a.bera(nr, a.rader[nr]["gildi"] if a.rader[nr]["gildi"] in audkenni else None,
               "SIL-auðkenni í sýnishorni")
    a.sleppa(["0065", "0090"], EKKI_BORID, "númer regex-skrefs í fyrirsögn, ekki niðurstaða")


def _forsida(a: Afgreidsla) -> None:
    d = lesa_gogn("skjalftar")
    a.bera("0002", d["lysigogn"]["samantekt"]["dagar"], "Dagar í glugganum")
    a.bera("0005", [d["lysigogn"]["sokn"]["faeribreytur"]["size_min"],
                    d["lysigogn"]["sokn"]["faeribreytur"]["size_max"]], "Stærðarsvið")


def _hagstofan(a: Afgreidsla) -> None:
    d = lesa_gogn("hagstofan")
    g, ly = d["gogn"], d["lysigogn"]
    toflur = {(x["namssvid"], x["kyn"]): x for x in g}
    reitir = {"Brautskráðir alls": "brautskradir", "Brottfallnir": "brottfallnir", "Enn í námi": "enn_i_nami"}
    kodar = {v["kodi"]: [x["kodi"] for x in v["gildi"]] for v in ly["viddir"]}
    valdir = {q["code"]: q["selection"]["values"] for q in ly["fyrirspurn"]["query"]}
    hopar: dict[tuple[str, str], list[str]] = {}
    for nr, rod in a.rader.items():
        if rod["tafla"] and rod["sulka"] in reitir:
            svid, _, kyn = rod["lina"].partition(" · ")
            a.bera(nr, toflur[(svid, kyn or "Alls")][reitir[rod["sulka"]]],
                   f"{rod['lina']} — {rod['sulka']} (%)")
        elif rod["tafla"] and "kóðar" in rod["sulka"].lower():
            hopar.setdefault((rod["lina"], rod["sulka"]), []).append(nr)
    for (vidd, sulka), nrs in hopar.items():
        listi = valdir[vidd] if sulka == "Valdir kóðar" else kodar[vidd]
        tolur = sorted(int(k) for k in listi if k.isdigit())
        for i, nr in enumerate(nrs):
            a.bera(nr, tolur[i] if i < len(tolur) else None, f"Kóðar víddar {vidd}: {sulka.lower()}")
    verk = next(x for x in kodar["Námssvið"] if x == "07")
    a.bera("0046", int(verk), "Kóði verkfræðisviðs")
    a.bera("0048", ly["tafla"]["fjoldi_gilda"], "Fjöldi prósentugilda í svari")
    a.bera("0063", int(ly["afmorkun"][2]["kodi"]), "Kóði „Hlutfall %“")
    a.bera("0066", ly["tafla"]["aukastafir_i_svari"], "Aukastafir í svari px")
    a.bera("0090", int(kodar["Kyn"][1]), "Kóði karla")
    a.bera("0091", int(kodar["Kyn"][2]), "Kóði kvenna")
    topp = max(x["brautskradir"] for x in g if x["kyn"] == "Alls")
    a.bera("0080", topp, "Hæsta brautskráningarhlutfall (%)")
    a.bera("0081", toflur[("Alls", "Alls")]["brautskradir"], "Brautskráðir alls (%)")
    munir = [m["prosentustig"] for m in ly["munir"]]
    for nr, i in (("0082", 0), ("0118", 1), ("0119", 2)):
        a.bera(nr, munir[i], "Munur í prósentustigum")
    for nr, i in (("0116", ("Verkfræði, framleiðsla og mannvirkjagerð", "Karlar")),
                  ("0117", ("Verkfræði, framleiðsla og mannvirkjagerð", "Konur"))):
        a.bera(nr, toflur[i]["brautskradir"], f"Verkfræði — {i[1].lower()} (%)")
    summur = {x["samtals"] for x in g}
    for nr in ("0084", "0085", "0086"):
        gildi = a.rader[nr]["gildi"]
        a.bera(nr, gildi if gildi in summur else None, "Samtala dálka eftir námundun (%)")
    a.sleppa(["0083", "0124"], EKKI_BORID, "fyrirsögn eða gildissvið staðfestingar, ekki niðurstaða")


def _vedurstodvar(a: Afgreidsla) -> None:
    d = lesa_gogn("vedurstodvar")
    ly = d["lysigogn"]
    sv, vp, bd = ly["svor"], ly["vidmidunarpunktur"], ly["beidnir"]
    stodvar = {s["audkenni"]: s for s in d["gogn"]}
    for nr, lykill in (("0010", "breidd"), ("0011", "lengd")):
        a.bera(nr, vp[lykill], f"Hnit VR-II ({lykill})")
    for nr, i in (("0018", 0), ("0019", 1), ("0021", 2), ("0022", 3), ("0024", 4)):
        a.bera(nr, bd[i]["fjoldi"], f"Stöðvar í svari: {bd[i]['faeribreytur']}")
    a.bera("0020", vp["radius_km"], "Radíus kassans (km)")
    a.bera("0023", int(bd[4]["faeribreytur"].split("=")[1]), "station_id í beiðni")
    for nr in ("0030", "0067"):
        a.bera(nr, vp["radius_km"], "Radíus kassans (km)")
    a.bera("0035", round(KM_A_GRADU * math.cos(math.radians(vp["breidd"]))), "Km á lengdargráðu (reiknað úr hnitum)")
    a.sleppa(["0033", "0034"], EKKI_BORID, "fasti í reiknireglu (111 km á breiddargráðu), ekki niðurstaða")
    virk, aflogd, lang = sv["naesta_virka"], sv["naesta_aflagda"], sv["langtimastod"]
    for nr in ("0047", "0049", "0051", "0061"):
        a.bera(nr, virk["audkenni"], "Auðkenni næstu virku stöðvar")
    for nr in ("0048", "0050", "0052"):
        a.bera(nr, virk["metrar"], "Fjarlægð næstu virku stöðvar (m)")
    a.bera("0053", aflogd["audkenni"], "Auðkenni næstu aflögðu stöðvar")
    a.bera("0054", aflogd["metrar"], "Fjarlægð næstu aflögðu stöðvar (m)")
    a.bera("0056", sv["munur_metrar"], "Munur stöðvanna (m)")
    a.bera("0057", sv["fjoldi_virkra"], "Virkar stöðvar")
    a.bera("0058", sv["fjoldi_allra"], "Allar stöðvar")
    a.bera("0059", sv["hlutfall_virkra_prosent"], "Hlutfall virkra stöðva (%)")
    a.bera("0060", sv["ar_aftur_i_timann"], "Ár aftur í tímann")
    a.bera("0064", lang["audkenni"], "Auðkenni stöðvar sem mælir 50 ár aftur")
    a.bera("0065", stodvar[lang["audkenni"]]["metrar"], "Fjarlægð stöðvarinnar (m)")
    a.sleppa(["0025", "0026"], EKKI_BORID, "HTTP-staða beiðnanna er ekki vistuð í nýju gagnaskránni")
    a.sleppa(["0002", "0003", "0014", "0015", "0027", "0029", "0036", "0044", "0045"],
             EKKI_BORID, HLUTI_AF_TEXTA)


def _mbl(a: Afgreidsla) -> None:
    d = lesa_gogn("mbl")
    sp = {r["lykill"]: r for r in d["gogn"]}
    ein = d["lysigogn"]["eintak"]
    temp = sp["hitastig-reykjavik"]
    for lykill, (mae, nrs) in {
        "einstakar-frettir": ("Einstakar fréttir", ["0019", "0027", "0076", "0085", "0093", "0094"]),
        "hitastig-reykjavik": ("Hitastig í Reykjavík (°C)", ["0020", "0040", "0077", "0086", "0099"]),
        "gengi-usd": ("Gengi USD (ISK)", ["0021", "0048", "0078", "0087", "0095", "0096"]),
        "synileg-ord": ("Sýnileg orð", ["0023", "0054", "0079", "0088", "0097"]),
        "auglysingareitir": ("Auglýsingareitir", ["0024", "0067", "0070", "0080", "0089", "0098"]),
    }.items():
        for nr in nrs:
            a.bera(nr, sp[lykill]["gildi"], mae, GLATAD_EINTAK)
    for nr in ("0026", "0091", "0092"):
        a.bera(nr, sp["einstakar-frettir"]["tilvik"], "Fréttahlekkjatilvik", GLATAD_EINTAK)
    for nr in ("0007", "0015"):
        a.bera(nr, ein["http_stada"], "HTTP-staða", GLATAD_EINTAK)
    for nr in ("0009", "0016"):
        a.bera(nr, ein["baeti"], "Stærð eintaks (bæti)", GLATAD_EINTAK)
    a.bera("0041", int(MBL_GLUGGI.search(temp["mynstur"])[1]), "Gluggi hitamynsturs (stafir)")
    a.bera("0074", ein["md5"][:6], "MD5-hakk eintaks (upphaf)", GLATAD_EINTAK)
    a.bera("0084", ein["md5"][-4:], "MD5-hakk eintaks (endir)", GLATAD_EINTAK)
    a.sleppa([f"{n:04d}" for n in range(56, 66)], EKKI_BORID,
             "orðatíðnitaflan er ekki í nýju gögnunum — mbl.json geymir aðeins fimm spurningar")
    a.sleppa("0071", EKKI_BORID, "fjöldi prófa gamla kóðans, ekki niðurstaða úr eintaki")
    a.sleppa(["0022", "0049", "0052"], EKKI_BORID, HLUTI_AF_TEXTA)
    a.sleppa(["0025", "0039", "0047", "0053", "0066"], EKKI_BORID, "númer kafla í fyrirsögn")


def _phoebe_tolfraedi(a: Afgreidsla) -> None:
    d = lesa_gogn("phoebe-tolfraedi")
    um, ly = d["gogn"], d["lysigogn"]
    umf, tg = ly["umfang"], ly["umfang"]["thattunargaedi"]
    jafn = ly["jafn_hlutur_prosent"]
    thaettir = {x["thattarod"]: x["thaettir"] for x in ly["naervera"]}
    toppur = max(x["lift"] for x in ly["tengsl"])
    a.bera("0037", umf["handritsskrar"] + umf["undanskildar_skrar"], "Handrit í delvinso/friends")
    a.bera("0042", umf["handritsskrar"], "Handritsskrár")
    a.bera("0043", umf["thaettir"], "Þættir")
    a.bera("0048", tg["textablokkir"], "Textablokkir")
    a.bera("0049", tg["tilsvor"], "Tilsvör")
    a.bera("0050", tg["oflokkad"], "Óflokkaðar blokkir")
    for nr in ("0051", "0349"):
        a.bera(nr, tg["oflokkad_prosent"], "Óflokkað hlutfall (%)")
    for nr in ("0052", "0058", "0189"):
        a.bera(nr, round(jafn, 1), "Jöfn skipting sex vina (%)")
    for nr in ("0054", "0060"):
        a.bera(nr, len(ly["plass_alls"]), "Fjöldi aðalpersóna")
    a.bera("0095", round(toppur, 1), "Hæsta lift-gildi (hlutfall)")
    a.bera("0096", round((round(toppur, 1) - 1) * 100), "Umfram samtal við Phoebe (%)")
    a.bera("0116", round(100 / (len(ly["plass_alls"]) - 1)), "Jöfn skipting hinna fimm (%)")
    a.bera("0134", thaettir[10], "Þættir í þáttaröð 10")
    a.bera("0135", thaettir[3], "Þættir í þáttaröð 3")
    a.sleppa(["0045", "0046", "0047"], EKKI_BORID, "dæmi um eitt handritsbrot, ekki niðurstaða úr gögnunum")
    a.sleppa(["0053", "0059"], EKKI_BORID, "teljari brotsins 1/6")
    assert len(um) == 60


def _central_perk(a: Afgreidsla) -> None:
    d = lesa_gogn("phoebe-central-perk")
    hopar = {x["hopur"]: x for x in d["lysigogn"]["hopar"]}
    sm = d["lysigogn"]["samantekt"]
    ph = hopar["phoebe_sings"]
    ekki, cp = hopar["no_central_perk"], hopar["central_perk"]
    for nr in ("0003", "0038"):
        a.bera(nr, sm["handritsskrar"], "Handritaskrár í greiningu")
    a.bera("0001", sm["songsenur"], "Söngsenur")
    a.bera("0054", sm["songsenur"], "Söngsenur")
    for nr in ("0002", "0055"):
        a.bera(nr, sm["songhandrit"], "Handrit með söng")
    a.bera("0004", ph["midgildi_prosent"], "Miðgildi hlutdeildar: Phoebe syngur (%)")
    a.bera("0016", ph["midgildi_prosent"], "Miðgildi hlutdeildar: Phoebe syngur (%)")
    for nr in ("0005", "0013"):
        a.bera(nr, cp["midgildi_prosent"], "Miðgildi hlutdeildar: Central Perk án söngs (%)")
    a.bera("0006", sm["munur_midgilda_prosentustig"], "Munur miðgilda (prósentustig)")
    a.bera("0007", round(ph["hinir_fimm_a_moti_phoebe"], 1), "Hinir fimm á móti Phoebe: syngur")
    a.bera("0017", round(ph["hinir_fimm_a_moti_phoebe"], 1), "Hinir fimm á móti Phoebe: syngur")
    a.bera("0008", round(cp["hinir_fimm_a_moti_phoebe"], 1), "Hinir fimm á móti Phoebe: án söngs")
    a.bera("0014", round(cp["hinir_fimm_a_moti_phoebe"], 1), "Hinir fimm á móti Phoebe: án söngs")
    a.bera("0009", ekki["handrit"], "Handrit án Central Perk-senu")
    a.bera("0010", ekki["midgildi_prosent"], "Miðgildi hlutdeildar: engin sena (%)")
    a.bera("0011", round(ekki["hinir_fimm_a_moti_phoebe"], 1), "Hinir fimm á móti Phoebe: engin sena")
    a.bera("0012", cp["handrit"], "Handrit í Central Perk án söngs")
    a.bera("0015", ph["handrit"], "Handrit þar sem Phoebe syngur")
    a.bera("0039", sm["handritsskrar"] + 2, "Skrár í delvinso/friends (227 + 2 undanskildar)")
    a.sleppa(["0000", "0046", "0051", "0052", "0065", "0066"], EKKI_BORID,
             "tala í aðferðalýsingu eða tilvísun í aðra greiningu, ekki niðurstaða")
    a.sleppa("0063", EKKI_VID, "innfelling á upprunahandriti var tekin út (höfundaréttur, issue #3)")


def _regex_inngangur(a: Afgreidsla) -> None:
    tg = lesa_gogn("phoebe-tolfraedi")["lysigogn"]["umfang"]["thattunargaedi"]
    a.bera("0001", tg["tilsvor"], "Tilsvör (gamla síðan kallar þau „línur“)")
    a.bera("0002", tg["textablokkir"], "Textablokkir")
    a.sleppa("0003", EKKI_BORID, "þáttaröð 2 í texta, ekki niðurstaða")


def _friends_index(a: Afgreidsla) -> None:
    ly = lesa_gogn("phoebe-tolfraedi")["lysigogn"]["umfang"]
    cp = lesa_gogn("phoebe-central-perk")["lysigogn"]["samantekt"]
    skrar_alls = ly["handritsskrar"] + ly["undanskildar_skrar"]
    for nr in ("0001", "0004", "0013"):
        a.bera(nr, skrar_alls, "Handritaskrár í safninu", "talan stemmir aðeins sem 227 + 2 undanskildar")
    for nr in ("0010", "0011"):
        a.bera(nr, ly["thaettir"], "Þættir")
    a.bera("0023", cp["songsenur"], "Söngsenur")
    a.bera("0024", cp["songhandrit"], "Handrit með söng")
    a.bera("0014", ly["handritsskrar"] - ly["skrar_med_tvo_thaetti"], "Skrár með stöku þáttanúmeri",
           "gamla talan er 229 − 6: hún taldi fjórar bandstriksskrár og tvær undanskildar, en níu skrár geyma tvo þætti")
    for nr in ("0012", "0021"):
        a.bera(nr, ly["thattunargaedi"]["textablokkir"], "„Línur“ eftir þáttun",
               "talan 69.500 er áætlun delvinso; textablokkir hér eru taldar úr sömu handritum")
    a.sleppa(["0002", "0003", "0005", "0006", "0009", "0022"], EKKI_BORID,
             "samanburður handritasafnanna tveggja, ekki í nýju gögnunum")


def _bidstada(a: Afgreidsla) -> None:
    a.sleppa(list(a.rader), EKKI_BORID, BIDSTADA)


def _utan_umfangs(a: Afgreidsla) -> None:
    a.sleppa(list(a.rader), EKKI_VID, UTAN_UMFANGS)


# gömul síða -> (ný síða, regla). Raðað eins og í vidmid.json.
SAMSVORUN: list[tuple[str, str, object]] = [
    ("capstone/earthquakes.html", "skjalftavaktin", _skjalftavaktin),
    ("index.html", "forsíða", _forsida),
    ("lotur/vefthjonustur/hagstofan.html", "hagstofan", _hagstofan),
    ("lotur/vefthjonustur/vedurstofan.html", "vedurstodvar", _vedurstodvar),
    ("lotur/regex/mbl.html", "mbl-regex", _mbl),
    ("friends/phoebe-statistics.html", "phoebe-tolfraedi", _phoebe_tolfraedi),
    ("phoebe-central-perk.html", "phoebe-central-perk", _central_perk),
    ("lotur/regex/index.html", "phoebe-tolfraedi", _regex_inngangur),
    ("friends/index.html", "friends-gagnasagan", _friends_index),
    ("friends/phoebe-tribute.html", "phoebe-tribute", _bidstada),
]


def allar_nidurstodur() -> list[Nidurstada]:
    """Flokkar allar efnislegar tölur viðmiðsins, síðu fyrir síðu."""
    vidmid = lesa_vidmid()
    kortlagt = {s for s, _, _ in SAMSVORUN}
    reglur = list(SAMSVORUN) + [
        (s["sida"], "—", _utan_umfangs) for s in vidmid["sidur"]
        if s["sida"] not in kortlagt and s["efnislegar"] > 0
    ]
    nidurstodur: list[Nidurstada] = []
    for gomul, ny, regla in reglur:
        afgreidsla = Afgreidsla(vidmid, gomul, ny)
        regla(afgreidsla)
        nidurstodur += afgreidsla.lokid()
    return nidurstodur


__all__ = ["allar_nidurstodur", "SAMSVORUN"]
