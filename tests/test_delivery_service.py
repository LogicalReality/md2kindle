from md2kindle.delivery import service
from md2kindle.models import PipelineParams


def make_params(**overrides):
    data = {
        "url": "https://mangadex.org/title/123",
        "title": "TestManga",
        "lang": "es-la",
        "mode": "v",
        "start": "1",
        "end": "1",
        "author": "TestAuthor",
        "manga_uuid": "123",
        "skip_oneshots": False,
        "silent": True,
        "telegram": False,
        "r2": False,
    }
    data.update(overrides)
    return PipelineParams(**data)


def test_deliver_files_no_files_does_nothing(monkeypatch):
    calls = []
    monkeypatch.setattr(service, "send_to_usb", lambda *args: calls.append(args))

    service.deliver_files([], make_params())

    assert calls == []


def test_deliver_files_logs_usb_success(monkeypatch):
    calls = []
    monkeypatch.setattr(service, "send_to_usb", lambda *args: True)
    monkeypatch.setattr(service, "format_manga_title", lambda *args: ("Manga", "Vol. 1"))
    monkeypatch.setattr(service, "log_download", lambda *args: calls.append(args))

    service.deliver_files(["book.mobi"], make_params())

    assert calls == [("Manga", "Vol. 1", "es-la", "book.mobi", "usb")]


def test_deliver_files_explicit_r2_sends_link_and_logs(monkeypatch):
    calls = []
    monkeypatch.setattr(service, "send_to_usb", lambda *args: False)
    monkeypatch.setattr(service, "format_manga_title", lambda *args: ("Manga", "Vol. 1"))
    monkeypatch.setattr(service, "send_to_r2", lambda *args: "https://example.test/book")
    monkeypatch.setattr(service, "send_message", lambda msg, **kwargs: calls.append(("msg", msg)))
    monkeypatch.setattr(service, "log_download", lambda *args: calls.append(("log", args)))
    monkeypatch.setattr(service.os.path, "getsize", lambda _: 1024 * 1024)

    service.deliver_files(["book.mobi"], make_params(r2=True))

    assert any(c[0] == "msg" and "https://example.test/book" in c[1] for c in calls)
    assert any(c[0] == "log" and c[1] == ("Manga", "Vol. 1", "es-la", "book.mobi", "r2") for c in calls)


def test_deliver_files_explicit_telegram_sends_and_logs(monkeypatch):
    calls = []
    monkeypatch.setattr(service, "send_to_usb", lambda *args: False)
    monkeypatch.setattr(service, "send_to_telegram", lambda path: calls.append(("telegram", path)))
    monkeypatch.setattr(service, "format_manga_title", lambda *args: ("Manga", "Vol. 1"))
    monkeypatch.setattr(service, "log_download", lambda *args: calls.append(("log", args)))

    service.deliver_files(["book.mobi"], make_params(telegram=True))

    assert calls == [
        ("telegram", "book.mobi"),
        ("log", ("Manga", "Vol. 1", "es-la", "book.mobi", "telegram")),
    ]


def test_deliver_files_interactive_fallback_to_r2(monkeypatch):
    calls = []
    monkeypatch.setattr(service.sys, "argv", ["md2kindle"])
    monkeypatch.setattr(service, "send_to_usb", lambda *args: False)
    monkeypatch.setattr(service, "format_manga_title", lambda *args: ("Manga", "Vol. 1"))
    monkeypatch.setattr(service, "send_to_r2", lambda *args: "https://example.test/book")
    monkeypatch.setattr(service, "send_message", lambda msg, **kwargs: calls.append(("msg", msg)))
    monkeypatch.setattr(service, "log_download", lambda *args: calls.append(("log", args)))
    monkeypatch.setattr(service.os.path, "getsize", lambda _: 1024 * 1024)

    service.deliver_files(["book.mobi"], make_params(), input_func=lambda _: "")

    assert any(c[0] == "msg" and "https://example.test/book" in c[1] for c in calls)
    assert any(c[0] == "log" and c[1] == ("Manga", "Vol. 1", "es-la", "book.mobi", "r2") for c in calls)


def test_deliver_files_interactive_fallback_to_telegram(monkeypatch):
    calls = []
    monkeypatch.setattr(service.sys, "argv", ["md2kindle"])
    monkeypatch.setattr(service, "send_to_usb", lambda *args: False)
    monkeypatch.setattr(service, "send_to_telegram", lambda path: calls.append(("telegram", path)))
    monkeypatch.setattr(service, "format_manga_title", lambda *args: ("Manga", "Vol. 1"))
    monkeypatch.setattr(service, "log_download", lambda *args: calls.append(("log", args)))

    service.deliver_files(["book.mobi"], make_params(), input_func=lambda _: "t")

    assert calls == [
        ("telegram", "book.mobi"),
        ("log", ("Manga", "Vol. 1", "es-la", "book.mobi", "telegram")),
    ]
