import streamlit as st
import random
import pandas as pd
from fpdf import FPDF
import datetime
from collections import defaultdict, Counter

# =========================
# إعدادات عامة
# =========================
BAR_LENGTH = 12.0
ITERATIONS = 3000
DIAMETERS = [6,8,10,12,14,16,18,20,22,25,32]

def weight_per_meter(diameter):
    return (diameter**2)/162

def optimize_cutting(lengths):
    best_solution = None
    min_waste = float("inf")
    min_bars = float("inf")

    for _ in range(ITERATIONS):
        shuffled = lengths[:]
        random.shuffle(shuffled)
        shuffled.sort(reverse=True)

        bars=[]
        for length in shuffled:
            placed=False
            for bar in bars:
                if sum(bar)+length<=BAR_LENGTH:
                    bar.append(length)
                    placed=True
                    break
            if not placed:
                bars.append([length])

        waste=sum(BAR_LENGTH - sum(bar) for bar in bars)

        if waste < min_waste or (waste==min_waste and len(bars)<min_bars):
            min_waste=waste
            min_bars=len(bars)
            best_solution=bars

    return best_solution

# =========================
# PDF Class
# =========================
class PDF(FPDF):

    def header(self):
        if self.page_no() > 1:
            self.set_font("Arial",'B',60)
            self.set_text_color(235,235,235)
            self.rotate(45, x=self.w/2, y=self.h/2)
            self.text(self.w/4, self.h/2, "NovaStruct")
            self.rotate(0)
            self.set_text_color(0,0,0)

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font("Arial",'I',8)
            self.set_text_color(120,120,120)
            # الفوتر على أقصى اليمين
            self.cell(0,10,"NovaStruct Company | Structural Engineering Solutions",0,0,"R")

# =========================
# PDF Generator
# =========================
def generate_pdf(main_df,waste_df,purchase_df,cutting_df,
                 total_main_weight,total_waste_weight,
                 total_purchase_weight,total_cost,
                 logo_path="logo.png",
                 signature_path="signature.png"):

    company_name="NovaStruct Company"
    engineer_name="Civil Engineer Moustafa Harmouch"
    signature="Structural Engineering Specialist"
    report_number=f"NS-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"

    pdf=PDF(orientation='L')
    pdf.set_auto_page_break(auto=True, margin=15)

    # ====================================
    # صفحة الغلاف
    # ====================================
    pdf.add_page()
    pdf.set_fill_color(230,240,255)
    pdf.rect(0,0,pdf.w,pdf.h,"F")
    pdf.set_fill_color(0,51,102)
    pdf.rect(0,0,25,pdf.h,"F")

    # رفع اللوجو أعلى الصفحة
    try:
        pdf.image(logo_path, x=pdf.w/2-35, y=10, w=70)
    except:
        pass

    pdf.ln(90)
    pdf.set_font("Arial",'B',38)
    pdf.set_text_color(0,51,102)
    pdf.cell(0,20,"Rebar Optimization Report",ln=True,align="C")

    pdf.set_draw_color(0,51,102)
    pdf.set_line_width(1)
    pdf.line(80, pdf.get_y()+5, pdf.w-80, pdf.get_y()+5)

    pdf.ln(20)
    pdf.set_font("Arial",'B',24)
    pdf.cell(0,15,company_name,ln=True,align="C")

    pdf.ln(10)
    pdf.set_font("Arial",'B',26)
    pdf.set_text_color(40,40,40)
    pdf.cell(0,15,engineer_name,ln=True,align="C")

    # إضافة صورة التوقيع أسفل اسم المهندس
    try:
        pdf.image(signature_path, x=pdf.w/2-40, y=pdf.get_y(), w=80)
    except:
        pass

    pdf.set_font("Arial",'I',18)
    pdf.set_text_color(90,90,90)
    pdf.ln(20)
    pdf.cell(0,10,signature,ln=True,align="C")

    pdf.set_text_color(0,0,0)
    pdf.ln(15)
    pdf.set_font("Arial",'',16)
    pdf.cell(0,10,f"Report No: {report_number}",ln=True,align="C")
    pdf.cell(0,10,f"Date: {datetime.date.today()}",ln=True,align="C")

    # ====================================
    # صفحة التقرير (الهيدر الجديد)
    # ====================================
    pdf.add_page()
    start_y = 10
    pdf.set_y(start_y)
    pdf.set_font("Arial",'B',18)
    pdf.set_text_color(0,0,0)
    pdf.set_x(10)
    pdf.cell(0,10,company_name,ln=0,align="L")
    pdf.set_x(0)
    pdf.cell(0,10,"Rebar Optimization Report",ln=0,align="C")
    try:
        pdf.image(logo_path, x=pdf.w-75, y=start_y-2, w=65)
    except:
        pass
    pdf.ln(25)
    pdf.set_font("Arial",'',10)
    pdf.cell(0,8,f"Report No: {report_number}",ln=True)
    pdf.cell(0,8,f"Date: {datetime.date.today()}",ln=True)
    pdf.ln(5)

    # ====================================
    # رسم الجداول باللون الأزرق الداكن للعناوين
    # ====================================
    def draw_table(df,headers,col_widths):
        pdf.set_fill_color(0,51,102)   # الأزرق الداكن
        pdf.set_text_color(255,255,255) # نص أبيض
        pdf.set_font("Arial",'B',9)
        for i,h in enumerate(headers):
            pdf.cell(col_widths[i],8,h,1,0,"C",fill=True)
        pdf.ln()
        pdf.set_text_color(0,0,0)
        fill=False
        for _,row in df.iterrows():
            pdf.set_fill_color(245,245,245)
            for i,col in enumerate(headers):
                value=str(row[col]) if col in df.columns else ""
                pdf.cell(col_widths[i],8,value,1,0,"C",fill=fill)
            pdf.ln()
            fill=not fill
        pdf.ln(4)

    pdf.set_font("Arial",'B',12)
    pdf.cell(0,8,"MainBar",ln=True)
    pdf.set_font("Arial",'',9)
    draw_table(main_df, ["Diameter","Length (m)","Quantity","Weight (kg)"], [35,40,35,40])

    pdf.cell(0,8,"Waste Bars",ln=True)
    draw_table(waste_df, ["Diameter","Waste Length (m)","Number of Bars","Waste Weight (kg)"], [35,45,45,45])

    pdf.cell(0,8,"Purchase 12m Bars",ln=True)
    draw_table(purchase_df, ["Diameter","Bars","Weight (kg)","Cost"], [35,35,45,45])

    pdf.cell(0,8,"Cutting Instructions",ln=True)
    draw_table(cutting_df, ["Diameter","Pattern","Count"], [35,160,35])

    filename=f"{report_number}.pdf"
    pdf.output(filename)
    return filename
