# 🚛 SWMS: Smart Waste Management Simulator — Comprehensive Demonstration & System Architecture Report

---

## 1. Executive Summary
The **Smart Waste Management Simulator (SWMS)** is a decision-support platform designed for **Urban Local Bodies (ULBs)**, **Gram Panchayats**, **Urban Planners**, and **Environmental Policy Officers**.

It transforms static census and demographic data into **dynamic, explainable 20-year waste projections**, allowing city administrators to **plan infrastructure capacity before it becomes a public health or environmental crisis**.

---

## 2. Core System Architecture & Technology Stack

```mermaid
graph TD
    A[React Frontend (Vite + Recharts)] -->|JWT Auth Header| B[FastAPI Backend REST Services]
    B --> C[Explainable Math Engine (calculations.py)]
    B --> D[SQLite Database (swms.db / SQLAlchemy ORM)]
    B --> E[Dynamic LLM Decision Assistant / Chatbot]
```

* **Frontend**: React 18, Recharts (Visualizations & Feasibility Threshold Lines), Axios, Vanilla CSS design tokens.
* **Backend**: FastAPI (Python), Pydantic v2 (Validation & Schemas), PyJWT (HS256 Bearer Token Authentication).
* **Database**: SQLite / PostgreSQL with SQLAlchemy ORM (`users`, `locations`, `planning_records`, `simulation_runs`).
* **Physics & Math Engine**: Pure, explainable planning algorithms (`backend/app/calculations.py`).

---

## 3. Role-Based Access Control (RBAC) Architecture

SWMS implements strict, enterprise-grade Role-Based Access Control at both the **API Route level** and **Frontend UI level**:

| Role | Core Purpose | System Capabilities | Visible Controls |
| :--- | :--- | :--- | :--- |
| **`SUPER_ADMIN`** | System Administration | Full access to user management, location creation, data record edits, deletes, and simulation runs. | Full Control + User Management |
| **`MUNICIPAL_AUTHORITY`** | City-Level Commissioner / ULB Officer | Planning across urban wards, approving infrastructure investments, creating locations, running simulations. | Input Form + Run Simulation |
| **`PANCHAYAT_AUTHORITY`** | Rural Development Officer | Managing village habitations, rural composting hubs, regional collection fleets, running simulations. | Input Form + Run Simulation |
| **`PLANNER`** | Urban / Environmental Engineer | Setting growth parameters, evaluating 20-year infrastructure deficit limits, running simulations. | Input Form + Run Simulation |
| **`DATA_ENTRY`** | Field Data Clerk | Entering ground census statistics, habitations, and infrastructure records. Restricted from deleting records or running simulations. | Form Inputs (Read/Edit Only) |
| **`VIEWER`** | Auditor, Citizen, NGO Researcher | Read-only inspection of published 20-year regional master plans, visual charts, deficit warnings, and chatbot Q&A. | Read-Only Dashboard & Charts (Form Inputs & Buttons Hidden) |

---

## 4. Mathematical Engine & Formulas

All simulator projections are completely **deterministic, explainable, and audit-friendly**:

### 4.1 Population Projection Formula
$$\text{Permanent Population}_t = \text{Permanent Population}_0 \times \left(1 + \frac{\text{Growth Rate}}{100}\right)^t$$

$$\text{Effective Population}_t = \text{Permanent}_t + \text{Floating} + \text{Tourist} + \text{Seasonal} + \text{Migrant} + \text{Event Population}$$

### 4.2 Daily Waste Generation
$$\text{Residential Waste (kg/day)} = \text{Effective Population}_t \times \text{Waste Per Person Per Day (kg)}$$

$$\text{Industrial Waste (kg/day)} = \text{Industrial Waste}_0 \times \left(1 + \frac{\text{Industrial Growth Rate}}{100}\right)^t$$

$$\text{Total Daily Waste (kg/day)} = (\text{Residential} + \text{Industrial} + \text{Commercial} + \text{Market}) \times \text{Seasonal Factor}$$

$$\text{Daily Tonnage (tonnes/day)} = \frac{\text{Total Daily Waste (kg/day)}}{1000}$$

### 4.3 Logistics & Collection Fleet Gap
$$\text{Required Collection Load (kg/day)} = \text{Total Daily Waste} \times \frac{\text{Collection Coverage \%}}{100}$$

$$\text{Fleet Throughput Capacity (kg/day)} = \text{Vehicle Count} \times \text{Vehicle Capacity (kg/trip)} \times \text{Trips Per Vehicle}$$

$$\text{Fleet Deficit (kg/day)} = \max(0, \text{Required Collection Load} - \text{Fleet Capacity})$$

### 4.4 Treatment Plant Deficit & Landfill Divergence
$$\text{Segregated Material (Recycled/Composted)} = \text{Total Daily Waste} \times \frac{\text{Segregation \%}}{100}$$

