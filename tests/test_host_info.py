from exotica.host_info import get_host_profile


def test_oracle_profile_reports_measured_ram_without_claiming_free_tier():
    profile = get_host_profile(
        {},
        sys_vendor="Oracle Corporation",
        memory_bytes=24 * 1024**3,
        cpu_cores=4,
    )

    assert profile.provider == "Oracle Cloud"
    assert profile.memory_gb == 24.0
    assert profile.cpu_cores == 4
    assert profile.tier == "Not verified"


def test_oracle_tier_is_only_shown_when_explicitly_configured():
    profile = get_host_profile(
        {"EXOTICA_CLOUD_PROVIDER": "oracle", "EXOTICA_CLOUD_TIER": "Always Free (configured)"},
        sys_vendor="Unknown",
        memory_bytes=24 * 1024**3,
        cpu_cores=4,
    )

    assert profile.provider == "Oracle Cloud"
    assert profile.tier == "Always Free (configured)"


def test_lavhost_marker_does_not_override_detected_provider():
    profile = get_host_profile(
        {"LAVHOST": "host-id"},
        sys_vendor="Oracle Corporation",
        memory_bytes=24 * 1024**3,
        cpu_cores=4,
    )

    assert profile.provider == "Oracle Cloud"
    assert profile.lavhost is True


def test_cpu_quota_can_be_overridden_for_cloud_vm():
    profile = get_host_profile(
        {
            "EXOTICA_CLOUD_PROVIDER": "Oracle Cloud",
            "EXOTICA_HOST_CPU_CORES": "4",
        },
        memory_bytes=24 * 1024**3,
    )

    assert profile.cpu_cores == 4.0
