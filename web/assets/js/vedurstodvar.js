/* vedurstodvar.js — síðusértækt efni Veðurstöðvasíðunnar (issue #22).

   gagnahluti.js fyllir data-gogn-reitur. Hér er það sem reitir ná ekki yfir:
   ártöl og auðkenni (án þúsundapunkts), já/nei, staða stöðvar í orðum,
   sóknardagsetningin og töflurnar tvær. Allt úr vedurstodvar.json.         */

(function () {
  "use strict";

  const data = window.SiteData;
  const layer = window.DataSection;

  function lookup(doc, path) {
    const value = data.valueAt(doc.gogn, path);
    if (value === undefined || value === null) {
      throw new data.DataError("Gildið „" + path + "“ er ekki í „vedurstodvar.json“.");
    }
    return value;
  }

  // Ártal og auðkenni eru heiti, ekki magn: 1963, ekki 1.963.
  function plain(value) {
    if (typeof value === "boolean") return value ? "Já" : "Nei";
    return String(value);
  }

  // Staðan í orðum og með tákni; liturinn er aldrei einn um merkinguna (3.3).
  function statusText(station) {
    return station.virk ? "✓ Virk — mælir enn" : "✕ Aflögð — hætti " + station.lokaar;
  }

  function fillHooks(doc, section) {
    section.querySelectorAll("[data-vedur-texti]").forEach(function (el) {
      el.textContent = plain(lookup(doc, el.dataset.vedurTexti));
    });
    section.querySelectorAll("[data-vedur-stada]").forEach(function (el) {
      el.textContent = statusText(lookup(doc, el.dataset.vedurStada));
    });
    section.querySelectorAll("[data-vedur-dags]").forEach(function (el) {
      el.textContent = data.formatDate(lookup(doc, el.dataset.vedurDags));
    });
  }

  // Tafla sem skrunar lárétt þarf að ná fókus svo lyklaborð geti skrunað henni.
  function addTable(section, wrapper, label) {
    wrapper.tabIndex = 0;
    wrapper.setAttribute("aria-label", label);
    section.querySelector("[data-gogn-efni]").appendChild(wrapper);
  }

  layer.registerRenderer("vedurstodvar", fillHooks);

  layer.registerRenderer("vedurstodvar-beidnir", function (doc, section) {
    fillHooks(doc, section);
    addTable(section, layer.buildTable({
      caption: "Fjöldi stöðva sem hver sía skilar úr eintakinu",
      columns: [
        { heading: "Sía", key: "sia" },
        { heading: "Stöðvar", key: "fjoldi", numeric: true }
      ],
      rows: lookup(doc, "beidnir")
    }), "Síurnar");
  });

  layer.registerRenderer("vedurstodvar-stodvar", function (doc, section) {
    fillHooks(doc, section);
    const stations = lookup(doc, "stodvar_i_kassa");
    const chosen = lookup(doc, "svor.naesta_virka.station_id");
    const longest = Math.max.apply(null, stations.map(function (s) { return s.metrar; }));
    const rows = stations.map(function (s) {
      return {
        rod: s.rod,
        stod: s.nafn + " (" + s.station_id + ")",
        metrar: s.metrar,
        timabil: s.virk ? "frá " + s.fyrsta_ar : s.fyrsta_ar + "–" + s.lokaar,
        stada: (s.virk ? "✓ Virk" : "✕ Aflögð") +
               (s.station_id === chosen ? " ★ forritið les" : "")
      };
    });
    const wrapper = layer.buildTable({
      caption: "Stöðvarnar " + data.formatNumber(stations.length) +
               " innan kassans um VR-II, raðaðar eftir fjarlægð",
      columns: [
        { heading: "Röð", key: "rod", numeric: true },
        { heading: "Stöð (auðkenni)", key: "stod" },
        { heading: "Fjarlægð (m)", key: "metrar", numeric: true },
        { heading: "Mælingar", key: "timabil" },
        { heading: "Staða", key: "stada" }
      ],
      rows: rows
    });
    wrapper.querySelectorAll("tbody tr").forEach(function (tr, i) {
      const s = stations[i];
      if (!s.virk) tr.className = "vedur-rod--aflogd";
      if (s.station_id === chosen) tr.className = "vedur-rod--valin";
      // Súlan er sjónræn endurtekning á tölunni við hliðina; skjálesari les töluna.
      const bar = document.createElement("meter");
      bar.className = "vedur-sula";
      bar.min = 0;
      bar.max = longest;
      bar.value = s.metrar;
      bar.setAttribute("aria-hidden", "true");
      tr.children[2].appendChild(bar);
    });
    addTable(section, wrapper, "Stöðvarnar eftir fjarlægð");
  });
})();
