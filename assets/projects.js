/*
  All project content lives here. To add a project or a case study later,
  edit this list — every page (home, project pages) reads from it.
  folder: the project's folder in "portfolio images" (or a path like ~/Desktop/x);
  only files in its include/ (or included/) subfolder are used (run site/tools/sync_portfolio.py after changing them).
  cover: made from the include/ file with "cover" in its name. with no such file,
  name any image here and it is used for the home-page card only.
  website, credits, problem and solution ({ title, text }) are optional.
  keep_order: true leaves images in the order listed instead of opening with the cover.
  images: files inside assets/img/<slug>/ ; the first one is the hero.
  wrap files in [ ] to show them side by side at the same height; .mp4 files
  play as looping videos. images are never cropped, except
  shave: { "file.jpg": 0.02 } — cuts that share off every side of a picture
  (for stray white edges), keeping its shape.
  projects are listed newest first.
*/
window.PROJECTS = [
  {
    slug: "track-of-time",
    folder: "~/Desktop/track of time",
    title: "track of time",
    type: "campaign, motion, and web design",
    year: "2026",
    credits: "Jaime Lai, Kevin Chang, Claude Code",
    website: "https://wwinnieliu.github.io/C2.5-Track-of-Time/#landing",
    overview:
      "Every day, commuters spend minutes on train platforms beside strangers sharing the same delay, yet no one acknowledges it. Waiting is a set of risograph cards that people fill in on the back with what they’re experiencing while they wait. Each pack also includes a legend card and a narration card. An interactive website collects the cards so visitors can see what everyone else was doing during the same wait. We used vibrant colors throughout to bring out the joy we want commuters to feel, so waiting reads as a shared ritual rather than lost time.",
    problem: {
      title: "We wait together, but never really together",
      text: "We think of the minutes on a train platform as dead time. Strangers share the same delay and the same boredom, but no one acknowledges it, so a shared moment goes by unnoticed.",
    },
    solution: {
      title: "Small Cards for a Shared Pause",
      text: "A set of risograph cards handed out on the platform. Riders write about their own wait on the back of a card, which turns a few idle minutes into a record that strangers waiting with them can share.",
    },
    cover: "cover.jpg",
    keep_order: true,
    card_tips: {"source": "cover.JPEG", "tips": [[[[458, 950], [730, 1350]], [[860, 1352], [1000, 1250]]], [[[1000, 1090], [1400, 1352]], [[1910, 950], [1672, 1352]]]]},
    card: "card.jpg",
    images: ["clock-ending.mp4", "track-of-time-motion.mp4", "pb059876.jpg", ["pb059851.jpg", "track-of-time.jpg"], ["cover.jpg", "pb059731.jpg"], ["pb059761.jpg", "pb050426.jpg"], ["pb050367.jpg", "pb050373.jpg"], ["track-of-time-color-palette.jpg", "pb050526.jpg"]],
  },
  {
    slug: "design-justice-network-principles",
    folder: "Design Justice Network Principles",
    title: "design justice network principles",
    type: "editorial, web",
    year: "2026",
    role: "editorial and web designer",
    client: "self directed",
    overview:
      "This project responds to the Design Justice Network Principles, a manifesto of ten principles that rethinks how design, technology, and planning can serve communities more equitably. I chose dots and lines as my core visual language: each dot represents an individual designer, and the lines connecting them show that we don’t work in isolation but are part of a collaborative, interconnected whole. Together, the dots and lines also became the structural foundation of the project, forming a flexible grid system that organizes each principle while keeping the layout cohesive. To make the manifesto accessible wherever it’s read, I designed both a desktop and a mobile version, adapting the grid to each format so it stays clear and engaging across screens.",
    cover: "cover.jpg",
    card: "card.jpg",
    images: ["cover.jpg", ["screen-recording-2026-11-01-at-8-08-58-pm.mp4", "screen-recording-2026-11-01-at-8-11-04-pm.mp4"], ["dsc08163.jpg", "dsc08164.jpg"], ["dsc08166.jpg", "dsc08178.jpg"]],
  },
  {
    slug: "what-we-see-when-we-read",
    folder: "What We See When We Read",
    title: "what we see when we read",
    type: "editorial design",
    year: "2026",
    role: "book designer",
    client: "self directed",
    overview:
      "An editorial book based on Peter Mendelsund’s exploration of how we visualize stories as we read, designed to mirror the blurry, ever-shifting images that form between reader and page. Gradients and a playful palette create atmosphere and movement without sacrificing clarity, while woven-in imagery shows what I pictured while reading, making the design feel personal and process-driven. Expressive but readable typography guides you through the content, balancing something loose and imaginative with a layout that still holds together as a cohesive system.",
    cover: "cover.jpg",
    shave: { "cover.jpg": 0.02, "isimg-829350.jpg": 0.03 },
    images: ["cover.jpg", "whatweseewhenweread-ezgif-com-optimize.mp4", ["isimg-829350.jpg", "isimg-829749.jpg"], ["isimg-829439.jpg", "isimg-830341.jpg"], "isimg-828333.jpg"],
  },
  {
    slug: "type-specimen",
    folder: "Type Speciman",
    title: "type specimen",
    type: "editorial design",
    year: "2026",
    role: "editorial designer",
    client: "self directed",
    overview:
      "A type specimen book showcasing three typefaces with distinct personalities: Futura 100, Commuter Sans, and Richmond Text. Rather than keeping it clean and minimal, I layered acetate over paper for a tactile, translucent depth, using color and pattern to give each typeface its own visual world within a cohesive system. The spiral binding adds a handmade, zine-like feel, letting the typefaces breathe while giving the layouts enough energy to make flipping through genuinely fun.",
    cover: "cover.jpg",
    card: "card.jpg",
    images: ["cover.jpg", "type-specimen.mp4", ["dsc05171.jpg", "dsc05175.jpg"], ["dsc05186.jpg", "dsc05201.jpg"], ["dsc05202.jpg", "dsc05211.jpg"], ["typespecimen-mockup1.jpg", "typespecimen-mockup2.jpg"]],
  },
  {
    slug: "water",
    folder: "Water Infographic",
    title: "water infographic",
    type: "infographic",
    year: "2026",
    role: "designer",
    client: "self directed",
    overview:
      "A data-driven infographic breaking down water usage, sources, pollution, and scarcity across the United States, set on a deep black background that makes the blues pop for a moodier, more dramatic take on a potentially dry topic. Custom water drop illustrations and icons carry the visual language throughout, keeping it cohesive rather than chart after chart. Boldly scaled typography guides the eye through the hierarchy, turning dense data into something digestible, visually interesting, and worth stopping to read.",
    cover: "cover.jpg",
    card: "card.jpg",
    images: ["cover.jpg", "dsc05529.jpg"],
  },
  {
    slug: "nyc-card-deck",
    folder: "NYC Card Deck",
    title: "nyc card deck",
    type: "brand identity",
    year: "2025",
    role: "brand designer",
    client: "self directed",
    overview:
      "A fully playable deck of poker cards celebrating New York City’s most iconic landmarks and symbols, with custom illustrations on each card face and hand-drawn landmark icons woven into a cohesive pattern. The project aims to capture the city’s nostalgic essence, with the hand-drawn touch adding an authenticity that deepens the emotional connection between visitor and city. The result works as both a souvenir and a functional game.",
    cover: "cover.jpg",
    images: ["cover.jpg", "pokercards-compressed.mp4", ["isimg-835591.jpg", "isimg-835705.jpg"], ["isimg-836071.jpg", "isimg-836292.jpg"]],
  },
  {
    slug: "clix",
    folder: "Clix",
    title: "clix",
    type: "packaging design, brand identity",
    year: "2025",
    role: "brand, packaging designer",
    client: "self directed",
    overview:
      "Developed from an entrepreneurship class, Clix is a business concept centered on a modular kitchenware system whose magnetic attachments let users customize their kitchenware to suit how they dine. Drawing on the Muji aesthetic, I designed a series of posters and logos that balance minimalism with a decorative touch. The result is a clean, cohesive brand identity that feels as functional and adaptable as the product itself.",
    cover: "cover.jpg",
    card: "card.jpg",
    images: ["cover.jpg", ["clix-bowl-mockuo.jpg", "clix-fork-mockup.jpg"], ["entre-mockup.jpg", "entre-mockup-copy-2.jpg"], "entre-logo-design.jpg"],
  },
  {
    slug: "rainshower",
    folder: "Rainshower",
    title: "rainshower",
    type: "packaging design, brand identity",
    year: "2024",
    role: "packaging designer, brand designer",
    client: "self directed",
    overview:
      "Rainshower is an organic soap brand inspired by South America’s rainforests, created to raise awareness about endangered animals threatened by habitat loss and overhunting, with the chameleon as its central figure. I designed custom typography based on the chameleon’s scales, paired with muted greens and earthy tones that reinforce the product’s organic, sustainable character. Clean packaging ties it together, communicating simplicity and environmental consciousness.",
    cover: "cover.jpg",
    images: ["cover.jpg", "pinklogosoap.jpg", "greenlogosoap.jpg", "print-layouts.jpg", "screenshot-2026-10-14-at-9-07-05-pm.jpg"],
  },
];
window.MEDIA_VERSION = "1793941595";
