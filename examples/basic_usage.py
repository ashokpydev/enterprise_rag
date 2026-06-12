"""
Example: Query the Enterprise RAG Platform
"""

import requests
import json

BASE_URL = "http://localhost:8000"
API_URL = f"{BASE_URL}/api/v1"

# Headers (required for multi-tenant isolation)
HEADERS = {
    "X-Tenant-ID": "enterprise-x",
    "X-User-ID": "user-123",
    "Content-Type": "application/json"
}

# ==================== Example 1: Simple Query ====================
print("=" * 60)
print("Example 1: Executing a RAG Query")
print("=" * 60)

query_payload = {
    "query": "What is the company's Q4 revenue forecast?",
    "top_k": 5,
    "temperature": 0.7,
    "include_trace": True
}

print(f"\n📤 Request:")
print(json.dumps(query_payload, indent=2))

response = requests.post(
    f"{API_URL}/query",
    json=query_payload,
    headers=HEADERS
)

print(f"\n✅ Response (Status: {response.status_code}):")
result = response.json()
print(json.dumps({
    "query_id": result["query_id"],
    "response": result["response"][:100] + "...",
    "retrieved_documents": len(result["retrieved_documents"]),
    "metrics": result["metrics"]
}, indent=2))

# ==================== Example 2: Upload Document ====================
print("\n" + "=" * 60)
print("Example 2: Uploading a Document")
print("=" * 60)

print("\n📤 Uploading test document...")

with open("test_document.txt", "wb") as f:
    f.write(b"""
    Q4 Financial Forecast
    
    Revenue Projection:
    - Enterprise segment: $12.5M (↑ 15% YoY)
    - Mid-market segment: $8.2M (↑ 8% YoY)
    - SMB segment: $4.1M (↑ 5% YoY)
    
    Total Q4 Revenue: $24.8M
    Gross Margin: 72%
    """)

files = {"file": ("test_document.txt", open("test_document.txt", "rb"), "text/plain")}

response = requests.post(
    f"{API_URL}/documents/upload",
    files=files,
    headers=HEADERS
)

print(f"\n✅ Response (Status: {response.status_code}):")
print(json.dumps(response.json(), indent=2))

# ==================== Example 3: A/B Testing ====================
print("\n" + "=" * 60)
print("Example 3: A/B Testing - Variant Comparison")
print("=" * 60)

# Variant A query
print("\n📤 Testing Variant A (512 token chunks)...")
response_a = requests.post(
    f"{API_URL}/query?ab_variant=variant_a",
    json={"query": "What is our revenue forecast?"},
    headers=HEADERS
)
metrics_a = response_a.json()["metrics"]

# Variant B query
print("📤 Testing Variant B (1024 token chunks)...")
response_b = requests.post(
    f"{API_URL}/query?ab_variant=variant_b",
    json={"query": "What is our revenue forecast?"},
    headers=HEADERS
)
metrics_b = response_b.json()["metrics"]

print("\n✅ A/B Test Results:")
comparison = {
    "metric": ["Latency (ms)", "Tokens", "Cost ($)", "Variant"],
    "Variant A": [
        metrics_a["total_latency_ms"],
        metrics_a["total_tokens"],
        metrics_a["cost_usd"],
        "variant_a"
    ],
    "Variant B": [
        metrics_b["total_latency_ms"],
        metrics_b["total_tokens"],
        metrics_b["cost_usd"],
        "variant_b"
    ]
}
for metric, val_a, val_b in zip(comparison["metric"], 
                                 comparison["Variant A"], 
                                 comparison["Variant B"]):
    print(f"  {metric:20} A: {val_a:10.2f}    B: {val_b:10.2f}")

# ==================== Example 4: Dashboard Metrics ====================
print("\n" + "=" * 60)
print("Example 4: Viewing Dashboard Metrics")
print("=" * 60)

print("\n📊 Fetching dashboard overview...")
response = requests.get(
    f"{API_URL}/dashboard/overview?days=7",
    headers=HEADERS
)

print(f"\n✅ Dashboard Metrics:")
dashboard = response.json()
print(json.dumps(dashboard["kpis"], indent=2))

# ==================== Example 5: Cost Tracking ====================
print("\n" + "=" * 60)
print("Example 5: Cost Tracking & Billing")
print("=" * 60)

print("\n💰 Fetching cost breakdown...")
response = requests.get(
    f"{API_URL}/dashboard/cost-tracking?days=30",
    headers=HEADERS
)

cost_data = response.json()
print(f"\n✅ Monthly Cost Summary:")
print(f"  Total Cost: ${cost_data['total_cost_usd']:.2f}")
print(f"  By Model:")
for model, data in cost_data["by_model"].items():
    print(f"    - {model}: ${data.get('cost_usd', 0):.2f}")

# ==================== Example 6: Anomaly Detection ====================
print("\n" + "=" * 60)
print("Example 6: System Anomalies")
print("=" * 60)

print("\n🚨 Checking for anomalies...")
response = requests.get(
    f"{API_URL}/dashboard/anomalies",
    headers=HEADERS
)

anomalies = response.json()
if anomalies["anomalies"]:
    print(f"\n⚠️  Detected {len(anomalies['anomalies'])} anomalies:")
    for anomaly in anomalies["anomalies"]:
        print(f"  [{anomaly['severity'].upper()}] {anomaly['message']}")
else:
    print("\n✅ No anomalies detected")

print("\n" + "=" * 60)
print("Examples complete!")
print("=" * 60)
