# Cloudflare Multi-Endpoint ETL Connector

**Author:** Srivardhan S - 3122225001704  
**Course:** Software Architecture Assignment 2 - SSN CSE B  
**Institution:** Kyureeus EdTech Program

---

## 📋 Project Overview

This ETL (Extract, Transform, Load) connector integrates with **THREE different Cloudflare public API endpoints** to extract diverse network and infrastructure data, transform it for analysis, and load it into MongoDB database for monitoring, analysis, and insights.

Unlike traditional single-endpoint ETL systems, this implementation demonstrates a comprehensive multi-source data integration strategy from a unified provider (Cloudflare), showcasing advanced data engineering capabilities.

---

## 🎯 API Provider Details

### Provider: Cloudflare
- **Company:** Cloudflare, Inc.
- **Service Type:** CDN, DNS, Network Services, Security
- **Data Format:** Text, JSON, Binary
- **Authentication:** Not required (Public APIs)
- **Rate Limits:** Fair use policy (reasonable request intervals)
- **Availability:** 99.9%+ uptime

---

## 🔗 Three API Endpoints Used

### **Endpoint 1: Cloudflare Trace API**

**Base URL:** `https://1.1.1.1/cdn-cgi/trace`

**Purpose:** Provides connection and request metadata including IP address, geographic location, TLS version, and HTTP protocol information.

**Method:** GET

**Response Format:** Text (key-value pairs)

**Rate Limits:** No explicit limit (fair use expected)

**Data Returned:**
- Client IP address
- Request timestamp
- Cloudflare data center (colo)
- Geographic location code
- TLS version
- HTTP version
- User agent
- Visit scheme (http/https)
- WARP status
- Gateway status

**Example Request:**
```bash
curl https://1.1.1.1/cdn-cgi/trace
```

**Example Response:**
```
fl=151f16
h=1.1.1.1
ip=203.192.241.46
ts=1729425600.123
visit_scheme=https
uag=Mozilla/5.0
colo=BLR
http=h2
loc=IN
tls=TLSv1.3
sni=plaintext
warp=off
gateway=off
```

---

### **Endpoint 2: Cloudflare DNS over HTTPS (DoH)**

**Base URL:** `https://cloudflare-dns.com/dns-query`

**Purpose:** Provides DNS query resolution over HTTPS with detailed DNS record information including answer records, TTL values, and response codes.

**Method:** GET

**Response Format:** JSON (RFC 8427 compliant)

**Rate Limits:** Fair use policy (implemented 0.5s delay between queries)

**Parameters:**
- `name`: Domain name to query (required)
- `type`: DNS record type (A, AAAA, CNAME, MX, TXT, etc.)

**Headers Required:**
```
Accept: application/dns-json
```

**Data Returned:**
- DNS query status
- Answer records with IP addresses
- Record TTL (Time To Live)
- DNS response codes
- Query flags (RD, RA, AD, CD)
- Authority and additional sections

**Example Request:**
```bash
curl "https://cloudflare-dns.com/dns-query?name=google.com&type=A" \
  -H "Accept: application/dns-json"
```

**Example Response:**
```json
{
  "Status": 0,
  "TC": false,
  "RD": true,
  "RA": true,
  "AD": false,
  "CD": false,
  "Question": [
    {
      "name": "google.com",
      "type": 1
    }
  ],
  "Answer": [
    {
      "name": "google.com",
      "type": 1,
      "TTL": 300,
      "data": "142.250.193.46"
    }
  ]
}
```

---

### **Endpoint 3: Cloudflare Speed Test API**

**Base URL:** `https://speed.cloudflare.com/__down`

**Purpose:** Provides network performance measurement by downloading test data to calculate connection speed, latency, and throughput metrics.

**Method:** GET

**Response Format:** Binary data (test payload)

**Rate Limits:** Fair use policy (implemented 1s delay between tests)

**Data Calculated:**
- Download speed (Mbps)
- Data transfer size (bytes)
- Elapsed time (seconds)
- Connection latency
- Throughput metrics

**Example Request:**
```bash
curl https://speed.cloudflare.com/__down
```

**Speed Calculation:**
```
Speed (Mbps) = (Data Size in bytes × 8) / (Elapsed Time in seconds × 1,000,000)
```

---

## 🏗️ ETL Pipeline Architecture

### **Extract Phase**

Three independent extractors handle different data sources:

#### 1. Trace Extractor
- Connects to Cloudflare Trace API
- Fetches current connection metadata
- Parses text-based key-value response format
- Single-request operation (no pagination)
- Implements retry logic for network failures

#### 2. DoH Extractor
- Queries DNS for multiple domains (default: 5)
- Sends parallel requests with rate limiting
- Handles JSON response parsing
- Implements 0.5-second delay between queries
- Supports custom domain lists
- Collects comprehensive DNS records

