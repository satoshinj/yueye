# AGENTS.md · 阅页 Yueye

## 项目

- 名称：**阅页 Yueye**
- 一句话：把你已经有权阅读的在线文档，收成可检索的离线副本。
- 仓库：`https://github.com/bitcoinjohnny/yueye`（**public**）
- 栈：Python 3.12 · Playwright · PySide6 · PyInstaller

## 硬性约定

1. **所有 `page.evaluate` 必须返回 `JSON.stringify(...)` 字符串**，用 `sites.jseval()` 解析。
   目标站会篡改结构化序列化，直接返回数组/对象一律得 `None` 且不报错。
2. **不用 `querySelector('a, b, c')` 表达优先级** —— 逗号列表按文档顺序返回。
   用 `sites.pick_js([...])` 按优先级逐个选。
3. **有头模式是默认**，不要改成无头：站点会识别无头并降级投喂内容，滑块也需人工完成。
4. **冻结环境下不能用 `Path(__file__).parent` 定位输出目录**，用 `config.app_dir()`。
5. **打包不能排除 `lxml`** —— `python-docx` 依赖它，排掉后 Word 导出在运行时才崩。

## 合规口径（对外表述必须一致）

- 只处理使用者**已登录、有权查看**的内容；权限外的内容服务端不下发。
- 不解密内容保护、不破解验证码、不代替使用者完成滑块。
- 「还剩 N 页未读」是**软信号，不据此停止**（它是异步引导浮层，出现不等于没权限）。
  README / DISCLAIMER / 说明页三处表述必须与此实现一致，**不得**写成「见提示即停」。
- 禁止表述：「批量下载」「可下载的网站清单」「一键扒站」「绕过/突破/解锁」。
- 站点一律写成**带验证程度的兼容性表**，并注明「除道客巴巴外未逐站验收」。

## 交付纪律

- **未实际验证不说「已修复」「已通过」**。改完必须跑 `python tests/test_engine.py`。
- 打包必须以 `selftest.exe` 通过为准 —— **GUI 能启动不代表能抓取**。
- 提交前扫描：不得含 `run.log` / `crash.log` / 导出 PDF / 本机绝对路径 / 真实文档 URL。
- 不静默降级：抓不全必须明确停止并说明原因。

## 常用命令

```bash
python tests/test_engine.py          # 8 组行为测试，不联网
python e2e_test.py <URL>             # 真实站点，URL 必须显式传入
build.bat                            # 打包 + 自检
```
