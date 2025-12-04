import pytest
from utils.config import get_file_size,getSystemDetails


def test_get_file_size():
    import tempfile
    import os

    with tempfile.NamedTemporaryFile(delete=False) as f:
        f.write(b'0' * (1024*1024))
        temp_path = f.name
    
    result = get_file_size(temp_path)


    assert result["mb"] == 1.0
    assert result['mb'] == 1.0
    assert result['kb'] == 1024.0
    assert result['bytes'] == 1024 * 1024

    os.unlink(temp_path)


def test_getSystemDetails():
    result = getSystemDetails()

    assert 'total_gb' in result
    assert 'available_gb' in result
    assert 'percent' in result
    assert 'logical' in result
    assert 'physical' in result

    assert result['total_gb'] > 0
    assert result['available_gb'] > 0
    assert 0 <= result['percent'] <= 100
    assert result['logical'] >= result['physical']


    
