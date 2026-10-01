/* skjalftavaktin.js — síðusértækt efni Skjálftavaktarinnar.

   Sýnidæmi fyrir gagnalagið (issue #19): tölurnar í „Úrtakið í tölum“ fyllir
   gagnahluti.js sjálft út frá data-gogn-reitur. Hér er aðeins það sem reitir
   ná ekki yfir — mánaðartaflan — skráð sem teiknari. Síðan sjálf (#20) byggir
   ofan á þessa skrá.                                                        */

(function () {
  "use strict";

  const data = window.SiteData;

  window.DataSection.registerRenderer("skjalftar-manudir", function (doc, section) {
    // Skráin geymir einn dag per línu; taflan sýnir mánuði.
    const months = new Map();
    doc.gogn.forEach(function (day) {
      const key = day.dagur.slice(0, 7);
      const month = months.get(key) || { manudur: key, dagar: 0, atburdir: 0 };
      month.dagar += 1;
      month.atburdir += day.fjoldi;
      months.set(key, month);
    });
    const rows = Array.from(months.values()).map(function (row) {
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
