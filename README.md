# wwinnieliu.com

Winnie Liu's portfolio — a static site (HTML, CSS, vanilla JS). No build step.

- Projects and their images are listed in `assets/projects.js`.
- `tools/sync_portfolio.py` rebuilds `assets/img/` from each project's `include/`
  folder in "portfolio images" (the folder this site lives in).
- Preview locally: `python3 -m http.server 5173`, then open http://localhost:5173.
