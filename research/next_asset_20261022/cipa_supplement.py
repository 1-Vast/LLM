"""Acquire author-linked supplement for intervention metadata, not response fitting."""
from cipa_assets import get
from discover import OUT
import json

if __name__=='__main__':
    response=get('cipa_supplement_tables','https://pmc.ncbi.nlm.nih.gov/articles/instance/6226030/bin/NIHMS1508943-supplement-Supplemental_Figures_and_Tables.pdf')
    print(json.dumps({'genuine_pdf':response.content.startswith(b'%PDF-')}))
