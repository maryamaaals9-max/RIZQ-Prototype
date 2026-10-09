import io
import math
from datetime import date
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(page_title="RIZQ | Climate Retrofit Intelligence", page_icon="🌿", layout="wide", initial_sidebar_state="expanded")

st.markdown('''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
html,body,[class*="css"], [data-testid="stApp"] {font-family:'DM Sans',sans-serif;}
[data-testid="stAppViewContainer"] {background:#f5f9f7;}
[data-testid="stHeader"] {background:#ffffffed;}
[data-testid="stMainBlockContainer"] {padding-top:2rem;}
[data-testid="stVerticalBlockBorderWrapper"] > div {border-radius:17px;}
.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] button[kind="primary"] {background:#167755;border:0;border-radius:12px;font-weight:700;}
[data-testid="stDataFrame"] {border-radius:14px;overflow:hidden;}
[data-testid="stSidebar"] {background:#102b34;}
[data-testid="stSidebar"] * {color:#e7f5ed !important;}
[data-testid="stSidebar"] div[role="radiogroup"] label:has(input:checked) {background:#1b5547;border-radius:10px;}
h1,h2,h3 {color:#14382f;letter-spacing:-.025em;}
.hero {background:linear-gradient(110deg,#102d36 0%,#185748 65%,#398567 100%);color:#fff;border-radius:22px;padding:32px 38px;margin-bottom:22px;box-shadow:0 10px 25px #173d3020;}
.hero .eyebrow {font-size:12px;font-weight:800;letter-spacing:2px;color:#b5e6c6;}
.hero h1 {color:#fff;font-size:46px;margin:7px 0 5px;}
.hero p {font-size:16px;color:#d8efe4;margin:0;}
.chip {display:inline-block;background:#ffffff20;border:1px solid #ffffff45;border-radius:20px;padding:6px 12px;margin:17px 7px 0 0;font-size:12px;}
.note {background:#e6f4ee;border:1px solid #c4e5d3;color:#215747;border-radius:12px;padding:13px 17px;margin:10px 0 22px;font-size:13px;}
.score {background:#102d36;border-radius:20px;padding:25px;color:white;}
.score strong {font-size:64px;color:#a7dfb2;}
.score h3 {color:white;}
.small {color:#657b74;font-size:13px;}
[data-testid="stMetric"] {background:white;padding:17px;border:1px solid #e0eae5;border-radius:15px;}
[data-testid="stMetricValue"] {color:#135c43;}
</style>''', unsafe_allow_html=True)

SAMPLE = [
 dict(id="RZQ-001",name="Al Noor Residence",kind="Residential apartment",age=18,kwh=8600,roof="Dark / high heat absorption",heat="High",flood="Medium",insulation="Poor",occupants=45,area=410,status="Assessed",funded=0,worker="",verified=False,post_kwh=0,score=92),
 dict(id="RZQ-002",name="Block C Housing",kind="Residential apartment",age=15,kwh=6800,roof="Dark / high heat absorption",heat="High",flood="Low",insulation="Poor",occupants=32,area=330,status="Funding approved",funded=84000,worker="Aisha Rahman",verified=False,post_kwh=0,score=86),
 dict(id="RZQ-003",name="Al Amal Building",kind="Mixed use",age=12,kwh=5700,roof="Moderate",heat="Medium",flood="Medium",insulation="Average",occupants=27,area=290,status="Worker assigned",funded=73000,worker="Omar Khalid",verified=False,post_kwh=0,score=81),
 dict(id="RZQ-004",name="Al Safa Villas",kind="Residential villa",age=4,kwh=1900,roof="Reflective / cool roof",heat="Low",flood="Low",insulation="Good",occupants=6,area=180,status="Verified",funded=29000,worker="Sara Ahmed",verified=True,post_kwh=1520,score=28),
]
WORKERS = [dict(name="Aisha Rahman",skill="Roof insulation",certified=True),dict(name="Omar Khalid",skill="Solar PV",certified=True),dict(name="Sara Ahmed",skill="Efficient cooling",certified=True),dict(name="Trainee Demo",skill="General support",certified=False)]

