# BuildTech — Module 14: Deterministic Compatibility Engine Walkthrough

Module 14 delivers BuildTech's deterministic hardware compatibility verification system.

---

## Key Achievements

### 1. Authoritative Specification Audit & Migration
- Audited the 8 hardware specification tables in PostgreSQL (`cpu_specifications`, `gpu_specifications`, `motherboard_specifications`, `memory_specifications`, `storage_specifications`, `psu_specifications`, `case_specifications`, `cooling_specifications`).
- Identified missing specification fields on `motherboard_specifications` for RAM speed and storage interfaces.
- Created and applied Alembic migration `f2a3b4c5d6e7` (`add_motherboard_compatibility_fields`), adding:
  - `max_memory_speed_mhz`: `sa.Integer()`, nullable=True
  - `supported_storage_interfaces`: `sa.JSON()`, nullable=True

### 2. Deterministic Rule Engine
Implemented in `backend/app/modules/compatibility/rules.py` with 9 strict, isolated domain rules:
- `CPU_SOCKET`: CPU.socket == Motherboard.socket
- `RAM_TYPE`: RAM.memory_type == Motherboard.memory_type
- `RAM_SPEED`: RAM.speed_mhz <= Motherboard.max_memory_speed_mhz (or WARNING if unspecified)
- `GPU_CASE_CLEARANCE`: GPU.length_mm <= Case.max_gpu_length_mm
- `MOTHERBOARD_FORM_FACTOR`: Motherboard.form_factor in Case.supported_motherboard_form_factors
- `STORAGE_INTERFACE`: Storage.interface in Motherboard.supported_storage_interfaces (or WARNING if unspecified)
- `PSU_CAPACITY`: PSU wattage >= calculated system draw:
  $$\text{Estimated System Power} = \text{CPU TDP} + \text{GPU TDP} + 75\text{W}$$
  $$\text{Required PSU Wattage} = \lceil\text{Estimated System Power} \times 1.25\rceil$$
- `COOLER_SOCKET`: CPU.socket in Cooler.supported_sockets
- `COOLER_CASE_HEIGHT`: Cooler.height_mm <= Case.max_cpu_cooler_height_mm

### 3. Read-Only Repository & CompatibilityService
- Implemented `CompatibilityRepository` with eager `joinedload` on all specification models (zero N+1 queries).
- Implemented `CompatibilityService` executing rules in application memory and aggregating results into a deterministic response structure.
- Stable rule sorting ensures identical inputs always produce identical output orders.
- Zero mutations: never modifies inventory, carts, orders, or payments.

### 4. Customer-Safe API
- `POST /api/v1/compatibility/check`
- Accepts `product_ids` array, retrieves authoritative PostgreSQL data, and returns PASS / WARNING / FAIL status with detailed rule checks and power calculations.

### 5. Frontend Hardware Configurator
- `frontend/src/features/compatibility/pages/CompatibilityCheckerPage.jsx`
- Clean slot selectors for CPU, Motherboard, RAM, GPU, PSU, Case, Storage, and Cooler.
- URL pre-population support: `/compatibility?productId=...`.
- "Check Hardware Compatibility" entry point added to `ProductDetailPage.jsx`.
- Desktop and mobile navigation links added to `Navbar.jsx`.
- Accessible status banners for PASS, WARNING, and FAIL.
- System power estimates breakdown.
- Responsive design for mobile, tablet, and desktop; full dark mode support.

---

## Verification Results

### Backend Automated Test Suite
- **Rule Unit Tests (`test_compatibility_rules.py`)**: 25 tests passed.
- **Service Integration Tests (`test_compatibility_service.py`)**: 6 tests passed.
- **API Integration Tests (`test_compatibility_api.py`)**: 6 tests passed.
- **Full Backend Regression**: **341 passed in 116.94s** (304 baseline + 37 new tests, 0 regressions).

### PostgreSQL E2E Verification (`scratch/verify_compatibility_e2e.py`)
All 15 mandatory verification scenarios passed:
1. Compatible CPU + Motherboard (AM5 ↔ AM5) &rarr; `PASS`
2. Incompatible CPU + Motherboard (LGA1700 ↔ AM5) &rarr; `FAIL`
3. Compatible RAM + Motherboard (DDR5 ↔ DDR5) &rarr; `PASS`
4. Incompatible RAM + Motherboard (DDR4 ↔ DDR5) &rarr; `FAIL`
5. GPU fits Case (240mm &le; 320mm) &rarr; `PASS`
6. GPU exceeds Case clearance (360mm > 320mm) &rarr; `FAIL`
7. Sufficient PSU (850W &ge; calculated requirement) &rarr; `PASS`
8. Insufficient PSU (400W < calculated requirement) &rarr; `FAIL`
9. Missing specification produces `WARNING`
10. Multi-component aggregation &rarr; `PASS` (7 rules passed)
11. Determinism verified over multiple iterations
12. No inventory mutation verified
13. No cart mutation verified
14. No order creation verified
15. No payment creation verified

### Frontend Build & Lint
- `npm run lint`: 0 errors.
- `npm run build`: built production bundle in 520ms cleanly.

---

## Certification Status
**BUILDTECH MODULE 14 — COMPATIBILITY ENGINE: CERTIFIED**
