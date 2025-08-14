# NVD CVE Feed ETL Connector

**Author:** Srivardhan S - 3122225001704  
**Course:** Software Architecture - SSN CSE B
**Institution:** Kyureeus EdTech Program

## 📋 Project Overview

This ETL (Extract, Transform, Load) connector integrates with the National Vulnerability Database (NVD) CVE Feed API to extract Common Vulnerabilities and Exposures (CVE) data, transform it for analysis, and load it into a MongoDB database for further processing and analysis.

## 🎯 API Provider Details

### **NVD CVE Feed API**
- **Base URL:** `https://services.nvd.nist.gov/rest/json/cves/2.0`
- **Provider:** National Institute of Standards and Technology (NIST)
- **Authentication:** Optional API key (recommended for higher rate limits)
- **Data Format:** JSON
- **Rate Limits:** 
  - Without API Key: 5 requests per 30 seconds
  - With API Key: 50 requests per 30 seconds

### **API Endpoints Used**
- **Primary Endpoint:** `/rest/json/cves/2.0`
- **Method:** GET
- **Parameters:**
  - `resultsPerPage`: Number of results per page (max 2000)
  - `startIndex`: Starting index for pagination
  - `pubStartDate`: Publication start date (ISO format)
  - `pubEndDate`: Publication end date (ISO format)
  - `modStartDate`: Modification start date (ISO format)
  - `modEndDate`: Modification end date (ISO format)

## 🏗️ ETL Pipeline Architecture

### **Extract Phase**
- Connects to NVD CVE API with proper authentication
- Handles pagination automatically
- Implements rate limiting and retry logic
- Fetches CVE data based on date ranges
- Manages API errors and timeouts

### **Transform Phase**
- Cleans and structures CVE data
- Extracts key fields (CVE ID, descriptions, CVSS scores, etc.)
- Adds ETL metadata (ingestion timestamp, version, source)
- Normalizes data for MongoDB compatibility
- Preserves original data for audit purposes

### **Load Phase**
- Stores data in MongoDB using upsert operations
- Prevents duplicate entries using CVE ID as unique identifier
- Maintains data lineage and audit trail
- Implements bulk operations for efficiency

## 🚀 Installation & Setup

### **Prerequisites**
- Python 3.8 or higher
- MongoDB (local or cloud instance)
- Git

### **Installation Steps**

1. **Clone the repository:**
```bash
git clone <repository-url>
cd SSN-college-software-architecture-Assignments
git checkout <your-branch-name>
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Setup environment variables:**
```bash
cp .env.example .env
# Edit .env file with your configuration
```

4. **Configure MongoDB:**
   - Install MongoDB locally or use MongoDB Atlas
   - Update `MONGODB_URI` in `.env` file

5. **Optional: Get NVD API Key:**
   - Visit: https://nvd.nist.gov/developers/request-an-api-key
   - Add your API key to `.env` file

## ⚙️ Configuration

### **Environment Variables (.env)**
```bash
# NVD API Configuration
NVD_API_KEY=your_api_key_here  # Optional but recommended

# MongoDB Configuration
MONGODB_URI=mongodb://localhost:27017/
MONGODB_DATABASE=etl_data
```

### **MongoDB Collection Strategy**
- **Collection Name:** `nvd_cve_raw`
- **Database:** Configurable via environment variable
- **Document Structure:**
  - `_id`: CVE identifier (e.g., CVE-2024-1234)
  - `cve_id`: CVE identifier
  - `description`: Primary English description
  - `cvss_v31_score`: CVSS v3.1 base score
  - `published`: Publication date
  - `last_modified`: Last modification date
  - `ingestion_timestamp`: ETL processing timestamp
  - `raw_data`: Original API response (for audit)

## 📖 Usage Examples

### **Basic Usage**
```bash
# Run ETL pipeline with default settings (last 7 days)
python etl_connector.py
```

### **Programmatic Usage**
```python
from etl_connector import NVDCVEConnector

# Initialize connector
connector = NVDCVEConnector()

# Run ETL for specific date range
success = connector.run_etl_pipeline(
    start_date='2024-01-01T00:00:00.000',
    end_date='2024-01-31T23:59:59.999'
)

# Clean up
connector.close()
```

### **Custom Date Range**
```python
# Extract CVEs from last month
from datetime import datetime, timedelta

end_date = datetime.now()
start_date = end_date - timedelta(days=30)

