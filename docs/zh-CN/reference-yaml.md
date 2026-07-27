[返回中文 README](../../README_CN.md) | [English](../en/reference-yaml.md)

# `LLM_DECOMPILE` reference YAML

reference YAML 存放在：

```text
ida_preprocessor_scripts/references/<module>/<func_name>.<platform>.yaml
```

## 准备步骤

1. 确认目标函数已有包含 `func_va` 的当前版本 YAML，或可通过 `configs/<GAMEVER>.yaml` 中的 symbol name 或 alias 在 IDA 中定位。
2. 运行独立 CLI：

   ```bash
   uv run generate_reference_yaml.py -gamever 14141 -module engine -platform windows -func_name CNetworkGameClient_RecordEntityBandwidth -mcp_host 127.0.0.1 -mcp_port 13337
   ```

   如需自动启动 `idalib-mcp`：

   ```bash
   uv run generate_reference_yaml.py -gamever 14141 -module engine -platform windows -func_name CNetworkGameClient_RecordEntityBandwidth -auto_start_mcp -binary bin/14141/engine/engine2.dll
   ```

3. 检查生成的 YAML：

   - `func_va` 可信。
   - `disasm_code` 非空且与目标函数语义匹配。
   - `procedure` 在可用时与预期语义一致；Hex-Rays 不可用时允许为空。
   - `func_name` 只能确认输出文件对应请求的 canonical name，不能单独证明地址解析正确。

4. 将文件接入目标 `find-*.py` 的 `LLM_DECOMPILE` 配置：

   - 仓库路径：`ida_preprocessor_scripts/references/<module>/<func_name>.<platform>.yaml`
   - `LLM_DECOMPILE` 中的相对路径：`references/<module>/<func_name>.<platform>.yaml`
   - 每个配置项必须显式声明允许的结果 section：

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

合法 section 包括 `found_call`、`found_vcall`、`found_funcptr`、`found_gv` 和 `found_struct_offset`。

同一 symbol 需要多个 reference 时，应写入同一个 `reference_yaml_paths` 列表，不要重复声明 spec。`LLM_DECOMPILE` 复用 Analyzer 的共享参数：`-llm_model`、`-llm_apikey`、`-llm_baseurl`、`-llm_temperature`、`-llm_effort` 和 `-llm_fake_as`。
