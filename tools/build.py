#!/usr/bin/env python3
"""Builds the graphics for the Novista-io GitHub organisation profile.

Every word comes from novista.io (src/content in the website repo), so the
profile and the site say the same thing. Change the copy below, then run:

    tools/fetch_fonts.sh                 # once: the three website fonts
    python3 tools/build.py               # needs: pip install uharfbuzz fonttools

Text is converted to outlines: an SVG shown through <img> on GitHub cannot
load web fonts, so this is the only way it looks the same everywhere.
Animations are plain CSS inside each SVG and stop under reduced motion.
"""
import base64
import io
import json
import os
import random
import re
import zlib
import struct

import uharfbuzz as hb
from fontTools.pens.svgPathPen import SVGPathPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TOOLS = os.path.join(ROOT, "tools")
OUT = os.path.join(ROOT, "profile", "assets")

# ---------------------------------------------------------------- copy

TAGLINE_PILL = "12 platforms in production"
HEADLINE = ("We don’t just build", "software.", "We run it.")
HERO_SUB = (
    "Novista builds custom software, AI automation and mobile applications — "
    "and operates twelve of its own platforms across education, healthcare, "
    "pharmacy, retail and distribution. The systems on the right are ours."
)
STATS = [("12", "Platforms"), ("6", "Industries"), ("4", "Practice areas")]

SERVICES = [
    ("web", "globe", "Web Development",
     "Web experiences designed to turn visitors into customers.",
     ["SaaS platforms", "Customer portals", "E-commerce", "Admin dashboards"]),
    ("mobile", "smartphone", "Mobile Development",
     "Turn your idea into a mobile experience your customers actually want to use.",
     ["iOS & Android", "Cross-platform", "Field & ops apps", "Backend integration"]),
    ("ai", "bot", "AI Solutions",
     "Put AI to work where it creates real business value.",
     ["AI agents", "Workflow automation", "Document intelligence", "LLM integrations"]),
    ("transformation", "refresh-ccw", "Digital Transformation",
     "Modernise the way your business works — from outdated systems to connected digital operations.",
     ["Legacy modernisation", "Systems integration", "Cloud migration", "Process automation"]),
]

# (slug, icon, name, category, tagline, preview), in the website's order.
PRODUCTS = [
    ("school-management", "graduation-cap", "School Management", "Industry platforms",
     "One system for admissions, academics, fees and parents.", "roster"),
    ("point-of-sale", "store", "Point of Sale", "Business operations",
     "Fast retail checkout that keeps stock and accounts in step.", "checkout"),
    ("hospital-management", "stethoscope", "Hospital Management System", "Industry platforms",
     "Patient flow, clinical records and billing in one place.", "roster"),
    ("laboratory-management", "flask-conical", "Laboratory Management System", "Industry platforms",
     "From sample collection to verified report, tracked end to end.", "lab"),
    ("erp", "layers", "ERP", "Business operations",
     "The operational backbone, configured to how you actually work.", "chart"),
    ("crm", "users", "CRM", "Business operations",
     "Every lead, conversation and deal in one pipeline.", "pipeline"),
    ("pharmacy-management", "pill", "Pharmacy Management", "Industry platforms",
     "Dispensing, batch control and expiry tracking without the manual checks.", "checkout"),
    ("hrms", "users", "HRMS", "Business operations",
     "Attendance, payroll and people records that agree with each other.", "roster"),
    ("accounting", "calculator", "Accounting", "Business operations",
     "Books that close on time because the data arrives already correct.", "checkout"),
    ("distribution-management", "truck", "Distribution Management", "Industry platforms",
     "Orders, routes and receivables across a whole dealer network.", "chart"),
    ("ai-agents", "bot", "AI Agents", "AI products",
     "Agents that do the routine work inside your systems.", "agent"),
    ("ai-enabled-solutions", "sparkles", "AI-Enabled Solutions", "AI products",
     "AI built into the software you already run.", "agent"),
]
# The grid groups them by category; the hero wall keeps the website's order.
CATEGORY_ORDER = ["Industry platforms", "Business operations", "AI products"]
INDUSTRIES = ["Education", "Healthcare", "Pharmacy & Life Sciences", "Retail & Commerce",
              "Distribution & Logistics", "Professional Services"]

PROCESS = [
    ("compass", "Discover", "Understand your business, users, goals and constraints."),
    ("map", "Plan", "Define the solution, architecture, roadmap and priorities."),
    ("hammer", "Build", "Design and develop using modern, scalable technologies."),
    ("rocket", "Launch", "Test, deploy, monitor and optimise."),
    ("trending-up", "Grow", "Keep improving the product as your business evolves."),
]

# ("si:<simple-icons slug>" | "lu:<lucide name>", label)
STACK = [
    ("Frontend", [("si:nextdotjs", "Next.js"), ("si:react", "React"), ("si:typescript", "TypeScript"),
                  ("si:tailwindcss", "Tailwind CSS"), ("si:angular", "Angular")]),
    ("Backend", [("si:nodedotjs", "Node.js"), ("si:dotnet", ".NET"), ("si:python", "Python"),
                 ("lu:server", "REST APIs"), ("si:graphql", "GraphQL")]),
    ("Mobile", [("si:react", "React Native"), ("si:flutter", "Flutter"), ("si:swift", "Swift"),
                ("si:kotlin", "Kotlin")]),
    ("AI", [("si:claude", "Claude"), ("si:openai", "OpenAI"), ("lu:layers", "RAG pipelines"),
            ("lu:bot", "AI agents"), ("lu:database", "Vector databases"),
            ("lu:sparkles", "Model Context Protocol")]),
    ("Data", [("si:postgresql", "PostgreSQL"), ("lu:database", "SQL Server"), ("si:mysql", "MySQL"),
              ("si:redis", "Redis"), ("lu:server", "Data warehousing")]),
    ("Cloud & DevOps", [("si:amazonwebservices", "AWS"), ("lu:cloud", "Azure"),
                        ("si:googlecloud", "Google Cloud"), ("si:docker", "Docker"),
                        ("si:githubactions", "CI/CD"), ("si:vercel", "Vercel")]),
]

TEAM = [
    ("bilal", "Muhammad Bilal Rasool", "CEO & Co-Founder",
     "Leads Novista’s direction and scopes every engagement around what the current "
     "way of working actually costs — including when the honest answer is a smaller build."),
    ("moin", "Moin Akmal Khan", "CTO & Co-Founder",
     "Owns the architecture and engineering standards behind everything Novista ships, "
     "and reviews the architecture on every engagement personally."),
]

