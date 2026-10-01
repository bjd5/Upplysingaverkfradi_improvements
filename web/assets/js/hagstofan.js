/* hagstofan.js — töflur og beiðnin á síðu Hagstofunnar (issue #21).

   Tölurnar sem standa einar og sér eru data-gogn-reitir í HTML. Hér eru
   aðeins töflurnar og aðferðin, sem reitir ná ekki yfir. Allt kemur úr
   hagstofan.json (gogn + lysigogn); engin tala er skrifuð í þessa skrá.    */

(function () {
  "use strict";

  const data = window.SiteData;
  const section = window.DataSection;

  // Sýnishorn úr flata listanum: fyrstu stöðurnar og sú síðasta.
  const SAMPLE_POSITIONS = [0, 1, 2, 3, 12, "last"];
  const JSON_INDENT = 2;

  function heading(text) {
    const node = document.createElement("h3");
    node.textContent = text;
    return node;
  }

  function percent(value) {
    return data.formatNumber(value) + "%";
  }

  function resultTable(doc) {
    const rows = doc.gogn.map(function (row) {
      return {
        namssvid: row.namssvid, kyn: row.kyn,
        brautskradir: percent(row.brautskradir), brottfallnir: percent(row.brottfallnir),
        enn_i_nami: percent(row.enn_i_nami), samtals: percent(row.samtals)
      };
    });
    const labels = {};
    doc.lysigogn.stodur.forEach(function (status) { labels[status.reitur] = status.heiti; });
    return section.buildTable({
      caption: "Hlutfall innritaðra eftir stöðu sex árum síðar",
      columns: [
        { heading: "Námssvið", key: "namssvid" },
        { heading: "Kyn", key: "kyn" },
        { heading: labels.brautskradir, key: "brautskradir", numeric: true },
        { heading: labels.brottfallnir, key: "brottfallnir", numeric: true },
        { heading: labels.enn_i_nami, key: "enn_i_nami", numeric: true },
        { heading: "Samtals", key: "samtals", numeric: true }
      ],
      rows: rows
    });
  }

  function differenceTable(doc) {
    const rows = doc.lysigogn.munir.map(function (diff) {
      return { lysing: diff.lysing, munur: data.formatNumber(diff.prosentustig) };
    });
    return section.buildTable({
      caption: "Munur á brautskráningarhlutfalli, í prósentustigum",
      columns: [
        { heading: "Samanburður", key: "lysing" },
        { heading: "Munur", key: "munur", numeric: true }
      ],
      rows: rows
    });
  }

  function constraintTable(doc) {
    return section.buildTable({
      caption: "Afmörkun beiðninnar",
      columns: [
        { heading: "Vídd", key: "heiti" },
        { heading: "Kóði", key: "kodi" },
        { heading: "Gildi", key: "gildi" }
      ],
      rows: doc.lysigogn.afmorkun
    });
  }

  function requestBlock(doc) {
    const pre = document.createElement("pre");
    pre.tabIndex = 0;
    pre.setAttribute("aria-label", "Beiðnin sjálf, query.json");
    const code = document.createElement("code");
    code.textContent = JSON.stringify(doc.lysigogn.fyrirspurn, null, JSON_INDENT);
    pre.appendChild(code);
    return pre;
  }

  function selectedValues(dimension) {
    return dimension.gildi
      .filter(function (value) { return value.valid; })
      .sort(function (a, b) { return a.stada - b.stada; });
  }

  function dimensionTable(doc) {
    const rows = doc.lysigogn.viddir.map(function (dimension) {
      const chosen = selectedValues(dimension);
      return {
        stada: dimension.stada, heiti: dimension.heiti,
        valin: chosen.length, af: dimension.gildi.length
      };
    });
    const total = doc.lysigogn.tafla.fjoldi_gilda;
    return section.buildTable({
      caption: "Víddalýsingin: sex víddir. Flati listinn hefur " + data.formatNumber(total) +
               " gildi, eitt fyrir hverja samsetningu.",
      columns: [
        { heading: "Röð", key: "stada", numeric: true },
        { heading: "Vídd", key: "heiti" },
        { heading: "Valin gildi", key: "valin", numeric: true },
        { heading: "Til í töflunni", key: "af", numeric: true }
      ],
      rows: rows
    });
  }

  // Les stöðu i í flata listanum: síðasta víddin breytist hraðast.
  function decodePosition(dimensions, position) {
    const parts = {};
    let rest = position;
    for (let i = dimensions.length - 1; i >= 0; i--) {
      const chosen = selectedValues(dimensions[i]);
      parts[dimensions[i].kodi] = chosen[rest % chosen.length];
      rest = Math.floor(rest / chosen.length);
    }
    return parts;
  }

  function positionTable(doc) {
    const dimensions = doc.lysigogn.viddir.slice().sort(function (a, b) {
      return a.stada - b.stada;
    });
    const total = doc.lysigogn.tafla.fjoldi_gilda;
    const field = {};
    doc.lysigogn.stodur.forEach(function (status) { field[status.kodi] = status.reitur; });
    const rows = SAMPLE_POSITIONS.map(function (sample) {
      const position = sample === "last" ? total - 1 : sample;
      const parts = decodePosition(dimensions, position);
      const line = doc.gogn.find(function (row) {
        return row.namssvid_kodi === parts["Námssvið"].kodi && row.kyn_kodi === parts["Kyn"].kodi;
      });
      return {
        stada: "value[" + position + "]",
        nemendur: parts["Nemendur"].heiti, namssvid: parts["Námssvið"].heiti,
        kyn: parts["Kyn"].heiti,
        gildi: percent(line[field[parts["Nemendur"].kodi]])
      };
    });
    return section.buildTable({
      caption: "Hvernig staða í listanum vísar á mælingu",
      columns: [
        { heading: "Staða", key: "stada" },
        { heading: "Nemendur", key: "nemendur" },
        { heading: "Námssvið", key: "namssvid" },
        { heading: "Kyn", key: "kyn" },
        { heading: "Gildi", key: "gildi", numeric: true }
      ],
      rows: rows
    });
  }

  function append(parent, nodes) {
    nodes.forEach(function (node) { parent.appendChild(node); });
  }

  section.registerRenderer("hagstofan-nidurstodur", function (doc, host) {
    append(host.querySelector("[data-gogn-efni]"),
           [differenceTable(doc), resultTable(doc)]);
  });

  section.registerRenderer("hagstofan-adferd", function (doc, host) {
    append(host.querySelector("[data-gogn-efni]"), [
      heading("Afmörkunin"), constraintTable(doc),
      heading("Beiðnin sjálf"), requestBlock(doc),
      heading("Svarið: víddir og flatur listi"), dimensionTable(doc), positionTable(doc)
    ]);
  });
})();
