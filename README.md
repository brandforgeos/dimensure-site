# Dimensure website

Static site for https://dimensure.co.uk, hosted on HostGator and deployed with cPanel Git Version Control.

- `src/pages/*.html`: one file per page. Each starts with a `<!--META {...} -->` JSON header (title, description, breadcrumbs, schema, FAQs).
- `src/assets/`: stylesheet and the sample point-cloud viewer.
- `src/static/`: favicons and `.htaccess`, copied to the site root.
- `images/`: WebP images (1536 and 768 px).
- `build.py`: builds everything into `site/`, including `sitemap.xml`, `robots.txt` and `llms.txt`. Phone number, email and the Web3Forms key are set in the `SITE` block at the top.

## Updating the site

1. Edit files in `src/` (or `SITE` in `build.py`).
2. Run `python3 build.py`.
3. Commit everything, including `site/`, and push to `main`.
4. In cPanel > Git Version Control, pull and deploy `dimensure-site` (or call the VersionControl/VersionControlDeployment API).

## Before launch

- Replace the placeholder phone number and add the Web3Forms key in `build.py`.
- Remove the `X-Robots-Tag noindex` block from `src/static/.htaccess`.
