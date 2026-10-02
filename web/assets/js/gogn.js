/* gogn.js — sameiginlega gagnalagið: sækir web/gogn/<skrá>.json (issue #19).

   Vefurinn talar ALDREI við API eða gagnagrunn (kafli 0). Hann les aðeins
   afleiddu JSON-skrárnar sem útflutningurinn skrifar (utflutningur/json_skrif.py),
   á sniðinu (regla 5.4):
     {"uppfaert": ISO, "heimild": texti, "gogn": [raðir], "lysigogn": {…}?}
   gogn er alltaf listi af röðum; lysigogn (valfrjálst) ber það sem síðan þarf
   til að lesa þær. Aðrir reitir eru ekki leyfðir, hvorki þar né hér.

   Þetta er EINA skráin á vefnum sem kallar í fetch. Hún sækir, staðfestir og
   sníður; birtingin á síðunni er í gagnahluti.js. Mynstrið sem síður nota er
   skjalfest í docs/vefur-gogn.md.                                            */

(function () {
  "use strict";

  // Slóðir eru reiknaðar frá þessari skrá (assets/js/ → ../../gogn/), ekki
  // frá síðunni. Þannig virkar sama kall frá index.html og sidur/*.html og
  // web/ er sjálfstætt birtanleg (regla 1.1).
  const DATA_ROOT = new URL("../../gogn/", document.currentScript.src);

  const REQUIRED_FIELDS = ["uppfaert", "heimild", "gogn"];
  const METADATA_FIELD = "lysigogn";
  const ALLOWED_FIELDS = REQUIRED_FIELDS.concat([METADATA_FIELD]);
  // Slóð í reit byrjar alltaf á öðrum þessara: "lysigogn.samantekt.atburdir"
  // eða "gogn.0.fjoldi". Rótin er skrifuð út svo lesandi HTML-sins sjái
  // strax hvaðan talan kemur.
  const FIELD_ROOTS = ["gogn", METADATA_FIELD];
  const HTTP_NOT_FOUND = 404;

  // Ísland er á UTC allt árið; fast tímabelti svo dagsetningin sé sú sama
  // hvar sem lesandinn er staddur.
  const TIME_ZONE = "Atlantic/Reykjavik";
  const MONTHS = [
    "janúar", "febrúar", "mars", "apríl", "maí", "júní",
    "júlí", "ágúst", "september", "október", "nóvember", "desember"
  ];
  // Sama snið og utflutningur/islenskt_snid.py: 61.161 og 2,95.
  const THOUSANDS_SEPARATOR = ".";
  const DECIMAL_SEPARATOR = ",";

  const cache = new Map();

  /** Villa sem má sýna lesanda: skilaboðin eru á íslensku. */
  class DataError extends Error {
    constructor(message, fileName) {
      super(message);
      this.name = "DataError";
      this.fileName = fileName;
    }
  }

  /** Full slóð gagnaskrár, t.d. fyrir tengil á hana í villuboðum. */
  function fileUrl(fileName) {
    return new URL(fileName, DATA_ROOT).href;
  }

  function isPlainObject(value) {
    return value !== null && typeof value === "object" && !Array.isArray(value);
  }

  function validate(doc, fileName) {
    if (!isPlainObject(doc)) {
      throw new DataError("Gagnaskráin „" + fileName + "“ er á röngu sniði.", fileName);
    }
    REQUIRED_FIELDS.forEach(function (field) {
      if (!(field in doc)) {
        throw new DataError("Í gagnaskrána „" + fileName + "“ vantar reitinn „" +
                            field + "“.", fileName);
      }
    });
    if (typeof doc.uppfaert !== "string" || isNaN(new Date(doc.uppfaert).getTime())) {
      throw new DataError("Dagsetningin í „" + fileName + "“ er ógild.", fileName);
    }
    if (typeof doc.heimild !== "string" || doc.heimild.trim() === "") {
      throw new DataError("Heimild vantar í „" + fileName + "“.", fileName);
    }
    Object.keys(doc).forEach(function (field) {
      if (ALLOWED_FIELDS.indexOf(field) === -1) {
        throw new DataError("Óþekktur reitur „" + field + "“ í „" + fileName + "“.",
                            fileName);
      }
    });
    if (!Array.isArray(doc.gogn) || !doc.gogn.every(isPlainObject)) {
      throw new DataError("Gögnin í „" + fileName + "“ eru ekki listi af röðum.",
                          fileName);
    }
    if (METADATA_FIELD in doc && !isPlainObject(doc.lysigogn)) {
      throw new DataError("Lýsigögnin í „" + fileName + "“ eru á röngu sniði.", fileName);
    }
    return doc;
  }

  /**
   * Sækir og staðfestir eina gagnaskrá. Hver skrá er sótt einu sinni á síðu,
   * þótt margir hlutar noti hana.
   * @param {string} fileName t.d. "skjalftar.json"
   * @returns {Promise<{uppfaert: string, heimild: string, gogn: Array<Object>,
   *          lysigogn: (Object|undefined)}>}
   *          Hafnar alltaf með DataError sem hefur íslensk skilaboð.
   */
  function load(fileName) {
    if (!cache.has(fileName)) {
      const request = fetch(fileUrl(fileName))
        .catch(function () {
          throw new DataError("Ekki náðist samband til að sækja „" + fileName + "“.",
                              fileName);
        })
        .then(function (response) {
          if (!response.ok) {
            const reason = response.status === HTTP_NOT_FOUND ? "fannst ekki" : "fékkst ekki";
            throw new DataError("Gagnaskráin „" + fileName + "“ " + reason + " (villa " +
                                response.status + ").", fileName);
          }
          return response.json().catch(function () {
            throw new DataError("Gagnaskráin „" + fileName + "“ er gölluð.", fileName);
          });
        })
        .then(function (doc) { return validate(doc, fileName); });
      cache.set(fileName, request);
    }
    return cache.get(fileName);
  }

  /** Flettir upp punktaslóð ("dypt_km.midgildi", "0.fjoldi") í hlut eða lista. */
  function valueAt(data, path) {
    return path.split(".").reduce(function (value, key) {
      return value !== null && typeof value === "object" ? value[key] : undefined;
    }, data);
  }

  /**
   * Eitt gildi úr skjali eftir slóðavenju reitanna: slóðin byrjar á "lysigogn."
   * eða "gogn.<röð>.". Skilar tölu eða streng; annað er villa sem sést.
   * @param {Object} doc staðfest skjal úr load()
   * @param {string} path t.d. "lysigogn.samantekt.atburdir"
   */
  function fieldAt(doc, path) {
    if (FIELD_ROOTS.indexOf(path.split(".")[0]) === -1) {
      throw new DataError("Slóðin „" + path + "“ verður að byrja á „lysigogn.“ eða " +
                          "„gogn.“.");
    }
    const value = valueAt(doc, path);
    if (typeof value !== "number" && typeof value !== "string") {
      throw new DataError("Gildið „" + path + "“ er ekki tala eða texti í gagnaskránni.");
    }
    return value;
  }

  /**
   * Íslenskt talnasnið. Tölurnar eru þegar námundaðar í JSON og eru ALDREI
   * námundaðar hér: 4.67 → "4,67", 61161 → "61.161", 3.0 → "3".
   * Strengir koma óbreyttir til baka — þeir eru þegar sniðnir.
   */
  function formatNumber(value) {
    if (typeof value === "string") return value;
    if (typeof value !== "number" || !isFinite(value)) {
      throw new DataError("Gildið „" + String(value) + "“ er ekki tala.");
    }
    const digits = String(Math.abs(value));
    // Veldisrithátt (1e21) er ekki hægt að skipta í þúsundir; hann kemur óbreyttur.
    if (digits.indexOf("e") !== -1) return String(value);
    const parts = digits.split(".");
    const whole = parts[0].replace(/\B(?=(\d{3})+(?!\d))/g, THOUSANDS_SEPARATOR);
    const sign = value < 0 ? "-" : "";
    return sign + whole + (parts[1] ? DECIMAL_SEPARATOR + parts[1] : "");
  }

  // Eiginleikaprófun, ekki þögguð villa: vanti vafrann íslensk Intl-gögn eða
  // tímabeltið fellur Intl hljóðlaust á ensku, og þá er eigið snið notað.
  function createIntlFormat() {
    try {
      const format = new Intl.DateTimeFormat("is-IS", {
        day: "numeric", month: "long", year: "numeric", timeZone: TIME_ZONE
      });
      return format.resolvedOptions().locale.indexOf("is") === 0 ? format : null;
    } catch (error) {
      return null;
    }
  }

  const intlFormat = createIntlFormat();

  /** ISO-dagsetning → "10. september 2026". */
  function formatDate(iso) {
    const date = new Date(iso);
    if (isNaN(date.getTime())) throw new DataError("Ógild dagsetning: „" + iso + "“.");
    if (intlFormat) return intlFormat.format(date);
    return date.getUTCDate() + ". " + MONTHS[date.getUTCMonth()] + " " +
           date.getUTCFullYear();
  }

  /** Mánuður "2023-11" → "nóvember 2023". Rangt snið fellur með villu. */
  function formatMonth(isoMonth) {
    const match = /^(\d{4})-(\d{2})$/.exec(isoMonth);
    const month = match ? Number(match[2]) : 0;
    if (month < 1 || month > MONTHS.length) {
      throw new DataError("Ógildur mánuður: „" + isoMonth + "“.");
    }
    return MONTHS[month - 1] + " " + match[1];
  }

  window.SiteData = Object.freeze({
    DataError: DataError,
    load: load,
    fileUrl: fileUrl,
    valueAt: valueAt,
    fieldAt: fieldAt,
    formatNumber: formatNumber,
    formatDate: formatDate,
    formatMonth: formatMonth
  });
})();
