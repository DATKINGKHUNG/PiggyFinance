import os
import json
import uuid
from datetime import datetime, timedelta
from flask import Flask, render_template, request, redirect, url_for, jsonify
import google.generativeai as genai
from dotenv import load_dotenv


load_dotenv()  # Load environment variables from .env file

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY") 

genai.configure(api_key=GOOGLE_API_KEY)

print(f"API Key loaded: {GOOGLE_API_KEY is not None}")  # Should print True
if not GOOGLE_API_KEY:
    print("Lỗi: Không tìm thấy GOOGLE_API_KEY")

app = Flask(__name__)
DATA_FILE = "expense_data.json"

# Hàm tiện ích
def load_data():
    """
    Hàm này tải dữ liệu chi tiêu từ một nguồn.
    """
    if not os.path.exists(DATA_FILE):
        return {
            'expenses': [],
            'categories': ['Ăn uống', 'Giải trí', 'Di chuyển', 'Nhà ở', 'Khác']
        }
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Lỗi: File {DATA_FILE} chứa dữ liệu JSON không hợp lệ.  Trả về dữ liệu mặc định.")
        return {
            'expenses': [],
            'categories': ['Ăn uống', 'Giải trí', 'Di chuyển', 'Nhà ở', 'Khác']
        }
    except Exception as e:
        print(f"Lỗi không mong muốn khi tải dữ liệu: {e}. Trả về dữ liệu mặc định.")
        return {
            'expenses': [],
            'categories': ['Ăn uống', 'Giải trí', 'Di chuyển', 'Nhà ở', 'Khác']
        }

