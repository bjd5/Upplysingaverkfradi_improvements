/* phoebe-myndrit.js — láréttar súlur á Phoebe-síðunum (issue #24).

   Teikniararnir sækja lista úr gagnaskránni og teikna SVG með
   createElementNS inn í hvern [data-myndrit] — aldrei innerHTML. Súlurnar
   byrja í núlli. Tölurnar standa líka í HTML-töflu við hverja mynd, svo síðan
   er læsileg án JavaScript (regla 3.4); myndin er viðbót.                  */

(function () {
  "use strict";

  const data = window.SiteData;
  const SVG_NS = "http://www.w3.org/2000/svg";
  const WIDTH = 400;
  const ROW_HEIGHT = 28;
  const BAR_HEIGHT = 18;
  const TOP = 30;
  const BOTTOM = 24;
  const RIGHT_MARGIN = 44;

  function node(name, attributes, text) {
    const item = document.createElementNS(SVG_NS, name);
    Object.keys(attributes).forEach(function (key) {
      item.setAttribute(key, attributes[key]);
    });
    if (text !== undefined) item.textContent = text;
    return item;
  }

  /**
   * Teiknar láréttar súlur. spec: {title, items: [{label, value}], labelWidth,
   * step, reference?: {value, label}}. Kvarðinn nær upp í næsta margfeldi af
   * step yfir stærsta gildið (eða viðmiðið).
   */
  function drawBars(spec) {
    const peak = Math.max.apply(null, spec.items.map(function (i) { return i.value; })
      .concat(spec.reference ? [spec.reference.value] : []));
    const max = Math.ceil(peak / spec.step) * spec.step;
    const left = spec.labelWidth;
    const scale = (WIDTH - left - RIGHT_MARGIN) / max;
    const height = TOP + spec.items.length * ROW_HEIGHT + BOTTOM;
    const svg = node("svg", {
      viewBox: "0 0 " + WIDTH + " " + height, role: "img", class: "stolparit",
      "aria-label": spec.title + ". Tölurnar eru í töflunni hér fyrir neðan."
    });

    for (let tick = 0; tick <= max + spec.step / 2; tick += spec.step) {
      const x = left + tick * scale;
      svg.appendChild(node("line", { class: "stolparit__grind", x1: x, x2: x,
                                      y1: TOP - 6, y2: height - BOTTOM }));
      svg.appendChild(node("text", { class: "stolparit__texti", x: x, y: height - 6,
                                      "text-anchor": "middle" }, data.formatNumber(tick)));
    }
    spec.items.forEach(function (item, index) {
      const y = TOP + index * ROW_HEIGHT;
      const width = item.value * scale;
      svg.appendChild(node("text", { class: "stolparit__texti", x: left - 8, y: y + 14,
                                      "text-anchor": "end" }, item.label));
      svg.appendChild(node("rect", { class: "stolparit__sula", x: left, y: y,
                                      width: width, height: BAR_HEIGHT }));
      svg.appendChild(node("text", { class: "stolparit__gildi", x: left + width + 6,
                                      y: y + 14 }, data.formatNumber(item.value)));
    });
    if (spec.reference) {
      const x = left + spec.reference.value * scale;
      svg.appendChild(node("line", { class: "stolparit__vidmid", x1: x, x2: x,
                                      y1: TOP - 6, y2: height - BOTTOM }));
      const flip = spec.reference.value > max / 2;
      svg.appendChild(node("text", { class: "stolparit__vidmid-texti",
                                      x: flip ? x - 4 : x + 4, y: 12,
                                      "text-anchor": flip ? "end" : "start" },
                           spec.reference.label + " (" + data.formatNumber(spec.reference.value) + ")"));
    }
    return svg;
  }

  function draw(section, name, spec) {
    const target = section.querySelector('[data-myndrit="' + name + '"]');
    if (!target) {
      throw new data.DataError("Myndritið „" + name + "“ vantar á síðuna.");
    }
    target.appendChild(drawBars(spec));
  }

  window.DataSection.registerRenderer("phoebe-tolfraedi", function (doc, section) {
    const phoebe = doc.gogn.filter(function (row) { return row.persona === "Phoebe"; });
    draw(section, "plass", {
      title: "Hlutdeild Phoebe af línum vinanna sex eftir þáttaröðum, í prósentum",
      items: phoebe.map(function (row) {
        return { label: "Þáttaröð " + row.thattarod, value: row.hlutdeild_prosent };
      }),
      labelWidth: 96, step: 5,
      reference: { value: doc.lysigogn.jafn_hlutur_prosent, label: "Jafn hlutur" }
    });
    draw(section, "naervera", {
      title: "Hve oft Phoebe er nefnd í tali á hvern þátt, eftir þáttaröðum",
      items: doc.lysigogn.naervera.map(function (row) {
        return { label: "Þáttaröð " + row.thattarod, value: row.i_tali_a_thatt };
      }),
      labelWidth: 96, step: 2
    });
    draw(section, "tengsl", {
      title: "Leiðrétt tengsl hvers vinar við Phoebe (lift)",
      items: doc.lysigogn.tengsl.map(function (row) {
        return { label: row.persona, value: row.lift };
      }),
      labelWidth: 96, step: 0.5,
      reference: { value: 1, label: "Samkvæmt málgleði" }
    });
  });

  window.DataSection.registerRenderer("central-perk-hopar", function (doc, section) {
    draw(section, "hopar", {
      title: "Miðgildi hlutdeildar Phoebe af orðum aðalpersónanna eftir hópum, í prósentum",
      items: doc.lysigogn.hopar.map(function (row) {
        return { label: row.heiti, value: row.midgildi_prosent };
      }),
      labelWidth: 150, step: 5
    });
  });
})();