#### 3. Speed Test Extractor
- Performs multiple speed test iterations (default: 3)
- Downloads binary test data
- Measures elapsed time with high precision
- Calculates real-time download speeds
- Implements 1-second delay between tests
- Handles network timeouts gracefully

### **Transform Phase**

Three specialized transformers process different data types:

#### 1. Trace Transformer
- Converts text format to structured JSON
- Extracts and normalizes key fields
- Adds ETL metadata (timestamp, version, source)
- Generates unique document identifier
- Preserves raw data for audit trail

#### 2. DoH Transformer
- Parses nested DNS Answer records
- Normalizes DNS status codes to readable format
- Structures multi-level JSON data
- Converts DNS type numbers to descriptions
- Handles missing or optional fields
- Maintains data relationships

#### 3. Speed Test Transformer
- Aggregates multiple test iterations
- Calculates statistical measures:
  - Average speed (mean)
  - Minimum speed
  - Maximum speed
  - Speed variance
- Preserves individual test results
- Adds performance metadata

### **Load Phase**

Three MongoDB collections with optimized schemas:

#### Collection 1: `cloudflare_trace_raw`
- **Purpose:** Connection and request metadata
- **Index:** ingestion_timestamp (ascending)
- **Document ID:** `trace_{timestamp}`
- **Average Size:** ~1KB per document

#### Collection 2: `cloudflare_doh_raw`
- **Purpose:** DNS query results and records
- **Index:** query_name (ascending)
- **Document ID:** `dns_{domain}_{timestamp}`
- **Average Size:** ~2KB per document

#### Collection 3: `cloudflare_speed_raw`
- **Purpose:** Network performance metrics
- **Index:** ingestion_timestamp (ascending)
- **Document ID:** `speed_{timestamp}`
- **Average Size:** ~3KB per document

---

## 🚀 Installation & Setup

### **Prerequisites**

- Python 3.8 or higher
- MongoDB 4.4 or higher (local or MongoDB Atlas)
- Git for version control
- Active internet connection
- Terminal/Command prompt access

### **Installation Steps**

#### Step 1: Clone the Repository

```bash
# Clone the main repository
git clone <repository-url>
cd SSN-college-software-architecture-Assignments

# Switch to your assignment branch
git checkout Srivardhan-S-3122225001704-cloudflare
```

#### Step 2: Install Python Dependencies

```bash
# Install required packages
pip install -r requirements.txt

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

#### Step 3: Setup Environment Variables

```bash
# Copy environment template
cp .env.example .env

# Edit .env file with your configuration
# For most cases, default values work perfectly
nano .env  # or use any text editor
```

#### Step 4: Configure MongoDB

**Option A: Local MongoDB**
```bash
# Start MongoDB service
mongod

# Verify it's running
mongosh
```

**Option B: MongoDB Atlas (Cloud)**
1. Create free account at [MongoDB Atlas](https://www.mongodb.com/cloud/atlas)
2. Create a cluster
3. Get connection string
4. Update `MONGODB_URI` in `.env` file

#### Step 5: Verify Installation

```bash
# Test MongoDB connection
python -c "from etl_connector import CloudflareETLConnector; c = CloudflareETLConnector(); print('Connected!' if c.connect_mongodb() else 'Failed!')"

# Run test suite
python test_endpoints.py
```

---

## ⚙️ Configuration

### **Environment Variables (.env)**

```bash
# ============================================
# MongoDB Configuration
# ============================================
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=etl_data

# For MongoDB Atlas, use:
# MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/

# ============================================
# Cloudflare API Endpoints
# ============================================
CLOUDFLARE_TRACE_URL=https://1.1.1.1/cdn-cgi/trace
CLOUDFLARE_DOH_URL=https://cloudflare-dns.com/dns-query
CLOUDFLARE_SPEED_URL=https://speed.cloudflare.com/__down

# ============================================
# Request Configuration
# ============================================
REQUEST_TIMEOUT=10        # Timeout in seconds
RETRY_ATTEMPTS=3         # Number of retry attempts
RETRY_DELAY=2            # Delay between retries (seconds)
```

### **MongoDB Collection Strategy**

| Collection Name | Purpose | Primary Index | Document Structure |
|----------------|---------|---------------|-------------------|
| `cloudflare_trace_raw` | Connection metadata | `ingestion_timestamp` | Flat structure with trace fields |
| `cloudflare_doh_raw` | DNS query results | `query_name` | Nested structure with answer arrays |
| `cloudflare_speed_raw` | Speed test metrics | `ingestion_timestamp` | Aggregated with individual tests |

### **Collection Indexes**

```javascript
// Trace collection
db.cloudflare_trace_raw.createIndex({ "ingestion_timestamp": 1 });

