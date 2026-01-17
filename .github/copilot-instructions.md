# Copilot 指南 — 仓库速览与代理指令

目的：帮助 AI 代理（Copilot / code assistant）快速进入本仓库并安全、可预测地修改代码。

- **项目类型**：单进程 Flask + SQLite 小型仓库管理应用，入口文件：`app.py`。
- **启动**：运行 `python app.py`，程序在首次运行会调用 `init_database()` 创建本地 `warehouse.db`（无需手动建库）。

关键位置和职责
- `app.py`：全部后端路由与 db 逻辑（主要路由：`/`、`/in_stock`、`/out_stock`、`/query_total`、`/query_in_history`、`/query_out_history`、`/api/get_stock_records`）。
- `templates/`：所有 Jinja2 模板（例如 `in_stock.html`, `out_stock.html`, `query.html`, `index.html`）。
- `static/laydate/`：第三方日期选择器资源（`laydate.js` 与样式）。

数据库与数据模型（可直接通过 `app.py` 可发现）
- 使用 SQLite（`warehouse.db`）与下列表：`warehouse_in`、`warehouse_out`、`total_inventory`。
- 约定字段（前端/后端必须一致）：`product_model`, `material`, `in_quantity`, `in_time`, `out_quantity`, `out_time`, `customer_unit`, `remarks`。

前端与后端集成要点
- 模板通过 `get_flashed_messages(with_categories=true)` 显示操作提示；后端使用 `flash(message, category)`，常用 category 为 `success` / `error`，前端把它们渲染为模态弹窗。
- 时间字段：前端使用 `laydate` 格式化为 `YYYY-MM-DD HH:MM:SS`，后端兼容 `YYYY-MM-DDTHH:MM:SS` 或 `YYYY-MM-DDTHH:MM`，失败回退为当前时间（见 `in_stock()` 与 `out_stock()` 的解析逻辑）。
- 异步接口：`POST /api/get_stock_records` 接收 JSON `{product_model, material}` 并返回合并的入/出记录，前端（`query.html`）通过该接口异步加载历史记录。

工程约定与常见模式
- 表单字段名必须与 `app.py` 中 `request.form[...]` 的 key 严格一致（例如：`product_model`, `material`, `in_quantity`, `out_quantity`, `customer_unit`, `in_time`, `out_time`, `remarks`）。
- 错误处理：路由内部以 try/except 捕获异常，`flash(..., 'error')` 并重定向；成功使用 `flash(..., 'success')`。
- 日志/调试：`app.py` 中存在多处 `print()` 调试输出，改动时注意不要移除关键调试行，除非用更合适的日志设施替代。

注意事项 / 已发现的潜在不一致
- 模板 `query.html` 使用分页链接 `/query_inventory?page=...`，但后端路由名为 `/query_total`（见 `app.py`）。修改路由或模板时请同步更新两侧。
- 直接运行会在当前工作目录生成 `warehouse.db`。CI/测试运行想要隔离需使用不同路径或临时 DB。

修改建议与示例
- 新增字段：
  - 在 `templates/*.html` 中添加对应 `<input name="FIELD">`。
  - 在 `app.py` 的路由处理处添加 `request.form['FIELD']` 并更新 SQL 插入/更新语句。
  - 如果影响 `total_inventory` 聚合逻辑，同步更新该表的 `SELECT/UPDATE/INSERT` 语句。
- 新增 API：保持 JSON contract，一律返回 `{'code': <int>, 'msg': <str>, ...}` 以符合现有前端解析逻辑。

快速参考（常用文件）
- 后端入口：`app.py`
- 模板目录：`templates/`（检查 `in_stock.html`, `out_stock.html`, `query.html`）
- 静态资源：`static/laydate/`

完成后请询问：
- 是否需要把分页路由统一为 `/query_inventory` 或改为 `/query_total`？
- 是否希望我把 `print()` 调试替换为 `logging`？

-- 结束