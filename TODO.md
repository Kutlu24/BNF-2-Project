# Open items

This file lists the open maintenance items of this repository. It does not list content work.

- Content work and course review live in the
  [issue tracker](https://github.com/maehr/critical-ai-literacy-for-historians/issues).
- The long-term goals live in the
  [roadmap](https://github.com/maehr/critical-ai-literacy-for-historians#roadmap) in `README.md`.
- The rules for a change live in
  [AGENTS.md](https://github.com/maehr/critical-ai-literacy-for-historians/blob/main/AGENTS.md) and in
  [CONTRIBUTING.md](CONTRIBUTING.md).

## Archiving and citation

The project has no release and no DOI yet. Complete these four steps in order.

1. Connect the repository to [Zenodo](https://zenodo.org/account/settings/github/). See the
   [GitHub guide](https://docs.github.com/en/repositories/archiving-a-github-repository/referencing-and-citing-content).
2. Create a `.zenodo.json` file. Add the creators, the contributors, the keywords, and the two licenses. See
   the [Zenodo documentation](https://developers.zenodo.org/#add-metadata-to-your-github-repository-release).
3. Tag the first release. The tag must match the pattern `v[0-9]*`, because `cliff.toml` looks for that
   pattern.
4. Enable the DOI badge in `README.md`. Remove the HTML comment around the badge, and replace
   `ZENODO_RECORD` with the record number from the Zenodo deposit URL. The repository ID in the badge is
   `1081381221`.

## Metadata to keep current

- `CITATION.cff`: add the DOI and the version after the first release.
- `README.md`: update the citation block after the first release.

## Done

The repository already has these items:

- GitHub security alerts and Dependabot updates
- A ruleset on `main` that requires a pull request
- A lint gate that covers every `.md`, `.yml`, `.json`, and `.qmd` file
- A publish workflow that lints, renders, checks the links, and deploys to GitHub Pages
- A changelog workflow that generates `CHANGELOG.md` and commits it to the pull request branch

## Open items from the Friction Log v3 walkthrough (round 3)

These items need a human decision or real model output. They are marked with `TODO` comments or bracketed placeholders in the exercise files.

- Legal check of the publication note (Article 50(4)) in "Arbeitsbereich einrichten" (de, en, fr). The seminar-paper classification was removed; the page now refers students to their university rules.
- Dodis terms of use for passing the edition text to an AI system (`startpaket-dodis-5020.qmd` and the translations).
- Check the sample answer to Source Criticism task 1a and the Chicago reference solution in Citing against the sources.
- Choose an open-access English article to replace the German test article in Citing (placeholder callout in Citing).
- Answer keys and a gallery of typical AI errors on Dodis 5020 need real model output. Collect them in the pilot.
- Pilot with 5 to 8 students: log actual minutes per step, run the prompts on two consumer systems, then rewrite the "At a glance" tables.
- Fill the placeholders in the course's own AI-use disclosure on the home page.
- Interactive web version: every `_rueckmeldung.qmd` / `_feedback.qmd` / `_retour.qmd` include marks the place for a per-page feedback form. Bracketed `[...]` fields in prompts and templates mark the inputs the interactive page should render as form fields.

## Reading access (open-access check)

`scripts/reading_access.py` classifies every entry of `bibliography.bib` and generates the pages
`de/lesezugang.qmd`, `en/reading-access.qmd` and `fr/acces-aux-lectures.qmd`. Do not edit those pages by hand.

- `python3 scripts/reading_access.py fetch` asks OpenAlex for each DOI and writes `data/reading-access.json`.
  Entries without a DOI are classified by hand in `OVERRIDES` (with a note of what was verified).
- `python3 scripts/reading_access.py pages` rewrites the three pages from that file.
- Re-run both before a release and review the diff. A new bibliography entry without a DOI needs an `OVERRIDES` entry.
- Open to check once in a browser: the EDPB consultation page (the host did not resolve during the check) and the
  Data Feminism web edition (the automated check got HTTP 403).
