(function () {
  "use strict";

  const EMAIL = "wliu01@risd.edu";
  const ROOT = document.body.dataset.root || "./";
  const PAGE = document.body.dataset.page || "";
  const projects = window.PROJECTS || [];
  const finePointer = window.matchMedia("(hover: hover) and (pointer: fine)").matches;
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

  const store = {
    get(k) { try { return localStorage.getItem(k); } catch (e) { return null; } },
    set(k, v) { try { localStorage.setItem(k, v); } catch (e) {} },
  };
  const esc = (s) => String(s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));
  const projectUrl = (p) => `${ROOT}projects/${p.slug}/`;
  const MEDIA_V = window.MEDIA_VERSION ? `?v=${window.MEDIA_VERSION}` : "";
  const imgUrl = (p, file) => `${ROOT}assets/img/${p.slug}/${file}${MEDIA_V}`;

  /* ───────── nav, mobile menu, footer, cursor ───────── */
  const moon = '<svg class="i-moon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M20.5 14.2A8.5 8.5 0 0 1 9.8 3.5a8.5 8.5 0 1 0 10.7 10.7Z"/></svg>';
  const sun = '<svg class="i-sun" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="4.2"/><path d="M12 2.5v2.2M12 19.3v2.2M2.5 12h2.2M19.3 12h2.2M5.3 5.3l1.6 1.6M17.1 17.1l1.6 1.6M5.3 18.7l1.6-1.6M17.1 6.9l1.6-1.6"/></svg>';

  document.body.insertAdjacentHTML(
    "afterbegin",
    `<header class="nav">
      <a href="${ROOT}">winnie liu</a>
      <div class="nav__mid">
        <a class="nav__link" href="${ROOT}about/">about</a>
        <a class="nav__link" href="mailto:${EMAIL}">get in touch</a>
      </div>
      <div class="nav__right">
        <button class="theme-toggle" type="button" aria-label="toggle dark and light mode">${moon}${sun}</button>
        <button class="nav__burger" type="button" aria-label="open menu"><span></span><span></span></button>
      </div>
    </header>
    <nav class="mobile-menu" aria-label="menu">
      <a href="${ROOT}">home</a>
      <a href="${ROOT}about/">about</a>
      <a href="mailto:${EMAIL}">get in touch</a>
    </nav>`
  );

  document.body.insertAdjacentHTML(
    "beforeend",
    `<footer class="footer">
      <canvas aria-hidden="true"></canvas>
      <div class="footer__msg">
        <p>thank you for stopping by ᢉ𐭩</p>
        <p>breathe and use your cursor to follow the trail .𖥔 ݁ ˖</p>
        <p>made with love</p>
      </div>
      <div class="footer__bar">
        <span>© 2026 winnie liu</span>
        <span class="footer__clock"></span>
      </div>
    </footer>
    <div class="cursor" aria-hidden="true"></div>`
  );

  // theme toggle
  const html = document.documentElement;
  const syncToggleLabel = () => {
    const light = html.dataset.theme === "light";
    document.querySelector(".theme-toggle").setAttribute("aria-label", light ? "switch to dark mode" : "switch to light mode");
  };
  syncToggleLabel();
  document.querySelector(".theme-toggle").addEventListener("click", () => {
    const next = html.dataset.theme === "light" ? "dark" : "light";
    html.dataset.theme = next;
    store.set("theme", next);
    syncToggleLabel();
  });

  // mobile menu
  document.querySelector(".nav__burger").addEventListener("click", () => {
    document.body.classList.toggle("menu-open");
  });

  /* ───────── smooth scroll ───────── */
  let lenis = null;
  if (window.Lenis && !reduceMotion) {
    lenis = new window.Lenis({ duration: 1.15, smoothWheel: true });
    const raf = (t) => { lenis.raf(t); requestAnimationFrame(raf); };
    requestAnimationFrame(raf);
  }

  /* ───────── cursor: circle that follows + grows on links ───────── */
  const cursor = document.querySelector(".cursor");
  if (finePointer) {
    html.classList.add("has-cursor");
    let tx = -100, ty = -100, cx = -100, cy = -100, shown = false;
    window.addEventListener("pointermove", (e) => {
      tx = e.clientX; ty = e.clientY;
      if (!shown) { cx = tx; cy = ty; shown = true; cursor.classList.add("is-visible"); }
    }, { passive: true });
    document.addEventListener("mouseleave", () => cursor.classList.remove("is-visible"));
    document.addEventListener("mouseenter", () => shown && cursor.classList.add("is-visible"));
    const loop = () => {
      cx += (tx - cx) * 0.22;
      cy += (ty - cy) * 0.22;
      cursor.style.transform = `translate3d(${cx}px, ${cy}px, 0)`;
      requestAnimationFrame(loop);
    };
    loop();
    document.addEventListener("mouseover", (e) => {
      const t = e.target;
      cursor.classList.toggle("is-draw", !!t.closest(".board__canvas"));
      cursor.classList.toggle("is-hover", !!t.closest("a, button, .card, input, [data-hover]") && !t.closest(".board__canvas"));
    });
  } else {
    cursor.remove();
  }

  /* ───────── project cards ───────── */
  const isVideo = (f) => /\.(mp4|m4v|webm)$/i.test(f);
  const cardHTML = (p) => {
    // card.jpg is the cover with its background extended to the card's 4:3 shape
    const cover = p.card || p.cover || "cover.jpg";
    const media = isVideo(cover)
      ? `<video src="${imgUrl(p, cover)}" autoplay muted loop playsinline preload="metadata"></video>`
      : `<img src="${imgUrl(p, cover)}" alt="${esc(p.title)}" loading="lazy" decoding="async">`;
    return `
    <a class="card reveal" href="${projectUrl(p)}">
      <div class="card__media">
        <div class="card__tag"><span class="pill">${esc(p.year || "new")}</span></div>
        ${media}
      </div>
      <div class="card__meta">
        <p class="card__title">${esc(p.title)}</p>
        <p class="card__sub">${esc(p.type)}</p>
      </div>
    </a>`;
  };

  document.querySelectorAll("[data-grid]").forEach((el) => {
    const exclude = el.dataset.exclude;
    const limit = parseInt(el.dataset.limit || "0", 10);
    let list = projects.filter((p) => p.slug !== exclude);
    if (exclude) {
      // "other projects": start from the ones after the current project
      const i = projects.findIndex((p) => p.slug === exclude);
      list = projects.slice(i + 1).concat(projects.slice(0, i));
    }
    if (limit) list = list.slice(0, limit);
    el.innerHTML = list.map(cardHTML).join("");
  });

  /* ───────── project page ───────── */
  if (PAGE === "project") {
    const p = projects.find((x) => x.slug === document.body.dataset.slug);
    const mount = document.querySelector("[data-project]");
    if (p && mount) {
      document.title = `${p.title} — winnie liu`;
      const facts = [["project type", p.type], ["year", p.year], ["my role", p.role], ["client", p.client]].filter((f) => f[1]);
      const media = (f, lazy) => isVideo(f)
        ? `<video src="${imgUrl(p, f)}" autoplay muted loop playsinline preload="${lazy ? "metadata" : "auto"}"></video>`
        : `<img src="${imgUrl(p, f)}" alt="${esc(p.title)}"${lazy ? ' loading="lazy" decoding="async"' : ""}>`;
      // a string is one full-width image; [a, b, …] sit side by side at the same height
      const row = (item) => Array.isArray(item)
        ? `<div class="row reveal" style="--n:${item.length}">${item.map((f) => `<figure class="shot">${media(f, true)}</figure>`).join("")}</div>`
        : `<figure class="shot reveal">${media(item, true)}</figure>`;
      const i = projects.indexOf(p);
      const prev = projects[(i - 1 + projects.length) % projects.length];
      const next = projects[(i + 1) % projects.length];
      mount.innerHTML = `
        <h1 class="display display--md project__title">${esc(p.title)}</h1>
        <figure class="shot">${media(p.images[0], false)}</figure>
        ${p.overview ? `<section class="overview"><p class="label">project overview</p><p class="overview__text">${esc(p.overview)}</p></section>` : ""}
        ${facts.length ? `<section class="facts">${facts.map(([k, v]) => `<div><p class="label">${k}</p><p class="val">${esc(v)}</p></div>`).join("")}</section>` : `<div style="height:96px"></div>`}
        <section class="gallery">
          ${p.images.slice(1).map(row).join("")}
        </section>
        <nav class="pager" aria-label="more projects">
          <a href="${projectUrl(prev)}"><span class="pager__dir">back</span><span class="pager__name">${esc(prev.title)}</span></a>
          <a href="${projectUrl(next)}"><span class="pager__dir">next</span><span class="pager__name">${esc(next.title)}</span></a>
        </nav>
        <section class="others">
          <h2 class="display display--md">other projects</h2>
          <div class="grid grid--3" data-others></div>
        </section>`;
      // rows: every cell gets the same shape (the average of the pictures' shapes),
      // and the cell is filled with the colour at the picture's edge, so a picture
      // with a different shape looks like its background simply continues.
      const edgeColour = (el, w, h) => {
        try {
          const c = document.createElement("canvas");
          c.width = 24; c.height = Math.max(1, Math.round(24 * h / w));
          const x = c.getContext("2d");
          x.drawImage(el, 0, 0, c.width, c.height);
          const d = x.getImageData(0, 0, c.width, c.height).data;
          let r = 0, g = 0, b = 0, n = 0;
          for (let y = 0; y < c.height; y++) for (let k = 0; k < c.width; k++) {
            if (y && k && y < c.height - 1 && k < c.width - 1) continue;
            const o = (y * c.width + k) * 4; r += d[o]; g += d[o + 1]; b += d[o + 2]; n++;
          }
          return `rgb(${r / n | 0},${g / n | 0},${b / n | 0})`;
        } catch (e) { return ""; }
      };
      mount.querySelectorAll(".row").forEach((rowEl) => {
        const figs = [...rowEl.children];
        const ars = [];
        figs.forEach((fig, k) => {
          const el = fig.firstElementChild;
          const fit = (w, h) => {
            if (!w || !h) return;
            ars[k] = w / h;
            const fill = edgeColour(el, w, h);
            if (fill) fig.style.setProperty("--fill", fill);
            if (ars.filter(Boolean).length === figs.length) {
              const cell = Math.exp(ars.reduce((s, a) => s + Math.log(a), 0) / ars.length);
              rowEl.style.setProperty("--cell", cell);
            }
          };
          if (el.tagName === "VIDEO") {
            if (el.readyState >= 2) fit(el.videoWidth, el.videoHeight);
            else el.addEventListener("loadeddata", () => fit(el.videoWidth, el.videoHeight), { once: true });
          } else if (el.complete && el.naturalWidth) fit(el.naturalWidth, el.naturalHeight);
          else el.addEventListener("load", () => fit(el.naturalWidth, el.naturalHeight), { once: true });
        });
      });
      mount.querySelector("[data-others]").innerHTML = projects.slice(i + 1).concat(projects.slice(0, i)).slice(0, 3).map(cardHTML).join("");
    }
  }

  // fade images in once loaded
  document.querySelectorAll(".card__media img, .card__media video").forEach((m) => {
    const done = () => m.classList.add("is-loaded");
    if (m.tagName === "VIDEO") { if (m.readyState >= 2) done(); else m.addEventListener("loadeddata", done); }
    else if (m.complete && m.naturalWidth) done(); else m.addEventListener("load", done);
  });

  /* ───────── reveal on scroll ───────── */
  const reveals = document.querySelectorAll(".reveal");
  if ("IntersectionObserver" in window && !reduceMotion) {
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => { if (en.isIntersecting) { en.target.classList.add("is-in"); io.unobserve(en.target); } });
    }, { rootMargin: "0px 0px -8% 0px" });
    reveals.forEach((el) => io.observe(el));
  } else {
    reveals.forEach((el) => el.classList.add("is-in"));
  }

  /* ───────── typewriter ───────── */
  const tw = document.querySelector("[data-typewriter]");
  if (tw) {
    const words = ["with curiosity.", "with intention.", "to storytell.", "to connect."];
    const out = tw.querySelector(".tw-text");
    let w = 0, n = 0, deleting = false;
    const tick = () => {
      const word = words[w];
      n += deleting ? -1 : 1;
      out.textContent = word.slice(0, n);
      let delay = deleting ? 50 : 100;
      if (!deleting && n === word.length) { deleting = true; delay = 1000; }
      else if (deleting && n === 0) { deleting = false; w = (w + 1) % words.length; delay = 300; }
      setTimeout(tick, delay);
    };
    setTimeout(tick, 600);
  }

  /* ───────── footer clock ───────── */
  const clock = document.querySelector(".footer__clock");
  const setTime = () => { clock.textContent = new Date().toLocaleTimeString("en-US"); };
  setTime();
  setInterval(setTime, 1000);

  /* ───────── footer ascii trail ───────── */
  (function trail() {
    const footer = document.querySelector(".footer");
    const canvas = footer.querySelector("canvas");
    const ctx = canvas.getContext("2d");
    const chars = " .:-=+*#%@";
    const pts = [];
    const head = { x: 0, y: 0 };
    let mouse = null, t = 0, running = false, w = 0, h = 0, dpr = 1;

    const resize = () => {
      const r = canvas.getBoundingClientRect();
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      w = r.width; h = r.height;
      canvas.width = w * dpr; canvas.height = h * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    };
    resize();
    window.addEventListener("resize", resize);
    footer.addEventListener("pointermove", (e) => {
      const r = canvas.getBoundingClientRect();
      mouse = { x: e.clientX - r.left, y: e.clientY - r.top };
    });
    footer.addEventListener("pointerleave", () => { mouse = null; });

    const frame = () => {
      if (!running) return;
      t += 0.016;
      ctx.clearRect(0, 0, w, h);
      // idle: drift in a slow loop; on hover: follow the cursor
      const idle = { x: w / 2 + Math.sin(t) * Math.min(260, w / 3), y: h / 2 + Math.cos(t * 0.7) * 120 };
      const target = mouse || idle;
      head.x += (target.x - head.x) * 0.25;
      head.y += (target.y - head.y) * 0.25;
      pts.push({ x: head.x, y: head.y, life: 1 });
      while (pts.length > 40) pts.shift();
      for (const p of pts) p.life -= 0.022;
      while (pts.length && pts[0].life <= 0) pts.shift();

      const cell = 13, radius = 110;
      const rgb = getComputedStyle(document.documentElement).getPropertyValue("--trail").trim();
      ctx.font = `${cell}px monospace`;
      ctx.textAlign = "center";
      ctx.textBaseline = "middle";
      const cols = Math.ceil(w / cell), rows = Math.ceil(h / cell);
      for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
          const x = c * cell + cell / 2, y = r * cell + cell / 2;
          let v = 0;
          for (let i = pts.length - 1; i >= 0; i -= 2) {
            const p = pts[i], d = Math.hypot(x - p.x, y - p.y);
            if (d < radius) v = Math.max(v, (1 - d / radius) * p.life);
          }
          if (v > 0.03) {
            v += Math.sin(x * 0.01 + t) * Math.cos(y * 0.01 + t * 0.7) * 0.06;
            v = Math.max(0, Math.min(1, v));
            ctx.fillStyle = `rgba(${rgb}, ${v * 0.9})`;
            ctx.fillText(chars[Math.min(chars.length - 1, Math.floor(v * chars.length))], x, y);
          }
        }
      }
      requestAnimationFrame(frame);
    };
    // only animate while the footer is on screen
    new IntersectionObserver(([en]) => {
      const was = running;
      running = en.isIntersecting && !reduceMotion;
      if (running && !was) { resize(); head.x = w / 2; head.y = h / 2; requestAnimationFrame(frame); }
    }).observe(footer);
  })();

  /* ───────── drawing board (about) ───────── */
  const board = document.querySelector("[data-board]");
  if (board) {
    const wrap = board.querySelector(".board__canvas");
    const canvas = wrap.querySelector("canvas");
    const hint = wrap.querySelector(".board__hint");
    const ctx = canvas.getContext("2d");
    const KEY = "winnie-drawing";
    const history = [];
    let color = null, size = 4, erasing = false, drawing = false, last = null, dpr = 1;

    const fit = (snapshot) => {
      const r = wrap.getBoundingClientRect();
      dpr = Math.min(window.devicePixelRatio || 1, 2);
      canvas.width = r.width * dpr; canvas.height = r.height * dpr;
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.lineCap = "round"; ctx.lineJoin = "round";
      if (snapshot) restore(snapshot);
    };
    const restore = (url) => {
      const img = new Image();
      img.onload = () => {
        const r = wrap.getBoundingClientRect();
        ctx.save(); ctx.globalCompositeOperation = "source-over";
        ctx.clearRect(0, 0, r.width, r.height);
        ctx.drawImage(img, 0, 0, r.width, r.height);
        ctx.restore();
        hint.style.opacity = 0;
      };
      img.src = url;
    };
    const snapshot = () => canvas.toDataURL("image/png");
    const save = () => store.set(KEY, snapshot());

    fit(store.get(KEY));
    let rt;
    window.addEventListener("resize", () => { clearTimeout(rt); const s = snapshot(); rt = setTimeout(() => fit(s), 150); });

    const pos = (e) => { const r = canvas.getBoundingClientRect(); return { x: e.clientX - r.left, y: e.clientY - r.top }; };
    const inkColor = () => color || getComputedStyle(document.documentElement).getPropertyValue("--fg").trim();
    canvas.addEventListener("pointerdown", (e) => {
      drawing = true; last = pos(e);
      canvas.setPointerCapture(e.pointerId);
      history.push(snapshot()); if (history.length > 30) history.shift();
      hint.style.opacity = 0;
      ctx.globalCompositeOperation = erasing ? "destination-out" : "source-over";
      ctx.strokeStyle = ctx.fillStyle = inkColor();
      ctx.lineWidth = erasing ? size * 4 : size;
      ctx.beginPath(); ctx.arc(last.x, last.y, ctx.lineWidth / 2, 0, Math.PI * 2); ctx.fill();
    });
    canvas.addEventListener("pointermove", (e) => {
      if (!drawing) return;
      const p = pos(e);
      ctx.beginPath(); ctx.moveTo(last.x, last.y); ctx.lineTo(p.x, p.y); ctx.stroke();
      last = p;
    });
    const end = () => { if (drawing) { drawing = false; save(); } };
    canvas.addEventListener("pointerup", end);
    canvas.addEventListener("pointercancel", end);

    board.querySelectorAll(".swatch").forEach((s) => s.addEventListener("click", () => {
      board.querySelectorAll(".swatch").forEach((x) => x.classList.remove("is-active"));
      s.classList.add("is-active");
      color = s.dataset.color === "ink" ? null : s.dataset.color;
      erasing = false; board.querySelector("[data-erase]").classList.remove("is-active");
    }));
    board.querySelector("[data-size]").addEventListener("input", (e) => { size = +e.target.value; });
    board.querySelector("[data-erase]").addEventListener("click", (e) => { erasing = !erasing; e.currentTarget.classList.toggle("is-active", erasing); });
    board.querySelector("[data-undo]").addEventListener("click", () => {
      const prev = history.pop();
      if (prev) { restore(prev); store.set(KEY, prev); }
    });
    board.querySelector("[data-clear]").addEventListener("click", () => {
      history.push(snapshot());
      const r = wrap.getBoundingClientRect();
      ctx.clearRect(0, 0, r.width, r.height);
      save(); hint.style.opacity = 1;
    });
    board.querySelector("[data-download]").addEventListener("click", () => {
      const out = document.createElement("canvas");
      out.width = canvas.width; out.height = canvas.height;
      const o = out.getContext("2d");
      o.fillStyle = getComputedStyle(wrap).backgroundColor; o.fillRect(0, 0, out.width, out.height);
      o.drawImage(canvas, 0, 0);
      const a = document.createElement("a");
      a.download = "drawing.png"; a.href = out.toDataURL("image/png"); a.click();
    });
  }
})();