if "buildings" not in st.session_state: st.session_state.buildings=[dict(x) for x in SAMPLE]
if "funds" not in st.session_state: st.session_state.funds={"City climate budget":600000.0,"Corporate ESG":400000.0,"NGO grants":250000.0}
if "evidence" not in st.session_state: st.session_state.evidence={}
if "last_assessment" not in st.session_state: st.session_state.last_assessment=None


def clamp(v):return max(0,min(100,float(v)))
def assess(b):
    heat={"Low":20,"Medium":60,"High":100}[b["heat"]]
    flood={"Low":10,"Medium":55,"High":100}[b["flood"]]
    climate=.7*heat+.3*flood
    energy=clamp(100*b["kwh"]/8500*.75+min(b["age"]*1.3,25))
    roof={"Reflective / cool roof":20,"Moderate":55,"Dark / high heat absorption":95}[b["roof"]]
    ins={"Good":15,"Average":55,"Poor":100}[b["insulation"]]
    suitability=.55*roof+.45*ins
    effectiveness=clamp(30+0.4*energy+0.3*suitability)
    social=clamp(b["occupants"]*1.8+20)
    factors={"Climate vulnerability":climate,"Energy need":energy,"Retrofit suitability":suitability,"Financial efficiency (proxy)":effectiveness,"Social impact":social}
    weights={"Climate vulnerability":.30,"Energy need":.25,"Retrofit suitability":.20,"Financial efficiency (proxy)":.15,"Social impact":.10}
    score=round(sum(factors[k]*weights[k] for k in weights))
    recommendations=[]
    if b["roof"]=="Dark / high heat absorption":recommendations.append("Reflective roof coating")
    if b["insulation"]!="Good":recommendations.append("Roof insulation")
    if b["kwh"]>=4000:recommendations.append("Efficient cooling upgrade")
    if b["area"]>=150 and b["kwh"]>=3000:recommendations.append("Solar PV feasibility review")
    if not recommendations:recommendations=["Energy audit and smart controls"]
    estimated_cost=round(7500+120*b["area"]+min(b["kwh"]*2.5,18000),-2)
    saving_fraction=min(.35,.08+.000014*b["kwh"]+.045*(b["insulation"]=="Poor")+.035*(b["roof"]=="Dark / high heat absorption"))
    annual_kwh=round(b["kwh"]*12*saving_fraction)
    # Illustrative only: 0.4 kg CO2/kWh; AED 0.30/kWh.
    return dict(score=score,factors=factors,weights=weights,recommendations=recommendations,cost=int(estimated_cost),annual_kwh=annual_kwh,annual_co2_t=round(annual_kwh*.0004,2),annual_aed=round(annual_kwh*.30),saving_pct=round(saving_fraction*100,1))

for _building in st.session_state.buildings:
    _building["score"] = assess(_building)["score"]

