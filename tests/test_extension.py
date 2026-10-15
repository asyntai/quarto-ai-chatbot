"""
Tests for the Asyntai AI chatbot Quarto extension.

Each test renders a real Quarto project in a temporary folder and reads the
output. Set QUARTO to the quarto executable if it is not on PATH.

    python tests/test_extension.py
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
EXT = os.path.join(ROOT, "_extensions", "ai-chatbot")
QUARTO = os.environ.get("QUARTO") or shutil.which("quarto") or "quarto"

WID = "asyntai_1a2b3c4d5e6f"
DEFAULT_SRC = "https://widget.asyntai.com/static/js/chat-widget.js"
TAG_RE = re.compile(r"<script[^>]*data-asyntai-id=\"([^\"]*)\"[^>]*>\s*</script>")

passed = 0
failed = []


def check(name, ok, detail=""):
    global passed
    if ok:
        passed += 1
        print("ok   " + name)
    else:
        failed.append(name)
        print("FAIL " + name + ("  " + detail if detail else ""))


def project(files):
    d = tempfile.mkdtemp(prefix="qa-")
    shutil.copytree(EXT, os.path.join(d, "_extensions", "ai-chatbot"))
    for path, body in files.items():
        full = os.path.join(d, path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w", encoding="utf-8") as f:
            f.write(body)
    return d


def render(d, *args):
    r = subprocess.run([QUARTO, "render", *args], cwd=d, capture_output=True,
                       text=True, encoding="utf-8", errors="replace")
    return r.returncode, r.stdout + r.stderr


def read(d, path):
    with open(os.path.join(d, path), encoding="utf-8") as f:
        return f.read()


def tags(html):
    return TAG_RE.findall(html)


def src_of(html):
    m = re.search(r"<script[^>]*src=\"([^\"]*)\"[^>]*data-asyntai-id", html)
    return m.group(1) if m else None


WEBSITE_CFG = (
    "project:\n  type: website\nwebsite:\n  title: Test\n"
    "  navbar:\n    left:\n      - index.qmd\n      - about.qmd\n"
    "filters:\n  - ai-chatbot\nasyntai:\n  widget-id: " + WID + "\n"
)


def test_website():
    d = project({
        "_quarto.yml": WEBSITE_CFG,
        "index.qmd": "---\ntitle: Home\n---\n\nHello.\n",
        "about.qmd": "---\ntitle: About\n---\n\nAbout us.\n",
        "docs/guide.qmd": "---\ntitle: Guide\n---\n\nA page in a subfolder.\n",
        "404.qmd": "---\ntitle: Not found\n---\n\nThe page is gone.\n",
    })
    code, out = render(d)
    check("website renders", code == 0, out[-500:])
    for page in ["index.html", "about.html", "docs/guide.html", "404.html"]:
        html = read(d, "_site/" + page)
        check("website " + page + " has exactly one widget tag", tags(html) == [WID], str(tags(html)))
    html = read(d, "_site/index.html")
    check("tag loads the Asyntai CDN script", src_of(html) == DEFAULT_SRC, str(src_of(html)))
    check("tag is async", re.search(r"<script async[^>]*data-asyntai-id", html) is not None)
    check("tag sits after the page content, before </body>",
          html.rfind("data-asyntai-id") > html.find("<main") and html.rfind("data-asyntai-id") < html.rfind("</body>"))
    check("site search index has no widget tag", "data-asyntai-id" not in read(d, "_site/search.json"))
    shutil.rmtree(d, ignore_errors=True)


def test_page_override():
    d = project({
        "_quarto.yml": WEBSITE_CFG,
        "index.qmd": "---\ntitle: Home\n---\n\nHello.\n",
        "about.qmd": "---\ntitle: About\nasyntai:\n  widget-id: " + WID + "\n  enabled: false\n---\n\nNo chat here.\n",
    })
    code, out = render(d)
    check("page override renders", code == 0, out[-500:])
    check("page with enabled: false has no tag", tags(read(d, "_site/about.html")) == [])
    check("other pages keep the tag", tags(read(d, "_site/index.html")) == [WID])
    shutil.rmtree(d, ignore_errors=True)


def test_blog_listing():
    d = project({
        "_quarto.yml": WEBSITE_CFG,
        "index.qmd": "---\ntitle: Blog\nlisting:\n  contents: posts\n---\n",
        "about.qmd": "---\ntitle: About\n---\n\nAbout.\n",
        "posts/first.qmd": "---\ntitle: First post\ndate: 2026-10-01\n---\n\nPost text.\n",
    })
    code, out = render(d)
    check("blog renders", code == 0, out[-500:])
    check("blog listing page has the tag", tags(read(d, "_site/index.html")) == [WID])
    check("blog post has the tag", tags(read(d, "_site/posts/first.html")) == [WID])
    shutil.rmtree(d, ignore_errors=True)


def test_book():
    d = project({
        "_quarto.yml": (
            "project:\n  type: book\nbook:\n  title: Handbook\n  chapters:\n"
            "    - index.qmd\n    - intro.qmd\nformat:\n  html: default\n"
            "filters:\n  - ai-chatbot\nasyntai:\n  widget-id: " + WID + "\n"
        ),
        "index.qmd": "# Preface {.unnumbered}\n\nHello.\n",
        "intro.qmd": "# Introduction\n\nText.\n",
    })
    code, out = render(d)
    check("book renders", code == 0, out[-500:])
    check("book preface has the tag", tags(read(d, "_book/index.html")) == [WID])
    check("book chapter has the tag", tags(read(d, "_book/intro.html")) == [WID])
    shutil.rmtree(d, ignore_errors=True)


def doc(front, body="Hello.\n"):
    return "---\n" + front + "filters:\n  - ai-chatbot\n---\n\n" + body


def test_single_formats():
    cfg = "asyntai:\n  widget-id: " + WID + "\n"
    d = project({
        "page.qmd": doc("title: Page\nformat: html\n" + cfg),
        "slides.qmd": doc("title: Slides\nformat: revealjs\n" + cfg, "## One\n\nA\n\n## Two\n\nB\n"),
        "board.qmd": doc("title: Board\nformat: dashboard\n" + cfg, "## Row\n\n::: {.card}\nText\n:::\n"),
        "selfcontained.qmd": doc("title: One file\nformat:\n  html:\n    embed-resources: true\n" + cfg),
    })
    for name, out_file, label in [
        ("page.qmd", "page.html", "single HTML document"),
        ("slides.qmd", "slides.html", "reveal.js slides"),
        ("board.qmd", "board.html", "dashboard"),
        ("selfcontained.qmd", "selfcontained.html", "embed-resources document"),
    ]:
        code, out = render(d, name)
        check(label + " renders", code == 0, out[-500:])
        if code == 0:
            html = read(d, out_file)
            check(label + " has exactly one widget tag", tags(html) == [WID], str(tags(html)))
            check(label + " still loads the script from the CDN", src_of(html) == DEFAULT_SRC, str(src_of(html)))
            check(label + " does not copy the widget code into the page", "asyntai-chained" not in html)
    shutil.rmtree(d, ignore_errors=True)


def test_non_html_formats():
    d = project({
        "report.qmd": doc("title: Report\nformat: docx\nasyntai:\n  widget-id: " + WID + "\n"),
        "notes.qmd": doc("title: Notes\nformat: gfm\nasyntai:\n  widget-id: " + WID + "\n"),
        "noid.qmd": doc("title: No ID\nformat: docx\n"),
    })
    code, out = render(d, "report.qmd")
    check("Word output renders", code == 0, out[-500:])
    code, out = render(d, "notes.qmd")
    check("Markdown output renders", code == 0, out[-500:])
    check("Markdown output has no widget tag", "asyntai" not in read(d, "notes.md"))
    code, out = render(d, "noid.qmd")
    check("Word output without settings renders (no HTML, no error)", code == 0, out[-500:])
    shutil.rmtree(d, ignore_errors=True)


def test_settings_errors():
    cases = [
        ("missing asyntai block", "", "add your widget ID"),
        ("empty widget-id", "asyntai:\n  widget-id: \"\"\n", '"widget-id" is required'),
        ("malformed widget-id", "asyntai:\n  widget-id: 12345\n", "does not look like a widget ID"),
        ("snippet pasted as widget-id", "asyntai:\n  widget-id: 'asyntai_abc\" onload=\"x'\n", "does not look like a widget ID"),
    ]
    for label, cfg, message in cases:
        d = project({"page.qmd": doc("title: Page\nformat: html\n" + cfg)})
        code, out = render(d, "page.qmd")
        # Quarto logs filter errors and finishes the page, like its own filters.
        check(label + " prints an ERROR line that explains the fix",
              ("ERROR" in out or "(E) ai-chatbot" in out) and message in out, out[-300:])
        check(label + " adds no widget tag", code == 0 and tags(read(d, "page.html")) == [])
        shutil.rmtree(d, ignore_errors=True)


def test_options():
    d = project({
        "trim.qmd": doc("title: T\nformat: html\nasyntai:\n  widget-id: '  " + WID + "  '\n"),
        "off.qmd": doc("title: O\nformat: html\nasyntai:\n  widget-id: " + WID + "\n  enabled: false\n"),
        "offnoid.qmd": doc("title: N\nformat: html\nasyntai:\n  enabled: false\n"),
        "url.qmd": doc("title: U\nformat: html\nasyntai:\n  widget-id: " + WID +
                       "\n  script-url: 'https://example.com/w.js?a=1&b=\"2\"'\n"),
    })
    code, out = render(d, "trim.qmd")
    check("spaces around widget-id are trimmed", code == 0 and tags(read(d, "trim.html")) == [WID], out[-300:])
    code, out = render(d, "off.qmd")
    check("enabled: false renders with no tag", code == 0 and tags(read(d, "off.html")) == [], out[-300:])
    code, out = render(d, "offnoid.qmd")
    check("enabled: false needs no widget-id", code == 0 and tags(read(d, "offnoid.html")) == [], out[-300:])
    code, out = render(d, "url.qmd")
    html = read(d, "url.html") if code == 0 else ""
    src = src_of(html) or ""
    check("script-url is used", code == 0 and src.startswith("https://example.com/w.js"), out[-300:])
    check("script-url quotes cannot break out of the attribute",
          '"2"' not in src and 'b="2"' not in html.replace("&quot;", "~"), src)
    shutil.rmtree(d, ignore_errors=True)


def test_quarto_add():
    d = tempfile.mkdtemp(prefix="qa-add-")
    zip_base = os.path.join(d, "ext")
    archive = shutil.make_archive(zip_base, "zip", ROOT, "_extensions")
    site = os.path.join(d, "site")
    os.makedirs(site)
    r = subprocess.run([QUARTO, "add", archive, "--no-prompt"], cwd=site,
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    installed = os.path.isfile(os.path.join(site, "_extensions", "ai-chatbot", "ai-chatbot.lua"))
    check("quarto add installs the extension", r.returncode == 0 and installed, (r.stdout + r.stderr)[-400:])
    with open(os.path.join(site, "page.qmd"), "w", encoding="utf-8") as f:
        f.write(doc("title: P\nformat: html\nasyntai:\n  widget-id: " + WID + "\n"))
    code, out = render(site, "page.qmd")
    check("installed extension adds the tag", code == 0 and tags(read(site, "page.html")) == [WID], out[-300:])
    shutil.rmtree(d, ignore_errors=True)


if __name__ == "__main__":
    print("quarto: " + subprocess.run([QUARTO, "--version"], capture_output=True, text=True).stdout.strip())
    for t in [test_website, test_page_override, test_blog_listing, test_book,
              test_single_formats, test_non_html_formats, test_settings_errors,
              test_options, test_quarto_add]:
        t()
    print("\n%d passed, %d failed" % (passed, len(failed)))
    sys.exit(1 if failed else 0)
