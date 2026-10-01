/* skjalftavaktin.js — töflur Skjálftavaktarinnar úr web/gogn/skjalftar.json.

   Tölurnar í niðurstöðunni og afmörkuninni fyllir gagnahluti.js út frá
   data-gogn-reitur. Hér eru aðeins töflurnar sem reitir ná ekki yfir. Taflan
   undir myndritinu er hins vegar í HTML-inu sjálfu svo hún virki án JavaScript
   (docs/myndrit.md); próf ber hana saman við gagnaskrána.                    */

(function () {
  "use strict";

  const data = window.SiteData;
  const table = window.DataSection.buildTable;

  // Íslensk skýring á hverri breytu beiðninnar, svo lesandi þurfi ekki að giska.
  const REQUEST_MEANING = {
    start_time: "Upphaf tímabils (UTC)",
    end_time: "Lok tímabils (UTC, ekki með)",
    depth_min: "Minnsta dýpt (km)",
    depth_max: "Mesta dýpt (km)",
    size_min: "Minnsta stærð",
    size_max: "Mesta stærð",
    polygon: "Svæðið, sem hnit (lengd breidd)",
    type: "Tegund atburðar",
    evaluation_mode: "Yfirferð (manual = yfirfarið)",
    format: "Svarsnið",
    system: "Mælikerfi (sil = SIL-kerfi Veðurstofunnar)"
  };

  function place(section, name, node) {
    const target = section.querySelector('[data-skjalftar-tafla="' + name + '"]');
    if (!target) {
      throw new data.DataError("Staður fyrir töfluna „" + name + "“ vantar á síðuna.");
    }
    target.appendChild(node);
  }

  function scaleTable(doc) {
    return table({
      caption: "Stærð skjálfta eftir kvarða",
      columns: [
        { heading: "Kvarði", key: "kvardi" },
        { heading: "Atburðir", key: "fjoldi", numeric: true },
        { heading: "Lágmark", key: "lagmark", numeric: true },
        { heading: "Miðgildi", key: "midgildi", numeric: true },
        { heading: "Hámark", key: "hamark", numeric: true }
      ],
      rows: doc.gogn.staerd_eftir_kvarda
    });
  }

  function monthTable(doc) {
    return table({
      caption: "Atburðir eftir mánuðum",
      columns: [
        { heading: "Mánuður", key: "manudur" },
        { heading: "Dagar", key: "dagar", numeric: true },
        { heading: "Atburðir", key: "atburdir", numeric: true }
      ],
      rows: doc.gogn.manudir.map(function (row) {
        return { manudur: data.formatMonth(row.manudur), dagar: row.dagar,
                 atburdir: row.atburdir };
      })
    });
  }

  function sampleTable(doc) {
    return table({
      caption: "Fyrstu átta atburðirnir, óbreytt úr hrágögnunum",
      columns: [
        { heading: "Auðkenni", key: "audkenni" },
        { heading: "Tími (UTC)", key: "timi" },
        { heading: "Stærð", key: "staerd", numeric: true },
        { heading: "Kvarði", key: "kvardi" },
        { heading: "Dýpt (km)", key: "dypt_km", numeric: true },
        { heading: "Breidd", key: "breidd", numeric: true },
        { heading: "Lengd", key: "lengd", numeric: true }
      ],
      rows: doc.gogn.syni
    });
  }

  window.DataSection.registerRenderer("skjalftar-tolur", function (doc, section) {
    place(section, "staerd", scaleTable(doc));
    place(section, "manudir", monthTable(doc));
    place(section, "syni", sampleTable(doc));
  });

  window.DataSection.registerRenderer("skjalftar-sokn", function (doc, section) {
    const request = doc.lysigogn.sokn;
    const rows = [
      { heiti: "Vefþjónusta", gildi: request.endapunktur },
      { heiti: "Sótt", gildi: data.formatDate(doc.uppfaert) },
      { heiti: "Hrá skrá", gildi: request.hraskra },
      { heiti: "Leyfi", gildi: request.leyfi }
    ];
    Object.keys(request.faeribreytur).forEach(function (key) {
      rows.push({ heiti: key + " — " + (REQUEST_MEANING[key] || "breyta beiðninnar"),
                  gildi: String(request.faeribreytur[key]) });
    });
    place(section, "sokn", table({
      caption: "Beiðnin sem var send og hvenær",
      columns: [
        { heading: "Atriði", key: "heiti" },
        { heading: "Gildi", key: "gildi" }
      ],
      rows: rows
    }));
  });
})();