def label(b):return f'{b["id"]} — {b["name"]}'
def get_building(key):return next(x for x in st.session_state.buildings if x["id"]==key)
def money(n):return f'AED {n:,.0f}'
def notice():st.markdown('<div class="note">🧪 <b>ACADEMIC RESEARCH PROTOTYPE</b> — All building records, budgets, workers, scores and impact estimates are simulated. No real financing, professional certification, meter integration or accredited verification. The explainable decision engine is rule-based, not a trained AI model.</div>',unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## 🌿 RIZQ")
    st.caption("CLIMATE RETROFIT INTELLIGENCE")
    st.write("Prioritize buildings. Fund upgrades. Verify impact.")
    page=st.radio("Explore the platform",["Command Center","Add Building","AI-Assisted Assessment","Funding Studio","Green Jobs & Workers","Impact Verification","Projects & Reports","Methodology & Testing"],label_visibility="collapsed")
    st.divider()
    st.caption("INT305 • Software Engineering")
    st.caption("Session-only demonstration • synthetic data")

st.markdown('<div class="hero"><div class="eyebrow">SUSTAINABLE CITIES • SMART FUNDING • GREEN JOBS</div><h1>RIZQ</h1><p>AI-Assisted Climate Retrofit Funding & Green Jobs Platform</p><span class="chip">◈ Explainable prioritization</span><span class="chip">◈ Blended finance</span><span class="chip">◈ Verified impact workflow</span></div>',unsafe_allow_html=True)
notice()

if page=="Command Center":
    st.header("Climate Retrofit Command Center")
    buildings=st.session_state.buildings
    a,b,c,d=st.columns(4)
    a.metric("Buildings assessed",len(buildings))
    b.metric("Projects funded",sum(x["funded"]>0 for x in buildings))
    c.metric("Available blended fund",money(sum(st.session_state.funds.values())))
    d.metric("Green job assignments",sum(bool(x["worker"]) for x in buildings))
    l,r=st.columns([1.2,1])
    with l:
        st.subheader("Highest priority buildings")
        for x in sorted(buildings,key=lambda y:y["score"],reverse=True)[:6]:
            with st.container(border=True):
                u,v=st.columns([4,1]);u.markdown(f'**{x["name"]}**  \n<span class="small">{x["kind"]} • {x["status"]}</span>',unsafe_allow_html=True);v.metric("Priority",f'{x["score"]}/100')
    with r:
        st.subheader("Blended fund allocation")
        funds=st.session_state.funds
        df=pd.DataFrame({"Source":list(funds),"Available AED":list(funds.values())})
        st.plotly_chart(px.pie(df,names="Source",values="Available AED",hole=.65,color_discrete_sequence=["#126c4b","#75bc87","#b4dec1"]),use_container_width=True)
        st.caption("Illustrative available funding by partner type")
    st.subheader("Project pipeline")
    status=pd.Series([x["status"] for x in buildings]).value_counts().rename_axis("Status").reset_index(name="Projects")
    st.plotly_chart(px.bar(status,x="Status",y="Projects",color="Status",color_discrete_sequence=["#0f6b4b","#54a37a","#95c9ac","#12333b"]),use_container_width=True)

elif page=="Add Building":
    st.header("Register a Building")
    st.write("Enter a building profile to generate an explainable retrofit assessment.")
    with st.form("add_building"):
        x,y=st.columns(2)
        with x:
            name=st.text_input("Building name",placeholder="e.g. Al Noor Residence")
            kind=st.selectbox("Building type",["Residential apartment","Residential villa","Mixed use","Commercial"])
            age=st.number_input("Building age (years)",0,100,18)
            kwh=st.number_input("Monthly electricity use (kWh)",100,100000,6000,step=100)
            area=st.number_input("Roof area (m²)",20,20000,300,step=10)
        with y:
            roof=st.selectbox("Roof condition",["Dark / high heat absorption","Moderate","Reflective / cool roof"])
            insulation=st.selectbox("Insulation",["Poor","Average","Good"])
            heat=st.selectbox("Heat exposure",["High","Medium","Low"])
            flood=st.selectbox("Flood exposure",["Medium","Low","High"])
            occupants=st.number_input("Number of occupants",1,2000,25)
        if st.form_submit_button("🌿 Analyze & register building",type="primary",use_container_width=True):
            if not name.strip():st.error("Please enter a building name.")
            else:
                b=dict(id=f'RZQ-{len(st.session_state.buildings)+1:03d}',name=name.strip(),kind=kind,age=age,kwh=kwh,area=area,roof=roof,insulation=insulation,heat=heat,flood=flood,occupants=occupants,status="Assessed",funded=0,worker="",verified=False,post_kwh=0)
                result=assess(b);b["score"]=result["score"];st.session_state.buildings.append(b);st.session_state.last_assessment=b["id"]
                st.success(f'{b["id"]} created. Priority score: {result["score"]}/100. Open AI-Assisted Assessment to see the full explanation.')

elif page=="AI-Assisted Assessment":
    st.header("Explainable Retrofit Assessment")
    buildings=st.session_state.buildings
    ids=[b["id"] for b in buildings]
    chosen=st.selectbox("Select a building",ids,index=ids.index(st.session_state.last_assessment) if st.session_state.last_assessment in ids else 0,format_func=lambda i:label(get_building(i)))
    b=get_building(chosen);res=assess(b)
    l,r=st.columns([1,2])
    with l:
        priority="VERY HIGH" if res["score"]>=75 else "HIGH" if res["score"]>=55 else "MODERATE" if res["score"]>=35 else "LOW"
        st.markdown(f'<div class="score"><h3>Retrofit Priority Score</h3><strong>{res["score"]}</strong><span>/100</span><h3>{priority} PRIORITY</h3><p>Transparent weighted assessment, not automated funding approval.</p></div>',unsafe_allow_html=True)
    with r:
        st.subheader("Recommended retrofit package")
        for i,rec in enumerate(res["recommendations"],1):st.markdown(f'**{i}. {rec}**')
        st.divider()
        a,c=st.columns(2);a.metric("Illustrative retrofit cost",money(res["cost"]));c.metric("Estimated annual energy reduction",f'{res["saving_pct"]}%')
        a,c=st.columns(2);a.metric("Estimated annual savings",f'{res["annual_kwh"]:,} kWh');c.metric("Estimated CO₂ avoided",f'{res["annual_co2_t"]} t/year')
    st.subheader("Why this score?")
    factors=pd.DataFrame([{"Factor":k,"Factor value":round(v,1),"Weight":f'{res["weights"][k]*100:.0f}%',"Contribution":round(v*res["weights"][k],1)} for k,v in res["factors"].items()])
    st.dataframe(factors,use_container_width=True,hide_index=True)
    st.plotly_chart(px.bar(factors,x="Factor",y="Contribution",color="Factor",color_discrete_sequence=["#0f654a","#3f916c","#7fbb96","#b2d9bd","#204b47"]),use_container_width=True)
    st.caption("Illustrative weights: climate 30%, energy 25%, suitability 20%, financial efficiency 15%, social impact 10%. Financial efficiency is a proxy. Results are educational estimates, not an engineering audit.")

elif page=="Funding Studio":
    st.header("Blended Climate Funding Studio")
    st.write("Simulate funding allocations from public budgets, corporate ESG sponsors and NGO grants.")
    c=st.columns(3)
    for i,(source,amount) in enumerate(st.session_state.funds.items()):c[i].metric(source,money(amount))
    choices=[x for x in st.session_state.buildings if not x["verified"]]
    if choices:
        with st.form("fund_project"):
            chosen=st.selectbox("Eligible project",[x["id"] for x in choices],format_func=lambda i:label(get_building(i)))
            source=st.selectbox("Funding source",list(st.session_state.funds))
            suggested=max(1000,assess(get_building(chosen))["cost"]-get_building(chosen)["funded"])
            amount=st.number_input("Simulated allocation (AED)",min_value=1000.0,max_value=1000000.0,value=float(min(suggested,1000000)),step=1000.0)
            if st.form_submit_button("Approve simulated funding",type="primary"):
                b=get_building(chosen)
                if amount>st.session_state.funds[source]:st.error("Insufficient funds in the selected source.")
                elif b["funded"]+amount>assess(b)["cost"]:st.error("Allocation exceeds the illustrative project cost. Reduce the amount.")
                else:
                    st.session_state.funds[source]-=amount;b["funded"]+=amount;b["status"]="Funding approved";st.success(f'{money(amount)} allocated to {b["name"]} (simulated).')
    st.subheader("Funding ledger")
    st.dataframe(pd.DataFrame([{"Project":x["name"],"Estimated cost":money(assess(x)["cost"]),"Funded":money(x["funded"]),"Funding gap":money(max(0,assess(x)["cost"]-x["funded"]))} for x in st.session_state.buildings]),use_container_width=True,hide_index=True)

elif page=="Green Jobs & Workers":
    st.header("Certified Green Workers & Assignment")
    st.dataframe(pd.DataFrame(WORKERS).rename(columns={"name":"Worker","skill":"Specialty","certified":"Demo certification"}),use_container_width=True,hide_index=True)
    st.caption("Worker profiles and certifications are simulated; no real credentials are issued or checked.")
    eligible=[b for b in st.session_state.buildings if b["funded"]>0 and not b["verified"]]
    if not eligible:st.info("Fund a project in Funding Studio to assign a worker.")
    else:
        with st.form("assign_worker"):
            chosen=st.selectbox("Funded project",[x["id"] for x in eligible],format_func=lambda i:label(get_building(i)))
            worker=st.selectbox("Worker",[x["name"] for x in WORKERS])
            if st.form_submit_button("Assign worker",type="primary"):
                w=next(x for x in WORKERS if x["name"]==worker)
                if not w["certified"]:st.error("Assignment rejected: this worker is not marked as certified in the demo.")
                else:
                    b=get_building(chosen);b["worker"]=worker;b["status"]="Worker assigned";st.success(f'{worker} assigned to {b["name"]}.')
    st.subheader("Current assignments")
    st.dataframe(pd.DataFrame([{"Project":x["name"],"Worker":x["worker"] or "Unassigned","Status":x["status"]} for x in st.session_state.buildings]),use_container_width=True,hide_index=True)

elif page=="Impact Verification":
    st.header("Completion Evidence & Verified Impact Record")
    chosen=st.selectbox("Project",[x["id"] for x in st.session_state.buildings],format_func=lambda i:label(get_building(i)))
    b=get_building(chosen)
    if b["verified"]:
        st.success("This project is verified within the simulated prototype workflow.")
    elif not b["worker"]:st.warning("Assign a certified demo worker before submitting verification evidence.")
    else:
        st.write(f'**Assigned worker:** {b["worker"]}')
        with st.form("verify"):
            st.markdown("#### Worker completion evidence")
            photo=st.file_uploader("Optional demonstration photo (JPG/PNG)",type=["jpg","jpeg","png"])
            evidence=st.checkbox("Worker completion evidence reviewed")
            inspection=st.checkbox("Inspector approval (demo)")
            meter=st.number_input("Post-retrofit monthly electricity (kWh)",min_value=1,max_value=int(b["kwh"]*2),value=max(1,int(b["kwh"]*.80)))
            st.caption(f'Baseline: {b["kwh"]:,} kWh/month. Only lower values can demonstrate energy savings.')
            if st.form_submit_button("Verify project & generate record",type="primary"):
                if not evidence or not inspection:st.error("Both evidence review and inspector approval must be checked.")
                elif meter>=b["kwh"]:st.error("Post-retrofit consumption must be lower than the baseline for a positive savings record.")
                else:
                    b["post_kwh"]=meter;b["verified"]=True;b["status"]="Verified"
                    st.session_state.evidence[b["id"]]={"evidence_reviewed":True,"inspector_approved":True,"photo_uploaded":bool(photo),"verification_date":str(date.today())}
                    st.success("Project verified in the demo. The impact record is available below.")
    if b["verified"]:
        baseline=b["kwh"];after=b["post_kwh"] or round(baseline*.8)
        saved=max(0,baseline-after);pct=100*saved/baseline
        st.subheader(f'Verified Impact Record • {b["id"]}')
        c=st.columns(4);c[0].metric("Baseline",f'{baseline:,} kWh/mo');c[1].metric("After",f'{after:,} kWh/mo');c[2].metric("Reduction",f'{pct:.1f}%');c[3].metric("CO₂ avoided (estimate)",f'{saved*12*.0004:.2f} t/yr')
        chart=pd.DataFrame({"Period":["Before retrofit","After retrofit"],"kWh per month":[baseline,after]})
        st.plotly_chart(px.bar(chart,x="Period",y="kWh per month",color="Period",color_discrete_sequence=["#193c43","#70b989"]),use_container_width=True)
        csv=f'Project ID,{b["id"]}\nBuilding,{b["name"]}\nBaseline monthly kWh,{baseline}\nPost retrofit monthly kWh,{after}\nReduction percent,{pct:.1f}\nEstimated annual CO2 avoided t,{saved*12*.0004:.2f}\nVerification type,Simulated academic prototype\n'
        st.download_button("⬇ Download impact record (CSV)",data=csv,file_name=f'{b["id"]}_impact_record.csv',mime="text/csv")
        st.caption("The term ‘Verified’ describes a simulated workflow; it is not third-party certification or a carbon credit.")

elif page=="Projects & Reports":
    st.header("Retrofit Project Portfolio")
    records=[]
    for b in st.session_state.buildings:
        res=assess(b)
        records.append({"ID":b["id"],"Building":b["name"],"Priority":b["score"],"Status":b["status"],"Estimated cost (AED)":res["cost"],"Funded (AED)":b["funded"],"Worker":b["worker"] or "—","Verified":b["verified"]})
    df=pd.DataFrame(records)
    st.dataframe(df,use_container_width=True,hide_index=True)
    st.download_button("⬇ Download project portfolio (CSV)",data=df.to_csv(index=False),file_name="RIZQ_project_portfolio.csv",mime="text/csv")
    st.subheader("Portfolio analytics")
    c=st.columns(3)
    c[0].metric("Total simulated funding used",money(sum(x["funded"] for x in st.session_state.buildings)))
    c[1].metric("Verified projects",sum(x["verified"] for x in st.session_state.buildings))
    c[2].metric("Average priority",f'{df["Priority"].mean():.0f}/100')

else:
    st.header("Methodology, Architecture & Test Plan")
    st.markdown("""**INT305 software-engineering workflow:** Register building → Calculate transparent priority score → Recommend retrofit package → Approve simulated funding → Assign certified worker → Submit evidence → Verify → Export impact record.

**User roles in the proposed full system:** Resident / Building Owner, City / NGO / ESG Sponsor, Certified Worker, Inspector / Verifier, and Administrator. The student demo models their actions in separate workflow pages; it does **not** implement secure multi-user login or production authorization.

**Scoring weights:** Climate vulnerability 30%, energy need 25%, retrofit suitability 20%, financial efficiency 15%, social impact 10%. Inputs are normalized to 0–100. The current financial-efficiency factor is a heuristic proxy, not a full cost-benefit calculation.

**Technology:** Streamlit + Python + Pandas + Plotly. Data is stored in session memory for the demonstration. Production architecture could use a FastAPI backend, a persistent SQL database, secure hashed-password authentication and role-based permissions.

**Estimation assumptions:** Energy-saving percentages and retrofit costs are illustrative formulas. The demo uses AED 0.30/kWh and 0.4 kg CO₂/kWh solely as adjustable teaching assumptions. They are not validated tariffs or official emission factors.

**Future AI upgrade:** Train and validate a supervised model on real, permissioned retrofit outcomes. Until then, describe this prototype as an *AI-assisted concept with a rule-based decision engine*, not as a trained predictive model.
""")
    st.subheader("Manual acceptance tests")
    tests=[("T1","Create a high-risk, high-energy building","High priority with explanation"),("T2","Assess efficient low-risk building","Lower priority"),("T3","Leave building name blank","Validation error"),("T4","Allocate simulated sponsor funding","Balance and project status update"),("T5","Assign Trainee Demo","Assignment rejected"),("T6","Assign certified worker","Assignment succeeds"),("T7","Verify with both checks and lower meter reading","Impact record generated"),("T8","Enter post-meter value higher than baseline","Validation error"),("T9","Download project CSV","Portfolio exported")]
    st.dataframe(pd.DataFrame(tests,columns=["Test ID","Action","Expected outcome"]),use_container_width=True,hide_index=True)
    st.info("For a production-ready version, add persistent storage, true role-based authentication, audit logs, automated tests and validated building/energy datasets.")

st.divider()
st.caption("RIZQ • INT305 • Academic research prototype • All displayed example data and transactions are simulated.")
