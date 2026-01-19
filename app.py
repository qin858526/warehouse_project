import math
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = "warehouse_2026"

# 数据库连接函数
def get_db_connection():
    conn = sqlite3.connect('warehouse.db')
    conn.row_factory = sqlite3.Row
    return conn

# 初始化数据库（确保表存在）
def init_database():
    conn = get_db_connection()
    # 入库表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS warehouse_in (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_model TEXT NOT NULL,
            material TEXT NOT NULL,
            in_quantity INTEGER NOT NULL,
            in_time DATETIME NOT NULL,
            remarks TEXT DEFAULT NULL
        )
    ''')
    # 新增：给in_time加索引
    conn.execute('CREATE INDEX IF NOT EXISTS idx_warehouse_in_time ON warehouse_in (in_time DESC)')
    # 出库表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS warehouse_out (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_model TEXT NOT NULL,
            material TEXT NOT NULL,
            out_quantity INTEGER NOT NULL,
            out_time DATETIME NOT NULL,
            customer_unit TEXT NOT NULL,
            remarks TEXT DEFAULT NULL
        )
    ''')
    # 新增：给out_time加索引
    conn.execute('CREATE INDEX IF NOT EXISTS idx_warehouse_out_time ON warehouse_out (out_time DESC)')
    # 库存表
    conn.execute('''
        CREATE TABLE IF NOT EXISTS total_inventory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            product_model TEXT NOT NULL,
            material TEXT NOT NULL,
            stock_quantity INTEGER NOT NULL DEFAULT 0,
            remarks TEXT DEFAULT NULL,
            UNIQUE(product_model, material)
        )
    ''')
    conn.commit()
    conn.close()

# 首页
@app.route('/')
def index():
    return render_template('index.html')

