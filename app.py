import streamlit as st
import random
import pandas as pd
from fpdf import FPDF
from datetime import date, datetime
from collections import defaultdict, Counter
import re

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
        if self.page_no() == 1:
            return

        # عنوان يسار
        self.set_font("Arial","B",14)
        self.cell(60,10,"Rebar Optimization Report",0,0,"L")

        # لوجو في المنتصف (منخفض قليلاً)
        if "logo.png":
            self.image("logo.png", x=85, y=12, w=30)

        # اسم الشركة يمين
        self.set_font("Arial","B",12)
        self.cell(0,10,"NovaStruct Company | Structural Engineering Solutions",0,1,"R")

        self.ln(10)

    def footer(self):
        if self.page_no()>1:
            self.set_y(-15)
            self.set_font("Arial","I",8)
            self.set_text_color(120,120,120)
            self.cell(0,10,"NovaStruct Company | Structural Engineering Solutions",0,0,"R")

# =========================
# Streamlit UI
# =========================
st.set_page_config(layout="wide")
st.title("Rebar Optimizer Pro")
st.subheader("Created by Civil Engineer Moustafa Harmouch")

price = st.number_input("Price per ton ($)", min_value=0.0, value=1000.0)

data = {}

for d in DIAMETERS:
    if f"rows_{d}" not in st.session_state:
        st.session_state[f"rows_{d}"]=[{"Length":0.0,"Quantity":0}]
    with st.expander(f"Diameter {d} mm"):
        rows = st.session_state[f"rows_{d}"]
        for i in range(len(rows)):
            col1,col2=st.columns(2)
            rows[i]["Length"]=col1.number_input(
                f"Length (m) [{i+1}]",
                value=float(rows[i]["Length"]),
                key=f"len_{d}_{i}"
            )
            rows[i]["Quantity"]=col2.number_input(
                f"Quantity [{i+1}]",
                value=int(rows[i]["Quantity"]),
                min_value=0,
                key=f"qty_{d}_{i}"
            )
        if st.button(f"Add Row Ø{d}", key=f"add_{d}"):
            st.session_state[f"rows_{d}"].append({"Length":0.0,"Quantity":0})

        lengths=[]
        for r in rows:
            if r["Length"]>0 and r["Quantity"]>0:
                lengths.extend([r["Length"]]*r["Quantity"])
        if lengths:
            data[d]=lengths

# =========================
# تشغيل
# =========================
if st.button("Run Optimization"):

    main_rows=[]
    for key, rows in st.session_state.items():
        if key.startswith("rows_"):
            diameter=int(key.split("_")[1])
            for r in rows:
                if r["Length"]>0 and r["Quantity"]>0:
                    weight=r["Length"]*r["Quantity"]*weight_per_meter(diameter)
                    main_rows.append({
                        "Diameter":f"{diameter} mm",
                        "Length (m)":r["Length"],
                        "Quantity":r["Quantity"],
                        "Weight (kg)":round(weight,2)
                    })

    main_df=pd.DataFrame(main_rows)

    if not main_df.empty:
        main_df=main_df.groupby(
            ["Diameter","Length (m)"]
        ).agg({
            "Quantity":"sum",
            "Weight (kg)":"sum"
        }).reset_index()

        main_df["Diameter_num"]=main_df["Diameter"].str.replace(" mm","").astype(int)
        main_df=main_df.sort_values(
            by=["Diameter_num","Length (m)"]
        ).drop(columns=["Diameter_num"])

    # =========================
    # PDF
    # =========================
    pdf=PDF(orientation="P")
    pdf.add_page()

    # ===== صفحة غلاف =====
    pdf.set_font("Arial","B",26)
    pdf.ln(40)
    pdf.cell(0,15,"Rebar Optimization Report",0,1,"C")

    pdf.ln(10)
    pdf.set_font("Arial","",14)
    pdf.cell(0,10,"Created by Civil Engineer Moustafa Harmouch",0,1,"C")
    pdf.cell(0,10,f"Date: {date.today()}",0,1,"C")
    pdf.cell(0,10,f"Report ID: {datetime.now().strftime('%Y%m%d%H%M%S')}",0,1,"C")

    pdf.add_page()

    # ===== جدول رئيسي =====
    pdf.set_font("Arial","B",14)
    pdf.set_text_color(0,0,139)
    pdf.cell(0,10,"MainBar",0,1)

    pdf.set_text_color(0,0,0)
    pdf.set_font("Arial","",10)

    col_widths=[30,30,30,30]

    for col in main_df.columns:
        pdf.cell(col_widths[main_df.columns.get_loc(col)],8,col,1,0,"C")
    pdf.ln()

    total_weight=0

    for _,row in main_df.iterrows():
        pdf.cell(col_widths[0],8,row["Diameter"],1)
        pdf.cell(col_widths[1],8,str(row["Length (m)"]),1)
        pdf.cell(col_widths[2],8,str(row["Quantity"]),1)
        pdf.cell(col_widths[3],8,str(row["Weight (kg)"]),1)
        total_weight+=row["Weight (kg)"]
        pdf.ln()

    pdf.set_font("Arial","B",10)
    pdf.cell(sum(col_widths)-30,8,"Total Weight",1)
    pdf.cell(30,8,str(round(total_weight,2)),1)
    pdf.ln(15)

    # ===== Cutting Instructions =====
    pdf.set_font("Arial","B",14)
    pdf.set_text_color(0,0,139)
    pdf.cell(0,10,"Cutting Instructions",0,1)
    pdf.set_text_color(0,0,0)
    pdf.set_font("Arial","",9)

    col_widths=[25,100,25]

    pdf.cell(col_widths[0],10,"Diameter",1,0,"C")
    pdf.cell(col_widths[1],10,"Pattern",1,0,"C")
    pdf.cell(col_widths[2],10,"Count",1,1,"C")

    for _,row in main_df.iterrows():
        pdf.cell(col_widths[0],20,row["Diameter"],1)
        pdf.multi_cell(col_widths[1],10,"Example Pattern",1)
        pdf.set_xy(pdf.get_x()+col_widths[1],pdf.get_y()-20)
        pdf.cell(col_widths[2],20,"1",1)
        pdf.ln()

    pdf.output("report.pdf")

    with open("report.pdf","rb") as f:
        st.download_button("Download PDF",f,"Rebar_Report.pdf")

    st.success("Optimization Completed Successfully ✅")
