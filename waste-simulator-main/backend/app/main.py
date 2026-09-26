from __future__ import annotations
import os, hashlib, hmac, re
from datetime import datetime, timedelta, timezone
from typing import Any, Literal
import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, Field, EmailStr, field_validator
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker
from .calculations import waste_breakdown, collection_plan, transport_plan, treatment_plan

load_dotenv()
DATABASE_URL=os.getenv("DATABASE_URL", "sqlite:///./swms.db")
if DATABASE_URL.startswith("postgresql+") is False and DATABASE_URL.startswith("postgresql:"): DATABASE_URL=DATABASE_URL.replace("postgresql:", "postgresql+psycopg:", 1)
engine=create_engine(DATABASE_URL, connect_args={"check_same_thread":False} if DATABASE_URL.startswith("sqlite") else {})
SessionLocal=sessionmaker(bind=engine, autoflush=False)
SECRET=os.getenv("JWT_SECRET", "development-secret-change-me-please-replace-with-a-long-value")
security=HTTPBearer()

class Base(DeclarativeBase): pass

class User(Base):
    __tablename__="users"; id: Mapped[int]=mapped_column(primary_key=True); name: Mapped[str]=mapped_column(String(120)); email: Mapped[str]=mapped_column(String(255), unique=True, index=True); password_hash: Mapped[str]=mapped_column(String(255)); role: Mapped[str]=mapped_column(String(40), default="VIEWER"); authority_type: Mapped[str]=mapped_column(String(30), default="OTHER"); organization: Mapped[str|None]=mapped_column(String(255), nullable=True); active: Mapped[bool]=mapped_column(Boolean, default=True); created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)

class Location(Base):
    __tablename__="locations"; id: Mapped[int]=mapped_column(primary_key=True); name: Mapped[str]=mapped_column(String(255)); location_type: Mapped[str]=mapped_column(String(60)); parent_id: Mapped[int|None]=mapped_column(ForeignKey("locations.id"), nullable=True); latitude: Mapped[float|None]=mapped_column(nullable=True); longitude: Mapped[float|None]=mapped_column(nullable=True); geometry: Mapped[dict|None]=mapped_column(JSON, nullable=True); details: Mapped[dict]=mapped_column(JSON, default=dict); created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)

class Record(Base):
    __tablename__="planning_records"; id: Mapped[int]=mapped_column(primary_key=True); location_id: Mapped[int]=mapped_column(ForeignKey("locations.id"), index=True); category: Mapped[str]=mapped_column(String(50), index=True); payload: Mapped[dict]=mapped_column(JSON); created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow); updated_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Run(Base):
    __tablename__="simulation_runs"; id: Mapped[int]=mapped_column(primary_key=True); location_id: Mapped[int]=mapped_column(ForeignKey("locations.id")); scenario_id: Mapped[int|None]=mapped_column(nullable=True); results: Mapped[dict]=mapped_column(JSON); created_at: Mapped[datetime]=mapped_column(DateTime, default=datetime.utcnow)

def db():
    s=SessionLocal()
    try: yield s
    finally: s.close()

def password_hash(password:str)->str:
    salt=os.urandom(16); return salt.hex()+":"+hashlib.pbkdf2_hmac("sha256",password.encode(),salt,310000).hex()

def verify(password:str, encoded:str)->bool:
    salt,digest=encoded.split(":"); return hmac.compare_digest(hashlib.pbkdf2_hmac("sha256",password.encode(),bytes.fromhex(salt),310000).hex(),digest)

def token_for(user:User): return jwt.encode({"sub":str(user.id),"role":user.role,"exp":datetime.now(timezone.utc)+timedelta(minutes=int(os.getenv("ACCESS_TOKEN_MINUTES","60")))},SECRET,algorithm="HS256")

def current_user(c:HTTPAuthorizationCredentials=Depends(security), s:Session=Depends(db)):
    try: claims=jwt.decode(c.credentials,SECRET,algorithms=["HS256"]); user=s.get(User,int(claims["sub"]))
    except Exception: raise HTTPException(401,"Invalid or expired token")
    if not user or not user.active: raise HTTPException(401,"Inactive user")
    return user

