/* mbl-regex.js — birtir spurningarnar fimm um forsíðu mbl.is (issue #23).

   Mynstrin koma orðrétt úr mbl.json; hér er enginn regex-strengur. Teiknarinn
   byggir eitt spjald á hverja spurningu og eintaksupplýsingar efst.          */

(function () {
  "use strict";

  const data = window.SiteData;

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function codeBlock(label, source) {
    const wrap = element("div", "mbl-spjald__kodi");
    wrap.appendChild(element("h4", "mbl-spjald__undirtitill", label));
    const pre = element("pre");
    pre.tabIndex = 0;
    pre.appendChild(element("code", "", source.trim()));
    wrap.appendChild(pre);
    return wrap;
  }

  function fact(list, term, value) {
    const row = list.appendChild(element("div"));
    row.appendChild(element("dt", "", term));
    row.appendChild(element("dd", "", value));
  }

  function buildCard(row) {
    const card = element("section", "mbl-spjald");
    const id = "mbl-spurning-" + row.nr;
    card.setAttribute("aria-labelledby", id);
    const title = card.appendChild(element("h4", "mbl-spjald__spurning", row.spurning));
    title.id = id;
    card.appendChild(element("p", "mbl-spjald__svar", row.svar));
    card.appendChild(codeBlock("Mynstrið sem gaf svarið (" + row.mynstur_flogg + ")", row.mynstur));
    if (row.afmorkun_mynstur) {
      card.appendChild(codeBlock("Leitin er afmörkuð með", row.afmorkun_mynstur));
    }
    const facts = card.appendChild(element("dl", "stadreyndir"));
    fact(facts, "Tilvik sem mynstrið fann", data.formatNumber(row.tilvik));
    fact(facts, "Einstök", data.formatNumber(row.einstok));
    fact(facts, "Dæmi um fund", row.synishorn);
    card.appendChild(element("p", "mbl-spjald__takmorkun", "Les ekki: " + row.takmarkanir));
    return card;
  }

  window.DataSection.registerRenderer("mbl-svor", function (doc, section) {
    const copy = doc.lysigogn.eintak;
    const content = section.querySelector("[data-gogn-efni]");
    const facts = content.querySelector("[data-mbl-eintak]");
    fact(facts, "Slóð", copy.slod);
    fact(facts, "Sótt", data.formatDate(copy.sott));
    fact(facts, "Stærð", data.formatNumber(copy.baeti) + " bæti");
    const list = content.querySelector("[data-mbl-spjold]");
    doc.gogn.forEach(function (row) { list.appendChild(buildCard(row)); });
  });
})();