HEADERS = [
    ("services", "Services", "Four ways we help",
     "Four practice areas, one team. Most projects draw on more than one — which is the "
     "point, because the parts have to work together."),
    ("platforms", "The estate", "Twelve platforms. Already running.",
     "Adopt one and we configure it to your operation. Faster than starting from nothing."),
    ("process", "How we work", "From idea to impact",
     "The same five stages on every engagement, scaled to the size of the project. You always "
     "know which one you are in and what comes next."),
    ("stack", "Technology", "The right tool for your problem",
     "We choose technology based on your business requirements — not the other way round. "
     "A stack that is unfashionable but well understood by your team will usually beat one "
     "that is new and impressive."),
    ("team", "About Novista", "Practical technology, built by people who ask about your business first",
     "We build solutions that solve real business problems — and we are straight with you "
     "about which ones software cannot solve."),
]

CTA_TITLE = "Have an idea, challenge, or project in mind?"
CTA_TEXT = (
    "Tell us what you are trying to achieve. We will help you figure out the best way "
    "forward — and tell you honestly if we are not the right fit."
)

# ---------------------------------------------------------------- palette
# Dark-theme tokens from the website's globals.css. The night ground stays dark
# on both GitHub themes, exactly as it does on the site.

NIGHT, NIGHT_2 = "#070c16", "#0b1628"
SURFACE, SURFACE_2 = "#0e1524", "#151e30"
LINE, NIGHT_LINE = "#1e2940", "#26344d"
INK, INK_SOFT, MUTED = "#f4f8fd", "#dbe5f2", "#96a9c2"
G1, G2, G3, G4 = "#24427a", "#2e77c9", "#4fb2ee", "#8bdefb"
ACCENT, ACCENT_2 = "#4fb2ee", "#6cc4f2"
# Section headers sit on GitHub's own background, so they come in two themes.
THEMES = {
    "light": {"ink": "#0b1628", "muted": "#5b6a80", "label": "#1e5fa8", "g": ("#1e5fa8", "#2e9be0")},
    "dark": {"ink": "#f4f8fd", "muted": "#93a3ba", "label": "#6cc4f2", "g": ("#2e77c9", "#4fb2ee")},
}

REDUCED_MOTION = "@media (prefers-reduced-motion:reduce){*{animation:none!important}}"


def fmt(v):
    r = round(v, 1)
    if r == int(r):
        return str(int(r))
    return ("%.1f" % r).replace("-0.", "-.").lstrip("0") if abs(r) < 1 else "%.1f" % r


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


# ---------------------------------------------------------------- fonts


class Face:
    count = 0

    def __init__(self, file, **axes):
        tt = TTFont(os.path.join(TOOLS, "fonts", file))
        tt = instancer.instantiateVariableFont(tt, axes)
        buf = io.BytesIO()
        tt.save(buf)
        data = buf.getvalue()
        self.tt = TTFont(io.BytesIO(data))
        self.glyphs = self.tt.getGlyphSet()
        self.order = self.tt.getGlyphOrder()
        self.upem = self.tt["head"].unitsPerEm
        self.font = hb.Font(hb.Face(data))
        self.key = "abcdefghijklmnop"[Face.count]
        Face.count += 1

    def shape(self, text):
        buf = hb.Buffer()
        buf.add_str(text)
        buf.guess_segment_properties()
        hb.shape(self.font, buf, {"kern": True, "liga": True})
        return [(i.codepoint, p.x_advance, p.x_offset, p.y_offset)
                for i, p in zip(buf.glyph_infos, buf.glyph_positions)]

    def width(self, text, size, track=0.0):
        g = self.shape(text)
        return (sum(a for _, a, _, _ in g) + track * self.upem * max(len(g) - 1, 0)) * size / self.upem

    def outline(self, gid, tx=0.0, ty=0.0, s=1.0, ntos=None):
        pen = SVGPathPen(self.glyphs, ntos=ntos or (lambda v: str(int(round(v)))))
        self.glyphs[self.order[gid]].draw(TransformPen(pen, (s, 0, 0, -s, tx, ty)))
        return pen.getCommands()

    def wrap(self, text, size, max_w, track=0.0):
        lines, line = [], ""
        for word in text.split(" "):
            trial = (line + " " + word).strip()
            if not line or self.width(trial, size, track) <= max_w:
                line = trial
            else:
                lines.append(line)
                line = word
        lines.append(line)
        return lines


DISPLAY = Face("BricolageGrotesque.ttf", opsz=96, wght=700, wdth=100)
TITLE = Face("BricolageGrotesque.ttf", opsz=32, wght=620, wdth=100)
BODY = Face("Geist.ttf", wght=400)
BODY_MEDIUM = Face("Geist.ttf", wght=550)
LABEL = Face("Archivo.ttf", wght=600, wdth=100)

LUCIDE = json.load(open(os.path.join(TOOLS, "lucide-icons.json")))
SIMPLE = json.load(open(os.path.join(TOOLS, "simple-icons.json")))

# ---------------------------------------------------------------- svg


class Svg:
    def __init__(self, w, h, title):
        self.w, self.h, self.title = w, h, title
        self.defs, self.body, self.css = [], [], []
        self.glyphs = {}
        self.n = 0

    def uid(self, prefix):
        self.n += 1
        return "%s%d" % (prefix, self.n)

    def add(self, *parts):
        self.body.extend(parts)

    def text(self, face, s, x, y, size, fill, anchor="start", track=0.0, upper=False,
             extra="", gradient=False):
        """One line of text as outlines. `gradient` draws it as a single path in
        page coordinates, so a userSpaceOnUse gradient lines up across it."""
        if upper:
            s = s.upper()
        w = face.width(s, size, track)
        if anchor == "middle":
            x -= w / 2
        elif anchor == "end":
            x -= w
        scale = size / face.upem
        pen = 0.0
        if gradient:
            d = []
            for gid, adv, xo, yo in face.shape(s):
                d.append(face.outline(gid, x + (pen + xo) * scale, y - yo * scale, scale, ntos=fmt))
                pen += adv + track * face.upem
            return '<path d="%s" fill="%s"%s/>' % ("".join(d), fill, extra)
        uses = []
        for gid, adv, xo, yo in face.shape(s):
            key = "%s%d" % (face.key, gid)
            if key not in self.glyphs:
                self.glyphs[key] = face.outline(gid)
            if self.glyphs[key]:
                uses.append('<use href="#%s" x="%s"%s/>' % (key, fmt(pen + xo), ' y="%s"' % fmt(-yo) if yo else ""))
            pen += adv + track * face.upem
        return '<g transform="translate(%s %s) scale(%.6g)" fill="%s"%s>%s</g>' % (
            fmt(x), fmt(y), scale, fill, extra, "".join(uses))

    def paragraph(self, face, s, x, y, size, max_w, lh, fill, anchor="start", track=0.0, extra=""):
        lines = face.wrap(s, size, max_w, track)
        for i, line in enumerate(lines):
            self.add(self.text(face, line, x, y + i * lh, size, fill, anchor, track, extra=extra))
        return y + (len(lines) - 1) * lh, lines

    def icon(self, name, x, y, size, color, width=2.0, extra=""):
        kind, slug = name.split(":") if ":" in name else ("lu", name)
        s = size / 24
        if kind == "si":
            return '<path transform="translate(%s %s) scale(%.5g)" d="%s" fill="%s"%s/>' % (
                fmt(x), fmt(y), s, SIMPLE[slug], color, extra)
        parts = []
        for tag, attrs in LUCIDE[slug]:
            parts.append("<%s %s/>" % (tag, " ".join('%s="%s"' % (k, v) for k, v in attrs.items())))
        return ('<g transform="translate(%s %s) scale(%.5g)" fill="none" stroke="%s" stroke-width="%s" '
                'stroke-linecap="round" stroke-linejoin="round"%s>%s</g>') % (
            fmt(x), fmt(y), s, color, fmt(width), extra, "".join(parts))

    def write(self, name):
        glyphs = "".join('<path id="%s" d="%s"/>' % (k, d) for k, d in self.glyphs.items() if d)
        css = "".join(self.css) + REDUCED_MOTION
        svg = (
            '<svg xmlns="http://www.w3.org/2000/svg" width="%d" height="%d" viewBox="0 0 %d %d" '
            'role="img" aria-label="%s"><title>%s</title><style>%s</style><defs>%s%s</defs>%s</svg>'
        ) % (self.w, self.h, self.w, self.h, esc(self.title), esc(self.title), css,
             glyphs, "".join(self.defs), "".join(self.body))
        path = os.path.join(OUT, name)
        with open(path, "w") as f:
            f.write(svg)
        return path, len(svg)