def require(*roles):
    def check(u:User=Depends(current_user)):
        if u.role not in roles: raise HTTPException(403,"Insufficient role permission")
        return u
    return check

class Register(BaseModel): name:str=Field(min_length=2,max_length=120); email:EmailStr; password:str=Field(min_length=8,max_length=128); role:Literal["SUPER_ADMIN","MUNICIPAL_AUTHORITY","PANCHAYAT_AUTHORITY","PLANNER","DATA_ENTRY","VIEWER"]="VIEWER"; authority_type:str="OTHER"; organization:str|None=None
class Login(BaseModel): email:EmailStr; password:str
class LocationIn(BaseModel): name:str=Field(min_length=2,max_length=255); location_type:str=Field(min_length=2,max_length=60); parent_id:int|None=None; latitude:float|None=Field(None,ge=-90,le=90); longitude:float|None=Field(None,ge=-180,le=180); geometry:dict|None=None; details:dict=Field(default_factory=dict)
class RecordIn(BaseModel): payload:dict[str,Any]
class SimulationParameters(BaseModel):
    total_population: float = Field(25000, ge=0, le=100000000)
    waste_per_person_per_day: float = Field(0.5, ge=0.01, le=10.0)
    population_growth_rate: float = Field(2.0, ge=-10.0, le=25.0)
    floating_population: float = Field(0.0, ge=0)
    tourist_population: float = Field(0.0, ge=0)
    seasonal_population: float = Field(0.0, ge=0)
    migrant_population: float = Field(0.0, ge=0)
    industrial_waste_kg_day: float = Field(0.0, ge=0)
    commercial_waste_kg_day: float = Field(0.0, ge=0)
    market_waste_kg_day: float = Field(0.0, ge=0)
    vehicle_count: int = Field(10, ge=0, le=10000)
    vehicle_capacity_kg: float = Field(2000.0, gt=0, le=100000)
    trips_per_vehicle: int = Field(1, ge=1, le=20)
    collection_coverage_percent: float = Field(100.0, ge=0, le=100)
    treatment_capacity_kg: float = Field(10000.0, ge=0)
    segregation_percent: float = Field(60.0, ge=0, le=100)
class CalculationIn(BaseModel): parameters:dict[str,Any]; event_population:float=Field(0,ge=0); event_percent:float=Field(0,ge=0,le=100)
class CapacityIn(BaseModel): daily_waste_kg:float=Field(ge=0); vehicle_count:int=Field(ge=0); vehicle_capacity_kg:float=Field(gt=0); trips_per_vehicle:int=Field(ge=1); collection_coverage_percent:float=Field(100,ge=0,le=100)
class TreatmentIn(BaseModel): daily_waste_kg:float=Field(ge=0); treatment_capacity_kg:float=Field(ge=0); segregation_percent:float=Field(ge=0,le=100)
class SimulationIn(BaseModel):
    location_id:int
    years:int=Field(20,ge=1,le=50)
    parameters:dict[str,Any]
    scenario_overrides:dict[str,Any]=Field(default_factory=dict)

    @field_validator("parameters")
    @classmethod
    def validate_params(cls, v: dict[str, Any]) -> dict[str, Any]:
        if "vehicle_capacity_kg" in v and float(v["vehicle_capacity_kg"]) <= 0:
            raise ValueError("vehicle_capacity_kg must be greater than 0")
        if "trips_per_vehicle" in v and int(v["trips_per_vehicle"]) < 1:
            raise ValueError("trips_per_vehicle must be at least 1")
        if "segregation_percent" in v and not (0 <= float(v["segregation_percent"]) <= 100):
            raise ValueError("segregation_percent must be between 0 and 100")
        if "waste_per_person_per_day" in v and float(v["waste_per_person_per_day"]) < 0:
            raise ValueError("waste_per_person_per_day must be non-negative")
        return v

app=FastAPI(title="SWMS API", version="1.0.0", description="Explainable waste planning and simulation API")
app.add_middleware(CORSMiddleware,allow_origins=os.getenv("CORS_ORIGINS","http://localhost:5173").split(","),allow_credentials=True,allow_methods=["*"],allow_headers=["*"])

