# macOS 图标候选说明

当前阶段只固定图标规范和候选位置，不生成正式 `.icns`。

## 候选规范

- 名称：万法常世客服中台。
- 风格：简洁、可识别、适合本地业务工具。
- 最终文件建议：`WanfaCustomerService.app/Contents/Resources/AppIcon.icns`。
- `Info.plist` 后续签名安装包阶段再加入 `CFBundleIconFile`。

## 边界

- 现在不是正式签名 `.dmg`。
- 不因为存在 `.app` 骨架就宣称完成原生安装器。
- 图标文件不得包含客户商标、客户数据或平台图标授权风险素材。