// DoH collection
db.cloudflare_doh_raw.createIndex({ "query_name": 1 });
db.cloudflare_doh_raw.createIndex({ "ingestion_timestamp": 1 });

// Speed collection
db.cloudflare_speed_raw.createIndex({ "ingestion_timestamp": 1 });
db.cloudflare_speed_raw.createIndex({ "average_speed_mbps": 1 });
```

---

## 📖 Usage Examples

### **Basic Usage**

Run the complete ETL pipeline with default settings:

```bash
python etl_connector.py
```

**Default Behavior:**
- Extracts trace data (1 request)
- Queries DNS for 5 domains (google.com, github.com, cloudflare.com, amazon.com, microsoft.com)
- Runs 3 speed test iterations
- Loads data into MongoDB

---

### **Programmatic Usage**

#### Example 1: Basic Pipeline Execution

```python
from etl_connector import CloudflareETLConnector

# Initialize connector
connector = CloudflareETLConnector()

# Run complete pipeline
success = connector.run_etl_pipeline()

if success:
    print("✅ Pipeline completed successfully!")
else:
    print("❌ Pipeline failed!")

# Always close connection
connector.close()
```

#### Example 2: Custom Configuration

```python
from etl_connector import CloudflareETLConnector

connector = CloudflareETLConnector()

# Run with custom settings
success = connector.run_etl_pipeline(
    include_trace=True,
    include_doh=True,
    include_speed=True,
    dns_domains=['facebook.com', 'twitter.com', 'linkedin.com'],
    speed_iterations=5
)

connector.close()
```

#### Example 3: Selective Endpoint Execution

```python
from etl_connector import CloudflareETLConnector

connector = CloudflareETLConnector()

# Run only Trace and DoH (skip Speed Test)
connector.run_etl_pipeline(
    include_trace=True,
    include_doh=True,
    include_speed=False,
    dns_domains=['google.com', 'github.com']
)

connector.close()
```

#### Example 4: Individual Endpoint Testing

```python
from etl_connector import CloudflareETLConnector

connector = CloudflareETLConnector()
connector.connect_mongodb()

# Test Trace API only
trace_data = connector.extract_trace_data()
if trace_data:
    transformed = connector.transform_trace_data(trace_data)
    connector.load_trace_data(transformed)
    print("✅ Trace API working!")

connector.close()
```

#### Example 5: Continuous Monitoring

```python
from etl_connector import CloudflareETLConnector
import time

connector = CloudflareETLConnector()

# Run every 5 minutes
while True:
    print("\n--- Starting new ETL cycle ---")
    connector.run_etl_pipeline()
    print("Waiting 5 minutes for next cycle...")
    time.sleep(300)  # 5 minutes
```

---

## 📊 Example Output

### **Sample Documents in MongoDB**

#### 1. Trace Document (cloudflare_trace_raw)

```json
{
  "_id": "trace_2024-10-20T12:00:00.000Z",
  "ip_address": "203.192.241.46",
  "timestamp": "1729425600.123",
  "visit_scheme": "https",
  "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
  "colo": "BLR",
  "http_version": "h2",
  "location": "IN",
  "tls_version": "TLSv1.3",
  "sni": "plaintext",
  "warp": "off",
  "gateway": "off",
  "ingestion_timestamp": "2024-10-20T12:00:00.000Z",
  "etl_version": "2.0",
  "source_api": "Cloudflare Trace",
  "raw_data": {
    "fl": "151f16",
    "h": "1.1.1.1",
    "ip": "203.192.241.46",
    "ts": "1729425600.123",
    "visit_scheme": "https",
    "uag": "Mozilla/5.0",
    "colo": "BLR",
    "http": "h2",
    "loc": "IN",
    "tls": "TLSv1.3",
    "sni": "plaintext",
    "warp": "off",
    "gateway": "off"
  }
}
```

#### 2. DoH Document (cloudflare_doh_raw)

```json
{
  "_id": "dns_google.com_2024-10-20T12:00:01.500Z",
  "query_name": "google.com",
  "query_type": 1,
  "status": 0,
  "response_code": "NOERROR",
  "answers": [
    {
      "name": "google.com",
      "type": 1,
      "ttl": 300,
      "data": "142.250.193.46"
    },
    {
      "name": "google.com",
      "type": 1,
      "ttl": 300,
      "data": "142.250.193.78"
    }
  ],
  "answer_count": 2,
  "truncated": false,
  "recursion_desired": true,
  "recursion_available": true,
  "authenticated_data": false,
  "ingestion_timestamp": "2024-10-20T12:00:01.500Z",
  "etl_version": "2.0",
  "source_api": "Cloudflare DoH",
  "raw_data": {
    "Status": 0,
    "TC": false,
    "RD": true,
    "RA": true,
    "AD": false,
    "CD": false,
    "Question": [
      {
        "name": "google.com",
        "type": 1
      }
    ],
    "Answer": [
      {
        "name": "google.com",
        "type": 1,
        "TTL": 300,
        "data": "142.250.193.46"
      }
    ],
    "queried_domain": "google.com"
  }
}
```

#### 3. Speed Test Document (cloudflare_speed_raw)

```json
{
  "_id": "speed_2024-10-20T12:00:10.000Z",
  "test_timestamp": "2024-10-20T12:00:10.000Z",
  "test_count": 3,
  "average_speed_mbps": 47.25,
  "min_speed_mbps": 44.82,
  "max_speed_mbps": 50.13,
  "speed_variance": 5.31,
  "individual_tests": [
    {
      "iteration": 1,
      "timestamp": "2024-10-20T12:00:05.000Z",
      "data_size_bytes": 1048576,
      "elapsed_time_seconds": 0.177,
      "speed_mbps": 47.39,
      "status_code": 200
    },
    {
      "iteration": 2,
      "timestamp": "2024-10-20T12:00:07.000Z",
      "data_size_bytes": 1048576,
      "elapsed_time_seconds": 0.187,
      "speed_mbps": 44.82,
      "status_code": 200
    },
    {
      "iteration": 3,
      "timestamp": "2024-10-20T12:00:09.000Z",
      "data_size_bytes": 1048576,
      "elapsed_time_seconds": 0.167,
      "speed_mbps": 50.13,
      "status_code": 200
    }
  ],
  "ingestion_timestamp": "2024-10-20T12:00:10.000Z",
  "etl_version": "2.0",
  "source_api": "Cloudflare Speed Test",
  "raw_data": [...]
}
```

---

### **Pipeline Execution Log**

```
================================================================================
Cloudflare Multi-Endpoint ETL Connector
Author: Srivardhan S - 3122225001704
================================================================================

