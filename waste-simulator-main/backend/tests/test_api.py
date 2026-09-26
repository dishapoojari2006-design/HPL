import os
os.environ["DATABASE_URL"]="sqlite:///./test_swms.db"
from fastapi.testclient import TestClient
from app.main import app, Base, engine
Base.metadata.drop_all(engine); Base.metadata.create_all(engine)
c=TestClient(app)
def auth():
    c.post('/api/v1/auth/register',json={'name':'Admin','email':'admin@example.com','password':'verysecurepass','role':'SUPER_ADMIN'})
    return {'Authorization':'Bearer '+c.post('/api/v1/auth/login',json={'email':'admin@example.com','password':'verysecurepass'}).json()['access_token']}
def test_health_and_protected_routes():
    assert c.get('/api/v1/health').status_code==200
    assert c.get('/api/v1/locations').status_code==401
def test_waste_and_simulation_flow():
    h=auth(); loc=c.post('/api/v1/locations',headers=h,json={'name':'Udupi Demo','location_type':'Gram Panchayat','latitude':13.3409,'longitude':74.7421}).json()
    p={'model':'PERSON','total_population':10000,'waste_per_person_per_day':0.5,'population_growth_rate':2,'vehicle_capacity_kg':2000,'vehicle_count':3,'treatment_capacity_kg':4000,'segregation_percent':60}
    assert c.post('/api/v1/calculations/waste',headers=h,json={'parameters':p}).json()['daily_waste_kg']==5000
    result=c.post('/api/v1/simulations',headers=h,json={'location_id':loc['id'],'years':5,'parameters':p}).json()
    assert len(result['results']['years'])==6
    assert result['results']['years'][5]['effective_population']>11040
    assert c.get('/api/v1/map',headers=h).json()['features'][0]['properties']['name']=='Udupi Demo'
