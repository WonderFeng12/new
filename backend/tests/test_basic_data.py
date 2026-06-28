"""
基础数据模块综合测试 (API Integration Tests)
Tests all basic-data CRUD endpoints: list, create, update, delete,
color mapping endpoint, and multi-role access.
"""
import requests
import json
import time
import random

TS = str(int(time.time()))[-5:]
SUFFIX = f"{TS}{random.randint(10,99)}"

BASE_URL = "http://localhost:8001/api"

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

# Track created IDs for cleanup
created_ids = []


# =========================================================================
# 1. CATEGORY LISTING
# =========================================================================
print("\n=== 1. CATEGORY LISTING ===")

# List packaging_type (seeded: 4 items)
resp = requests.get(f"{BASE_URL}/basic-data/packaging_type", headers=headers_admin)
check_status(resp, 200)
pt_items = resp.json()
print(f"  Packaging type items found: {len(pt_items)}")
check("List packaging_type returns list", isinstance(pt_items, list))
check("Packaging_type has 4 items", len(pt_items) == 4,
      f"got {len(pt_items)}")

# Verify structure of each item
if len(pt_items) > 0:
    item = pt_items[0]
    check("Item has id field", "id" in item)
    check("Item has category field", "category" in item)
    check("Item has code field", "code" in item)
    check("Item has value field", "value" in item)
    check("Item has sort_order field", "sort_order" in item)

# Verify seed data content
seed_codes = ["纸箱", "抽真空", "压缩包", "打卷面料"]
pt_codes = [item["code"] for item in pt_items]
for expected_code in seed_codes:
    check(f"Seed item '{expected_code}' exists", expected_code in pt_codes,
          f"found codes: {pt_codes}")

# Verify sort_order
for item in pt_items:
    expected_order = seed_codes.index(item["code"]) + 1
    check(f"Item '{item['code']}' has correct sort_order",
          item["sort_order"] == expected_order,
          f"expected {expected_order}, got {item['sort_order']}")

# List color_mapping (no seed data -> empty)
resp = requests.get(f"{BASE_URL}/basic-data/color_mapping", headers=headers_admin)
check_status(resp, 200)
cm_items = resp.json()
check("List color_mapping returns list", isinstance(cm_items, list))
check("color_mapping is empty initially", len(cm_items) == 0,
      f"got {len(cm_items)} items")

# List non-existent category -> empty list
resp = requests.get(f"{BASE_URL}/basic-data/nonexistent_category", headers=headers_admin)
check_status(resp, 200)
non_items = resp.json()
check("Non-existent category returns list", isinstance(non_items, list))
check("Non-existent category is empty", len(non_items) == 0)

# List endpoint works without authentication (no JWT required)
resp = requests.get(f"{BASE_URL}/basic-data/packaging_type")
check("List endpoint works without auth", resp.status_code == 200,
      f"got {resp.status_code}")


# =========================================================================
# 2. CREATE (color_mapping)
# =========================================================================
print("\n=== 2. CREATE (color_mapping) ===")

# Create with all fields
resp = requests.post(f"{BASE_URL}/basic-data/color_mapping", headers=headers_admin, json={
    "category": "color_mapping",
    "code": f"红色_{SUFFIX}",
    "value": "#FF0000",
    "sort_order": 1
})
check_status(resp, 200)
red = resp.json()
created_ids.append(red["id"])
check("Create returns id", red["id"] > 0)
check("Create returns correct category", red["category"] == "color_mapping",
      f"got '{red['category']}'")
check("Create returns correct code", red["code"] == f"红色_{SUFFIX}",
      f"got '{red['code']}'")
check("Create returns correct value", red["value"] == "#FF0000",
      f"got '{red['value']}'")
check("Create returns correct sort_order", red["sort_order"] == 1,
      f"got {red['sort_order']}")
print(f"  Created color_mapping ID={red['id']}: {red['code']} = {red['value']}")

# Create another item
resp = requests.post(f"{BASE_URL}/basic-data/color_mapping", headers=headers_admin, json={
    "category": "color_mapping",
    "code": f"蓝色_{SUFFIX}",
    "value": "#0000FF",
    "sort_order": 2
})
check_status(resp, 200)
blue = resp.json()
created_ids.append(blue["id"])
check("Second item has correct code", blue["code"] == f"蓝色_{SUFFIX}")
check("Second item has correct sort_order", blue["sort_order"] == 2)
print(f"  Created color_mapping ID={blue['id']}: {blue['code']} = {blue['value']}")

