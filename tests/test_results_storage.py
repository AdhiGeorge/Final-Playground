import pytest
import asyncio
import json
import os
from pathlib import Path
from datetime import datetime

import aiofiles
import aiofiles.os
import pybreaker # Import pybreaker for the advanced test example

from utils.results_storage import ResultsStorage, SearchResultModel
from utils.config import config # AppConfig instance

# Test query and data
TEST_QUERY_NORMAL = "normal query for testing"
TEST_QUERY_SPECIAL_CHARS = "query with/slashes?and spaces"
TEST_URLS = ["http://example.com/page1", "https://example.org/resource?id=123"]
TEST_HTML_CONTENT = "<html><body><h1>Test Page</h1></body></html>"
TEST_METADATA = {"source": "test_scraper", "scraped_at": datetime.now().isoformat()}

@pytest.fixture
def temp_data_dir(tmp_path_factory):
    temp_base = tmp_path_factory.mktemp("test_data_base")
    original_base_dir = config.settings.directories.base
    config.settings.directories.base = str(temp_base)
    yield temp_base
    config.settings.directories.base = original_base_dir

@pytest.fixture
def storage_search(temp_data_dir):
    # temp_data_dir fixture has already patched config.directories.base
    rs = ResultsStorage(query=TEST_QUERY_NORMAL, type_='search')
    return rs

@pytest.fixture
def storage_scrape(temp_data_dir):
    # temp_data_dir fixture has already patched config.directories.base
    rs = ResultsStorage(query=TEST_QUERY_NORMAL, type_='scrape')
    return rs

@pytest.fixture
def storage_scrape_special_chars(temp_data_dir):
    # temp_data_dir fixture has already patched config.directories.base
    rs = ResultsStorage(query=TEST_QUERY_SPECIAL_CHARS, type_='scrape')
    return rs

@pytest.mark.asyncio
async def test_directory_structure_search(storage_search: ResultsStorage, temp_data_dir: Path):
    await storage_search._ensure_directories_ready() # Ensure directories are created before assertions
    assert storage_search.is_ready()
    sanitized_query = storage_search._sanitize_query(TEST_QUERY_NORMAL)
    expected_query_dir = temp_data_dir / sanitized_query
    expected_results_dir = expected_query_dir / config.settings.search.results.directory

    assert await aiofiles.os.path.isdir(expected_query_dir)
    assert await aiofiles.os.path.isdir(expected_results_dir)
    assert storage_search.query_dir == expected_query_dir
    assert storage_search.results_dir == expected_results_dir

@pytest.mark.asyncio
async def test_directory_structure_scrape(storage_scrape: ResultsStorage, temp_data_dir: Path):
    await storage_scrape._ensure_directories_ready() # Ensure directories are created before assertions
    assert storage_scrape.is_ready()
    sanitized_query = storage_scrape._sanitize_query(TEST_QUERY_NORMAL)
    expected_query_dir = temp_data_dir / sanitized_query
    scrape_subdirs_config = config.settings.scraping.directories.scrape
    expected_scrape_base_dir = expected_query_dir / scrape_subdirs_config.base
    expected_html_dir = expected_scrape_base_dir / scrape_subdirs_config.html
    expected_logs_dir = expected_scrape_base_dir / scrape_subdirs_config.logs
    expected_pdfs_dir = expected_scrape_base_dir / scrape_subdirs_config.pdfs
    expected_images_dir = expected_scrape_base_dir / scrape_subdirs_config.images

    assert await aiofiles.os.path.isdir(expected_query_dir)
    assert await aiofiles.os.path.isdir(expected_scrape_base_dir)
    assert await aiofiles.os.path.isdir(expected_html_dir)
    assert await aiofiles.os.path.isdir(expected_logs_dir)
    assert await aiofiles.os.path.isdir(expected_pdfs_dir)
    assert await aiofiles.os.path.isdir(expected_images_dir)

    assert storage_scrape.query_dir == expected_query_dir
    assert storage_scrape.results_dir == expected_scrape_base_dir
    assert storage_scrape.scrape_html_dir == expected_html_dir
    assert storage_scrape.scrape_logs_dir == expected_logs_dir

