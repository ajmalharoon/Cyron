"""Schema-level checks for target/scan payload validation. These don't hit a
real database — see the project README for running the full stack to do an
end-to-end check."""
import pytest
from pydantic import ValidationError

from app.schemas.scan import ScanCreate
from app.schemas.target import TargetCreate


def test_target_create_requires_a_known_type():
    with pytest.raises(ValidationError):
        TargetCreate(value="example.com", type="not-a-real-type")


def test_target_create_accepts_domain():
    t = TargetCreate(value="example.com", type="domain")
    assert t.value == "example.com"


def test_scan_create_requires_at_least_one_mode():
    with pytest.raises(ValidationError):
        ScanCreate(target="example.com", modes=[], authorized=True)


def test_scan_create_valid_payload():
    s = ScanCreate(target="example.com", modes=["active"], authorized=True)
    assert s.modes == ["active"]


def test_scan_create_accepts_tool_selection():
    s = ScanCreate(
        target="example.com",
        modes=["active"],
        authorized=True,
        tools={"net": ["Nmap", "Naabu"]},
    )
    assert s.tools == {"net": ["Nmap", "Naabu"]}


def test_scan_create_tools_defaults_to_none():
    s = ScanCreate(target="example.com", modes=["active"], authorized=True)
    assert s.tools is None
