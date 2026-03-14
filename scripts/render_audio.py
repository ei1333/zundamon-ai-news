#!/usr/bin/env python3
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Render episode audio from scripts_text parts via VOICEVOX helper.')
    parser.add_argument('date', help='Episode date in YYYY-MM-DD format')
    parser.add_argument('speaker', nargs='?', default='zundamon', help='Speaker name')
    return parser.parse_args()


def chunk_manifest(parts: list[dict[str, str]], max_chars: int = 110) -> tuple[list[dict[str, object]], list[str]]:
    manifest: list[dict[str, object]] = []
    warnings: list[str] = []
    seq = 0
    for part in parts:
        part_id = part['id']
        text = ' '.join(part['text'].split())
        if len(text) > max_chars:
            warnings.append(f'WARN: {part_id} is {len(text)} chars; chunking within the part')
        buf = ''
        chunk_index = 0
        tokens = text.replace('。', '。\n').replace('、', '、\n').splitlines()
        for token in (token.strip() for token in tokens):
            if not token:
                continue
            if len(buf) + len(token) <= max_chars:
                buf += token
            else:
                if buf:
                    seq += 1
                    chunk_index += 1
                    manifest.append({'seq': seq, 'part_id': part_id, 'chunk_index': chunk_index, 'text': buf})
                buf = token
        if buf:
            seq += 1
            chunk_index += 1
            manifest.append({'seq': seq, 'part_id': part_id, 'chunk_index': chunk_index, 'text': buf})
    return manifest, warnings


def synthesize_chunks(manifest: list[dict[str, object]], *, tmp_dir: Path, speaker: str, tts_script: Path) -> None:
    for item in manifest:
        out_file = tmp_dir / f"{item['part_id']}-{item['chunk_index']:02d}.wav"
        subprocess.run([str(tts_script), speaker, str(item['text']), str(out_file)], check=True)


def concat_wavs(manifest: list[dict[str, object]], *, tmp_dir: Path, output_path: Path) -> None:
    parts = [tmp_dir / f"{item['part_id']}-{item['chunk_index']:02d}.wav" for item in manifest]
    if not parts:
        raise SystemExit('No synthesized chunks were created')
    with wave.open(str(parts[0]), 'rb') as first:
        params = first.getparams()
        frames = [first.readframes(first.getnframes())]
    for part in parts[1:]:
        with wave.open(str(part), 'rb') as w:
            if w.getparams()[:3] != params[:3]:
                raise SystemExit(f'Incompatible wav params: {part}')
            frames.append(w.readframes(w.getnframes()))
    with wave.open(str(output_path), 'wb') as out:
        out.setparams(params)
        for frame in frames:
            out.writeframes(frame)


def main() -> None:
    args = parse_args()
    if not re.fullmatch(r'\d{4}-\d{2}-\d{2}', args.date):
        raise SystemExit(f'Invalid date format: {args.date}\nExpected YYYY-MM-DD')

    script_text = ROOT / 'scripts_text' / f'{args.date}.txt'
    script_parts = ROOT / 'scripts_text' / f'{args.date}.parts.json'
    output = ROOT / 'assets' / 'audio' / f'sample-news-{args.date}.wav'
    tts_script = Path(os.environ.get('VOICEVOX_TTS_SCRIPT', str(Path.home() / '.openclaw' / 'workspace' / 'voicevox_tts.sh')))

    subprocess.run([sys.executable, str(ROOT / 'scripts' / 'render_episode.py'), args.date], check=True)

    if not script_text.exists():
        raise SystemExit(f'Script text not found: {script_text}')
    if not script_parts.exists():
        raise SystemExit(f'Script parts not found: {script_parts}')
    if not shutil.which(str(tts_script)) and not tts_script.exists():
        raise SystemExit(f'VOICEVOX helper is not executable or not found: {tts_script}')

    output.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        parts = json.loads(script_parts.read_text(encoding='utf-8'))
        manifest, warnings = chunk_manifest(parts)
        (tmp_dir / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        if warnings:
            print('\n'.join(warnings), file=sys.stderr)
        synthesize_chunks(manifest, tmp_dir=tmp_dir, speaker=args.speaker, tts_script=tts_script)
        concat_wavs(manifest, tmp_dir=tmp_dir, output_path=output)

    print(f'Rendered: assets/audio/sample-news-{args.date}.wav')


if __name__ == '__main__':
    main()
