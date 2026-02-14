import streamlit as st
import random
import pandas as pd
from fpdf import FPDF
import datetime
from collections import defaultdict, Counter

# =========================
# إعدادات التطبيق
# =========================
BAR_LENGTH = 12.0
ITERATIONS = 3000
DIAMETERS = [6, 8, 10, 12, 14, 16, 18, 20, 22, 25, 32]

# =========================
# وزن لكل متر
# =========================
def weight_per_meter(diameter):
    return (diameter ** 2) / 162

# =========================
# تحسين القطع
# =========================
def optimize_cutting(lengths):
    best_solution = None
    min_waste = float("inf")
    min_bars = float("inf")
    for _ in range(ITERATIONS):
        shuffled = lengths[:]
        random.shuffle(shuffled)
        shuffled.sort(reverse=True)
        bars = []
        for length in shuffled:
            placed = False
            for bar in bars:
                if sum(bar) + length <= BAR_LENGTH:
                    bar.append(length)
                    placed = True
                    break
            if not placed:
                bars.append([length])
        waste = sum(BAR_LENGTH - sum(bar) for bar in bars)
        if waste < min_waste or (waste == min_waste and len(bars) < min_bars):
            min_waste = waste
            min_bars = len(bars)
            best_solution = bars
    return best_solution

# =========================
# توليد تقرير PDF مع تصميم هندسي
# =========================
def generate_pdf(main_df, waste_df, purchase_df, cutting_df, logo_path="logo.png"):
    company_name = "NovaStruct Company"
    pdf = FPDF(orientation='L')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)

    # شعار الشركة
    try:
        pdf.image(logo_path, x=10, y=8, w=30)
    except:
        pass

    # اسم الشركة كبير وأزرق داكن
    pdf.set_font("Arial", 'B', 22)
    pdf.set_text_color(0, 51, 102)  # أزرق داكن
    pdf.cell(0, 15, company_name, ln=True, align="C")

    # إعادة اللون الأسود لبقية التقرير
    pdf.set_text_color(0, 0, 0)

    # عنوان التقرير
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, "Rebar Optimization Report", ln=True, align="C")

    # خط تحت العنوان
    x_left = 10
    x_right = pdf.w - 10
    y = pdf.get_y()
    pdf.set_line_width(0.7)
    pdf.set_draw_color(0, 51, 102)  # أزرق داكن
    pdf.line(x_left, y, x_right, y)
    pdf.ln(5)

    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 8, "Created by Civil Engineer Moustafa Harmouch", ln=True)
    pdf.cell(0, 8, f"Date: {datetime.date.today()}", ln=True)
    pdf.ln(5)

    # =========================
    # دالة رسم الجداول مع تلوين هندسي
    # =========================
    def draw_table(df, headers, col_widths):
        # رؤوس الجداول ملونة أزرق داكن مع خط أبيض
        pdf.set_fill_color(0, 51, 102)  # أزرق داكن
        pdf.set_text_color(255, 255, 255)  # أبيض
        pdf.set_font("Arial", 'B', 9)
        for i, h in enumerate(headers):
            pdf.cell(col_widths[i], 8, h, border=1, align="C", fill=True)
        pdf.ln()
        pdf.set_text_color(0, 0, 0)  # إعادة اللون الأسود للصفوف

        # الصفوف متناوبة بالرمادي الفاتح
        fill = False
        for _, row in df.iterrows():
            pdf.set_fill_color(245, 245, 245)
            for i, col in enumerate(headers):
                pdf.cell(col_widths[i], 8, str(row[col]), 1, 0, "C", fill=fill)
            pdf.ln()
            fill = not fill

        pdf.ln(5)

    # =========================
    # MainBar
    # =========================
    st_columns = ["Diameter", "Length (m)", "Quantity", "Weight (kg)"]
    st_col_widths = [30, 35, 30, 35]
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "MainBar", ln=True)
    pdf.set_font("Arial", '', 9)
    draw_table(main_df, st_columns, st_col_widths)

    # =========================
    # Waste Bars
    # =========================
    st_columns = ["Diameter", "Waste Length (m)", "Number of Bars", "Waste Weight (kg)"]
    st_col_widths = [30, 40, 40, 40]
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "Waste Bars", ln=True)
    pdf.set_font("Arial", '', 9)
    draw_table(waste_df, st_columns, st_col_widths)

    # =========================
    # Purchase 12m Bars
    # =========================
    st_columns = ["Diameter", "Bars", "Weight (kg)", "Cost"]
    st_col_widths = [30, 35, 40, 40]
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "Purchase 12m Bars", ln=True)
    pdf.set_font("Arial", '', 9)
    draw_table(purchase_df, st_columns, st_col_widths)

    # =========================
    # Cutting Instructions
    # =========================
    st_columns = ["Diameter", "Pattern", "Count"]
    st_col_widths = [30, 140, 30]
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, "Cutting Instructions", ln=True)
    pdf.set_font("Arial", '', 8)
    draw_table(cutting_df, st_columns, st_col_widths)

    pdf.cell(0, 8, "Signature: ____________________", ln=True)
    filename = f"Rebar_Report_{datetime.date.today()}.pdf"
    pdf.output(filename)
    return filename