# ---------------------------------------------------------------- shared pieces


def mark_paths():
    src = open(os.path.join(TOOLS, "novista-mark.svg")).read()
    paths = dict(re.findall(r'<path class="([na])" d="([^"]+)"', src))
    return paths["n"], paths["a"]


MARK_N, MARK_A = mark_paths()


def logo(x, y, size, n_fill, a_fill):
    # The source mark is drawn on a 2872 unit square, flipped (potrace output).
    s = size / 2872
    return ('<g transform="translate(%s %s) scale(%.6g)"><g transform="translate(-786 3704) scale(1 -1)">'
            '<path d="%s" fill="%s"/><path d="%s" fill="%s"/></g></g>') % (
        fmt(x), fmt(y), s, MARK_N, n_fill, MARK_A, a_fill)


def noise_png(size=96, seed=7):
    """A small tile of grain, as a data URI PNG (the website uses grain too)."""
    rnd = random.Random(seed)
    raw = b"".join(b"\x00" + bytes(v for _ in range(size) for v in (255, 255, 255, rnd.randrange(0, 256)))
                   for _ in range(size))

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0))
           + chunk(b"IDAT", zlib.compress(raw, 9)) + chunk(b"IEND", b""))
    return "data:image/png;base64," + base64.b64encode(png).decode()


GRAIN = noise_png()


def night_panel(svg, w, h, r, aurora=(), grain=True, border=True):
    """Night ground with drifting aurora light, clipped to a rounded card."""
    clip, bg = svg.uid("c"), svg.uid("bg")
    svg.defs.append('<clipPath id="%s"><rect width="%d" height="%d" rx="%d"/></clipPath>' % (clip, w, h, r))
    svg.defs.append('<linearGradient id="%s" x1="0" y1="0" x2="1" y2="1">'
                    '<stop offset="0" stop-color="%s"/><stop offset="1" stop-color="%s"/></linearGradient>'
                    % (bg, NIGHT_2, NIGHT))
    svg.add('<g clip-path="url(#%s)">' % clip, '<rect width="%d" height="%d" fill="url(#%s)"/>' % (w, h, bg))
    for i, (cx, cy, rx, ry, color, alpha, dx, dy, dur) in enumerate(aurora):
        gid, cls = svg.uid("au"), svg.uid("drift")
        svg.defs.append('<radialGradient id="%s"><stop offset="0" stop-color="%s" stop-opacity="%s"/>'
                        '<stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>'
                        % (gid, color, alpha, color))
        svg.css.append("@keyframes k%s{50%%{transform:translate(%dpx,%dpx)}}.%s{animation:k%s %ds ease-in-out infinite}"
                       % (cls, dx, dy, cls, cls, dur))
        svg.add('<ellipse class="%s" cx="%d" cy="%d" rx="%d" ry="%d" fill="url(#%s)"/>' % (cls, cx, cy, rx, ry, gid))
    if grain:
        pat = svg.uid("grain")
        svg.defs.append('<pattern id="%s" width="96" height="96" patternUnits="userSpaceOnUse">'
                        '<image href="%s" width="96" height="96"/></pattern>' % (pat, GRAIN))
        svg.add('<rect width="%d" height="%d" fill="url(#%s)" opacity=".035"/>' % (w, h, pat))
    return clip


def close_panel(svg, w, h, r, border=True):
    svg.add("</g>")
    if border:
        svg.add('<rect x=".75" y=".75" width="%s" height="%s" rx="%s" fill="none" stroke="%s" stroke-width="1.5"/>'
                % (fmt(w - 1.5), fmt(h - 1.5), fmt(r - .75), NIGHT_LINE))


def pulse_dot(svg, x, y, color, delay=0.0, r=4):
    cls = svg.uid("p")
    svg.css.append(
        "@keyframes k%s{0%%{transform:scale(1);opacity:.55}80%%,100%%{transform:scale(3.2);opacity:0}}"
        ".%s{transform-box:fill-box;transform-origin:center;animation:k%s 2.4s cubic-bezier(0,0,.2,1) infinite;animation-delay:%.2fs}"
        % (cls, cls, cls, delay))
    return ('<circle class="%s" cx="%s" cy="%s" r="%s" fill="%s"/><circle cx="%s" cy="%s" r="%s" fill="%s"/>'
            % (cls, fmt(x), fmt(y), fmt(r), color, fmt(x), fmt(y), fmt(r), color))


def linear(svg, stops, x1=0, y1=0, x2=1, y2=0, user=None):
    gid = svg.uid("lg")
    units = ""
    if user:
        x1, y1, x2, y2 = user
        units = ' gradientUnits="userSpaceOnUse"'
    svg.defs.append('<linearGradient id="%s" x1="%s" y1="%s" x2="%s" y2="%s"%s>%s</linearGradient>' % (
        gid, fmt(x1), fmt(y1), fmt(x2), fmt(y2), units,
        "".join('<stop offset="%s" stop-color="%s"%s/>' % (o, c, ' stop-opacity="%s"' % a if a != 1 else "")
                for o, c, a in stops)))
    return "url(#%s)" % gid


