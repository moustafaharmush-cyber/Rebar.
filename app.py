import streamlit as st
import random
import pandas as pd
from fpdf import FPDF
from datetime import date, datetime
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
# PDF Class مع الهيدر والفوتر
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
            self.cell(0,10,"NovaStruct Company | Structural Engineering Solutions",0,0,"R")

# =========================
# واجهة Streamlit
# =========================
st.set_page_config(layout="wide")
st.title("Rebar Optimizer Pro")
st.subheader("Created by Civil Engineer Moustafa Harmouch")

price = st.number_input("Price per ton ($)", min_value=0.0, value=1000.0)

data = {}
for d in DIAMETERS:
    if f"rows_{d}" not in st.session_state:
        st.session_state[f"rows_{d}"] = [{"Length":0.0,"Quantity":0}]
    with st.expander(f"Diameter {d} mm"):
        rows = st.session_state[f"rows_{d}"]
        for i in range(len(rows)):
            col1,col2 = st.columns(2)
            rows[i]["Length"] = col1.number_input(f"Length (m) [{i+1}]", value=float(rows[i]["Length"]), key=f"len_{d}_{i}")
            rows[i]["Quantity"] = col2.number_input(f"Quantity [{i+1}]", value=int(rows[i]["Quantity"]), min_value=0, key=f"qty_{d}_{i}")
        if st.button(f"Add Row Ø{d}", key=f"add_{d}"):
            st.session_state[f"rows_{d}"].append({"Length":0.0,"Quantity":0})
        lengths=[]
        for r in rows:
            if r["Length"]>0 and r["Quantity"]>0:
                lengths.extend([r["Length"]]*r["Quantity"])
        if lengths:
            data[d] = lengths

