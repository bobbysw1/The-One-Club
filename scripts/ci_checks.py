#!/usr/bin/env python3
"""Repo-wide sanity checks, run in CI on every push and runnable locally.

Exists because this repo has been broken in production multiple times by
things a five-second automated check would have caught: a syntax error in
api/chat.js that 500'd every chat request, a merge that silently dropped a
`(function(){` opener in assets/lead-form.js, and a live Google Maps API
key committed in plain text across 28 pages. None of these needed a human
to catch, they needed a script that runs before the push, not after a user
reports it.

Checks:
  1. Every .js file parses (node --check)
  2. Every .json file is valid JSON
  3. Every inline <script> block in every .html file parses as JS
     (excluding <script type="application/ld+json">)
  4. Every <script type="application/ld+json"> block is valid JSON
  5. <div>/</div> and <script>/</script> tags are balanced per file
  6. No obvious secret patterns (API keys, tokens) in tracked files

Usage: python3 scripts/ci_checks.py
Exit code 0 = all clean, 1 = at least one failure (details printed).
"""
import json
import os
import re
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SKIP_DIRS = {'.git', '.claude', 'node_modules', '__pycache__'}

SECRET_PATTERNS = [
    (re.compile(r'AIza[0-9A-Za-z_\-]{35}'), 'Google API key'),
    (re.compile(r'sk-[a-zA-Z0-9]{20,}'), 'OpenAI-style secret key'),
    (re.compile(r'github_pat_[a-zA-Z0-9_]{20,}'), 'GitHub fine-grained PAT'),
    (re.compile(r'ghp_[a-zA-Z0-9]{30,}'), 'GitHub classic PAT'),
]

failures = []


def walk_files(exts):
    for dirpath, dirnames, filenames in os.walk(ROOT):
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for f in filenames:
            if f.endswith(exts):
                yield os.path.join(dirpath, f)


def rel(path):
    return os.path.relpath(path, ROOT)


def check_js_files():
    for path in walk_files(('.js',)):
        result = subprocess.run(['node', '--check', path], capture_output=True, text=True)
        if result.returncode != 0:
            failures.append(f"[JS SYNTAX] {rel(path)}\n{result.stderr.strip()}")


def check_json_files():
    for path in walk_files(('.json',)):
        try:
            with open(path, encoding='utf-8') as f:
                json.load(f)
        except Exception as e:
            failures.append(f"[JSON] {rel(path)}: {e}")


def check_html_files():
    ld_json_re = re.compile(r'<script type="application/ld\+json">(.*?)</script>', re.DOTALL)
    importmap_re = re.compile(r'<script type="importmap">(.*?)</script>', re.DOTALL)
    module_script_re = re.compile(r'<script type="module"(?:\s[^>]*)?>(.*?)</script>', re.DOTALL)
    # "Plain" scripts: excludes ld+json, importmap, and module (each checked separately above/below)
    plain_script_re = re.compile(
        r'<script(?![^>]*(?:application/ld\+json|type="importmap"|type="module"))(?:\s[^>]*)?>(.*?)</script>',
        re.DOTALL
    )
    for path in walk_files(('.html',)):
        with open(path, encoding='utf-8') as f:
            content = f.read()

        div_open = len(re.findall(r'<div\b', content))
        div_close = len(re.findall(r'</div>', content))
        if div_open != div_close:
            failures.append(f"[DIV BALANCE] {rel(path)}: {div_open} open vs {div_close} close")

        script_open = len(re.findall(r'<script\b', content))
        script_close = len(re.findall(r'</script>', content))
        if script_open != script_close:
            failures.append(f"[SCRIPT BALANCE] {rel(path)}: {script_open} open vs {script_close} close")

        for m in ld_json_re.finditer(content):
            try:
                json.loads(m.group(1))
            except Exception as e:
                failures.append(f"[JSON-LD] {rel(path)}: {e}")

        for m in importmap_re.finditer(content):
            try:
                json.loads(m.group(1))
            except Exception as e:
                failures.append(f"[IMPORTMAP] {rel(path)}: {e}")

        for m in plain_script_re.finditer(content):
            body = m.group(1).strip()
            if not body:
                continue
            with tempfile.NamedTemporaryFile(mode='w', suffix='.js', delete=False) as tmp:
                tmp.write(body)
                tmp_path = tmp.name
            result = subprocess.run(['node', '--check', tmp_path], capture_output=True, text=True)
            os.unlink(tmp_path)
            if result.returncode != 0:
                failures.append(f"[INLINE JS] {rel(path)}\n{result.stderr.strip()[:300]}")

        for m in module_script_re.finditer(content):
            body = m.group(1).strip()
            if not body:
                continue
            with tempfile.NamedTemporaryFile(mode='w', suffix='.mjs', delete=False) as tmp:
                tmp.write(body)
                tmp_path = tmp.name
            result = subprocess.run(['node', '--check', tmp_path], capture_output=True, text=True)
            os.unlink(tmp_path)
            if result.returncode != 0:
                failures.append(f"[INLINE MODULE JS] {rel(path)}\n{result.stderr.strip()[:300]}")


def check_secrets():
    for path in walk_files(('.html', '.js', '.py', '.json', '.md', '.yml', '.yaml')):
        try:
            with open(path, encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception:
            continue
        for pattern, label in SECRET_PATTERNS:
            for m in pattern.finditer(content):
                failures.append(f"[SECRET] {rel(path)}: possible {label} ({m.group(0)[:12]}...)")


def main():
    check_js_files()
    check_json_files()
    check_html_files()
    check_secrets()

    if failures:
        print(f"\n{len(failures)} check(s) failed:\n")
        for f in failures:
            print(f"  {f}\n")
        sys.exit(1)

    print("All checks passed.")
    sys.exit(0)


if __name__ == '__main__':
    main()
