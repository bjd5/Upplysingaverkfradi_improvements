/* stada-gagna.js — sýnir á forsíðunni hvenær gögnin voru síðast uppfærð.

   Les yfirlit.json í gegnum sameiginlega gagnalagið (gogn.js) og birtir með
   sama íhlut og gagnahlutarnir (gagnahluti.js), svo dagsetningarsnið og
   villuboð eru á einum stað. Án JavaScript stendur sjálfgefni textinn í
   HTML-inu (regla 3.4).                                                      */

(function () {
  "use strict";

  const DEFAULT_FILE = "yfirlit.json";

  const target = document.querySelector("[data-stada-gagna]");
  if (!target) return;

  function summary(doc) {
    const count = Array.isArray(doc.gogn) ? doc.gogn.length : 0;
    if (count === 0) return "engin gögn sótt enn";
    const noun = count === 1 ? "gagnasafn" : "gagnasöfn";
    return count + " " + noun + " · Heimildir: " + doc.heimild;
  }

  window.SiteData.load(target.dataset.stadaGagna || DEFAULT_FILE)
    .then(function (doc) {
      window.DataSection.fillStatus(target, doc.uppfaert, summary(doc));
    })
    .catch(function (error) {
      window.DataSection.fillStatusError(target, error);
    });
})();
