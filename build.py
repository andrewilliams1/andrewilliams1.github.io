#!/usr/bin/env python3
"""Build the résumé PDF and website from resume.yaml.

Usage:
    python build.py            # everything
    python build.py --no-pdf   # skip LaTeX (no TeX install needed)

Outputs:
    build/andre-williams-resume.tex / .pdf
    _site/                     # what GitHub Pages serves
"""
import argparse
import re
import shutil
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, StrictUndefined

ROOT = Path(__file__).resolve().parent
BUILD = ROOT / "build"
SITE = ROOT / "_site"
PDF_NAME = "andre-williams-resume"

ASSETS = ROOT / "assets"          # images etc., copied to _site/assets/
STATIC_SITE_FILES = ["CNAME"]      # optional; copied to the site root if present

LATEX_ESCAPES = {
    "\\": r"\textbackslash{}",
    "&": r"\&",
    "%": r"\%",
    "$": r"\$",
    "#": r"\#",
    "_": r"\_",
    "{": r"\{",
    "}": r"\}",
    "~": r"\textasciitilde{}",
    "^": r"\textasciicircum{}",
}
LATEX_RE = re.compile("|".join(re.escape(k) for k in LATEX_ESCAPES))


def latex_escape(value):
    return LATEX_RE.sub(lambda m: LATEX_ESCAPES[m.group()], str(value))


def fmt_date(value):
    """Accepts YYYY-MM or a full YYYY-MM-DD date; always displays 'Mon YYYY'."""
    text = str(value).strip()
    if text.lower() == "present":
        return "Present"
    return datetime.strptime(text[:7], "%Y-%m").strftime("%b %Y")


def load_data():
    data = yaml.safe_load((ROOT / "resume.yaml").read_text(encoding="utf-8"))
    # Optional fields default to empty so templates can simply test them.
    for proj in data.get("projects", []):
        for key, empty in (("context", ""), ("tags", []), ("bullets", [])):
            proj.setdefault(key, empty)
        proj.setdefault("resume", True)   # resume: false = site only
        proj.setdefault("url", "")
    for job in data["work"]:
        job.setdefault("location", "")
        job.setdefault("bullets", [])
    data["work_groups"] = group_roles(data["work"])
    return data


def group_roles(work):
    """Group consecutive roles at the same org, so promotions share one block."""
    groups = []
    for job in work:
        if groups and groups[-1]["org"] == job["org"]:
            g = groups[-1]
            g["roles"].append(job)
            g["start"] = job["start"]          # roles are newest first
        else:
            groups.append({"org": job["org"], "location": job.get("location", ""),
                           "start": job["start"], "end": job["end"], "roles": [job]})
    return groups


def fmt_year(value):
    return str(value)[:4]


def env(autoescape=False, **delims):
    e = Environment(
        autoescape=autoescape,
        loader=FileSystemLoader(ROOT / "templates"),
        undefined=StrictUndefined,
        trim_blocks=True,
        lstrip_blocks=True,
        keep_trailing_newline=True,
        **delims,
    )
    e.filters["date"] = fmt_date
    e.filters["year"] = fmt_year
    return e


def build_latex(data, compile_pdf):
    tex_env = env(
        block_start_string="((*", block_end_string="*))",
        variable_start_string="(((", variable_end_string=")))",
        comment_start_string="((=", comment_end_string="=))",
    )
    tex_env.filters["e"] = latex_escape
    tex = tex_env.get_template("resume.tex.j2").render(
        **data,
        pdf_subtitle=data["basics"].get("pdf_subtitle", ""),
    )
    tex_path = BUILD / f"{PDF_NAME}.tex"
    tex_path.write_text(tex, encoding="utf-8")
    print(f"· wrote {tex_path.relative_to(ROOT)}")
    pdf = BUILD / f"{PDF_NAME}.pdf"
    if not compile_pdf:
        # Reuse the last compiled PDF so the site's download link still works.
        if pdf.exists():
            print(f"· reusing existing {pdf.relative_to(ROOT)}")
            return pdf
        print("! no PDF built yet: the site's résumé download link will be broken locally")
        return None
    cmd = ["latexmk", "-pdf", "-interaction=nonstopmode", "-halt-on-error",
           f"-outdir={BUILD}", str(tex_path)]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stdout[-3000:])
        sys.exit("LaTeX build failed")
    pdf = BUILD / f"{PDF_NAME}.pdf"
    print(f"· wrote {pdf.relative_to(ROOT)}")
    return pdf


def build_site(data, pdf):
    SITE.mkdir(exist_ok=True)
    html = env(autoescape=True).get_template("index.html.j2").render(
        **data, pdf_name=PDF_NAME, build_date=datetime.now().strftime("%B %Y"))
    (SITE / "index.html").write_text(html, encoding="utf-8")
    if ASSETS.exists():
        shutil.copytree(ASSETS, SITE / "assets", dirs_exist_ok=True)
    for name in STATIC_SITE_FILES:
        src = ROOT / name
        if src.exists():
            shutil.copy2(src, SITE / name)
    if pdf:
        shutil.copy2(pdf, SITE / pdf.name)
    print(f"· assembled {SITE.relative_to(ROOT)}/")


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--no-pdf", action="store_true", help="skip compiling the PDF")
    args = parser.parse_args()
    BUILD.mkdir(exist_ok=True)
    data = load_data()
    pdf = build_latex(data, compile_pdf=not args.no_pdf)
    build_site(data, pdf)


if __name__ == "__main__":
    main()
