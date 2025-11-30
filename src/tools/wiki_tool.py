import os
import json
from typing import Optional, Dict

import wikipedia

# Note: configuration is read per-instance in __init__ to allow tests to
# change env vars at runtime (monkeypatching).


class WikipediaCustomTool:
    """A small wrapper around the `wikipedia` library tailored for AgenticTravelRAG.

    This is synchronous by design. For integration with async agents, wrap or call
    it in a thread/executor or implement an async wrapper.
    """

    def __init__(self):
        # instance-level config read from environment for testability
        self.lang = os.getenv("WIKI_LANG", "ko")
        self.max_sentences = int(os.getenv("WIKI_MAX_SENTENCES", "3"))
        self.use_cache = os.getenv("WIKI_USE_CACHE", "True").lower() in ("1", "true", "yes")
        self.cache_path = os.getenv("WIKI_CACHE_PATH", "data/cache/wiki_cache.jsonl")

        wikipedia.set_lang(self.lang)
        # ensure cache directory exists when needed
        if self.use_cache:
            cache_dir = os.path.dirname(self.cache_path)
            if cache_dir and not os.path.exists(cache_dir):
                os.makedirs(cache_dir, exist_ok=True)

    def _read_cache(self) -> Dict[str, Dict]:
        if not self.use_cache or not os.path.exists(self.cache_path):
            return {}
        out = {}
        try:
            with open(self.cache_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        item = json.loads(line)
                        out[item['query']] = item
                    except Exception:
                        continue
        except Exception:
            return {}
        return out

    def _write_cache_item(self, query: str, record: Dict):
        if not self.use_cache:
            return
        try:
            with open(self.cache_path, 'a', encoding='utf-8') as f:
                entry = {'query': query, 'title': record.get('title'), 'summary': record.get('summary'), 'source': record.get('source')}
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception:
            # best-effort caching
            pass

    def run(self, query: str) -> Dict[str, Optional[str]]:
        """Search and return a small structured result for the given query.

        Returns a dict with keys: title, summary, source, or an error key.
        """
        query = (query or "").strip()
        if not query:
            return {'error': 'empty query'}

        # Check cache first
        cache = self._read_cache()
        if query in cache:
            return {'title': cache[query].get('title'), 'summary': cache[query].get('summary'), 'source': cache[query].get('source'), 'cached': True}

        try:
            wikipedia.set_lang(self.lang)
            results = wikipedia.search(query, results=1)
            if not results:
                return {'error': 'no_results'}

            title = results[0]
            try:
                summary = wikipedia.summary(title, sentences=self.max_sentences, auto_suggest=False)
            except Exception:
                # fallback: try without auto_suggest
                summary = wikipedia.summary(title, sentences=self.max_sentences)

            page = wikipedia.page(title, auto_suggest=False)
            source = page.url if hasattr(page, 'url') else None

            record = {'title': title, 'summary': summary, 'source': source}
            # Write cache (best-effort)
            self._write_cache_item(query, record)

            return record

        except wikipedia.exceptions.DisambiguationError as e:
            # return a short message and some options
            return {'error': 'disambiguation', 'options': e.options[:5]}
        except wikipedia.exceptions.PageError:
            return {'error': 'page_error'}
        except Exception as e:
            return {'error': 'exception', 'message': str(e)}
