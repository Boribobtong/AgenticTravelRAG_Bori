from src.tools.climate_db import get_climate_info


def test_get_climate_info_paris_december():
    info = get_climate_info('Paris', 12)
    assert info is not None
    assert 'avg_temp' in info
    assert isinstance(info['avg_temp'], tuple)
