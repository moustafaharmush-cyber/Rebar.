import streamlit as st
import random
import pandas as pd
from fpdf import FPDF
import datetime
from collections import defaultdict, Counter
import math

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
# PDF Class (لإضافة Watermark بكل الصفحات)
# =========================
class PDF(FPDF):

    def header(self):
        if self.page_no() > 1:
            self.set_font("Arial",'B',50)
            self.set_text_color(230,230,230)
            self.rotate(45, x=self.w/2, y=self.h/2)
            self.text(self.w/4, self.h/2, "NovaStruct")
            self.rotate(0)
            self.set_text_color(0,0,0)

    def footer(self):
        if self.page_no() > 1:
            self.set_y(-15)
            self.set_font("Arial",'I',8)
            self.set_text_color(120,120,120)
            self.cell(0,10,"NovaStruct Company | Structural Engineering Solutions",0,0,"C")


# =========================
# PDF Generator
# =========================
def generate_pdf(main_df,waste_df,purchase_df,cutting_df,
                 total_main_weight,total_waste_weight,
                 total_purchase_weight,total_cost,
                 logo_path="logo.png"):

    company_name="NovaStruct Company"
    report_number=f"NS-{datetime.datetime.now().strftime('%Y%m%d-%H%M%S')}"

    pdf=PDF(orientation='L')
    pdf.set_auto_page_break(auto=True, margin=15)

    # ====================================
    # صفحة الغلاف
    # ====================================
    pdf.add_page()

    pdf.set_fill_color(230,240,255)
    pdf.rect(0,0,pdf.w,pdf.h,"F")

    try:
        pdf.image(logo_path, x=pdf.w/2-30, y=20, w=60)
    except:
        pass

    pdf.ln(60)
    pdf.set_font("Arial",'B',36)
    pdf.set_text_color(0,51,102)
    pdf.cell(0,20,"Rebar Optimization Report",ln=True,align="C")

    pdf.set_font("Arial",'B',22)
    pdf.ln(10)
    pdf.cell(0,15,company_name,ln=True,align="C")

    pdf.set_font("Arial",'',16)
    pdf.ln(5)
    pdf.cell(0,10,f"Report No: {report_number}",ln=True,align="C")
    pdf.cell(0,10,f"Date: {datetime.date.today()}",ln=True,align="C")

    # ====================================
    # صفحة التقرير
    # ====================================
    pdf.add_page()

    # Header
    pdf.set_font("Arial",'B',18)
    pdf.cell(0,10,company_name,align="L")

    try:
        pdf.image(logo_path, x=pdf.w-70, y=8, w=60)
    except:
        pass

    pdf.ln(15)

    pdf.set_font("Arial",'B',16)
    pdf.cell(0,10,"Rebar Optimization Report",ln=True,align="C")

    pdf.set_font("Arial",'',10)
    pdf.cell(0,8,f"Report No: {report_number}",ln=True)
    pdf.cell(0,8,f"Date: {datetime.date.today()}",ln=True)
    pdf.ln(5)

    def draw_table(df,headers,col_widths):
        pdf.set_fill_color(0,51,102)
        pdf.set_text_color(255,255,255)
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

    # MainBar
    pdf.set_font("Arial",'B',12)
    pdf.cell(0,8,"MainBar",ln=True)
    pdf.set_font("Arial",'',9)
    draw_table(main_df,
               ["Diameter","Length (m)","Quantity","Weight (kg)"],
               [35,40,35,40])
    pdf.set_font("Arial",'B',10)
    pdf.cell(0,8,f"Total Main Steel Weight: {total_main_weight:.2f} kg",ln=True)
    pdf.ln(4)

    # Waste
    pdf.set_font("Arial",'B',12)
    pdf.cell(0,8,"Waste Bars",ln=True)
    pdf.set_font("Arial",'',9)
    draw_table(waste_df,
               ["Diameter","Waste Length (m)","Number of Bars","Waste Weight (kg)"],
               [35,45,45,45])
    pdf.set_font("Arial",'B',10)
    pdf.cell(0,8,f"Total Waste Weight: {total_waste_weight:.2f} kg",ln=True)
    pdf.ln(4)

    # Purchase
    pdf.set_font("Arial",'B',12)
    pdf.cell(0,8,"Purchase 12m Bars",ln=True)
    pdf.set_font("Arial",'',9)
    draw_table(purchase_df,
               ["Diameter","Bars","Weight (kg)","Cost"],
               [35,35,45,45])
    pdf.set_font("Arial",'B',10)
    pdf.cell(0,8,f"Total Purchase Weight: {total_purchase_weight:.2f} kg",ln=True)
    pdf.cell(0,8,f"Total Cost: ${total_cost:.2f}",ln=True)
    pdf.ln(5)

    # Cutting
    pdf.set_font("Arial",'B',12)
    pdf.cell(0,8,"Cutting Instructions",ln=True)
    pdf.set_font("Arial",'',8)
    draw_table(cutting_df,
               ["Diameter","Pattern","Count"],
               [35,160,35])

    filename=f"{report_number}.pdf"
    pdf.output(filename)

    return filename


