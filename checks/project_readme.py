"""Finite offline README/translation contracts; no readability or legal judgment.

Parses inline/reference/shortcut links, nested linked images, escaped and balanced
URI parentheses, optional titles, code/comments and HTML a/img. CommonMark 0.31.2
is a reference, not a claim of complete CommonMark or browser implementation.
"""
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import argparse
import html
from html.parser import HTMLParser
import json
import re
import urllib.parse
import xml.etree.ElementTree as ET
from checks.validation_common import require, read_json, digest, safe_path, ValidationError
from checks.corpus_contract import markdown_blocks, anchors, headings

ROOT = Path(__file__).resolve().parents[1]
CONTRACT = 'sources/project-governance/documentation-rights.json'
ESCAPE = re.compile(r'\\([!"#$%&\'()*+,\-./:;<=>?@\[\]\\^_`{|}~])')


def unescape(value):
    return html.unescape(ESCAPE.sub(r'\1', value))


def reference_key(value):
    return re.sub(r'\s+', ' ', value).strip().casefold()


def visible(text):
    return ''.join(b['visible_text'] if b['kind'] not in {'code', 'comment'}
                   else '\n' * b['text'].count('\n') for b in markdown_blocks(text))


def code_end(text, i):
    run = re.match(r'`+', text[i:])[0]
    match = re.search(r'(?<!`)'+re.escape(run)+r'(?!`)', text[i+len(run):])
    return i+len(run)+match.end() if match else i+len(run)


def closing_bracket(text, start):
    depth = 1; i = start+1
    while i < len(text):
        if text[i] == '\\': i += 2; continue
        if text[i] == '`': i = code_end(text, i); continue
        if text[i] == '[': depth += 1
        elif text[i] == ']':
            depth -= 1
            if depth == 0: return i
        i += 1
    return None


def destination(text, start, inline=True):
    """Return decoded destination and end offset; malformed syntax contributes none."""
    i = start
    while i < len(text) and text[i].isspace(): i += 1
    begin = i
    if i < len(text) and text[i] == '<':
        i += 1; begin = i
        while i < len(text):
            if text[i] == '\\': i += 2; continue
            if text[i] in '\n\r<': return None
            if text[i] == '>': break
            i += 1
        if i >= len(text): return None
        value = text[begin:i]; i += 1
    else:
        depth = 0
        while i < len(text):
            char = text[i]
            if char == '\\': i += 2; continue
            if char == '(' : depth += 1
            elif char == ')':
                if depth == 0: break
                depth -= 1
            if char.isspace(): break
            i += 1
        if depth: return None
        value = text[begin:i]
    gap = i
    while i < len(text) and text[i].isspace(): i += 1
    if i > gap and i < len(text) and text[i] in '\"\'(':
        delim = ')' if text[i] == '(' else text[i]; i += 1
        while i < len(text):
            if text[i] == '\\': i += 2; continue
            if text[i] == delim: break
            i += 1
        if i >= len(text): return None
        i += 1
        while i < len(text) and text[i].isspace(): i += 1
    if inline:
        if i >= len(text) or text[i] != ')': return None
        i += 1
    elif i != len(text): return None
    return unescape(value), i


class HTMLLinks(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True); self.links = []; self.current = None
    def handle_starttag(self, tag, attrs):
        values = dict(attrs)
        require(len(values) == len(attrs), 'duplicate HTML attribute')
        require(tag not in {'script', 'style', 'iframe', 'object', 'embed'}, 'unsupported active HTML', tag)
        require('hidden' not in values and values.get('aria-hidden') != 'true' and
                not re.search(r'display\s*:\s*none|visibility\s*:\s*hidden', values.get('style', ''), re.I),
                'hidden HTML is not an entry', tag)
        if tag == 'a' and 'href' in values:
            require(self.current is None, 'nested HTML link')
            self.current = {'kind': 'link', 'url': values['href'], 'label': '', 'parent_url': None}
        if tag == 'img':
            self.links.append({'kind': 'image', 'url': values.get('src', ''), 'label': values.get('alt', ''),
                               'decorative': values.get('role') == 'presentation',
                               'parent_url': self.current['url'] if self.current else None})
            if self.current: self.current['label'] += values.get('alt', '')
    def handle_endtag(self, tag):
        if tag == 'a' and self.current:
            self.links.append(self.current); self.current = None
    def handle_data(self, data):
        if self.current: self.current['label'] += data


