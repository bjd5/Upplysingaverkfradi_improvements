"""Skrá yfir gögnin sem P0.1 bjargaði, og hvaðan byggða síðan kom.

Hrein gagnaskrá — engin rökvísi. provenance.py les þetta og reiknar SHA-256.
Samhengið er í docs/vidmid/README.md og docs/endurbygging.md (kafli 2).
"""

from __future__ import annotations

# Söfnin fjögur sem P0.1 bjargaði. Slóðirnar eru skráðar með ~ fyrir
# heimamöppuna: repo-ið er opið og full slóð segir ekkert umfram þetta.
SOFN = (
    {
        "heiti": "mbl",
        "mappa": "data/raw/mbl",
        "uppruni": "~/Desktop/Skóla forritun/upplysingver/data/raw/mbl",
        "upprunarepo": None,
        "skyring": (
            "Eina eintakið sem til er af mbl.is-forsíðunni sem regex-æfingin "
            "byggir á. Sótt af https://www.mbl.is/frettir/ (ekki forsíðunni "
            "sjálfri) 2026-09-16. Var gitignored í upprunaverkefninu."
        ),
    },
    {
        "heiti": "vefur",
        "mappa": "docs/vidmid/vefur",
        "uppruni": "~/PycharmProjects/idn302g-2026-team-friends-thesveinn/docs",
        "upprunarepo": "Upplysingaverkfraedi/idn302g-2026-team-friends-phoebe",
        "skyring": (
            "Byggða gamla Quarto-síðan, 28 HTML-skrár. Eina heildarskráin yfir "
            "hverja tölu sem gamla síðan birtir. Var gitignored (afleiða)."
        ),
    },
    {
        "heiti": "generated",
        "mappa": "docs/vidmid/generated",
        "uppruni": "~/PycharmProjects/idn302g-2026-team-friends-thesveinn/site/_generated",
        "upprunarepo": "Upplysingaverkfraedi/idn302g-2026-team-friends-phoebe",
        "skyring": (
            "Afleidd úttök greininganna sem Quarto límdi inn í síðurnar. "
            "vedurstofa-*.md eru EINA ummerkið um veðurstöðvagögnin — hráa "
            "API-svarið var aldrei vistað."
        ),
    },
    {
        "heiti": "phoebe-stats",
        "mappa": "docs/vidmid/phoebe-stats",
        "uppruni": "~/PycharmProjects/idn302g-2026-team-friends-thesveinn/data/processed/phoebe-stats",
        "upprunarepo": "Upplysingaverkfraedi/idn302g-2026-team-friends-phoebe",
        "skyring": (
            "Friends-tölfræðin fullreiknuð: línufjöldi, senur, hlutföll. "
            "Tölur um textann, ekki textinn sjálfur — handritin sjálf eru "
            "ekki afrituð (höfundaréttur óútkljáður, issue #3)."
        ),
    },
)

# Hvaða commit var undir þegar gamla síðan var byggð?
#
# Verklýsing P0.1 sagði 2865ed6. Það stenst ekki: 2865ed6 er frá 2026-09-20
# 11:51Z en ENGIN skrá í byggingunni er yngri en 2026-09-17 09:51Z. docs/ var
# gitignored í upprunarepo-inu (.gitignore lína 29), svo byggingin á sér ekkert
# beint git-ummerki. Það sem er hægt að sanna er tvennt: breytingartími hverrar
# skráar (fylgdi með í cp -p) og reflog upprunarepo-sins, sem segir hvaða HEAD
# var virkur á þeim tíma. Þau tvö saman gefa töfluna hér að neðan.
#
# Niðurstaðan: byggingin er ekki EIN bygging heldur þrjár — Quarto endurbyggði
# aðeins þær síður sem höfðu breyst. Það skiptir máli fyrir P0.2: fjórar síður
# eru byggðar úr commit sem er ekki einu sinni á sögu main.
BYGGINGARLOTUR = (
    {
        "fra_utc": "2026-09-16T14:00:00Z",
        "til_utc": "2026-09-16T20:00:00Z",
        "commit": "5510cab56e1c3e69a220cda6eb3cd87430cdb442",
        "commit_utc": "2026-09-16T14:55:45Z",
        "grein": "tmp/samrunaprof",
        "a_sogu_main": False,
        "athugasemd": (
            "Bráðabirgðagrein sem rataði aldrei á main sem slík. Þrjár af "
            "kjarnasíðum rannsóknarinnar eru byggðar hér."
        ),
    },
    {
        "fra_utc": "2026-09-16T23:00:00Z",
        "til_utc": "2026-09-16T23:26:00Z",
        "commit": "9cf667de5bc889b1fb8b334bce54063fb2f0e481",
        "commit_utc": "2026-09-16T23:06:12Z",
        "grein": "feat/tokenskraning-agenta",
        "a_sogu_main": True,
        "athugasemd": "origin/main er 37 commit á undan þessu.",
    },
    {
        "fra_utc": "2026-09-17T09:42:10Z",
        "til_utc": "2026-09-18T00:00:00Z",
        "commit": "fdf1261f5b3ff215c58551898b84015e38dff457",
        "commit_utc": "2026-09-17T08:53:44Z",
        "grein": "feat/tokenskraning-agenta",
        "a_sogu_main": True,
        "athugasemd": (
            "Sóttur með pull --ff-only kl. 09:42:10Z; HEAD hreyfðist ekki aftur "
            "fyrr en 2026-09-23. Meirihluti síðnanna er héðan. origin/main er "
            "22 commit á undan þessu."
        ),
    },
)

VIDMIDSREPO = "Upplysingaverkfraedi/idn302g-2026-team-friends-phoebe"
