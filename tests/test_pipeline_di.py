import pytest
from unittest.mock import patch, Mock
from md2kindle.app.pipeline import run
from md2kindle.core.models import PipelineContext, MangaContext, DownloadRange, DeliveryOptions

def test_pipeline_uses_injected_services():
    """Test that pipeline.run uses provided converter and deliverer."""
    mock_converter = Mock()
    mock_deliverer = Mock()
    
    # Mocking aggregated data and downloader to avoid side effects
    with patch("md2kindle.services.mangadex.downloader.download_manga", return_value=True), \
         patch("md2kindle.services.mangadex.api.get_manga_aggregate", return_value={}), \
         patch("md2kindle.services.mangadex.downloader.audit_and_cleanup"), \
         patch("os.makedirs"), \
         patch("os.path.exists", return_value=False), \
         patch("glob.glob", return_value=["test.cbz"]), \
         patch("shutil.rmtree"):
        
        manga = MangaContext(
            url="http://mangadex.org/title/123",
            title="Test Manga",
            author="Test Author",
            lang="en",
            manga_uuid=None
        )
        range_opt = DownloadRange(
            mode="c",
            start="1",
            end="1",
            skip_oneshots=False
        )
        delivery = DeliveryOptions(r2=False, telegram=False)
        
        ctx = PipelineContext(
            manga=manga,
            range=range_opt,
            delivery=delivery,
            silent=True
        )
        
        mock_converter.convert.return_value = ["output.mobi"]
        
        run(ctx, converter=mock_converter, deliverer=mock_deliverer)
        
        mock_converter.convert.assert_called_once()
        mock_deliverer.deliver.assert_called_once_with(["output.mobi"], ctx)
