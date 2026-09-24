/* stada-gagna.js — les web/gogn/yfirlit.json og sýnir hvenær gögnin voru
   síðast uppfærð. Vefurinn talar ALDREI beint við API eða gagnagrunn (kafli 0). */

(function () {
  "use strict";

  // Sniðum dagsetningu sjálf: Intl fellur aftur á ensku í vöfrum sem
  // vantar is-IS gögn, og síðan á að vera alíslensk (regla 1.2).
  const MANUDIR = [
    "janúar", "febrúar", "mars", "apríl", "maí", "júní",
    "júlí", "ágúst", "september", "október", "nóvember", "desember"
  ];

  function islenskDagsetning(dagsetning) {
    return dagsetning.getDate() + ". " +
           MANUDIR[dagsetning.getMonth()] + " " +
           dagsetning.getFullYear();
  }

  function faerslutexti(fjoldi, heimild) {
    if (fjoldi === 0) return "engin gögn sótt enn";
    const ord = fjoldi === 1 ? "færsla" : "færslur";
    return fjoldi + " " + ord + (heimild ? " úr " + heimild : "");
  }

  const reitur = document.querySelector("[data-stada-gagna]");
  if (!reitur) return;

  // Slóðin er afstæð frá síðunni sem kallar — undirsíður gefa upp sína slóð.
  const slod = reitur.dataset.stadaGagna || "gogn/yfirlit.json";

  fetch(slod)
    .then(function (svar) {
      if (!svar.ok) throw new Error("Náði ekki í yfirlit: " + svar.status);
      return svar.json();
    })
    .then(function (gogn) {
      const dagsetning = new Date(gogn.uppfaert);
      if (isNaN(dagsetning.getTime())) throw new Error("Ógild dagsetning í yfirliti");

      const fjoldi = Array.isArray(gogn.gogn) ? gogn.gogn.length : 0;

      const texti = document.createElement("span");
      const sterkt = document.createElement("strong");
      sterkt.textContent = "Gögn uppfærð " + islenskDagsetning(dagsetning);
      texti.appendChild(sterkt);
      texti.appendChild(
        document.createTextNode(" · " + faerslutexti(fjoldi, gogn.heimild))
      );

      const punktur = reitur.querySelector(".stada-gagna__punktur");
      reitur.textContent = "";
      if (punktur) reitur.appendChild(punktur);
      reitur.appendChild(texti);
    })
    .catch(function (villa) {
      // Villur eru aldrei þaggaðar (regla 6) — en síðan brotnar ekki heldur.
      console.warn("Staða gagna ekki tiltæk:", villa.message);
    });
})();
