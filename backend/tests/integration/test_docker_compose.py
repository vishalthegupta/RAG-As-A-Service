"""Tests for Docker Compose configuration"""
from __future__ import annotations

import pytest
import yaml
import os


def test_docker_compose_file_exists():
    """Test that docker-compose.yml exists"""
    compose_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "docker-compose.yml"
    )
    assert os.path.exists(compose_path), "docker-compose.yml not found"


def test_docker_compose_has_all_services():
    """Test that docker-compose.yml has all 5 required services"""
    compose_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "docker-compose.yml"
    )
    
    with open(compose_path, 'r') as f:
        compose_config = yaml.safe_load(f)
    
    assert "services" in compose_config
    services = compose_config["services"]
    
    # Check all required services exist
    required_services = ["api", "worker", "db", "redis"]
    for service in required_services:
        assert service in services, f"Service '{service}' not found in docker-compose.yml"


def test_docker_compose_has_volumes():
    """Test that docker-compose.yml defines required volumes"""
    compose_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "docker-compose.yml"
    )
    
    with open(compose_path, 'r') as f:
        compose_config = yaml.safe_load(f)
    
    assert "volumes" in compose_config
    volumes = compose_config["volumes"]
    
    # Check required volumes
    required_volumes = ["postgres_data", "chroma_data", "upload_data", "model_cache"]
    for volume in required_volumes:
        assert volume in volumes, f"Volume '{volume}' not found in docker-compose.yml"


def test_env_example_exists():
    """Test that .env.example exists"""
    env_example_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        ".env.example"
    )
    assert os.path.exists(env_example_path), ".env.example not found"


def test_env_example_contains_required_variables():
    """Test that .env.example contains all required variable names"""
    env_example_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        ".env.example"
    )
    
    with open(env_example_path, 'r') as f:
        content = f.read()
    
    # Check for required variables
    required_vars = [
        "JWT_SECRET_KEY",
        "DATABASE_URL",
        "SYNC_DATABASE_URL",
        "REDIS_URL",
        "GROQ_API_KEY",
    ]
    
    for var in required_vars:
        assert var in content, f"Required variable '{var}' not found in .env.example"


def test_gitignore_exists():
    """Test that .gitignore exists"""
    gitignore_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        ".gitignore"
    )
    assert os.path.exists(gitignore_path), ".gitignore not found"


def test_gitignore_contains_required_entries():
    """Test that .gitignore includes required entries"""
    gitignore_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        ".gitignore"
    )
    
    with open(gitignore_path, 'r') as f:
        content = f.read()
    
    # Check for required entries
    required_entries = [
        ".env",
        "__pycache__",
        "model_cache",
        "chroma_data",
        "uploads",
    ]
    
    for entry in required_entries:
        assert entry in content, f"Required entry '{entry}' not found in .gitignore"
