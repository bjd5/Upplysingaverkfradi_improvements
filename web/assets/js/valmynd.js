/* valmynd.js — opnun og lokun farsímavalmyndar.

   Síðan er fullvirk án þessarar skráar (regla 3.4): sé JavaScript slökkt
   birtist hnappurinn aldrei og valmyndarlistinn stendur opinn. Þess vegna
   setur skráin bæði data-js og aria-expanded sjálf — markup-ið má ekki
   lofa hegðun sem er ekki til staðar.                                     */

(function () {
  "use strict";

  var valmynd = document.querySelector(".valmynd");
  if (!valmynd) return;

  var hnappur = valmynd.querySelector(".valmynd__hnappur");
  var listi = valmynd.querySelector(".valmynd__listi");
  if (!hnappur || !listi) return;

  // Segir CSS að JS sé virkt — fyrr er valmyndin alltaf sýnileg.
  valmynd.dataset.js = "virkt";

  function setjaStodu(opin) {
    valmynd.dataset.opin = String(opin);
    hnappur.setAttribute("aria-expanded", String(opin));
  }

  setjaStodu(false);

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

  // Fari notandinn með lyklaborði út úr valmyndinni lokast hún líka.
  valmynd.addEventListener("focusout", function (atburdur) {
    if (!valmynd.contains(atburdur.relatedTarget) &&
        valmynd.dataset.opin === "true") {
      setjaStodu(false);
    }
  });
})();