connector = NVDCVEConnector()
connector.run_etl_pipeline(
    start_date=start_date.isoformat(),
    end_date=end_date.isoformat()
)
```

## 📊 Example Output

### **Sample CVE Document in MongoDB**
```json
{
  "_id": "CVE-2024-1234",
  "cve_id": "CVE-2024-1234",
  "source_identifier": "cve@mitre.org",
  "published": "2024-02-15T10:30:00.000",
  "last_modified": "2024-02-16T08:15:00.000",
  "vuln_status": "Analyzed",
  "description": "A critical vulnerability in...",
  "cvss_v31_score": 9.8,
  "cvss_v31_severity": "CRITICAL",
  "ingestion_timestamp": "2024-02-20T12:00:00.000Z",
  "etl_version": "1.0",
  "source_api": "NVD CVE Feed",
  "references": [...],
  "metrics": {...},
  "raw_data": {...}
}
```

### **Pipeline Execution Log**
```
2024-02-20 12:00:00 - INFO - Starting NVD CVE ETL Pipeline
2024-02-20 12:00:01 - INFO - Connected to MongoDB: etl_data.nvd_cve_raw
2024-02-20 12:00:02 - INFO - Extracting CVE data from 2024-02-13T12:00:00 to 2024-02-20T12:00:00
2024-02-20 12:00:05 - INFO - Extracted 150 CVEs (total: 150)
2024-02-20 12:00:06 - INFO - Transformed 150 CVE records
2024-02-20 12:00:08 - INFO - Loaded data to MongoDB: Inserted: 145, Modified: 5
2024-02-20 12:00:09 - INFO - Total documents in collection: 1250
2024-02-20 12:00:09 - INFO - ETL Pipeline completed successfully!
```

## 🧪 Testing & Validation

### **Built-in Validation**
- Connection testing for MongoDB and NVD API
- Data structure validation
- Duplicate prevention
- Error handling and retry logic
- Rate limit compliance

### **Manual Testing**
```bash
# Test MongoDB connection
python -c "from etl_connector import NVDCVEConnector; c = NVDCVEConnector(); print('Connected successfully')"

# Test API connectivity
python -c "from etl_connector import NVDCVEConnector; c = NVDCVEConnector(); print('API accessible')"
```

## 🔧 Error Handling

The connector includes comprehensive error handling for:
- **Network Issues:** Timeout, connection errors, DNS resolution
- **API Errors:** Rate limiting, invalid responses, server errors
- **Data Issues:** Malformed JSON, missing fields, invalid dates
- **Database Issues:** Connection failures, write errors, validation errors

## 📝 Logging

Logs are written to both console and `etl_connector.log` file with the following information:
- Execution timestamps
- API request/response details
- Data transformation statistics
- MongoDB operation results
- Error details and stack traces

## 🔒 Security Best Practices

- ✅ API credentials stored in environment variables
- ✅ `.env` file excluded from git commits
- ✅ Input validation and sanitization
- ✅ Secure MongoDB connection handling
- ✅ No hardcoded secrets in source code

## 📋 Project Structure
```
/your-branch-name/
├── etl_connector.py      # Main ETL script
├── .env                  # Environment variables (not committed)
├── .env.example          # Environment template
├── requirements.txt      # Python dependencies
├── README.md            # This documentation
├── etl_connector.log    # Application logs (generated)
└── .gitignore           # Git ignore patterns
```

## 🚨 Troubleshooting

### **Common Issues**

1. **Rate Limiting**
   - Symptom: HTTP 429 errors
   - Solution: Ensure proper delays between requests, consider getting API key

2. **MongoDB Connection Failed**
   - Symptom: ConnectionFailure exception
   - Solution: Check MongoDB service, verify URI in `.env`

3. **No Data Retrieved**
   - Symptom: Empty extraction results
   - Solution: Check date ranges, verify API connectivity

4. **API Key Issues**
   - Symptom: Authentication errors
   - Solution: Verify API key validity, check rate limits

## 📚 Additional Resources

- [NVD API Documentation](https://nvd.nist.gov/developers)
- [MongoDB Python Driver Documentation](https://pymongo.readthedocs.io/)
- [Python Requests Documentation](https://requests.readthedocs.io/)
- [CVE Details Reference](https://cve.mitre.org/)

## 🤝 Support

For questions or issues:
- Post in the KYUREEUS/SSN College WhatsApp group
- Check API documentation for endpoint-specific issues
- Review logs for detailed error information

## 📄 License

This project is part of the SSN CSE Software Architecture course assignment under the Kyureeus EdTech program.

---

**Note:** Remember to add your `.env` file to `.gitignore` before committing and never commit sensitive credentials to the repository.
