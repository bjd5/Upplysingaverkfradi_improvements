"""Skrifar samanburðarskjalið fyrir veðurstöðvarnar á íslensku.

Aðskilið frá útreikningnum í ``vedurstodvar_samanburdur.py`` af sömu ástæðu og
HTML er aðskilið frá CSS: önnur einingin reiknar, hin ákveður framsetningu, og
hvorug þarf að vita hvernig hin vinnur (reglur 2 og 6).

Engin tala er slegin inn hér — allt kemur úr samanburðinum.
"""

from __future__ import annotations

from pathlib import Path

# Hvenær frosna viðmiðið var byggt. Dagsetningin er niðurstaða P0.1, sem rakti
# byggingarlotur gömlu síðunnar — sjá docs/vidmid/README.md, kafla 2.
VIDMIDSBYGGING = "2026-09-17"

SVARA_HEITI = {
    "naesta": "Næsta virka stöð við VR-II",
    "naesta_aflogd": "Næsta aflagða stöð",
    "langtimastod": "Næsta virka stöð sem mælir 50 ár aftur",
}


def _stod_texti(faersla: tuple[int, str, int]) -> str:
    """Sniðmát fyrir eina stöð: heiti, auðkenni og fjarlægð í metrum."""
    audkenni, nafn, metrar = faersla
    return f"{nafn} ({audkenni}), {metrar} m"


def _siutafla(siur: list[dict]) -> list[str]:
    """Tafla yfir fjölda stöðva í hverri af fimm beiðnum gömlu síðunnar."""
    linur = [
        "| Sía í beiðninni | Viðmið (gamla síðan) | Frosið eintak | Munur |",
        "|---|---:|---:|---:|",
    ]
    for sia in siur:
        munur = "—" if sia["munur"] == 0 else f"{sia['munur']:+d}"
        linur.append(f"| {sia['sia']} | {sia['vidmid']} | {sia['nuna']} | {munur} |")
    return linur


def _svaratafla(svor: dict) -> list[str]:
    """Tafla yfir stöðvavalið sjálft — sömu spurningar og gamla síðan svaraði."""
    linur = [
        "| Spurning | Viðmið (gamla síðan) | Frosið eintak | Sama stöð? |",
        "|---|---|---|:-:|",
    ]
    for lykill, heiti in SVARA_HEITI.items():
        faersla = svor[lykill]
        sama = "✅" if faersla["vidmid"][0] == faersla["nuna"][0] else "❌"
        linur.append(
            f"| {heiti} | {_stod_texti(tuple(faersla['vidmid']))} "
            f"| {_stod_texti(tuple(faersla['nuna']))} | {sama} |"
        )
    return linur


def _nidurstada(samanburdur: dict) -> list[str]:
    """Dregur saman hvað stemmdi og hvað ekki — í orðum, ekki bara í töflu."""
    frabrigdi = [sia for sia in samanburdur["siur"] if sia["munur"] != 0]
    onnur_stod = [
        SVARA_HEITI[lykill]
        for lykill, faersla in samanburdur["svor"].items()
        if faersla["vidmid"][0] != faersla["nuna"][0]
    ]

    linur: list[str] = []
    if not frabrigdi and not onnur_stod:
        linur += [
            "**Allar tölur stemma.** Frosna eintakið gefur sömu fjöldatölur og sama "
            "stöðvaval og gamla síðan birti, þrátt fyrir að vera sótt viku síðar og "
            "óháð henni.",
            "",
            "Það þýðir **ekki** að listinn sé stöðugur. Stöðvaskrá Veðurstofunnar er "
            "lýsigagnaskrá sem breytist þegar stöð er sett upp eða tekin niður, ekki "
            "mælingaröð sem breytist á klukkutíma fresti. Vikan sem skilur eintökin að "
            "var einfaldlega vika án breytinga. Næsta uppfærsla þjónustunnar getur "
            "hreyft hvaða tölu sem er hér — og gerði það óséð í hverri byggingu gömlu "
            "síðunnar, því hún vistaði svarið aldrei.",
        ]
    else:
        linur.append("**Tölurnar víkja frá viðmiðinu.** Það er vænt niðurstaða hér:")
        linur.append("")
        for sia in frabrigdi:
            linur.append(
                f"- `{sia['sia']}`: viðmiðið {sia['vidmid']}, frosna eintakið "
                f"{sia['nuna']} ({sia['munur']:+d})."
            )
        for heiti in onnur_stod:
            linur.append(f"- {heiti}: önnur stöð en viðmiðið valdi.")
        linur += [
            "",
            "Munurinn mælir breytingu á stöðvaskrá Veðurstofunnar milli 2026-09-17 og "
            "söfnunardags, ekki villu í úrvinnslunni. Frá og með þessu eintaki er "
            "gagnið fast og tölur nýju síðunnar endurskapanlegar.",
        ]
    return linur


