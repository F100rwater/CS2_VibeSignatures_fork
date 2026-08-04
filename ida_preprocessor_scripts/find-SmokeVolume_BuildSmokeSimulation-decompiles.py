#!/usr/bin/env python3
"""Preprocess script for find-SmokeVolume_BuildSmokeSimulation-decompiles skill."""

from ida_analyze_util import preprocess_common_skill

TARGET_STRUCT_MEMBER_NAMES = [
    "SmokeVolume_m_vecCenterOrigin",
    "SmokeVolume_m_flStartTime",
]


def _llm_decompile_spec(symbol_name, reference_stem):
    return {
        "symbol_name": symbol_name,
        "prompt_path": "prompt/call_llm_decompile.md",
        "reference_yaml_paths": [
            f"references/server/{reference_stem}.{{platform}}.yaml",
        ],
        "expected_result_sections": ["found_struct_offset"],
        "dependency_policy": {
            f"{reference_stem}.{{platform}}.yaml": "required",
        },
    }


# Windows writes these fields directly in BuildSmokeSimulation. Linux de-inlines
# that initialization into SmokeVolume_BuildSmokeSimulation_Initialize.
LLM_DECOMPILE_WINDOWS = [
    _llm_decompile_spec(symbol_name, "SmokeVolume_BuildSmokeSimulation")
    for symbol_name in TARGET_STRUCT_MEMBER_NAMES
]
LLM_DECOMPILE_LINUX = [
    _llm_decompile_spec(symbol_name, "SmokeVolume_BuildSmokeSimulation_Initialize")
    for symbol_name in TARGET_STRUCT_MEMBER_NAMES
]

GENERATE_YAML_DESIRED_FIELDS = [
    (
        symbol_name,
        [
            "struct_name",
            "member_name",
            "offset",
            "size",
            "offset_sig",
            "offset_sig_disp",
        ],
    )
    for symbol_name in TARGET_STRUCT_MEMBER_NAMES
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
    """Locate SmokeVolume center-origin and start-time member offsets via LLM decompile."""
    llm_decompile = LLM_DECOMPILE_WINDOWS if platform == "windows" else LLM_DECOMPILE_LINUX
    return await preprocess_common_skill(
        session=session,
        expected_outputs=expected_outputs,
        old_yaml_map=old_yaml_map,
        new_binary_dir=new_binary_dir,
        platform=platform,
        image_base=image_base,
        struct_member_names=TARGET_STRUCT_MEMBER_NAMES,
        llm_decompile_specs=llm_decompile,
        llm_config=llm_config,
        generate_yaml_desired_fields=GENERATE_YAML_DESIRED_FIELDS,
        debug=debug,
    )
