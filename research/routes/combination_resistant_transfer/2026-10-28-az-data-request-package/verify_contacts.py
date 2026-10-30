# R204-DATA6 contact verification (read-only public pages/APIs; NO emails/forms sent).
# Saves raw receipts to ../receipts/ and prints structured findings.
import json, os, re, hashlib, urllib.request, urllib.parse, urllib.error

BASE = r'D:\MAESTRO\research\2026-10-28-az-data-request-package'
REC = os.path.join(BASE, 'receipts')
os.makedirs(REC, exist_ok=True)
UA = {"User-Agent": "MAESTRO-R204-DATA6/1.0 (academic metadata verification; no automated sending)"}

findings = []

def fetch(url, timeout=45, accept=None):
    h = dict(UA)
    if accept:
        h['Accept'] = accept
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        data = r.read()
        return {'url': url, 'status': getattr(r, 'status', 200), 'content_type': r.headers.get('Content-Type'),
                'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest(), 'data': data,
                'final_url': r.geturl()}

def save(name, raw, suffix='txt'):
    p = os.path.join(REC, f'{name}.{suffix}')
    mode = 'wb' if isinstance(raw, bytes) else 'w'
    if isinstance(raw, bytes):
        open(p, 'wb').write(raw)
    else:
        open(p, 'w', encoding='utf-8').write(raw)
    return p

EMAIL = re.compile(r'[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}')
CONTACT_KEYS = ['corresponding author', 'correspondence', 'contact', 'data availability', 'lead contact',
                'requests for data', 'data requests']

def emails_with_context(text, keys=CONTACT_KEYS, window=160):
    out = []
    low = text.lower()
    for m in EMAIL.finditer(text):
        s = max(0, m.start() - window); e = min(len(text), m.end() + window)
        ctx = text[s:e].replace('\n', ' ')
        nearby = [k for k in keys if k in low[max(0, m.start()-400):m.start()]]
        out.append({'email': m.group(0), 'context': ctx, 'nearby_terms': nearby})
    return out

# ---------- 1) Europe PMC: paper metadata + full text ----------
print('== Europe PMC paper metadata ==')
epmc_ok = False
try:
    url = ('https://www.ebi.ac.uk/europepmc/webservices/rest/search?'
           + urllib.parse.urlencode({'query': 'PMCID:PMC11061612', 'format': 'json', 'resultType': 'core'}))
    r = fetch(url); save('epmc_core_PMC11061612', r['data'], 'json')
    js = json.loads(r['data'])
    res = js['resultList']['result'][0]
    meta = {k: res.get(k) for k in ['id', 'pmid', 'pmcid', 'doi', 'title', 'authorString',
                                    'firstPublicationDate', 'journalTitle', 'pubYear', 'fullTextUrlList']}
    auth = res.get('authorList', {}).get('author', [])
    meta['authors'] = [{'fullName': a.get('fullName'), 'affiliation': a.get('affiliation'),
                        'firstName': a.get('firstName'), 'lastName': a.get('lastName')} for a in auth]
    findings.append({'item': 'epmc_core_meta', **meta, 'receipt': 'epmc_core_PMC11061612.json'})
    print('title:', meta['title'])
    print('doi:', meta['doi'], '| pmid:', meta['pmid'], '| journal:', meta['journalTitle'], meta['pubYear'])
    print('authors:', '; '.join([a['fullName'] or '' for a in meta['authors']])[:500])
    epmc_ok = True
except Exception as e:
    findings.append({'item': 'epmc_core_meta', 'error': repr(e)})
    print('ERROR', e)

if epmc_ok:
    print('\n== Europe PMC full text XML ==')
    try:
        url = 'https://www.ebi.ac.uk/europepmc/webservices/rest/PMC11061612/fullTextXML'
        r = fetch(url, accept='application/xml'); save('epmc_fulltext_PMC11061612', r['data'], 'xml')
        txt = r['data'].decode('utf-8', 'replace')
        ems = emails_with_context(txt)
        findings.append({'item': 'epmc_fulltext', 'url': url, 'bytes': r['bytes'], 'sha256': r['sha256'],
                         'emails': ems, 'receipt': 'epmc_fulltext_PMC11061612.xml'})
        print('bytes:', r['bytes'], '| emails found:', len(ems))
        for e in ems[:10]:
            print('  email:', e['email'], '| nearby:', e['nearby_terms'])
        # also look for 'Correspondence' text block
        idx = txt.lower().find('correspond')
        print('correspondence ctx:', txt[max(0, idx-100):idx+400].replace('\n', ' ')[:500] if idx >= 0 else 'NONE')
    except Exception as e:
        findings.append({'item': 'epmc_fulltext', 'error': repr(e)})
        print('ERROR', e)

