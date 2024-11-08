from flask import Flask, render_template, request, redirect, url_for, send_file
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

def get_all_dates(start_date, end_date, weekday=None):
    dates = []
    current_date = start_date
    while current_date <= end_date:
        if weekday is None or current_date.weekday() == weekday:
            dates.append(current_date)
        current_date += timedelta(days=1)
    return dates

def fetch_stock_data(stock_symbols, date=None, date_range=None, weekday=None):
    # Set date range for data fetching
    if date:
        start_date = end_date = datetime.strptime(date, '%Y-%m-%d')
        dates = [start_date]
    elif date_range:
        start_date = datetime.strptime(date_range[0], '%Y-%m-%d')
        end_date = datetime.strptime(date_range[1], '%Y-%m-%d')
        dates = get_all_dates(start_date, end_date, weekday=weekday)

    # Fetch data for all stocks
    data = yf.download(stock_symbols, start=start_date, end=end_date, interval="1d", group_by='ticker')

    # Prepare the result data
    result_data = pd.DataFrame({'stock': [s.replace('.NS', '') for s in stock_symbols]})
    for d in dates:
        date_str = d.strftime('%Y-%m-%d')
        prices = []
        for stock in stock_symbols:
            try:
                price = data[stock]['Close'].loc[date_str]
            except KeyError:
                price = None
            prices.append(price)
        result_data[date_str] = prices
    return result_data.round(0)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        date_type = request.form.get('date_type')
        date = request.form.get('date') if date_type == 'specific' else None
        start_date = request.form.get('start_date') if date_type == 'range' else None
        end_date = request.form.get('end_date') if date_type == 'range' else None
        weekday = int(request.form.get('weekday')) if date_type == 'range' and request.form.get('weekday') else None
        
        stock_symbols = []
        if 'stock_name' in request.form and request.form['stock_name']:
            stock_symbols = [request.form['stock_name'].strip().upper() + '.NS']
        elif 'stock_file' in request.files and request.files['stock_file'].filename:
            file = request.files['stock_file']
            file_path = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
            file.save(file_path)
            with open(file_path, 'r') as f:
                stock_symbols = [line.strip().upper() + '.NS' for line in f]

        date_range = (start_date, end_date) if start_date and end_date else None
        result_data = fetch_stock_data(stock_symbols, date, date_range, weekday)
        result_csv_path = os.path.join(app.config['UPLOAD_FOLDER'], 'result.csv')
        result_data.to_csv(result_csv_path, index=False)

        return redirect(url_for('result', filename='result.csv'))

    return render_template('index.html')

@app.route('/result')
def result():
    filename = request.args.get('filename')
    return render_template('result.html', filename=filename)

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(os.path.join(app.config['UPLOAD_FOLDER'], filename), as_attachment=True)

if __name__ == '__main__':
    app.run(debug=True)
