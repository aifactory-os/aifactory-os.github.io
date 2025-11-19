def test_orchestrator_import():
    """Test that orchestrator can be imported"""
    try:
        from core import orchestrator
        assert orchestrator.main_workflow
    except ImportError:
        assert False, "Cannot import orchestrator"

def test_logger_import():
    """Test that logger can be imported"""
    try:
        from core import logger
        assert logger.log_success
    except ImportError:
        assert False, "Cannot import logger"