/* hagstofan.js — töflur og json-stat2-dæmið á Hagstofusíðunni (issue #21).

   Stakar tölur fyllir gagnahluti.js út frá data-gogn-reitur. Hér er aðeins
   það sem byggist á listum: töflurnar, fyrirspurnin og dæmið um hvernig
   flati value-listinn er lesinn. Allt kemur úr web/gogn/hagstofan.json;
   hér er hvorki námundað né fyllt upp með núllum (docs/vefur-gogn.md).    */

(function () {
  "use strict";

  const data = window.SiteData;
  const section = window.DataSection;

  const ALL = "Alls";
  // Summa flokka sem ná yfir allan hópinn; frávik stafar af námundun.
  const WHOLE = 100;
  // Dæmið: brautskráðar konur í verkfræði. Víddir með einum völdum kóða
  // taka hann sjálfkrafa.
  const EXAMPLE = { "Nemendur": "5", "Námssvið": "07", "Kyn": "2" };
  const EXAMPLE_GROUP = { namssvid_kodi: "07", kyn_kodi: "2" };

  function slot(root, name) {
    const target = root.querySelector("[data-hagstofan-tafla='" + name + "']");
    if (!target) throw new data.DataError("Staðinn fyrir töfluna „" + name + "“ vantar.");
    return target;
  }

  /** buildTable gefur aðeins dálkafyrirsagnir; fremstu dálkarnir eru raðafyrirsagnir. */
  function table(spec, rowHeaders) {
    const wrapper = section.buildTable(spec);
    wrapper.querySelectorAll("tbody tr").forEach(function (tr) {
      Array.prototype.slice.call(tr.cells, 0, rowHeaders).forEach(function (td) {
        const th = document.createElement("th");
        th.scope = "row";
        th.textContent = td.textContent;
        tr.replaceChild(th, td);
      });
    });
    return wrapper;
  }

  function statusColumns(doc) {
    return doc.lysigogn.stodur.map(function (status) {
      return { heading: status.heiti + " (%)", key: status.reitur, numeric: true };
    });
  }

  function groupLabel(group) {
    return group.namssvid + " · " + group.kyn;
  }

  /** Ör + formerki + orð: merkingin er aldrei í lit einum (regla 3.3). */
  function difference(points) {
    const text = data.formatNumber(Math.abs(points));
    if (points > 0) return "▲ +" + text + " (A hærri)";
    if (points < 0) return "▼ −" + text + " (A lægri)";
    return "= 0 (jafnt)";
  }

  function renderResults(doc, root) {
    const rows = doc.gogn;
    slot(root, "svid").appendChild(table({
      caption: "Staða árgangsins eftir námssviði, bæði kyn",
      columns: [{ heading: "Námssvið", key: "namssvid" }].concat(statusColumns(doc)),
      rows: rows.filter(function (row) { return row.kyn_kodi === ALL; })
    }, 1));
    slot(root, "kyn").appendChild(table({
      caption: "Staða árgangsins eftir námssviði og kyni",
      columns: [{ heading: "Námssvið", key: "namssvid" }, { heading: "Kyn", key: "kyn" }]
        .concat(statusColumns(doc)),
      rows: rows.filter(function (row) { return row.kyn_kodi !== ALL; })
    }, 2));
    slot(root, "summur").appendChild(table({
      caption: "Summa flokkanna þriggja í hverjum hópi",
      columns: [{ heading: "Námssvið", key: "namssvid" }, { heading: "Kyn", key: "kyn" },
                { heading: "Summa (%)", key: "samtals", numeric: true },
                { heading: "Skýring", key: "skyring" }],
      rows: rows.map(function (row) {
        return { namssvid: row.namssvid, kyn: row.kyn, samtals: row.samtals,
                 skyring: row.samtals === WHOLE ? "= 100" : "≈ 100 — námundun" };
      })
    }, 2));
    slot(root, "munir").appendChild(table({
      caption: "Munur á brautskráningarhlutfalli, hópur A − hópur B",
      columns: [{ heading: "Samanburður", key: "lysing" }, { heading: "Hópur A", key: "a" },
                { heading: "Hópur B", key: "b" }, { heading: "Munur (prósentustig)", key: "munur" }],
      rows: doc.lysigogn.munir.map(function (item) {
        return { lysing: item.lysing, a: groupLabel(item.a), b: groupLabel(item.b),
                 munur: difference(item.prosentustig) };
      })
    }, 1));
  }

  function selectedCodes(dimension) {
    return dimension.gildi
      .filter(function (value) { return value.valid; })
      .sort(function (x, y) { return x.stada - y.stada; });
  }

  function renderJsonStat(doc, root) {
    const dimensions = doc.lysigogn.viddir.slice().sort(function (x, y) {
      return x.stada - y.stada;
    });
    root.querySelector("[data-hagstofan-fyrirspurn]").textContent =
      JSON.stringify(doc.lysigogn.fyrirspurn, null, 2);

    slot(root, "viddir").appendChild(table({
      caption: "Víddir svarsins í röð id, með size og category.index",
      columns: [{ heading: "Vídd", key: "heiti" }, { heading: "size", key: "staerd", numeric: true },
                { heading: "Valdir kóðar í röð", key: "valdir" },
                { heading: "Aðrir kóðar í lýsigögnum", key: "adrir" }],
      rows: dimensions.map(function (dimension) {
        return {
          heiti: dimension.heiti, staerd: dimension.staerd,
          valdir: selectedCodes(dimension).map(function (value) {
            return value.kodi === value.heiti ? value.kodi : value.kodi + " = " + value.heiti;
          }).join("; "),
          adrir: dimension.gildi.filter(function (value) { return !value.valid; })
            .map(function (value) { return value.heiti; }).join("; ") || "—"
        };
      })
    }, 1));

    const sizes = dimensions.map(function (dimension) { return dimension.staerd; });
    const product = sizes.reduce(function (a, b) { return a * b; }, 1);
    if (product !== doc.lysigogn.tafla.fjoldi_gilda) {
      throw new data.DataError("Margfeldi víddanna stemmir ekki við fjölda gilda.");
    }
    root.querySelector("[data-hagstofan-margfeldi]").textContent = sizes.join(" × ");

    // Sama regla og þáttarinn notar: síðasta víddin breytist hraðast.
    const positions = dimensions.map(function (dimension) {
      const code = EXAMPLE[dimension.kodi] || selectedCodes(dimension)[0].kodi;
      const value = dimension.gildi.find(function (item) { return item.kodi === code; });
      if (!value || !value.valid) {
        throw new data.DataError("Kóðinn „" + code + "“ er ekki í fyrirspurninni.");
      }
      return value.stada;
    });
    const flat = positions.reduce(function (index, position, i) {
      return index * sizes[i] + position;
    }, 0);
    const row = doc.gogn.find(function (item) {
      return item.namssvid_kodi === EXAMPLE_GROUP.namssvid_kodi &&
             item.kyn_kodi === EXAMPLE_GROUP.kyn_kodi;
    });
    const status = doc.lysigogn.stodur.find(function (item) {
      return item.kodi === EXAMPLE["Nemendur"];
    });
    if (!row || !status) throw new data.DataError("Röðina í dæminu vantar í gögnin.");
    const fill = function (part, text) {
      root.querySelector("[data-hagstofan-daemi='" + part + "']").textContent = text;
    };
    fill("saeti", positions.join(", "));
    fill("flatt", String(flat));
    fill("gildi", data.formatNumber(row[status.reitur]));
  }

  section.registerRenderer("hagstofan", function (doc, root) {
    renderResults(doc, root);
    renderJsonStat(doc, root);
  });
})();