def save_data(data):
    try:
        with open(DATA_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        print(f"Lỗi khi lưu dữ liệu: {e}")
        # Có thể raise lại exception nếu cần dừng chương trình:  raise

def parse_date(date_str):
    """Hàm này cố gắng chuyển đổi chuỗi ngày tháng sang đối tượng datetime."""
    try:
        return datetime.strptime(date_str, '%d/%m/%Y')
    except ValueError:
        print(f"Cảnh báo: Không thể phân tích cú pháp ngày tháng: {date_str}.  Sử dụng ngày hiện tại.")
        return datetime.now()

@app.context_processor
def inject_now():
    return {
        'datetime': datetime,
        'now': datetime.now()
    }

# Routes
@app.route('/')
def index():
    return redirect(url_for('home'))

@app.route('/home')
def home():
    """Trang chủ"""
    return render_template('home.html')

@app.route('/expenses', methods=['GET', 'POST'])
def expenses():
    """Quản lý chi tiêu (thêm/xem)"""
    data = load_data()
    
    if request.method == 'POST':
        # Xử lý thêm chi tiêu mới
        try:
            amount = float(request.form['amount'])
            if amount < 0:
                raise ValueError("Amount must be a non-negative number")
        except ValueError as e:
            # Log lỗi và trả về thông báo cho người dùng
            print(f"Lỗi: Giá trị không hợp lệ cho amount: {e}")
            return render_template('expenses.html', 
                                   expenses=data['expenses'],
                                   categories=data['categories'],
                                   error_message="Vui lòng nhập số tiền hợp lệ (>= 0)."), 400

        new_expense = {
            'id': str(uuid.uuid4()),  # Dùng UUID
            'amount': amount,
            'category': request.form['category'],
            'note': request.form.get('note', ''),
            'date': request.form['date'] or datetime.now().strftime('%d/%m/%Y')
        }
        data['expenses'].append(new_expense)
        save_data(data)
        return redirect(url_for('expenses'))
    
    return render_template('expenses.html',
                         expenses=data['expenses'],
                         categories=data['categories'],
                         error_message=None) # Truyền thêm biến báo lỗi


@app.route('/delete/<string:expense_id>', methods=['POST']) #Sửa thành string
def delete_expense(expense_id):
    """Xóa chi tiêu"""
    data = load_data()
    data['expenses'] = [e for e in data['expenses'] if e['id'] != expense_id]
    save_data(data)
    return redirect(url_for('expenses'))

def get_most_expensive_category(expenses):
    """
    Xác định danh mục chi tiêu nhiều nhất.

    Args:
        expenses (list): Danh sách các khoản chi tiêu.

    Returns:
        str: Danh mục chi tiêu nhiều nhất, hoặc "Không có" nếu không có chi tiêu.
    """
    if not expenses:
        return "Không có"
    category_totals = {}
    for expense in expenses:
        category = expense['category']
        amount = expense['amount']
        category_totals.setdefault(category, 0)  # Đảm bảo category có trong dict
        category_totals[category] += amount
    return max(category_totals, key=category_totals.get)

@app.route('/stats')
def stats():
    """Thống kê chi tiêu"""
    time_filter = request.args.get('filter', 'all')  # Lấy bộ lọc từ tham số 'filter'
    data = load_data()
    now = datetime.now()
    filtered_expenses = []

    # Lọc chi tiêu theo các mục: Tất cả, Năm, Tháng
    for expense in data['expenses']:
        exp_date = parse_date(expense['date'])
        
        # Lọc theo tuần
        if time_filter == 'week':
            start_of_week = now - timedelta(days=now.weekday())
            if exp_date >= start_of_week:
                filtered_expenses.append(expense)
        
        # Lọc theo tháng
        elif time_filter == 'month':
            if exp_date.month == now.month and exp_date.year == now.year:
                filtered_expenses.append(expense)
        
        # Lọc theo năm
        elif time_filter == 'year':
            if exp_date.year == now.year:
                filtered_expenses.append(expense)
        
        # Mặc định, tất cả
        else:  # all
            filtered_expenses.append(expense)

    # Tính toán các giá trị cần thiết
    total = sum(e['amount'] for e in filtered_expenses)
    categories = {}
    for category in data['categories']:
        category_sum = sum(e['amount'] for e in filtered_expenses if e['category'] == category)
        if category_sum > 0:
            categories[category] = category_sum

     # Gom nhóm chi tiêu để vẽ biểu đồ
    grouped_data = {}
    for expense in filtered_expenses:
        expense_date = parse_date(expense['date'])
        if time_filter == 'year':
            key = expense_date.strftime('%m/%Y')
        elif time_filter == 'month':
            key = expense_date.strftime('%d/%m')
        else:
            key = expense_date.strftime('%Y-%m-%d')  # Đầy đủ hơn cho tuần và tất cả
        if key not in grouped_data:
            grouped_data[key] = 0
        grouped_data[key] += expense['amount']

    return render_template('stats.html',
                           total=total,
                           categories=categories,
                           time_filter=time_filter,
                           filtered_expenses=filtered_expenses,
                           grouped_data=grouped_data)


@app.route('/add', methods=['POST'])
def add_expense():
    """Thêm chi tiêu mới (POST only)"""
    data = load_data()
    try:
        amount = float(request.form['amount'])
        if amount < 0:
            raise ValueError("Amount must be a non-negative number")
    except ValueError:
        return "Invalid amount", 400  # Trả về lỗi HTTP 400

    new_expense = {
        'id': str(uuid.uuid4()),
        'date': request.form['date'],
        'category': request.form['category'],
        'amount': amount,
        'note': request.form['note']
    }
    data['expenses'].append(new_expense)
    save_data(data)
    return redirect(url_for('index')) # Bạn nên chuyển hướng đến trang hiển thị chi tiêu



@app.route('/ask-gemini', methods=['POST'])
def ask_gemini():
    """
    Nhận yêu cầu từ người dùng, truy vấn Gemini API và trả về phản hồi.
    """
    data = load_data()
    user_input = request.json.get('input_text')
    time_filter = request.json.get('current_filter', 'all')

    # Chuẩn bị dữ liệu theo bộ lọc
    filtered_expenses = []
    now = datetime.now()

    for expense in data['expenses']:
        exp_date = parse_date(expense['date'])
        if time_filter == 'month' and (exp_date.month != now.month or exp_date.year != now.year):
            continue
        elif time_filter == 'year' and exp_date.year != now.year:
            continue
        filtered_expenses.append(expense)

    # Tính toán các giá trị cần thiết
    total_spending = sum(e['amount'] for e in filtered_expenses)
    most_expensive_category = get_most_expensive_category(filtered_expenses)

    # Tạo prompt
    prompt = f"""Bạn là trợ lý tài chính thông minh. Dưới đây là dữ liệu chi tiêu {time_filter} của người dùng:\n\n    Tổng chi tiêu: {total_spending:,.0f} VND\n    Danh mục chi tiêu nhiều nhất: {most_expensive_category}\n\n    Yêu cầu của người dùng: {user_input}\n\n    Hãy trả lời ngắn gọn, rõ ràng và đưa ra lời khuyên cụ thể.\n    """

    try:
        model = genai.GenerativeModel('gemini-2.5-flash-preview-04-17')
        response = model.generate_content(prompt)
        ai_response_text = response.text if response.text else "Xin lỗi, tôi không thể tạo phản hồi ngay bây giờ."

        return jsonify({"response": ai_response_text})
    except Exception as e:
        error_message = f"Lỗi khi gọi API Gemini: {str(e)}"
        print(error_message)
        return jsonify({"error": error_message}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8000))
    app.run(host='0.0.0.0', port=port, debug=True)
