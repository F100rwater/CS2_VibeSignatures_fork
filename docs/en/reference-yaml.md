[Back to README](../../README.md) | [中文](../zh-CN/reference-yaml.md)

# Reference YAML for `LLM_DECOMPILE`

Reference YAML files are stored at:

```text
ida_preprocessor_scripts/references/<module>/<func_name>.<platform>.yaml
```

## Preparation

1. Confirm the target function already has a current-version YAML with `func_va`, or can be resolved in IDA by symbol name or alias from `configs/<GAMEVER>.yaml`.
2. Run the standalone CLI:

   ```bash
   uv run generate_reference_yaml.py -gamever 14141 -module engine -platform windows -func_name CNetworkGameClient_RecordEntityBandwidth -mcp_host 127.0.0.1 -mcp_port 13337
   ```

   To auto-start `idalib-mcp`, run:

   ```bash
   uv run generate_reference_yaml.py -gamever 14141 -module engine -platform windows -func_name CNetworkGameClient_RecordEntityBandwidth -auto_start_mcp -binary bin/14141/engine/engine2.dll
   ```

3. Check the generated YAML:

   - `func_va` is credible.
   - `disasm_code` is non-empty and matches the target function semantics.
   - `procedure` matches the expected semantics when available. It can be empty when Hex-Rays is unavailable.
   - `func_name` only confirms the output file targets the requested canonical name; it does not prove address-resolution correctness.

4. Wire the file into the target `find-*.py` `LLM_DECOMPILE` specification:

   - Repository path: `ida_preprocessor_scripts/references/<module>/<func_name>.<platform>.yaml`
   - Relative path inside `LLM_DECOMPILE`: `references/<module>/<func_name>.<platform>.yaml`
   - Every entry must explicitly declare its accepted result sections:

     ```python
     {
         "symbol_name": "INetworkMessages_FindNetworkGroup",
         "prompt_path": "prompt/call_llm_decompile.md",
         "reference_yaml_paths": [
             "references/engine/CNetworkGameClient_RecordEntityBandwidth.{platform}.yaml",
         ],
         "expected_result_sections": ["found_vcall"],
     }
     ```

Valid result sections are `found_call`, `found_vcall`, `found_funcptr`, `found_gv`, and `found_struct_offset`.

Use multiple `reference_yaml_paths` for one symbol instead of repeating the same symbol in multiple specifications. `LLM_DECOMPILE` uses the shared Analyzer flags `-llm_model`, `-llm_apikey`, `-llm_baseurl`, `-llm_temperature`, `-llm_effort`, and `-llm_fake_as`.
