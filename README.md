# andre-williams.com

One file, `resume.yaml`, builds the résumé PDF and the website.

## Updating

1. Edit `resume.yaml`.
2. Commit to `main` (directly, or by merging a PR). GitHub Actions builds and deploys in about a minute, with the PDF at `/andre-williams-resume.pdf`. A failed build never touches the live site.
3. To update LinkedIn, copy from the live site: the About text is `summary` in `resume.yaml`, and each role's bullets match the site.

## Building locally

```bash
pip install -r requirements.txt
python build.py            # needs TeX Live/MiKTeX with the packages listed in build.yml
python build.py --no-pdf   # site only (reuses the last PDF if there is one)
```

Outputs land in `build/` (PDF, .tex) and `_site/` (what Pages serves).

## Layout

- `resume.yaml`: all content
- `templates/`: résumé (LaTeX) and site (HTML) layouts
- `assets/`: images and other static files, copied to the site as-is
- `build.py`: renders everything into `build/` and `_site/`

## One-time setup

In the repo's **Settings → Pages**, set **Source** to **GitHub Actions**. The custom domain stays as configured.
