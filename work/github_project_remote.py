"""Use Git Credential Manager in memory; never print or persist credentials."""
import argparse
import json
import os
import subprocess
import urllib.error
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('action', choices=['check', 'create', 'verify'])
parser.add_argument('--name', default='rift-apart-photo-mode')
args = parser.parse_args()
env = dict(os.environ, GCM_INTERACTIVE='never', GIT_TERMINAL_PROMPT='0')
result = subprocess.run(['git', 'credential', 'fill'], input='protocol=https\nhost=github.com\n\n',
                        text=True, capture_output=True, env=env, timeout=35)
fields = dict(line.split('=', 1) for line in result.stdout.splitlines() if '=' in line)
token = fields.get('password')
if result.returncode or not token:
    raise SystemExit('No usable noninteractive GitHub credential was found. No credential output was printed.')

def api(path, method='GET', body=None):
    request = urllib.request.Request('https://api.github.com' + path,
        data=json.dumps(body).encode() if body is not None else None,
        headers={'Authorization': 'Bearer ' + token, 'Accept': 'application/vnd.github+json',
                 'User-Agent': 'PhotoMode-Project-Migration', 'X-GitHub-Api-Version': '2022-11-28'},
        method=method)
    try:
        with urllib.request.urlopen(request, timeout=25) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        if error.code == 404:
            return None
        raise SystemExit(f'GitHub API request failed: HTTP {error.code}; credentials omitted.')

user = api('/user')
if not user or not user.get('login'):
    raise SystemExit('GitHub account could not be verified.')
owner = user['login']
repo = api(f'/repos/{owner}/{args.name}')
if args.action == 'create':
    if repo:
        raise SystemExit('Repository name already exists; refusing to modify it automatically.')
    repo = api('/user/repos', 'POST', {'name': args.name, 'private': True, 'auto_init': False,
        'description': 'Build-guarded Ratchet & Clank Rift Apart Photo Mode extension and lighting/fog research.'})
if args.action == 'verify':
    if not repo or not repo.get('private'):
        raise SystemExit('Expected private repository not found.')
    head = api(f'/repos/{owner}/{args.name}/git/ref/heads/main')
    print(json.dumps({'url': repo['html_url'], 'private': repo['private'],
                      'remote_main': head['object']['sha'] if head else None}))
else:
    print(json.dumps({'login': owner, 'id': user['id'], 'repo_exists': bool(repo),
                      'url': repo.get('html_url') if repo else None,
                      'private': repo.get('private') if repo else None}))
