#!/usr/bin/env python3
"""Check the open-access status of every entry in bibliography.bib.

    python3 scripts/reading_access.py fetch   # query OpenAlex for DOI entries -> data/reading-access.json
    python3 scripts/reading_access.py pages   # write the three reading-access pages

`fetch` needs the network and only reads public metadata (DOI -> OpenAlex).
Entries without a DOI are classified in OVERRIDES below, by hand, after the
URL was opened. Re-run `fetch` before a release and review the diff.
"""
import json, re, sys, time, urllib.parse, urllib.request, datetime, pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent
BIB = ROOT / 'bibliography.bib'
DATA = ROOT / 'data' / 'reading-access.json'

def parse_bib():
    s = BIB.read_text(encoding='utf-8')
    out = {}
    for e in re.split(r'\n(?=@\w+\{)', s):
        m = re.match(r'@(\w+)\{([^,]+),', e)
        if not m:
            continue
        f = {k: v for k, v in re.findall(r'^\s*(\w+)\s*=\s*\{(.*)\},?\s*$', e, re.M)}
        f['_type'] = m.group(1)
        out[m.group(2)] = f
    return out

def tex(s):
    """Plain text from the BibTeX braces and accents used in this file."""
    rep = {'\\"{u}': 'ü', '\\"{o}': 'ö', '\\"{a}': 'ä', '\\"{U}': 'Ü', "\\'{a}": 'á', "\\'{i}": 'í', "\\'{e}": 'é', "\\'{E}": 'É', "\\'{o}": 'ó', "\\'{u}": 'ú', "\\'{c}": 'ć',
           '\\"u': 'ü', '\\"o': 'ö', '\\"a': 'ä', '\\ss': 'ß', '{\\ss}': 'ß', '\\&': '&', '\\_': '_', "\\'e": 'é', '\\`e': 'è'}
    for k, v in rep.items():
        s = s.replace(k, v)
    return re.sub(r'[{}]', '', s).replace('--', '–').strip()

def get(url):
    req = urllib.request.Request(url, headers={'User-Agent': 'critical-ai-literacy-reading-access/1.0'})
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.load(r)

def openalex(doi):
    u = ('https://api.openalex.org/works/https://doi.org/' + urllib.parse.quote(doi, safe='/') +
         '?select=open_access,best_oa_location,locations,primary_location')
    try:
        return get(u)
    except Exception as e:
        return {'error': str(e)}

def summarise(d):
    if 'error' in d:
        return {'status': 'unknown', 'error': d['error']}
    oa = d.get('open_access') or {}
    best = d.get('best_oa_location') or {}
    # prefer a repository copy that is a PDF / landing page different from the paywalled publisher page
    repo = None
    for loc in d.get('locations') or []:
        src = (loc.get('source') or {}).get('type')
        if loc.get('is_oa') and src == 'repository':
            repo = loc.get('pdf_url') or loc.get('landing_page_url'); break
    return {
        'status': oa.get('oa_status') or ('open' if oa.get('is_oa') else 'closed'),
        'is_oa': bool(oa.get('is_oa')),
        'url': best.get('pdf_url') or best.get('landing_page_url') or oa.get('oa_url'),
        'license': best.get('license'),
        'version': best.get('version'),
        'repository_copy': repo,
    }

