from pathlib import Path

source = Path('research/hcc_link_recovery_20261023/agent/retrieve.py').read_text(encoding='utf-8')
start = source.index('SOURCES = [')
end = source.index('\n\nfor name, url', start)
source = source[:start] + "SOURCES = [('elsevier_full', 'https://api.elsevier.com/content/article/PII:S258955592500103X?httpAccept=text/xml&view=FULL'), ('epmc_doi_core', 'https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=DOI:10.1016/j.jhepr.2025.101426&format=json&resultType=core')]" + source[end:]
exec(compile(source, '<source_retrieval_followup>', 'exec'))