# =========================
# Streamlit UI
# =========================
st.set_page_config(layout="wide")
st.title("Rebar Optimizer Pro")
st.subheader("Created by Civil Engineer Moustafa Harmouch")

price = st.number_input("Price per ton ($)", min_value=0.0, value=1000.0)
data={}

for d in DIAMETERS:
    if f"rows_{d}" not in st.session_state:
        st.session_state[f"rows_{d}"]=[{"Length":0.0,"Quantity":0}]

    with st.expander(f"Diameter {d} mm"):
        rows=st.session_state[f"rows_{d}"]

        for i in range(len(rows)):
            col1,col2=st.columns(2)
            rows[i]["Length"]=col1.number_input(f"Length (m) [{i+1}]",
                                                value=float(rows[i]["Length"]),
                                                key=f"len_{d}_{i}")
            rows[i]["Quantity"]=col2.number_input(f"Quantity [{i+1}]",
                                                  value=int(rows[i]["Quantity"]),
                                                  min_value=0,
                                                  key=f"qty_{d}_{i}")

        if st.button(f"Add Row Ø{d}",key=f"add_{d}"):
            st.session_state[f"rows_{d}"].append({"Length":0.0,"Quantity":0})

        lengths=[]
        for r in rows:
            if r["Length"]>0 and r["Quantity"]>0:
                lengths.extend([r["Length"]]*r["Quantity"])

        if lengths:
            data[d]=lengths


if st.button("Run Optimization"):

    main_rows=[]

    for key,rows in st.session_state.items():
        if key.startswith("rows_"):
            diameter=int(key.split("_")[1])

            for r in rows:
                if r["Length"]>0 and r["Quantity"]>0:
                    weight=r["Length"]*r["Quantity"]*weight_per_meter(diameter)
                    main_rows.append({
                        "Diameter":diameter,
                        "Length":round(r["Length"],2),
                        "Quantity":r["Quantity"],
                        "Weight":round(weight,2)
                    })

    main_df=pd.DataFrame(main_rows)

    if not main_df.empty:
        main_df = main_df.groupby(["Diameter","Length"]).agg({
            "Quantity":"sum",
            "Weight":"sum"
        }).reset_index()

        main_df = main_df.sort_values(by=["Diameter","Length"])

        main_df = main_df.rename(columns={
            "Length":"Length (m)",
            "Weight":"Weight (kg)"
        })

        main_df["Diameter"] = main_df["Diameter"].astype(int).astype(str) + " mm"
        main_df["Length (m)"] = main_df["Length (m)"].astype(str)
        main_df["Quantity"] = main_df["Quantity"].astype(str)
        main_df["Weight (kg)"] = main_df["Weight (kg)"].astype(str)

    waste_dict=defaultdict(lambda:{"count":0,"weight":0})
    purchase_list=[]
    cutting_instr=[]

    for d,lengths in data.items():
        solution=optimize_cutting(lengths)
        if not solution:
            continue

        bars_used=len(solution)
        wpm=weight_per_meter(d)
        total_weight=bars_used*BAR_LENGTH*wpm
        cost=(total_weight/1000)*price

        purchase_list.append([f"{d} mm",bars_used,round(total_weight,2),round(cost,2)])

        for bar in solution:
            waste=round(BAR_LENGTH-sum(bar),2)
            if waste>0:
                key=(f"{d} mm",waste)
                waste_dict[key]["count"]+=1
                waste_dict[key]["weight"]+=waste*wpm

        pattern_counts=Counter(tuple(bar) for bar in solution)

        for pattern,count in pattern_counts.items():
            pattern_str=" + ".join([f"{round(l,2)} m" for l in pattern])
            cutting_instr.append([f"{d} mm",pattern_str,count])

    waste_data=[]
    for (diameter,waste_len),info in waste_dict.items():
        waste_data.append([diameter,waste_len,info["count"],round(info["weight"],2)])

    waste_df=pd.DataFrame(waste_data,
        columns=["Diameter","Waste Length (m)","Number of Bars","Waste Weight (kg)"])

    purchase_df=pd.DataFrame(purchase_list,
        columns=["Diameter","Bars","Weight (kg)","Cost"])

    cutting_df=pd.DataFrame(cutting_instr,
        columns=["Diameter","Pattern","Count"])

    total_main_weight = sum(float(w) for w in main_df["Weight (kg)"]) if not main_df.empty else 0
    total_purchase_weight = purchase_df["Weight (kg)"].sum() if not purchase_df.empty else 0
    total_cost = purchase_df["Cost"].sum() if not purchase_df.empty else 0
    total_waste_weight = waste_df["Waste Weight (kg)"].sum() if not waste_df.empty else 0

    st.success("Optimization Completed Successfully ✅")

    st.dataframe(main_df)
    st.dataframe(waste_df)
    st.dataframe(purchase_df)
    st.dataframe(cutting_df)

    pdf_file=generate_pdf(main_df,waste_df,purchase_df,cutting_df,
                          total_main_weight,total_waste_weight,
                          total_purchase_weight,total_cost,
                          logo_path="logo.png")

    with open(pdf_file,"rb") as f:
        st.download_button("Download PDF Report",f,file_name=pdf_file)