# 库存查询
@app.route('/query_total', methods=['GET'])
def query_total():

    # 筛选参数
    # 产品型号：下拉筛选（精确匹配）+ 手动输入（模糊匹配）
    model_filter = request.args.get('model', '')  # 下拉参数（model）
    product_model = request.args.get('product_model', '').strip()  # 手动输入参数

    # 材质：下拉筛选（精确匹配）+ 手动输入（模糊匹配）
    material_filter = request.args.get('material_filter', '')  # 下拉参数（新参数名）
    material = request.args.get('material', '').strip()  # 手动输入参数

    stock_min = request.args.get('stock_min', '')
    stock_max = request.args.get('stock_max', '')

    # 1. 获取分页参数：页码（默认第1页）、每页显示10条（可自定义）
    page = request.args.get('page', 1, type=int)  # 从URL获取?page=X参数
    per_page = 10  # 每页固定显示10条，可改成20/50

    # 2. 计算分页偏移量（OFFSET）：(页码-1)*每页条数
    offset = (page - 1) * per_page

    # 基础SQL（统计总数+查询数据）
    count_sql = f"SELECT COUNT(*) FROM total_inventory WHERE 1=1"
    params = []
    #新筛选
    query = "SELECT * FROM total_inventory WHERE 1=1"  # 1=1方便拼接条件
    
    # 产品型号条件：同时应用下拉和手动筛选（精确+模糊）
    if model_filter:
        query += " AND product_model = ?"
        params.append(model_filter)
    if product_model:
        query += " AND product_model LIKE ?"
        params.append(f'%{product_model}%')

    # 材质条件：同时应用下拉和手动筛选（精确+模糊）
    if material_filter:
        query += " AND material = ?"
        params.append(material_filter)
    if material:
        query += " AND material LIKE ?"
        params.append(f'%{material}%')

    if stock_min.isdigit():
        count_sql += " AND stock_quantity >= ?"
        query += " AND stock_quantity >= ?"
        params.append(int(stock_min))
    if stock_max.isdigit():
        count_sql += " AND stock_quantity <= ?"
        query += " AND stock_quantity <= ?"
        params.append(int(stock_max))

    # 3. 数据库查询：当前页数据 + 总数据条数（适配你的表名）----------旧版
    # conn = get_db_connection()
    # # 统计符合条件的总条数
    # total_count = conn.execute(count_sql, params).fetchone()[0]
    # # 计算总页数
    # total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1
    # # 分页查询数据
    # data_sql += f" LIMIT {per_page} OFFSET {offset}"
    # stocks = conn.execute(data_sql, params).fetchall()
    # conn.close()

    # # 4. 计算总页数（向上取整，比如11条=2页）
    # total_pages = math.ceil(total_count / per_page) if total_count > 0 else 1

    # # 5. 传递参数到你的query.html（模板名不变）
    # return render_template(
    #     'query.html',  # 你的库存查询页模板名：query.html
    #     stocks=stocks,  # 库存数据（模板里遍历的变量名不变）
    #     current_page=page,  # 新增：当前页码
    #     total_pages=total_pages,  # 新增：总页数
    #     per_page=per_page  # 新增：每页条数（可选）
    # )

    # 先查询总条数（用于分页）
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query.replace("*", "COUNT(*)"), params)
    total = cursor.fetchone()[0]
    total_pages = max(1, (total + per_page - 1) // per_page)  # 总页数

    # 添加分页限制
    query += " LIMIT ? OFFSET ?"
    params.extend([per_page, (page - 1) * per_page])
    cursor.execute(query, params)
    stocks = cursor.fetchall()  # 实际项目中建议转换为字典列表
    conn.close()

    # 传递数据到模板
    return render_template(
        'query.html',
        stocks=stocks,
        current_page=page,
        total_pages=total_pages
    )

# 入库（核心：全局异常捕获，确保数据库提交）
# 入库（核心：全局异常捕获，确保数据库提交）
@app.route('/in_stock', methods=['GET', 'POST'])
def in_stock():
    product_models = ["型号A", "型号B", "型号C", "型号D"]
    materials = ["材质1", "材质2", "材质3", "材质4", "材质5"]
    
    if request.method == 'POST':
        # 全局异常捕获：任何错误都能打印，且不中断流程
        if '_flashes' in session:
            session.pop('_flashes')

        try:
            # 1. 获取表单数据
            product_model = request.form['product_model']
            material = request.form['material']
            in_quantity = int(request.form['in_quantity'])
            user_input_time = request.form.get('in_time', '')
            remarks = request.form.get('remarks', '')

            # 2. 简化时间处理：兼容任意格式，失败则用当前时间
            if not user_input_time:
                in_time = datetime.now()
            else:
                # 兼容秒级/分钟级格式，失败则用当前时间
                try:
                    in_time = datetime.strptime(user_input_time, '%Y-%m-%dT%H:%M:%S')
                except:
                    try:
                        in_time = datetime.strptime(user_input_time, '%Y-%m-%dT%H:%M')
                    except:
                        in_time = datetime.now()

            # 3. 数据库操作（确保执行到提交）
            # 入库接口的数据库操作部分（修改后）
            conn = get_db_connection()
            # 调试日志1：打印要插入的数据
            print(f"准备插入入库数据：{product_model}, {material}, {in_quantity}, {in_time}")
            # 插入入库记录
            conn.execute(
                'INSERT INTO warehouse_in (product_model, material, in_quantity, in_time, remarks) VALUES (?, ?, ?, ?, ?)',
                (product_model, material, in_quantity, in_time, remarks)
            )
            # 调试日志2：打印插入后的行数（确认插入成功）
            cursor = conn.execute('SELECT COUNT(*) FROM warehouse_in')
            count = cursor.fetchone()[0]
            print(f"插入后warehouse_in表总行数：{count}")

            # 更新库存
            stock = conn.execute(
                'SELECT * FROM total_inventory WHERE product_model = ? AND material = ?',
                (product_model, material)
            ).fetchone()
            if stock:
                new_quantity = stock['stock_quantity'] + in_quantity
                conn.execute(
                    'UPDATE total_inventory SET stock_quantity = ? WHERE product_model = ? AND material = ?',
                    (new_quantity, product_model, material)
                )
            else:
                conn.execute(
                    'INSERT INTO total_inventory (product_model, material, stock_quantity, remarks) VALUES (?, ?, ?, ?)',
                    (product_model, material, in_quantity, remarks)
                )
            # 调试日志3：打印库存表行数
            cursor2 = conn.execute('SELECT COUNT(*) FROM total_inventory')
            count2 = cursor2.fetchone()[0]
            print(f"插入后total_inventory表总行数：{count2}")

            conn.commit()
            conn.close()
            flash('入库成功！', 'success')  # 新增success分类
            return redirect(url_for('in_stock'))  # 改为返回入库页（方便继续操作）
        
        # 捕获所有异常，打印错误（方便排查），并提示用户
        except Exception as e:
            print(f"入库失败，异常信息：{str(e)}")  # 控制台打印错误
            flash(f'入库失败：{str(e)}', 'error')  # 新增error分类
            return redirect(url_for('in_stock'))  # 返回入库页面

    return render_template('in_stock.html', models=product_models, materials=materials)

# 出库（同入库逻辑，全局异常捕获）
@app.route('/out_stock', methods=['GET', 'POST'])
def out_stock():
    product_models = ["型号A", "型号B", "型号C", "型号D"]
    materials = ["材质1", "材质2", "材质3", "材质4", "材质5"]
    
    if request.method == 'POST':
        if '_flashes' in session:
            session.pop('_flashes')
        try:
            product_model = request.form['product_model']
            material = request.form['material']
            out_quantity = int(request.form['out_quantity'])
            customer_unit = request.form['customer_unit']
            user_input_time = request.form.get('out_time', '')
            remarks = request.form.get('remarks', '')

            # 简化时间处理
            if not user_input_time:
                out_time = datetime.now()
            else:
                try:
                    out_time = datetime.strptime(user_input_time, '%Y-%m-%dT%H:%M:%S')
                except:
                    try:
                        out_time = datetime.strptime(user_input_time, '%Y-%m-%dT%H:%M')
                    except:
                        out_time = datetime.now()

            # 数据库操作
            conn = get_db_connection()
            # 检查库存
            stock = conn.execute(
                'SELECT * FROM total_inventory WHERE product_model = ? AND material = ?',
                (product_model, material)
            ).fetchone()
            if not stock:
                conn.close()
                flash('错误：该货物不存在，无法出库！', 'error')  # 新增error分类
                return redirect(url_for('out_stock'))
            if stock['stock_quantity'] < out_quantity:
                conn.close()
                flash(f'错误：库存不足！当前库存：{stock["stock_quantity"]}，请求出库：{out_quantity}', 'error')  # 新增error分类
                return redirect(url_for('out_stock'))
            
            # 插入出库记录
            conn.execute(
                'INSERT INTO warehouse_out (product_model, material, out_quantity, customer_unit, out_time, remarks) VALUES (?, ?, ?, ?, ?, ?)',
                (product_model, material, out_quantity, customer_unit, out_time, remarks)
            )
            # 更新库存
            new_quantity = stock['stock_quantity'] - out_quantity
            conn.execute(
                'UPDATE total_inventory SET stock_quantity = ? WHERE product_model = ? AND material = ?',
                (new_quantity, product_model, material)
            )
            conn.commit()
            conn.close()

            flash('出库成功！', 'success')  # 新增success分类
            return redirect(url_for('out_stock'))
        
        except Exception as e:
            print(f"出库失败，异常信息：{str(e)}")
            flash(f'出库失败：{str(e)}', 'error')  # 新增error分类
            return redirect(url_for('out_stock'))

    return render_template('out_stock.html', models=product_models, materials=materials)

# 历史入库查询
@app.route('/query_in_history', methods=['GET'])
def query_in_history():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    conn = get_db_connection()
    in_records = conn.execute(
        'SELECT * FROM warehouse_in ORDER BY in_time DESC LIMIT ? OFFSET ?',
        (per_page, offset)
    ).fetchall()
    total_count = conn.execute('SELECT COUNT(*) FROM warehouse_in').fetchone()[0]
    conn.close()

    total_pages = math.ceil(total_count / per_page)
    return render_template(
        'in_history.html',
        in_records=in_records,
        current_page=page,
        total_pages=total_pages
    )

# 历史出库查询
@app.route('/query_out_history', methods=['GET'])
def query_out_history():
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    conn = get_db_connection()
    out_records = conn.execute(
        'SELECT * FROM warehouse_out ORDER BY out_time DESC LIMIT ? OFFSET ?',
        (per_page, offset)
    ).fetchall()
    total_count = conn.execute('SELECT COUNT(*) FROM warehouse_out').fetchone()[0]
    conn.close()

    total_pages = math.ceil(total_count / per_page)
    return render_template(
        'out_history.html',
        out_records=out_records,
        current_page=page,
        total_pages=total_pages
    )
# ========== 新增：查询产品+材质的入库/出库记录接口（不影响原有功能） ==========
@app.route('/api/get_stock_records', methods=['POST'])
def get_stock_records():
    try:
        # 获取前端传的产品型号和材质
        data = request.get_json()
        product_model = data.get('product_model')
        material = data.get('material')
        if not product_model or not material:
            return jsonify({'code': 1, 'msg': '产品型号/材质不能为空'})
        
        conn = get_db_connection()
        cursor = conn.cursor()

        # 1. 查询入库记录（匹配你的warehouse_in表结构）
        cursor.execute('''
            SELECT '入库' as type, in_quantity as quantity, '' as unit, in_time as operate_time, remarks 
            FROM warehouse_in 
            WHERE product_model = ? AND material = ?
            ORDER BY in_time DESC
            LIMIT 10
        ''', (product_model, material))
        in_records = [dict(row) for row in cursor.fetchall()]

        # 2. 查询出库记录（匹配你的warehouse_out表结构，unit对应customer_unit）
        cursor.execute('''
            SELECT '出库' as type, out_quantity as quantity, customer_unit as unit, out_time as operate_time, remarks 
            FROM warehouse_out 
            WHERE product_model = ? AND material = ?
            ORDER BY out_time DESC
            LIMIT 10
        ''', (product_model, material))
        out_records = [dict(row) for row in cursor.fetchall()]

        # 3. 合并记录+按时间倒序，取前10条
        all_records = in_records + out_records
        all_records.sort(key=lambda x: x['operate_time'], reverse=True)
        latest_records = all_records[:10]

        conn.close()
        return jsonify({
            'code': 0,
            'msg': '查询成功',
            'records': latest_records
        })
    except Exception as e:
        print(f"记录查询失败：{str(e)}")
        return jsonify({'code': 2, 'msg': f'查询失败：{str(e)}'})

if __name__ == '__main__':
    init_database()  # 启动时确保表存在
    app.run(debug=True, host='0.0.0.0', port=8888)
    # -w 4：开启4个工作进程（根据电脑性能调整）
    # -b 0.0.0.0:5000：绑定所有网卡+5000端口
    # gunicorn -w 4 -b 0.0.0.0:5000 app:app