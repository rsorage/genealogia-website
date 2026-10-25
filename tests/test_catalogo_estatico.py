"""Indexabilidade e ciclo de atualização das páginas, com dados fictícios."""
import importlib.util
import json
import re
import tempfile
import unittest
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

SPEC = importlib.util.spec_from_file_location('estatico', Path(__file__).resolve().parents[1] / 'scripts/catalogo_estatico.py')
static = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(static)

TEMPLATE = '''<style>body{color:#202c32}__ESTILOS_CATALOGO__</style>
<link rel="icon" href="data:image/svg+xml,x"><header class="masthead"><a href="/registros-vistos/" aria-current="page">Registros vistos</a></header>'''
SITEMAP = '''<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>https://genealogia.rsorage.com/</loc><lastmod>2026-01-01</lastmod></url>
<url><loc>https://genealogia.rsorage.com/registros-vistos/</loc><lastmod>2026-10-24</lastmod></url></urlset>'''


def row(identifier='L-0001', **overrides):
    data = dict(id=identifier, nome='Exemplo', sobrenome='Fictício', pai='', mae='', conjuge_nome='', conjuge_sobrenome='',
                comune='Local fictício', serie='Nati', ano='1884', parte='I', num_atto='7', data_evento='1884-01-03',
                imagem='4', papel='testemunha', leitura='provável', tipo='Nascimentos', nota='', conferencia='Leitura provisória.',
                portal='Portale Antenati', url='https://antenati.cultura.gov.it/ark:/12657/an_ua123/Exemplo',
                ato_id='A-0123456789abcdef', papeis=['Testemunha'])
    data.update(overrides)
    return data


