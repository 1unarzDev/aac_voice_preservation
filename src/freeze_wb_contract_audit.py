"""Create/verify a self-contained post-hoc W-B Action-1 evidence snapshot.

Creation refuses to replace prior evidence. Verification checks the archive, not
the changing live workspace; the artifact's original input hashes are checked
against live inputs at creation. This is never a prospective freeze claim.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import tarfile

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'analysis/wb'
ARCHIVE = OUT / 'contract_audit_evidence_20261101.tar.gz'
MANIFEST = OUT / 'contract_audit_evidence_manifest.json'


def digest(data):
    return hashlib.sha256(data).hexdigest()


def verify():
    manifest=json.loads(MANIFEST.read_text())
    assert digest(ARCHIVE.read_bytes()) == manifest['archive_sha256']
    expected={r['path']:r for r in manifest['files']}
    with tarfile.open(ARCHIVE,'r:gz') as archive:
        assert set(archive.getnames()) == set(expected)
        for member in archive.getmembers():
            assert member.isfile() and not Path(member.name).is_absolute() and '..' not in Path(member.name).parts
            data=archive.extractfile(member).read()
            assert digest(data) == expected[member.name]['sha256'], member.name
            assert len(data) == expected[member.name]['size_bytes'], member.name
    print(f"Verified archive SHA-256 and {len(expected)} member hashes: {ARCHIVE.relative_to(ROOT)}")


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--verify',action='store_true')
    args=ap.parse_args()
    if args.verify:
        verify();return
    if ARCHIVE.exists() or MANIFEST.exists():
        raise FileExistsError('Refusing to overwrite a historical evidence snapshot')
    audit=json.loads((OUT/'contract_audit.json').read_text())
    for name,expected in audit['input_hashes'].items():
        assert digest((ROOT/name).read_bytes()) == expected, f'input changed since analysis: {name}'
    # Confirm byte preservation of the original statistical tables.
    history=OUT/'contract_audit_history_20261101.tar.gz'
    with tarfile.open(history,'r:gz') as old:
        for name in ['analysis/wb/report_tables.md','analysis/wb/estimates.csv','analysis/wb/long_dims.csv.gz']:
            assert old.extractfile(name).read() == (ROOT/name).read_bytes(), name
    names=set(audit['input_hashes'])
    names.update(['analysis/derived/r2_hyp_checks.json',
                  'analysis/derived/r2_hyp_examples.json','analysis/derived/r2_mine_hyp.py',
                  'paper/figs/CAPTIONS.md','src/refresh_captions.py',
                  'src/wb_contract_audit_report.py','src/freeze_wb_contract_audit.py',
                  'src/attribute.py','src/judge.py','src/build_requests.py','annotation/CB_rules.md',
                  'annotation/wb_admissibility/agreement.json', 'analysis/oracle/human_gate.log',
                  'prompts/P0.txt','runs/requests/wb1.jsonl'])
    names.update(str(p.relative_to(ROOT)) for p in (ROOT/'runs/wb1').iterdir() if p.is_file())
    names.update(str(p.relative_to(ROOT)) for p in OUT.iterdir()
                 if p.is_file() and not p.name.startswith('contract_audit_evidence'))
    command='.venv/bin/python src/wb_contract_audit.py'
    produced={f'analysis/wb/{name}':command for name in ['contract_audit.json','contract_audit_inventory.csv',
               'contract_audit_diff.csv','contract_audit_estimates.csv','contract_audit_run.log']}
    produced['analysis/wb/contract_audit.md']='.venv/bin/python src/wb_contract_audit_report.py'
    produced['analysis/wb/contract_audit_report_run.log']='.venv/bin/python src/wb_contract_audit_report.py'
    blobs={};entries=[]
    for name in sorted(names):
        path=ROOT/name
        before=path.stat();data=path.read_bytes();after=path.stat()
        assert (before.st_size,before.st_mtime_ns)==(after.st_size,after.st_mtime_ns),name
        blobs[name]=data
        entries.append(dict(path=name,sha256=digest(data),size_bytes=len(data),
                            mtime_ns=before.st_mtime_ns,producing_command=produced.get(name)))
    with ARCHIVE.open('xb') as stream:
        with tarfile.open(fileobj=stream,mode='w:gz') as archive:
            for name,data in blobs.items():
                member=tarfile.TarInfo(name);member.size=len(data);member.mtime=0;member.mode=0o644
                archive.addfile(member,io.BytesIO(data))
    manifest=dict(schema_version=1,created_at=datetime.now(timezone.utc).isoformat(),
                  kind='post-hoc evidence snapshot; not prospective item/codebook freeze',
                  action='W-B restoration contract audit',
                  archive=str(ARCHIVE.relative_to(ROOT)),archive_sha256=digest(ARCHIVE.read_bytes()),
                  creation_command='.venv/bin/python src/freeze_wb_contract_audit.py',
                  verification_command='.venv/bin/python src/freeze_wb_contract_audit.py --verify',
                  provenance_note='null producing_command: input, historical command not independently recorded, or editorial update; no model calls',
                  generator_calls=0,judge_calls=0,files=entries)
    with MANIFEST.open('x') as stream:
        stream.write(json.dumps(manifest,indent=2)+'\n')
    verify()


if __name__=='__main__':
    main()