def parse_links(text):
    text = visible(text); definitions = {}; parts = []
    for line in text.splitlines(keepends=True):
        match = re.match(r'^ {0,3}\[([^\]\n]+)\]:[ \t]*(.*)$', line.rstrip('\r\n'))
        parsed = destination(match[2], 0, False) if match else None
        if match and parsed:
            definitions.setdefault(reference_key(match[1]), parsed[0]); parts.append('\n')
        else: parts.append(line)
    text = ''.join(parts)
    def scan(chunk, parent=None):
        result = []; i = 0
        while i < len(chunk):
            if chunk[i] == '\\': i += 2; continue
            if chunk[i] == '`': i = code_end(chunk, i); continue
            if chunk[i] == '<':
                end = chunk.find('>', i+1)
                if end >= 0: i = end+1; continue
            image = chunk.startswith('![', i)
            begin = i+1 if image else i
            if begin >= len(chunk) or chunk[begin] != '[': i += 1; continue
            close = closing_bracket(chunk, begin)
            if close is None: i += 1; continue
            label = chunk[begin+1:close]; end = close+1; url = None
            if end < len(chunk) and chunk[end] == '(':
                parsed = destination(chunk, end+1)
                if parsed: url, end = parsed
            if url is None and end < len(chunk) and chunk[end] == '[':
                refclose = chunk.find(']', end+1)
                if refclose >= 0:
                    key = reference_key(chunk[end+1:refclose] or label)
                    require(key in definitions, 'undefined reference link', key)
                    url = definitions[key]; end = refclose+1
            if url is None and reference_key(label) in definitions:
                url = definitions[reference_key(label)]
            if url is None: i = begin+1; continue
            children = scan(label, url if not image else parent)
            if not image: require(not any(x['kind'] == 'link' for x in children), 'nested Markdown link outside finite profile')
            plain = label
            # The accessible label of a linked image is the image alternative.
            if children:
                plain = ' '.join(x['label'] for x in children)
            else: plain = unescape(re.sub(r'[*_`]', '', label))
            result.append({'kind': 'image' if image else 'link', 'url': url,
                           'label': plain, 'parent_url': parent})
            if not image: result.extend(children)
            i = end
        return result
    result = scan(text)
    # Inline code must not become HTML a/img either.
    no_code = re.sub(r'(?<!`)(`+)(?!`)(.*?)\1(?!`)', '', text, flags=re.S)
    parser = HTMLLinks(); parser.feed(no_code); parser.close()
    require(parser.current is None, 'unclosed HTML link')
    return result+parser.links


def resolve_target(root, source, url):
    require(isinstance(url, str) and url.strip() == url and url, 'empty/malformed link target')
    value = urllib.parse.urlsplit(url)
    require(value.scheme in {'', 'https', 'http', 'mailto'}, 'unsupported link protocol', url)
    require(not (value.netloc and not value.scheme), 'protocol-relative link unsupported', url)
    if value.scheme: return None
    require(not value.query, 'local query unsupported', url)
    raw = urllib.parse.unquote(value.path)
    require('\\' not in raw and '\x00' not in raw, 'invalid local path', url)
    target = safe_path(root, raw or Path(source).name, base=Path(source).parent, allow_parent=True, kind='any')
    if target.is_dir(): target = safe_path(root, (target/'README.md').relative_to(root).as_posix())
    if value.fragment:
        require(target.suffix == '.md', 'fragment target must be Markdown', url)
        require(urllib.parse.unquote(value.fragment) in anchors(target.read_text(encoding='utf-8')),
                'missing target anchor', url)
    return target