@pytest.mark.asyncio
async def test_directory_structure_special_chars_query(storage_scrape_special_chars: ResultsStorage, temp_data_dir: Path):
    rs = storage_scrape_special_chars
    await rs._ensure_directories_ready() # Ensure directories are created
    assert rs.is_ready()
    sanitized_query_name = rs._sanitize_query(TEST_QUERY_SPECIAL_CHARS)
    expected_query_dir = temp_data_dir / sanitized_query_name
    scrape_subdirs_config = config.settings.scraping.directories.scrape
    expected_scrape_base_dir = expected_query_dir / scrape_subdirs_config.base
    expected_html_dir = expected_scrape_base_dir / scrape_subdirs_config.html
    expected_logs_dir = expected_scrape_base_dir / scrape_subdirs_config.logs
    expected_pdfs_dir = expected_scrape_base_dir / scrape_subdirs_config.pdfs
    expected_images_dir = expected_scrape_base_dir / scrape_subdirs_config.images

    assert await aiofiles.os.path.isdir(expected_query_dir)
    assert await aiofiles.os.path.isdir(expected_scrape_base_dir)
    assert await aiofiles.os.path.isdir(expected_html_dir)
    assert await aiofiles.os.path.isdir(expected_logs_dir)
    assert await aiofiles.os.path.isdir(expected_pdfs_dir)
    assert await aiofiles.os.path.isdir(expected_images_dir)

    assert rs.query_dir == expected_query_dir
    assert rs.results_dir == expected_scrape_base_dir
    assert rs.scrape_html_dir == expected_html_dir
    assert rs.scrape_logs_dir == expected_logs_dir
    assert rs.scrape_pdfs_dir == expected_pdfs_dir
    assert rs.scrape_images_dir == expected_images_dir

@pytest.mark.asyncio
async def test_save_and_load_search_results(storage_search: ResultsStorage):
    file_path_str = await storage_search.save_search_results(query=TEST_QUERY_NORMAL, results=TEST_URLS, metadata=TEST_METADATA)
    assert file_path_str is not None
    file_path = Path(file_path_str)
    assert await aiofiles.os.path.exists(file_path)

    loaded_data = await storage_search.load_results(file_path.name)
    assert loaded_data is not None
    assert loaded_data['query'] == TEST_QUERY_NORMAL
    assert loaded_data['urls'] == [str(url) for url in TEST_URLS]
    assert loaded_data['metadata'] == TEST_METADATA
    assert 'timestamp' in loaded_data

    latest_loaded_data = await storage_search.load_latest_results()
    assert latest_loaded_data == loaded_data

@pytest.mark.asyncio
async def test_save_search_results_validation_failure(storage_search: ResultsStorage):
    with pytest.raises(ValueError):
        await storage_search.save_search_results(query=TEST_QUERY_NORMAL, results=["not-a-url"], metadata=TEST_METADATA)

@pytest.mark.asyncio
async def test_save_scrape_html_content(storage_scrape: ResultsStorage):
    test_url = TEST_URLS[0]
    file_path_str = await storage_scrape.save_scrape_html_content(url=test_url, html_content=TEST_HTML_CONTENT)
    assert file_path_str is not None
    file_path = Path(file_path_str)
    assert await aiofiles.os.path.exists(file_path)

    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
        content = await f.read()
    assert content == TEST_HTML_CONTENT

    expected_html_dir = storage_scrape.scrape_html_dir
    assert file_path.parent == expected_html_dir