# =========================
# تشغيل التحسين
# =========================
if st.button("Run Optimization"):
    main_rows=[]
    for key, rows in st.session_state.items():
        if key.startswith("rows_"):
            diameter=int(key.split("_")[1])
            for r in rows:
                if r["Length"]>0 and r["Quantity"]>0:
                    weight = r["Length"]*r["Quantity"]*weight_per_meter(diameter)
                    main_rows.append({
                        "Diameter": f"{diameter} mm",
                        "Length (m)": r["Length"],
                        "Quantity": r["Quantity"],
                        "Weight (kg)": round(weight,2)
                    })
    main_df = pd.DataFrame(main_rows)
    if not main_df.empty:
        main_df = main_df.groupby(["Diameter","Length (m)"]).agg({"Quantity":"sum","Weight (kg)":"sum"}).reset_index()

    waste_dict = defaultdict(lambda: {"count":0,"weight":0})
    purchase_list=[]
    cutting_instr=[]

    for d, lengths in data.items():
        solution = optimize_cutting(lengths)
        if not solution:
            continue
        bars_used = len(solution)
        wpm = weight_per_meter(d)
        total_weight = bars_used * BAR_LENGTH * wpm
        cost = (total_weight/1000)*price
        purchase_list.append([f"{d} mm", bars_used, round(total_weight,2), round(cost,2)])

        for bar in solution:
            waste = BAR_LENGTH - sum(bar)
            if waste>0:
                key=(f"{d} mm", round(waste,2))
                waste_dict[key]["count"]+=1
                waste_dict[key]["weight"]+=waste*wpm

        pattern_counts=Counter(tuple(bar) for bar in solution)
        for pattern,count in pattern_counts.items():
            pattern_str = " + ".join([f"{l:.2f} m" for l in pattern])
            cutting_instr.append([f"{d} mm", pattern_str,count])

    waste_data=[]
    for (diameter,waste_len),info in waste_dict.items():
        waste_data.append([diameter, waste_len, info["count"], round(info["weight"],2)])
    waste_df=pd.DataFrame(waste_data, columns=["Diameter","Waste Length (m)","Number of Bars","Waste Weight (kg)"])
    purchase_df=pd.DataFrame(purchase_list, columns=["Diameter","Bars","Weight (kg)","Cost"])
    cutting_df=pd.DataFrame(cutting_instr, columns=["Diameter","Pattern","Count"])

    st.success("Optimization Completed Successfully ✅")
    st.markdown("### MainBar")
    st.dataframe(main_df)
    st.markdown("### Waste Bars")
    st.dataframe(waste_df)
    st.markdown("### Purchase 12m Bars")
    st.dataframe(purchase_df)
    st.markdown("### Cutting Instructions")
    st.dataframe(cutting_df)

    # =========================
    # PDF Generator Portrait
    # =========================
    pdf_file = "Rebar_Report.pdf"
    pdf = PDF(orientation='P')
    pdf.set_auto_page_break(auto=True, margin=20)

    logo_path = "logo.png"
    company_name="NovaStruct Company"
    engineer_name="Civil Engineer Moustafa Harmouch"
    report_number=f"NS-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    # ==== صفحة الغلاف ====
    pdf.add_page()
    pdf.set_fill_color(230,240,255)
    pdf.rect(0,0,pdf.w,pdf.h,"F")
    try:
        pdf.image(logo_path, x=pdf.w/2-35, y=40, w=70)  # رفع اللوجو أعلى
    except:
        pass
    pdf.ln(120)
    pdf.set_font("Arial",'B',38)
    pdf.set_text_color(0,51,102)
    pdf.cell(0,20,"Rebar Optimization Report",ln=True,align="C")
    pdf.ln(20)
    pdf.set_font("Arial",'B',26)
    pdf.cell(0,15,company_name,ln=True,align="C")
    pdf.ln(10)
    pdf.set_font("Arial",'B',26)
    pdf.cell(0,15,engineer_name,ln=True,align="C")
    pdf.set_font("Arial",'',16)
    pdf.ln(20)
    pdf.cell(0,10,f"Report No: {report_number}",ln=True,align="C")
    pdf.cell(0,10,f"Date: {date.today()}",ln=True,align="C")

    # ==== الصفحة الثانية مع الهيدر ====
    pdf.add_page()
    start_y = 10
    pdf.set_y(start_y)
    pdf.set_font("Arial",'B',18)
    pdf.set_text_color(0,0,0)
    pdf.set_xy(10, start_y)
    pdf.cell(80,15,"Rebar Optimization Report", ln=0, align="L")
    try:
        pdf.image(logo_path, x=(pdf.w/2)-25, y=start_y+5, w=50)  # إنزال اللوجو قليلاً
    except:
        pass
    pdf.set_xy(pdf.w-110, start_y)
    pdf.cell(100,15, company_name, ln=0, align="R")
    pdf.ln(30)
    pdf.set_font("Arial",'',10)
    pdf.cell(0,8,f"Report No: {report_number}", ln=True)
    pdf.cell(0,8,f"Date: {date.today()}", ln=True)
    pdf.ln(10)

    # ==== دالة رسم الجداول ====
    def draw_table(df, headers, col_widths, title="", sum_columns=[]):
        if title:
            pdf.set_font("Arial",'B',16)
            pdf.set_text_color(0,51,102)
            pdf.cell(0,10,title,ln=True,align="L")
            pdf.ln(5)

        pdf.set_fill_color(0,51,102)
        pdf.set_text_color(255,255,255)
        pdf.set_font("Arial",'B',10)

        def draw_table_header():
            if title:
                pdf.set_font("Arial",'B',16)
                pdf.set_text_color(0,51,102)
                pdf.cell(0,10,title,ln=True,align="L")
                pdf.ln(5)
            pdf.set_fill_color(0,51,102)
            pdf.set_text_color(255,255,255)
            pdf.set_font("Arial",'B',10)
            for i,h in enumerate(headers):
                pdf.cell(col_widths[i],12,h,1,0,"C",fill=True)
            pdf.ln()
            pdf.set_text_color(0,0,0)

        fill=False
        totals={col:0 for col in sum_columns}

        for idx, row in df.iterrows():
            if pdf.get_y() > pdf.h - 30:
                pdf.add_page()
                draw_table_header()
            pdf.set_fill_color(245,245,245) if fill else pdf.set_fill_color(255,255,255)
            for i,col in enumerate(headers):
                value=str(row[col]) if col in df.columns else ""
                pdf.cell(col_widths[i],10,value,1,0,"C",fill=fill)
                if col in sum_columns:
                    totals[col]+=float(row[col])
            pdf.ln()
            fill=not fill

        if sum_columns:
            pdf.set_fill_color(200,200,200)
            pdf.set_font("Arial",'B',10)
            for i,col in enumerate(headers):
                if col in sum_columns:
                    pdf.cell(col_widths[i],10,f"{totals[col]:.2f}",1,0,"C",fill=True)
                elif i==0:
                    pdf.cell(col_widths[i],10,"TOTAL",1,0,"C",fill=True)
                else:
                    pdf.cell(col_widths[i],10,"",1,0,"C",fill=True)
            pdf.ln(12)

    # ==== رسم جميع الجداول ====
    draw_table(main_df, ["Diameter","Length (m)","Quantity","Weight (kg)"], [35,45,35,35], title="MainBar", sum_columns=["Weight (kg)"])
    draw_table(waste_df, ["Diameter","Waste Length (m)","Number of Bars","Waste Weight (kg)"], [35,50,40,40], title="Waste Bars", sum_columns=["Waste Weight (kg)"])
    draw_table(purchase_df, ["Diameter","Bars","Weight (kg)","Cost"], [35,35,40,40], title="Purchase 12m Bars", sum_columns=["Weight (kg)","Cost"])
    draw_table(cutting_df, ["Diameter","Pattern","Count"], [35,100,35], title="Cutting Instructions")  # ✅ تم تعديل العرض من 150→100

    pdf.output(pdf_file)
    with open(pdf_file,"rb") as f:
        st.download_button("Download PDF Report", f, file_name=pdf_file)