@app.on_event("startup")
def start(): Base.metadata.create_all(engine)

@app.get("/api/v1/health")
def health(): return {"status":"healthy","database":"configured","postgis_mode":DATABASE_URL.startswith("postgresql")}

@app.post("/api/v1/auth/register",status_code=201)
def register(x:Register,s:Session=Depends(db)):
    if s.scalar(select(User).where(User.email==x.email)): raise HTTPException(409,"Email already registered")
    u=User(name=x.name,email=x.email,password_hash=password_hash(x.password),role=x.role,authority_type=x.authority_type,organization=x.organization); s.add(u);s.commit();s.refresh(u);return {"id":u.id,"email":u.email,"role":u.role}

@app.post("/api/v1/auth/login")
def login(x:Login,s:Session=Depends(db)):
    u=s.scalar(select(User).where(User.email==x.email))
    if not u or not verify(x.password,u.password_hash): raise HTTPException(401,"Invalid email or password")
    return {"access_token":token_for(u),"token_type":"bearer","user":{"id":u.id,"name":u.name,"role":u.role}}

@app.get("/api/v1/auth/me")
def me(u:User=Depends(current_user)): return {"id":u.id,"name":u.name,"email":u.email,"role":u.role,"authority_type":u.authority_type}

@app.post("/api/v1/locations",status_code=201)
def create_location(x:LocationIn,s:Session=Depends(db),u:User=Depends(require("SUPER_ADMIN","MUNICIPAL_AUTHORITY","PANCHAYAT_AUTHORITY","PLANNER","DATA_ENTRY"))):
    row=Location(**x.model_dump());s.add(row);s.commit();s.refresh(row);return serialize_location(row)

@app.get("/api/v1/locations")
def locations(s:Session=Depends(db),u:User=Depends(current_user)): return [serialize_location(x) for x in s.scalars(select(Location)).all()]

@app.get("/api/v1/locations/{location_id}")
def get_location(location_id:int,s:Session=Depends(db),u:User=Depends(current_user)):
    x=s.get(Location,location_id)
    if not x: raise HTTPException(404,"Location not found")
    return serialize_location(x)

def serialize_location(x): return {"id":x.id,"name":x.name,"location_type":x.location_type,"parent_id":x.parent_id,"latitude":x.latitude,"longitude":x.longitude,"geometry":x.geometry,"details":x.details}

ALLOWED={"demography","infrastructure","industrial","environment","terrain","economic","cultural","habitations","waste","events","strategies","scenarios"}

@app.post("/api/v1/locations/{location_id}/{category}",status_code=201)
def add_record(location_id:int,category:str,x:RecordIn,s:Session=Depends(db),u:User=Depends(require("SUPER_ADMIN","MUNICIPAL_AUTHORITY","PANCHAYAT_AUTHORITY","PLANNER","DATA_ENTRY"))):
    if category not in ALLOWED: raise HTTPException(404,"Unknown planning category")
    if not s.get(Location,location_id): raise HTTPException(404,"Location not found")
    row=Record(location_id=location_id,category=category,payload=x.payload);s.add(row);s.commit();s.refresh(row);return serialize_record(row)

@app.get("/api/v1/locations/{location_id}/{category}")
def records(location_id:int,category:str,s:Session=Depends(db),u:User=Depends(current_user)): return [serialize_record(r) for r in s.scalars(select(Record).where(Record.location_id==location_id,Record.category==category)).all()]

@app.put("/api/v1/records/{record_id}")
def update_record(record_id:int,x:RecordIn,s:Session=Depends(db),u:User=Depends(require("SUPER_ADMIN","MUNICIPAL_AUTHORITY","PANCHAYAT_AUTHORITY","PLANNER","DATA_ENTRY"))):
    r=s.get(Record,record_id)
    if not r: raise HTTPException(404,"Record not found")
    r.payload=x.payload;s.commit();s.refresh(r);return serialize_record(r)

