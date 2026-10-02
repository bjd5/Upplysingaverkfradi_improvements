/* skjalftavaktin.js — síðusértækt efni Skjálftavaktarinnar.

   Sýnidæmi fyrir gagnalagið (issue #19): tölurnar í „Úrtakið í tölum“ fyllir
   gagnahluti.js sjálft út frá data-gogn-reitur. Hér er aðeins það sem reitir
   ná ekki yfir — mánaðartaflan — skráð sem teiknari. Síðan sjálf (#20) byggir
   ofan á þessa skrá.                                                        */

(function () {
  "use strict";

  const data = window.SiteData;

  window.DataSection.registerRenderer("skjalftar-manudir", function (doc, section) {
    // Mánaðasamantektin er í lysigogn; daglegu raðirnar (doc.gogn) eiga heima
    // í HTML-töflu myndritsins, sem verður að virka án JavaScript (#17).
    const rows = doc.lysigogn.manudir.map(function (row) {
      return { manudur: data.formatMonth(row.manudur), dagar: row.dagar,
               atburdir: row.atburdir };
    });
    const table = window.DataSection.buildTable({
      caption: "Atburðir eftir mánuðum",
      columns: [
        { heading: "Mánuður", key: "manudur" },
        { heading: "Dagar", key: "dagar", numeric: true },
        { heading: "Atburðir", key: "atburdir", numeric: true }
      ],
      rows: rows
    });
    section.querySelector("[data-gogn-efni]").appendChild(table);
  });
})();
