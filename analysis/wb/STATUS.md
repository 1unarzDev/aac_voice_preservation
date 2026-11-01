# W-B status (checkpoint)
Done: sample (data/specs/wb_sample.jsonl, src/wb_sample.py); POS-cap4 verified 0/160 mismatch;
panel p1/p2/p1g raw in annotation/wb_admissibility/raw (32+16 files); items data/items/wb.jsonl (src/wb_items.py, panel values);
requests runs/requests/wb1.jsonl (1812; base subset wb1_base.jsonl 1272 generated + judged).
Pending: restored-channel local generation (runs/wb1_gen.sh runs/requests/wb1.jsonl, waits on /tmp/aacv_gpu.lock; terra part cached).
Then: generate.py --requests runs/requests/wb1.jsonl --run-id wb1 (all cached, assembles) -> explode (+--by-input)
-> judge --items data/items/wb.jsonl --concurrency 8 -> attribute --fallback J1 (copy to scored_fallbackJ1.parquet) -> attribute (no fallback)
-> python src/wb_admissibility.py merge && audit -> python src/wb_report.py -> write analysis/wb/report.md.
- Watcher: runs/wb1_finish.sh (setsid) runs everything after GENDONE; ends with WBFINISHED in runs/wb1_attr.log.
- [ckpt 2] panel merged incl. strict p1g; annotation/wb_audit.json written; wb_report.py works on base data (A, B, strict sensitivity final;
  C waits for restored channel). wb1_gen.sh relaunched with setsid (waiting on GPU lock behind r2c1). After WBFINISHED: assemble
  analysis/wb/report.md = narrative (analysis/wb/narrative.md) + report_tables.md.
- [ckpt 3] GPU lock held by r2c1 during its terra API wait (~90 min more at 22:5x). Interim run wb1i (base + terra restored) via runs/wb1i_run.sh -> analysis/wb/report_wb1i.md. Final wb1 auto via wb1_finish.sh watcher.
- [ckpt 4] analysis/wb/report.md currently = interim wb1i (narrative.md + tables). When wb1_finish.sh completes (WBFINISHED in runs/wb1_attr.log)
  it rewrites analysis/wb/report.md from wb1 (4-model restored); then update the C paragraph in narrative.md and rerun `python src/wb_report.py`.
- [ckpt 5] DONE: wb1 complete (1836 rows); report.md regenerated from wb1 with final narrative.

- [ckpt 6, 2026-11-01] Cycle-2 Action 1 complete: all 139 restoration inputs / 556 stored outputs audited in `contract_audit.md`; original source tables retained, actual-input fidelity and aligned/expressible sensitivities separate. Seven definite chip/source conflicts; two word cases unknown, nine unclear references and five source-consensus fallbacks withheld from aligned sensitivity. W-B remains machine-assessed; 20-message human audit still unreturned. No new generation/judging; no request rebuild. Hashed post-hoc evidence snapshot: `contract_audit_evidence_manifest.json`.
