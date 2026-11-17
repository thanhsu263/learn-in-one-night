#!/usr/bin/env python3
"""Sanity-check a generated study guide HTML.

Usage: python check_html.py <guide.html>

Checks: balanced tags, leftover {{placeholders}} / TEMPLATE comments, quiz toggle present,
nav links point at existing chapter ids, and per-chapter counts of term rows, key boxes and
trap boxes (flags chapters that are empty or likely bloated). Exit code 1 on errors.
"""
import re
import sys
from html.parser import HTMLParser

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}


class Balance(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.errors = [], []

    def handle_starttag(self, tag, attrs):
        if tag not in VOID:
            self.stack.append((tag, self.getpos()[0]))

    def handle_endtag(self, tag):
        if tag in VOID:
            return
        if self.stack and self.stack[-1][0] == tag:
            self.stack.pop()
            return
        # implicit closes (li/td/tr/p) are legal HTML; tolerate them
        for i in range(len(self.stack) - 1, -1, -1):
            if self.stack[i][0] == tag:
                dropped = [t for t, _ in self.stack[i + 1:] if t not in {"li", "td", "th", "tr", "p"}]
                if dropped:
                    self.errors.append(f"line {self.getpos()[0]}: </{tag}> closes unclosed {dropped}")
                del self.stack[i:]
                return
        self.errors.append(f"line {self.getpos()[0]}: stray </{tag}>")


def main():
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    path = sys.argv[1]
    s = open(path, encoding="utf-8").read()
    errors, warns = [], []

    p = Balance()
    p.feed(s)
    errors += p.errors
    left = [t for t, _ in p.stack if t not in {"li", "td", "th", "tr", "p"}]
    if left:
        errors.append(f"unclosed at end: {left}")

    ph = sorted(set(re.findall(r"\{\{[^}]+\}\}", s)))
    if ph:
        errors.append(f"leftover placeholders: {ph[:10]}")
    if "TEMPLATE" in s:
        warns.append("TEMPLATE comments still present")
    if 'id="quiz"' not in s or "body.quiz" not in s:
        errors.append("self-quiz toggle missing")

    ids = set(re.findall(r'\bid="([^"]+)"', s))
    for href in re.findall(r'href="#([^"]+)"', s):
        if href not in ids:
            errors.append(f"nav link #{href} has no matching id")

    sections = re.split(r'(?=<section class="ch")', s)[1:]
    print(f"{'chapter':<10}{'terms':>7}{'key':>5}{'traps':>7}{'formula':>9}  title")
    for sec in sections:
        cid = (re.search(r'id="([^"]+)"', sec) or [None, "?"])[1]
        title = re.sub(r"<[^>]+>", "", (re.search(r"<h2>(.*?)</h2>", sec, re.S) or [None, ""])[1]).strip()
        tables = re.findall(r'<table class="t">.*?</table>', sec, re.S)
        terms = sum(max(0, len(re.findall(r"<tr>", t)) - 1) for t in tables)
        key = sec.count('class="key"')
        traps = len(re.findall(r"<li>", "".join(re.findall(r'class="trap".*?</div>', sec, re.S))))
        f = sec.count('class="f"')
        print(f"{cid:<10}{terms:>7}{key:>5}{traps:>7}{f:>9}  {title[:60]}")
        if cid != "cf":
            if key == 0:
                warns.append(f"{cid}: no 'Nhớ trong 30 giây' key box")
            if traps == 0:
                warns.append(f"{cid}: no exam traps")
            if terms > 60:
                warns.append(f"{cid}: {terms} term rows - probably too long; cut what the exam doesn't test")

    for w in warns:
        print("WARN:", w)
    for e in errors:
        print("ERROR:", e)
    print("OK" if not errors else f"{len(errors)} error(s)")
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