================================================================================
Starting Cloudflare Multi-Endpoint ETL Pipeline
================================================================================
2024-10-20 12:00:00 - INFO - Cloudflare Multi-Endpoint ETL Connector initialized
2024-10-20 12:00:00 - INFO - Connected to MongoDB: etl_data

--- Processing Endpoint 1: Trace API ---
2024-10-20 12:00:01 - INFO - Extracting data from Cloudflare Trace API...
2024-10-20 12:00:01 - INFO - Successfully extracted trace data with 11 fields
2024-10-20 12:00:01 - INFO - Transforming trace data...
2024-10-20 12:00:01 - INFO - Trace data transformed successfully
2024-10-20 12:00:01 - INFO - Trace data loaded to MongoDB: trace_2024-10-20T12:00:01.000Z

--- Processing Endpoint 2: DNS over HTTPS ---
2024-10-20 12:00:02 - INFO - Extracting DNS data for 5 domains...
2024-10-20 12:00:02 - INFO - Retrieved DNS data for google.com
2024-10-20 12:00:03 - INFO - Retrieved DNS data for github.com
2024-10-20 12:00:04 - INFO - Retrieved DNS data for cloudflare.com
2024-10-20 12:00:05 - INFO - Retrieved DNS data for amazon.com
2024-10-20 12:00:06 - INFO - Retrieved DNS data for microsoft.com
2024-10-20 12:00:06 - INFO - Successfully extracted DNS data for 5 domains
2024-10-20 12:00:06 - INFO - Transforming 5 DNS records...
2024-10-20 12:00:06 - INFO - Transformed 5 DNS records
2024-10-20 12:00:07 - INFO - DNS data loaded to MongoDB: 5 records

--- Processing Endpoint 3: Speed Test ---
2024-10-20 12:00:07 - INFO - Running 3 speed test iterations...
2024-10-20 12:00:08 - INFO - Speed test 1: 47.39 Mbps
2024-10-20 12:00:10 - INFO - Speed test 2: 44.82 Mbps
2024-10-20 12:00:12 - INFO - Speed test 3: 50.13 Mbps
2024-10-20 12:00:12 - INFO - Completed 3 speed tests
2024-10-20 12:00:12 - INFO - Transforming 3 speed test results...
2024-10-20 12:00:12 - INFO - Speed test data transformed successfully
2024-10-20 12:00:13 - INFO - Speed test data loaded to MongoDB: speed_2024-10-20T12:00:12.000Z

================================================================================
2024-10-20 12:00:13 - INFO - ETL Pipeline completed successfully!

Collection Statistics:
  - cloudflare_trace_raw: 1 documents
  - cloudflare_doh_raw: 5 documents
  - cloudflare_speed_raw: 1 documents
================================================================================

✅ ETL Pipeline executed successfully!
📊 Check MongoDB for processed data in:
   - cloudflare_trace_raw
   - cloudflare_doh_raw
   - cloudflare_speed_raw
