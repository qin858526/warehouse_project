import math  # 新增：用于计算总页数
# （其他原有导入：Flask、sqlite3、datetime等保留）

# 你的库存查询路由（原query_inventory函数）+ 分页功能
@app.route('/query_inventory', methods=['GET'])
def query_inventory():  # 函数名保持你的query_inventory，不改动
    # 1. 获取分页参数：页码（默认第1页）、每页显示10条（可自定义）
    page = request.args.get('page', 1, type=int)  # 从URL获取?page=X参数
    per_page = 10  # 每页固定显示10条，可改成20/50

    # 2. 计算分页偏移量（OFFSET）：(页码-1)*每页条数
    offset = (page - 1) * per_page

    # 3. 数据库查询：当前页数据 + 总数据条数（适配你的表名）
    conn = get_db_connection()
    # 查当前页数据：LIMIT限制条数，OFFSET跳过前N条（核心分页逻辑）
    stocks = conn.execute(
        'SELECT * FROM total_inventory LIMIT ? OFFSET ?',  # 你的库存表名不变
        (per_page, offset)
    ).fetchall()
    # 查总条数：用于计算总页数
    total_count = conn.execute('SELECT COUNT(*) FROM total_inventory').fetchone()[0]
    conn.close()

    # 4. 计算总页数（向上取整，比如11条=2页）
    total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1

    # 5. 传递参数到你的query.html（模板名不变）
    return render_template(
        'query.html',  # 你的库存查询页模板名：query.html
        stocks=stocks,  # 库存数据（模板里遍历的变量名不变）
        current_page=page,  # 新增：当前页码
        total_pages=total_pages,  # 新增：总页数
        per_page=per_page  # 新增：每页条数（可选）
    )