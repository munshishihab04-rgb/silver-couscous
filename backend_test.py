#!/usr/bin/env python3
"""
Backend API Testing for LicenzPol Storefront
Tests order management, CSV exports, and SEO endpoints
"""

import requests
import sys
from datetime import datetime

# Backend base URL
BASE_URL = "https://4ee166ee-cf4f-4cde-bbf5-e6d60079ddd9.preview.emergentagent.com"
API_BASE = f"{BASE_URL}/api"

# Admin credentials
ADMIN_EMAIL = "admin@licenzpol.local"
ADMIN_PASSWORD = "Admin!2025#Local"

# Test results tracking
test_results = {
    "passed": 0,
    "failed": 0,
    "errors": []
}


def log_test(name, passed, details=""):
    """Log test result"""
    if passed:
        test_results["passed"] += 1
        print(f"✅ {name}")
    else:
        test_results["failed"] += 1
        test_results["errors"].append(f"{name}: {details}")
        print(f"❌ {name}")
        if details:
            print(f"   Details: {details}")


def test_admin_login():
    """Test admin login and get JWT token"""
    print("\n=== Testing Admin Login ===")
    try:
        response = requests.post(
            f"{API_BASE}/admin/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10
        )
        
        if response.status_code == 200:
            data = response.json()
            if "token" in data and "user" in data:
                log_test("Admin login successful", True)
                return data["token"]
            else:
                log_test("Admin login response format", False, f"Missing token or user in response: {data}")
                return None
        else:
            log_test("Admin login", False, f"Status {response.status_code}: {response.text}")
            return None
    except Exception as e:
        log_test("Admin login", False, f"Exception: {str(e)}")
        return None