@app.delete("/api/v1/records/{record_id}",status_code=204)
def delete_record(record_id:int,s:Session=Depends(db),u:User=Depends(require("SUPER_ADMIN","MUNICIPAL_AUTHORITY","PANCHAYAT_AUTHORITY","PLANNER"))):
    r=s.get(Record,record_id)
    if not r: raise HTTPException(404,"Record not found")
    s.delete(r);s.commit()

def serialize_record(r): return {"id":r.id,"location_id":r.location_id,"category":r.category,"payload":r.payload,"created_at":r.created_at.isoformat()}

@app.post("/api/v1/calculations/waste")
def calculate_waste(x:CalculationIn,u:User=Depends(current_user)):
    result=waste_breakdown(x.parameters,event_population=x.event_population,event_percent=x.event_percent)
    composition=x.parameters.get("composition",{})
    if composition and round(sum(composition.values()),4)!=100: raise HTTPException(422,"Waste composition percentages must total 100")
    result["composition"]={k:{"percentage":v,"kg_day":round(result["daily_waste_kg"]*v/100,2)} for k,v in composition.items()};return result

@app.post("/api/v1/calculations/collection")
def collection(x:CapacityIn,u:User=Depends(current_user)):
    return collection_plan(x.daily_waste_kg,x.vehicle_count,x.vehicle_capacity_kg,x.trips_per_vehicle,x.collection_coverage_percent)

@app.post("/api/v1/calculations/transportation")
def transportation(x:CapacityIn,u:User=Depends(current_user)): return transport_plan(x.daily_waste_kg,x.vehicle_count,x.vehicle_capacity_kg,x.trips_per_vehicle)

@app.post("/api/v1/calculations/treatment")
def treatment(x:TreatmentIn,u:User=Depends(current_user)): return treatment_plan(x.daily_waste_kg,x.treatment_capacity_kg,x.segregation_percent)

@app.post("/api/v1/simulations",status_code=201)
def simulate(x:SimulationIn,s:Session=Depends(db),u:User=Depends(require("SUPER_ADMIN","MUNICIPAL_AUTHORITY","PANCHAYAT_AUTHORITY","PLANNER"))):
    if not s.get(Location,x.location_id): raise HTTPException(404,"Location not found")
    params={**x.parameters,**x.scenario_overrides}; series=[]
    for year in range(x.years+1):
        result=waste_breakdown(params,year); result["collection"] = collection_plan(result["daily_waste_kg"],int(params.get("vehicle_count",0)),float(params.get("vehicle_capacity_kg",1)),int(params.get("trips_per_vehicle",1)),float(params.get("collection_coverage_percent",100))); result["treatment"] = treatment_plan(result["daily_waste_kg"],float(params.get("treatment_capacity_kg",0)),float(params.get("segregation_percent",0)));series.append(result)
    run=Run(location_id=x.location_id,results={"parameters":params,"years":series});s.add(run);s.commit();s.refresh(run);return {"simulation_id":run.id,"results":run.results}

@app.get("/api/v1/dashboard/{location_id}")
def dashboard(location_id:int,s:Session=Depends(db),u:User=Depends(current_user)):
    run=s.scalar(select(Run).where(Run.location_id==location_id).order_by(Run.created_at.desc()))
    records=s.scalars(select(Record).where(Record.location_id==location_id)).all()
    return {"location_id":location_id,"data_completeness_percent":round(len({r.category for r in records}&set(ALLOWED))/7*100,1),"latest_simulation":run.results if run else None,"record_counts":{c:sum(1 for r in records if r.category==c) for c in ALLOWED}}

@app.get("/api/v1/map")
def map_data(s:Session=Depends(db),u:User=Depends(current_user)):
    features=[]
    for l in s.scalars(select(Location).where(Location.latitude.is_not(None),Location.longitude.is_not(None))).all(): features.append({"type":"Feature","geometry":l.geometry or {"type":"Point","coordinates":[l.longitude,l.latitude]},"properties":{"id":l.id,"name":l.name,"type":l.location_type}})
    return {"type":"FeatureCollection","features":features}

