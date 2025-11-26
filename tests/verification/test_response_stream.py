import asyncio

from src.agents.response_generator import ResponseGeneratorAgent
from src.core.state import StateManager


def test_stream_response_yields_steps():
    agent = ResponseGeneratorAgent()
    sm = StateManager()
    state = sm.create_initial_state('s1', 'test')
    # minimal hotel option object with attributes used in formatting
    class H:
        def __init__(self):
            self.name = 'Test Hotel'
            self.rating = 4.5
            self.price_range = '$$$'
            self.review_highlights = ['clean']

    state['hotel_options'] = [H()]

    async def run():
        gen = agent.stream_response(state)
        parts = []
        async for p in gen:
            parts.append(p)
        return parts

    parts = asyncio.get_event_loop().run_until_complete(run())
    assert any(p['step'] == 'hotels' for p in parts)
    assert any(p['step'] == 'weather' for p in parts)
    assert any(p['step'] == 'final' for p in parts)
