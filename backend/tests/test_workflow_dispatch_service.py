from underlytics_api.services import workflow_dispatch_service


def test_async_dispatch_disabled_without_pubsub_configuration(monkeypatch):
    monkeypatch.setattr(workflow_dispatch_service, "WORKFLOW_EXECUTION_MODE", "sync")
    monkeypatch.setattr(workflow_dispatch_service, "PUBSUB_WORKFLOW_TOPIC", None)

    assert workflow_dispatch_service.use_async_workflow_dispatch() is False
