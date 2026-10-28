#!/usr/bin/env python3
"""reports.py testleri: kişisel veri temizleme, rapor oluşturma, gönderme kuyruğu."""
import json
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
import reports

def test_scrub():
    """Kişisel veri temizleme."""
    text = "TD2P-AAAA.BBBB C:\\Users\\Soner\\Desktop\\x.log admin@example.com ghp_abcdefghijklmnopqrst123"
    clean = reports.scrub(text)
    assert "AAAA" not in clean
    assert "Soner" not in clean
    assert "admin" not in clean
    assert "abcdefghijklmnopqrst" not in clean
    assert "<license>" in clean
    assert "<user>" in clean
    assert "<email>" in clean
    assert "<token>" in clean
    print("✓ scrub")

def test_build():
    """Rapor oluştur."""
    try:
        reports.build("invalid_type", "test", "test")
    except ValueError as e:
        assert str(e) == "type"
    
    try:
        reports.build("bug", "x", "test")
    except ValueError as e:
        assert str(e) == "title"
    
    try:
        reports.build("bug", "title", "x")
    except ValueError as e:
        assert str(e) == "body"
    
    report = reports.build("bug", "Item wrong", "Test description longer",
                           contact="user#123", app_version="5.0.6", lang="tr",
                           system={"os": "Windows 11"}, log="test log", card="Striker")
    
    assert report["type"] == "bug"
    assert report["title"] == "Item wrong"
    assert report["contact"] == "user#123"
    assert report["app_version"] == "5.0.6"
    print("✓ build")

def test_store():
    """Rapor depolama."""
    with tempfile.TemporaryDirectory() as tmpdir:
        store = reports.Store(tmpdir)
        
        payload = {"type": "bug", "title": "Test", "body": "Description"}
        
        # Gönder (başarısız, çünkü URL yok)
        status, rec = store.send("http://invalid", payload)
        assert status == "queued"
        assert len(store.queue) == 1
        
        # Gönderilenler boş
        assert len(store.sent) == 0
        
        # Çıkış ve ön
        store.refresh("http://invalid", "test_client")
        print("✓ store")

def test_system_info():
    """Sistem bilgisi."""
    info = reports.system_info("5.0.6")
    assert "os" in info
    assert "python" in info
    assert "app" in info
    assert info["app"] == "5.0.6"
    print("✓ system_info")

def test_log_tail():
    """Günlük dosyasından son satırlar."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        for i in range(150):
            f.write(f"log line {i}\n")
        f.flush()
        path = f.name
    
    tail = reports.log_tail(path, lines=10)
    assert "log line 149" in tail
    assert "log line 140" in tail
    assert "log line 139" not in tail
    
    Path(path).unlink()
    print("✓ log_tail")

if __name__ == "__main__":
    test_scrub()
    test_build()
    test_store()
    test_system_info()
    test_log_tail()
    print("\nRESULT: PASS")
