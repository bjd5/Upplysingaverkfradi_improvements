# Frammistaða — 500 KB þakið á fyrstu hleðslu

Regla 3.4 í [`../CLAUDE.md`](../CLAUDE.md): fyrsta hleðsla hverrar síðu er
undir **500 KB** samtals (HTML, CSS, JS, JSON, myndir, letur).

## 1. Staðan

Mælt með Chromium 320 px breiðum, kaldri skyndiminni, yfir `localhost`.
„Body“ er ócomprimerað; „flutningur“ er það sem fór yfir tengingu (haus og
body, án þjöppunar þar sem þjónninn þjappar ekki — raunþjónn með gzip er
minni). Allar tölur eru bæti.

| Síða | Body | Flutningur | JSON sem hlaðið er |
|---|---:|---:|---|
| `index.html` | 50.762 | 53.044 | `yfirlit.json` |
| `sidur/adferdafraedi.html` | 33.918 | 35.794 | — |
| `sidur/friends-gagnasagan.html` | 32.637 | 34.513 | — |
| `sidur/hagstofan.html` | 32.533 | 34.409 | — |
| `sidur/mbl-regex.html` | 32.474 | 34.350 | — |
| `sidur/phoebe-central-perk.html` | 32.636 | 34.512 | — |
| `sidur/phoebe-tmdb.html` | 32.576 | 34.452 | — |
| `sidur/phoebe-tolfraedi.html` | 32.706 | 34.582 | — |
| `sidur/phoebe-tribute.html` | 32.391 | 34.267 | — |
| `sidur/skjalftavaktin.html` | 59.170 | 62.010 | `skjalftar.json` |
| `sidur/uppahalds-video.html` | 32.500 | 34.376 | — |
| `sidur/vedurstodvar.html` | 32.491 | 34.367 | — |

Stærsta síðan er um 12 % af þakinu.

- **Ytri beiðnir:** engar. Allar beiðnir fara á sama upprunann; engin CDN,
  engin framework.
- **Letur:** engin vefletur eru hlaðin. Tokens vísa í kerfisletur, svo
  engin þyngd er sótt.
- **Myndir:** engin `<img>` er á síðunum núna. SVG-myndir í
  `web/assets/img/` (favicon og myndrit) eru teiknaðar vektorar úr Python;
  SVG er réttara en WebP fyrir línur og texta og er því undanskilið
  WebP-kröfunni. Rastamyndir skulu vera WebP með `width`, `height` og
  `loading="lazy"` neðan við fold.
- **JSON:** aðeins skrárnar sem síða sækir telja. `hagstofan.json`,
  `mbl.json`, `phoebe-tolfraedi.json` og `vedurstodvar.json` eru ekki sóttar
  af neinni síðu enn.
- **Skriftur:** allar með `defer`.
- **Án JavaScript:** allar síður eru læsilegar og engin lárétt skrun
  (`scrollWidth` = 320). Efnið í `main` er til staðar; gagnareitir fyllast
  aðeins með JavaScript.
- **Console:** engin villa nema á `skjalftavaktin.html`, þar sem
  `samantekt.*` vantar í `skjalftar.json` (óskylt stærðinni; prófið
  `test_vefur_gogn` fellur af sömu ástæðu).

## 2. Hvernig mælingin er endurtekin

Prófið reiknar stærðina úr skrám á disk (ócomprimeruð, örlítið ríflegri en
mæling í vafra því hún telur öll JSON-nöfn í skriftum sem síðan hleður):

```
python3 -m unittest tests.test_vefur_frammistada
```

Það fellur ef síða fer yfir 500 KB, `<script>` vantar `defer`, ytri slóð
(`http://`, `https://`, `//`) er í `src`/`href`, eða stílskrá í
`web/assets/css/components/` er hvergi tengd.

Mæling yfir netið (Playwright fyrir node, Chromium uppsett):

```
python3 -m http.server 8000 --directory web &
NODE_PATH=$(npm root -g) node maela.js web 8000
```

`maela.js` (geymd utan repo) er:

```js
// Mælir fyrstu hleðslu hverrar síðu. Notkun: node maela.js <web-mappa> <port>
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const root = process.argv[2], port = process.argv[3] || '8765';
const pages = ['index.html', ...fs.readdirSync(path.join(root, 'sidur')).sort().map(f => 'sidur/' + f)];
(async () => {
  const b = await chromium.launch();
  for (const js of [true, false]) {
    console.log('--- javaScriptEnabled=' + js);
    for (const p of pages) {
      const ctx = await b.newContext({ javaScriptEnabled: js, viewport: { width: 320, height: 640 } });
      const pg = await ctx.newPage();
      const errs = [], ext = [], jobs = [];
      let body = 0, wire = 0;
      pg.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
      pg.on('pageerror', e => errs.push(String(e)));
      pg.on('response', r => jobs.push((async () => {
        try {
          const u = r.url();
          if (!u.startsWith('http://localhost:' + port)) ext.push(u);
          const bd = await r.body();
          const sz = await r.request().sizes();
          body += bd.length; wire += sz.responseBodySize + sz.responseHeadersSize;
        } catch (e) { errs.push('mæling: ' + e); }
      })()));
      await pg.goto(`http://localhost:${port}/${p}`, { waitUntil: 'networkidle' });
      await Promise.all(jobs);
      const txt = (await pg.innerText('main')).length;
      const sw = await pg.evaluate(() => document.documentElement.scrollWidth);
      console.log(p.padEnd(34), 'body', String(body).padStart(6), 'wire', String(wire).padStart(6),
        'ext', ext.length, 'villur', errs.length, 'textalengd', txt, 'scrollWidth', sw, errs.join('|'));
      await ctx.close();
    }
  }
  await b.close();
})();
```

Skriftan opnar hverja síðu með `javaScriptEnabled` true og false, leggur
saman `response.body()` og `request.sizes()` fyrir allar beiðnir, telur
beiðnir út fyrir `localhost` og safnar console-villum.
