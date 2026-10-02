/* mbl-regex.js — teiknarar síðunnar „Reglulegar segðir á fréttasíðu“ (#23).
   Svör og mynstur koma úr mbl.json (gogn = svörin fimm, lysigogn = eintakið).
   Enginn regex-strengur æfingarinnar er hér; allt fer inn sem textContent. */

(function () {
  "use strict";

  const data = window.SiteData;
  const KEY_FORMAT = /^[a-z0-9-]+$/;  // lykillinn verður #svar-<lykill>
  // Sýnishorn er aðeins birt í greinum merktum data-mbl-synishorn (ekki
  // fréttatexti) og aðeins ef það er stutt — höfundarréttur, sjá síðuna.
  const MAX_SAMPLE = 200;

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = String(text);
    return node;
  }

  function anchorId(answer) {
    if (!KEY_FORMAT.test(answer.lykill)) {
      throw new data.DataError("Ógildur lykill svars: „" + answer.lykill + "“.");
    }
    return "svar-" + answer.lykill;
  }

  // VERBOSE-mynstrin eru inndregin í Python-skránni. Aðeins sameiginlegur
  // inndráttur og auðar endalínur fara; engu öðru er breytt.
  function dedent(pattern) {
    const lines = pattern.replace(/^\s*\n|\n\s*$/g, "").split("\n");
    const indent = Math.min.apply(null, lines.filter(function (l) { return l.trim(); })
      .map(function (l) { return l.length - l.trimStart().length; }));
    return lines.map(function (l) { return l.slice(indent); }).join("\n");
  }

  // Skrunanlegur kóðareitur verður að nást með lyklaborði (regla 3.3).
  function codeBlock(target, heading, name, flags, text) {
    target.appendChild(element("h4", "mynstur__titill", heading));
    if (name) {
      const meta = target.appendChild(element("p", "mynstur__heiti"));
      meta.appendChild(element("code", "", name));
      if (flags) meta.append(" · flögg: ", element("code", "", flags));
    }
    const pre = target.appendChild(element("pre", "mynstur__kodi"));
    pre.tabIndex = 0;
    pre.appendChild(element("code", "", text));
  }

  function fact(list, term, value) {
    const row = list.appendChild(element("div"));
    row.append(element("dt", "", term), element("dd", "", value));
  }

  function fillPattern(slot, answer) {
    const target = slot.querySelector("[data-gogn-efni]");
    target.appendChild(element("p", "mynstur__spurning", answer.spurning));
    const facts = target.appendChild(element("dl", "mynstur__tolur"));
    fact(facts, "Svar", answer.svar);
    fact(facts, "Samsvaranir alls", data.formatNumber(answer.tilvik));
    fact(facts, "Ólík gildi", data.formatNumber(answer.einstok));
    if (answer.afmorkun_mynstur) {
      codeBlock(target, "Afmörkun á undan", answer.afmorkun_heiti, "",
                dedent(answer.afmorkun_mynstur));
    }
    codeBlock(target, "Mynstrið", answer.mynstur_heiti, answer.mynstur_flogg,
              dedent(answer.mynstur));
    if ("mblSynishorn" in slot.dataset && answer.synishorn.length <= MAX_SAMPLE) {
      codeBlock(target, "Sýnishorn úr eintakinu", "", "", answer.synishorn);
    }
    const limit = target.appendChild(element("p", "mynstur__takmorkun"));
    limit.append(element("strong", "", "Takmörkun: "), answer.takmarkanir);
  }

  window.DataSection.registerRenderer("mbl-eintak", function (doc, section) {
    const iso = doc.lysigogn.eintak.sott;
    // Ísland er á UTC allt árið, svo UTC-tíminn er líka íslenskur tími.
    const time = new Date(iso).toISOString().slice(11, 19);
    section.querySelector("[data-mbl-sott]").textContent =
      data.formatDate(iso) + " kl. " + time + " UTC";
    section.querySelector("[data-mbl-eintok]").textContent =
      data.formatNumber(doc.lysigogn.eintok.length);
  });

  window.DataSection.registerRenderer("mbl-svor", function (doc, section) {
    const table = element("table", "gagnatafla");
    table.appendChild(element("caption", "", "Spurningarnar, svörin og mynstrin"));
    const head = table.appendChild(element("thead")).appendChild(element("tr"));
    ["Nr.", "Spurning", "Svar og mynstur"].forEach(function (heading) {
      head.appendChild(element("th", "", heading)).scope = "col";
    });
    const body = table.appendChild(element("tbody"));
    doc.gogn.forEach(function (answer) {
      const id = anchorId(answer);
      if (!document.getElementById(id)) {
        throw new data.DataError("Mynstrið „" + answer.lykill + "“ á sér engan stað á síðunni.");
      }
      const row = body.appendChild(element("tr"));
      row.append(element("td", "gagnatafla__tala", data.formatNumber(answer.nr)),
                 element("td", "", answer.spurning));
      const cell = row.appendChild(element("td"));
      cell.appendChild(element("span", "mynstur-svar", answer.svar));
      const link = cell.appendChild(element("a", "mynstur-tengill"));
      link.href = "#" + id;
      link.appendChild(element("code", "", answer.mynstur_heiti));
    });
    const wrapper = element("div", "tafla-umgjord");
    wrapper.appendChild(table);
    section.querySelector("[data-gogn-efni]").appendChild(wrapper);
  });

  window.DataSection.registerRenderer("mbl-mynstur", function (doc, section) {
    const answers = new Map(doc.gogn.map(function (a) { return [a.lykill, a]; }));
    const slots = section.querySelectorAll("[data-mbl-svar]");
    // Svar án mynsturs á síðunni (eða öfugt) má ekki hverfa hljóðlaust (regla 8).
    if (slots.length !== answers.size) {
      throw new data.DataError("Síðan hefur " + slots.length + " mynstur en gögnin " +
                               answers.size + ".");
    }
    slots.forEach(function (slot) {
      const answer = answers.get(slot.dataset.mblSvar);
      if (!answer) {
        throw new data.DataError("Svarið „" + slot.dataset.mblSvar + "“ er ekki í gögnunum.");
      }
      fillPattern(slot, answer);
    });
  });
})();
