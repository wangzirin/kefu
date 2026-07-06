# H2W-DATA2R4 资料包预检 API 与前端入口

## 结论

- 阶段状态：`material_precheck_api_ui_ready`
- 阻断项：`0` 个

## 完成内容

- 新增客户资料包内存预检接口，用于校验知识资料 CSV、试跑问题 CSV 和资料说明 JSON。
- 试点准备页新增资料预检入口，预检结果展示资料行数、问题数、知识类型和阻断项。
- 预检不保存原始资料，不标记真实客户资料已就绪，不开启真实外发。

## 已验证命令

- frontend: npm run typecheck && npm run build
- backend: PYTHONPATH=backend backend/.venv/bin/python -m pytest backend/tests/test_pilot_api.py backend/tests/test_p3_06u_26h2w_sealed_pilot_package_gates.py -q

## 证据文件

- output/p3_06u_26h2w_data2r4_material_precheck_api_ui/summary.json
- docs/P3-06U-26H2W_DATA2R4_MATERIAL_PRECHECK_API_UI.md

## 不可承诺

- 正式客户验收签收
- 真实平台自动外发
- 企业微信、公众号、抖音、淘宝、京东、拼多多等真实渠道接通
- 生产 SLA 承诺
- 已签名 dmg/exe 安装器
- RPA 或个人号外挂正式交付

## 阻断项

- 无