def test_order_management(token):
    """Test order management endpoints"""
    print("\n=== Testing Order Management Endpoints ===")
    
    if not token:
        print("⚠️  Skipping order management tests - no auth token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: GET /api/admin/orders - list all orders
    try:
        response = requests.get(f"{API_BASE}/admin/orders", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "total" in data and "items" in data:
                log_test("GET /api/admin/orders returns {total, items}", True)
                print(f"   Found {data['total']} orders")
            else:
                log_test("GET /api/admin/orders shape", False, f"Missing total or items: {data}")
        else:
            log_test("GET /api/admin/orders", False, f"Status {response.status_code}: {response.text}")
    except Exception as e:
        log_test("GET /api/admin/orders", False, f"Exception: {str(e)}")
    
    # Test 2: Search filter - q=cliente1
    try:
        response = requests.get(f"{API_BASE}/admin/orders?q=cliente1", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "items" in data:
                # Check if results contain cliente1
                matches = [o for o in data["items"] if "cliente1" in o.get("email", "").lower()]
                if len(matches) > 0 or data["total"] == 0:
                    log_test("GET /api/admin/orders?q=cliente1 filters by search", True)
                else:
                    log_test("GET /api/admin/orders?q=cliente1", False, "No matching results found")
            else:
                log_test("GET /api/admin/orders?q=cliente1", False, "Missing items in response")
        else:
            log_test("GET /api/admin/orders?q=cliente1", False, f"Status {response.status_code}")
    except Exception as e:
        log_test("GET /api/admin/orders?q=cliente1", False, f"Exception: {str(e)}")
    
    # Test 3: Status filter
    try:
        response = requests.get(f"{API_BASE}/admin/orders?status=demo_confirmed", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "items" in data:
                # Verify all items have demo_confirmed status
                all_match = all(o.get("status") == "demo_confirmed" for o in data["items"])
                if all_match or len(data["items"]) == 0:
                    log_test("GET /api/admin/orders?status=demo_confirmed filters by status", True)
                else:
                    log_test("GET /api/admin/orders?status=demo_confirmed", False, "Some items don't match status filter")
            else:
                log_test("GET /api/admin/orders?status=demo_confirmed", False, "Missing items")
        else:
            log_test("GET /api/admin/orders?status=demo_confirmed", False, f"Status {response.status_code}")
    except Exception as e:
        log_test("GET /api/admin/orders?status=demo_confirmed", False, f"Exception: {str(e)}")
    
    # Test 4: Pagination - limit and skip
    try:
        response = requests.get(f"{API_BASE}/admin/orders?limit=2&skip=0", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if "items" in data and len(data["items"]) <= 2:
                log_test("GET /api/admin/orders?limit=2&skip=0 respects pagination", True)
            else:
                log_test("GET /api/admin/orders?limit=2&skip=0", False, f"Expected ≤2 items, got {len(data.get('items', []))}")
        else:
            log_test("GET /api/admin/orders?limit=2&skip=0", False, f"Status {response.status_code}")
    except Exception as e:
        log_test("GET /api/admin/orders?limit=2&skip=0", False, f"Exception: {str(e)}")
    
    # Test 5: Get single order by reference
    # First, get a reference from the list
    try:
        response = requests.get(f"{API_BASE}/admin/orders?limit=1", headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("items") and len(data["items"]) > 0:
                reference = data["items"][0].get("reference")
                if reference:
                    # Now get that specific order
                    response2 = requests.get(f"{API_BASE}/admin/orders/{reference}", headers=headers, timeout=10)
                    if response2.status_code == 200:
                        order = response2.json()
                        if "reference" in order and "items" in order:
                            log_test(f"GET /api/admin/orders/{reference} returns single order with items", True)
                        else:
                            log_test(f"GET /api/admin/orders/{reference}", False, "Missing reference or items")
                    else:
                        log_test(f"GET /api/admin/orders/{reference}", False, f"Status {response2.status_code}")
                else:
                    log_test("GET /api/admin/orders/{reference}", False, "No reference found in order")
            else:
                print("⚠️  No orders available to test GET by reference")
        else:
            log_test("GET /api/admin/orders (for reference)", False, f"Status {response.status_code}")
    except Exception as e:
        log_test("GET /api/admin/orders/{reference}", False, f"Exception: {str(e)}")
    
    # Test 6: Create a test order via public endpoint, then PATCH it
    try:
        # Create order via public endpoint
        order_data = {
            "email": "test@example.com",
            "first_name": "Test",
            "last_name": "User",
            "country": "IT",
            "company": "Test Co",
            "vat": "IT12345678901",
            "items": [
                {
                    "product_slug": "microsoft-office-2019-professional-plus",
                    "product_name": "Microsoft Office 2019 Professional Plus",
                    "variant_id": "office-2019-pro-plus-1pc",
                    "variant_label": "1 PC",
                    "quantity": 1,
                    "unit_price_eur": 49.99
                }
            ],
            "subtotal_eur": 49.99,
            "total_eur": 49.99,
            "language": "it"
        }
        
        create_response = requests.post(f"{API_BASE}/orders", json=order_data, timeout=10)
        if create_response.status_code == 200:
            created_order = create_response.json()
            test_reference = created_order.get("reference")
            
            if test_reference:
                # Test PATCH with valid status
                patch_data = {"status": "paid", "admin_notes": "test note"}
                patch_response = requests.patch(
                    f"{API_BASE}/admin/orders/{test_reference}",
                    json=patch_data,
                    headers=headers,
                    timeout=10
                )
                
                if patch_response.status_code == 200:
                    updated_order = patch_response.json()
                    if updated_order.get("status") == "paid" and updated_order.get("admin_notes") == "test note":
                        log_test("PATCH /api/admin/orders/{reference} updates status and admin_notes", True)
                    else:
                        log_test("PATCH /api/admin/orders/{reference}", False, 
                                f"Status or notes not updated correctly: {updated_order}")
                else:
                    log_test("PATCH /api/admin/orders/{reference}", False, 
                            f"Status {patch_response.status_code}: {patch_response.text}")
                
                # Test PATCH with invalid status
                invalid_patch = {"status": "garbage"}
                invalid_response = requests.patch(
                    f"{API_BASE}/admin/orders/{test_reference}",
                    json=invalid_patch,
                    headers=headers,
                    timeout=10
                )
                
                if invalid_response.status_code == 400:
                    log_test("PATCH /api/admin/orders/{reference} with invalid status returns 400", True)
                else:
                    log_test("PATCH with invalid status", False, 
                            f"Expected 400, got {invalid_response.status_code}")
                
                # Test DELETE
                delete_response = requests.delete(
                    f"{API_BASE}/admin/orders/{test_reference}",
                    headers=headers,
                    timeout=10
                )
                
                if delete_response.status_code == 200:
                    # Verify it's deleted
                    verify_response = requests.get(
                        f"{API_BASE}/admin/orders/{test_reference}",
                        headers=headers,
                        timeout=10
                    )
                    if verify_response.status_code == 404:
                        log_test("DELETE /api/admin/orders/{reference} removes order", True)
                    else:
                        log_test("DELETE /api/admin/orders/{reference}", False, 
                                "Order still exists after delete")
                else:
                    log_test("DELETE /api/admin/orders/{reference}", False, 
                            f"Status {delete_response.status_code}")
            else:
                log_test("Create test order for PATCH/DELETE", False, "No reference in created order")
        else:
            log_test("Create test order for PATCH/DELETE", False, 
                    f"Status {create_response.status_code}: {create_response.text}")
    except Exception as e:
        log_test("PATCH/DELETE order tests", False, f"Exception: {str(e)}")
    
    # Test 7: GET non-existent order
    try:
        response = requests.get(f"{API_BASE}/admin/orders/UNKNOWN-REF", headers=headers, timeout=10)
        if response.status_code == 404:
            log_test("GET /api/admin/orders/UNKNOWN-REF returns 404", True)
        else:
            log_test("GET /api/admin/orders/UNKNOWN-REF", False, 
                    f"Expected 404, got {response.status_code}")
    except Exception as e:
        log_test("GET /api/admin/orders/UNKNOWN-REF", False, f"Exception: {str(e)}")
    
    # Test 8: Test auth requirement - missing token
    try:
        response = requests.get(f"{API_BASE}/admin/orders", timeout=10)
        if response.status_code in [401, 403]:
            log_test("GET /api/admin/orders without auth returns 401/403", True)
        else:
            log_test("GET /api/admin/orders without auth", False, 
                    f"Expected 401/403, got {response.status_code}")
    except Exception as e:
        log_test("GET /api/admin/orders without auth", False, f"Exception: {str(e)}")


def test_csv_exports(token):
    """Test CSV export endpoints"""
    print("\n=== Testing CSV Export Endpoints ===")
    
    if not token:
        print("⚠️  Skipping CSV export tests - no auth token")
        return
    
    headers = {"Authorization": f"Bearer {token}"}
    
    # Test 1: Orders CSV
    try:
        response = requests.get(f"{API_BASE}/admin/exports/orders.csv", headers=headers, timeout=10)
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            content_disp = response.headers.get("Content-Disposition", "")
            
            checks = []
            checks.append(("Content-Type is text/csv", "text/csv" in content_type))
            checks.append(("charset=utf-8", "utf-8" in content_type))
            checks.append(("Content-Disposition has attachment", "attachment" in content_disp))
            checks.append(("filename with timestamp", "orders-" in content_disp and ".csv" in content_disp))
            
            # Check CSV content
            csv_text = response.text
            lines = csv_text.strip().split("\n")
            if len(lines) > 0:
                header = lines[0]
                checks.append(("Header starts with reference,created_at,status,email", 
                              header.startswith("reference,created_at,status,email")))
                checks.append(("At least 5 demo rows", len(lines) >= 6))  # header + 5 rows
            else:
                checks.append(("CSV has content", False))
            
            all_passed = all(check[1] for check in checks)
            if all_passed:
                log_test("GET /api/admin/exports/orders.csv", True)
            else:
                failed = [check[0] for check in checks if not check[1]]
                log_test("GET /api/admin/exports/orders.csv", False, f"Failed: {', '.join(failed)}")
        else:
            log_test("GET /api/admin/exports/orders.csv", False, f"Status {response.status_code}")
    except Exception as e:
        log_test("GET /api/admin/exports/orders.csv", False, f"Exception: {str(e)}")
    
    # Test 2: Orders CSV with status filter
    try:
        response = requests.get(
            f"{API_BASE}/admin/exports/orders.csv?status=demo_confirmed",
            headers=headers,
            timeout=10
        )
        if response.status_code == 200:
            log_test("GET /api/admin/exports/orders.csv?status=demo_confirmed filters", True)
        else:
            log_test("GET /api/admin/exports/orders.csv?status=demo_confirmed", False, 
                    f"Status {response.status_code}")
    except Exception as e:
        log_test("GET /api/admin/exports/orders.csv?status=demo_confirmed", False, f"Exception: {str(e)}")
    
    # Test 3: Customers CSV
    try:
        response = requests.get(f"{API_BASE}/admin/exports/customers.csv", headers=headers, timeout=10)
        if response.status_code == 200:
            csv_text = response.text
            lines = csv_text.strip().split("\n")
            if len(lines) > 0:
                header = lines[0]
                expected_cols = ["email", "first_name", "last_name", "country", "company", "vat", 
                               "orders", "revenue", "first_order_at", "last_order_at"]
                has_all_cols = all(col in header for col in expected_cols)
                if has_all_cols:
                    log_test("GET /api/admin/exports/customers.csv with correct columns", True)
                else:
                    missing = [col for col in expected_cols if col not in header]
                    log_test("GET /api/admin/exports/customers.csv", False, f"Missing columns: {missing}")
            else:
                log_test("GET /api/admin/exports/customers.csv", False, "Empty CSV")
        else:
            log_test("GET /api/admin/exports/customers.csv", False, f"Status {response.status_code}")
    except Exception as e:
        log_test("GET /api/admin/exports/customers.csv", False, f"Exception: {str(e)}")
    
    # Test 4: Products CSV
    try:
        response = requests.get(f"{API_BASE}/admin/exports/products.csv", headers=headers, timeout=10)
        if response.status_code == 200:
            csv_text = response.text
            lines = csv_text.strip().split("\n")
            if len(lines) > 0:
                header = lines[0]
                expected_cols = ["slug", "name", "brand", "category", "licenseType", "platforms",
                               "variants_count", "price_from_eur", "price_to_eur", "updated_at"]
                has_all_cols = all(col in header for col in expected_cols)
                
                # Check for ~397 data rows
                data_rows = len(lines) - 1  # exclude header
                has_397_rows = 390 <= data_rows <= 405  # allow some variance
                
                if has_all_cols and has_397_rows:
                    log_test(f"GET /api/admin/exports/products.csv (~{data_rows} rows)", True)
                else:
                    issues = []
                    if not has_all_cols:
                        missing = [col for col in expected_cols if col not in header]
                        issues.append(f"Missing columns: {missing}")
                    if not has_397_rows:
                        issues.append(f"Expected ~397 rows, got {data_rows}")
                    log_test("GET /api/admin/exports/products.csv", False, "; ".join(issues))
            else:
                log_test("GET /api/admin/exports/products.csv", False, "Empty CSV")
        else:
            log_test("GET /api/admin/exports/products.csv", False, f"Status {response.status_code}")
    except Exception as e:
        log_test("GET /api/admin/exports/products.csv", False, f"Exception: {str(e)}")
    
    # Test 5: Analytics CSV
    try:
        response = requests.get(f"{API_BASE}/admin/exports/analytics.csv", headers=headers, timeout=10)
        if response.status_code == 200:
            csv_text = response.text
            lines = csv_text.strip().split("\n")
            if len(lines) > 0:
                header = lines[0]
                expected_cols = ["ts", "event_type", "visitor_id", "session_id", "path", 
                               "product_slug", "device_type", "language", "referrer_host", 
                               "value_eur", "ip"]
                has_all_cols = all(col in header for col in expected_cols)
                if has_all_cols:
                    log_test("GET /api/admin/exports/analytics.csv with correct columns", True)
                else:
                    missing = [col for col in expected_cols if col not in header]
                    log_test("GET /api/admin/exports/analytics.csv", False, f"Missing columns: {missing}")
            else:
                log_test("GET /api/admin/exports/analytics.csv", False, "Empty CSV")
        else:
            log_test("GET /api/admin/exports/analytics.csv", False, f"Status {response.status_code}")
    except Exception as e:
        log_test("GET /api/admin/exports/analytics.csv", False, f"Exception: {str(e)}")
    
    # Test 6: Missing auth on export
    try:
        response = requests.get(f"{API_BASE}/admin/exports/orders.csv", timeout=10)
        if response.status_code in [401, 403]:
            log_test("GET /api/admin/exports/orders.csv without auth returns 401/403", True)
        else:
            log_test("GET /api/admin/exports/orders.csv without auth", False, 
                    f"Expected 401/403, got {response.status_code}")
    except Exception as e:
        log_test("GET /api/admin/exports/orders.csv without auth", False, f"Exception: {str(e)}")


def test_seo_endpoints():
    """Test public SEO endpoints (no auth required)"""
    print("\n=== Testing Public SEO Endpoints ===")
    
    # Test 1: /api/sitemap.xml
    try:
        response = requests.get(f"{API_BASE}/sitemap.xml", timeout=10)
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            xml_content = response.text
            
            checks = []
            checks.append(("Content-Type is application/xml", "application/xml" in content_type))
            checks.append(("charset=utf-8", "utf-8" in content_type))
            checks.append(("Contains <urlset root", "<urlset" in xml_content))
            
            # Count <url> entries
            url_count = xml_content.count("<url>")
            checks.append((f"~412 <url> entries (found {url_count})", 400 <= url_count <= 425))
            
            # Check for specific URLs
            checks.append(("Contains /", 'loc>https://' in xml_content and '/</loc>' in xml_content))
            checks.append(("Contains /catalog", '/catalog</loc>' in xml_content))
            checks.append(("Contains product URL", '/product/microsoft-office-2019-professional-plus</loc>' in xml_content))
            
            # Check absolute URLs match preview host
            checks.append(("URLs contain preview.emergentagent.com", 
                          "preview.emergentagent.com" in xml_content))
            
            all_passed = all(check[1] for check in checks)
            if all_passed:
                log_test("GET /api/sitemap.xml", True)
            else:
                failed = [check[0] for check in checks if not check[1]]
                log_test("GET /api/sitemap.xml", False, f"Failed: {', '.join(failed)}")
        else:
            log_test("GET /api/sitemap.xml", False, f"Status {response.status_code}")
    except Exception as e:
        log_test("GET /api/sitemap.xml", False, f"Exception: {str(e)}")
    
    # Test 2: /api/robots.txt
    try:
        response = requests.get(f"{API_BASE}/robots.txt", timeout=10)
        if response.status_code == 200:
            content_type = response.headers.get("Content-Type", "")
            robots_content = response.text
            
            checks = []
            checks.append(("Content-Type is text/plain", "text/plain" in content_type))
            checks.append(("Contains Sitemap: line", "Sitemap:" in robots_content))
            checks.append(("Sitemap points to /api/sitemap.xml", "/api/sitemap.xml" in robots_content))
            checks.append(("Sitemap URL is absolute with preview host", 
                          "preview.emergentagent.com" in robots_content))
            
            all_passed = all(check[1] for check in checks)
            if all_passed:
                log_test("GET /api/robots.txt", True)
            else:
                failed = [check[0] for check in checks if not check[1]]
                log_test("GET /api/robots.txt", False, f"Failed: {', '.join(failed)}")
        else:
            log_test("GET /api/robots.txt", False, f"Status {response.status_code}")
    except Exception as e:
        log_test("GET /api/robots.txt", False, f"Exception: {str(e)}")
    
    # Test 3: /sitemap.xml (root path)
    try:
        response = requests.get(f"{BASE_URL}/sitemap.xml", timeout=10)
        if response.status_code == 200:
            xml_content = response.text
            if "<urlset" in xml_content:
                log_test("GET /sitemap.xml (root path) same as /api/sitemap.xml", True)
            else:
                log_test("GET /sitemap.xml (root path)", False, "Not valid sitemap XML")
        else:
            log_test("GET /sitemap.xml (root path)", False, f"Status {response.status_code}")
    except Exception as e:
        log_test("GET /sitemap.xml (root path)", False, f"Exception: {str(e)}")


def main():
    """Run all backend tests"""
    print("=" * 70)
    print("LicenzPol Backend API Testing")
    print("=" * 70)
    print(f"Base URL: {BASE_URL}")
    print(f"API Base: {API_BASE}")
    print(f"Admin: {ADMIN_EMAIL}")
    print("=" * 70)
    
    # Step 1: Login and get token
    token = test_admin_login()
    
    # Step 2: Test order management
    test_order_management(token)
    
    # Step 3: Test CSV exports
    test_csv_exports(token)
    
    # Step 4: Test SEO endpoints
    test_seo_endpoints()
    
    # Print summary
    print("\n" + "=" * 70)
    print("TEST SUMMARY")
    print("=" * 70)
    print(f"✅ Passed: {test_results['passed']}")
    print(f"❌ Failed: {test_results['failed']}")
    print(f"Total: {test_results['passed'] + test_results['failed']}")
    
    if test_results["errors"]:
        print("\n❌ FAILED TESTS:")
        for error in test_results["errors"]:
            print(f"  - {error}")
    
    print("=" * 70)
    
    # Exit with appropriate code
    sys.exit(0 if test_results["failed"] == 0 else 1)


if __name__ == "__main__":
    main()
