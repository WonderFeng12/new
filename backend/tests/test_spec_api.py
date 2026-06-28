"""
规格模块综合测试 (API Integration Tests)
Tests all spec CRUD endpoints, is_in_use tracking (Contract + ContractItem),
spec_name auto-generation, weight normalization, and edge cases.
"""
import requests
import json
import time
import random

# Unique numeric suffix to avoid collisions with seed data
# Length/width must be purely numeric per backend validation
TS = str(int(time.time()))[-5:]
SUFFIX = f"{TS}{random.randint(10,99)}"

BASE_URL = "http://localhost:8000/api"

# ----- Authentication -----
def get_token(username, password):
    resp = requests.post(f"{BASE_URL}/auth/login", json={
        "username": username, "password": password
    })
    assert resp.status_code == 200, f"Login failed for {username}: {resp.text}"
    data = resp.json()
    return data["access_token"], data["user"]

ADMIN_TOKEN, ADMIN_USER = get_token("admin", "admin123")
SALES_TOKEN, SALES_USER = get_token("sales", "sales123")
PRODUCER_TOKEN, PRODUCER_USER = get_token("producer", "prod123")

print(f"Admin: {ADMIN_USER['display_name']} ({ADMIN_USER['role']}) token={ADMIN_TOKEN[:20]}...")
print(f"Sales: {SALES_USER['display_name']} ({SALES_USER['role']}) token={SALES_TOKEN[:20]}...")
print(f"Producer: {PRODUCER_USER['display_name']} ({PRODUCER_USER['role']}) token={PRODUCER_TOKEN[:20]}...")

headers_admin = {"Authorization": f"Bearer {ADMIN_TOKEN}"}
headers_sales = {"Authorization": f"Bearer {SALES_TOKEN}"}
headers_producer = {"Authorization": f"Bearer {PRODUCER_TOKEN}"}

