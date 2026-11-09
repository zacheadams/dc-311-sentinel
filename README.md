# Washington, DC 311 Service Request Sentinel (2025 – 2026)

> [!NOTE]
> The technical documentation in this repository's Markdown files (`README.md`, `Agents.md`) is structured for automated agents, indexing, and technical architecture reference. The interactive analyses, spatial visualizations, and sortable matrices are published on the rendered site:
> - **[Project Hub & Query Trend Explorer (`index.html`)](https://zacheadams.github.io/dc-311-sentinel/)**
> - **[Emerging Issues & 30-Day Surge Acceleration Monitor (`emerging.html`)](https://zacheadams.github.io/dc-311-sentinel/emerging.html)**
> - **[Ward & ANC Areas of Concern (`wards.html`)](https://zacheadams.github.io/dc-311-sentinel/wards.html)**
> - **[Interactive Spatial Choropleth Map (`map.html`)](https://zacheadams.github.io/dc-311-sentinel/map.html)**
> - **[Other Analysis (`tables.html`)](https://zacheadams.github.io/dc-311-sentinel/tables.html)**

An open spatial and operational intelligence platform evaluating all **885,742** Washington, DC 311 service requests filed across **2025 (440,600 requests)** and **2026 YTD (445,142 requests through November 9, 2026)**.

---

## Executive Findings (2026 YTD through November 9, 2026)

### 1. District-Wide Volume & SLA Performance
- **Total 2026 YTD Requests (Jan 1 – Nov 9, 2026):** **445,142** vs. **395,801** in the exact same period of 2025 (**+12.5% YoY**).
- **Recent 30-Day Acceleration (Oct 11 – Nov 9, 2026):** **39,780** requests vs. **33,800** in the same 30 calendar days of 2025 (**+17.7% YoY**).
- **On-Time SLA Compliance:** Declined from **88.7%** in 2025 to **85.7%** in 2026 YTD (**-3.0 percentage points**), with **19,290** requests currently open in the 2026 backlog.
- **Top 10 Most Requested Services (2026 YTD):**
  1. **Bulk Collection (`S0031`):** 59,574 (13.38% of all 311 volume; +2.5% YoY)
  2. **Parking Enforcement (`S0261`):** 52,287 (11.75%; +6.6% YoY)
  3. **Scheduled Yard Waste (`S0476`):** 33,755 (7.58%; +1.4% YoY)
  4. **Trash Collection - Missed (`S0441`):** 31,245 (7.02%; **+34.6% YoY**)
  5. **DC Government Information (`DCGOVTINFO`):** 21,540 (4.84%; **+34.8% YoY**)
  6. **DC Health Rodent & Vector Control (`S0311`):** 18,950 combined across legacy `Rodent Inspection and Treatment` and renamed `DC Health Rodent & Vector Control` (4.26%; **+24.6% YoY**)
  7. **Illegal Dumping (`S0181`):** 16,823 (3.78%; **+14.4% YoY**)
  8. **Recycling Collection - Missed (`S0321`):** 13,591 (3.05%; -10.0% YoY)
  9. **Residential Parking Permit Violation (`S0331`):** 13,281 (2.98%; +1.9% YoY)
  10. **Sanitation Enforcement (`S0346`):** 12,720 (2.86%; +10.2% YoY)

### 2. Ward 1 – 8 Areas of Concern & Signature Concentrations (Location Quotients)
Using **Location Quotients ($\text{LQ} = \text{Local Share} / \text{Citywide Share}$)** across 100.0% spatially joined requests surfaces what is disproportionately concentrated in each Ward beyond raw volume leaders:

| Ward | Councilmember | 2026 YTD (YoY %) | SLA Met % | #1 Request by Volume | Top Disproportionate Signature Concerns (LQ) | Leading Ward Emerging Surge |
| :--- | :--- | ---: | ---: | :--- | :--- | :--- |
| **Ward 1** | Brianne Nadeau | 52,647 (+13.2%) | 85.4% | Parking Enforcement (7,996) | **Abandoned Bicycle** (2.60x LQ)<br>**Graffiti Removal** (2.39x LQ) | **Dockless Vehicle Parking** (+518.1%) |
| **Ward 2** | Brooke Pinto | 49,580 (+11.8%) | 86.3% | Parking Enforcement (8,518) | **Parking Meter Repair** (4.33x LQ)<br>**Emergency No-Parking** (3.97x LQ) | **Snow & Ice Removal** (+342.4%) |
| **Ward 3** | Matthew Frumin | 42,514 (+12.4%) | 78.8% | Bulk Collection (6,820) | **Missed Curbside Compost** (3.25x LQ)<br>**Supercan Repair** (2.58x LQ) | **Trash Collection - Missed** (+148.6%) |
| **Ward 4** | Janeese Lewis George | 66,074 (+13.2%) | 84.5% | Bulk Collection (10,696) | **Tree Planting** (2.30x LQ)<br>**DC Spray Parks** (2.12x LQ) | **Snow & Ice Removal** (+236.7%) |
| **Ward 5** | Zachary Parker | 66,966 (+10.9%) | 85.1% | Bulk Collection (9,445) | **DOEE Air Quality Concerns** (3.78x LQ)<br>**Trash Cart Repair** (2.41x LQ) | **Snow & Ice Removal** (+311.0%) |
| **Ward 6** | Charles Allen | 61,940 (+7.1%) | 88.1% | Parking Enforcement (10,086) | **DMV Hearings** (5.04x LQ)<br>**DMV Copy of Ticket** (4.56x LQ) | **DMV Refunds - Tickets** (+981.0%) |
| **Ward 7** | Wendell Felder | 59,739 (+16.9%) | 87.5% | Bulk Collection (10,153) | **Vacant Lot - Public Property** (2.25x LQ)<br>**Residential Snow Hero** (2.22x LQ) | **Snow & Ice Removal** (+354.4%) |
| **Ward 8** | Trayon White, Sr. | 45,680 (+15.8%) | 88.7% | DC Gov Information (12,823) | **DC Gov Information** (5.80x LQ)<br>**DOEE - LIHEAP** (2.75x LQ) | **Snow & Ice Removal** (+317.5%) |

### 3. Emerging Issues & 30-Day Surge Acceleration
Evaluating YTD same-period YoY growth alongside 30-day acceleration isolates true structural surges:
- **Dockless Vehicle Parking Complaint (`DOCVEH2022`):** Up **+157.0% YTD** (8,592 vs. 3,343) and **+776.6% in the last 30 days** (acceleration ratio: 4.95x).
- **Snow & Ice Removal on Public Space (`SnowIceRP24`) & ServeDC Snow Hero (`SERVDCSNOW`):** Up **+274.5%** (9,270 vs. 2,475) and **+211.3%** (4,477 vs. 1,438) driven by the major January 2026 winter storm event.
- **DMV Service & Ticket Processing Surges (`DMV01`, `DMV19`, `DMV66`, `ITISSUES`, `DMV31`):** Driver's License/ID Issues (**+116.3%**, 4,651 vs. 2,150), Vehicle Registration (**+88.6%**, 2,486 vs. 1,318), Online Processing Issues (**+136.4%** YTD, **+460.5%** in the last 30 days), and Copy of Ticket (**+242.2%**).
- **Sanitation & Public Space Infrastructure Surges:** Trash Cart Repair (`TRACO001`, **+72.7%**, 2,513 vs. 1,455), Missed Curbside Compost (`COMPOSTM`, **+68.2%**), Sidewalk Repair (`S0361`, **+55.1%**, 4,914 vs. 3,168), Public Space Litter Can Collection (`S0217`, **+54.6%** YTD, **+149.1%** in last 30 days), Rat Replacement Containers (`RATREPLACECONTRS`, **+44.1%**), Tree Inspection / Down Trees (`S0457`, **+39.5%**, 10,062 vs. 7,214), Trash Collection - Missed (`S0441`, **+34.6%**, 31,245 vs. 23,212), and Potholes (`S0301`, **+33.6%** YTD).

### 4. Unstructured `DETAILS` Column Audit
Full ingestion and inspection of the `DETAILS` column across all 885,742 tickets revealed that OUC populates `DETAILS` on only **777 records** in the public FeatureServer layer—and **774 (99.6%)** are identical Department of General Services (DGS) administrative mass-closure templates (`Playground Repair`, `Grounds Landscaping`, `Dog Park Maintenance`, `Spray Parks`, `Overflowing Recycling Can`, `Pool Maintenance`, `Grass Mowing Services Missed`) closing tickets in bulk and instructing residents to file a new 311 request if the issue remains.

---

## Local Setup & Pipeline Execution

```bash
# Create virtual environment and install analytical dependencies (duckdb, pyarrow)
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# Run the full pipeline (fetches boundaries, daily weather, and 2025-2026 311 data,
# builds data/warehouse.duckdb, computes JSON artifacts, and compiles HTML pages)
.venv/bin/python scripts/update_pipeline.py

# Rebuild warehouse, JSON, and HTML from local Parquet without network calls
.venv/bin/python scripts/update_pipeline.py --skip-fetch

# Run unit and data integrity test suite
.venv/bin/python -m unittest discover -s tests -v

# Sync raw Parquet and DuckDB warehouse to personal Google Drive (via rclone)
.venv/bin/python scripts/sync_gdrive.py push
.venv/bin/python scripts/sync_gdrive.py status

# Run full pipeline and automatically sync to Google Drive
.venv/bin/python scripts/update_pipeline.py --sync-gdrive

# Start local web server
python3 -m http.server 8000
```
