#!/usr/bin/env python3
"""Preprocess script for find-CNetworkClientService_OnEventMapCallbacks-engine skill."""

from ida_analyze_util import preprocess_common_skill

SOURCE_YAML_STEM = "CNetworkClientService_RegisterEventMapInternal"

TARGET_FUNCTION_NAMES = [
    "RegisterEventListener_Abstract",
    "CNetworkClientService_OnClientAdvanceTick",
    "CNetworkClientService_OnClientPostAdvanceTick",
]

LLM_DECOMPILE = [
    {
        "symbol_name": "RegisterEventListener_Abstract",
        "prompt_path": "prompt/call_llm_decompile.md",
        "reference_yaml_paths": [
            f"references/engine/{SOURCE_YAML_STEM}.{{platform}}.yaml",
        ],
        "expected_result_sections": ["found_call"],
        "dependency_policy": {
            f"{SOURCE_YAML_STEM}.{{platform}}.yaml": "required",
        },
    },
    {
        "symbol_name": "CNetworkClientService_OnClientAdvanceTick",
        "prompt_path": "prompt/call_llm_decompile.md",
        "reference_yaml_paths": [
            f"references/engine/{SOURCE_YAML_STEM}.{{platform}}.yaml",
        ],
        "expected_result_sections": ["found_funcptr"],
        "dependency_policy": {
            f"{SOURCE_YAML_STEM}.{{platform}}.yaml": "required",
        },
    },
    {
        "symbol_name": "CNetworkClientService_OnClientPostAdvanceTick",
        "prompt_path": "prompt/call_llm_decompile.md",
        "reference_yaml_paths": [
            f"references/engine/{SOURCE_YAML_STEM}.{{platform}}.yaml",
        ],
        "expected_result_sections": ["found_funcptr"],
        "dependency_policy": {
            f"{SOURCE_YAML_STEM}.{{platform}}.yaml": "required",
        },
    },
]

_SIGNED_GENERATE_FIELDS = [
    "func_name",
    "func_sig",
    "func_va",
    "func_rva",
    "func_size",
]

GENERATE_YAML_DESIRED_FIELDS = [
    ("RegisterEventListener_Abstract", _SIGNED_GENERATE_FIELDS),
    ("CNetworkClientService_OnClientAdvanceTick", _SIGNED_GENERATE_FIELDS),
    # MSVC ICF folds the empty OnClientPostAdvanceTick callback into
    # _guard_check_icall_nop, whose two-byte body is shared by many stubs. Allow the
    # signature generator to extend beyond the function boundary to regain uniqueness.
    (
        "CNetworkClientService_OnClientPostAdvanceTick",
        [
            "func_name",
            "func_sig",
            "func_sig_allow_across_function_boundary: true",
            "func_va",
            "func_rva",
            "func_size",
        ],
    ),
]


async def preprocess_skill(
    session,
    skill_name,
    expected_outputs,
    old_yaml_map,
    new_binary_dir,
    platform,
    image_base,
    llm_config=None,
    debug=False,
):
    """Resolve RegisterEventListener_Abstract and event callbacks through decompilation."""
    return await preprocess_common_skill(
        session=session,
        expected_outputs=expected_outputs,
        old_yaml_map=old_yaml_map,
        new_binary_dir=new_binary_dir,
        platform=platform,
        image_base=image_base,
        func_names=TARGET_FUNCTION_NAMES,
        llm_decompile_specs=LLM_DECOMPILE,
        llm_config=llm_config,
        generate_yaml_desired_fields=GENERATE_YAML_DESIRED_FIELDS,
        debug=debug,
    )