# ---------- 2) Figshare project 163378 metadata + page ----------
print('\n== Figshare project 163378 ==')
try:
    url = 'https://api.figshare.com/v2/projects/163378/articles'
    r = fetch(url); save('figshare_project_163378_articles', r['data'], 'json')
    arts = json.loads(r['data'])
    arts_meta = []
    for a in arts[:12]:
        try:
            aurl = f"https://api.figshare.com/v2/articles/{a['id']}"
            ra = fetch(aurl); save(f"figshare_article_{a['id']}", ra['data'], 'json')
            ja = json.loads(ra['data'])
            arts_meta.append({'id': a['id'], 'title': ja.get('title'), 'doi': ja.get('doi'),
                              'url_public': ja.get('url_public_html') or ja.get('url_public_api'),
                              'authors': [x.get('full_name') for x in (ja.get('authors') or [])],
                              'emails_in_metadata': sorted(set(EMAIL.findall(json.dumps(ja)))),
                              'defined_type': ja.get('defined_type_name'), 'published_date': ja.get('published_date')})
        except Exception as e:
            arts_meta.append({'id': a['id'], 'error': repr(e)})
    findings.append({'item': 'figshare_project_meta', 'project_id': 163378, 'n_articles': len(arts),
                     'articles': arts_meta, 'receipt': 'figshare_project_163378_articles.json'})
    print('articles:', len(arts))
    for a in arts_meta[:4]:
        print('  ', a.get('id'), '|', (a.get('title') or '')[:80], '| authors:', a.get('authors'))
except Exception as e:
    findings.append({'item': 'figshare_project_meta', 'error': repr(e)})
    print('ERROR', e)

# Figshare public project page (may be SPA; record status/bytes and any emails)
for name, url in [('figshare_project_page', 'https://figshare.com/projects/AZ_GDSC_2024/163378'),
                  ('figshare_193440', 'https://figshare.com/')]:
    try:
        r = fetch(url); save(name, r['data'], 'html')
        txt = r['data'].decode('utf-8', 'replace')
        ems = emails_with_context(txt, keys=['contact', 'author'])
        findings.append({'item': name, 'url': url, 'status': r['status'], 'bytes': r['bytes'],
                         'emails': ems, 'receipt': name + '.html'})
        print(name, 'status', r['status'], 'bytes', r['bytes'], 'emails', len(ems))
    except Exception as e:
        findings.append({'item': name, 'url': url, 'error': repr(e)})
        print(name, 'ERROR', e)

# ---------- 3) GDSC / Wellcome Sanger public pages ----------
print('\n== GDSC / Wellcome Sanger pages ==')
pages = [
    ('gdsc_combinations_home', 'https://gdsc-combinations.depmap.sanger.ac.uk/'),
    ('gdsc_combinations_about', 'https://gdsc-combinations.depmap.sanger.ac.uk/about'),
    ('gdsc_cancerrxgene', 'https://www.cancerrxgene.org/'),
    ('sanger_contact', 'https://www.sanger.ac.uk/about/contact/'),
]
for name, url in pages:
    try:
        r = fetch(url); save(name, r['data'], 'html')
        txt = r['data'].decode('utf-8', 'replace')
        ems = emails_with_context(txt, keys=['contact', 'enquir', 'helpdesk', 'data access'])
        # also find mailto links
        mailtos = re.findall(r'mailto:([^"\'>\s]+)', txt)
        findings.append({'item': name, 'url': url, 'status': r['status'], 'bytes': r['bytes'],
                         'emails_on_page': sorted(set(e['email'] for e in ems)),
                         'mailto_links': sorted(set(mailtos)), 'receipt': name + '.html'})
        print(name, 'status', r['status'], 'bytes', r['bytes'], 'emails', sorted(set(e['email'] for e in ems))[:5],
              'mailto', sorted(set(mailtos))[:5])
    except Exception as e:
        findings.append({'item': name, 'url': url, 'error': repr(e)})
        print(name, 'ERROR', e)

# ---------- 4) publisher article page (AACR; likely blocked; record status only) ----------
print('\n== Publisher page (record status only) ==')
try:
    url = 'https://aacrjournals.org/cancerdiscovery/article/14/6/1014/744431'
    r = fetch(url, timeout=30); save('aacr_article_page', r['data'], 'html')
    txt = r['data'].decode('utf-8', 'replace')
    findings.append({'item': 'aacr_article_page', 'url': url, 'status': r['status'], 'bytes': r['bytes'],
                     'emails': emails_with_context(txt, keys=['correspond', 'contact']), 'receipt': 'aacr_article_page.html'})
    print('status', r['status'], 'bytes', r['bytes'])
except Exception as e:
    findings.append({'item': 'aacr_article_page', 'url': url, 'error': repr(e)})
    print('ERROR', e)

out = os.path.join(BASE, 'contacts_raw_findings.json')
open(out, 'w', encoding='utf-8').write(json.dumps(findings, ensure_ascii=False, indent=1))
print('\nWROTE', out)