def png_container_info(raw):
    """Finite framing/CRC/IHDR metadata only; no pixel decoding or PNG conformance claim."""
    import zlib
    require(type(raw)is bytes and raw.startswith(b'\x89PNG\r\n\x1a\n'),'PNG signature')
    pos=8;types=[];dimensions=None
    while pos<len(raw):
        require(len(raw)-pos>=12,'truncated PNG chunk')
        length=int.from_bytes(raw[pos:pos+4],'big');kind=raw[pos+4:pos+8]
        require(length<=0x7fffffff and pos+length+12<=len(raw),'PNG chunk bounds')
        require(all(65<=c<=90 or 97<=c<=122 for c in kind),'PNG chunk type')
        data=raw[pos+8:pos+8+length];crc=int.from_bytes(raw[pos+8+length:pos+12+length],'big')
        require((zlib.crc32(kind+data)&0xffffffff)==crc,'PNG chunk CRC')
        if not types:require(kind==b'IHDR'and length==13,'PNG first IHDR')
        if kind==b'IHDR':
            require(dimensions is None and length==13,'duplicate or invalid PNG IHDR')
            width=int.from_bytes(data[:4],'big');height=int.from_bytes(data[4:8],'big')
            require(0<width<=0x7fffffff and 0<height<=0x7fffffff,'PNG dimension range')
            dimensions=(width,height)
        if kind==b'IEND':require(length==0 and pos+12==len(raw),'PNG IEND or trailing bytes')
        types.append(kind);pos+=length+12
    require(dimensions is not None and types[-1]==b'IEND'and b'IDAT'in types,'PNG required container chunks')
    return {'format':'PNG','width':dimensions[0],'height':dimensions[1],'bytes':len(raw)}


def validate_image_metadata(path,contract):
    """Check the explicitly selected PNG profile; other assets retain identity checks."""
    if path.suffix.lower()=='.png'or'format'in contract:
        require(contract.get('format')=='PNG'and path.suffix.lower()=='.png','unsupported declared raster metadata profile')
        actual=png_container_info(path.read_bytes())
        require(all(type(contract.get(key))is int and contract[key]==actual[key]for key in ('width','height','bytes')),'PNG declared dimensions/bytes mismatch')
        return actual
    return None


def validate_svg(path):
    try: tree = ET.fromstring(path.read_bytes())
    except (ET.ParseError, OSError) as exc: raise ValidationError(('invalid SVG', str(path))) from exc
    require(tree.tag == '{http://www.w3.org/2000/svg}svg', 'SVG root required', str(path))
    title = tree.find('{http://www.w3.org/2000/svg}title'); desc = tree.find('{http://www.w3.org/2000/svg}desc')
    require(title is not None and ''.join(title.itertext()).strip(), 'SVG title required')
    require(desc is not None and ''.join(desc.itertext()).strip(), 'SVG description required')
    return tree


def validate_document_links(root, name):
    path = safe_path(root, name); records = parse_links(path.read_text(encoding='utf-8')); local = external = 0
    for record in records:
        label = html.unescape(record['label']).strip()
        decorative = record.get('decorative') and record['kind'] == 'image' and not record['parent_url']
        require(label or decorative, 'empty link name or image alternative', name, record['url'])
        target = resolve_target(root, path, record['url'])
        if target is None: external += 1
        else:
            local += 1
            if record['kind'] == 'image':
                require(target.is_file() and target.suffix.lower() in {'.svg', '.png', '.jpg', '.jpeg', '.gif', '.webp'}, 'invalid image target')
                if target.suffix.lower() == '.svg': validate_svg(target)
    return records, {'local': local, 'external_not_fetched': external}


def clause_ids(body):
    return [h['match'][1] for h in headings(markdown_blocks(body)) if h['match']]


def validate_translations(root, rows):
    seen = set(); total = 0
    for row in rows:
        require(row['document_id'] not in seen, 'duplicate translation mapping'); seen.add(row['document_id'])
        require(row['source_language'] == 'zh-Hans' and row['target_language'] == 'en' and
                row['authority'] == 'source-only' and row['coverage'] == 'full', 'translation authority/coverage contract')
        source = safe_path(root, row['source_path']); target = safe_path(root, row['target_path'])
        require(source != target, 'translation cannot alias source')
        require(digest(source.read_bytes()) == row['source_sha256'], 'stale translation source identity', row['document_id'])
        require(digest(target.read_bytes()) == row['target_sha256'], 'stale translation target identity', row['document_id'])
        zh = source.read_text(encoding='utf-8'); en = target.read_text(encoding='utf-8')
        marker=row.get('target_version_marker','Source version')
        require(marker in {'Source version','Version'},'unknown translation version metadata profile')
        def version_values(text,label):
            visible='\n'.join(b['visible_text'] for b in markdown_blocks(text) if b['kind']not in {'code','comment'})
            return re.findall(r'\*\*'+re.escape(label)+r'[：:]\*\*[ \t]*([^*\s]+)',visible)
        require(version_values(zh,'版本')==[row['source_version']] and version_values(en,marker)==[row['source_version']], 'translation version mismatch')
        require(clause_ids(zh) == clause_ids(en) == row['clause_ids'], 'translation clause sequence mismatch')
        require(len(row['clause_ids']) == len(set(row['clause_ids'])), 'duplicate translation clause')
        total += len(row['clause_ids'])
    return {'documents': len(seen), 'clauses': total, 'result': 'identity-verified',
            'scope': 'source/target hashes, language labels, version markers and clause sequence'}


