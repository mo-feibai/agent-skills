#!/usr/bin/env python
"""Session token / cost report for an OpenCode session, straight from its SQLite store.

Usage
  python session-cost.py                 # newest session
  python session-cost.py <SESSION_ID>
  python session-cost.py --top 10        # rank sessions by prompt tokens
  python session-cost.py --prices 0.15 0.6 0.003   # in / out / cache-read per 1M

Output is ASCII on purpose: this machine's console is GBK and would mangle CJK.
Only reads the database (mode=ro); never writes.
"""
import collections
import json
import os
import sqlite3
import statistics
import sys

DB = os.path.join(os.environ.get('USERPROFILE', os.path.expanduser('~')),
                  '.local', 'share', 'opencode', 'opencode.db')
DB_URI = 'file:' + DB.replace('\\', '/') + '?mode=ro'


def connect():
    return sqlite3.connect(DB_URI, uri=True)


def load_steps(conn, sid):
    rows = conn.execute(
        "select p.data, m.data, m.id from part p join message m on m.id = p.message_id "
        "where p.session_id = ? order by m.time_created, p.time_created", (sid,)).fetchall()
    steps, cur = [], None
    for pd, md, mid in rows:
        msg = json.loads(md)
        if msg.get('role') != 'assistant':
            continue
        if cur is None or cur['id'] != mid:
            tok = msg.get('tokens') or {}
            cur = {'id': mid,
                   'prompt': tok.get('input', 0) + (tok.get('cache') or {}).get('read', 0),
                   'input': tok.get('input', 0),
                   'cache_read': (tok.get('cache') or {}).get('read', 0),
                   'cache_write': (tok.get('cache') or {}).get('write', 0),
                   'output': tok.get('output', 0) + tok.get('reasoning', 0),
                   'cost': msg.get('cost', 0.0),
                   'added': 0, 'tools': []}
            steps.append(cur)
        part = json.loads(pd)
        kind = part.get('type')
        if kind == 'text':
            cur['added'] += len(part.get('text') or '')
        elif kind == 'tool':
            state = part.get('state') or {}
            out = str(state.get('output') or '')
            inp = json.dumps(state.get('input') or {}, ensure_ascii=False)
            cur['added'] += len(out) + len(inp)
            args = state.get('input') or {}
            target = str(args.get('filePath') or args.get('path') or args.get('pattern')
                         or args.get('command') or args.get('url') or '')
            cur['tools'].append((part.get('tool'), len(out), target))
    return steps


def chars_per_token(steps):
    ratios = []
    for a, b in zip(steps, steps[1:]):
        delta = b['prompt'] - a['prompt']
        if a['added'] > 2000 and delta > 0:
            ratios.append(delta / a['added'])
    return statistics.median(ratios) if ratios else 0.3


def report(conn, sid, prices):
    steps = load_steps(conn, sid)
    if not steps:
        print('no assistant steps for %s' % sid)
        return
    pin, pout, pcache = prices
    prompt = sum(s['prompt'] for s in steps)
    new_tok = sum(s['input'] for s in steps)
    cached = sum(s['cache_read'] for s in steps)
    written = sum(s['cache_write'] for s in steps)
    out_tok = sum(s['output'] for s in steps)
    paid = sum(s['cost'] for s in steps)
    if paid == 0:
        paid = (new_tok * pin + cached * pcache + written * pin * 1.25 + out_tok * pout) / 1e6
    nocache = (prompt * pin + out_tok * pout) / 1e6
    r = chars_per_token(steps)

    print('session   %s' % sid)
    print('steps     %d' % len(steps))
    print('prompt    %d tokens (avg %d/step)' % (prompt, prompt // len(steps)))
    print('cache hit %.1f%%   new %d   cached %d' % (100.0 * cached / max(prompt, 1), new_tok, cached))
    print('output    %d tokens (incl. reasoning)' % out_tok)
    print('paid      $%.4f' % paid)
    print('no-cache  $%.2f   saved $%.2f (%.1f%%)'
          % (nocache, nocache - paid, 100.0 * (nocache - paid) / max(nocache, 1e-9)))
    print('')
    flat = sorted(((t[1], i, t[0], t[2]) for i, s in enumerate(steps) for t in s['tools'] if t[1] > 2000),
                  reverse=True)
    print('largest tool outputs (share is an upper bound: assumes the output stayed to the end)')
    for chars, idx, tool, target in flat[:5]:
        tok = chars * r
        contrib = tok * (len(steps) - idx - 1)
        print('  step %-5d %-12s %7d chars ~%6d tok  %5.1f%% of prompt  %s'
              % (idx + 1, tool, chars, tok, 100.0 * contrib / max(prompt, 1), target[:56]))


def top(conn, n):
    rows = conn.execute("select session_id, data from message").fetchall()
    agg = collections.defaultdict(lambda: [0, 0])
    for sid, data in rows:
        msg = json.loads(data)
        if msg.get('role') != 'assistant':
            continue
        tok = msg.get('tokens') or {}
        agg[sid][0] += 1
        agg[sid][1] += tok.get('input', 0) + (tok.get('cache') or {}).get('read', 0)
    ranked = sorted(agg.items(), key=lambda kv: kv[1][1], reverse=True)[:n]
    print('%-34s %7s %14s' % ('session', 'steps', 'prompt tokens'))
    for sid, (steps, prompt) in ranked:
        print('%-34s %7d %14d' % (sid, steps, prompt))


def main():
    args = sys.argv[1:]
    prices = (0.15, 0.6, 0.003)
    if '--prices' in args:
        i = args.index('--prices')
        prices = tuple(float(x) for x in args[i + 1:i + 4])
        args = args[:i] + args[i + 4:]
    conn = connect()
    if '--top' in args:
        i = args.index('--top')
        n = int(args[i + 1]) if len(args) > i + 1 else 10
        top(conn, n)
        return
    if args:
        sid = args[0]
    else:
        sid = conn.execute("select session_id from part order by time_created desc limit 1").fetchone()[0]
    report(conn, sid, prices)


if __name__ == '__main__':
    main()