# Create item without value (optional value defaults to "")
resp = requests.post(f"{BASE_URL}/basic-data/color_mapping", headers=headers_admin, json={
    "category": "color_mapping",
    "code": f"绿色_{SUFFIX}",
    "sort_order": 3
})
check_status(resp, 200)
green = resp.json()
created_ids.append(green["id"])
check("Item without value has empty string value",
      green.get("value") in ("", None),
      f"got '{green.get('value')}'")
check("Item without value still gets sort_order", green["sort_order"] == 3)
print(f"  Created color_mapping ID={green['id']}: {green['code']} (no value)")

# Create item with sort_order=0
resp = requests.post(f"{BASE_URL}/basic-data/color_mapping", headers=headers_admin, json={
    "category": "color_mapping",
    "code": f"白色_{SUFFIX}",
    "value": "#FFFFFF",
    "sort_order": 0
})
check_status(resp, 200)
white = resp.json()
created_ids.append(white["id"])
check("Item with sort_order=0 preserves value", white["sort_order"] == 0,
      f"got {white['sort_order']}")
print(f"  Created color_mapping ID={white['id']}: {white['code']} sort_order=0")

# Verify color_mapping list now has 4 items
resp = requests.get(f"{BASE_URL}/basic-data/color_mapping", headers=headers_admin)
check_status(resp, 200)
check("color_mapping now has 4 items", len(resp.json()) == 4,
      f"got {len(resp.json())} items")


# =========================================================================
# 3. CREATE (packaging_type)
# =========================================================================
print("\n=== 3. CREATE (packaging_type) ===")

# Create new packaging_type
resp = requests.post(f"{BASE_URL}/basic-data/packaging_type", headers=headers_admin, json={
    "category": "packaging_type",
    "code": f"测试包装_{SUFFIX}",
    "value": f"测试包装_{SUFFIX}",
    "sort_order": 5
})
check_status(resp, 200)
new_pt = resp.json()
created_ids.append(new_pt["id"])
check("New packaging_type has correct code", new_pt["code"] == f"测试包装_{SUFFIX}")
check("New packaging_type has correct value", new_pt["value"] == f"测试包装_{SUFFIX}")
print(f"  Created packaging_type ID={new_pt['id']}: {new_pt['code']}")

# Verify it appears in list
resp = requests.get(f"{BASE_URL}/basic-data/packaging_type", headers=headers_admin)
check_status(resp, 200)
pt_after = resp.json()
check("Packaging_type now has 5 items", len(pt_after) == 5,
      f"got {len(pt_after)}")
codes_after = [item["code"] for item in pt_after]
check("New item appears in list", f"测试包装_{SUFFIX}" in codes_after)

# Verify ordering (new item has sort_order=5, should be last)
check("New item is last in list",
      pt_after[-1]["code"] == f"测试包装_{SUFFIX}",
      f"last item code is '{pt_after[-1]['code']}'")


# =========================================================================
# 4. UPDATE
# =========================================================================
print("\n=== 4. UPDATE ===")

# Update all fields
resp = requests.put(
    f"{BASE_URL}/basic-data/color_mapping/{red['id']}",
    headers=headers_admin,
    json={
        "code": f"红色_更新_{SUFFIX}",
        "value": "#FF3333",
        "sort_order": 10
    }
)
check_status(resp, 200)
updated = resp.json()
check("Update changes code", updated["code"] == f"红色_更新_{SUFFIX}",
      f"got '{updated['code']}'")
check("Update changes value", updated["value"] == "#FF3333",
      f"got '{updated['value']}'")
check("Update changes sort_order", updated["sort_order"] == 10,
      f"got {updated['sort_order']}")
check("Update preserves id", updated["id"] == red["id"])
check("Update preserves category", updated["category"] == "color_mapping")
print(f"  Updated ID={red['id']}: code='{updated['code']}' value='{updated['value']}' sort_order={updated['sort_order']}")

# Partial update (only one field)
resp = requests.put(
    f"{BASE_URL}/basic-data/color_mapping/{red['id']}",
    headers=headers_admin,
    json={"sort_order": 5}
)
check_status(resp, 200)
partial = resp.json()
check("Partial update changes only sort_order", partial["sort_order"] == 5,
      f"got {partial['sort_order']}")
check("Partial update preserves code", partial["code"] == f"红色_更新_{SUFFIX}",
      f"got '{partial['code']}'")
check("Partial update preserves value", partial["value"] == "#FF3333",
      f"got '{partial['value']}'")

# Restore original values
requests.put(
    f"{BASE_URL}/basic-data/color_mapping/{red['id']}",
    headers=headers_admin,
    json={
        "code": f"红色_{SUFFIX}",
        "value": "#FF0000",
        "sort_order": 1
    }
)

