# =========================
# تثبيت المكتبات
# =========================
!pip install streamlit fpdf pandas pyngrok

# =========================
# الكود الكامل للتطبيق
# =========================
import streamlit as st
import random
import pandas as pd
from fpdf import FPDF
import datetime
from collections import defaultdict, Counter
from pyngrok import ngrok
import os

# =========================
# إعداد ngrok
# =========================
ngrok.kill()  # اغلاق أي نفق مفتوح
url = ngrok.connect(port=8501)
print("Open this link on your phone:", url)

# =========================
# إعدادات التطبيق
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
# PDF Generator
# =========================
def generate_pdf(main_df,waste_df,purchase_df,cutting_df,logo_path="logo.png"):
    company_name="NovaStruct Company"
    pdf=FPDF(orientation='L')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=10)

    try:
        pdf.image(logo_path, x=10, y=8, w=30)
    except:
        pass

    # اسم الشركة كبير وأزرق
    pdf.set_font("Arial",'B',22)
    pdf.set_text_color(0,51,102)
    pdf.cell(0,15,company_name,ln=True,align="C")
    pdf.set_text_color(0,0,0)

    # عنوان التقرير
    pdf.set_font("Arial",'B',16)
    pdf.cell(0,10,"Rebar Optimization Report",ln=True,align="C")

    # خط تحت العنوان
    x_left=10
    x_right=pdf.w-10
    y=pdf.get_y()
    pdf.set_line_width(0.7)
    pdf.set_draw_color(0,51,102)
    pdf.line(x_left,y,x_right,y)
    pdf.ln(5)

    pdf.set_font("Arial",'',10)
    pdf.cell(0,8,"Created by Civil Engineer Moustafa Harmouch",ln=True)
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
                pdf.cell(col_widths[i],8,str(row[col]),1,0,"C",fill=fill)
            pdf.ln()
            fill=not fill
        pdf.ln(5)

    # MainBar
    pdf.set_font("Arial",'B',11)
    pdf.cell(0,8,"MainBar",ln=True)
    pdf.set_font("Arial",'',9)
    draw_table(main_df,["Diameter","Length (m)","Quantity","Weight (kg)"],[30,35,30,35])

    # Waste Bars
    pdf.set_font("Arial",'B',11)
    pdf.cell(0,8,"Waste Bars",ln=True)
    pdf.set_font("Arial",'',9)
    draw_table(waste_df,["Diameter","Waste Length (m)","Number of Bars","Waste Weight (kg)"],[30,40,40,40])

    # Purchase
    pdf.set_font("Arial",'B',11)
    pdf.cell(0,8,"Purchase 12m Bars",ln=True)
    pdf.set_font("Arial",'',9)
    draw_table(purchase_df,["Diameter","Bars","Weight (kg)","Cost"],[30,35,40,40])

    # Cutting Instructions
    pdf.set_font("Arial",'B',11)
    pdf.cell(0,8,"Cutting Instructions",ln=True)
    pdf.set_font("Arial",'',8)
    draw_table(cutting_df,["Diameter","Pattern","Count"],[30,140,30])

    pdf.cell(0,8,"Signature: ____________________",ln=True)
    filename=f"Rebar_Report_{datetime.date.today()}.pdf"
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
            rows[i]["Length"]=col1.number_input(f"Length (m) [{i+1}]",value=float(rows[i]["Length"]),key=f"len_{d}_{i}")
            rows[i]["Quantity"]=col2.number_input(f"Quantity [{i+1}]",value=int(rows[i]["Quantity"]),min_value=0,key=f"qty_{d}_{i}")

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
                    main_rows.append({"Diameter":diameter,"Length":r["Length"],"Quantity":r["Quantity"],"Weight":round(weight,2)})
    main_df=pd.DataFrame(main_rows)
    if not main_df.empty:
        main_df=main_df.groupby(["Diameter","Length"]).agg({"Quantity":"sum","Weight":"sum"}).reset_index()

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
        purchase_list.append([d,bars_used,round(total_weight,2),round(cost,2)])

        for bar in solution:
            waste=BAR_LENGTH-sum(bar)
            if waste>0:
                key=(d,round(waste,2))
                waste_dict[key]["count"]+=1
                waste_dict[key]["weight"]+=waste*wpm

        pattern_counts=Counter(tuple(bar) for bar in solution)
        for pattern,count in pattern_counts.items():
            pattern_str=" + ".join([f"{l:.2f} m" for l in pattern])
            cutting_instr.append([d,pattern_str,count])

    waste_data=[]
    for (diameter,waste_len),info in waste_dict.items():
        waste_data.append([diameter,waste_len,info["count"],round(info["weight"],2)])
    waste_df=pd.DataFrame(waste_data,columns=["Diameter","Waste Length (m)","Number of Bars","Waste Weight (kg)"])
    purchase_df=pd.DataFrame(purchase_list,columns=["Diameter","Bars","Weight (kg)","Cost"])
    cutting_df=pd.DataFrame(cutting_instr,columns=["Diameter","Pattern","Count"])

    st.success("Optimization Completed Successfully ✅")
    st.markdown("### MainBar")
    st.dataframe(main_df)
    st.markdown("### Waste Bars")
    st.dataframe(waste_df)
    st.markdown("### Purchase 12m Bars")
    st.dataframe(purchase_df)
    st.markdown("### Cutting Instructions")
    st.dataframe(cutting_df)

    pdf_file=generate_pdf(main_df,waste_df,purchase_df,cutting_df,logo_path="logo.png")
    with open(pdf_file,"rb") as f:
        st.download_button("Download PDF Report",f,file_name=pdf_file)
