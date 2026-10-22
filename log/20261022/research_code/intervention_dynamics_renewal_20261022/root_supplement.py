"""One PDF request, requiring actual PDF bytes; no automatic fallback."""
import subprocess

import root_search as scout


def main():
    url = 'https://pmc.ncbi.nlm.nih.gov/articles/instance/11264686/bin/msystems.00256-24-s0001.pdf'
    receipt, raw = scout.get('supplement', url)
    if receipt.get('status') != 200 or not raw.startswith(b'%PDF-') or 'error_type' in receipt:
        scout.write(scout.OUT/'SUPPLEMENT_STATUS.json', {'status': 'ACCESS_FAILED_OR_NOT_PDF',
                    'http_status': receipt.get('status'), 'pdf_magic': raw.startswith(b'%PDF-'),
                    'fallback_GETs': 0})
        print('SUPPLEMENT_ACCESS_FAILED_OR_NOT_PDF_RETAINED')
        return 1
    path = scout.OUT/'msystems.00256-24-s0001.pdf'
    with path.open('xb') as handle:
        handle.write(raw)
    completed = subprocess.run(['pdftotext', '-layout', str(path), str(scout.OUT/'SUPPLEMENT_TEXT.txt')],
                               capture_output=True, text=True, timeout=30)
    scout.write(scout.OUT/'SUPPLEMENT_STATUS.json', {'status': 'PDF_ACQUIRED',
                'bytes': len(raw), 'text_extraction_exit': completed.returncode,
                'source_sha256': receipt['sha256'], 'fallback_GETs': 0})
    print('PDF_ACQUIRED' if completed.returncode == 0 else 'PDF_ACQUIRED_TEXT_EXTRACTION_FAILED')
    return 0 if completed.returncode == 0 else 1


if __name__ == '__main__':
    raise SystemExit(main())
