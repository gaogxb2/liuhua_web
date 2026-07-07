#!/usr/bin/env python3
"""按单板记录改写 txt 内 code，使柱状图 0x00-0x3f 近似正态分布。"""
import re
import shutil
import sys
from collections import Counter
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data_processor import DataProcessor  # noqa: E402

CLOCK_RE = re.compile(
    r'display clock \| no-more\s*\r?\n(.*?)\r?\n</Message>',
    re.DOTALL | re.IGNORECASE,
)
DATE_RE = re.compile(r'(\d{4}-\d{2}-\d{2})')
R024_RE = re.compile(r'software\s+(R024)', re.IGNORECASE)
CODE_UP_RE = re.compile(r'(code-up:)(0x[0-9A-Fa-f]+)', re.IGNORECASE)
DS_TX_RE = re.compile(
    r'(DS_TX:\s*(?:[A-Za-z0-9xX]+\s*,\s*){26})([A-Za-z0-9xX]+)',
    re.IGNORECASE,
)


def is_r024(content: str) -> bool:
    return bool(R024_RE.search(content))


def rewrite_all_codes(content: str, targets: list[int], r024: bool) -> str:
    """第一个 lane 用 targets[0]（单板代表 code），其余 lane 用 0x3F 保证 min=targets[0]"""
    idx = {'i': 0}

    def next_target() -> int:
        i = idx['i']
        idx['i'] += 1
        if i < len(targets):
            return targets[i]
        return 63

    if r024:
        def repl(m):
            val = next_target()
            return m.group(1) + f'0x{val:02X}'
        return CODE_UP_RE.sub(repl, content)

    def repl(m):
        val = next_target()
        return m.group(1) + f'0x{val:X}'
    return DS_TX_RE.sub(repl, content)


def resolve_log_path(logs_dir: Path, rel: str) -> Path:
    p = Path(rel)
    if p.is_absolute():
        return p
    return logs_dir / rel


def main():
    logs_dir = ROOT / 'logs'
    backup = ROOT / 'logs_backup'
    if not backup.exists():
        print(f'备份 logs -> {backup}')
        shutil.copytree(logs_dir, backup)
    else:
        print(f'从 {backup} 恢复原始 logs 后重新改写')
        shutil.rmtree(logs_dir)
        shutil.copytree(backup, logs_dir)

    processor = DataProcessor()
    df = processor.analyze_folder(str(logs_dir), extract_zip=False)
    recs = processor.build_board_records(df)
    if not recs:
        print('无单板记录，退出')
        return

    rng = np.random.default_rng(42)
    n = len(recs)
    # loc=31.5 居中 0x00-0x3f，scale=13 使样本覆盖全段
    targets = np.clip(np.round(rng.normal(loc=31.5, scale=13, size=n)), 0, 63).astype(int)

    path_to_target: dict[str, int] = {}
    for rec, primary in zip(recs, targets):
        rel = str(rec.get('文件路径', '') or '')
        if rel:
            path_to_target[rel] = int(primary)

    print(f'共 {n} 块单板，改写 {len(path_to_target)} 个 txt')
    print(f'目标 code 范围: {targets.min()}-{targets.max()}')

    for rel, primary in sorted(path_to_target.items()):
        fp = resolve_log_path(logs_dir, rel)
        if not fp.exists():
            print(f'  跳过不存在: {rel}')
            continue
        text = fp.read_text(encoding='utf-8', errors='ignore')
        r024 = is_r024(text)
        count = len(CODE_UP_RE.findall(text)) if r024 else len(DS_TX_RE.findall(text))
        count = max(count, 1)
        lane_targets = [primary] + [63] * (count - 1)
        new_text = rewrite_all_codes(text, lane_targets, r024)
        if new_text != text:
            fp.write_text(new_text, encoding='utf-8')

    processor2 = DataProcessor()
    df2 = processor2.analyze_folder(str(logs_dir), extract_zip=False)
    recs2 = processor2.build_board_records(df2)
    dist: Counter[int] = Counter()
    fault = 0
    for r in recs2:
        codes = r.get('codes', [])
        if codes:
            m = min(codes)
            dist[m] += 1
            if m < DataProcessor.FAULT_CODE_THRESHOLD:
                fault += 1
    print(f'改写后: 单板 {len(recs2)}, 硫化 {fault}, code 范围 {min(dist.keys())}-{max(dist.keys())}')
    print('柱状图分布(0x00-0x3f, 每板最小code):', dict(sorted(dist.items())))


if __name__ == '__main__':
    main()
