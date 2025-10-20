"""
Test script to verify all three Cloudflare endpoints are working
Author: Srivardhan S - 3122225001704
"""

from etl_connector import CloudflareETLConnector
import sys

def test_mongodb_connection():
    """Test MongoDB connectivity"""
    print("\n" + "="*60)
    print("Testing MongoDB Connection...")
    print("="*60)
    
    connector = CloudflareETLConnector()
    if connector.connect_mongodb():
        print("✅ MongoDB connection successful!")
        return True
    else:
        print("❌ MongoDB connection failed!")
        return False

def test_trace_endpoint():
    """Test Cloudflare Trace API"""
    print("\n" + "="*60)
    print("Testing Endpoint 1: Cloudflare Trace API...")
    print("="*60)
    
    connector = CloudflareETLConnector()
    data = connector.extract_trace_data()
    
    if data and len(data) > 0:
        print(f"✅ Trace API working! Retrieved {len(data)} fields")
        print(f"   Sample data: IP={data.get('ip')}, Location={data.get('loc')}")
        return True
    else:
        print("❌ Trace API failed!")
        return False

def test_doh_endpoint():
    """Test Cloudflare DNS over HTTPS"""
    print("\n" + "="*60)
    print("Testing Endpoint 2: Cloudflare DNS over HTTPS...")
    print("="*60)
    
    connector = CloudflareETLConnector()
    data = connector.extract_doh_data(['google.com'])
    
    if data and len(data) > 0:
        print(f"✅ DoH API working! Retrieved DNS data for {len(data)} domain(s)")
        if data[0].get('Answer'):
            print(f"   Sample: {data[0].get('queried_domain')} -> {data[0]['Answer'][0].get('data')}")
        return True
    else:
        print("❌ DoH API failed!")
        return False

def test_speed_endpoint():
    """Test Cloudflare Speed Test"""
    print("\n" + "="*60)
    print("Testing Endpoint 3: Cloudflare Speed Test...")
    print("="*60)
    
    connector = CloudflareETLConnector()
    data = connector.extract_speed_data(test_iterations=1)
    
    if data and len(data) > 0:
        print(f"✅ Speed Test API working!")
        print(f"   Speed: {data[0].get('speed_mbps')} Mbps")
        return True
    else:
        print("❌ Speed Test API failed!")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("Cloudflare Multi-Endpoint ETL - Testing Suite")
    print("Author: Srivardhan S - 3122225001704")
    print("="*60)
    
    results = []
    
    # Test MongoDB
    results.append(("MongoDB Connection", test_mongodb_connection()))
    
    # Test all three endpoints
    results.append(("Trace API", test_trace_endpoint()))
    results.append(("DoH API", test_doh_endpoint()))
    results.append(("Speed Test API", test_speed_endpoint()))
    
    # Summary
    print("\n" + "="*60)
    print("Test Summary")
    print("="*60)
    
    for name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{name:.<40} {status}")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print("\n" + "="*60)
    print(f"Results: {passed}/{total} tests passed")
    print("="*60)
    
    if passed == total:
        print("\n🎉 All tests passed! Ready to run full ETL pipeline.")
        print("   Run: python etl_connector.py")
        sys.exit(0)
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()