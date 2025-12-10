import pytest
from secure_box.utils.tools import ASCIIBar
from rich.progress import Task


def test_ascii_bar_render():
    bar = ASCIIBar()
    
    class MockTask:
        def __init__(self, percentage):
            self.percentage = percentage
    
    task = MockTask(0)
    result = bar.render(task)
    assert "[" in str(result)
    assert "]" in str(result)
    
    task = MockTask(50)
    result = bar.render(task)
    rendered = str(result)
    assert "=" in rendered
    assert ">" in rendered
    
    task = MockTask(100)
    result = bar.render(task)
    rendered = str(result)
    assert rendered.count("=") > 25


def test_ascii_bar_progression():
    bar = ASCIIBar()
    
    class MockTask:
        def __init__(self, percentage):
            self.percentage = percentage
    
    results = []
    for percent in [0, 25, 50, 75, 100]:
        task = MockTask(percent)
        rendered = str(bar.render(task))
        results.append(rendered.count("="))
    
    for i in range(len(results) - 1):
        assert results[i] <= results[i + 1]