class ChatIn(BaseModel):
    location_id: int
    question: str = Field(min_length=2, max_length=500)

@app.post("/api/v1/chatbot")
def chatbot(x:ChatIn, s:Session=Depends(db), u:User=Depends(current_user)):
    run = s.scalar(select(Run).where(Run.location_id == x.location_id).order_by(Run.created_at.desc()))
    if not run:
        raise HTTPException(404, "Run a simulation before asking planning questions")

    years = run.results["years"]
    params = run.results.get("parameters", {})
    q = x.question.lower()

    # Extract target year from prompt (e.g., year 10, 15, 5, etc.)
    match = re.search(r"\byear\s*(\d+)\b|\b(\d+)\s*years?\b|\b(\d+)\b", q)
    year = 10
    if match:
        found_nums = [int(n) for n in match.groups() if n is not None]
        for num in found_nums:
            if 0 <= num <= 20:
                year = num
                break

    idx = min(year, len(years) - 1)
    row = years[idx]

    daily_t = row["daily_waste_tonnes"]
    daily_kg = row["daily_waste_kg"]
    annual_t = row["annual_waste_tonnes"]
    pop = row["effective_population"]
    treat_gap_kg = row["treatment"]["treatment_gap_kg_day"]
    treat_gap_t = round(treat_gap_kg / 1000.0, 2)
    treat_cap_kg = row["treatment"]["treatment_capacity_kg_day"]
    treat_cap_t = round(treat_cap_kg / 1000.0, 2)

    seg_kg = row["treatment"]["segregated_kg_day"]
    seg_t = round(seg_kg / 1000.0, 2)
    unseg_kg = row["treatment"]["unsegregated_kg_day"]
    unseg_t = round(unseg_kg / 1000.0, 2)

    coll_cap_kg = row["collection"]["collection_capacity_kg_day"]
    coll_cap_t = round(coll_cap_kg / 1000.0, 2)
    coll_gap_kg = row["collection"]["collection_gap_kg_day"]

    res_kg = row["base_person_waste_kg_day"]
    res_t = round(res_kg / 1000.0, 2)
    ind_kg = row["industrial_waste_kg_day"]
    ind_t = round(ind_kg / 1000.0, 2)

    if any(w in q for w in ["population", "people", "citizen", "inhabitant"]):
        answer = (
            f"👥 **Population Projection for Year {year}**:\n"
            f"• Effective Population: {pop:,.0f} citizens.\n"
            f"• Daily Per-Capita Waste: {params.get('waste_per_person_per_day', 0.5)} kg/person/day.\n"
            f"• Total Residential Generation: {res_t} tonnes/day ({res_kg:,.1f} kg/day)."
        )
    elif any(w in q for w in ["annual", "yearly", "per year", "annual waste"]):
        answer = (
            f"📅 **Annual Waste Projection for Year {year}**:\n"
            f"• Total Annual Tonnage: {annual_t:,.2f} tonnes/year.\n"
            f"• Equivalent Daily Generation: {daily_t:.2f} tonnes/day ({daily_kg:,.1f} kg/day).\n"
            f"• Cumulative 20-Year Impact: Projected to reach ~{annual_t * 20:,.0f} tonnes over 2 decades."
        )
    elif any(w in q for w in ["treatment", "capacity", "deficit", "plant", "shortage", "gap", "exceed"]):
        if treat_gap_kg > 0:
            answer = (
                f"⚠️ **Treatment Capacity Deficit in Year {year}**:\n"
                f"• Daily Waste Generation: {daily_t:.2f} tonnes/day ({daily_kg:,.1f} kg/day).\n"
                f"• Installed Plant Capacity: {treat_cap_t:.2f} tonnes/day ({treat_cap_kg:,.0f} kg/day).\n"
                f"• Daily Deficit: {treat_gap_t:.2f} tonnes/day ({treat_gap_kg:,.1f} kg/day).\n"
                f"👉 *Recommendation*: Expand processing capacity by at least {treat_gap_t} tonnes/day to achieve full coverage."
            )
        else:
            answer = (
                f"✅ **Treatment Capacity Status for Year {year}**:\n"
                f"• Installed capacity of {treat_cap_t} tonnes/day ({treat_cap_kg:,.0f} kg/day) is SUFFICIENT for Year {year}.\n"
                f"• Surplus capacity: {abs(treat_gap_t):.2f} tonnes/day."
            )
    elif any(w in q for w in ["fleet", "collection", "truck", "vehicle", "transport", "logistics"]):
        if coll_gap_kg > 0:
            answer = (
                f"🚛 **Collection Fleet Capacity Shortage in Year {year}**:\n"
                f"• Required Collection Load: {daily_t:.2f} tonnes/day.\n"
                f"• Current Fleet Throughput: {coll_cap_t:.2f} tonnes/day ({params.get('vehicle_count', 10)} trucks @ {params.get('vehicle_capacity_kg', 2000):,.0f} kg/trip).\n"
                f"• Fleet Shortage: {coll_gap_kg / 1000.0:.2f} tonnes/day.\n"
                f"👉 *Recommendation*: Procure additional collection trucks or increase trips per vehicle."
            )
        else:
            answer = (
                f"🚚 **Collection Fleet Capacity Status in Year {year}**:\n"
                f"• Current fleet capacity ({coll_cap_t} tonnes/day) is ADEQUATE to transport all {daily_t:.2f} tonnes/day of daily waste."
            )
    elif any(w in q for w in ["segregation", "recycle", "recycled", "landfill", "unsegregated"]):
        seg_pct = params.get("segregation_percent", 60)
        answer = (
            f"♻️ **Segregation & Recycling Breakdown for Year {year}**:\n"
            f"• Segregation Efficiency: {seg_pct}%.\n"
            f"• Segregated (Recycled / Composted): {seg_t:.2f} tonnes/day ({seg_kg:,.1f} kg/day).\n"
            f"• Unsegregated (Direct to Landfill): {unseg_t:.2f} tonnes/day ({unseg_kg:,.1f} kg/day).\n"
            f"👉 *Insight*: Increasing segregation to 80% would divert an extra {(daily_kg * 0.2) / 1000:.2f} tonnes/day away from landfills."
        )
    elif any(w in q for w in ["industrial", "commercial", "composition", "source"]):
        answer = (
            f"🧩 **Waste Source Composition for Year {year}**:\n"
            f"• Total Daily Generation: {daily_t:.2f} tonnes/day.\n"
            f"• Residential & Municipal Baseline: {res_t:.2f} tonnes/day ({res_kg:,.1f} kg/day).\n"
            f"• Industrial Baseline: {ind_t:.2f} tonnes/day ({ind_kg:,.1f} kg/day)."
        )
    elif any(w in q for w in ["advice", "recommend", "suggest", "action", "help", "do"]):
        answer = (
            f"💡 **Strategic Planning Advice for Year {year}**:\n"
            f"1. **Treatment Expansion**: Upgrade plant capacity by {treat_gap_t} t/day to bridge the treatment gap.\n"
            f"2. **Segregation Target**: Boost segregation from {params.get('segregation_percent', 60)}% to 80% to maximize material recovery.\n"
            f"3. **Fleet Planning**: Maintain total fleet capacity above {daily_t:.2f} tonnes/day."
        )
    else:
        answer = (
            f"📊 **SWMS Simulation Overview for Year {year}**:\n"
            f"• Projected Daily Waste: {daily_t:.2f} tonnes/day ({daily_kg:,.1f} kg/day).\n"
            f"• Annual Waste Generation: {annual_t:,.2f} tonnes/year.\n"
            f"• Effective Population: {pop:,.0f} inhabitants.\n"
            f"• Plant Capacity Deficit: {treat_gap_t:.2f} tonnes/day ({treat_gap_kg:,.0f} kg/day).\n"
            f"• Collection Fleet Throughput: {coll_cap_t:.2f} tonnes/day."
        )

    return {"answer": answer, "evidence": row}

@app.get("/api/v1/reports/{location_id}")
def report(location_id:int,s:Session=Depends(db),u:User=Depends(current_user)):
    return dashboard(location_id,s,u)
