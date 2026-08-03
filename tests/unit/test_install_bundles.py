from b1.commands.install import DEFAULT_BUNDLES, resolve_bundles


def test_default_bundles_have_no_stale_module_names():
    # llc-auth0 was migrated to llc-gcp-identity-platform upstream in
    # b1CodingTool-LLC-lib; bundles must reference the current module name.
    for bundle_name, items in DEFAULT_BUNDLES.items():
        assert "llc-auth0" not in items, (
            f"bundle '{bundle_name}' references retired module 'llc-auth0'"
        )


def test_llc_bundle_includes_gcp_identity_platform():
    resolved = resolve_bundles(["llc"], custom_bundles={})
    assert "llc-gcp-identity-platform" in resolved