# ---------------------------------------------------------------- hero

MUTED_BAR = 'fill="#93a3ba" fill-opacity=".25"'
MUTED_FAINT = 'fill="#93a3ba" fill-opacity=".18"'
BRAND_BAR = 'fill="%s" fill-opacity=".6"' % ACCENT_2


def bar(x, y, w, attrs=MUTED_BAR, h=6):
    return '<rect x="%s" y="%s" width="%s" height="%s" rx="%s" %s/>' % (fmt(x), fmt(y), fmt(w), h, fmt(h / 2), attrs)


def preview(svg, kind, x, y, w, title):
    """The website's PlatformPreview cards (src/components/visuals/previews.tsx), redrawn."""
    body_h = {"roster": 112, "chart": 114, "checkout": 98, "pipeline": 106, "agent": 106, "lab": 100}[kind]
    h = 28 + body_h
    out = ['<g transform="translate(%s %s)">' % (fmt(x), fmt(y)),
           '<rect width="%d" height="%d" rx="12" fill="%s" stroke="%s"/>' % (w, h, SURFACE, LINE),
           '<path d="M12 .5h%dq11.5 0 11.5 11.5v16.5h-%dv-16.5q0-11.5 11.5-11.5z" fill="%s"/>' % (w - 24, w - 1, SURFACE_2),
           '<path d="M.5 28.5h%d" stroke="%s"/>' % (w - 1, LINE)]
    for i in range(3):
        out.append('<circle cx="%d" cy="14.5" r="2.6" fill="#93a3ba" fill-opacity=".3"/>' % (14 + i * 8))
    size = 10.5
    while LABEL.width(title, size, .02) > w - 54 and size > 8.5:
        size -= .25
    out.append(svg.text(LABEL, title, 44, 18.5, size, MUTED, track=.02))
    inner = w - 24
    by = 28 + 12
    if kind == "roster":
        for i, (frac, on) in enumerate([(.62, True), (.48, False), (.70, True), (.40, False)]):
            ry = by + i * 24
            out.append('<circle cx="20" cy="%d" r="8" %s/>' % (ry + 8, 'fill="%s" fill-opacity=".5"' % ACCENT_2 if on else MUTED_FAINT))
            out.append(bar(36, ry + 5, (inner - 24 - 30) * frac))
            out.append(bar(w - 12 - 18, ry + 5, 18, BRAND_BAR if on else MUTED_BAR))
    elif kind == "chart":
        bars = [38, 54, 44, 68, 58, 82]
        gap = 6
        bw = (inner - gap * 5) / 6
        grad = linear(svg, [(0, G2, 1), (1, G3, 1)], 0, 1, 0, 0)
        for i, hpc in enumerate(bars):
            bh = 64 * hpc / 100
            fill = 'fill="%s"' % grad if i == 5 else MUTED_FAINT
            out.append('<rect x="%s" y="%s" width="%s" height="%s" rx="2" %s/>' % (
                fmt(12 + i * (bw + gap)), fmt(by + 64 - bh), fmt(bw), fmt(bh), fill))
        out.append('<path d="M12 %sh%d" stroke="%s"/>' % (fmt(by + 74.5), inner, LINE))
        out.append(bar(12, by + 84, inner * .34))
        out.append(bar(w - 12 - inner * .2, by + 84, inner * .2, BRAND_BAR))
    elif kind == "checkout":
        for i, frac in enumerate([.58, .44, .66]):
            out.append(bar(12, by + i * 14, (inner - 30) * frac))
            out.append(bar(w - 12 - 22, by + i * 14, 22))
        out.append('<path d="M12 %sh%d" stroke="%s"/>' % (fmt(by + 46.5), inner, LINE))
        out.append(bar(12, by + 61, inner * .3))
        out.append('<rect x="%d" y="%d" width="56" height="16" rx="6" fill="%s"/>' % (w - 12 - 56, by + 56, ACCENT_2))
    elif kind == "pipeline":
        cw = (inner - 12) / 3
        cols = [[1, 1, 0], [1, 0, 0], [1, 1, 1]]
        for ci, col in enumerate(cols):
            cx = 12 + ci * (cw + 6)
            out.append(bar(cx, by, 32, MUTED_BAR, h=4))
            for ri, filled in enumerate(col):
                ry = by + 10 + ri * 26
                if filled:
                    stroke = ACCENT_2 if (ci == 2 and ri == 0) else LINE
                    so = ' stroke-opacity=".5"' if (ci == 2 and ri == 0) else ""
                    fill = SURFACE_2 if (ci == 2 and ri == 0) else SURFACE
                    out.append('<rect x="%s" y="%d" width="%s" height="20" rx="6" fill="%s" stroke="%s"%s/>'
                               % (fmt(cx + .5), ry, fmt(cw - 1), fill, stroke, so))
                else:
                    out.append('<rect x="%s" y="%d" width="%s" height="20" rx="6" fill="none" stroke="%s" '
                               'stroke-opacity=".6" stroke-dasharray="3 3"/>' % (fmt(cx + .5), ry, fmt(cw - 1), LINE))
    elif kind == "agent":
        out.append('<rect x="12" y="%d" width="16" height="16" rx="5" %s/>' % (by, MUTED_BAR))
        out.append('<path d="M%d %dh%sq8 0 8 8v8q0 8-8 8h-%sq-8 0-8-8v-12q0-4 4-4z" %s/>'
                   % (36, by, fmt(inner - 24 - 16), fmt(inner - 24 - 16), MUTED_FAINT))
        bw = (inner - 24) * .75
        bx = w - 12 - 16 - 8 - bw
        out.append('<path d="M%s %dh%sq4 0 4 4v20q0 8-8 8h-%sq-8 0-8-8v-16q0-8 8-8z" fill="%s" fill-opacity=".25" stroke="%s" stroke-opacity=".4"/>'
                   % (fmt(bx + 8), by + 32, fmt(bw - 12), fmt(bw - 4), ACCENT_2, ACCENT_2))
        out.append('<rect x="%d" y="%d" width="16" height="16" rx="5" fill="%s" fill-opacity=".6"/>' % (w - 28, by + 32, ACCENT_2))
        cls = svg.uid("blink")
        svg.css.append("@keyframes k%s{50%%{opacity:.25}}.%s{animation:k%s 2s ease-in-out infinite}" % (cls, cls, cls))
        out.append('<circle class="%s" cx="15" cy="%d" r="3" fill="%s"/>' % (cls, by + 80, ACCENT))
        out.append(svg.text(LABEL, "running", 24, by + 83.5, 9.5, MUTED))
    elif kind == "lab":
        for i, (frac, state) in enumerate([(.56, "done"), (.44, "run"), (.62, "wait")]):
            ry = by + i * 26
            if i:
                out.append('<path d="M12 %sh%d" stroke="%s"/>' % (fmt(ry - .5), inner, LINE))
            out.append('<rect x="12" y="%d" width="4" height="12" rx="2" fill="#93a3ba" fill-opacity=".3"/>' % (ry + 6))
            out.append(bar(24, ry + 9, (inner - 40) * frac))
            dot = {"done": 'fill="%s"' % ACCENT, "run": 'fill="%s"' % ACCENT_2, "wait": MUTED_BAR}[state]
            out.append('<circle cx="%d" cy="%d" r="4" %s/>' % (w - 16, ry + 12, dot))
    out.append("</g>")
    return "".join(out), h


