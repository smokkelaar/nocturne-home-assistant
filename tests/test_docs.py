"""Offline checks for the guide's local links, figures and safety boundaries."""
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
SVG = '{http://www.w3.org/2000/svg}'


def heading_ids(text):
    # The guides use ordinary ATX headings, not HTML ids or duplicate anchors.
    return {re.sub(r'[^\w\- ]', '', line.lstrip('#').strip().lower()).replace(' ', '-')
            for line in text.splitlines() if re.match(r'^#{1,6} ', line)}


class DocumentationTests(unittest.TestCase):
    def test_local_markdown_links_and_anchors_exist(self):
        for source in ROOT.rglob('*.md'):
            if '.git' in source.parts:
                continue
            for raw in re.findall(r'\[[^\[\]\n]*\]\(([^)\s]+)\)', source.read_text(encoding='utf-8')):
                url = urlsplit(raw)
                if url.scheme or url.netloc:
                    continue
                target = (source.parent / unquote(url.path)).resolve() if url.path else source
                with self.subTest(source=source.relative_to(ROOT), target=raw):
                    self.assertTrue(target.is_relative_to(ROOT), 'Link escapes repository')
                    self.assertTrue(target.exists(), 'Missing linked file')
                    if url.fragment and target.suffix == '.md':
                        self.assertIn(unquote(url.fragment), heading_ids(target.read_text(encoding='utf-8')))

    def test_diagrams_are_accessible_static_svg(self):
        diagrams = list((ROOT / 'docs/images').glob('*.svg'))
        self.assertEqual(4, len(diagrams))
        for file in diagrams:
            with self.subTest(file=file.name):
                root = ET.parse(file).getroot()
                self.assertEqual(SVG + 'svg', root.tag)
                self.assertIsNotNone(root.find(SVG + 'title'))
                self.assertIsNotNone(root.find(SVG + 'desc'))
                self.assertIn('viewBox', root.attrib)
                self.assertEqual('960', root.attrib.get('width'), 'Avoid tiny default SVG size in GitHub Markdown')
                self.assertEqual(root.attrib['viewBox'].split()[3], root.attrib.get('height'))
                for node in root.iter():
                    self.assertNotIn(node.tag, (SVG + 'script', SVG + 'foreignObject', SVG + 'image'))
                    for key, value in node.attrib.items():
                        self.assertFalse(key.lower().startswith('on'), 'Executable SVG handler')
                        if key.endswith('href'):
                            self.assertTrue(value.startswith('#'), 'External SVG dependency')

    def test_installation_has_all_steps_and_checkpoints(self):
        guide = (ROOT / 'docs/INSTALLATIE.md').read_text(encoding='utf-8')
        for step in range(1, 9):
            self.assertIn(f'## Stap {step}:', guide)
        self.assertGreaterEqual(guide.count('Controlepunt'), 7)
        for reference in ['MIGRATION.md', 'HTTPS-EN-DNS.md', 'OPLOSPLAN.md']:
            self.assertIn(reference, guide)
        self.assertIn('geen screenshots', guide)

    def test_entrypoints_make_dutch_guide_discoverable(self):
        for name in ['README.md', 'nocturne_local/README.md', 'nocturne_local/DOCS.md', 'docs/NL.md']:
            self.assertIn('INSTALLATIE.md', (ROOT / name).read_text(encoding='utf-8'))

    def test_proposals_do_not_claim_implementation(self):
        plan = (ROOT / 'docs/OPLOSPLAN.md').read_text(encoding='utf-8')
        self.assertIn('Voorstellen, geen reeds geïmplementeerde functies', plan)
        self.assertGreaterEqual(plan.count('**Acceptatie:**'), 7)


if __name__ == '__main__':
    unittest.main()