# ----- Test Helpers -----
def test(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    msg = f"  [{status}] {name}"
    if detail:
        msg += f" -- {detail}"
    print(msg)
    return condition

passed = 0
failed = 0
def check(name, condition, detail=""):
    global passed, failed
    if test(name, condition, detail):
        passed += 1
    else:
        failed += 1

def check_status(resp, expected=200):
    if resp.status_code != expected:
        print(f"    ERROR: expected {expected}, got {resp.status_code}")
        print(f"    Response: {resp.text[:500]}")
        return False
    return True

# =========================================================================
# 1. LIST SPECS
# =========================================================================
print("\n=== 1. LIST SPECS ===")

# List all specs
resp = requests.get(f"{BASE_URL}/specs", headers=headers_admin)
check_status(resp, 200)
specs = resp.json()
print(f"  Total specs found: {len(specs)}")
check("List specs returns list", isinstance(specs, list))

# Check each spec has required fields
for s in specs:
    check(f"Spec {s['id']} has spec_name", bool(s.get("spec_name")))
    check(f"Spec {s['id']} has is_in_use field", "is_in_use" in s)

# List with keyword
if specs:
    keyword = specs[0]["spec_name"][:3]
    resp_kw = requests.get(f"{BASE_URL}/specs?keyword={keyword}", headers=headers_admin)
    check_status(resp_kw, 200)
    filtered = resp_kw.json()
    check(f"Keyword '{keyword}' returns results", len(filtered) > 0, f"got {len(filtered)}")
    for s in filtered:
        check(f"Result matches keyword", keyword.lower() in s["spec_name"].lower())

# List with non-matching keyword
resp_kw = requests.get(f"{BASE_URL}/specs?keyword=ZZZZ_NOTEXIST", headers=headers_admin)
check_status(resp_kw, 200)
check("Non-matching keyword returns empty list", len(resp_kw.json()) == 0)

# All roles can list specs
for role_name, h in [("admin", headers_admin), ("sales", headers_sales), ("producer", headers_producer)]:
    resp = requests.get(f"{BASE_URL}/specs", headers=h)
    check(f"{role_name} can list specs", resp.status_code == 200)

# =========================================================================
# 2. CREATE SPEC
# =========================================================================
print("\n=== 2. CREATE SPEC ===")

# Create spec with valid data (weight as pure number, should auto-append KG)
created_spec_id = None
L1 = f"{SUFFIX}200"
W1 = f"{SUFFIX}240"
EXPECTED1 = f"{L1}*{W1}/4KG/单层"
resp = requests.post(f"{BASE_URL}/specs", headers=headers_admin, json={
    "length": L1,
    "width": W1,
    "weight": "4",
    "layer_type": "单层"
})
check_status(resp, 200)
spec = resp.json()
created_spec_id = spec["id"]
check("Create spec returns id", spec["id"] > 0)
check("spec_name is auto-generated", spec["spec_name"] == EXPECTED1,
      f"got '{spec['spec_name']}'")
check("spec_description matches spec_name", spec["spec_description"] == spec["spec_name"])
check("weight has KG suffix", spec["weight"] == "4KG", f"got '{spec['weight']}'")
check("is_in_use is False for new spec", spec["is_in_use"] == False)
check("created_by is set", bool(spec.get("created_by")))
check("updated_by is set", bool(spec.get("updated_by")))
print(f"  Created spec ID={spec['id']}: {spec['spec_name']}")

# Create spec with decimal weight
L2 = f"{SUFFIX}150"
W2 = f"{SUFFIX}200"
resp = requests.post(f"{BASE_URL}/specs", headers=headers_admin, json={
    "length": L2,
    "width": W2,
    "weight": "3.5",
    "layer_type": "双层"
})
check_status(resp, 200)
spec2 = resp.json()
check("Decimal weight", spec2["weight"] == "3.5KG", f"got '{spec2['weight']}'")
check("spec_name with decimal weight", spec2["spec_name"] == f"{L2}*{W2}/3.5KG/双层")
created_spec2_id = spec2["id"]

# Create spec with KG already in weight (should normalize)
L3 = f"{SUFFIX}180"
W3 = f"{SUFFIX}220"
resp = requests.post(f"{BASE_URL}/specs", headers=headers_admin, json={
    "length": L3,
    "width": W3,
    "weight": "5KG",
    "layer_type": "复合"
})
check_status(resp, 200)
spec3 = resp.json()
check("Weight normalization (KG already present)", spec3["weight"] == "5KG",
      f"got '{spec3['weight']}'")
check("spec_name after weight normalization", spec3["spec_name"] == f"{L3}*{W3}/5KG/复合")

# Create duplicate spec (same name)
resp = requests.post(f"{BASE_URL}/specs", headers=headers_admin, json={
    "length": L1,
    "width": W1,
    "weight": "4",
    "layer_type": "单层"
})
check("Duplicate spec returns 400", resp.status_code == 400,
      f"got {resp.status_code}: {resp.text[:100]}")
detail = resp.json().get("detail", "")
check("Duplicate error mentions spec name", EXPECTED1 in detail or "已存在" in detail)

# Create spec with invalid length (non-numeric)
resp = requests.post(f"{BASE_URL}/specs", headers=headers_admin, json={
    "length": "abc",
    "width": "240",
    "weight": "4",
    "layer_type": "单层"
})
check("Non-numeric length returns 400", resp.status_code == 400,
      f"got {resp.status_code}: {resp.text[:100]}")

# Create spec with invalid width (non-numeric)
resp = requests.post(f"{BASE_URL}/specs", headers=headers_admin, json={
    "length": "200",
    "width": "xyz",
    "weight": "4",
    "layer_type": "单层"
})
check("Non-numeric width returns 400", resp.status_code == 400)

# Create spec with invalid weight (non-numeric)
resp = requests.post(f"{BASE_URL}/specs", headers=headers_admin, json={
    "length": "200",
    "width": "240",
    "weight": "abc",
    "layer_type": "单层"
})
check("Non-numeric weight returns 400", resp.status_code == 400)

# All roles can create specs
L_sales = f"{SUFFIX}100"
W_sales = f"{SUFFIX}150"
resp = requests.post(f"{BASE_URL}/specs", headers=headers_sales, json={
    "length": L_sales, "width": W_sales, "weight": "2", "layer_type": "单层"
})
check("Sales can create spec", resp.status_code == 200,
      f"got {resp.status_code}")
if resp.status_code == 201:
    spec_sales_id = resp.json()["id"]
    check("Sales-created spec has created_by", bool(resp.json().get("created_by")))

L_prod = f"{SUFFIX}120"
W_prod = f"{SUFFIX}160"
resp = requests.post(f"{BASE_URL}/specs", headers=headers_producer, json={
    "length": L_prod, "width": W_prod, "weight": "2.5", "layer_type": "双层"
})
check("Producer can create spec", resp.status_code == 200,
      f"got {resp.status_code}")

# =========================================================================
# 3. GET SPEC BY ID
# =========================================================================
print("\n=== 3. GET SPEC ===")

resp = requests.get(f"{BASE_URL}/specs/{created_spec_id}", headers=headers_admin)
check_status(resp, 200)
spec = resp.json()
check("Get spec returns correct id", spec["id"] == created_spec_id)
check("Get spec has spec_name", spec["spec_name"] == EXPECTED1,
      f"got '{spec['spec_name']}'")
check("Get spec has is_in_use", "is_in_use" in spec)

# Get non-existent spec
resp = requests.get(f"{BASE_URL}/specs/99999", headers=headers_admin)
check("Get non-existent spec returns 404", resp.status_code == 404)

# All roles can get spec
resp = requests.get(f"{BASE_URL}/specs/{created_spec_id}", headers=headers_sales)
check("Sales can get spec", resp.status_code == 200)
resp = requests.get(f"{BASE_URL}/specs/{created_spec_id}", headers=headers_producer)
check("Producer can get spec", resp.status_code == 200)

# =========================================================================
# 4. UPDATE SPEC
# =========================================================================
print("\n=== 4. UPDATE SPEC ===")

# Update spec (not in use) - use unique lengths to avoid name collision
L_upd = f"{SUFFIX}210"
W_upd = f"{SUFFIX}250"
resp = requests.put(f"{BASE_URL}/specs/{created_spec_id}", headers=headers_admin, json={
    "length": L_upd,
    "width": W_upd
})
check_status(resp, 200)
spec = resp.json()
check("Update changes spec_name", spec["spec_name"] == f"{L_upd}*{W_upd}/4KG/单层",
      f"got '{spec['spec_name']}'")
check("Update preserves weight", spec["weight"] == "4KG")
check("Update preserves layer_type", spec["layer_type"] == "单层")
check("updated_by is set", bool(spec.get("updated_by")))

# Restore original
resp = requests.put(f"{BASE_URL}/specs/{created_spec_id}", headers=headers_admin, json={
    "length": L1, "width": W1
})
check_status(resp, 200)

# Update all fields
L_upd2 = f"{SUFFIX}300"
W_upd2 = f"{SUFFIX}350"
resp = requests.put(f"{BASE_URL}/specs/{created_spec_id}", headers=headers_admin, json={
    "length": L_upd2,
    "width": W_upd2,
    "weight": "6",
    "layer_type": "双层"
})
check_status(resp, 200)
spec = resp.json()
check("Update all fields changes spec_name",
      spec["spec_name"] == f"{L_upd2}*{W_upd2}/6KG/双层",
      f"got '{spec['spec_name']}'")

# Restore again
requests.put(f"{BASE_URL}/specs/{created_spec_id}", headers=headers_admin, json={
    "length": L1, "width": W1, "weight": "4", "layer_type": "单层"
})

# Update non-existent spec
resp = requests.put(f"{BASE_URL}/specs/99999", headers=headers_admin, json={
    "length": "200"
})
check("Update non-existent returns 404", resp.status_code == 404)

# Update to create duplicate
resp = requests.post(f"{BASE_URL}/specs", headers=headers_admin, json={
    "length": "500", "width": "600", "weight": "10", "layer_type": "复合"
})
check_status(resp, 200)
spec_dup = resp.json()

resp = requests.put(f"{BASE_URL}/specs/{created_spec_id}", headers=headers_admin, json={
    "length": "500", "width": "600", "weight": "10", "layer_type": "复合"
})
check("Update to duplicate name returns 400", resp.status_code == 400,
      f"got {resp.status_code}: {resp.text[:100]}")

# =========================================================================
# 5. DELETE SPEC (not in use)
# =========================================================================
print("\n=== 5. DELETE SPEC ===")

# Delete spec that is not in use
resp = requests.delete(f"{BASE_URL}/specs/{spec_dup['id']}", headers=headers_admin)
check("Delete non-referenced spec returns 200", resp.status_code == 200,
      f"got {resp.status_code}")

# Verify deleted
resp = requests.get(f"{BASE_URL}/specs/{spec_dup['id']}", headers=headers_admin)
check("Deleted spec returns 404", resp.status_code == 404)

# Delete non-existent spec
resp = requests.delete(f"{BASE_URL}/specs/99999", headers=headers_admin)
check("Delete non-existent returns 404", resp.status_code == 404)

# =========================================================================
# 6. CLONE SPEC
# =========================================================================
print("\n=== 6. CLONE SPEC ===")

resp = requests.post(f"{BASE_URL}/specs/{created_spec_id}/clone", headers=headers_admin)
check_status(resp, 200)
clone = resp.json()
check("Clone has same spec_name", clone["spec_name"] == EXPECTED1,
      f"got '{clone['spec_name']}'")
check("Clone has different id", clone["id"] != created_spec_id)
check("Clone has created_by set", bool(clone.get("created_by")))
print(f"  Cloned spec ID={clone['id']}: {clone['spec_name']}")

# Clone non-existent spec
resp = requests.post(f"{BASE_URL}/specs/99999/clone", headers=headers_admin)
check("Clone non-existent returns 404", resp.status_code == 404)

# =========================================================================
# 7. IS_IN_USE VIA CONTRACT.spec_id (legacy)
# =========================================================================
print("\n=== 7. IS_IN_USE via Contract.spec_id ===")

# Create a spec
L4 = f"{SUFFIX}400"
W4 = f"{SUFFIX}500"
resp = requests.post(f"{BASE_URL}/specs", headers=headers_admin, json={
    "length": L4, "width": W4, "weight": "8", "layer_type": "双层"
})
check_status(resp, 200)
spec_in_use = resp.json()
spec_in_use_id = spec_in_use["id"]
print(f"  Created spec ID={spec_in_use_id}: {spec_in_use['spec_name']}")

# Verify it's not in use yet
resp = requests.get(f"{BASE_URL}/specs/{spec_in_use_id}", headers=headers_admin)
check("Spec not in use yet", resp.json()["is_in_use"] == False)

# Create a customer and a contract referencing this spec
resp = requests.post(f"{BASE_URL}/customers", headers=headers_admin, json={
    "name": f"客户-规格引用-{SUFFIX}",
    "contact": "联系人",
    "phone": "13800138000"
})
check_status(resp, 200)
customer_id = resp.json()["id"]

contract_payload = {
    "contract_no": f"TEST{SUFFIX}1",
    "spec_id": spec_in_use_id,
    "customer_id": customer_id,
    "contract_date": "2026-06-26",
    "items": [
        {
            "line_no": 1,
            "spec_id": spec_in_use_id,
            "unit_price": 100,
            "qty": 10,
            "amount": 1000,
            "pattern_code": "P001"
        }
    ]
}
resp = requests.post(f"{BASE_URL}/contracts", headers=headers_admin, json=contract_payload)
if resp.status_code in (200, 201):
    contract_id = resp.json()["id"]
    print(f"  Created contract ID={contract_id} referencing spec via contract.spec_id")

    # Verify is_in_use = True
    resp = requests.get(f"{BASE_URL}/specs/{spec_in_use_id}", headers=headers_admin)
    check("is_in_use True when in Contract.spec_id", resp.json()["is_in_use"] == True,
          f"got is_in_use={resp.json()['is_in_use']}")

    # Verify spec cannot be edited
    resp = requests.put(f"{BASE_URL}/specs/{spec_in_use_id}", headers=headers_admin, json={
        "length": "999"
    })
    check("Cannot edit spec referenced by Contract", resp.status_code == 400,
          f"got {resp.status_code}: {resp.text[:100]}")

    # Verify spec cannot be deleted
    resp = requests.delete(f"{BASE_URL}/specs/{spec_in_use_id}", headers=headers_admin)
    check("Cannot delete spec referenced by Contract", resp.status_code == 400,
          f"got {resp.status_code}: {resp.text[:100]}")

    # Cleanup: delete contract
    resp = requests.delete(f"{BASE_URL}/contracts/{contract_id}", headers=headers_admin)
    print(f"  Cleaned up contract ID={contract_id}: status={resp.status_code}")
else:
    print(f"  WARNING: Could not create contract: {resp.status_code} {resp.text[:200]}")

# Ensure customer cleanup
requests.delete(f"{BASE_URL}/customers/{customer_id}", headers=headers_admin)

# =========================================================================
# 8. IS_IN_USE VIA ContractItem.spec_id (new feature)
# =========================================================================
print("\n=== 8. IS_IN_USE via ContractItem.spec_id ===")

# Create a spec
L5 = f"{SUFFIX}600"
W5 = f"{SUFFIX}700"
resp = requests.post(f"{BASE_URL}/specs", headers=headers_admin, json={
    "length": L5, "width": W5, "weight": "12", "layer_type": "复合"
})
check_status(resp, 200)
spec_item_ref = resp.json()
spec_item_ref_id = spec_item_ref["id"]
print(f"  Created spec ID={spec_item_ref_id}: {spec_item_ref['spec_name']}")

# Create customer
resp = requests.post(f"{BASE_URL}/customers", headers=headers_admin, json={
    "name": f"客户-行项目引用-{SUFFIX}",
    "contact": "联系人",
    "phone": "13900139000"
})
check_status(resp, 200)
customer_id2 = resp.json()["id"]

# Create a dummy spec for contract-level spec_id (not our test spec)
L_other = f"{SUFFIX}1"
W_other = f"{SUFFIX}1"
resp = requests.post(f"{BASE_URL}/specs", headers=headers_admin, json={
    "length": L_other, "width": W_other, "weight": "1", "layer_type": "单层"
})
check_status(resp, 200)
other_spec_id = resp.json()["id"]

contract_payload2 = {
    "contract_no": f"TEST{SUFFIX}2",
    "spec_id": other_spec_id,
    "customer_id": customer_id2,
    "contract_date": "2026-06-26",
    "items": [
        {
            "line_no": 1,
            "spec_id": spec_item_ref_id,  # Use our spec here
            "unit_price": 200,
            "qty": 5,
            "amount": 1000,
            "pattern_code": "P002"
        }
    ]
}
resp = requests.post(f"{BASE_URL}/contracts", headers=headers_admin, json=contract_payload2)
if resp.status_code in (200, 201):
    contract_id2 = resp.json()["id"]
    print(f"  Created contract ID={contract_id2}, item references spec via ContractItem.spec_id")

    # Verify is_in_use = True
    resp = requests.get(f"{BASE_URL}/specs/{spec_item_ref_id}", headers=headers_admin)
    check("is_in_use True when in ContractItem.spec_id",
          resp.json()["is_in_use"] == True,
          f"got is_in_use={resp.json()['is_in_use']}")

    # Also check list API shows is_in_use
    resp = requests.get(f"{BASE_URL}/specs", headers=headers_admin)
    list_specs = resp.json()
    for s in list_specs:
        if s["id"] == spec_item_ref_id:
            check("List API shows is_in_use for item-referenced spec",
                  s["is_in_use"] == True)
            break

    # Verify cannot edit
    resp = requests.put(f"{BASE_URL}/specs/{spec_item_ref_id}", headers=headers_admin, json={
        "weight": "99"
    })
    check("Cannot edit spec referenced by ContractItem", resp.status_code == 400,
          f"got {resp.status_code}: {resp.text[:100]}")

    # Verify cannot delete
    resp = requests.delete(f"{BASE_URL}/specs/{spec_item_ref_id}", headers=headers_admin)
    check("Cannot delete spec referenced by ContractItem", resp.status_code == 400,
          f"got {resp.status_code}: {resp.text[:100]}")

    # Cleanup
    resp = requests.delete(f"{BASE_URL}/contracts/{contract_id2}", headers=headers_admin)
    print(f"  Cleaned up contract ID={contract_id2}: status={resp.status_code}")
else:
    print(f"  WARNING: Could not create contract: {resp.status_code} {resp.text[:200]}")

requests.delete(f"{BASE_URL}/customers/{customer_id2}", headers=headers_admin)
requests.delete(f"{BASE_URL}/specs/{other_spec_id}", headers=headers_admin)

# =========================================================================
# 9. EDGE CASES
# =========================================================================
print("\n=== 9. EDGE CASES ===")

# Spec with very large dimensions
resp = requests.post(f"{BASE_URL}/specs", headers=headers_admin, json={
    "length": "9999", "width": "9999", "weight": "999", "layer_type": "单层"
})
check("Create spec with large dimensions", resp.status_code in (200, 201))
if resp.status_code in (200, 201):
    requests.delete(f"{BASE_URL}/specs/{resp.json()['id']}", headers=headers_admin)

# Create spec then check list includes it
L_edge = f"{SUFFIX}88"
W_edge = f"{SUFFIX}99"
resp = requests.post(f"{BASE_URL}/specs", headers=headers_admin, json={
    "length": L_edge, "width": W_edge, "weight": "1.234", "layer_type": "复合"
})
check_status(resp, 200)
spec_edge = resp.json()
check("Spec with decimal weight created", spec_edge["weight"] == "1.234KG")

# Verify it's in list
resp = requests.get(f"{BASE_URL}/specs?keyword={L_edge}*{W_edge}", headers=headers_admin)
check("Spec appears in keyword search", len(resp.json()) > 0)
found = any(s["id"] == spec_edge["id"] for s in resp.json())
check("Correct spec found by id", found)

# Cleanup
requests.delete(f"{BASE_URL}/specs/{spec_edge['id']}", headers=headers_admin)

# =========================================================================
# SUMMARY
# =========================================================================
print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed, {passed + failed} total")
print("=" * 60)

# Cleanup test specs we created
print("\n--- Cleanup ---")
for sid in [created_spec_id, created_spec2_id]:
    if sid:
        resp = requests.delete(f"{BASE_URL}/specs/{sid}", headers=headers_admin)
        print(f"  Deleted spec {sid}: {resp.status_code}")

if failed > 0:
    exit(1)
