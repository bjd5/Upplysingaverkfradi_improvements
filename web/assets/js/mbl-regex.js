/* mbl-regex.js — síðusértækt efni „Reglulegar segðir á fréttasíðu“ (#23).

   Allar tölur, svör og mynstur koma úr mbl.json gegnum gagnalagið. Enginn
   regex-strengur mbl-æfingarinnar er í þessari skrá. Mynstrin fara á síðuna
   sem textContent, svo þau eru birt sem texti og aldrei túlkuð sem HTML.   */

(function () {
  "use strict";

  const data = window.SiteData;
  const sections = window.DataSection;
  // Lykill verður hluti af slóð (#svar-…); annað snið er gagnavilla.
  const KEY_FORMAT = /^[a-z0-9-]+$/;
  const ANCHOR_PREFIX = "svar-";

  function element(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined) node.textContent = text;
    return node;
  }

  function anchorId(answer) {
    if (!KEY_FORMAT.test(String(answer.lykill))) {
      throw new data.DataError("Ógildur lykill svars: „" + answer.lykill + "“.");
    }
    return ANCHOR_PREFIX + answer.lykill;
  }

  function twoDigits(value) {
    return String(value).padStart(2, "0");
  }

  /** ISO-tími → „16. september 2026 kl. 12:08:51 UTC“. */
  function formatDateTime(iso) {
    const date = new Date(iso);
    return data.formatDate(iso) + " kl. " + twoDigits(date.getUTCHours()) + ":" +
           twoDigits(date.getUTCMinutes()) + ":" + twoDigits(date.getUTCSeconds()) + " UTC";
  }

  // VERBOSE-mynstrin eru inndregin í Python-skránni. Aðeins sameiginlegi
  // inndrátturinn og auðar línur í endana fara; engu öðru er breytt.
  function dedent(pattern) {
    const lines = pattern.replace(/^\s*\n|\n\s*$/g, "").split("\n");
    const indents = lines.filter(function (line) { return line.trim() !== ""; })
      .map(function (line) { return line.length - line.trimStart().length; });
    const indent = Math.min.apply(null, indents);
    return lines.map(function (line) { return line.slice(indent); }).join("\n");
  }

  function code(text) {
    return element("code", "", String(text));
  }

  // Skrunanlegur kóðareitur verður að nást með lyklaborði (regla 3.3).
  function codeBlock(pattern) {
    const pre = element("pre", "mynstur__kodi");
    pre.tabIndex = 0;
    pre.appendChild(code(dedent(pattern)));
    return pre;
  }

  function fact(list, term, value) {
    const row = list.appendChild(element("div"));
    row.appendChild(element("dt", "", term));
    row.appendChild(element("dd", "", value));
  }

  function patternBlock(target, heading, name, flags, pattern) {
    target.appendChild(element("h4", "mynstur__titill", heading));
    const meta = target.appendChild(element("p", "mynstur__heiti"));
    meta.appendChild(code(name));
    if (flags) {
      meta.appendChild(document.createTextNode(" · flögg: "));
      meta.appendChild(code(flags));
    }
    target.appendChild(codeBlock(pattern));
  }

  function fillPattern(target, answer) {
    target.appendChild(element("p", "mynstur__spurning", answer.spurning));
    const facts = target.appendChild(element("dl", "mynstur__tolur"));
    fact(facts, "Svar", data.formatNumber(answer.svar));
    fact(facts, "Samsvaranir alls", data.formatNumber(answer.tilvik));
    fact(facts, "Ólík gildi", data.formatNumber(answer.einstok));
    if (answer.afmorkun_mynstur) {
      patternBlock(target, "Afmörkun á undan", answer.afmorkun_heiti, "",
                   answer.afmorkun_mynstur);
    }
    patternBlock(target, "Mynstrið", answer.mynstur_heiti, answer.mynstur_flogg,
                 answer.mynstur);
    const limit = target.appendChild(element("p", "mynstur__takmorkun"));
    limit.appendChild(element("strong", "", "Takmörkun: "));
    limit.appendChild(document.createTextNode(answer.takmarkanir));
  }

  sections.registerRenderer("mbl-eintak", function (doc, section) {
    section.querySelector("[data-mbl-sott]").textContent =
      formatDateTime(doc.gogn.uppruni.sott);
    section.querySelector("[data-mbl-eintok]").textContent =
      data.formatNumber(doc.gogn.eintok.length);
  });

  sections.registerRenderer("mbl-svor", function (doc, section) {
    const table = element("table", "gagnatafla");
    table.appendChild(element("caption", "", "Spurningarnar, svörin og mynstrin"));
    const head = table.appendChild(element("thead")).appendChild(element("tr"));
    ["Nr.", "Spurning", "Svar", "Mynstur"].forEach(function (heading) {
      head.appendChild(element("th", "", heading)).scope = "col";
    });
    const body = table.appendChild(element("tbody"));
    doc.gogn.svor.forEach(function (answer) {
      const id = anchorId(answer);
      if (!document.getElementById(id)) {
        throw new data.DataError("Mynstrið „" + answer.lykill + "“ á sér engan stað á síðunni.");
      }
      const row = body.appendChild(element("tr"));
      row.appendChild(element("td", "gagnatafla__tala", data.formatNumber(answer.nr)));
      row.appendChild(element("td", "", answer.spurning));
      row.appendChild(element("td", "mynstur-svar", data.formatNumber(answer.svar)));
      const link = element("a", "mynstur-tengill");
      link.href = "#" + id;
      link.appendChild(code(answer.mynstur_heiti));
      row.appendChild(element("td")).appendChild(link);
    });
    const wrapper = element("div", "tafla-umgjord");
    wrapper.appendChild(table);
    section.querySelector("[data-gogn-efni]").appendChild(wrapper);
  });

  sections.registerRenderer("mbl-mynstur", function (doc, section) {
    const answers = new Map(doc.gogn.svor.map(function (answer) {
      return [answer.lykill, answer];
    }));
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
      fillPattern(slot.querySelector("[data-gogn-efni]"), answer);
    });
  });
})();
