import json
import sys
import types
import pytest

# Defensive import: tests should run even when `wikipedia` is not installed in the test env.
try:
    import wikipedia
except Exception:
    wikipedia = types.ModuleType('wikipedia')
    class _Disamb(Exception):
        def __init__(self, title, options):
            self.title = title
            self.options = options
    class _PageError(Exception):
        pass
    wikipedia.exceptions = types.SimpleNamespace(DisambiguationError=_Disamb, PageError=_PageError)
    sys.modules['wikipedia'] = wikipedia

from src.tools.wiki_tool import WikipediaCustomTool

class DummyPage:
    def __init__(self, url):
        self.url = url

class DummyDisambiguation(Exception):
    pass

def test_wiki_tool_basic(monkeypatch, tmp_path):
    # Prepare monkeypatches for wikipedia functions
    monkeypatch.setenv('WIKI_USE_CACHE', 'False')

    def fake_search(q, results=1):
        return ['몽마르뜨']
    def fake_summary(title, sentences=3, auto_suggest=False):
        return '몽마르뜨 요약 텍스트'
    def fake_page(title, auto_suggest=False):
        return DummyPage('https://ko.wikipedia.org/wiki/몽마르뜨')

    monkeypatch.setattr('wikipedia.search', fake_search)
    monkeypatch.setattr('wikipedia.summary', fake_summary)
    monkeypatch.setattr('wikipedia.page', fake_page)

    tool = WikipediaCustomTool()
    res = tool.run('몽마르뜨')

    assert res.get('title') == '몽마르뜨'
    assert '요약' in res.get('summary')
    assert res.get('source').startswith('https://')

def test_wiki_tool_disambiguation(monkeypatch):
    # Simulate DisambiguationError
    class FakeDisamb(Exception):
        def __init__(self, options):
            self.options = options
    def fake_search(q, results=1):
        raise wikipedia.exceptions.DisambiguationError('term', ['A','B','C'])

    monkeypatch.setattr('wikipedia.search', fake_search)

    tool = WikipediaCustomTool()
    res = tool.run('AmbiguousTerm')
    assert res.get('error') in ('disambiguation', 'exception') or 'options' in res

def test_wiki_tool_cache(monkeypatch, tmp_path):
    cache_path = tmp_path / 'wiki_cache.jsonl'
    monkeypatch.setenv('WIKI_USE_CACHE', 'True')
    monkeypatch.setenv('WIKI_CACHE_PATH', str(cache_path))

    # Create cache entry
    entry = {'query': 'Paris', 'title': 'Paris', 'summary': 'Paris summary', 'source': 'https://...'}
    with open(cache_path, 'w', encoding='utf-8') as f:
        f.write(json.dumps(entry, ensure_ascii=False) + '\n')

    tool = WikipediaCustomTool()
    res = tool.run('Paris')
    assert res.get('cached') is True
    assert res.get('title') == 'Paris'