# Entries without a DOI (or where the DOI record is wrong), classified by hand.
# status: open | free_web | closed ; url = where the legal free copy lives.
OVERRIDES = {
    # --- checked by hand (what was verified is in "verified") ---
    'oberbichler2025implementing': {'status': 'open', 'url': 'https://zenodo.org/records/14924737', 'license': 'cc-by-4.0', 'version': 'working paper', 'verified': 'Zenodo API: access_right open, licence CC BY 4.0'},
    'buolamwini2018gender': {'status': 'open', 'url': 'https://proceedings.mlr.press/v81/buolamwini18a.html', 'license': None, 'verified': 'page opens (HTTP 200); PMLR proceedings are free to read'},
    'dignazio2023feminism': {'status': 'open', 'url': 'https://data-feminism.mitpress.mit.edu/', 'license': None, 'verified': 'automated check blocked (HTTP 403); MIT Press publishes the book as an open-access web edition. Check once in a browser.'},
    'risam2022minimal': {'status': 'open', 'url': 'https://digitalhumanities.org/dhq/vol/16/2/000646/000646.html', 'license': None, 'verified': 'page opens (HTTP 200); DHQ is a free journal'},
    'dfg2023generative': {'status': 'free', 'url': None, 'verified': 'PDF opens (HTTP 200); official publication'},
    'eu2016dsgvo': {'status': 'free', 'url': None, 'multilingual': 'eurlex', 'verified': 'EUR-Lex answers (HTTP 202); official text'},
    'eu2024kiverordnung': {'status': 'free', 'url': None, 'multilingual': 'eurlex', 'verified': 'EUR-Lex answers (HTTP 202); official text'},
    'eucommission2026genai': {'status': 'free', 'url': None, 'verified': 'document opens (HTTP 200); official publication'},
    'icmje2026recommendations': {'status': 'free', 'url': None, 'verified': 'page opens (HTTP 200)'},
    'schweiz2020datenschutzgesetz': {'status': 'free', 'url': None, 'multilingual': 'fedlex', 'verified': 'Fedlex opens (HTTP 200); official text'},
    'edpb2026forschung': {'status': 'free', 'url': None, 'verified': 'NOT verified: the host did not resolve from the machine that ran the check. Official EDPB consultation page; open it once in a browser.'},
    'mattu2016machine': {'status': 'free', 'url': None, 'verified': 'article opens (HTTP 200)'},
    'karpathy2025deepdive': {'status': 'free', 'url': None, 'verified': 'video page opens (HTTP 200)'},
    'unibe2026kirichtlinien': {'status': 'free', 'url': None, 'verified': 'page opens (HTTP 200)'},
    'chicago2024manual': {'status': 'closed', 'kind': 'standard', 'free_alternative': 'https://www.chicagomanualofstyle.org/tools_citationguide.html', 'verified': 'Quick Guide (free) opens; the full manual is a paid product'},
    'buolamwini2023unmasking': {'status': 'closed', 'kind': 'book', 'verified': 'trade book; no open full text found'},
    'noble2018oppression': {'status': 'closed', 'kind': 'book', 'verified': 'OpenAlex and DOAB: no open full text found'},
    'oneil2016weapons': {'status': 'closed', 'kind': 'book', 'verified': 'trade book; no open full text found'},
    'russell2020ai': {'status': 'closed', 'kind': 'book', 'verified': 'textbook; no open full text found'},
    'zuboff2017surveillance': {'status': 'closed', 'kind': 'book', 'verified': 'trade book; no open full text found'},
    'milligan2019history': {'status': 'closed', 'kind': 'book', 'verified': 'OpenAlex and DOAB: no open full text found'},
}