def validate_readmes(root, contract):
    require(type(contract) is dict and contract.get('badge_protocol') == 'shields-static/1',
            'README Shields badge protocol is required')
    require(type(contract.get('badge')) is dict, 'README collection badge contract is required')
    by_language = {}; counts = {'local': 0, 'external_not_fetched': 0}
    for language, name in contract['files'].items():
        records, count = validate_document_links(root, name); by_language[language] = records
        for key in counts: counts[key] += count[key]
        content = safe_path(root, name).read_text(encoding='utf-8')
        require(set(contract['anchors']) <= anchors(content), 'missing README section anchor', name)
        actual_commands = [b['text'].split('\n', 1)[1].rsplit('\n', 2)[0] for b in markdown_blocks(content)
                           if b['kind'] == 'code' and b['text'].startswith('```sh\n')]
        require(actual_commands == contract['shell_blocks'], 'README command contract mismatch', name)
        for role, targets in contract['navigation'].items():
            require(any(r['kind'] == 'link' and r['url'] == targets[language] for r in records), 'missing named navigation role', name, role)
        counterpart = contract['files']['en' if language == 'zh-Hans' else 'zh-Hans']
        require(any(r['kind'] == 'link' and r['url'] == counterpart for r in records), 'missing reciprocal language link')
        expected_images = ({item['path'] for item in contract['images']}
                           | {contract['badge']['url']}
                           | {badge['url'] for badge in contract.get('additional_badges', [])})
        require(all(r['url'] in expected_images or r.get('decorative') for r in records if r['kind'] == 'image'), 'unregistered README image or badge', name)
        for image_contract in contract['images']:
            matching = [r for r in records if r['kind'] == 'image' and r['url'] == image_contract['path']]
            require(matching, 'missing README image', name)
            require(all(r['label'].strip() and not r.get('decorative') for r in matching), 'meaningful README asset cannot be decorative', image_contract['path'])
            image_path = safe_path(root, image_contract['path'])
            require(digest(image_path.read_bytes()) == image_contract['sha256'], 'image identity mismatch', image_contract['path'])
            validate_image_metadata(image_path,image_contract)
        from checks.readme_badges import validate_additional_badges, validate_badge
        require(contract['badge']['kind'] == 'status', 'collection status badge required')
        validate_badge(root, records, contract['badge'])
        validate_additional_badges(root, records, contract)
    return {'files': len(by_language), 'navigation_roles': len(contract['navigation']), **counts}


def validate(root=ROOT):
    root = Path(root).resolve(); contract = read_json(root/CONTRACT)
    require(contract['schema'] == 'standards-documentation-rights/1', 'unsupported contract schema')
    readmes = validate_readmes(root, contract['readme_contract'])
    ref=contract['translation_registry'];value=read_json(safe_path(root,ref['path']))
    rows=[row for row in value['records'] if row['document_id']in ref['document_ids']]
    require({row['document_id']for row in rows}==set(ref['document_ids']),'missing README-topic translation mapping')
    translations = validate_translations(root, rows)
    for row in rows:
        validate_document_links(root, row['source_path']); validate_document_links(root, row['target_path'])
    return {'readmes': readmes, 'translations': translations,
            'scope': 'README navigation, local links and anchors, image metadata, badge fields and translation identities'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--root', type=Path, default=ROOT); args = parser.parse_args()
    try: print(json.dumps(validate(args.root), ensure_ascii=False, indent=2))
    except (ValidationError, KeyError, TypeError, OSError) as exc:
        print(json.dumps({'result': 'failed', 'detail': str(exc)}, ensure_ascii=False), file=sys.stderr); sys.exit(1)