$$\text{Unsegregated Waste (Direct to Landfill)} = \text{Total Daily Waste} - \text{Segregated Material}$$

$$\text{Treatment Deficit (kg/day)} = \max(0, \text{Total Daily Waste} - \text{Installed Treatment Plant Capacity})$$

---

## 5. Input Validation Framework

To prevent invalid physics, zero-division crashes, or corrupt data entry, both client-side and server-side schemas enforce strict boundaries:

| Input Field | Lower Bound | Upper Bound | Step | Validation Rationale |
| :--- | :---: | :---: | :---: | :--- |
| `total_population` | $0$ | $100,000,000$ | $100$ | Cannot have negative population |
| `waste_per_person_per_day` | $0.01\text{ kg}$ | $10.0\text{ kg}$ | $0.01$ | Standard human baseline ($0.1$–$5.0$ kg) |
| `population_growth_rate` | $-10.0\%$ | $25.0\%$ | $0.1$ | Realistic demographic limits |
| `vehicle_count` | $0$ | $10,000$ | $1$ | Fleet count |
| `vehicle_capacity_kg` | **$> 0\text{ kg}$** | $100,000\text{ kg}$ | $100$ | **Prevents division by zero in trip calculations** |
| `trips_per_vehicle` | **$\ge 1$** | $20$ | $1$ | Minimum 1 trip required per active truck |
| `segregation_percent` | $0\%$ | $100\%$ | $1$ | Physical percentage bound |
| `treatment_capacity_kg` | $0\text{ kg}$ | $100,000,000\text{ kg}$ | $500$ | Plant daily processing throughput |

---

## 6. Step-by-Step Live Demonstration Script for Tomorrow

Use this exact walkthrough during your presentation:

### Step 1: Introduction & Login (1 minute)
1. Launch app at `http://localhost:5173`.
2. **Point out**: *"SWMS is a decision-support simulator. It provides tailored interfaces depending on user authority."*
3. Log in with **Planner Account**: `planner@swms.org` (Password: `Password123!`).

### Step 2: Parameter Configuration & Real-Time Validation (2 minutes)
1. Show the **Planning Inputs Grid**: Total Population ($25,000$), Waste/Person ($0.5$ kg/day), Vehicle Capacity ($2,000$ kg), Treatment Capacity ($10,000$ kg).
2. **Demonstrate Input Safety**: Type `0` into *Vehicle Capacity*.
3. Point out the **real-time inline warning**: `⚠️ Must be greater than 0 kg`. Show that invalid inputs turn red and block submission safely.
4. Correct *Vehicle Capacity* back to `2000`.

### Step 3: Running the 20-Year Simulation (2 minutes)
1. Click **Run 20-year simulation**.
2. Highlight the **Active Region Context Banner**: `📍 Udupi Demonstration (Gram Panchayat)`.
3. Highlight the 3 **Key Metric Cards**:
   - **Baseline Waste (Year 0)**: $15.5\text{ t/day}$
   - **Projected Waste (Year 20)**: $21.574\text{ t/day}$
   - **Treatment Plant Deficit (Year 0)**: $5,500\text{ kg/day}$
4. Point to the **Feasibility Analysis Chart**: Show how the red threshold line highlights exact years where waste generation exceeds installed plant capacity.

### Step 4: Role-Based Access Control Demonstration (2 minutes)
1. Click **Sign out** at the top right.
2. Log in as **Viewer Account**: `viewer@swms.org` (Password: `Password123!`).
3. **Point out**: *"Notice how for an auditor or citizen viewer, the input forms and simulation buttons are automatically hidden. Viewers immediately see the published master plan without clutter or risk of modifying parameters."*

### Step 5: AI Planning Assistant / Chatbot (1 minute)
1. Ask the chatbot: `"What is the treatment gap in year 10?"`
2. Show how the assistant reads exact simulation numbers from the backend database to give precise planning advice.

---

## 7. Frequently Asked Questions (FAQ) for Demo Observers

**Q1: How are population growth and floating populations combined?**
*Answer*: Permanent population grows compoundly over time ($P_t = P_0 (1+r)^t$), while floating/tourist populations add to daily effective volume, capturing both residential load and tourist spikes.

**Q2: How does the system prevent invalid inputs or division-by-zero crashes?**
*Answer*: SWMS uses double-layer validation. The frontend uses HTML5 bounds and real-time JavaScript validation state with inline warnings, while the backend FastAPI schemas enforce strict Pydantic rules (`vehicle_capacity_kg > 0`).

**Q3: Can viewer roles change data or trigger simulations?**
*Answer*: No. The backend strictly checks JWT claims (`require("SUPER_ADMIN", "PLANNER", ...)`), and the frontend hides input fields and submission controls for `VIEWER` roles.