def fetch():
    bib = parse_bib()
    old = json.loads(DATA.read_text()) if DATA.exists() else {}
    res = {}
    for key, f in bib.items():
        if key in OVERRIDES:
            res[key] = dict(OVERRIDES[key], source='manual'); continue
        doi = f.get('doi')
        if not doi:
            res[key] = old.get(key, {'status': 'unclassified', 'source': 'none'}); continue
        res[key] = dict(summarise(openalex(doi)), source='openalex', doi=doi)
        time.sleep(0.15)
    out = {'checked': datetime.date.today().isoformat(), 'entries': res}
    DATA.write_text(json.dumps(out, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')
    from collections import Counter
    print(Counter(v.get('status') for v in res.values()))


# ------------------------------------------------------------------ pages
EX = {  # key -> {lang: file stem}
    'workspace': dict(de='arbeitsbereich-einrichten', en='set-up-workspace', fr='preparer-espace-de-travail'),
    'kit': dict(de='startpaket-dodis-5020', en='starter-kit-dodis-5020', fr='kit-de-depart-dodis-5020'),
    'pe': dict(de='prompt-engineering', en='prompt-engineering', fr='prompt-engineering'),
    'lr': dict(de='literaturrecherche-sozialversicherung-ch', en='literature-research-social-security-ch', fr='recherche-bibliographique-securite-sociale-ch'),
    'rq': dict(de='formulieren-historische-forschungsfrage-schweiz-europarat', en='formulating-historical-research-question-switzerland-council-of-europe', fr='formuler-question-recherche-historique-suisse-conseil-europe'),
    'sc': dict(de='quellenkritik-bundesrat-europarat-1949', en='source-criticism-federal-council-council-of-europe-1949', fr='critique-sources-conseil-federal-conseil-europe-1949'),
    'ss': dict(de='quellensuche-vorort-europarat-1963', en='source-search-vorort-council-of-europe-1963', fr='recherche-sources-vorort-conseil-europe-1963'),
    'wr': dict(de='schreiben', en='writing', fr='ecriture'),
    'ci': dict(de='zitieren', en='citing', fr='citer'),
    'ph': dict(de='public-history', en='public-history', fr='public-history'),
}
PAGE = {'de': 'lesezugang.qmd', 'en': 'reading-access.qmd', 'fr': 'acces-aux-lectures.qmd'}
GERMAN_ONLY = {'fickers2020hermeneutik', 'dfg2023generative', 'unibe2026kirichtlinien', 'schweiz2020datenschutzgesetz'}

def access_class(v):
    st = v.get('status')
    if st in ('open', 'free', 'closed'):
        return st
    if st in ('closed', 'unknown', 'unclassified', None):
        return 'closed'
    if st == 'bronze':
        return 'free'
    return 'open' if v.get('license') else 'free'

def authors(f):
    raw = f.get('author') or f.get('editor') or ''
    if raw.startswith('{'):
        return tex(raw)
    names = [a.strip() for a in raw.split(' and ') if a.strip() and a.strip() != 'others']
    fam = [tex(n.split(',')[0]) for n in names]
    more = ' and others' in raw or len(fam) > 2
    return (', '.join(fam[:2]) + (' et al.' if more else '')) if fam else ''

def venue(f):
    for k in ('journal', 'booktitle', 'publisher', 'institution', 'organization', 'howpublished'):
        if f.get(k):
            return tex(f[k])
    return ''

def titles_of(lang):
    out = {}
    for k, m in EX.items():
        fp = ROOT / lang / 'exercises' / (m[lang] + '.qmd')
        t = re.search(r'^title:\s*["\']?(.*?)["\']?\s*$', fp.read_text(encoding='utf-8'), re.M)
        out[k] = (t.group(1) if t else m[lang], 'exercises/' + m[lang] + '.qmd')
    out['home'] = ({'de': 'Kursstart', 'en': 'Home', 'fr': 'Accueil'}[lang], 'index.qmd')
    out['glossary'] = ({'de': 'Glossar', 'en': 'Glossary', 'fr': 'Glossaire'}[lang], 'glossary.qmd')
    return out

def usage():
    """key -> (set of exercise keys, set of exercise keys where it is required reading), from the German files."""
    used, req = {}, {}
    for k, fn in (('home', 'index.qmd'), ('glossary', 'glossary.qmd')):
        txt = (ROOT / 'de' / fn).read_text(encoding='utf-8')
        for key in set(re.findall(r'@([A-Za-z]\w*(?:[:-]\w+)*)', txt)):
            used.setdefault(key, set()).add(k)
    for k, m in EX.items():
        txt = (ROOT / 'de' / 'exercises' / (m['de'] + '.qmd')).read_text(encoding='utf-8')
        for key in set(re.findall(r'@([A-Za-z]\w*(?:[:-]\w+)*)', txt)):
            used.setdefault(key, set()).add(k)
        for block in re.findall(r'title="Pflichtlektüre"\}\n(.*?)\n:::', txt, re.S):
            for key in set(re.findall(r'@([A-Za-z]\w*(?:[:-]\w+)*)', block)):
                req.setdefault(key, set()).add(k)
    return used, req

T = {
 'de': dict(
  title='Lesezugang: Literatur finden und beschaffen',
  desc='Welche Texte des Kurses frei lesbar sind, wo Sie sie finden und wie Sie die übrigen auf legalem Weg beschaffen.',
  intro='Diese Seite sagt Ihnen für jede Quelle der [Bibliographie](bibliography.qmd), ob Sie sie sofort lesen können und wie Sie an die übrigen kommen. **Alle Pflichtlektüren des Kurses sind frei zugänglich.** Die Quellen, die Sie nicht frei lesen können, sind Hintergrundliteratur: Der Kurs funktioniert auch ohne sie.',
  legend_h='So lesen Sie die Tabellen',
  legend=['**Offen:** frei lesbar mit offener Lizenz (zum Beispiel CC BY). Sie dürfen den Text speichern und, je nach Lizenz, weitergeben.',
          '**Frei lesbar:** kostenlos im Netz lesbar, aber nicht offen lizenziert (zum Beispiel amtliche Texte, Preprints, Zeitschriften mit kostenlosem Zugang). Der Zugang kann sich ändern. Speichern Sie Ihre Kopie für Ihre Arbeit und halten Sie das Zugriffsdatum fest.',
          '**Kein freier Zugang:** Sie brauchen eine Bibliothek, eine Fernleihe oder einen Kauf. Der Abschnitt «Wege zum Text» zeigt, wie.'],
  req='Pflichtlektüre', cols_open=('Quelle', 'Sprache', 'Zugang', 'Lizenz', 'Genutzt in'), cols_closed=('Quelle', 'Art', 'Wege zum Text', 'Genutzt in'),
  open_h='Sofort lesbar', closed_h='Kein freier Zugang: so kommen Sie an die Texte', ways_h='Wege zum Text',
  read='Lesen', doi='DOI', kind=dict(book='Buch', article='Aufsatz', standard='Handbuch'), kind_default='Aufsatz',
  lic_none='keine offene Lizenz', pre='Preprint', verified_no='Link noch nicht automatisch geprüft, bitte einmal im Browser öffnen.',
  lang_name=dict(de='Deutsch', en='Englisch', multi='mehrsprachig'),
  how_search='In Ihrer Bibliothek suchen', how_scholar='Frei lesbare Kopie suchen', how_alt='Kostenlose Alternative',
  ways=['**1. Prüfen, ob es doch eine freie Kopie gibt.** Autorinnen und Autoren legen Fassungen oft in Repositorien ab. Suchen Sie nach dem Titel bei [Google Scholar](https://scholar.google.com/), [CORE](https://core.ac.uk/) oder mit der Erweiterung [Unpaywall](https://unpaywall.org/). Bei Büchern hilft das [Directory of Open Access Books](https://www.doabooks.org/).',
        '**2. Über Ihre Bibliothek.** Suchen Sie den Titel in [swisscovery](https://swisscovery.slsp.ch/) (Schweizer Hochschulbibliotheken) oder im Katalog Ihrer Hochschule. Viele Zeitschriften und E-Books sind über Lizenzen Ihrer Hochschule freigeschaltet. Melden Sie sich dafür mit Ihrem Hochschulkonto an.',
        '**3. Fernleihe.** Besitzt Ihre Bibliothek den Titel nicht, bestellen Sie ihn per Fernleihe. Rechnen Sie mit mehreren Tagen. Beginnen Sie früh, besonders bei Büchern.',
        '**4. Die Autorin oder den Autor fragen.** Eine freundliche E-Mail mit der Bitte um eine Kopie für Studium oder Forschung führt oft zum Ziel. Ob eine Fassung weitergegeben werden darf, regelt der Verlag; die Datenbank [Sherpa Romeo](https://v2.sherpa.ac.uk/romeo/) zeigt die Regeln.',
        '**5. Für Forschende:** Fragen Sie Ihre Bibliothek nach Lizenzen und Konsortien, nach Zugang über Kooperationen und nach der Möglichkeit, Texte für Text- und Data-Mining zu nutzen. Planen Sie eine Open-Access-Veröffentlichung eigener Texte gleich mit ein.'],
  warn_h='Wenn Sie den Text nicht rechtzeitig bekommen',
  warn='Lassen Sie ein KI-System den Text nicht «zusammenfassen», den Sie nicht geöffnet haben. Erfundene Literaturangaben und Inhaltsangaben sind gut belegt ([Walters & Wilder 2023](https://doi.org/10.1038/s41598-023-41032-5)). Notieren Sie die Quelle im Rechercheprotokoll als **nicht gelesen**, und arbeiten Sie mit dem Abstract oder mit dem Text einer freien Alternative.',
  legal_h='Hinweis zu Schattenbibliotheken',
  legal='Der Kurs rät von Anna\'s Archive, Library Genesis und ähnlichen Plattformen ab (siehe den Hinweis auf der [Bibliographie](bibliography.qmd)). Die Wege oben sind legal und reichen für alle Quellen dieser Seite.',
  stand='Stand der Prüfung', stand_txt='Der Zugang wurde am {d} mit OpenAlex (für Quellen mit DOI) und von Hand (für die übrigen) geprüft. Zugänge ändern sich: Melden Sie einen toten Link über ein [Issue im Repository](https://github.com/maehr/critical-ai-literacy-for-historians/issues/new/choose).'),
 'en': dict(
  title='Reading access: finding and getting the literature',
  desc='Which texts of the course you can read freely, where to find them and how to get the others by legal means.',
  intro='For every source in the [bibliography](bibliography.qmd), this page tells you whether you can read it right away and how to get the others. **Every required reading of the course is freely available.** The sources you cannot read freely are background literature: the course works without them.',
  legend_h='How to read the tables',
  legend=['**Open:** free to read under an open licence (for example CC BY). You may keep the text and, depending on the licence, share it.',
          '**Free to read:** readable online at no cost, but not openly licensed (for example official texts, preprints, journals with free access). Access can change. Keep a copy for your work and note the access date.',
          '**No free access:** you need a library, an interlibrary loan or a purchase. The section "Ways to the text" shows how.'],
  req='required reading', cols_open=('Source', 'Language', 'Access', 'Licence', 'Used in'), cols_closed=('Source', 'Type', 'Ways to the text', 'Used in'),
  open_h='Readable right away', closed_h='No free access: how to get these texts', ways_h='Ways to the text',
  read='Read', doi='DOI', kind=dict(book='Book', article='Article', standard='Manual'), kind_default='Article',
  lic_none='no open licence', pre='preprint', verified_no='Link not yet checked automatically; please open it once in a browser.',
  lang_name=dict(de='German', en='English', multi='multilingual'),
  how_search='Search your library', how_scholar='Look for a free copy', how_alt='Free alternative',
  ways=['**1. Check whether a free copy exists after all.** Authors often deposit versions in repositories. Search the title in [Google Scholar](https://scholar.google.com/), [CORE](https://core.ac.uk/) or with the [Unpaywall](https://unpaywall.org/) extension. For books, the [Directory of Open Access Books](https://www.doabooks.org/) helps.',
        '**2. Through your library.** Search the title in [swisscovery](https://swisscovery.slsp.ch/) (Swiss university libraries) or in your university\'s catalogue. Many journals and e-books are unlocked by your university\'s licences. Log in with your university account.',
        '**3. Interlibrary loan.** If your library does not own the title, order it by interlibrary loan. Expect several days. Start early, especially for books.',
        '**4. Ask the author.** A polite email asking for a copy for study or research often works. The publisher decides whether a version may be shared; the [Sherpa Romeo](https://v2.sherpa.ac.uk/romeo/) database shows the rules.',
        '**5. For researchers:** ask your library about licences and consortia, access through collaborations, and the possibility of using texts for text and data mining. Plan open-access publication of your own texts from the start.'],
  warn_h='If you cannot get the text in time',
  warn='Do not let an AI system "summarise" a text you have not opened. Invented references and summaries are well documented ([Walters & Wilder 2023](https://doi.org/10.1038/s41598-023-41032-5)). Record the source in your search log as **not read**, and work with the abstract or with the text of a free alternative.',
  legal_h='A note on shadow libraries',
  legal='The course advises against Anna\'s Archive, Library Genesis and similar platforms (see the note on the [bibliography](bibliography.qmd) page). The routes above are legal and cover every source on this page.',
  stand='Status of the check', stand_txt='Access was checked on {d} with OpenAlex (for sources with a DOI) and by hand (for the others). Access changes: report a dead link through an [issue in the repository](https://github.com/maehr/critical-ai-literacy-for-historians/issues/new/choose).'),
 'fr': dict(
  title='Accès aux lectures : trouver et se procurer la littérature',
  desc='Quels textes du cours sont librement lisibles, où les trouver et comment obtenir les autres par des voies légales.',
  intro='Pour chaque source de la [bibliographie](bibliography.qmd), cette page indique si vous pouvez la lire tout de suite et comment obtenir les autres. **Toutes les lectures obligatoires du cours sont librement accessibles.** Les sources que vous ne pouvez pas lire librement sont de la littérature de fond: le cours fonctionne sans elles.',
  legend_h='Comment lire les tableaux',
  legend=['**Ouvert:** librement lisible sous licence ouverte (par exemple CC BY). Vous pouvez conserver le texte et, selon la licence, le partager.',
          '**Lisible gratuitement:** lisible en ligne sans frais, mais sans licence ouverte (par exemple textes officiels, prépublications, revues en accès gratuit). L\'accès peut changer. Conservez une copie pour votre travail et notez la date de consultation.',
          '**Pas d\'accès libre:** il faut une bibliothèque, un prêt entre bibliothèques ou un achat. La section «Voies d\'accès au texte» montre comment.'],
  req='lecture obligatoire', cols_open=('Source', 'Langue', 'Accès', 'Licence', 'Utilisé dans'), cols_closed=('Source', 'Type', 'Voies d\'accès', 'Utilisé dans'),
  open_h='Lisible tout de suite', closed_h='Pas d\'accès libre: comment obtenir ces textes', ways_h='Voies d\'accès au texte',
  read='Lire', doi='DOI', kind=dict(book='Livre', article='Article', standard='Manuel'), kind_default='Article',
  lic_none='sans licence ouverte', pre='prépublication', verified_no='Lien pas encore vérifié automatiquement; ouvrez-le une fois dans un navigateur.',
  lang_name=dict(de='allemand', en='anglais', multi='multilingue'),
  how_search='Chercher dans votre bibliothèque', how_scholar='Chercher une copie libre', how_alt='Alternative gratuite',
  ways=['**1. Vérifier s\'il existe quand même une copie libre.** Les auteurs déposent souvent des versions dans des dépôts. Cherchez le titre dans [Google Scholar](https://scholar.google.com/), [CORE](https://core.ac.uk/) ou avec l\'extension [Unpaywall](https://unpaywall.org/). Pour les livres, le [Directory of Open Access Books](https://www.doabooks.org/) aide.',
        '**2. Par votre bibliothèque.** Cherchez le titre dans [swisscovery](https://swisscovery.slsp.ch/) (bibliothèques universitaires suisses) ou dans le catalogue de votre université. Beaucoup de revues et de livres numériques sont accessibles grâce aux licences de votre université. Connectez-vous avec votre compte universitaire.',
        '**3. Prêt entre bibliothèques.** Si votre bibliothèque ne possède pas le titre, commandez-le par prêt entre bibliothèques. Comptez plusieurs jours. Commencez tôt, surtout pour les livres.',
        '**4. Demander à l\'auteur.** Un courriel poli demandant une copie pour l\'étude ou la recherche réussit souvent. L\'éditeur décide si une version peut être partagée; la base [Sherpa Romeo](https://v2.sherpa.ac.uk/romeo/) montre les règles.',
        '**5. Pour les chercheurs:** interrogez votre bibliothèque sur les licences et consortiums, l\'accès via des collaborations et la possibilité d\'utiliser les textes pour la fouille de textes et de données. Prévoyez dès le début la publication en libre accès de vos propres textes.'],
  warn_h='Si vous n\'obtenez pas le texte à temps',
  warn='Ne laissez pas un système d\'IA «résumer» un texte que vous n\'avez pas ouvert. Les références et résumés inventés sont bien documentés ([Walters & Wilder 2023](https://doi.org/10.1038/s41598-023-41032-5)). Notez la source dans votre journal de recherche comme **non lue**, et travaillez avec le résumé ou avec le texte d\'une alternative libre.',
  legal_h='Remarque sur les bibliothèques clandestines',
  legal='Le cours déconseille Anna\'s Archive, Library Genesis et les plateformes semblables (voir la remarque sur la page [Bibliographie](bibliography.qmd)). Les voies ci-dessus sont légales et couvrent toutes les sources de cette page.',
  stand='État de la vérification', stand_txt='L\'accès a été vérifié le {d} avec OpenAlex (pour les sources avec DOI) et à la main (pour les autres). Les accès changent: signalez un lien mort par une [issue dans le dépôt](https://github.com/maehr/critical-ai-literacy-for-historians/issues/new/choose).'),
}

def q(s):
    return urllib.parse.quote(s)

def localized(url, lang, kind):
    if kind == 'eurlex':
        return re.sub(r'/(deu|eng|fra)$', {'de': '/deu', 'en': '/eng', 'fr': '/fra'}[lang], url)
    if kind == 'fedlex':
        return re.sub(r'/(de|fr|it)$', {'de': '/de', 'en': '/de', 'fr': '/fr'}[lang], url)
    return url

def pages():
    bib, data = parse_bib(), json.loads(DATA.read_text())
    ent, checked = data['entries'], data['checked']
    used, req = usage()
    for lang in ('de', 'en', 'fr'):
        t, ex = T[lang], titles_of(lang)
        def cite(key):
            f = bib[key]
            a, y = authors(f), f.get('year', '')
            title = tex(f.get('title', '')).replace('|', '\\|')
            v = venue(f)
            head = f'{a} ({y})' if y else a
            return f'{head}: *{title}*' + (f'. {v}' if v else '')
        def usedin(key):
            order = list(EX) + ['home', 'glossary']
            ks = sorted(used.get(key, set()), key=order.index)
            return '<br>'.join(f'[{ex[k][0]}]({ex[k][1]})' + (f' ({t["req"]})' if k in req.get(key, set()) else '') for k in ks) or '–'
        def link(key, v):
            f = bib[key]
            url = v.get('url') or f.get('url')
            url = localized(url, lang, v.get('multilingual', '')) if url else None
            doi = v.get('doi') or f.get('doi')
            parts = []
            if url:
                parts.append(f'[{t["read"]}]({url})')
            if doi and not (url and doi in url):
                parts.append(f'[{t["doi"]}](https://doi.org/{doi})')
            return ' · '.join(parts) or '–'
        def lang_of(key, v):
            if v.get('multilingual'): return t['lang_name']['multi']
            return t['lang_name']['de' if key in GERMAN_ONLY else 'en']
        rows_open, rows_closed = [], []
        for key in sorted(bib, key=lambda k: (authors(bib[k]).lower(), bib[k].get('year', ''))):
            v = ent[key]; c = access_class(v)
            if c in ('open', 'free'):
                lic = (v.get('license') or '').upper().replace('-', ' ') if v.get('license') else t['lic_none']
                if v.get('license') is None and c == 'free' and v.get('version') == 'submittedVersion':
                    lic = t['pre']
                acc = link(key, v) + ('' if v.get('verified', '').startswith('NOT') is False else f' ⚠ {t["verified_no"]}')
                rows_open.append(f'| {cite(key)} | {lang_of(key, v)} | {acc} | {lic} | {usedin(key)} |')
            else:
                f = bib[key]; title = tex(f.get('title', ''))
                kind = t['kind'].get(v.get('kind') or ('book' if f['_type'] == 'book' else ''), t['kind_default'])
                ways = [f'[{t["how_search"]}](https://swisscovery.slsp.ch/discovery/search?query=any,contains,{q(title)}&vid=41SLSP_NETWORK:slsp_network)',
                        f'[{t["how_scholar"]}](https://scholar.google.com/scholar?q={q(title)})']
                if v.get('free_alternative'):
                    ways.insert(0, f'[{t["how_alt"]}]({v["free_alternative"]})')
                doi = v.get('doi') or f.get('doi')
                if doi:
                    ways.append(f'[{t["doi"]}](https://doi.org/{doi})')
                rows_closed.append(f'| {cite(key)} | {kind} | {" · ".join(ways)} | {usedin(key)} |')
        def table(cols, rows):
            widths = {5: '[36, 9, 15, 10, 30]', 4: '[36, 8, 36, 20]'}[len(cols)]
            return ('| ' + ' | '.join(cols) + ' |\n| ' + ' | '.join('---' for _ in cols) + ' |\n' + '\n'.join(rows)
                    + '\n\n: {tbl-colwidths="' + widths + '"}')
        md = f"""---
lang: {lang}
title: '{t["title"]}'
description: "{t["desc"]}"
date: '{checked}'
date-modified: '{checked}'
page-layout: full
draft: false
citation: false
---

<!-- GENERATED by scripts/reading_access.py from bibliography.bib and data/reading-access.json. Edit the script, not this file. -->

{t["intro"]}

## {t["legend_h"]}

""" + '\n'.join(f'- {x}' for x in t['legend']) + f"""

## {t["open_h"]}

{table(t["cols_open"], rows_open)}

## {t["closed_h"]}

{table(t["cols_closed"], rows_closed)}

## {t["ways_h"]}

""" + '\n\n'.join(t['ways']) + f"""

::: {{.callout-warning}}

## {t["warn_h"]}

{t["warn"]}
:::

::: {{.callout-note}}

## {t["legal_h"]}

{t["legal"]}
:::

## {t["stand"]}

{t["stand_txt"].format(d=checked)}
"""
        (ROOT / lang / PAGE[lang]).write_text(md, encoding='utf-8')
        print(lang, PAGE[lang], 'open/free:', len(rows_open), 'closed:', len(rows_closed))

if __name__ == '__main__':
    cmd = sys.argv[1] if len(sys.argv) > 1 else ''
    if cmd == 'fetch': fetch()
    elif cmd == 'pages': pages()
    else: print(__doc__)
