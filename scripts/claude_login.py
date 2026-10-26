#!/usr/bin/env python3
"""Connect the Claude Pro plan for the WhatsApp update job, with the official `claude setup-token`.

Run by .github/workflows/whatsapp-update.yml (kind=login), so an admin can log in from the admin team's WhatsApp group:
1. Starts `claude setup-token` in a terminal and waits for its sign-in link.
2. Puts the link on the incoming branch (login/<REF>.txt); the bot posts it in the group.
3. Waits up to 15 minutes for the code the admin copies after signing in. The bot sends it as the name of a
   "Claude login code" run (.github/workflows/claude-login-code.yml); the code works once, and only for this
   sign-in, so that run is deleted as soon as the code is read.
4. Types the code in and saves the year-long token as the CLAUDE_CODE_OAUTH_TOKEN secret. The token is never printed.
Writes /tmp/login.json: {"status": "done"} or {"status": "failed", "summary": "..."}.
Environment: GITHUB_REPOSITORY, REF, GH_TOKEN (this run's token), SECRETS_TOKEN (may set repository secrets).
"""
import base64
import fcntl
import json
import os
import pty
import re
import select
import struct
import subprocess
import sys
import termios
import time

REPO, REF = os.environ.get('GITHUB_REPOSITORY', ''), os.environ.get('REF', '')
WAIT_FOR_CODE = 15 * 60
ANSI = re.compile(r'\x1b\][^\x07\x1b]*(\x07|\x1b\\)|\x1b\[[0-9;?]*[ -/]*[@-~]|\x1b[()][0-9A-Za-z]|\x1b[=>]')
TOKEN = re.compile(r'sk-ant-oat01-[A-Za-z0-9_-]{20,}')
URL = re.compile(r'https://\S*(?:oauth|authorize)\S*')


def finish(status, summary=''):
    json.dump({'status': status, 'summary': summary}, open('/tmp/login.json', 'w', encoding='utf-8'))
    print('Login: %s%s' % (status, ' (%s)' % summary if summary else ''))
    sys.exit(0)


def gh(*args, token=None):
    env = dict(os.environ)
    if token:
        env['GH_TOKEN'] = token
    return subprocess.run(['gh', *args], capture_output=True, text=True, env=env)


class Terminal:
    """`claude setup-token` in a wide pseudo-terminal, so its link isn't wrapped across lines."""

    def __init__(self, cmd):
        self.pid, self.fd = pty.fork()
        if self.pid == 0:
            os.environ.update(TERM='xterm-256color', COLUMNS='2000', LINES='50')
            os.execvp(cmd[0], cmd)
        fcntl.ioctl(self.fd, termios.TIOCSWINSZ, struct.pack('HHHH', 50, 2000, 0, 0))
        self.text = ''

    def wait_for(self, pattern, seconds):
        """Read output until pattern matches the text so far (escape codes removed); None on timeout or exit."""
        end = time.time() + seconds
        while time.time() < end:
            m = pattern.search(self.text)
            if m:
                return m
            ready, _, _ = select.select([self.fd], [], [], 0.5)
            if ready:
                try:
                    data = os.read(self.fd, 65536)
                except OSError:
                    data = b''
                if not data:
                    return pattern.search(self.text)
                self.text += ANSI.sub('', data.decode('utf-8', 'replace'))
        return pattern.search(self.text)

    def type(self, s):
        for ch in s:  # one key at a time, like a person pasting into the prompt
            os.write(self.fd, ch.encode())
            time.sleep(0.01)
        os.write(self.fd, b'\r')

    def stop(self):
        try:
            os.kill(self.pid, 9)
        except OSError:
            pass


def code_from_runs():
    """The code the bot relayed for this login, and the id of the run that carried it (deleted after use)."""
    r = gh('api', 'repos/%s/actions/workflows/claude-login-code.yml/runs?per_page=20' % REPO,
           '--jq', '.workflow_runs[] | [.id, .display_title] | @tsv')
    prefix = 'Claude login code %s ' % REF
    for line in r.stdout.splitlines():
        run_id, _, title = line.partition('\t')
        if title.startswith(prefix):
            return title[len(prefix):].strip(), run_id
    return None, None


def main():
    if not (REPO and REF and os.environ.get('SECRETS_TOKEN')):
        finish('failed', 'the login job is missing its settings (SSMB_BOT_GITHUB_TOKEN secret)')
    term = Terminal(['claude', 'setup-token'])
    link = term.wait_for(URL, 120)
    if not link:
        term.stop()
        finish('failed', 'Claude did not show a sign-in link: ' + ' '.join(term.text.split())[-200:])
    body = base64.b64encode(link.group(0).encode()).decode()
    put = gh('api', '-X', 'PUT', 'repos/%s/contents/login/%s.txt' % (REPO, REF), '-f', 'message=Claude sign-in link ' + REF,
             '-f', 'content=' + body, '-f', 'branch=incoming')
    if put.returncode:
        term.stop()
        finish('failed', 'could not pass the sign-in link on: ' + put.stderr.strip()[-200:])
    print('Sign-in link passed on; waiting for the code.')

    end, code, run_id = time.time() + WAIT_FOR_CODE, None, None
    while time.time() < end and not code:
        code, run_id = code_from_runs()
        if not code:
            term.wait_for(re.compile(r'(?!)'), 5)  # keep reading the terminal while waiting
    if not code:
        term.stop()
        finish('failed', 'no code came within 15 minutes')
    gh('api', '-X', 'DELETE', 'repos/%s/actions/runs/%s' % (REPO, run_id))  # the code is used up; don't leave it on show
    print('Code received.')
    term.type(code)
    token = term.wait_for(TOKEN, 120)
    term.stop()
    if not token:
        tail = ' '.join(TOKEN.sub('[token]', term.text).split())[-200:]
        finish('failed', 'Claude did not accept the code: ' + tail)
    print('::add-mask::' + token.group(0))
    saved = subprocess.run(['gh', 'secret', 'set', 'CLAUDE_CODE_OAUTH_TOKEN', '--repo', REPO], input=token.group(0), text=True,
                           capture_output=True, env=dict(os.environ, GH_TOKEN=os.environ['SECRETS_TOKEN']))
    if saved.returncode:
        finish('failed', 'logged in, but the token could not be saved: ' + saved.stderr.strip()[-200:])
    # a copied login stored earlier (CLAUDE_CREDENTIALS) isn't needed any more
    gh('secret', 'delete', 'CLAUDE_CREDENTIALS', '--repo', REPO, token=os.environ['SECRETS_TOKEN'])
    finish('done')


if __name__ == '__main__':
    main()
