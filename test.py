import math
from flask import Flask, render_template, request, flash, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key'  # 保持你原有密钥

# 数据库连接函数（保持你原有逻辑）
def get_db_connection():
    conn = sqlite3.connect('your_database.db')  # 替换为你的数据库名
    conn.row_factory = sqlite3.Row
    return conn

# 库存查询 + 分页功能
@app.route('/stock_query', methods=['GET'])
def stock_query():
    # 1. 获取分页参数：页码（默认第1页）、每页条数（固定10条）
    page = request.args.get('page', 1, type=int)  # 从URL获取page参数，默认1
    per_page = 10  # 每页显示10条，可自定义（比如20）

    # 2. 计算分页偏移量（OFFSET）：(页码-1)*每页条数
    offset = (page - 1) * per_page

    # 3. 查询当前页数据 + 总数据条数
    conn = get_db_connection()
    # 当前页数据：LIMIT 限制条数，OFFSET 跳过前N条
    stocks = conn.execute(
        'SELECT * FROM total_inventory LIMIT ? OFFSET ?',
        (per_page, offset)
    ).fetchall()
    # 总数据条数：用于计算总页数
    total_count = conn.execute('SELECT COUNT(*) FROM total_inventory').fetchone()[0]
    conn.close()

    # 4. 计算总页数（向上取整，比如11条=2页）
    total_pages = math.ceil(total_count / per_page)

    # 5. 传递给前端：当前页数据、当前页码、总页数
    return render_template(
        'stock_query.html',
        stocks=stocks,
        current_page=page,
        total_pages=total_pages,
        per_page=per_page
    )

# 入库记录查询 + 分页（同理）
@app.route('/in_stock_query', methods=['GET'])
def in_stock_query():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    conn = get_db_connection()
    in_records = conn.execute(
        'SELECT * FROM warehouse_in LIMIT ? OFFSET ?',
        (per_page, offset)
    ).fetchall()
    total_count = conn.execute('SELECT COUNT(*) FROM warehouse_in').fetchone()[0]
    conn.close()

    total_pages = math.ceil(total_count / per_page)
    return render_template(
        'in_stock_query.html',
        in_records=in_records,
        current_page=page,
        total_pages=total_pages
    )

# 出库记录查询 + 分页（同理）
@app.route('/out_stock_query', methods=['GET'])
def out_stock_query():
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page

    conn = get_db_connection()
    out_records = conn.execute(
        'SELECT * FROM warehouse_out LIMIT ? OFFSET ?',
        (per_page, offset)
    ).fetchall()
    total_count = conn.execute('SELECT COUNT(*) FROM warehouse_out').fetchone()[0]
    conn.close()

    total_pages = math.ceil(total_count / per_page)
    return render_template(
        'out_stock_query.html',
        out_records=out_records,
        current_page=page,
        total_pages=total_pages
    )