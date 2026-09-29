/* vedurstodvar.js — síðusértækt efni Veðurstöðvasíðunnar (issue #22).

   gagnahluti.js fyllir data-gogn-reitur. Hér er það sem reitir ná ekki yfir,
   allt úr vedurstodvar.json og með sömu slóðavenju (lysigogn. / gogn.):
     data-vedur-texti="slóð"  ártal eða auðkenni, án þúsundapunkts (1963)
     data-vedur-janei="slóð"  já/nei-gildi
     data-vedur-stada="slóð"  staða stöðvar í orðum og með tákni
     data-vedur-sott          sóknardagurinn (uppfaert = tími frosna svarsins)
   og töflurnar tvær: síurnar og stöðvarnar eftir fjarlægð. Engin námundun. */

(function () {
  "use strict";

  const data = window.SiteData;
  const layer = window.DataSection;

  function objectAt(doc, path) {
    const value = data.valueAt(doc, path);
    if (/^(lysigogn|gogn)\./.test(path) && value !== null && typeof value === "object") {
      return value;
    }
    throw new data.DataError("Gildið „" + path + "“ er ekki í gagnaskránni.");
  }

  // Tómt lokaár (ending) þýðir að stöðin mælir enn — sama skilyrði og active=true.
  function isActive(station) {
    return station.lokaar === null;
  }

  // Liturinn er aldrei einn um merkinguna: orð og tákn (regla 3.3).
  function statusText(station) {
    return isActive(station) ? "✓ Virk — mælir enn" : "✕ Aflögð — hætti " + station.lokaar;
  }

  function each(section, hook, fill) {
    section.querySelectorAll("[" + hook + "]").forEach(function (el) {
      el.textContent = fill(el.getAttribute(hook));
    });
  }

  function fillHooks(doc, section) {
    each(section, "data-vedur-texti", function (path) {
      return String(data.fieldAt(doc, path));
    });
    each(section, "data-vedur-janei", function (path) {
      const value = data.valueAt(doc, path);
      if (typeof value !== "boolean") throw new data.DataError("„" + path + "“ er ekki já/nei.");
      return value ? "Já" : "Nei";
    });
    each(section, "data-vedur-stada", function (path) {
      return statusText(objectAt(doc, path));
    });
    each(section, "data-vedur-sott", function () { return data.formatDate(doc.uppfaert); });
  }

  // Tafla sem skrunar lárétt þarf fókus svo lyklaborð geti skrunað henni.
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
        { heading: "Sía", key: "faeribreytur" },
        { heading: "Hvað hún biður um", key: "lysing" },
        { heading: "Stöðvar", key: "fjoldi", numeric: true }
      ],
      rows: objectAt(doc, "lysigogn.beidnir")
    }), "Síurnar");
  });

  // Raðirnar í gogn eru þegar raðaðar eftir fjarlægð, næsta fyrst.
  layer.registerRenderer("vedurstodvar-stodvar", function (doc, section) {
    fillHooks(doc, section);
    const chosen = objectAt(doc, "lysigogn.svor.naesta_virka").audkenni;
    const longest = Math.max.apply(null, doc.gogn.map(function (s) { return s.metrar; }));
    const wrapper = layer.buildTable({
      caption: "Stöðvarnar " + data.formatNumber(doc.gogn.length) +
               " innan kassans um VR-II, næsta fyrst",
      columns: [
        { heading: "Stöð (auðkenni)", key: "stod" },
        { heading: "Fjarlægð (m)", key: "metrar", numeric: true },
        { heading: "Mælingar", key: "timabil" },
        { heading: "Staða", key: "stada" }
      ],
      rows: doc.gogn.map(function (s) {
        return {
          stod: s.nafn + " (" + s.audkenni + ")",
          metrar: s.metrar,
          timabil: isActive(s) ? "frá " + s.upphafsar : s.upphafsar + "–" + s.lokaar,
          stada: (isActive(s) ? "✓ Virk" : "✕ Aflögð") +
                 (s.audkenni === chosen ? " ★ forritið les" : "")
        };
      })
    });
    wrapper.querySelectorAll("tbody tr").forEach(function (tr, i) {
      const s = doc.gogn[i];
      if (s.audkenni === chosen) tr.className = "vedur-rod--valin";
      else if (!isActive(s)) tr.className = "vedur-rod--aflogd";
      // Súlan endurtekur töluna sjónrænt; skjálesari les töluna sjálfa.
      const bar = tr.children[1].appendChild(document.createElement("meter"));
      bar.className = "vedur-sula";
      bar.max = longest;
      bar.value = s.metrar;
      bar.setAttribute("aria-hidden", "true");
    });
    addTable(section, wrapper, "Stöðvarnar eftir fjarlægð");
  });
})();