# Update with only value field
resp = requests.put(
    f"{BASE_URL}/basic-data/color_mapping/{red['id']}",
    headers=headers_admin,
    json={"value": "#FF1111"}
)
check_status(resp, 200)
val_only = resp.json()
check("Value-only update changes value", val_only["value"] == "#FF1111")
# Restore
requests.put(
    f"{BASE_URL}/basic-data/color_mapping/{red['id']}",
    headers=headers_admin,
    json={"value": "#FF0000"}
)

# Update non-existent id
resp = requests.put(
    f"{BASE_URL}/basic-data/color_mapping/99999",
    headers=headers_admin,
    json={"value": "anything"}
)
check("Update non-existent returns 404", resp.status_code == 404,
      f"got {resp.status_code}: {resp.text[:100]}")


# =========================================================================
# 5. DELETE
# =========================================================================
print("\n=== 5. DELETE ===")

# Delete an item (the white item with sort_order=0)
resp = requests.delete(
    f"{BASE_URL}/basic-data/color_mapping/{white['id']}",
    headers=headers_admin
)
check_status(resp, 200)
delete_resp = resp.json()
check("Delete returns ok", delete_resp.get("ok") == True,
      f"got {delete_resp}")

# Remove from created_ids since deleted
if white['id'] in created_ids:
    created_ids.remove(white['id'])

# Verify item is gone from list
resp = requests.get(f"{BASE_URL}/basic-data/color_mapping", headers=headers_admin)
check_status(resp, 200)
items_after_delete = resp.json()
check("Deleted item removed from list", len(items_after_delete) == 3,
      f"got {len(items_after_delete)} items")
deleted_ids = [item["id"] for item in items_after_delete]
check("Deleted item id not in list", white['id'] not in deleted_ids)

# Delete non-existent
resp = requests.delete(
    f"{BASE_URL}/basic-data/color_mapping/99999",
    headers=headers_admin
)
check("Delete non-existent returns 404", resp.status_code == 404,
      f"got {resp.status_code}: {resp.text[:100]}")

# Double-delete should also 404
resp = requests.delete(
    f"{BASE_URL}/basic-data/color_mapping/{white['id']}",
    headers=headers_admin
)
check("Delete already-deleted returns 404", resp.status_code == 404,
      f"got {resp.status_code}: {resp.text[:100]}")


# =========================================================================
# 6. COLOR MAPPING ENDPOINT
# =========================================================================
print("\n=== 6. COLOR MAPPING ENDPOINT ===")

# Get color mapping
resp = requests.get(f"{BASE_URL}/basic-data/mapping/color")
check_status(resp, 200)
mapping = resp.json()
check("Color mapping returns dict", isinstance(mapping, dict))

# Should include items with non-empty value
check("Mapping includes red",
      mapping.get(f"红色_{SUFFIX}") == "#FF0000",
      f"got {mapping}")
check("Mapping includes blue",
      mapping.get(f"蓝色_{SUFFIX}") == "#0000FF",
      f"got {mapping}")

# Should NOT include green (value was empty)
check("Mapping excludes items without value",
      f"绿色_{SUFFIX}" not in mapping,
      f"mapping keys: {list(mapping.keys())}")

# Should NOT include deleted white item
check("Mapping excludes deleted items",
      f"白色_{SUFFIX}" not in mapping)

# Endpoint works without auth
resp = requests.get(f"{BASE_URL}/basic-data/mapping/color")
check("Color mapping works without auth", resp.status_code == 200)


# =========================================================================
# 7. MULTI-ROLE ACCESS
# =========================================================================
print("\n=== 7. MULTI-ROLE ACCESS ===")

role_code_suffix = f"{SUFFIX}"

# All roles can list
for role_name, h in [("admin", headers_admin), ("sales", headers_sales), ("producer", headers_producer)]:
    resp = requests.get(f"{BASE_URL}/basic-data/packaging_type", headers=h)
    check(f"{role_name} can list", resp.status_code == 200)

# All roles can create
for role_name, h in [("admin", headers_admin), ("sales", headers_sales), ("producer", headers_producer)]:
    create_code = f"{role_name}_创建_{role_code_suffix}"
    resp = requests.post(f"{BASE_URL}/basic-data/color_mapping", headers=h, json={
        "category": "color_mapping",
        "code": create_code,
        "sort_order": 99
    })
    check(f"{role_name} can create", resp.status_code == 200,
          f"got {resp.status_code}: {resp.text[:100]}")
    if resp.status_code == 200:
        created_ids.append(resp.json()["id"])