def byggja_skjal(samanburdur: dict) -> str:
    """Byggir allt markdown-skjalið sem streng."""
    valin = samanburdur["valin_stod"]
    vr_ii = samanburdur["vr_ii"]
    linur = [
        "# Veðurstöðvar — frosið eintak borið við gömlu síðuna",
        "",
        "Veðurstöðvarnar eru eina gagnasafnið í verkefninu sem **átti sér ekkert",
        "eintak**. Gamla verkefnið sótti stöðvalistann upp á nýtt í hverri byggingu og",
        "vistaði svarið aldrei, svo gamla veðurstöðvasíðan gat sýnt aðrar tölur í dag en",
        "í gær án þess að nokkur tæki eftir því.",
        "",
        "P0.3 (issue #2) sótti **eitt** eintak og frysti það. Þetta skjal svarar",
        "spurningunni sem frystingin kallar á: *hvað víkur frosna eintakið frá því sem",
        "gamla síðan birti?* Munur er vænt niðurstaða, ekki villa — það er ekki hægt að",
        "bera frosið gagn við gagn sem var aldrei fryst og vænta þess að þau séu eins.",
        "",
        "Skjalið er **afleitt**: það verður til úr",
        "`src/python/vinnsla/vedurstodvar_samanburdur.py` og er ekki handbreytt (regla 10).",
        "",
        "---",
        "",
        "## 1. Hvað er borið saman",
        "",
        "| | Heimild |",
        "|---|---|",
        f"| **Frosið eintak** | `data/raw/vedurstodvar/{samanburdur['eintak']}` "
        "(provenance í sömu möppu) |",
        "| **Viðmið** | `docs/vidmid/generated/vedurstofa-siur.md`, "
        f"`-nidurstada.md` og `-svor.md` — byggð {VIDMIDSBYGGING} |",
        "",
        "Fjöldatölurnar eru **lesnar** úr viðmiðsskjalinu, ekki slegnar inn. Gamla síðan",
        "sendi fimm beiðnir; frosna eintakið er ósíaða svarið og síurnar fjórar eru",
        "reiknaðar staðbundið úr því með sömu skilyrðum og gamla skriftan sendi",
        "þjónustunni.",
        "",
        "## 2. Fjöldi stöðva í hverri síu",
        "",
        *_siutafla(samanburdur["siur"]),
        "",
        f"Af stöðvunum eru {samanburdur['fjoldi_aflagdra']} aflagðar — reiturinn `ending` er",
        "ártal en ekki tómt. Listinn er því ekki listi yfir stöðvar í rekstri heldur",
        "allar stöðvar sem Veðurstofan þekkir, virkar og aflagðar.",
        "",
        "## 3. Stöðvavalið sjálft",
        "",
        *_svaratafla(samanburdur["svor"]),
        "",
        f"Hnit VR-II: {vr_ii['breidd']}, {vr_ii['lengd']} — {vr_ii['heimild']}.",
        "",
        "## 4. Niðurstaða",
        "",
        *_nidurstada(samanburdur),
        "",
        "## 5. Takmarkanir sem fylgja þessu safni",
        "",
        "- Eintakið er **ný söfnun**, ekki afrit af því sem gamla síðan sá. Tala sem",
        "  víkur frá gömlu síðunni er breyting á stöðvaskránni, ekki villa.",
        "- Eintakið er **ekki lifandi staða**. Stöð sem bætist við eða er tekin niður",
        "  eftir söfnunardag kemur ekki fram fyrr en nýtt eintak er fryst.",
        f"- Stöðin sem síðan les, {valin['name']} ({valin['station']}), hóf mælingar",
        f"  {valin['start']} og á því engar mælingar frá því fyrir þann tíma.",
        "- Nálægð og samfelld tímaröð eru tvö ólík skilyrði; sama stöðin uppfyllir",
        "  sjaldnast bæði. Röðun eftir fjarlægð einni saman getur skilað aflagðri stöð.",
        "",
        "---",
        "",
        f"*Afleitt skjal úr eintaki sem var sótt {samanburdur['sott_utc']}, byggt af "
        "`src/python/vinnsla/vedurstodvar_samanburdur.py`. Sama keyrsla á sömu gögnum "
        "gefur sama skjal — óháð því hvenær hún er gerð.*",
    ]
    return "\n".join(linur) + "\n"


def skrifa_skjal(samanburdur: dict, slod: Path) -> None:
    """Skrifar samanburðarskjalið á tilgreinda slóð."""
    slod.parent.mkdir(parents=True, exist_ok=True)
    slod.write_text(byggja_skjal(samanburdur), encoding="utf-8")
