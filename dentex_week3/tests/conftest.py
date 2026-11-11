"""Shared fixtures for the dentex_week3 unit tests.

The tests never load real weights: ``ultralytics`` is replaced with a stub
before ``inference_pipeline`` is imported, and each test installs fake
detectors that return the boxes it needs. They run in CI without torch.
"""

import os
import sys
import types

import numpy as np
import pytest

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(ROOT, "production"))
sys.path.insert(0, os.path.join(ROOT, "api"))

if "ultralytics" not in sys.modules:
    stub = types.ModuleType("ultralytics")

    class _UnusedYOLO:  # the tests inject fakes into _MODELS instead
        def __init__(self, *args, **kwargs):
            raise RuntimeError("real YOLO must not load in unit tests")

    stub.YOLO = _UnusedYOLO
    sys.modules["ultralytics"] = stub

import inference_pipeline as ip  # noqa: E402


class _Scalar:
    def __init__(self, value):
        self._value = value

    def item(self):
        return self._value


class _Coords:
    def __init__(self, xyxy):
        self._xyxy = np.array(xyxy, dtype=float)

    def cpu(self):
        return self

    def numpy(self):
        return self._xyxy


class FakeBox:
    def __init__(self, cls, conf, xyxy):
        self.cls = [_Scalar(cls)]
        self.conf = [_Scalar(conf)]
        self.xyxy = [_Coords(xyxy)]


class FakeModel:
    """Mimics ``YOLO(...).predict(...)[0].boxes``; ``boxes`` is (cls, conf, xyxy)."""

    def __init__(self, boxes=(), error=None):
        self.boxes = [FakeBox(*b) for b in boxes]
        self.error = error
        self.calls = []

    def predict(self, source, imgsz, conf, verbose):
        if self.error:
            raise self.error
        self.calls.append({"imgsz": imgsz, "conf": conf})
        kept = [b for b in self.boxes if b.conf[0].item() >= conf]
        return [types.SimpleNamespace(boxes=kept)]


def tooth(fdi, conf, xyxy):
    """Tooth-detector box for an FDI number: class index = (quadrant-1)*8 + (tooth-1)."""
    q, t = int(str(fdi)[0]), int(str(fdi)[1])
    return ((q - 1) * 8 + (t - 1), conf, xyxy)


@pytest.fixture
def models(monkeypatch):
    """Install fake detectors; returns a setter so each test chooses its boxes."""
    monkeypatch.setattr(ip, "_MODELS", {})
    # Force the plain missing-teeth rule; the ResNet classifier is not under test.
    monkeypatch.setattr(ip, "_MISSING_MODEL", {"model": None})
    monkeypatch.delenv("DENTEX_CARIES_VERIFIER", raising=False)

    def install(teeth=(), lesions=(), findings=(), findings_error=None):
        ip._MODELS["tooth"] = FakeModel(teeth)
        ip._MODELS["disease"] = FakeModel(lesions)
        ip._MODELS["findings"] = FakeModel(findings, error=findings_error)
        return ip._MODELS

    return install


@pytest.fixture
def image():
    return np.zeros((1000, 2000, 3), dtype=np.uint8)
