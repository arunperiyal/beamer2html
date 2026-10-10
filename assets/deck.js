/* deck.js -- turns the <section class="slide"> elements of slides.html into a
 * presentation. No external dependencies; works from file:// in any modern
 * browser (Chrome, Firefox, Edge, Safari).
 *
 * Keys:  → ↓ Space PageDown  next step / slide
 *        ← ↑ PageUp           previous step / slide
 *        Home / End           first / last slide
 *        F                    fullscreen
 *        P                    play / pause the animations and videos on the current slide
 *        S                    presenter view (notes, next slide, timer) in a new window
 *        H                    show / hide this help
 *        <number> Enter       go to slide <number>
 */
(function () {
  "use strict";

  const C = Object.assign({
    title: "[Presentation Title]", seminar: "[Seminar Name]",
    degree: "[Degree Name]", presenter: "[Presenter Name]",
    rollNo: "[Roll Number]", supervisor: "[Supervisor Name]",
    department: "[Department Name]", institute: "[Institute Name]",
    logo: "figures/logo.png",
    author1: "[Author 1]", author2: "[Author 2]", conference: "[Conference Name]",
    shortTitle: "[Short Title]", footAuthor: "[Presenter Name]",
    titleBar: "on", titleHeight: 88, sectionName: "on", footer: "full",
    dividers: "off", fontSize: 11, marginLeft: 80, marginRight: 80, barMargin: 32,
    maxNames: 3,
  }, window.DECK_CONFIG || {});

  const deck = document.querySelector(".deck");
  let slides = Array.from(deck.querySelectorAll(":scope > section.slide"));
  const esc = (s) => String(s).replace(/[&<>"]/g,
    (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

  document.documentElement.style.setProperty("--title-h", C.titleHeight + "px");
  // side margins: slide body (\setbeamersize text margins), title bar/footer (\SetBarMargin)
  const MARGINS = { marginLeft: "--body-l", marginRight: "--body-r", barMargin: "--pad-x" };
  for (const [key, v] of Object.entries(MARGINS)) {
    if (C[key] != null) document.documentElement.style.setProperty(v, C[key] + "px");
  }
  document.documentElement.style.setProperty("--fs", (C.fontSize || 11) / 11);
  if (C.captionSize) document.documentElement.style.setProperty("--caption-size", C.captionSize + "em");

  // ------------------------------------------------------------ live reload
  // Decks built with `tex2html --watch` check two files once a second:
  //  * html/build.js -- reload when it names a newer build. The URL keeps
  //    #slide.step, so the reload comes back to the same place.
  //  * html/goto.js  -- written by the editor plugin (:Tex2HtmlSync): go to
  //    { slide, step }. A request older than this page load is ignored.
  // Other decks never check.
  if (C.watch) {
    const load = (file, done) => {
      const s = document.createElement("script");
      s.src = "html/" + file + "?t=" + Date.now();   // bypass the cache
      s.onload = s.onerror = () => { s.remove(); done(); };
      document.head.appendChild(s);
    };
    let seenGoto;
    setInterval(() => {
      load("build.js", () => {
        if (window.TEX2HTML_BUILD && window.TEX2HTML_BUILD !== C.build) location.reload();
      });
      load("goto.js", () => {
        const g = window.TEX2HTML_GOTO;
        if (g && seenGoto !== undefined && g.t !== seenGoto) show(g.slide - 1, g.step || 0);
        seenGoto = g ? g.t : null;
      });
    }, 1000);
  }

  // ------------------------------------------------------------ sections
  // A slide with data-section="Name" starts a section; later slides inherit it.
  const sections = [];
  let current = "";
  slides.forEach((s) => {
    if (s.dataset.section) {
      current = s.dataset.section;
      sections.push(current);
    }
    s._section = current;
  });

  // ------------------------------------------------------------ citations
  // <cite data-ref="key1,key2"></cite>  ->  [1, 2]   (numbered in order of
  // first citation, consecutive numbers compressed: [2-4]).
  // data-style="text" (\textcite): "Liu et al. [13] and Xie et al. [14]";
  // "author" (\citeauthor): "Liu et al.". Unknown keys are shown in bold
  // and get no number, as with biblatex.
  const bib = parseBibtex(window.BIBTEX || "");
  const order = [];
  const number = (k) => {
    let i = order.indexOf(k);
    if (i < 0) { order.push(k); i = order.length - 1; }
    return i + 1;
  };
  const missing = (k) => `<b>${esc(k)}</b>`;
  deck.querySelectorAll("cite[data-ref]").forEach((el) => {
    const keys = el.dataset.ref.split(",").map((k) => k.trim()).filter(Boolean);
    keys.filter((k) => !bib[k]).forEach((k) => console.warn("deck.js: unknown reference", k));
    const style = el.dataset.style;
    if (style === "authoryear") {                  // literature table: "A et al. (Y)"
      keys.forEach((k) => { if (bib[k]) number(k); });
      el.innerHTML = keys.map((k) => bib[k] ? authorYear(bib[k]) : missing(k)).join("<br>");
      return;
    }
    if (style === "text" || style === "author") {
      const found = keys.filter((k) => bib[k]);   // in number order, as sortcites
      if (style === "text") found.forEach(number), found.sort((a, b) => number(a) - number(b));
      el.innerHTML = andList([...found.map((k) => citeNames(bib[k]) +
        (style === "text" ? ` [${number(k)}]` : "")), ...keys.filter((k) => !bib[k]).map(missing)]);
      return;
    }
    const nums = keys.filter((k) => bib[k]).map(number).sort((a, b) => a - b);
    const parts = [];
    for (let i = 0; i < nums.length; i++) {
      let j = i;
      while (j + 1 < nums.length && nums[j + 1] === nums[j] + 1) j++;
      parts.push(j - i >= 2 ? `${nums[i]}–${nums[j]}`
               : j > i ? `${nums[i]}, ${nums[j]}` : `${nums[i]}`);
      i = j;
    }
    el.innerHTML = [nums.length ? `[${parts.join(", ")}]` : "",
                    ...keys.filter((k) => !bib[k]).map(missing)].filter(Boolean).join(" ");
  });

  // ------------------------------------------------------------ publications
  // \pub[status]{key} -> <div class="pub" data-key>: the entry comes from the
  // .bib file; it is not numbered and not added to the References slide.
  deck.querySelectorAll(".pub[data-key] .pub-entry").forEach((el) => {
    const key = el.parentNode.dataset.key;
    if (bib[key]) el.innerHTML = formatEntry(bib[key], C.maxNames);
    else {
      console.warn("deck.js: unknown reference", key);
      el.textContent = key + " (not found in the .bib file)";
    }
  });

  // ------------------------------------------------------------ templates
  const TEMPLATES = {
    seminar: () => `
      <div class="banner">${C.title}</div>
      <div class="info">
        <div>${C.seminar}</div>
        <div>presented for the degree of</div>
        <div><b>${C.degree}</b></div>
        <div class="gap"></div>
        <div>Presented by,</div>
        <div><b>${C.presenter}</b></div>
        <div><b>${C.rollNo}</b></div>
        <div>Under the guidance of</div>
        <div><b>${C.supervisor}</b></div>
        <img class="logo" src="${esc(C.logo)}" alt=""
             onerror="this.outerHTML='<div class=&quot;logo-placeholder&quot;>Logo</div>'">
        <div>${C.department}</div>
        <div>${C.institute}</div>
      </div>`,
    conference: () => `
      <div class="banner">${C.title}</div>
      <div class="info">
        <div class="authors"><span>${C.author1}</span><span>${C.author2}</span></div>
        <div class="rule"></div>
        <div class="venue">${C.conference}</div>
      </div>`,
    overview: (s) => `
      <h2>${s.dataset.title || "Overview"}</h2>
      <ul class="overview-list">
        ${sections.map((n) => `<li>${n}</li>`).join("")}
      </ul>`,
    references: (s) => `
      <h2>${s.dataset.title || "References"}</h2>
      <ol class="references">
        ${order.map((k, i) => `<li><span class="label">[${i + 1}]</span>
          <span>${bib[k] ? formatEntry(bib[k], C.maxNames) : esc(k) + " (not found)"}</span></li>`).join("")}
      </ol>`,
    thanks: (s) => `
      <div class="thanks-box">
        <div class="big">${s.dataset.title || "Thank You"}</div>
        <div class="small">${s.dataset.subtitle ?? "Questions?"}</div>
      </div>`,
  };
  const PLAIN = ["seminar", "conference", "thanks"];   // no title bar / footer

  slides.forEach((s) => {
    const t = s.dataset.template;
    if (t && TEMPLATES[t]) s.innerHTML = TEMPLATES[t](s);
    if (t) s.classList.add(t);
    if (t === "overview" || t === "references") {
      s.dataset.align = "top";
      s.dataset.sectionName = "off";              // not part of any section
    }
  });

  // ------------------------------------------------------------ content chrome
  // Per-slide overrides: data-title-bar, data-section-name, data-footer,
  // data-title-height (px), data-dividers.
  slides.forEach((s, i) => {
    if (PLAIN.includes(s.dataset.template)) return;
    const opt = (name, key) => s.dataset[name] || C[key];
    const bar = opt("titleBar", "titleBar") === "on";
    const showSec = opt("sectionName", "sectionName") === "on" && s._section;
    const footer = opt("footer", "footer");
    if (opt("dividers", "dividers") === "on") s.classList.add("dividers");

    const h2 = s.querySelector(":scope > h2");
    const h3 = s.querySelector(":scope > h3");
    if (s.dataset.titleHeight) s.style.setProperty("--title-h", s.dataset.titleHeight + "px");
    for (const [key, v] of Object.entries(MARGINS)) {     // data-margin-left etc.
      if (s.dataset[key]) s.style.setProperty(v, s.dataset[key] + "px");
    }
    const header = document.createElement("div");
    header.className = "titlebar";
    header.innerHTML = `
      <div class="titles">
        ${h2 ? `<h2><span>${h2.innerHTML}</span></h2>` : ""}
        ${h3 ? `<h3>${h3.innerHTML}</h3>` : ""}
      </div>
      ${showSec ? `<div class="secname">${s._section}</div>` : ""}`;
    if (h2) h2.remove();
    if (h3) h3.remove();

    const body = document.createElement("div");
    body.className = "body" + (s.dataset.align === "top" ? " top" : "");
    while (s.firstChild) body.appendChild(s.firstChild);

    s.classList.add(bar ? "bar-on" : "bar-off");
    if (h2 || h3) s.append(header, body);         // no title -> no title area
    else s.append(body);

    if (footer !== "off") {
      const f = document.createElement("div");
      f.className = "footer " + footer;
      f.innerHTML = footer === "number" ? `<span class="num"></span>`
        : `<span>${C.footAuthor}</span><span>${C.shortTitle}</span>
           <span class="num"></span>`;
      s.appendChild(f);
    }
  });

  // ------------------------------------------------------------ long reference lists
  // Like beamer's allowframebreaks: entries that do not fit move on to
  // "<title> (cont.)" slides, as many as needed.
  slides.filter((s) => s.dataset.template === "references").forEach(splitReferences);
  slides = Array.from(deck.querySelectorAll(":scope > section.slide"));
  slides.forEach((s, i) => s.querySelectorAll(".footer .num").forEach((n) => {
    n.textContent = n.parentNode.classList.contains("number") ? i + 1
      : `${i + 1} / ${slides.length}`;
  }));

  function splitReferences(s) {
    const body = s.querySelector(".body"), list = s.querySelector("ol.references");
    if (!body || !list) return;
    const moved = [];
    s.classList.add("active");                   // measure with the slide laid out
    while (body.scrollHeight > body.clientHeight + 1 && list.children.length > 1) {
      moved.unshift(list.lastElementChild);
      list.lastElementChild.remove();
    }
    s.classList.remove("active");
    if (!moved.length) return;
    const next = s.cloneNode(true);
    next._section = s._section;
    next.querySelector("ol.references").replaceChildren(...moved);
    const title = next.querySelector(".titlebar h2 span");
    if (title && !s._continued) title.innerHTML += " (cont.)";
    next._continued = true;
    s.after(next);
    splitReferences(next);
  }

  // ------------------------------------------------------------ shapes
  // \begin{annotate} -> <div class="annotate"> with <span class="shape"> place-
  // holders (\shape), and <span class="shape slide-shape"> (\slideshape) /
  // <span class="slide-grid"> anywhere on a slide. Drawn as SVG over the
  // annotated element (its image, table, ...) or the whole slide, from
  // fractions with the origin bottom left; redrawn when the element resizes.
  const SVGNS = "http://www.w3.org/2000/svg";
  const PX_PER_PT = 80 / 28.45;                  // as units.py
  let shapeIds = 0;
  slides.forEach((s) => {
    s.querySelectorAll(".annotate").forEach((ann) => {
      const target = () => ann.querySelector(
        ":scope img, :scope table, :scope .anim, :scope .figure-placeholder") || ann;
      shapeLayer(ann, [...ann.querySelectorAll("span.shape:not(.slide-shape)")],
        ann.hasAttribute("data-grid") || s.classList.contains("dividers"), target, false);
    });
    const grid = s.querySelector("span.slide-grid");
    const own = [...s.querySelectorAll("span.slide-shape")];
    if (own.length || grid) shapeLayer(s, own, !!grid, () => s, true);
    s.querySelectorAll("span.slide-grid").forEach((g) => g.remove());
  });

  function shapeLayer(host, spans, grid, target, inside) {
    const layer = document.createElement("div");
    layer.className = "shape-layer";
    const svg = document.createElementNS(SVGNS, "svg");
    layer.appendChild(svg);
    const items = spans.map((sp) => {
      const g = document.createElementNS(SVGNS, "g");
      const d = { ...sp.dataset };
      if (d.spec) g.dataset.spec = d.spec;
      svg.appendChild(g);
      const makeLabel = (html) => {
        const l = document.createElement("div");
        l.className = "shape-label";
        l.innerHTML = html;
        l.style.color = d.color;
        l.style.fontSize = `calc(30px * var(--fs) * ${d.size || 0.9})`;
        if (d.spec) l.dataset.spec = d.spec;
        layer.appendChild(l);
        return l;
      };
      let label = null, axisLabels = {};
      if (d.kind === "axes") {                     // one label per axis
        sp.querySelectorAll(".axis-label").forEach((a) => {
          axisLabels[a.dataset.axis] = makeLabel(a.innerHTML);
        });
      } else if (sp.innerHTML.trim()) label = makeLabel(sp.innerHTML.trim());
      sp.remove();
      return { d, g, label, axisLabels };
    });
    const gridG = document.createElementNS(SVGNS, "g");
    const gridLabels = [];
    if (grid) {
      svg.prepend(gridG);
      for (let k = 0; k <= 10; k += 2) {
        for (const axis of ["x", "y"]) {
          const l = document.createElement("div");
          l.className = `shape-grid-label ${axis}${inside ? " inside" : ""}`;
          l.textContent = k === 0 ? "0" : k === 10 ? "1" : `0.${k}`;
          layer.appendChild(l);
          gridLabels.push({ l, axis, f: k / 10 });
        }
      }
    }
    if (getComputedStyle(host).position === "static") host.style.position = "relative";
    host.appendChild(layer);

    const draw = () => {
      const t = target();
      const hr = host.getBoundingClientRect(), tr = t.getBoundingClientRect();
      if (!hr.width || !tr.width) return;           // not laid out (hidden slide)
      const k = host.offsetWidth / hr.width;         // undo the deck's scaling
      const w = tr.width * k, h = tr.height * k;
      Object.assign(layer.style, { left: (tr.left - hr.left) * k + "px",
        top: (tr.top - hr.top) * k + "px", width: w + "px", height: h + "px" });
      const X = (f) => f * w, Y = (f) => (1 - f) * h;
      if (grid) {
        let lines = "";
        for (let i = 0; i <= 10; i++) {
          const sw = i % 2 ? 0.6 : 1.1;
          lines += `<line x1="${X(i / 10)}" y1="0" x2="${X(i / 10)}" y2="${h}" stroke-width="${sw}"/>` +
                   `<line x1="0" y1="${Y(i / 10)}" x2="${w}" y2="${Y(i / 10)}" stroke-width="${sw}"/>`;
        }
        gridG.innerHTML = lines;
        gridG.setAttribute("class", "shape-grid");
        gridLabels.forEach(({ l, axis, f }) => {
          l.style.left = (axis === "x" ? X(f) : 0) + "px";
          l.style.top = (axis === "x" ? h : Y(f)) + "px";
        });
      }
      items.forEach(({ d, g, label, axisLabels }) => {
        const [x1, y1] = d.p1.split(",").map(Number);
        const [x2, y2] = (d.p2 || d.p1).split(",").map(Number);
        const ax = X(x1), ay = Y(y1), bx = X(x2), by = Y(y2);
        const sw = +d.width || PX_PER_PT;
        const stroke = `stroke="${d.color}" stroke-width="${sw}"` +
          (d.dashed ? ` stroke-dasharray="${3 * PX_PER_PT} ${3 * PX_PER_PT}"` : "");
        const fill = d.fill ? `fill="${d.fill}" fill-opacity="${d.opacity}"` : `fill="none"`;
        const minX = Math.min(ax, bx), maxX = Math.max(ax, bx);
        const minY = Math.min(ay, by), maxY = Math.max(ay, by);
        if (d.kind === "rect") {
          g.innerHTML = `<rect x="${minX}" y="${minY}" width="${maxX - minX}" height="${maxY - minY}"` +
            ` rx="${+d.rounded || 0}" ${stroke} ${fill}/>`;
        } else if (d.kind === "ellipse") {
          g.innerHTML = `<ellipse cx="${(ax + bx) / 2}" cy="${(ay + by) / 2}" rx="${(maxX - minX) / 2}"` +
            ` ry="${(maxY - minY) / 2}" ${stroke} ${fill}/>`;
        } else if (d.kind === "axes") {
          // x at rotate degrees, y at +90, z (0.7 long) at +oblique (225);
          // length is a fraction of the width; an axis without a label is left out
          const L = (+d.p2 || 0.1) * w, rot = +d.rotate || 0;
          const obl = d.oblique === undefined ? 225 : +d.oblique;
          const id = `shape-arrow-${++shapeIds}`;
          let out = `<defs><marker id="${id}" viewBox="0 0 10 10" refX="9" refY="5"` +
            ` markerWidth="4.5" markerHeight="4.5" orient="auto-start-reverse">` +
            `<path d="M0,0 L10,5 L0,10 L3,5 z" fill="${d.color}"/></marker></defs>`;
          for (const [axis, deg, f] of [["x", rot, 1], ["y", rot + 90, 1], ["z", rot + obl, 0.7]]) {
            if (!axisLabels[axis]) continue;
            const t = deg * Math.PI / 180, c = Math.cos(t), s = Math.sin(t);
            const tx = ax + c * f * L, ty = ay - s * f * L;
            out += `<line x1="${ax}" y1="${ay}" x2="${tx}" y2="${ty}" ${stroke} marker-end="url(#${id})"/>`;
            const l = axisLabels[axis];
            if (l) {                                 // like a TikZ anchor at deg+180
              l.style.left = tx + "px";
              l.style.top = ty + "px";
              l.style.padding = "0";
              l.style.transform = `translate(calc(${-50 + 50 * c}% + ${4 * c}px),` +
                ` calc(${-50 - 50 * s}% - ${4 * s}px))`;
            }
          }
          g.innerHTML = out;
        } else if (d.kind === "line" || d.kind === "arrow") {
          let marker = "";
          if (d.kind === "arrow") {
            const id = `shape-arrow-${++shapeIds}`;
            marker = ` marker-end="url(#${id})"`;
            g.innerHTML = `<defs><marker id="${id}" viewBox="0 0 10 10" refX="9" refY="5"` +
              ` markerWidth="4.5" markerHeight="4.5" orient="auto-start-reverse">` +
              `<path d="M0,0 L10,5 L0,10 L3,5 z" fill="${d.color}"/></marker></defs>`;
          } else g.innerHTML = "";
          g.insertAdjacentHTML("beforeend", `<line x1="${ax}" y1="${ay}" x2="${bx}" y2="${by}"` +
            ` ${stroke}${marker}/>`);
        }
        if (label) {
          const at = d.kind === "text" ? [ax, ay, "-50%", "-50%"] : {
            above: [(ax + bx) / 2, minY, "-50%", "-100%"],
            below: [(ax + bx) / 2, maxY, "-50%", "0%"],
            left:  [minX, (ay + by) / 2, "-100%", "-50%"],
            right: [maxX, (ay + by) / 2, "0%", "-50%"],
          }[d.labelpos] || [(ax + bx) / 2, minY, "-50%", "-100%"];
          label.style.left = at[0] + "px";
          label.style.top = at[1] + "px";
          label.style.transform = `translate(${at[2]}, ${at[3]})`;
          label.classList.toggle("text", d.kind === "text");
          if (d.kind === "text") {                   // fill = background, border = frame
            label.style.background = d.fill
              ? `color-mix(in srgb, ${d.fill} ${100 * (+d.opacity || 1)}%, transparent)` : "";
            label.style.border = d.border ? `${sw}px ${d.dashed ? "dashed" : "solid"} ${d.border}` : "";
            label.style.borderRadius = d.border || d.fill ? `${+d.rounded || 0}px` : "";
            label.classList.toggle("boxed", !!(d.fill || d.border));
          }
        }
      });
    };
    const ro = new ResizeObserver(draw);
    ro.observe(host);
    const t = target();
    if (t !== host) ro.observe(t);
    host.querySelectorAll("img").forEach((im) => im.addEventListener("load", draw));
  }

  // ------------------------------------------------------------ steps
  // Step s of a slide corresponds to beamer overlay s+1.
  //  * <span class="pause">: everything after the k-th marker gets
  //    data-step="k" and appears at step k.
  //  * <span class="onslide" data-spec>: everything after it gets
  //    data-from="<spec>" (\onslide<2-> switch form).
  //  * data-spec="<spec>" on an element (\item<2->, \uncover, \only, ...):
  //    shown on the matching overlays; data-mode="only" removes it from the
  //    layout instead of just hiding it, data-invert inverts the match.
  // Hidden content otherwise keeps its space, as in beamer.
  slides.forEach((s) => { s._steps = tagSteps(s); });

  function tagSteps(slide) {
    const body = slide.querySelector(".body") || slide;
    let pauses = 0;
    slide.querySelectorAll("span.pause, span.onslide").forEach((mark) => {
      const isPause = mark.classList.contains("pause");
      if (isPause) pauses++;
      const k = pauses;
      for (let node = mark; node && node !== body; node = node.parentNode) {
        for (let sib = node.nextSibling; sib; sib = sib.nextSibling) {
          if (sib.nodeType === Node.TEXT_NODE) {
            if (!sib.textContent.trim()) continue;
            const span = document.createElement("span");
            sib.replaceWith(span);
            span.appendChild(sib);
            sib = span;
          }
          if (sib.nodeType !== Node.ELEMENT_NODE ||
              sib.matches("span.pause, span.onslide")) continue;
          if (isPause) sib.dataset.step = k;       // later markers overwrite
          else sib.dataset.from = mark.dataset.spec;
        }
      }
    });
    // number of steps: pauses, or the highest overlay number used in a spec
    let top = 1;
    slide.querySelectorAll("[data-spec], [data-from]").forEach((el) => {
      ((el.dataset.spec || "") + "," + (el.dataset.from || "")).replace(/\d+/g,
        (d) => { top = Math.max(top, +d); });
    });
    return Math.max(pauses, top - 1);
  }

  // "1,3-4,6-"  "-2"  "3"  -> does overlay n match?
  function matchSpec(spec, n) {
    return spec.split(",").some((p) => {
      const m = p.trim().match(/^(\d*)(-?)(\d*)$/);
      if (!m || !(m[1] || m[3])) return true;
      const a = m[1] ? +m[1] : 1, b = m[3] ? +m[3] : Infinity;
      return m[2] ? n >= a && n <= b : n === a;
    });
  }

  function showStep(slide, step) {
    const n = step + 1;
    slide.querySelectorAll("[data-step], [data-from], [data-spec]").forEach((el) => {
      let visible = true, on = true;
      if (el.dataset.step) visible = step >= +el.dataset.step;
      if (el.dataset.from) visible = visible && matchSpec(el.dataset.from, n);
      if (el.dataset.spec !== undefined) {
        on = matchSpec(el.dataset.spec, n) !== el.hasAttribute("data-invert");
      }
      if (el.dataset.mode === "only") {
        el.style.display = on ? "" : "none";
        el.style.visibility = visible ? "" : "hidden";
      } else {
        el.style.visibility = visible && on ? "" : "hidden";
      }
    });
  }

  // printing / Save as PDF: every slide at its last step (like beamer's
  // final overlay), then back to where the presenter was
  addEventListener("beforeprint", () => slides.forEach((s) => showStep(s, s._steps)));
  addEventListener("afterprint", () => slides.forEach((s, i) =>
    showStep(s, i === idx ? step : 0)));

  // ------------------------------------------------------------ animations
  let anims = [];                        // created at the end, once Anim is defined

  // ------------------------------------------------------------ navigation
  let idx = 0, step = 0;
  // show(n, st): slide n at step st (st = Infinity -> all steps shown)
  function show(n, st = 0) {
    n = Math.max(0, Math.min(slides.length - 1, n));
    if (n !== idx || !slides[n].classList.contains("active")) {
      slides[idx].classList.remove("active");
      anims.forEach((a) => { if (slides[idx].contains(a.el)) a.leave(); });
      idx = n;
      slides[idx].classList.add("active");
      anims.forEach((a) => { if (slides[idx].contains(a.el)) a.enter(); });
    }
    step = Math.max(0, Math.min(slides[idx]._steps, st));
    showStep(slides[idx], step);
    syncVideos();
    history.replaceState(null, "", "#" + (idx + 1) + (step ? "." + step : ""));
    renderPresenter();
  }
  function next() {
    if (step < slides[idx]._steps) show(idx, step + 1);
    else if (idx < slides.length - 1) show(idx + 1, 0);
  }
  function prev() {
    if (step > 0) show(idx, step - 1);
    else if (idx > 0) show(idx - 1, Infinity);     // previous slide, fully revealed
  }

  function fit() {
    const k = Math.min(innerWidth / 1280, innerHeight / 720);
    deck.style.transform = `scale(${k})`;
    deck.style.left = (innerWidth - 1280 * k) / 2 + "px";
    deck.style.top = (innerHeight - 720 * k) / 2 + "px";
  }
  addEventListener("resize", fit);
  fit();

  // ------------------------------------------------------------ touch
  // Swipe left (next) / right (previous); a tap on the right two thirds of
  // the screen goes forward, on the left third back. Taps on links, buttons,
  // the animation controls / time bar and animation images (play / pause)
  // keep their own meaning. Ignored while two fingers are down or the page is
  // pinch-zoomed in.
  const TOUCH_OWN = "a, button, input, select, textarea, video, " +
    ".anim-controls, .anim-bar, .anim img";
  const zoomed = () => window.visualViewport && visualViewport.scale > 1.01;
  let touch = null, fingers = 0;
  addEventListener("pointerdown", (e) => {
    if (e.pointerType === "mouse") return;
    fingers++;
    touch = fingers === 1 && !zoomed() ? { x: e.clientX, y: e.clientY, t: Date.now(),
      own: !!(e.target.closest && e.target.closest(TOUCH_OWN)) } : null;
  });
  addEventListener("pointercancel", (e) => {
    if (e.pointerType !== "mouse") { fingers = Math.max(0, fingers - 1); touch = null; }
  });
  addEventListener("pointerup", (e) => {
    if (e.pointerType === "mouse") return;
    fingers = Math.max(0, fingers - 1);
    const t = touch;
    touch = null;
    if (!t) return;
    const dx = e.clientX - t.x, dy = e.clientY - t.y;
    if (Math.abs(dx) > 50 && Math.abs(dx) > 1.5 * Math.abs(dy)) {        // swipe
      dx < 0 ? next() : prev();
    } else if (!t.own && Math.hypot(dx, dy) < 12 && Date.now() - t.t < 500) {   // tap
      e.clientX < innerWidth / 3 ? prev() : next();
    }
  });

  // ?nopresenter: where no second window can open (tex2html viewer's Android
  // app), the presenter view is left out of the help and S does nothing
  const noPresenter = new URLSearchParams(location.search).has("nopresenter");
  const hud = document.createElement("div");
  hud.className = "hud";
  hud.textContent = "→ / Space / PgDn   next step / slide\n← / PgUp          previous\n" +
    "Home / End        first / last\n<number> Enter    go to slide\n" +
    "F                 fullscreen\nP                 play / pause animation, video\n" +
    (noPresenter ? "" : "S                 presenter view (notes)\n") + "H                 this help\n" +
    "Touch: swipe left / right, or tap the right / left side";
  document.body.appendChild(hud);

  let typed = "";
  addEventListener("keydown", onKey);
  function onKey(e) {
    if (e.target.matches && e.target.matches("input")) e.target.blur();
    if (e.ctrlKey || e.metaKey || e.altKey) return;
    const k = e.key;
    if (/^[0-9]$/.test(k)) { typed += k; return; }
    if (k === "Enter" && typed) { show(parseInt(typed, 10) - 1); typed = ""; return; }
    typed = "";
    if (["ArrowRight", "ArrowDown", " ", "PageDown"].includes(k)) next();
    else if (["ArrowLeft", "ArrowUp", "PageUp", "Backspace"].includes(k)) prev();
    else if (k === "Home") show(0);
    else if (k === "End") show(slides.length - 1, Infinity);
    else if (k === "f" || k === "F") {
      document.fullscreenElement ? document.exitFullscreen()
        : document.documentElement.requestFullscreen();
    } else if (k === "p" || k === "P") {
      anims.forEach((a) => { if (slides[idx].contains(a.el)) a.toggle(); });
      const on = videos.filter((v) => v._on), playing = on.some((v) => !v.paused);
      on.forEach((v) => (playing ? v.pause() : playVideo(v)));   // any playing: pause all
    } else if (k === "h" || k === "H") hud.classList.toggle("show");
    else if ((k === "s" || k === "S") && !noPresenter) openPresenter();
    else return;
    e.preventDefault();
  }

  // ------------------------------------------------------------ presenter view
  // \note{...} becomes <aside class="note"> (never shown on the slide). S opens
  // a second window -- put it on the laptop screen, the slides on the
  // projector -- with the current slide, the next step or slide, the notes,
  // a clock and an elapsed-time timer. It is driven from this window and
  // forwards its keys here, so either window can be used to navigate.
  let pw = null, t0 = 0;

  const PRESENTER_CSS = `
    html, body { background: #15181d; color: #e8e8e8; overflow: auto; height: auto;
                 font-family: system-ui, sans-serif; margin: 0; }
    .pv { display: flex; flex-direction: column; height: 100vh; padding: 14px;
          box-sizing: border-box; gap: 12px; }
    .pv-bar { display: flex; gap: 28px; align-items: center; font-size: 22px; }
    .pv-timer { font-variant-numeric: tabular-nums; color: #9fd4ff; font-weight: 600; }
    .pv-clock { font-variant-numeric: tabular-nums; color: #aaa; }
    .pv-bar button { font: inherit; font-size: 15px; background: #2a2f37; color: #ddd;
                     border: 1px solid #444; border-radius: 5px; padding: 3px 10px;
                     cursor: pointer; }
    .pv-main { flex: 1; min-height: 0; display: flex; gap: 18px; }
    .pv-slides { flex: none; display: flex; flex-direction: column; gap: 6px; }
    .pv-label { font-size: 14px; color: #999; text-transform: uppercase;
                letter-spacing: 0.06em; margin-top: 6px; }
    .pv-frame { position: relative; width: 480px; height: 270px; overflow: hidden;
                background: #fff; border-radius: 3px; }
    .pv-frame.small { width: 384px; height: 216px; }
    .pv-frame .deck { position: absolute; transform-origin: 0 0; }
    .pv-frame .anim-controls { display: none; }
    .pv-end { color: #777; font-size: 16px; padding: 12px 0; }
    .pv-notes { flex: 1; min-width: 0; overflow: auto; font-size: 26px; line-height: 1.45;
                background: #1d2128; border-radius: 6px; padding: 14px 20px; }
    .pv-notes ul { padding-left: 1.2em; margin: 0.3em 0; }
    .pv-notes .pv-empty { color: #777; font-style: italic; }
  `;

  function openPresenter() {
    if (pw && !pw.closed) { pw.focus(); return; }
    pw = window.open("", "deck-presenter", "width=1150,height=720");
    if (!pw) { console.warn("deck.js: the presenter window was blocked"); return; }
    const d = pw.document;
    d.open();
    d.write("<!DOCTYPE html><html><head><meta charset='utf-8'><title></title></head>" +
            "<body></body></html>");
    d.close();
    d.title = "Presenter view – " + document.title;
    d.documentElement.style.cssText = document.documentElement.style.cssText;
    // the deck's stylesheet, plus the <style>s MathJax added, plus our own
    document.querySelectorAll('link[rel="stylesheet"], style').forEach((el) => {
      const c = d.createElement(el.tagName);
      if (el.tagName === "LINK") { c.rel = "stylesheet"; c.href = el.href; }
      else {                                       // live rules: MathJax adds some by insertRule
        try { c.textContent = [...el.sheet.cssRules].map((r) => r.cssText).join("\n"); }
        catch (e) { c.textContent = el.textContent; }
      }
      d.head.appendChild(c);
    });
    const css = d.createElement("style");
    css.textContent = PRESENTER_CSS;
    d.head.appendChild(css);
    d.body.innerHTML = `
      <div class="pv">
        <div class="pv-bar">
          <span class="pv-count"></span>
          <span class="pv-timer"></span>
          <button class="pv-reset" title="Restart the elapsed-time timer">Reset timer</button>
          <span class="pv-clock"></span>
        </div>
        <div class="pv-main">
          <div class="pv-slides">
            <div class="pv-label">Current</div><div class="pv-frame pv-cur"></div>
            <div class="pv-label pv-next-label">Next</div><div class="pv-frame small pv-next"></div>
          </div>
          <div class="pv-notes"></div>
        </div>
      </div>`;
    d.addEventListener("keydown", onKey);
    d.querySelector(".pv-reset").addEventListener("click", () => { t0 = Date.now(); tick(); });
    t0 = Date.now();
    renderPresenter();
  }

  // copy of a slide at a given step, scaled into a preview frame
  function preview(frame, slide, st) {
    frame.innerHTML = "";
    if (!slide) {
      frame.style.display = "none";
      return;
    }
    frame.style.display = "";
    const wrap = frame.ownerDocument.createElement("div");
    wrap.className = "deck";
    wrap.style.transform = `scale(${frame.clientWidth / 1280})`;
    const c = slide.cloneNode(true);
    c.classList.add("active");
    c.querySelectorAll("video").forEach((v) => { v.removeAttribute("controls"); v.preload = "none"; });
    showStep(c, st);
    wrap.appendChild(c);
    frame.appendChild(wrap);
  }

  function notesHtml(slide) {
    const notes = Array.from(slide.querySelectorAll("aside.note"));
    if (!notes.length) return '<p class="pv-empty">No notes for this slide.</p>';
    const plain = notes.filter((n) => !n.hasAttribute("data-item"));
    const items = notes.filter((n) => n.hasAttribute("data-item"));
    return plain.map((n) => `<div>${n.innerHTML}</div>`).join("") +
      (items.length ? `<ul>${items.map((n) => `<li>${n.innerHTML}</li>`).join("")}</ul>` : "");
  }

  function renderPresenter() {
    if (!pw || pw.closed) return;
    const d = pw.document, s = slides[idx];
    d.querySelector(".pv-count").textContent = `Slide ${idx + 1} / ${slides.length}` +
      (s._steps ? `  ·  step ${step + 1} / ${s._steps + 1}` : "");
    preview(d.querySelector(".pv-cur"), s, step);
    const moreSteps = step < s._steps, last = idx === slides.length - 1;
    d.querySelector(".pv-next-label").textContent = moreSteps ? "Next step"
      : last ? "End of presentation" : "Next slide";
    preview(d.querySelector(".pv-next"), moreSteps ? s : last ? null : slides[idx + 1],
            moreSteps ? step + 1 : 0);
    d.querySelector(".pv-notes").innerHTML = notesHtml(s);
    tick();
  }

  function tick() {
    if (!pw || pw.closed) return;
    const t = Math.floor((Date.now() - t0) / 1000);
    const two = (n) => String(n).padStart(2, "0");
    pw.document.querySelector(".pv-timer").textContent =
      `${two(Math.floor(t / 3600))}:${two(Math.floor(t / 60) % 60)}:${two(t % 60)}`;
    pw.document.querySelector(".pv-clock").textContent =
      new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
  }
  setInterval(tick, 1000);


  // ================================================================ helpers

  /* Animation player. Markup:
   *   <div class="anim" data-fps="3" data-frames="3000:5000:50" data-autoplay data-loop
   *        data-controls="all">
   *     <div class="panels">
   *       <figure><figcaption>Label</figcaption>
   *         <img data-src="path/frame_{n}.png"></figure>
   *       ...
   *     </div>
   *   </div>
   * data-frames = "first:last:step" (or "first:last"); {n} in data-src is
   * replaced by the frame number ({n:4} zero-pads to 4 digits). All panels share
   * one clock. An <img> may carry its own data-frames / data-dt (\animpanel
   * [frames=, dt=]): at clock step i it shows its i-th frame, holding its last
   * one when it has fewer; its time goes to the .anim-ptime-value of its figure.
   * data-controls (as animate's `controls` key): "all", or any of
   *   play (play/pause)  step (prev/next frame, slider)  stop (first/last)
   *   speed (slower/faster); omitted -> no control bar. Clicking an image or
   *   pressing P always plays / pauses.
   */
  function frameList(spec) {
    const [a, b, st] = (spec || "0:0").split(":").map(Number);
    const step = st || 1, out = [];
    for (let n = a; step > 0 ? n <= b : n >= b; n += step) out.push(n);
    return out;
  }
  function Anim(el) {
    this.el = el;
    this.nums = frameList(el.dataset.frames);
    this.fps = parseFloat(el.dataset.fps || "10");
    this.speed = 1;
    this.loop = el.hasAttribute("data-loop");
    this.autoplay = el.hasAttribute("data-autoplay");
    this.imgs = Array.from(el.querySelectorAll("img[data-src]"));
    this.pnums = this.imgs.map((img) =>               // each panel's frame numbers
      img.dataset.frames ? frameList(img.dataset.frames) : this.nums);
    this.count = Math.max(this.nums.length, ...this.pnums.map((l) => l.length));
    this.urls = this.imgs.map((img, p) => this.pnums[p].map((n) =>
      img.dataset.src.replace(/\{n(?::(\d+))?\}/g,
        (_, w) => w ? String(n).padStart(+w, "0") : String(n))));
    this.cache = [];                     // keeps preloaded frames alive
    this.i = 0; this.timer = null; this.loaded = false;

    const want = (el.dataset.controls || "").split(",").map((x) => x.trim());
    const has = (g) => want.includes("all") || want.includes(g);
    const btn = (a, label, title) => `<button data-a="${a}" title="${title}">${label}</button>`;
    const bar = document.createElement("div");
    bar.className = "anim-controls";
    bar.innerHTML = [
      has("stop") ? btn("first", "⏮", "First frame") : "",
      has("step") ? btn("prev", "◀", "Previous frame") : "",
      has("play") ? btn("play", "▶", "Play / pause (P)") : "",
      has("step") ? btn("next", "▶|", "Next frame") : "",
      has("stop") ? btn("last", "⏭", "Last frame") : "",
      has("step") ? `<input type="range" min="0" max="${this.count - 1}" value="0">` : "",
      has("speed") ? btn("slower", "−", "Slower") : "",
      has("step") || has("speed") ? `<span class="readout"></span>` : "",
      has("speed") ? btn("faster", "+", "Faster") : "",
    ].join("");
    if (bar.innerHTML) el.appendChild(bar);
    this.playBtn = bar.querySelector('[data-a="play"]');
    this.slider = bar.querySelector("input");
    this.readout = bar.querySelector(".readout");
    this.timeEl = el.querySelector(".anim-time-value");
    this.barFill = el.querySelector(".anim-bar-fill");     // timebar
    const track = el.querySelector(".anim-bar-track");
    if (track) {
      track.addEventListener("mousedown", (e) => e.preventDefault());
      track.addEventListener("click", (e) => {             // click: go to that frame
        const r = track.getBoundingClientRect();
        this.pause();
        this.go(Math.round((e.clientX - r.left) / r.width * (this.count - 1)));
      });
    }
    this.dt = parseFloat(el.dataset.dt || "0");
    this.digits = parseInt(el.dataset.timeDigits || "2", 10);
    this.ptimes = this.imgs.map((img) => {           // per-panel time (own ranges)
      const v = img.closest("figure") && img.closest("figure").querySelector(".anim-ptime-value");
      return v ? { el: v, dt: parseFloat(img.dataset.dt || el.dataset.dt || "0") } : null;
    });

    bar.addEventListener("mousedown", (e) => {
      if (e.target.tagName === "BUTTON") e.preventDefault();   // keep keys for slides
    });
    bar.addEventListener("click", (e) => {
      const act = e.target.dataset && e.target.dataset.a;
      if (!act) return;
      if (act === "play") this.toggle();
      else if (act === "slower") this.setSpeed(this.speed / 2);
      else if (act === "faster") this.setSpeed(this.speed * 2);
      else {
        this.pause();
        const last = this.count - 1;
        this.go({ first: 0, last, prev: this.i - 1, next: this.i + 1 }[act]);
      }
    });
    if (this.slider) {
      this.slider.addEventListener("input", () => { this.pause(); this.go(+this.slider.value); });
    }
    this.imgs.forEach((img) => img.addEventListener("click", () => this.toggle()));

    this.go(0);
    this.updateReadout();
  }
  Anim.prototype.preload = function () {
    if (this.loaded) return;
    this.loaded = true;
    this.urls.forEach((list) => list.forEach((u) => {
      const im = new Image(); im.decoding = "async"; im.src = u; this.cache.push(im);
    }));
  };
  Anim.prototype.go = function (i) {
    const n = this.count;
    i = this.loop ? (i + n) % n : Math.max(0, Math.min(n - 1, i));
    this.i = i;
    this.imgs.forEach((img, p) => {      // a shorter panel holds its last frame
      img.src = this.urls[p][Math.min(i, this.urls[p].length - 1)];
      const t = this.ptimes[p];
      if (t) {
        const l = this.pnums[p];
        t.el.textContent = (l[Math.min(i, l.length - 1)] * t.dt).toFixed(this.digits);
      }
    });
    if (this.timeEl) {                    // time = frame number x dt (data-dt)
      this.timeEl.textContent = (this.nums[Math.min(i, this.nums.length - 1)] * this.dt)
        .toFixed(this.digits);
    }
    if (this.barFill) {
      this.barFill.style.width = (n > 1 ? i / (n - 1) * 100 : 100) + "%";
    }
    if (this.slider) this.slider.value = i;
    this.updateReadout();
  };
  Anim.prototype.updateReadout = function () {
    if (!this.readout) return;
    this.readout.textContent =
      `${this.i + 1} / ${this.count} · ×${+this.speed.toFixed(2)}`;
  };
  Anim.prototype.play = function () {
    this.preload();
    clearInterval(this.timer);
    this.timer = setInterval(() => {
      if (!this.loop && this.i >= this.count - 1) return this.pause();
      this.go(this.i + 1);
    }, 1000 / (this.fps * this.speed));
    if (this.playBtn) this.playBtn.textContent = "⏸";
  };
  Anim.prototype.pause = function () {
    clearInterval(this.timer); this.timer = null;
    if (this.playBtn) this.playBtn.textContent = "▶";
  };
  Anim.prototype.toggle = function () { this.timer ? this.pause() : this.play(); };
  Anim.prototype.setSpeed = function (s) {
    this.speed = Math.max(0.125, Math.min(8, s));
    this.updateReadout();
    if (this.timer) this.play();
  };
  Anim.prototype.enter = function () {
    this.preload();
    this.go(0);
    if (this.autoplay) this.play();
  };
  Anim.prototype.leave = function () { this.pause(); };

  /* Minimal BibTeX reader: @type{key, field = {value} | "value" | number, ...} */
  function parseBibtex(src) {
    const out = {};
    const re = /@(\w+)\s*\{\s*([^,\s]+)\s*,/g;
    let m;
    while ((m = re.exec(src))) {
      const type = m[1].toLowerCase(), key = m[2];
      if (type === "comment" || type === "string" || type === "preamble") continue;
      let i = re.lastIndex, depth = 1;
      const startBody = i;
      while (i < src.length && depth > 0) {
        if (src[i] === "{") depth++; else if (src[i] === "}") depth--;
        i++;
      }
      const body = src.slice(startBody, i - 1);
      const fields = { type };
      const fre = /(\w+)\s*=\s*/g;
      let f;
      while ((f = fre.exec(body))) {
        const name = f[1].toLowerCase();
        let j = fre.lastIndex, val = "";
        if (body[j] === "{") {
          let d = 0, k = j;
          for (; k < body.length; k++) {
            if (body[k] === "{") d++; else if (body[k] === "}") { d--; if (d === 0) break; }
          }
          val = body.slice(j + 1, k); j = k + 1;
        } else if (body[j] === '"') {
          const k = body.indexOf('"', j + 1); val = body.slice(j + 1, k); j = k + 1;
        } else {
          const k = body.slice(j).search(/[,\n}]|$/); val = body.slice(j, j + k); j += k;
        }
        fields[name] = cleanTeX(val.trim());
        fre.lastIndex = j;
      }
      out[key] = fields;
      re.lastIndex = i;
    }
    return out;
  }
  function cleanTeX(s) {
    return s.replace(/\\relax\s*/g, "").replace(/\\&/g, "&").replace(/\\%/g, "%").replace(/--/g, "–")
            .replace(/~/g, " ").replace(/[{}]/g, "").replace(/\s+/g, " ");
  }
  // "Surname (Year)", "A & B (Year)" or "A et al. (Year)", as \citeauthor in
  // the literature table
  function authorYear(e) {
    const last = (e.author || e.editor || "").split(/\s+and\s+/).filter(Boolean)
      .map((n) => esc(n.includes(",") ? n.split(",")[0].trim() : n.trim().split(" ").pop()));
    const who = last.length > 2 ? last[0] + " et al."
      : last.length === 2 ? last[0] + " &amp; " + last[1] : (last[0] || "");
    return `${who} (${esc(e.year || "n.d.")})`;
  }

  // surnames as biblatex prints them in citations (maxcitenames = 3)
  function citeNames(e) {
    const last = (e.author || e.editor || "").split(/\s+and\s+/).filter(Boolean)
      .map((n) => esc(n.includes(",") ? n.split(",")[0].trim() : n.trim().split(" ").pop()));
    return last.length > 3 ? last[0] + " et al." : andList(last);
  }
  // "A", "A and B", "A, B, and C"
  function andList(xs) {
    return xs.length < 3 ? xs.join(" and ")
      : xs.slice(0, -1).join(", ") + ", and " + xs[xs.length - 1];
  }

  function formatNames(s, max) {
    const names = s.split(/\s+and\s+/).map((n) => {
      let last, first;
      if (n.includes(",")) [last, first] = n.split(",").map((x) => x.trim());
      else { const p = n.trim().split(" "); last = p.pop(); first = p.join(" "); }
      const init = (first || "").split(/[\s.]+/).filter(Boolean)
        .flatMap((w) => /^[A-Z]{2,3}$/.test(w) ? w.split("") : [w])   // "RK" -> R. K.
        .map((w) => w.split("-").map((x) => x[0] + ".").join("-")).join(" ");
      return (init ? init + " " : "") + last;
    });
    if (names.length > max) return names[0] + " et al.";
    return names.length > 1
      ? names.slice(0, -1).join(", ") + " and " + names[names.length - 1] : names[0];
  }
  function formatEntry(e, max) {
    const A = e.author ? esc(formatNames(e.author, max)).replace(/\.?$/, ". ") : "";
    const T = esc(e.title || "");
    const y = esc(e.year || ""), pp = e.pages ? ", " + esc(e.pages) : "";
    switch (e.type) {
      case "article":
        return `${A}“${T}”. In: <i>${esc(e.journal || "")}</i> ${esc(e.volume || "")}` +
               ` (${y})${pp}.`;
      case "inproceedings": case "conference":
        return `${A}“${T}”. In: <i>${esc(e.booktitle || "")}</i>. ${y}${pp}.`;
      case "book":
        return `${A}<i>${T}</i>. ${esc(e.publisher || "")}, ${y}.`;
      case "phdthesis": case "mastersthesis":
        return `${A}“${T}”. ${e.type === "phdthesis" ? "PhD thesis" : "Master's thesis"}. ` +
               `${esc(e.school || "")}, ${y}.`;
      default:
        return `${A}“${T}”. ${esc(e.howpublished || e.note || "")} ${y}.`;
    }
  }

  // ------------------------------------------------------------ videos
  // \slidevideo -> <video class="video" data-autoplay data-loop data-start
  // data-end>. A video is "on" while its slide is shown and it is not hidden
  // by a step: it pauses when it goes off, and with data-autoplay starts
  // (from data-start) when it comes on. data-start..data-end bound playback.
  // Without controls, a click on it plays / pauses.
  function videoShown(v) {
    for (let el = v; el && el !== deck; el = el.parentElement) {
      if (el.style.display === "none" || el.style.visibility === "hidden") return false;
    }
    return true;
  }
  function playVideo(v) {
    const p = v.play();
    if (p) p.catch(() => {});                    // autoplay with sound refused: stays paused
  }
  function syncVideos() {
    videos.forEach((v) => {
      const on = slides[idx].contains(v) && videoShown(v);
      if (on && !v._on && v.hasAttribute("data-autoplay")) {
        if (v.dataset.start) v.currentTime = +v.dataset.start;
        playVideo(v);
      } else if (!on && v._on) v.pause();
      v._on = on;
    });
  }
  let videos = [];

  // ================================================================ start
  anims = Array.from(deck.querySelectorAll(".anim")).map((el) => new Anim(el));
  videos = Array.from(deck.querySelectorAll("video.video"));
  videos.forEach((v) => {
    const start = +(v.dataset.start || 0), end = +(v.dataset.end || Infinity);
    v.addEventListener("timeupdate", () => {
      if (v.currentTime < end) return;
      if (v.hasAttribute("data-loop")) { v.currentTime = start; playVideo(v); }
      else v.pause();
    });
    v.addEventListener("ended", () => {          // to the end of the file
      if (v.hasAttribute("data-loop")) { v.currentTime = start; playVideo(v); }
    });
    if (!v.controls) {
      v.style.cursor = "pointer";
      v.addEventListener("click", () => (v.paused ? playVideo(v) : v.pause()));
    }
  });
  const [hs, hst] = location.hash.slice(1).split(".").map((x) => parseInt(x, 10));
  show(Number.isFinite(hs) ? hs - 1 : 0, Number.isFinite(hst) ? hst : 0);
})();
