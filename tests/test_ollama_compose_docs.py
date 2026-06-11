from pathlib import Path


def test_compose_defines_local_ollama_service() -> None:
    text = Path("compose.yaml").read_text(encoding="utf-8")

    assert "ollama:" in text
    assert "image: ollama/ollama:latest" in text
    assert '"11434:11434"' in text
    assert "ollama-data:/root/.ollama" in text
    assert "OLLAMA_HOST: 0.0.0.0:11434" in text
    assert "- CMD" in text
    assert "- ollama" in text
    assert "- list" in text


def test_windows_setup_documents_local_model_and_bypass() -> None:
    text = Path("docs/windows-setup.md").read_text(encoding="utf-8")

    assert "Docker Desktop" in text
    assert "qwen2.5:1.5b-instruct" in text
    assert "docker compose up -d ollama" in text
    assert "manual bypass" in text
    assert "http://localhost:11434" in text