# Verify all created items exist
resp = requests.get(f"{BASE_URL}/basic-data/color_mapping", headers=headers_admin)
check_status(resp, 200)
all_items = resp.json()
all_codes = [item["code"] for item in all_items]
for role_name in ["admin", "sales", "producer"]:
    expected_code = f"{role_name}_创建_{role_code_suffix}"
    check(f"Item created by {role_name} exists in list",
          expected_code in all_codes,
          f"missing '{expected_code}'")

# All roles can update
for role_name, h in [("admin", headers_admin), ("sales", headers_sales), ("producer", headers_producer)]:
    resp = requests.put(
        f"{BASE_URL}/basic-data/color_mapping/{red['id']}",
        headers=h,
        json={"sort_order": 1}
    )
    check(f"{role_name} can update", resp.status_code == 200,
          f"got {resp.status_code}")

# All roles can delete (delete a freshly created item)
delete_targets = []
for role_name, h in [("sales", headers_sales), ("producer", headers_producer)]:
    # Create an item specifically to delete
    resp = requests.post(f"{BASE_URL}/basic-data/color_mapping", headers=h, json={
        "category": "color_mapping",
        "code": f"{role_name}_待删除_{role_code_suffix}",
        "sort_order": 100
    })
    if resp.status_code == 200:
        delete_targets.append((role_name, h, resp.json()["id"]))

for role_name, h, did in delete_targets:
    resp = requests.delete(
        f"{BASE_URL}/basic-data/color_mapping/{did}",
        headers=h
    )
    check(f"{role_name} can delete own created item", resp.status_code == 200,
          f"got {resp.status_code}: {resp.text[:100]}")


# =========================================================================
# 8. EDGE CASES
# =========================================================================
print("\n=== 8. EDGE CASES ===")

# Create item with special characters in code
special_code = f"特殊/符号&空格_{SUFFIX}"
resp = requests.post(f"{BASE_URL}/basic-data/color_mapping", headers=headers_admin, json={
    "category": "color_mapping",
    "code": special_code,
    "value": "#123456",
    "sort_order": 200
})
check_status(resp, 200)
special_item = resp.json()
created_ids.append(special_item["id"])
check("Create with special chars in code", special_item["code"] == special_code,
      f"got '{special_item['code']}'")

# Verify in mapping
resp = requests.get(f"{BASE_URL}/basic-data/mapping/color")
check_status(resp, 200)
mapping = resp.json()
check("Special char item in mapping", mapping.get(special_code) == "#123456")

# Create item with very long values
long_code = "A" * 90
resp = requests.post(f"{BASE_URL}/basic-data/color_mapping", headers=headers_admin, json={
    "category": "color_mapping",
    "code": long_code,
    "value": "B" * 190,
    "sort_order": 300
})
check_status(resp, 200)
long_item = resp.json()
created_ids.append(long_item["id"])
check("Create with long code (90 chars)", len(long_item["code"]) == 90)
check("Create with long value (190 chars)", len(long_item["value"]) == 190)

# Update item to empty value
resp = requests.put(
    f"{BASE_URL}/basic-data/color_mapping/{green['id']}",
    headers=headers_admin,
    json={"value": "now_has_value"}
)
check_status(resp, 200)
check("Update empty value to non-empty", resp.json()["value"] == "now_has_value")
# Restore
requests.put(
    f"{BASE_URL}/basic-data/color_mapping/{green['id']}",
    headers=headers_admin,
    json={"value": ""}
)


# =========================================================================
# CLEANUP
# =========================================================================
print("\n=== CLEANUP ===")
for item_id in created_ids:
    resp = requests.delete(
        f"{BASE_URL}/basic-data/color_mapping/{item_id}",
        headers=headers_admin
    )
    status = "ok" if resp.status_code == 200 else f"fail({resp.status_code})"
    print(f"  Delete ID={item_id}: {status}")

# Also clean up the test packaging_type
resp = requests.delete(
    f"{BASE_URL}/basic-data/packaging_type/{new_pt['id']}",
    headers=headers_admin
)
print(f"  Delete packaging_type ID={new_pt['id']}: {'ok' if resp.status_code == 200 else 'fail(' + str(resp.status_code) + ')'}")

# Verify clean state: color_mapping back to 0
resp = requests.get(f"{BASE_URL}/basic-data/color_mapping", headers=headers_admin)
check("color_mapping back to empty after cleanup", len(resp.json()) == 0,
      f"got {len(resp.json())} items remaining")

# Verify packaging_type back to 4
resp = requests.get(f"{BASE_URL}/basic-data/packaging_type", headers=headers_admin)
check("packaging_type back to 4 after cleanup", len(resp.json()) == 4,
      f"got {len(resp.json())} items")


# =========================================================================
# SUMMARY
# =========================================================================
print("\n" + "=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed, {passed + failed} total")
print("=" * 60)

if failed > 0:
    exit(1)