def hero():
    W, H = 1200, 640
    svg = Svg(W, H, "Novista Solutions — We don’t just build software. We run it.")
    night_panel(svg, W, H, 28, aurora=[
        (1010, 60, 460, 360, G2, .55, -70, 50, 26),
        (180, 700, 520, 380, "#1e5fa8", .45, 80, -40, 30),
        (880, 420, 300, 260, G3, .16, -50, -40, 22),
    ])
    # Platform wall: the website's hero centrepiece, two columns drifting.
    glow = svg.uid("glow")
    svg.defs.append('<radialGradient id="%s"><stop offset="0" stop-color="%s" stop-opacity=".22"/>'
                    '<stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>' % (glow, G3, G3))
    svg.add('<ellipse cx="905" cy="320" rx="330" ry="330" fill="url(#%s)"/>' % glow)
    mask, fade = svg.uid("m"), svg.uid("fade")
    svg.defs.append('<linearGradient id="%s" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity="0"/>'
                    '<stop offset=".16" stop-color="#fff"/><stop offset=".84" stop-color="#fff"/>'
                    '<stop offset="1" stop-color="#fff" stop-opacity="0"/></linearGradient>' % fade)
    svg.defs.append('<mask id="%s"><rect x="640" width="560" height="%d" fill="url(#%s)"/></mask>' % (mask, H, fade))
    cw, gap = 234, 18
    columns = [(PRODUCTS[:6], 662, "up", 52, 0), (PRODUCTS[6:], 662 + cw + gap, "down", 64, 34)]
    svg.add('<g mask="url(#%s)">' % mask)
    for items, cx, direction, dur, offset in columns:
        cards, y, = [], 0
        for _ in range(2):
            for slug, icon, name, cat, tag, kind in items:
                markup, h = preview(svg, kind, cx, y, cw, name)
                cards.append(markup)
                y += h + 16
        track = y / 2
        cls = svg.uid("col")
        frm, to = (0, -track) if direction == "up" else (-track, 0)
        svg.css.append("@keyframes k%s{from{transform:translateY(%spx)}to{transform:translateY(%spx)}}"
                       ".%s{animation:k%s %ds linear infinite}" % (cls, fmt(frm + offset), fmt(to + offset), cls, cls, dur))
        svg.add('<g class="%s" transform="translate(0 %d)">%s</g>' % (cls, offset + (frm if direction == "down" else 0), "".join(cards)))
    svg.add("</g>")

    x = 64
    svg.add(logo(x, 52, 54, INK, ACCENT))
    svg.add(svg.text(DISPLAY, "Novista", x + 66, 80, 30, INK, track=-.02))
    svg.add(svg.text(LABEL, "Solutions", x + 67, 99, 10.5, MUTED, track=.32, upper=True))

    pill_text = TAGLINE_PILL.upper()
    pw = LABEL.width(pill_text, 11.5, .14) + 50
    svg.add('<rect x="%d" y="146" width="%s" height="34" rx="17" fill="#fff" fill-opacity=".04" stroke="%s"/>' % (x, fmt(pw), NIGHT_LINE))
    svg.add(pulse_dot(svg, x + 19, 163, ACCENT, r=3.5))
    svg.add(svg.text(LABEL, pill_text, x + 33, 167.5, 11.5, MUTED, track=.14))

    size, lh = 62, 64
    y = 252
    l1, l2a, l2b = HEADLINE
    svg.add(svg.text(DISPLAY, l1, x, y, size, INK, track=-.03))
    svg.add(svg.text(DISPLAY, l2a, x, y + lh, size, INK, track=-.03))
    gx = x + DISPLAY.width(l2a + " ", size, -.03)
    gw = DISPLAY.width(l2b, size, -.03)
    grad = linear(svg, [(0, G3, 1), (.55, G4, 1), (1, "#c5efff", 1)], user=(gx, 0, gx + gw, 0))
    svg.add(svg.text(DISPLAY, l2b, gx, y + lh, size, grad, track=-.03, gradient=True))
    assert DISPLAY.width(l1, size, -.03) < 580, "headline too wide"
    end, _ = svg.paragraph(BODY, HERO_SUB, x, y + lh + 56, 18.5, 520, 29, MUTED)

    sy = end + 44
    svg.add('<path d="M%d %sh500" stroke="%s"/>' % (x, fmt(sy + .5), NIGHT_LINE))
    for i, (value, label) in enumerate(STATS):
        sx = x + i * 160
        svg.add(svg.text(DISPLAY, value, sx, sy + 46, 34, INK, track=-.02))
        svg.add(svg.text(LABEL, label, sx, sy + 70, 11, MUTED, track=.14, upper=True))
    assert sy + 70 < H - 30, "hero text overflows: %d" % (sy + 70)
    close_panel(svg, W, H, 28)
    return svg.write("hero.svg")


# ---------------------------------------------------------------- services


def service_layout(promise, caps, W=590):
    """Returns the promise's last baseline and where each chip goes."""
    end = 182 + (len(BODY.wrap(promise, 18.5, W - 72)) - 1) * 28
    cx, cy, chips = 36, end + 30, []
    for cap in caps:
        cw = BODY_MEDIUM.width(cap, 15) + 32
        if cx + cw > W - 36:
            cx, cy = 36, cy + 44
        chips.append((cap, cx, cy, cw))
        cx += cw + 10
    return end, chips


SERVICE_H = max(service_layout(s[3], s[4])[1][-1][2] for s in SERVICES) + 34 + 88