```

---

## 🧪 Testing & Validation

### **Built-in Validation Features**

✅ **Connection Testing**
- MongoDB connectivity verification
- API endpoint availability checks
- Network connectivity validation

✅ **Data Structure Validation**
- JSON schema validation
- Required field verification
- Data type checking

✅ **Error Handling**
- Automatic retry with exponential backoff
- Graceful degradation
- Comprehensive exception handling

✅ **Rate Limit Compliance**
- Configurable delays between requests
- Fair use policy adherence
- Request throttling

✅ **Duplicate Prevention**
- Unique document IDs
- Timestamp-based identification
- Collision avoidance

---

### **Manual Testing**

#### Test 1: MongoDB Connection

```bash
python -c "from etl_connector import CloudflareETLConnector; c = CloudflareETLConnector(); result = c.connect_mongodb(); print('✅ Connected' if result else '❌ Failed')"
```

#### Test 2: Run Test Suite

```bash
python test_endpoints.py
```

**Expected Output:**
```
============================================================
Cloudflare Multi-Endpoint ETL - Testing Suite
Author: Srivardhan S - 3122225001704
============================================================

============================================================
Testing MongoDB Connection...
============================================================
✅ MongoDB connection successful!

============================================================
Testing Endpoint 1: Cloudflare Trace API...
============================================================
✅ Trace API working! Retrieved 11 fields
   Sample data: IP=203.192.241.46, Location=IN

============================================================
Testing Endpoint 2: Cloudflare DNS over HTTPS...
============================================================
✅ DoH API working! Retrieved DNS data for 1 domain(s)
   Sample: google.com -> 142.250.193.46

============================================================
Testing Endpoint 3: Cloudflare Speed Test...
============================================================
✅ Speed Test API working!
   Speed: 47.25 Mbps

============================================================
Test Summary
============================================================
MongoDB Connection......................... ✅ PASSED
Trace API.................................. ✅ PASSED
DoH API.................................... ✅ PASSED
Speed Test API............................. ✅ PASSED

============================================================
Results: 4/4 tests passed
============================================================

🎉 All tests passed! Ready to run full ETL pipeline.
   Run: python etl_connector.py
```

#### Test 3: Verify Data in MongoDB

```python
from pymongo import MongoClient

client = MongoClient('mongodb://localhost:27017/')
db = client['etl_data']

# Check document counts
print("="*60)
print("MongoDB Data Verification")
print("="*60)
print(f"Trace documents:  {db.cloudflare_trace_raw.count_documents({})}")
print(f"DoH documents:    {db.cloudflare_doh_raw.count_documents({})}")
print(f"Speed documents:  {db.cloudflare_speed_raw.count_documents({})}")
print("="*60)

# View sample documents
print("\n📄 Sample Trace Document:")
trace_doc = db.cloudflare_trace_raw.find_one()
if trace_doc:
    print(f"   IP: {trace_doc.get('ip_address')}")
    print(f"   Location: {trace_doc.get('location')}")
    print(f"   TLS: {trace_doc.get('tls_version')}")

print("\n📄 Sample DoH Document:")
doh_doc = db.cloudflare_doh_raw.find_one()
if doh_doc:
    print(f"   Domain: {doh_doc.get('query_name')}")
    print(f"   Status: {doh_doc.get('response_code')}")
    print(f"   Answers: {doh_doc.get('answer_count')}")

print("\n📄 Sample Speed Document:")
speed_doc = db.cloudflare_speed_raw.find_one()
if speed_doc:
    print(f"   Avg Speed: {speed_doc.get('average_speed_mbps')} Mbps")
    print(f"   Min Speed: {speed_doc.get('min_speed_mbps')} Mbps")
    print(f"   Max Speed: {speed_doc.get('max_speed_mbps')} Mbps")

print("\n✅ Verification complete!")
```

---

## 🔧 Error Handling

### **Network Issues**

**Handled:**
- Connection timeouts
- DNS resolution failures
- Network unreachable errors
- SSL/TLS handshake failures

**Recovery Strategy:**
```python
# Automatic retry with exponential backoff
for attempt in range(retry_attempts):
    try:
        response = requests.get(url, timeout=timeout)
        return response
    except Timeout:
        wait_time = retry_delay * (2 ** attempt)
        time.sleep(wait_time)
```

---

### **API Errors**

**Handled:**
- HTTP 429 (Rate Limited)
- HTTP 500 (Server Error)
- HTTP 503 (Service Unavailable)
- Invalid response formats
- Empty payloads

**Example Log:**
```
2024-10-20 12:00:05 - WARNING - Request failed with status 429: Rate limited
2024-10-20 12:00:05 - WARNING - Rate limited. Waiting 2 seconds...
2024-10-20 12:00:07 - INFO - Retry attempt 2/3
2024-10-20 12:00:08 - INFO - Request successful
```

---

### **Database Issues**

**Handled:**
- Connection failures
- Write errors
- Bulk write errors
- Duplicate key errors
- Validation errors

**Recovery Strategy:**
```python
try:
    collection.insert_one(document)