@pytest.mark.asyncio
async def test_save_scrape_metadata(storage_scrape: ResultsStorage):
    test_url = TEST_URLS[1]
    scrape_metadata = {
        "url": test_url,
        "title": "Test Title",
        "html_file_path": "some/path/to/file.html",
        **TEST_METADATA
    }
    file_path_str = await storage_scrape.save_scrape_metadata(url=test_url, metadata=scrape_metadata)
    assert file_path_str is not None
    file_path = Path(file_path_str)
    assert await aiofiles.os.path.exists(file_path)

    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
        content = await f.read()
        loaded_metadata = json.loads(content)
    assert loaded_metadata == scrape_metadata

    expected_logs_dir = storage_scrape.scrape_logs_dir
    assert file_path.parent == expected_logs_dir

@pytest.mark.asyncio
async def test_get_latest_results_no_files(storage_search: ResultsStorage, temp_data_dir: Path):
    await storage_search._ensure_directories_ready() # Ensure base directories are attempted
    sanitized_query = storage_search._sanitize_query(TEST_QUERY_NORMAL)
    results_dir = temp_data_dir / sanitized_query / config.settings.search.results.directory
    # The _ensure_directories_ready call in storage_search should have created this.
    # We still ensure it exists for the test's specific conditions.
    await aiofiles.os.makedirs(results_dir, exist_ok=True)
    # Delete any json files if they exist from previous runs or other tests
    for item_name in await aiofiles.os.listdir(results_dir):
        if item_name.endswith('.json'):
            await aiofiles.os.remove(results_dir / item_name)
    
    latest_file = await storage_search.get_latest_results_file()
    assert latest_file is None
    latest_data = await storage_search.load_latest_results()
    assert latest_data is None

@pytest.mark.asyncio
async def test_circuit_breaker_file_ops_exists(storage_search: ResultsStorage):
    assert hasattr(storage_search, 'file_breaker')
    assert storage_search.file_breaker.fail_max == config.settings.circuit_breaker.fail_max
    assert storage_search.file_breaker.reset_timeout == config.settings.circuit_breaker.reset_timeout

# Advanced circuit breaker test (optional, might need more setup)
# from unittest.mock import patch
# @pytest.mark.asyncio
# async def test_circuit_breaker_opens_and_prevents_writes(storage_search: ResultsStorage):
#     original_aio_open = aiofiles.open
#     open_calls = 0

#     async def mock_aio_open_for_cb(*args, **kwargs):
#         nonlocal open_calls
#         open_calls += 1
#         if open_calls <= storage_search.file_breaker.fail_max:
#             # print(f"Mock open call {open_calls}, raising OSError")
#             raise OSError("Simulated write error from mock_aio_open_for_cb")
#         # print(f"Mock open call {open_calls}, proceeding with original open (should be blocked by CB)")
#         return await original_aio_open(*args, **kwargs)

#     # Patch aiofiles.open within the utils.results_storage module where it's used
#     with patch('utils.results_storage.aiofiles.open', mock_aio_open_for_cb):
#         # Trigger failures to open the circuit breaker
#         for i in range(storage_search.file_breaker.fail_max):
#             # print(f"Attempting save_search_results, iteration {i+1} to trigger CB failure")
#             await storage_search.save_search_results(query=f"cb_test_fail_{i}", results=TEST_URLS, metadata=TEST_METADATA)
        
#         # print("Attempting save_search_results when CB should be open")
#         result_when_open = await storage_search.save_search_results(query="cb_test_blocked", results=TEST_URLS, metadata=TEST_METADATA)
#         assert result_when_open is None, "save_search_results should return None when CircuitBreakerError is caught"
#         assert open_calls == storage_search.file_breaker.fail_max, f"Expected {storage_search.file_breaker.fail_max} calls to aiofiles.open, got {open_calls}"
#         # Ensure circuit breaker is actually open
#         assert storage_search.file_breaker.state.name == "OPEN"

#         # To test reset, you might need to advance time if using time-based reset
#         # For pybreaker, if reset_timeout is set, it will transition to HALF_OPEN then CLOSED/OPEN
