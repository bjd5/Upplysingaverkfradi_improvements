/* valmynd.js — opnun/lokun farsímavalmyndar og merking núverandi síðu.
   Síðan er fullvirk án þessarar skrár (regla 3.4). */

(function () {
  "use strict";

  const valmynd = document.querySelector(".valmynd");
  if (!valmynd) return;

  const hnappur = valmynd.querySelector(".valmynd__hnappur");
  const listi = valmynd.querySelector(".valmynd__listi");
  if (!hnappur || !listi) return;

  // Segir CSS að JS sé virkt — fyrr er valmyndin alltaf sýnileg.
  valmynd.dataset.js = "virkt";
  valmynd.dataset.opin = "false";

  function setjaStodu(opin) {
    valmynd.dataset.opin = String(opin);
    hnappur.setAttribute("aria-expanded", String(opin));
  }

  hnappur.addEventListener("click", function () {
    setjaStodu(valmynd.dataset.opin !== "true");
  });

  document.addEventListener("keydown", function (atburdur) {
    if (atburdur.key === "Escape" && valmynd.dataset.opin === "true") {
      setjaStodu(false);
      hnappur.focus();
    }
  });

  document.addEventListener("click", function (atburdur) {
    if (!valmynd.contains(atburdur.target) && valmynd.dataset.opin === "true") {
      setjaStodu(false);
    }
  });
})();