def service_card(index, key, icon, name, promise, caps):
    W, H = 590, SERVICE_H
    svg = Svg(W, H, "%s — %s" % (name, promise))
    night_panel(svg, W, H, 24, aurora=[(W - 40, -10, 260, 200, G2, .42, -40, 30, 18 + index * 3)], grain=False)
    tile = linear(svg, [(0, G2, 1), (1, G3, 1)], 0, 0, 1, 1)
    svg.add('<rect x="36" y="36" width="58" height="58" rx="17" fill="%s"/>' % tile)
    svg.add(svg.icon(icon, 50, 50, 30, "#fff", 2))
    svg.add(svg.text(LABEL, "%02d" % (index + 1), W - 36, 58, 13, MUTED, anchor="end", track=.14))
    svg.add(svg.text(TITLE, name, 36, 146, 33, INK, track=-.02))
    svg.paragraph(BODY, promise, 36, 182, 18.5, W - 72, 28, MUTED)
    for cap, cx, cy, cw in service_layout(promise, caps)[1]:
        svg.add('<rect x="%s" y="%s" width="%s" height="34" rx="17" fill="%s" stroke="%s"/>' % (
            fmt(cx), fmt(cy), fmt(cw), SURFACE_2, NIGHT_LINE))
        svg.add(svg.text(BODY_MEDIUM, cap, cx + 16, cy + 22, 15, INK_SOFT))
    label = "Explore"
    svg.add(svg.text(LABEL, label, 36, H - 34, 12.5, ACCENT_2, track=.14, upper=True))
    lw = LABEL.width(label.upper(), 12.5, .14)
    cls = svg.uid("nudge")
    svg.css.append("@keyframes k%s{50%%{transform:translateX(5px)}}.%s{animation:k%s 2.2s ease-in-out infinite}" % (cls, cls, cls))
    svg.add('<g class="%s">%s</g>' % (cls, svg.icon("arrow-right", 36 + lw + 8, H - 47, 16, ACCENT_2, 2.2)))
    close_panel(svg, W, H, 24)
    return svg.write("service-%s.svg" % key)


# ---------------------------------------------------------------- platforms