except DuplicateKeyError:
    logger.warning("Duplicate document, updating instead")
    collection.replace_one({"_id": document["_id"]}, document)
except ConnectionFailure:
    logger.error("MongoDB connection lost, reconnecting...")
    self.connect_mongodb()
```

---

### **Data Issues**

**Handled:**
- Missing fields
- Null values
- Invalid data types
- Parsing errors
- Encoding issues

**Example:**
```python
# Safe field extraction with defaults
ip_address = raw_data.get('ip', 'unknown')
timestamp = raw_data.get('ts', datetime.now().isoformat())
```

---

## 📝 Logging

### **Log Destinations**

1. **Console Output** (stdout) - Real-time monitoring
2. **etl_connector.log** - Persistent file storage

### **Log Levels**

| Level | Purpose | Example |
|-------|---------|---------|
| INFO | Normal operations | "Connected to MongoDB" |
| WARNING | Recoverable issues | "Rate limited, retrying..." |
| ERROR | Failed operations | "Failed to load data" |

### **Log Format**

```
YYYY-MM-DD HH:MM:SS - LEVEL - Message
```

### **Sample Log File (etl_connector.log)**

```
2024-10-20 12:00:00 - INFO - Cloudflare Multi-Endpoint ETL Connector initialized
2024-10-20 12:00:00 - INFO - Connected to MongoDB: etl_data
2024-10-20 12:00:01 - INFO - Extracting data from Cloudflare Trace API...
2024-10-20 12:00:01 - INFO - Successfully extracted trace data with 11 fields
2024-10-20 12:00:02 - INFO - Extracting DNS data for 5 domains...
2024-10-20 12:00:05 - WARNING - Rate limited. Waiting 2 seconds...
2024-10-20 12:00:07 - INFO - Successfully extracted DNS data for 5 domains
2024-10-20 12:00:12 - INFO - ETL Pipeline completed successfully!
```

---

## 🔒 Security Best Practices

### **Implemented Security Measures**

✅ **Environment Variables**
- All configuration in `.env` file
- No hardcoded credentials
- Secure loading with `python-dotenv`

✅ **Git Security**
- `.env` in `.gitignore`
- No committed secrets
- Template file (`.env.example`) provided

✅ **Network Security**
- HTTPS only for API calls
- TLS/SSL certificate verification
- Secure connection handling

✅ **Input Validation**
- User input sanitization
- Type checking
- Range validation

✅ **Error Messages**
- Sensitive info excluded from logs
- Generic error messages for users
- Detailed logs for debugging (not exposed)

### **Security Checklist**

```bash
# Verify .env is not staged
git status
# Should NOT show .env

# Check .gitignore
cat .gitignore | grep ".env"
# Should show: .env

# Verify no hardcoded secrets
grep -r "password" --exclude=".env" --exclude="README.md"
# Should return no results
```

---

## 📋 Project Structure

```
/Srivardhan-S-3122225001704-cloudflare/
│
├── etl_connector.py          # Main ETL script
│   ├── CloudflareETLConnector class
│   ├── Trace API methods
│   ├── DoH API methods
│   ├── Speed Test API methods
│   └── Main pipeline orchestration
│
├── test_endpoints.py         # Testing suite
│   ├── MongoDB connection test
│   ├── Individual endpoint tests
│   └── Summary report
│
├── requirements.txt          # Python dependencies
│   ├── requests==2.31.0
│   ├── pymongo==4.6.1
│   └── python-dotenv==1.0.0
│
├── .env                      # Environment variables (NOT COMMITTED)
│   ├── MongoDB URI
│   ├── API endpoints
│   └── Configuration
│
├── .env.example              # Environment template (COMMITTED)
│   └── Sample configuration
│
├── README.md                 # This documentation
│   ├── Project overview
│   ├── Installation guide
│   ├── Usage examples
│   └── Troubleshooting
│
├── .gitignore               # Git ignore patterns
│   ├── .env
│   ├── __pycache__/
│   ├── *.log
│   └── Virtual environment
│
└── etl_connector.log        # Application logs (auto-generated)
    └── Execution history
```

---

## 🚨 Troubleshooting

### **Issue 1: MongoDB Connection Failed**

**Symptom:**
```
ConnectionFailure: [Errno 111] Connection refused
```

**Solutions:**

1. **Check MongoDB Service:**
```bash
# Check if MongoDB is running
sudo systemctl status mongod

# Start MongoDB
sudo systemctl start mongod

