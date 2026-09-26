"""Pure, explainable planning calculations used by API, dashboard and chatbot."""
from math import ceil

def waste_breakdown(p: dict, years: int = 0, event_population: float = 0, event_percent: float = 0) -> dict:
    model = p.get("model", "PERSON")
    growth = float(p.get("population_growth_rate", 0)) / 100
    permanent = float(p.get("permanent_population", p.get("total_population", 0))) * (1 + growth) ** years
    floating = float(p.get("floating_population", 0))
    tourist = float(p.get("tourist_population", 0))
    seasonal = float(p.get("seasonal_population", 0))
    migrant = float(p.get("migrant_population", 0))
    effective = permanent + floating + tourist + seasonal + migrant + event_population
    person = effective * float(p.get("waste_per_person_per_day", 0))
    households = float(p.get("households", 0)) * (1 + growth) ** years
    household = households * float(p.get("waste_per_household_per_day", 0))
    if model == "HOUSEHOLD": base = household
    elif model == "COMBINED": base = person + household
    else: base = person
    industrial = float(p.get("industrial_waste_kg_day", 0)) * (1 + float(p.get("industrial_growth_rate", 0))/100) ** years
    commercial = float(p.get("commercial_waste_kg_day", 0))
    market = float(p.get("market_waste_kg_day", 0))
    seasonal_factor = float(p.get("seasonal_factor", 1))
    adjusted = (base + industrial + commercial + market) * seasonal_factor
    event = adjusted * event_percent / 100
    daily = adjusted + event
    return {"year": years, "model": model, "base_population": round(permanent, 2), "effective_population": round(effective, 2), "base_person_waste_kg_day": round(person, 2), "base_household_waste_kg_day": round(household, 2), "industrial_waste_kg_day": round(industrial, 2), "commercial_waste_kg_day": round(commercial, 2), "market_waste_kg_day": round(market, 2), "seasonal_factor": seasonal_factor, "event_waste_kg_day": round(event, 2), "daily_waste_kg": round(daily, 2), "daily_waste_tonnes": round(daily/1000, 3), "monthly_waste_kg": round(daily*30, 2), "annual_waste_kg": round(daily*365, 2), "annual_waste_tonnes": round(daily*365/1000, 3)}

def collection_plan(daily_kg: float, vehicle_count: int, vehicle_capacity_kg: float, trips: int, coverage: float) -> dict:
    if vehicle_capacity_kg <= 0: raise ValueError("vehicle_capacity_kg must be greater than zero")
    required = daily_kg * coverage / 100
    capacity = vehicle_count * vehicle_capacity_kg * trips
    return {"required_collection_kg_day": required, "required_trips": ceil(required/vehicle_capacity_kg), "collection_capacity_kg_day": capacity, "collection_gap_kg_day": max(0, required-capacity), "status": "No collection capacity shortage" if capacity >= required else "Capacity shortage"}

def transport_plan(waste_kg: float, vehicle_count: int, vehicle_capacity_kg: float, trips: int) -> dict:
    if vehicle_capacity_kg <= 0: raise ValueError("vehicle_capacity_kg must be greater than zero")
    capacity = vehicle_count * vehicle_capacity_kg * trips
    return {"required_trips": ceil(waste_kg/vehicle_capacity_kg), "transport_capacity_kg_day": capacity, "transport_gap_kg_day": max(0, waste_kg-capacity)}

def treatment_plan(daily_kg: float, capacity_kg: float, segregation_percent: float) -> dict:
    segregated = daily_kg * segregation_percent/100
    return {"segregated_kg_day": round(segregated, 2), "unsegregated_kg_day": round(daily_kg-segregated, 2), "treatment_capacity_kg_day": capacity_kg, "treatment_gap_kg_day": max(0, daily_kg-capacity_kg), "status": "No treatment capacity shortage" if capacity_kg >= daily_kg else "Capacity shortage"}
