"""
Unit tests for Demo Data Generator
"""
import pytest
from core.demo_data import DEMO_BUCKETS, generate_bucket_objects, get_demo_dataset

def test_demo_buckets_structure():
    assert len(DEMO_BUCKETS) >= 4
    for b in DEMO_BUCKETS:
        assert "name" in b
        assert "region" in b
        assert "primary_type" in b

def test_generate_bucket_objects():
    bucket_name = DEMO_BUCKETS[0]["name"]
    objs = generate_bucket_objects(bucket_name, count=50)
    assert len(objs) == 50
    for o in objs:
        assert "Key" in o
        assert "Size" in o
        assert "StorageClass" in o
        assert "AgeDays" in o
        assert o["Size"] > 0
        assert o["AgeDays"] >= 0

def test_get_demo_dataset():
    data = get_demo_dataset()
    assert "buckets" in data
    assert "objects" in data
    assert "dataframe" in data
    assert len(data["objects"]) > 500
    assert not data["dataframe"].empty