def platforms():
    cols, tw, th, gap = 3, 388, 156, 18
    ordered = sorted(PRODUCTS, key=lambda p: CATEGORY_ORDER.index(p[3]))
    rows = (len(ordered) + cols - 1) // cols
    W = cols * tw + (cols - 1) * gap
    strip_y = rows * (th + gap)
    H = strip_y + 74
    svg = Svg(W, H, "Twelve platforms built and run by Novista: " + ", ".join(p[2] for p in ordered))
    for i, (slug, icon, name, cat, tag, kind) in enumerate(ordered):
        x, y = (i % cols) * (tw + gap), (i // cols) * (th + gap)
        clip = svg.uid("t")
        svg.defs.append('<clipPath id="%s"><rect width="%d" height="%d" rx="20"/></clipPath>' % (clip, tw, th))
        svg.add('<g transform="translate(%d %d)"><g clip-path="url(#%s)">' % (x, y, clip))
        bg = linear(svg, [(0, SURFACE, 1), (1, NIGHT, 1)], 0, 0, 1, 1)
        svg.add('<rect width="%d" height="%d" fill="%s"/>' % (tw, th, bg))
        gl = svg.uid("tg")
        svg.defs.append('<radialGradient id="%s"><stop offset="0" stop-color="%s" stop-opacity=".28"/>'
                        '<stop offset="1" stop-color="%s" stop-opacity="0"/></radialGradient>' % (gl, G2, G2))
        svg.add('<ellipse cx="%d" cy="0" rx="170" ry="110" fill="url(#%s)"/>' % (tw - 30, gl))
        svg.add("</g>")
        svg.add('<rect x=".75" y=".75" width="%s" height="%s" rx="19.25" fill="none" stroke="%s" stroke-width="1.5"/>'
                % (fmt(tw - 1.5), fmt(th - 1.5), NIGHT_LINE))
        svg.add('<rect x="24" y="24" width="46" height="46" rx="14" fill="%s" stroke="%s"/>' % (SURFACE_2, NIGHT_LINE))
        svg.add(svg.icon(icon, 35, 35, 24, G4, 2))
        svg.add(svg.text(LABEL, cat, 86, 41, 10.5, MUTED, track=.14, upper=True))
        size = 21
        while TITLE.width(name, size, -.01) > tw - 86 - 24 and size > 15:
            size -= .5
        svg.add(svg.text(TITLE, name, 86, 66, size, INK, track=-.01))
        svg.add(pulse_dot(svg, tw - 28, 37, ACCENT, delay=(i * .37) % 2.4, r=3.5))
        svg.paragraph(BODY, tag, 24, 106, 16, tw - 48, 24, MUTED)
        svg.add("</g>")
    # Industries strip, as under the website's hero.
    svg.add('<rect y="%d" width="%d" height="56" rx="28" fill="%s" stroke="%s"/>' % (strip_y, W, SURFACE, NIGHT_LINE))
    label = "INDUSTRIES"
    lx = 28
    svg.add(svg.text(LABEL, label, lx, strip_y + 33, 11, ACCENT_2, track=.18))
    x = lx + LABEL.width(label, 11, .18) + 26
    for j, ind in enumerate(INDUSTRIES):
        if j:
            svg.add('<circle cx="%s" cy="%s" r="2" fill="%s"/>' % (fmt(x - 13), fmt(strip_y + 28), NIGHT_LINE))
        svg.add(svg.text(BODY_MEDIUM, ind, x, strip_y + 33.5, 15, INK_SOFT))
        x += BODY_MEDIUM.width(ind, 15) + 26
    assert x - 26 < W - 20, "industries strip overflows: %d" % x
    return svg.write("platforms.svg")


# ---------------------------------------------------------------- process


def process():
    W, H = 1200, 330
    svg = Svg(W, H, "How we work: " + ", ".join("%d. %s" % (i + 1, t) for i, (_, t, _) in enumerate(PROCESS)))
    night_panel(svg, W, H, 28, aurora=[(600, -60, 520, 200, G2, .35, 0, 30, 20)], grain=True)
    n = len(PROCESS)
    xs = [140 + i * (W - 280) / (n - 1) for i in range(n)]
    ly = 82
    svg.add('<path d="M%s %dH%s" stroke="%s" stroke-width="2"/>' % (fmt(xs[0]), ly, fmt(xs[-1]), NIGHT_LINE))
    # A pulse of light travels the line; each stage lights as it passes.
    dur, start, end = 7.0, xs[0] - 60, xs[-1] + 60
    beam = linear(svg, [(0, G3, 0), (.5, G4, 1), (1, G3, 0)])
    cls = svg.uid("beam")
    svg.css.append("@keyframes k%s{from{transform:translateX(%spx)}to{transform:translateX(%spx)}}"
                   ".%s{animation:k%s %ss linear infinite}" % (cls, fmt(start - 70), fmt(end - 70), cls, cls, fmt(dur)))
    clipl = svg.uid("cl")
    svg.defs.append('<clipPath id="%s"><rect x="%s" y="%d" width="%s" height="8"/></clipPath>' % (clipl, fmt(xs[0]), ly - 4, fmt(xs[-1] - xs[0])))
    svg.add('<g clip-path="url(#%s)"><rect class="%s" x="0" y="%d" width="140" height="3" rx="1.5" fill="%s"/></g>' % (clipl, cls, ly - 1.5, beam))
    for i, (icon, title, summary) in enumerate(PROCESS):
        x = xs[i]
        t = (x - start) / (end - start) * dur
        lit = svg.uid("lit")
        svg.css.append("@keyframes k%s{0%%,100%%{opacity:0}4%%{opacity:1}22%%{opacity:0}}"
                       ".%s{animation:k%s %ss linear infinite;animation-delay:%.2fs}" % (lit, lit, lit, fmt(dur), t - .04 * dur))
        svg.add('<circle cx="%s" cy="%d" r="34" fill="%s" stroke="%s" stroke-width="1.5"/>' % (fmt(x), ly, SURFACE, NIGHT_LINE))
        ring = linear(svg, [(0, G2, 1), (1, G4, 1)], 0, 0, 1, 1)
        svg.add('<g class="%s"><circle cx="%s" cy="%d" r="34" fill="%s" fill-opacity=".14" stroke="%s" stroke-width="2"/></g>'
                % (lit, fmt(x), ly, G3, ring))
        svg.add(svg.icon(icon, x - 13, ly - 13, 26, INK_SOFT, 2))
        svg.add(svg.text(LABEL, "%02d" % (i + 1), x, 152, 12, ACCENT_2, anchor="middle", track=.16))
        svg.add(svg.text(TITLE, title, x, 186, 25, INK, anchor="middle", track=-.01))
        end_y, _ = svg.paragraph(BODY, summary, x, 218, 15.5, 196, 23, MUTED, anchor="middle")
        assert end_y < H - 24
    close_panel(svg, W, H, 28)
    return svg.write("process.svg")


# ---------------------------------------------------------------- stack


def stack():
    W = 1200
    pad, label_w, chip_h, chip_gap, row_gap = 48, 210, 46, 10, 14
    layout, y = [], pad
    for group, items in STACK:
        x, rows = pad + label_w, [[]]
        for icon, label in items:
            cw = 16 + 20 + 10 + BODY_MEDIUM.width(label, 16.5) + 18
            if x + cw > W - pad:
                x = pad + label_w
                rows.append([])
            rows[-1].append((icon, label, x, cw))
            x += cw + chip_gap
        layout.append((group, rows, y))
        y += len(rows) * chip_h + (len(rows) - 1) * chip_gap + row_gap * 2 + 1
    H = int(y - row_gap * 2 - 1 + pad)
    svg = Svg(W, H, "Technology we work in: " + "; ".join("%s: %s" % (g, ", ".join(l for _, l in it)) for g, it in STACK))
    night_panel(svg, W, H, 28, aurora=[(1100, H + 40, 420, 260, G2, .4, -60, -30, 24), (120, -40, 360, 200, "#1e5fa8", .35, 50, 20, 28)])
    # A slow sheen across the panel.
    sheen = linear(svg, [(0, "#fff", 0), (.5, "#fff", .05), (1, "#fff", 0)])
    cls = svg.uid("sheen")
    svg.css.append("@keyframes k%s{0%%{transform:translateX(-400px) skewX(-20deg)}60%%,100%%{transform:translateX(%dpx) skewX(-20deg)}}"
                   ".%s{animation:k%s 9s ease-in-out infinite}" % (cls, W + 200, cls, cls))
    svg.add('<rect class="%s" y="0" width="260" height="%d" fill="%s"/>' % (cls, H, sheen))
    for gi, (group, rows, gy) in enumerate(layout):
        if gi:
            svg.add('<path d="M%d %sH%d" stroke="%s"/>' % (pad, fmt(gy - row_gap - .5), W - pad, LINE))
        svg.add(svg.text(LABEL, group, pad, gy + 28, 12, ACCENT_2, track=.16, upper=True))
        for ri, row in enumerate(rows):
            ry = gy + ri * (chip_h + chip_gap)
            for icon, label, x, cw in row:
                svg.add('<rect x="%s" y="%s" width="%s" height="%d" rx="%d" fill="%s" stroke="%s"/>' % (
                    fmt(x), fmt(ry), fmt(cw), chip_h, chip_h // 2, SURFACE_2, NIGHT_LINE))
                svg.add(svg.icon(icon, x + 16, ry + 13, 20, INK_SOFT, 2))
                svg.add(svg.text(BODY_MEDIUM, label, x + 46, ry + 29, 16.5, INK_SOFT))
    close_panel(svg, W, H, 28)
    return svg.write("stack.svg")


# ---------------------------------------------------------------- team


def photo_uri(key):
    from PIL import Image
    img = Image.open(os.path.join(TOOLS, "team", key + ".jpg")).convert("RGB")
    side = min(img.size)
    top = int((img.height - side) * .18)  # 4:5 portraits: keep the face, not the chest
    img = img.crop(((img.width - side) // 2, top, (img.width - side) // 2 + side, top + side)).resize((240, 240), Image.LANCZOS)
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=82, optimize=True, progressive=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def team_card(index, key, name, role, line):
    W, H = 590, 250
    svg = Svg(W, H, "%s, %s at Novista Solutions" % (name, role))
    night_panel(svg, W, H, 24, aurora=[(0, H, 260, 200, G2, .38, 40, -20, 22 + index * 4)], grain=False)
    cx, cy, r = 100, 125, 62
    clip = svg.uid("ph")
    svg.defs.append('<clipPath id="%s"><circle cx="%d" cy="%d" r="%d"/></clipPath>' % (clip, cx, cy, r))
    svg.add('<image href="%s" x="%d" y="%d" width="%d" height="%d" clip-path="url(#%s)"/>' % (
        photo_uri(key), cx - r, cy - r, 2 * r, 2 * r, clip))
    ring = linear(svg, [(0, G2, 1), (.5, G4, 1), (1, G2, 0)], 0, 0, 1, 1)
    cls = svg.uid("spin")
    svg.css.append("@keyframes k%s{to{transform:rotate(360deg)}}.%s{transform-box:fill-box;transform-origin:center;"
                   "animation:k%s 14s linear infinite}" % (cls, cls, cls))
    svg.add('<circle class="%s" cx="%d" cy="%d" r="%d" fill="none" stroke="%s" stroke-width="2.5"/>' % (cls, cx, cy, r + 7, ring))
    x = 196
    svg.add(svg.text(LABEL, role, x, 70, 12, ACCENT_2, track=.16, upper=True))
    svg.add(svg.text(TITLE, name, x, 104, 27, INK, track=-.015))
    end, _ = svg.paragraph(BODY, line, x, 140, 16, W - x - 34, 24, MUTED)
    assert end < H - 20, name
    close_panel(svg, W, H, 24)
    return svg.write("team-%s.svg" % key)


# ---------------------------------------------------------------- headers


def header(key, label, title, desc, theme):
    t = THEMES[theme]
    W = 1200
    lines = DISPLAY.wrap(title, 44, 980, -.025)
    dlines = BODY.wrap(desc, 18.5, 860)
    H = 52 + len(lines) * 50 + 16 + len(dlines) * 29 + 8
    svg = Svg(W, H, "%s — %s" % (label, title))
    lw = LABEL.width(label.upper(), 12.5, .22)
    g = linear(svg, [(0, t["g"][0], 1), (1, t["g"][1], 1)])
    svg.add('<rect x="%s" y="11" width="28" height="3" rx="1.5" fill="%s"/>' % (fmt(W / 2 - lw / 2 - 40), g))
    svg.add('<rect x="%s" y="11" width="28" height="3" rx="1.5" fill="%s" transform="rotate(180 %s 12.5)"/>' % (
        fmt(W / 2 + lw / 2 + 12), g, fmt(W / 2 + lw / 2 + 26)))
    svg.add(svg.text(LABEL, label, W / 2, 17, 12.5, t["label"], anchor="middle", track=.22, upper=True))
    y = 66
    for line in lines:
        svg.add(svg.text(DISPLAY, line, W / 2, y, 44, t["ink"], anchor="middle", track=-.025))
        y += 50
    y += 4
    for line in dlines:
        svg.add(svg.text(BODY, line, W / 2, y, 18.5, t["muted"], anchor="middle"))
        y += 29
    return svg.write("h-%s-%s.svg" % (key, theme))


# ---------------------------------------------------------------- closing band


def cta():
    W, x = 1200, 64
    title_lines = DISPLAY.wrap(CTA_TITLE, 52, 700, -.03)
    text_lines = BODY.wrap(CTA_TEXT, 18.5, 560)
    by = 140 + (len(title_lines) - 1) * 58 + 10 + 58 + (len(text_lines) - 1) * 29 + 34
    H = int(by + 52 + 64)
    svg = Svg(W, H, CTA_TITLE + " Start a project with Novista.")
    night_panel(svg, W, H, 28, aurora=[
        (1080, 120, 420, 320, G2, .5, -60, 40, 24), (200, H + 60, 520, 260, "#1e5fa8", .4, 70, -30, 28)])
    # The mark's swoosh: an arc that draws itself and lands on the arrowhead.
    arc = "M560 %dC760 %d 960 300 1110 92" % (H + 50, H)
    stroke = linear(svg, [(0, G3, 0), (.7, G3, .8), (1, G4, 1)], user=(560, H + 50, 1110, 92))
    cls, head = svg.uid("arc"), svg.uid("head")
    svg.css.append(
        "@keyframes k%s{0%%{stroke-dashoffset:820;opacity:1}38%%{stroke-dashoffset:0;opacity:1}86%%{stroke-dashoffset:0;opacity:1}100%%{stroke-dashoffset:0;opacity:0}}"
        ".%s{stroke-dasharray:820;animation:k%s 8s cubic-bezier(.65,0,.35,1) infinite}"
        "@keyframes k%s{0%%,30%%{opacity:0;transform:translate(-30px,40px)}40%%,86%%{opacity:1;transform:none}100%%{opacity:0}}"
        ".%s{animation:k%s 8s cubic-bezier(.65,0,.35,1) infinite}" % (cls, cls, cls, head, head, head))
    svg.add('<path class="%s" d="%s" fill="none" stroke="%s" stroke-width="10" stroke-linecap="round" opacity=".18"/>' % (cls, arc, stroke))
    svg.add('<path class="%s" d="%s" fill="none" stroke="%s" stroke-width="3" stroke-linecap="round"/>' % (cls, arc, stroke))
    svg.add('<path class="%s" d="M1134 54l-8 52-12-14-18-2z" fill="%s"/>' % (head, ACCENT))
    svg.add(svg.text(LABEL, "Start a project", x, 78, 12.5, ACCENT_2, track=.22, upper=True))
    y = 140
    for line in title_lines:
        svg.add(svg.text(DISPLAY, line, x, y, 52, INK, track=-.03))
        y += 58
    for i, line in enumerate(text_lines):
        svg.add(svg.text(BODY, line, x, y + 10 + i * 29, 18.5, MUTED))
    label = "Start a Project"
    bw = BODY_MEDIUM.width(label, 17) + 76
    svg.add('<rect x="%d" y="%s" width="%s" height="52" rx="26" fill="%s"/>' % (x, fmt(by), fmt(bw), INK))
    svg.add(svg.text(BODY_MEDIUM, label, x + 26, by + 32, 17, NIGHT_2))
    nudge = svg.uid("nudge")
    svg.css.append("@keyframes k%s{50%%{transform:translateX(5px)}}.%s{animation:k%s 2.2s ease-in-out infinite}" % (nudge, nudge, nudge))
    svg.add('<g class="%s">%s</g>' % (nudge, svg.icon("arrow-right", x + bw - 44, by + 17, 18, NIGHT_2, 2.4)))
    close_panel(svg, W, H, 28)
    return svg.write("cta.svg")


def button(key, icon, label, primary):
    H = 56
    tw = BODY_MEDIUM.width(label, 18)
    W = int(24 + 22 + 12 + tw + 28)
    svg = Svg(W, H, label)
    if primary:
        fill = linear(svg, [(0, G2, 1), (1, G3, 1)], 0, 0, 1, 1)
        svg.add('<rect width="%d" height="%d" rx="%d" fill="%s"/>' % (W, H, H // 2, fill))
        color = "#fff"
    else:
        svg.add('<rect x=".75" y=".75" width="%s" height="%s" rx="%s" fill="%s" stroke="%s" stroke-width="1.5"/>' % (
            fmt(W - 1.5), fmt(H - 1.5), fmt(H / 2 - .75), NIGHT_2, NIGHT_LINE))
        color = INK
    svg.add(svg.icon(icon, 24, 17, 22, color, 2))
    svg.add(svg.text(BODY_MEDIUM, label, 58, 34.5, 18, color))
    return svg.write("btn-%s.svg" % key)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    results = [hero()]
    results += [service_card(i, *s) for i, s in enumerate(SERVICES)]
    results += [platforms(), process(), stack(), cta()]
    results += [team_card(i, *t) for i, t in enumerate(TEAM)]
    for h in HEADERS:
        results += [header(*h, theme) for theme in THEMES]
    results += [
        button("site", "globe", "novista.io", True),
        button("project", "arrow-up-right", "Start a project", False),
        button("mail", "mail", "hello@novista.io", False),
        button("whatsapp", "message-circle", "WhatsApp", False),
    ]
    for path, size in results:
        print("%7.1f KB  %s" % (size / 1024, os.path.relpath(path, ROOT)))