# Enable auto-start
sudo systemctl enable mongod
```

2. **Verify Connection String:**
```bash
# Test connection
mongosh "mongodb://localhost:27017/"
```

3. **For MongoDB Atlas:**
- Check network access whitelist
- Verify username/password
- Ensure cluster is running

---

### **Issue 2: API Request Timeout**

**Symptom:**
```
Request timeout (attempt 1/3)
```

**Solutions:**

1. **Check Internet Connection:**
```bash
ping cloudflare.com
```

2. **Increase Timeout:**
```bash
# Edit .env file
REQUEST_TIMEOUT=20  # Increase from 10 to 20
```

3. **Test Endpoints Manually:**
```bash
curl https://1.1.1.1/cdn-cgi/trace
```

---

### **Issue 3: Rate Limiting**

**Symptom:**
```
WARNING - Rate limited. Waiting 2 seconds...
```

**Solutions:**

1. **Reduce Request Frequency:**
```python
# Increase delays in code
time.sleep(1.0)  # Instead of 0.5
```

2. **Reduce DNS Domains:**
```python
# Query fewer domains
dns_domains=['google.com', 'github.com']  # Instead of 5
```

3. **This is normal behavior** - the connector handles it automatically

---

### **Issue 4: Import Errors**

**Symptom:**
```
ModuleNotFoundError: No module named 'requests'
```

**Solutions:**

1. **Install Dependencies:**
```bash
pip install -r requirements.txt
```

2. **Use Virtual Environment:**
```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. **Verify Installation:**
```bash
pip list | grep requests
pip list | grep pymongo
pip list | grep python-dotenv
```

---

### **Issue 5: Empty Data Retrieved**

**Symptom:**
```
WARNING - No data extracted
```

**Solutions:**

1. **Check Internet:**
```bash
ping 1.1.1.1
```

2. **Test Endpoints:**
```bash
curl https://1.1.1.1/cdn-cgi/trace
curl "https://cloudflare-dns.com/dns-query?name=google.com&type=A" -H "Accept: application/dns-json"
```

3. **Check Firewall:**
```bash
# Ensure ports 80 and 443 are not blocked
```

---

### **Issue 6: Permission Errors**

**Symptom:**
```
PermissionError: [Errno 13] Permission denied: 'etl_connector.log'
```

**Solutions:**

```bash
# Fix file permissions
chmod 644 etl_connector.log

# Or remove and recreate
rm etl_connector.log
python etl_connector.py
```

---

## 📚 Additional Resources

