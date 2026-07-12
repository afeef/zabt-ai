# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2025-2026 Afeef Janjua
import io
import json
from unittest.mock import MagicMock

from PIL import Image

from zabt_vision.pipeline.upload import upload_keyframe_jpg, upload_raw_output_json


def test_upload_keyframe_uploads_high_quality_jpeg():
    s3 = MagicMock()
    img = Image.new("RGB", (640, 480), color="red")
    key = upload_keyframe_jpg(
        client=s3,
        bucket="zabt",
        owner_id="u1",
        meeting_id="m1",
        segment_id="seg1",
        image=img,
    )
    assert key == "users/u1/meetings/m1/visual/seg1.jpg"
    s3.put_object.assert_called_once()
    kwargs = s3.put_object.call_args.kwargs
    assert kwargs["Bucket"] == "zabt"
    assert kwargs["Key"] == key
    assert kwargs["ContentType"] == "image/jpeg"
    body = kwargs["Body"]
    # Re-decode from upload bytes — should be a valid JPEG
    decoded = Image.open(io.BytesIO(body))
    assert decoded.size == (640, 480)


def test_upload_raw_output_json():
    s3 = MagicMock()
    payload = {"segments": [], "model": "qwen3-vl:8b-thinking"}
    key = upload_raw_output_json(
        client=s3,
        bucket="zabt",
        owner_id="u1",
        meeting_id="m1",
        payload=payload,
    )
    assert key == "users/u1/meetings/m1/visual/raw_output.json"
    kwargs = s3.put_object.call_args.kwargs
    assert kwargs["ContentType"] == "application/json"
    decoded = json.loads(kwargs["Body"])
    assert decoded == payload