class ReadHTML(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.tags = []
        self.links = []
        self.ids = []
        self.text = []
        self.canonicals = []
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        self.tags.append((tag, attrs))
        if tag == 'a':
            self.links.append(attrs.get('href', ''))
        if attrs.get('id'):
            self.ids.append(attrs['id'])
        if tag == 'link' and attrs.get('rel') == 'canonical':
            self.canonicals.append(attrs['href'])

    def handle_data(self, value):
        self.text.append(value)


class StaticContent(unittest.TestCase):
    def documents(self, rows):
        groups = static.make_groups({'nomes': rows})
        return groups, static.render_static(TEMPLATE, groups)

    def test_every_name_is_in_html_without_executing_javascript(self):
        rows = [row(f'L-{n:04}', nome=f'Pessoa {n}', num_atto=str(n), ato_id=f'A-{n:016x}') for n in range(1, 41)]
        groups, docs = self.documents(rows)
        page = ReadHTML(docs[groups[0]['path'] + 'index.html'])
        for item in rows:
            self.assertIn(item['id'], page.ids)
            self.assertIn(item['nome'], ''.join(page.text))
        self.assertEqual(len(page.ids), len(set(page.ids)))
        self.assertFalse(any(tag == 'script' and attrs.get('type') != 'application/ld+json' for tag, attrs in page.tags))

    def test_index_has_real_links_to_all_leaf_pages(self):
        groups, docs = self.documents([row(), row('L-0002', comune='Outro lugar')])
        links = ReadHTML(docs[static.BASE + 'index.html']).links
        for group in groups:
            self.assertIn('/' + group['path'], links)

    def test_every_leaf_has_its_own_canonical_and_description(self):
        groups, docs = self.documents([row(), row('L-0002', ano='1885')])
        titles = set()
        for group in groups:
            source = docs[group['path'] + 'index.html']
            page = ReadHTML(source)
            self.assertEqual(page.canonicals, [static.SITE + '/' + group['path']])
            self.assertTrue(any(tag == 'meta' and attrs.get('name') == 'description' for tag, attrs in page.tags))
            self.assertEqual(sum(tag == 'h1' for tag, _ in page.tags), 1)
            titles.add(re.search(r'<title>(.*?)</title>', source)[1])
        self.assertEqual(len(titles), len(groups))

    def test_uncertainty_partial_scope_and_primary_reference_are_visible(self):
        groups, docs = self.documents([row(nome='[Ro]cco', leitura='duvidosa', nota='O ato continua em outra imagem, não lida.')])
        page = docs[groups[0]['path'] + 'index.html']
        self.assertIn('[Ro]cco', page)
        self.assertIn('Leitura duvidosa', page)
        self.assertIn('outra imagem, não lida', page)
        self.assertIn('transcrição é parcial', page)
        self.assertIn('an_ua123/Exemplo', page)

    def test_parentage_not_invented_and_private_extra_fields_not_rendered(self):
        groups, docs = self.documents([row(origem_tabela='/Users/private/ORIGEM.csv', obs='PRIVATE_OBSERVATION')])
        source = docs[groups[0]['path'] + 'index.html']
        self.assertNotIn('<dt>Pai</dt>', source)
        self.assertNotIn('<dt>Mãe</dt>', source)
        self.assertNotIn('PRIVATE_OBSERVATION', source)
        self.assertNotIn('/Users/private', source)

    def test_names_and_notes_are_escaped_as_text(self):
        groups, docs = self.documents([row(nome='<img src=x onerror=alert(1)>', nota='<script>alert(1)</script>')])
        page = ReadHTML(docs[groups[0]['path'] + 'index.html'])
        self.assertFalse(any(tag == 'img' for tag, _ in page.tags))
        self.assertFalse(any(tag == 'script' and attrs.get('type') != 'application/ld+json' for tag, attrs in page.tags))
        self.assertIn('<img src=x onerror=alert(1)>', ''.join(page.text))

    def test_breadcrumbs_are_valid_json_and_reference_existing_routes(self):
        groups, docs = self.documents([row()])
        source = docs[groups[0]['path'] + 'index.html']
        structured = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', source, re.S)[1])
        self.assertEqual(structured['@type'], 'BreadcrumbList')
        self.assertEqual(structured['itemListElement'][-1]['item'], static.SITE + '/' + groups[0]['path'])

    def test_repeated_participant_ids_are_not_created_by_grouping(self):
        groups, docs = self.documents([row(), row('L-0002', papel='mãe, declarante', papeis=['Mãe', 'Declarante'])])
        ids = ReadHTML(docs[groups[0]['path'] + 'index.html']).ids
        self.assertEqual(ids.count('L-0001'), 1)
        self.assertEqual(ids.count('L-0002'), 1)

    def test_address_collision_stops_generation(self):
        with self.assertRaisesRegex(ValueError, 'mesmo endereço'):
            self.documents([row(comune='A & B'), row('L-0002', comune='A B')])


class GeneratedLifecycle(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'sitemap.xml').write_text(SITEMAP)
        self.path = static.BASE + 'local/nati/1884/index.html'
        self.documents = {'registros-vistos/index.html': 'MAIN', self.path: static.MARKER + 'CONTENT'}

    def apply(self, documents=None, today='2026-10-25'):
        outputs, stale, manifest = static.plan(self.root, documents or self.documents, today)
        static.apply_plan(self.root, outputs, stale)
        return outputs, stale, manifest

    def test_dates_preserved_when_content_does_not_change(self):
        self.apply()
        _, _, manifest = self.apply(today='2026-10-26')
        self.assertTrue(all(entry['lastmod'] == '2026-10-25' for entry in manifest['files'].values()))

    def test_date_changes_only_for_updated_page(self):
        self.apply()
        docs = dict(self.documents)
        docs[self.path] += ' UPDATED'
        _, _, manifest = self.apply(docs, today='2026-10-26')
        self.assertEqual(manifest['files'][self.path]['lastmod'], '2026-10-26')
        self.assertEqual(manifest['files']['registros-vistos/index.html']['lastmod'], '2026-10-25')

    def test_obsolete_page_removed_from_disk_and_sitemap(self):
        self.apply()
        _, stale, _ = self.apply({'registros-vistos/index.html': 'MAIN'})
        self.assertEqual(stale, [self.path])
        self.assertFalse((self.root / self.path).exists())
        self.assertNotIn('local/nati/1884', (self.root / 'sitemap.xml').read_text())

    def test_manual_edit_of_obsolete_page_requires_review(self):
        self.apply()
        (self.root / self.path).write_text('USER EDIT')
        with self.assertRaisesRegex(ValueError, 'editada localmente'):
            static.plan(self.root, {'registros-vistos/index.html': 'MAIN'}, '2026-10-26')
        self.assertEqual((self.root / self.path).read_text(), 'USER EDIT')

    def test_unmanaged_page_cannot_be_overwritten(self):
        target = self.root / self.path
        target.parent.mkdir(parents=True)
        target.write_text('EXISTING USER FILE')
        with self.assertRaisesRegex(ValueError, 'não pertence'):
            static.plan(self.root, self.documents, '2026-10-25')

    def test_manifest_cannot_own_files_outside_catalog(self):
        path = self.root / static.MANIFEST
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps({'version': 1, 'files': {'../../private/index.html': {'sha256': 'a' * 64, 'lastmod': '2026-10-25'}}}))
        with self.assertRaisesRegex(ValueError, 'Caminho'):
            static.load_manifest(self.root)

    def test_sitemap_preserves_other_pages_and_has_no_query_urls(self):
        self.apply()
        xml = (self.root / 'sitemap.xml').read_text()
        self.assertIn('<lastmod>2026-01-01</lastmod>', xml)
        locations = ET.fromstring(xml).findall('{http://www.sitemaps.org/schemas/sitemap/0.9}url/{http://www.sitemaps.org/schemas/sitemap/0.9}loc')
        self.assertEqual(len(locations), 3)
        self.assertFalse(any('?' in el.text or '#' in el.text for el in locations))

    def test_missing_sitemap_root_stops_before_writes(self):
        (self.root / 'sitemap.xml').write_text('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"></urlset>')
        with self.assertRaisesRegex(ValueError, 'principal'):
            static.plan(self.root, self.documents, '2026-10-25')
        self.assertFalse((self.root / self.path).exists())


if __name__ == '__main__':
    unittest.main()