### **Cloudflare Documentation**
- [Cloudflare Trace](https://www.cloudflare.com/cdn-cgi/trace) - Connection metadata
- [DNS over HTTPS](https://developers.cloudflare.com/1.1.1.1/encryption/dns-over-https/) - DoH API
- [Cloudflare Speed Test](https://speed.cloudflare.com/) - Performance testing
- [Cloudflare API Docs](https://developers.cloudflare.com/) - Complete API reference

### **Python Libraries**
- [Requests Documentation](https://requests.readthedocs.io/) - HTTP library
- [PyMongo Documentation](https://pymongo.readthedocs.io/) - MongoDB driver
- [Python-dotenv](https://pypi.org/project/python-dotenv/) - Environment variables

### **MongoDB**
- [MongoDB Manual](https://docs.mongodb.com/manual/) - Official documentation
- [MongoDB Atlas](https://www.mongodb.com/cloud/atlas) - Cloud database
- [MongoDB Python Tutorial](https://docs.mongodb.com/drivers/python/) - Python integration

### **DNS & Networking**
- [DNS Record Types](https://www.cloudflare.com/learning/dns/dns-records/) - Understanding DNS
- [DNS over HTTPS RFC](https://datatracker.ietf.org/doc/html/rfc8484) - DoH specification

---

## 🎓 Key Learning Outcomes

### **Technical Skills Demonstrated**

✅ **Multi-Source Data Integration**
- Connecting to three different API endpoints
- Handling diverse data formats (text, JSON, binary)
- Coordinated data extraction

✅ **ETL Pipeline Design**
- Modular extract, transform, load components
- Independent processing pipelines
- Unified orchestration

✅ **Data Engineering**
- Schema design for different data types
- Data normalization and transformation
- Statistical aggregation

✅ **Error Handling & Resilience**
- Automatic retry mechanisms
- Graceful degradation
- Comprehensive exception handling

✅ **Database Management**
- Collection strategy design
- Index optimization
- Bulk operations

✅ **Security Best Practices**
- Environment variable management
- Credential protection
- Secure coding practices

✅ **Code Quality**
- Clean, maintainable code
- Comprehensive documentation
- Proper logging and monitoring

---

## 🤝 Support

### **Getting Help**

1. **KYUREEUS/SSN College WhatsApp Group**
   - Post questions and screenshots
   - Quick responses from peers and instructors
   - Share solutions and tips

2. **Instructor Email**
   - Include your name and roll number
   - Attach relevant logs or error messages
   - Describe steps already attempted

3. **Documentation Resources**
   - Review this README
   - Check Cloudflare API documentation
   - Consult Python library docs

4. **Log Files**
   - Check `etl_connector.log` for detailed errors
   - Look for ERROR or WARNING messages
   - Include relevant log sections when asking for help

---

## ✅ Pre-Submission Checklist

Before submitting your Pull Request, verify:

### **Code Quality**
- [ ] All three endpoints are implemented
- [ ] Code runs without errors
- [ ] Proper error handling included
- [ ] Logging is comprehensive
- [ ] Code is well-commented

### **Testing**
- [ ] `test_endpoints.py` passes all tests
- [ ] MongoDB connection successful
- [ ] Data loaded into all three collections
- [ ] Sample documents verified

### **Security**
- [ ] `.env` is in `.gitignore`
- [ ] `.env` is NOT committed to Git
- [ ] No hardcoded credentials
- [ ] `.env.example` is provided

### **Documentation**
- [ ] README.md is complete
- [ ] All sections filled out
- [ ] Usage examples tested
- [ ] Troubleshooting section accurate

### **Git Workflow**
- [ ] Proper branch naming
- [ ] Commit messages include name and roll number
- [ ] No unnecessary files committed
- [ ] Pull Request description is clear

### **Final Verification**

```bash
# 1. Check Git status
git status
# Verify .env is NOT in "Changes to be committed"

# 2. Run tests
python test_endpoints.py
# Should show: 4/4 tests passed

# 3. Run full pipeline
python etl_connector.py
# Should complete successfully

# 4. Verify MongoDB
python -c "from pymongo import MongoClient; c = MongoClient('mongodb://localhost:27017/'); db = c['etl_data']; print('Trace:', db.cloudflare_trace_raw.count_documents({}), 'DoH:', db.cloudflare_doh_raw.count_documents({}), 'Speed:', db.cloudflare_speed_raw.count_documents({}))"
# Should show counts > 0

# 5. Check logs
tail -n 20 etl_connector.log
# Should show successful completion
```

---

## 📄 License

This project is part of the SSN CSE Software Architecture course assignment under the Kyureeus EdTech program.

---

## 👨‍💻 Author Information

**Name:** Srivardhan S  
**Roll Number:** 3122225001704  
**Department:** Computer Science and Engineering - B  
**Institution:** SSN College of Engineering  
**Program:** Kyureeus EdTech  
**Assignment:** Software Architecture Assignment 2  
**Submission Date:** October 2024

---

## 🏆 Assignment Highlights

### **Why This Implementation Stands Out**

1. **Three Distinct Endpoints** ✅
   - Trace API (connection metadata)
   - DoH API (DNS resolution)
   - Speed Test (performance metrics)

2. **Professional Code Quality** ✅
   - Clean, modular architecture
   - Comprehensive error handling
   - Extensive documentation

3. **Production-Ready Features** ✅
   - Retry logic with exponential backoff
   - Rate limiting compliance
   - Detailed logging

4. **Diverse Data Handling** ✅
   - Text parsing (key-value)
   - JSON processing (nested structures)
   - Binary data (speed tests)

5. **Complete Testing Suite** ✅
   - Automated endpoint testing
   - MongoDB verification
   - Integration testing

---

## 📊 Performance Metrics

### **Typical Execution Times**

| Operation | Duration |
|-----------|----------|
| MongoDB Connection | ~0.5 seconds |
| Trace API Call | ~0.3 seconds |
| DoH Query (per domain) | ~0.5 seconds |
| Speed Test (per iteration) | ~2-3 seconds |
| **Total Pipeline** | **~15-20 seconds** |

### **Data Volume**

| Collection | Documents per Run | Average Size |
|-----------|-------------------|--------------|
| cloudflare_trace_raw | 1 | ~1 KB |
| cloudflare_doh_raw | 5 (default) | ~2 KB each |
| cloudflare_speed_raw | 1 | ~3 KB |
| **Total** | **7 documents** | **~14 KB** |

---

## 🚀 Future Enhancements

Potential improvements for advanced students:

1. **Additional Endpoints**
   - Cloudflare Workers metrics
   - Radar API data
   - Zone analytics

2. **Advanced Features**
   - Scheduled execution (cron jobs)
   - Data visualization dashboard
   - Alerting system for anomalies

3. **Performance Optimization**
   - Parallel API requests
   - Caching mechanisms
   - Batch processing

4. **Extended Analytics**
   - Time-series analysis
   - Trend detection
   - Anomaly detection

---

**🎉 Congratulations on completing Assignment 2!**

This comprehensive ETL connector demonstrates advanced data engineering skills and is ready for submission. Good luck! 🚀

---

*Last Updated: October 20, 2024*  
*Version: 2.0*  
*Status: Ready for Submission ✅*
