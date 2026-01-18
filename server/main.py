from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from typing import Optional, List, Dict, Any
import pandas as pd
import numpy as np
import io
import math
import os
import json
from datetime import datetime
from utils.pdf import generate_pdf
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# CORS configuration
origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

# Allow any private network IP for mobile/LAN access
# Regex matches: 192.168.x.x, 10.x.x.x, 172.16.x.x - 172.31.x.x
origin_regex = r"^http://(192\.168\.\d+\.\d+|10\.\d+\.\d+\.\d+|172\.(1[6-9]|2\d|3[0-1])\.\d+\.\d+)(:\d+)?$"

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_origin_regex=origin_regex,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB limit

# Rate Limiting Logic
USAGE_FILE = "data/usage.json"

def get_usage_data():
    if not os.path.exists(USAGE_FILE):
        return {}
    try:
        with open(USAGE_FILE, 'r') as f:
            return json.load(f)
    except:
        return {}

def save_usage_data(data):
    try:
        os.makedirs(os.path.dirname(USAGE_FILE), exist_ok=True)
        with open(USAGE_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        print(f"Error saving usage data: {e}")

def check_rate_limit(ip: str, is_demo: bool = False) -> bool:
    data = get_usage_data()
    record = data.get(ip, {})
    
    # Handle legacy format where value was string
    if isinstance(record, str):
        record = {} # Reset if old format
        
    if is_demo:
        count = record.get("demo_count", 0)
        if count >= 2:
            return False # Demo limit reached
    else:
        count = record.get("upload_count", 0)
        last_date = record.get("last_upload_date")
        today = datetime.now().strftime("%Y-%m-%d")
        
        # Reset count if it's a new day
        if last_date != today:
            return True
        
        if count >= 1:
            return False # Upload limit reached
            
    return True

def record_usage(ip: str, is_demo: bool = False):
    data = get_usage_data()
    record = data.get(ip, {})
    
    # Handle legacy format
    if isinstance(record, str):
        record = {}
        
    if is_demo:
        record["demo_count"] = record.get("demo_count", 0) + 1
    else:
        today = datetime.now().strftime("%Y-%m-%d")
        last_date = record.get("last_upload_date")
        
        # Reset count if new day
        if last_date != today:
            record["upload_count"] = 1
            record["last_upload_date"] = today
        else:
            record["upload_count"] = record.get("upload_count", 0) + 1
            record["last_upload_date"] = today
        
    data[ip] = record
    save_usage_data(data)

def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize column names to standard keys: date, amount, type, category."""
    # Map of standard keys to possible synonyms (lower cased)
    column_map = {
        'date': ['date', 'datetime', 'timestamp', 'التاريخ', 'الوقت', 'day'],
        'amount': ['amount', 'value', 'cost', 'price', 'المبلغ', 'القيمة', 'السعر', 'total'],
        'type': ['type', 'kind', 'direction', 'النوع', 'الحالة', 'category_type'],
        'category': ['category', 'cat', 'description', 'desc', 'الفئة', 'التصنيف', 'البند']
    }
    
    # Create a mapping dictionary for renaming
    rename_dict = {}
    existing_cols = [c.lower().strip() for c in df.columns]
    
    # Helper to find first match
    for std_col, synonyms in column_map.items():
        for col in df.columns:
            clean_col = col.lower().strip()
            if clean_col in synonyms:
                rename_dict[col] = std_col
                break 
    
    # Apply renaming
    df = df.rename(columns=rename_dict)
    
    return df

    return df

def clean_currency(x):
    if isinstance(x, (int, float)):
        return x
    if isinstance(x, str):
        # Remove currency symbols, commas, spaces, LTR/RTL marks
        clean_str = x.replace('$', '').replace('€', '').replace('£', '').replace('SAT', '').replace('ر.س', '').replace(',', '').strip()
        try:
            return float(clean_str)
        except ValueError:
            return np.nan
    return np.nan

def detect_schema(df: pd.DataFrame) -> str:
    """
    Detects if the dataframe is 'transactions' or 'pnl'.
    """
    cols = [c.lower().strip() for c in df.columns]
    
    # P&L keywords
    month_keywords = ['month', 'period', 'الشهر', 'شهر', 'الفترة']
    rev_keywords = ['revenue', 'sales', 'income', 'الإيرادات', 'المبيعات', 'الدخل', 'rev']
    exp_keywords = ['expenses', 'opex', 'costs', 'cost', 'المصروفات', 'التكاليف', 'المصاريف', 'exp']
    
    has_month = any(k in c for c in cols for k in month_keywords)
    has_rev = any(k in c for c in cols for k in rev_keywords)
    has_exp = any(k in c for c in cols for k in exp_keywords)
    
    if has_month and has_rev and has_exp:
        return 'pnl'
        
    return 'transactions'

def parse_pnl(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parses P&L format: Month, Revenue, Expenses
    Returns DF with checks.
    """
    # Normalize P&L columns
    rename_map = {}
    
    month_keywords = ['month', 'period', 'الشهر', 'شهر', 'الفترة']
    rev_keywords = ['revenue', 'sales', 'income', 'الإيرادات', 'المبيعات', 'الدخل', 'rev']
    exp_keywords = ['expenses', 'opex', 'costs', 'cost', 'المصروفات', 'التكاليف', 'المصاريف', 'exp']
    
    for col in df.columns:
        c_lower = col.lower().strip()
        if any(k in c_lower for k in month_keywords) and 'month' not in rename_map.values():
            rename_map[col] = 'month'
        elif any(k in c_lower for k in rev_keywords) and 'revenue' not in rename_map.values():
            rename_map[col] = 'revenue'
        elif any(k in c_lower for k in exp_keywords) and 'expenses' not in rename_map.values():
            rename_map[col] = 'expenses'
            
    df = df.rename(columns=rename_map)
    
    req = ['month', 'revenue', 'expenses']
    missing = [c for c in req if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail=f"ملف قائمة الدخل ناقص. لا يوجد أعمدة: {', '.join(missing)}")
        
    # Clean Numbers
    df['revenue'] = df['revenue'].apply(clean_currency)
    df['expenses'] = df['expenses'].apply(clean_currency)
    
    # Clean Date (Date parsing is tricky for 'Jan-24', 'فبراير 2024')
    # simple attempt: try pd.to_datetime, if fails try adding day
    def parse_month_str(x):
        try:
            return pd.to_datetime(x)
        except:
             # Try appending day 1
            try:
                return pd.to_datetime(f"1-{x}")
            except:
                pass
            return pd.to_datetime(x, errors='coerce')

    df['date'] = df['month'].apply(parse_month_str)
    
    df = df.dropna(subset=['date', 'revenue', 'expenses'])
    if df.empty:
         raise HTTPException(status_code=400, detail="لم يتم العثور على تواريخ صالحة في ملف قائمة الدخل.")
         
    return df.sort_values('date')

def parse_data(contents: bytes, filename: str) -> tuple[pd.DataFrame, str]:
    try:
        if filename.endswith('.csv'):
            df = pd.read_csv(io.BytesIO(contents), encoding='utf-8-sig')
        else:
            df = pd.read_excel(io.BytesIO(contents))
    except Exception as e:
        raise HTTPException(status_code=400, detail="الملف غير صالح للتحليل المالي. يرجى رفع ملف يحتوي على بيانات مالية بصيغة CSV أو Excel.")

    schema = detect_schema(df)
    
    if schema == 'pnl':
        df = parse_pnl(df)
        return df, schema
    
    # Transactions Logic (Existing)
    df = normalize_columns(df)
    
    # Validation: Check for required columns
    required_cols = ['date', 'amount']
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise HTTPException(status_code=400, detail="الملف غير صالح للتحليل المالي. يرجى رفع ملف يحتوي على بيانات مالية بصيغة CSV أو Excel.")

    # 1. Parse Date
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    
    # 2. Parse Amount
    df['amount'] = df['amount'].apply(clean_currency)
    
    # Drop rows with invalid date or amount
    df = df.dropna(subset=['date', 'amount'])
    
    if len(df) == 0:
        raise HTTPException(status_code=400, detail="الملف غير صالح للتحليل المالي. يرجى رفع ملف يحتوي على بيانات مالية بصيغة CSV أو Excel.")
        
    return df, schema

def calculate_kpis(df: pd.DataFrame) -> Dict[str, Any]:
    # Ensure sorted by date
    df = df.sort_values('date')
    
    # Determine Income vs Expense
    # If 'type' column exists, use it. Else use sign.
    if 'type' in df.columns:
        # Normalize type values
        def categorize_type(t):
            t = str(t).lower().strip()
            if t in ['income', 'revenue', 'credit', 'cr', 'دخل', 'ايرادات', 'إيرادات', 'ايداع']:
                return 'income'
            if t in ['expense', 'cost', 'debit', 'dr', 'مصروف', 'مصروفات', 'سحب']:
                return 'expense'
            return 'unknown'
            
        df['norm_type'] = df['type'].apply(categorize_type)
        
        # Unified signed amount column logic
        df['signed_amount'] = np.where(df['norm_type'] == 'expense', -df['amount'].abs(), 
                                       np.where(df['norm_type'] == 'income', df['amount'].abs(), df['amount']))
    else:
        # Fallback to sign for unknown types
        df['signed_amount'] = df['amount']

    # Calculations
    total_revenue = df[df['signed_amount'] > 0]['signed_amount'].sum()
    total_expenses = df[df['signed_amount'] < 0]['signed_amount'].abs().sum()
    net_profit = total_revenue - total_expenses
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Monthly Aggregation
    df['month_period'] = df['date'].dt.to_period('M')
    monthly = df.groupby('month_period')['signed_amount'].agg(
        revenue=lambda x: x[x > 0].sum(),
        expenses=lambda x: x[x < 0].abs().sum(),
        net=lambda x: x.sum()
    ).sort_index()
    
    # Delta Logic (Last Month vs Previous)
    if len(monthly) >= 2:
        last_month = monthly.iloc[-1]
        prev_month = monthly.iloc[-2]
        
        rev_delta = ((last_month['revenue'] - prev_month['revenue']) / prev_month['revenue'] * 100) if prev_month['revenue'] > 0 else 0
        exp_delta = ((last_month['expenses'] - prev_month['expenses']) / prev_month['expenses'] * 100) if prev_month['expenses'] > 0 else 0
        net_delta = ((last_month['net'] - prev_month['net']) / abs(prev_month['net']) * 100) if prev_month['net'] != 0 else 0
        margin_last = (last_month['net'] / last_month['revenue'] * 100) if last_month['revenue'] > 0 else 0
        margin_prev = (prev_month['net'] / prev_month['revenue'] * 100) if prev_month['revenue'] > 0 else 0
        margin_delta = margin_last - margin_prev # Absolute percentage point difference
    else:
        rev_delta = exp_delta = net_delta = margin_delta = None
        
    avg_monthly_expenses = monthly['expenses'].mean() if not monthly.empty else 0
    highest_expense_month_val = monthly['expenses'].max() if not monthly.empty else 0
    highest_expense_month_name = str(monthly['expenses'].idxmax()) if not monthly.empty else "N/A"

    def fmt_money(val):
        return f"{val:,.0f}" 
    
    def fmt_delta(val, is_pct=True, suffix_override=None):
        if val is None: return "غير متاح"
        sign = "+" if val >= 0 else ""
        
        if suffix_override:
            return f"{sign}{val:.1f} {suffix_override}"
            
        suffix = "%" if is_pct else ""
        return f"{sign}{val:.1f}{suffix}"

    # Insight Helpers
    def get_rev_insight(val, delta):
        if delta is None: return "لا تتوفر بيانات كافية للمقارنة."
        if delta > 0: return "نمو إيجابي في الإيرادات مقارنة بالشهر السابق."
        if delta < 0: return "تراجع في الإيرادات يتطلب مراجعة أسباب الانخفاض."
        return "استقرار في الإيرادات مقارنة بالشهر السابق."

    def get_exp_insight(val, delta):
        if delta is None: return "لا تتوفر بيانات كافية للمقارنة."
        if delta > 20: return "ارتفاع ملحوظ في المصروفات التشغيلية."
        if delta < -10: return "تحسن في ضبط المصروفات وترشيد الإنفاق."
        return "المصروفات ضمن النطاق المعتاد."
    
    def get_net_insight(val, delta):
        if val < 0: return "تسجيل خسارة صافية خلال الفترة."
        if delta is not None and delta > 0: return "نمو في صافي الأرباح مقارنة بالفترة السابقة."
        return "تحقيق صافي ربح إيجابي."

    def get_margin_insight(val, delta):
        if val < 10: return "هامش الربح منخفض وقد يؤثر على الاستدامة."
        if val > 40: return "هامش ربح صحي وممتاز."
        return "هامش ربح جيد ومستقر."
        
    kpis = [
        { 
            "name": "إجمالي الإيرادات", 
            "value": fmt_money(total_revenue), 
            "delta": fmt_delta(rev_delta),
            "insight": get_rev_insight(total_revenue, rev_delta)
        },
        { 
            "name": "إجمالي المصروفات", 
            "value": fmt_money(total_expenses), 
            "delta": fmt_delta(exp_delta),
            "insight": get_exp_insight(total_expenses, exp_delta)
        },
        { 
            "name": "صافي الربح", 
            "value": fmt_money(net_profit), 
            "delta": fmt_delta(net_delta),
            "insight": get_net_insight(net_profit, net_delta)
        },
        { 
            "name": "هامش الربح", 
            "value": f"{profit_margin:.1f}%", 
            "delta": fmt_delta(margin_delta, is_pct=False, suffix_override="نقطة"),
            "insight": get_margin_insight(profit_margin, margin_delta)
        },
        { 
            "name": "متوسط المصروفات", 
            "value": fmt_money(avg_monthly_expenses), 
            "delta": "شهرياً",
            "insight": "متوسط الإنفاق الشهري التشغيلي."
        },
        { 
            "name": "أعلى مصروفات", 
            "value": fmt_money(highest_expense_month_val), 
            "delta": highest_expense_month_name,
            "insight": "الشهر الأعلى إنفاقاً خلال الفترة."
        },
    ]
    
    # Risks / Anomalies
    risks = []
    
    # Risk 1: Margin too low
    if profit_margin < 10:
        risks.append("هامش الربح الإجمالي منخفض جداً (أقل من 10%)")
        
    # Risk 2: High Expenses Trend
    if exp_delta is not None and exp_delta > 20:
        risks.append(f"ارتفاع حاد في المصروفات الشهرية بنسبة {exp_delta:.1f}%")
        
    # Risk 3: Revenue Drop
    if rev_delta is not None and rev_delta < -15:
        risks.append(f"انخفاض ملحوظ في الإيرادات الشهرية بنسبة {abs(rev_delta):.1f}%")
        
    # Risk 4: Negative Net Profit (Last Month)
    if not monthly.empty and monthly.iloc[-1]['net'] < 0:
        risks.append("صافي ربح الشهر الأخير سلبي (خسارة)")
        
    # Risk 5: Concentration Risk (Category)
    top_cat_risk = False
    if 'category' in df.columns:
        # Filter expenses
        expenses_df = df[df['signed_amount'] < 0].copy()
        if not expenses_df.empty:
            expenses_df['abs_amt'] = expenses_df['signed_amount'].abs()
            cat_group = expenses_df.groupby('category')['abs_amt'].sum().sort_values(ascending=False)
            if not cat_group.empty:
                top_cat = cat_group.index[0]
                top_pct = (cat_group.iloc[0] / total_expenses) * 100
                if top_pct > 40:
                    risks.append(f"تركيز عالي للمصروفات في بند '{top_cat}' ({top_pct:.1f}%)")
                    top_cat_risk = top_cat # Store for recommendation

    # Fill default risks if empty
    if not risks:
        risks.append("لم يتم رصد مخاطر حرجة بناءً على البيانات الحالية.")

    # Recommendations Mapping
    recommendations_list = []
    for r in risks:
        if "هامش الربح" in r:
            recommendations_list.append("مراجعة تسعير المنتجات أو خفض التكاليف المباشرة فوراً.")
        elif "ارتفاع حاد في المصروفات" in r:
            recommendations_list.append("تحليل بنود المصروفات المتضخمة لهذا الشهر ووضع سقف للإنفاق.")
        elif "انخفاض" in r and "الإيرادات" in r:
            recommendations_list.append("تفعيل حملات تسويقية عاجلة أو مراجعة أداء فريق المبيعات.")
        elif "خسارة" in r or "سلبي" in r:
            recommendations_list.append("إجراء مراجعة شاملة للتدفقات النقدية لتجنب أزمة سيولة.")
        elif "تركيز عالي" in r:
            recommendations_list.append(f"البحث عن موردين بدائل أو تقليل الاعتماد على '{top_cat_risk}' إن أمكن.")
    
    # Deduplicate preserving order
    recommendations = list(dict.fromkeys(recommendations_list))
    
    if not recommendations:
        recommendations.append("الاستمرار في مراقبة الأداء المالي للحفاظ على الاستقرار.")
        
    return {
        "kpis": kpis,
        "risks": risks,
        "recommendations": recommendations,
        "monthly_count": len(monthly)
    }

def calculate_pnl_results(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculates KPIs, Risks, Recs from P&L Data (Month, Revenue, Expenses)
    """
    # Basic calcs
    if 'revenue' not in df.columns or 'expenses' not in df.columns:
        raise HTTPException(status_code=400, detail="PnL data must have revenue and expenses")
        
    total_revenue = df['revenue'].sum()
    total_expenses = df['expenses'].sum()
    net_profit = total_revenue - total_expenses
    profit_margin = (net_profit / total_revenue * 100) if total_revenue > 0 else 0
    
    # Monthly aggregations (df is already monthly rows hopefully)
    monthly = df.set_index('date').sort_index()
    monthly['net'] = monthly['revenue'] - monthly['expenses']
    
    # Delta Logic (Last Month vs Previous)
    if len(monthly) >= 2:
        last_month = monthly.iloc[-1]
        prev_month = monthly.iloc[-2]
        
        rev_delta = ((last_month['revenue'] - prev_month['revenue']) / prev_month['revenue'] * 100) if prev_month['revenue'] > 0 else 0
        exp_delta = ((last_month['expenses'] - prev_month['expenses']) / prev_month['expenses'] * 100) if prev_month['expenses'] > 0 else 0
        net_delta = ((last_month['net'] - prev_month['net']) / abs(prev_month['net']) * 100) if prev_month['net'] != 0 else 0
        
        margin_last = (last_month['net'] / last_month['revenue'] * 100) if last_month['revenue'] > 0 else 0
        margin_prev = (prev_month['net'] / prev_month['revenue'] * 100) if prev_month['revenue'] > 0 else 0
        margin_delta = margin_last - margin_prev 
    else:
        rev_delta = exp_delta = net_delta = margin_delta = None
        
    avg_monthly_expenses = monthly['expenses'].mean() if not monthly.empty else 0
    highest_expense_month_val = monthly['expenses'].max() if not monthly.empty else 0
    
    # Find month name for highest expense
    highest_exp_row = monthly.loc[monthly['expenses'].idxmax()] if not monthly.empty else None
    if highest_exp_row is not None:
        # Format date as YYYY-MM
        highest_expense_month_name = str(monthly['expenses'].idxmax()).split(' ')[0][:7]
    else:
        highest_expense_month_name = "N/A"

    # Reuse formatting helpers (duplicated for safety/speed without refactor hell)
    def fmt_money(val): return f"{val:,.0f}" 
    def fmt_delta(val, is_pct=True, suffix_override=None):
        if val is None: return "غير متاح"
        sign = "+" if val >= 0 else ""
        if suffix_override: return f"{sign}{val:.1f} {suffix_override}"
        suffix = "%" if is_pct else ""
        return f"{sign}{val:.1f}{suffix}"

    # Insight Helpers (Same logic)
    def get_rev_insight(val, delta):
        if delta is None: return "لا تتوفر بيانات كافية للمقارنة."
        if delta > 0: return "نمو إيجابي في الإيرادات مقارنة بالشهر السابق."
        if delta < 0: return "تراجع في الإيرادات يتطلب مراجعة أسباب الانخفاض."
        return "استقرار في الإيرادات مقارنة بالشهر السابق."

    def get_exp_insight(val, delta):
        if delta is None: return "لا تتوفر بيانات كافية للمقارنة."
        if delta > 20: return "ارتفاع ملحوظ في المصروفات التشغيلية."
        if delta < -10: return "تحسن في ضبط المصروفات وترشيد الإنفاق."
        return "المصروفات ضمن النطاق المعتاد."
    
    def get_net_insight(val, delta):
        if val < 0: return "تسجيل خسارة صافية خلال الفترة."
        if delta is not None and delta > 0: return "نمو في صافي الأرباح مقارنة بالفترة السابقة."
        return "تحقيق صافي ربح إيجابي."

    def get_margin_insight(val, delta):
        if val < 10: return "هامش الربح منخفض وقد يؤثر على الاستدامة."
        if val > 40: return "هامش ربح صحي وممتاز."
        return "هامش ربح جيد ومستقر."
        
    kpis = [
        { "name": "إجمالي الإيرادات", "value": fmt_money(total_revenue), "delta": fmt_delta(rev_delta), "insight": get_rev_insight(total_revenue, rev_delta) },
        { "name": "إجمالي المصروفات", "value": fmt_money(total_expenses), "delta": fmt_delta(exp_delta), "insight": get_exp_insight(total_expenses, exp_delta) },
        { "name": "صافي الربح", "value": fmt_money(net_profit), "delta": fmt_delta(net_delta), "insight": get_net_insight(net_profit, net_delta) },
        { "name": "هامش الربح", "value": f"{profit_margin:.1f}%", "delta": fmt_delta(margin_delta, is_pct=False, suffix_override="نقطة"), "insight": get_margin_insight(profit_margin, margin_delta) },
        { "name": "متوسط المصروفات", "value": fmt_money(avg_monthly_expenses), "delta": "شهرياً", "insight": "متوسط الإنفاق الشهري التشغيلي." },
        { "name": "أعلى مصروفات", "value": fmt_money(highest_expense_month_val), "delta": highest_expense_month_name, "insight": "الشهر الأعلى إنفاقاً خلال الفترة." },
    ]
    
    # Risks
    risks = []
    if profit_margin < 10: risks.append("هامش الربح الإجمالي منخفض جداً (أقل من 10%)")
    if exp_delta is not None and exp_delta > 20: risks.append(f"ارتفاع حاد في المصروفات الشهرية بنسبة {exp_delta:.1f}%")
    if rev_delta is not None and rev_delta < -15: risks.append(f"انخفاض ملحوظ في الإيرادات الشهرية بنسبة {abs(rev_delta):.1f}%")
    if not monthly.empty and monthly.iloc[-1]['net'] < 0: risks.append("صافي ربح الشهر الأخير سلبي (خسارة)")
    if not risks: risks.append("لم يتم رصد مخاطر حرجة بناءً على البيانات الحالية.")

    # Recommendations
    recommendations_list = []
    for r in risks:
        if "هامش الربح" in r: recommendations_list.append("مراجعة تسعير المنتجات أو خفض التكاليف المباشرة فوراً.")
        elif "ارتفاع حاد" in r: recommendations_list.append("تحليل بنود المصروفات المتضخمة لهذا الشهر ووضع سقف للإنفاق.")
        elif "انخفاض" in r: recommendations_list.append("تفعيل حملات تسويقية عاجلة أو مراجعة أداء فريق المبيعات.")
        elif "خسارة" in r: recommendations_list.append("إجراء مراجعة شاملة للتدفقات النقدية لتجنب أزمة سيولة.")
    
    recommendations = list(dict.fromkeys(recommendations_list))
    if not recommendations: recommendations.append("الاستمرار في مراقبة الأداء المالي للحفاظ على الاستقرار.")
    
    return {
        "kpis": kpis,
        "risks": risks,
        "recommendations": recommendations,
        "monthly_count": len(monthly)
    }

@app.get("/health")
async def health_check():
    return {"ok": True}

@app.get("/reports/{filename}")
async def get_report(filename: str):
    file_path = os.path.join(os.path.dirname(__file__), "reports", filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/pdf", filename=filename)
    raise HTTPException(status_code=404, detail="التقرير غير موجود")

@app.post("/api/analyze")
async def analyze_file(
    request: Request,
    file: UploadFile = File(...),
    concern: Optional[str] = Form(None),
    is_demo: Optional[str] = Form(None)
):
    # Debug Logging for Mobile Connection Issues
    print(f"Incoming Request from Client: {request.client.host}")
    print(f"Origin Header: {request.headers.get('origin', 'No Origin')}")
    if file:
        print(f"Processing File: {file.filename}")

    # Check Rate Limit
    client_ip = request.client.host
    demo_flag = (is_demo == "1")
    
    if not check_rate_limit(client_ip, is_demo=demo_flag):
        msg = "تم الوصول إلى الحد اليومي لمحاولات التحليل التجريبية. يمكنك إعادة المحاولة غدًا." if demo_flag else "تم الوصول إلى الحد اليومي لمحاولة التحليل. يمكنك إعادة المحاولة غدًا."
        return JSONResponse(
            status_code=429,
            content={"detail": msg}
        )

    # 1. Validation Logic
    filename = file.filename or ""
    extension = filename.split(".")[-1].lower() if "." in filename else ""
    if extension not in ["csv", "xlsx", "xls"]:
        raise HTTPException(status_code=400, detail="نوع الملف غير مدعوم. يرجى رفع ملف CSV أو Excel.")
        
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="حجم الملف كبير جداً (الحد الأقصى 10 ميجابايت).")

    # 2. Parse Data
    try:
        df, schema = parse_data(contents, filename)
    except HTTPException as he:
        raise he
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"خطأ في معالجة الملف: {str(e)}")

    # 3. Analyze
    if schema == 'pnl':
        results = calculate_pnl_results(df)
        intro_text = "تم تحليل قائمة دخل شهرية. "
    else:
        results = calculate_kpis(df)
        intro_text = "تم تحليل بيانات معاملات مالية. "
    
    # 4. Generate Summary (Dynamic - Deterministic Draft)
    kpis = results['kpis']
    rev_val = kpis[0]['value']
    profit_val = kpis[2]['value']
    margin_val = kpis[3]['value']
    
    summary_text = f"{intro_text}بناءً على تحليل {results['monthly_count']} شهر من البيانات، "
    summary_text += f"حقق النشاط إجمالي إيرادات {rev_val} بصافي ربح {profit_val}. "
    summary_text += f"هامش الربح الحالي هو {margin_val}. "
    if len(results['risks']) > 0 and "لم يتم رصد" not in results['risks'][0]:
        summary_text += "يرجى الانتباه للمخاطر المرصودة أدناه لضمان الاستدامة المالية."
    else:
        summary_text += "الأداء المالي يبدو مستقراً بشكل عام."
    
    recommendations_list = results['recommendations']

    # 4.5 LLM Executive Rewrite (Optional)
    from utils.llm_writer import write_executive_text
    
    # Payload for LLM
    llm_payload = {
        "summary": summary_text,
        "kpis": kpis,
        "risks": results['risks'],
        "recommendations": recommendations_list
    }
    
    # Try to get enhanced text
    llm_result = await write_executive_text(llm_payload)
    
    if llm_result:
        print("Using LLM Executive Content")
        summary_text = llm_result.get("executive_summary", summary_text)
        recommendations_list = llm_result.get("executive_recommendations", recommendations_list)

    # 5. Generate PDF
    # Pass all data needed for report
    report_data = {
        "summary": summary_text,
        "kpis": kpis,
        "risks": results['risks'],
        "recommendations": recommendations_list
    }
    
    try:
        pdf_filename = await generate_pdf(report_data)
        report_url = f"/reports/{pdf_filename}"
    except Exception as e:
        print(f"Error generating PDF: {e}")
        report_url = None

    # Record successful usage
    record_usage(client_ip, is_demo=demo_flag)
    
    return {
        "summary": summary_text,
        "kpis": results['kpis'],
        "risks": results['risks'],
        "recommendations": recommendations_list,
        "report_pdf_url": report_url
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
