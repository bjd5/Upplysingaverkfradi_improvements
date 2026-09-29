/* gagnahluti.js — birtir gögn úr gogn.js á síðunni (issue #19).

   Krefst gogn.js á undan sér. Síða merkir gagnahluta í HTML:

     <section data-gogn="skjalftar.json" [data-gogn-teiknari="nafn"]>
       <noscript>…varaleið án JavaScript…</noscript>
       <div data-gogn-efni hidden>
         … <span data-gogn-reitur="lysigogn.samantekt.atburdir"></span> …
       </div>
       [<p class="stada-gagna" data-gogn-uppruni>…</p>]
     </section>

   Á meðan gögnin hlaðast stendur „Sæki gögn …“ efst í hlutanum. Takist það
   birtist efnið og „Gögn uppfærð … · Heimild: …“ neðst. Mistakist það birtast
   íslensk villuboð í hlutanum sjálfum og efnið helst falið — aldrei auður
   reitur eða hálffyllt tafla (regla 6). Allt er byggt með createElement;
   innerHTML er aldrei notað, svo gagnaskrá getur ekki orðið innspýtingarleið.
   Nánar í docs/vefur-gogn.md.                                                */

(function () {
  "use strict";

  const data = window.SiteData;
  const renderers = new Map();

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function readableMessage(error) {
    return error instanceof data.DataError
      ? error.message
      : "Óvænt villa kom upp við að birta gögnin.";
  }

  function fillStatusParts(target, state, strongText, restText) {
    const dot = element("span", "stada-gagna__punktur");
    dot.setAttribute("aria-hidden", "true");
    const text = element("span");
    text.appendChild(element("strong", "", strongText));
    text.appendChild(document.createTextNode(restText));
    target.textContent = "";
    target.appendChild(dot);
    target.appendChild(text);
    target.dataset.stada = state;
  }

  /**
   * Fyllir stada-gagna-einingu: „Gögn uppfærð <dags.> · <nánar>“.
   * Punkturinn er skraut; textinn ber merkinguna (regla 3.3).
   */
  function fillStatus(target, iso, detail) {
    fillStatusParts(target, "i-lagi", "Gögn uppfærð " + data.formatDate(iso),
                    " · " + detail);
  }

  /** Villa í stada-gagna-einingu — sést á síðunni, ekki bara í console. */
  function fillStatusError(target, error) {
    fillStatusParts(target, "villa", "Villa:", " " + readableMessage(error));
    console.error("[gagnahluti.js]", error);
  }

  /**
   * Byggir töflu úr röðum gagnanna, innan í .tafla-umgjord (skrunar lárétt,
   * síðan ekki). Tölur fá íslenskt snið, en eru ekki námundaðar.
   * @param {{caption: string, columns: Array<{heading: string, key: string,
   *          numeric?: boolean}>, rows: Array<Object>}} spec
   * rows eru venjulega doc.gogn (raðirnar) eða listi úr doc.lysigogn.
   * @returns {HTMLDivElement}
   */
  function buildTable(spec) {
    const table = element("table", "gagnatafla");
    table.appendChild(element("caption", "", spec.caption));
    const headRow = element("tr");
    spec.columns.forEach(function (column) {
      const cell = element("th", column.numeric ? "gagnatafla__tala" : "", column.heading);
      cell.scope = "col";
      headRow.appendChild(cell);
    });
    table.appendChild(element("thead")).appendChild(headRow);
    const body = table.appendChild(element("tbody"));
    spec.rows.forEach(function (row) {
      const tr = body.appendChild(element("tr"));
      spec.columns.forEach(function (column) {
        const value = data.valueAt(row, column.key);
        if (value === undefined) {
          throw new data.DataError("Dálkinn „" + column.key + "“ vantar í gögnin.");
        }
        tr.appendChild(element("td", column.numeric ? "gagnatafla__tala" : "",
                               column.numeric ? data.formatNumber(value) : String(value)));
      });
    });
    const wrapper = element("div", "tafla-umgjord");
    wrapper.appendChild(table);
    return wrapper;
  }

  /**
   * Síðuskrá skráir teiknara fyrir efni sem reitir ná ekki yfir (töflur o.fl.):
   * render(skjal, hluti), þar sem skjal = {uppfaert, heimild, gogn, lysigogn}. Kasti
   * teiknarinn villu birtist hún í hlutanum eins og aðrar villur.
   */
  function registerRenderer(name, render) {
    renderers.set(name, render);
  }

  function fillFields(section, doc) {
    section.querySelectorAll("[data-gogn-reitur]").forEach(function (field) {
      field.textContent = data.formatNumber(data.fieldAt(doc, field.dataset.gognReitur));
    });
  }

  function runRenderer(section, doc, fileName) {
    const name = section.dataset.gognTeiknari;
    if (!name) return;
    const render = renderers.get(name);
    if (!render) {
      throw new data.DataError("Enginn teiknari er skráður undir „" + name + "“.",
                               fileName);
    }
    render(doc, section);
  }

  function showProvenance(section, doc) {
    let target = section.querySelector("[data-gogn-uppruni]");
    if (!target) {
      target = section.appendChild(element("p", "stada-gagna"));
      target.dataset.gognUppruni = "";
    }
    fillStatus(target, doc.uppfaert, "Heimild: " + doc.heimild);
  }

  function showError(section, status, error, fileName) {
    status.className = "gogn-villa";
    status.setAttribute("role", "alert");
    status.textContent = "";
    status.appendChild(element("strong", "gogn-villa__titill",
                               "Ekki tókst að birta gögnin í þessum hluta."));
    status.appendChild(element("span", "", " " + readableMessage(error) + " "));
    const link = element("a", "gogn-villa__tengill", "Opna gagnaskrána");
    link.href = data.fileUrl(fileName);
    status.appendChild(link);
    section.dataset.gognStada = "villa";
    console.error("[gagnahluti.js] " + fileName + ":", error);
  }

  function processSection(section) {
    const fileName = section.dataset.gogn;
    const status = element("p", "gogn-stada", "Sæki gögn …");
    status.setAttribute("role", "status");
    // Staðan fer þar sem efnið á að birtast — á eftir fyrirsögn hlutans.
    const content = section.querySelector("[data-gogn-efni]");
    section.insertBefore(status, content && content.parentNode === section ? content : null);
    section.dataset.gognStada = "hledst";
    section.setAttribute("aria-busy", "true");

    return data.load(fileName)
      .then(function (doc) {
        fillFields(section, doc);
        runRenderer(section, doc, fileName);
        section.querySelectorAll("[data-gogn-efni]").forEach(function (content) {
          content.hidden = false;
        });
        showProvenance(section, doc);
        status.remove();
        section.dataset.gognStada = "tilbuid";
      })
      .catch(function (error) { showError(section, status, error, fileName); })
      .finally(function () { section.removeAttribute("aria-busy"); });
  }

  let started = false;

  // Hefst á DOMContentLoaded, sem kemur á eftir ÖLLUM defer-skriftum: síðuskrár
  // sem hlaðast á eftir þessari ná því að skrá teiknara fyrst.
  function start() {
    if (started) return;
    started = true;
    document.querySelectorAll("[data-gogn]").forEach(processSection);
  }

  if (!data) {
    // Röng röð skrifta er forritunarvilla; hún á að sjást strax.
    throw new Error("gagnahluti.js þarf gogn.js á undan sér.");
  }

  if (document.readyState === "complete") {
    start();
  } else {
    document.addEventListener("DOMContentLoaded", start);
    window.addEventListener("load", start);
  }

  window.DataSection = Object.freeze({
    fillStatus: fillStatus,
    fillStatusError: fillStatusError,
    buildTable: buildTable,
    registerRenderer: registerRenderer
  });
})();
