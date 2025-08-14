import os
import sys
import time
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import requests
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure, BulkWriteError
from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_connector.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class NVDCVEConnector:
    
    def __init__(self):
        self.base_url = "https://services.nvd.nist.gov/rest/json/cves/2.0"
        self.api_key = os.getenv('NVD_API_KEY')
        self.mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.mongo_db = os.getenv('MONGODB_DATABASE', 'etl_data')
        self.collection_name = 'nvd_cve_raw'
        
        self.rate_limit_delay = 6 if not self.api_key else 0.6
        self.max_retries = 3
        self.timeout = 30
        
        self.mongo_client = None
        self.db = None
        self.collection = None
        
        self._setup_mongodb()
    
    def _setup_mongodb(self):
        try:
            self.mongo_client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            self.mongo_client.admin.command('ping')
            self.db = self.mongo_client[self.mongo_db]
            self.collection = self.db[self.collection_name]
            logger.info(f"Connected to MongoDB: {self.mongo_db}.{self.collection_name}")
        except ConnectionFailure as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise
    
    def _get_headers(self) -> Dict[str, str]:
        headers = {
            'User-Agent': 'ETL-Connector-SSN-CSE/1.0',
            'Accept': 'application/json'
        }
        
        if self.api_key:
            headers['apiKey'] = self.api_key
            logger.info("Using API key for authentication")
        else:
            logger.info("Using public access (no API key)")
            
        return headers
    
    def extract_data(self, start_date: Optional[str] = None, 
                    end_date: Optional[str] = None, 
                    results_per_page: int = 100) -> List[Dict[str, Any]]:
        all_cves = []
        start_index = 0
        
        if not start_date:
            start_date = (datetime.now() - timedelta(days=7)).isoformat()
        if not end_date:
            end_date = datetime.now().isoformat()
        
        logger.info(f"Extracting CVE data from {start_date} to {end_date}")
        
        while True:
            params = {
                'resultsPerPage': results_per_page,
                'startIndex': start_index,
                'pubStartDate': start_date,
                'pubEndDate': end_date
            }
            
            try:
                response = self._make_request(params)
                
                if not response:
                    break
                
                vulnerabilities = response.get('vulnerabilities', [])
                if not vulnerabilities:
                    logger.info("No more vulnerabilities to fetch")
                    break
                
                all_cves.extend(vulnerabilities)
                logger.info(f"Extracted {len(vulnerabilities)} CVEs (total: {len(all_cves)})")
                
                total_results = response.get('totalResults', 0)
                if start_index + results_per_page >= total_results:
                    break
                
                start_index += results_per_page
                
                time.sleep(self.rate_limit_delay)
                
            except Exception as e:
                logger.error(f"Error during extraction: {e}")
                break
        
        logger.info(f"Total CVEs extracted: {len(all_cves)}")
        return all_cves
    
    def _make_request(self, params: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        headers = self._get_headers()
        
        for attempt in range(self.max_retries):
            try:
                logger.debug(f"Making request (attempt {attempt + 1}): {params}")
                response = requests.get(
                    self.base_url,
                    params=params,
                    headers=headers,
                    timeout=self.timeout
                )
                
                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 429:
                    logger.warning("Rate limited, waiting longer...")
                    time.sleep(self.rate_limit_delay * 2)
                    continue
                else:
                    logger.error(f"HTTP Error {response.status_code}: {response.text}")
                    return None
                    
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt + 1}): {e}")
                if attempt == self.max_retries - 1:
                    raise
                time.sleep(2 ** attempt)
        
        return None
    
    def transform_data(self, cves: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        transformed = []
        
        for cve_item in cves:
            try:
                cve = cve_item.get('cve', {})
                
                transformed_record = {
                    '_id': cve.get('id'),
                    'cve_id': cve.get('id'),
                    'source_identifier': cve.get('sourceIdentifier'),
                    'published': cve.get('published'),
                    'last_modified': cve.get('lastModified'),
                    'vuln_status': cve.get('vulnStatus'),
                    'descriptions': cve.get('descriptions', []),
                    'references': cve.get('references', []),
                    'metrics': cve.get('metrics', {}),
                    'weaknesses': cve.get('weaknesses', []),
                    'configurations': cve.get('configurations', []),
                    'vendor_comments': cve.get('vendorComments', []),
                    
                    'ingestion_timestamp': datetime.utcnow(),
                    'etl_version': '1.0',
                    'source_api': 'NVD CVE Feed',
                    'raw_data': cve_item
                }
                
                if 'cvssMetricV31' in transformed_record['metrics']:
                    cvss_v31 = transformed_record['metrics']['cvssMetricV31']
                    if cvss_v31:
                        transformed_record['cvss_v31_score'] = cvss_v31[0].get('cvssData', {}).get('baseScore')
                        transformed_record['cvss_v31_severity'] = cvss_v31[0].get('cvssData', {}).get('baseSeverity')
                
                descriptions = transformed_record.get('descriptions', [])
                english_desc = next((d for d in descriptions if d.get('lang') == 'en'), {})
                transformed_record['description'] = english_desc.get('value', 'No description available')
                
                transformed.append(transformed_record)
                
            except Exception as e:
                logger.error(f"Error transforming CVE record: {e}")
                continue
        
        logger.info(f"Transformed {len(transformed)} CVE records")
        return transformed
    
    def load_data(self, transformed_data: List[Dict[str, Any]]) -> bool:
        if not transformed_data:
            logger.warning("No data to load")
            return True
        
        try:
            operations = []
            for record in transformed_data:
                operations.append({
                    'replaceOne': {
                        'filter': {'_id': record['_id']},
                        'replacement': record,
                        'upsert': True
                    }
                })
            
            result = self.collection.bulk_write(operations, ordered=False)
            
            logger.info(f"Loaded data to MongoDB:")
            logger.info(f"  - Inserted: {result.upserted_count}")
            logger.info(f"  - Modified: {result.modified_count}")
            logger.info(f"  - Matched: {result.matched_count}")
            
            return True
            
        except BulkWriteError as e:
            logger.error(f"Bulk write error: {e.details}")
            return False
        except Exception as e:
            logger.error(f"Error loading data to MongoDB: {e}")
            return False
    
    def validate_data(self) -> bool:
        try:
            count = self.collection.count_documents({})
            logger.info(f"Total documents in collection: {count}")
            
            recent_count = self.collection.count_documents({
                'ingestion_timestamp': {
                    '$gte': datetime.utcnow() - timedelta(hours=1)
                }
            })
            logger.info(f"Documents ingested in last hour: {recent_count}")
            
            sample = self.collection.find_one()
            if sample:
                logger.info(f"Sample document structure validated: {list(sample.keys())}")
            
            return True
            
        except Exception as e:
            logger.error(f"Validation error: {e}")
            return False
    
    def run_etl_pipeline(self, start_date: Optional[str] = None, 
                        end_date: Optional[str] = None) -> bool:
        logger.info("Starting NVD CVE ETL Pipeline")
        
        try:
            logger.info("Step 1: Extracting data from NVD API")
            raw_data = self.extract_data(start_date, end_date)
            
            if not raw_data:
                logger.warning("No data extracted, pipeline completed")
                return True
            
            logger.info("Step 2: Transforming data")
            transformed_data = self.transform_data(raw_data)
            
            logger.info("Step 3: Loading data to MongoDB")
            load_success = self.load_data(transformed_data)
            
            if not load_success:
                logger.error("Failed to load data")
                return False
            
            logger.info("Step 4: Validating loaded data")
            validation_success = self.validate_data()
            
            if validation_success:
                logger.info("ETL Pipeline completed successfully!")
                return True
            else:
                logger.error("Data validation failed")
                return False
                
        except Exception as e:
            logger.error(f"ETL Pipeline failed: {e}")
            return False
        
        finally:
            if self.mongo_client:
                self.mongo_client.close()
    
    def close(self):
        if self.mongo_client:
            self.mongo_client.close()
            logger.info("MongoDB connection closed")


def main():
    try:
        connector = NVDCVEConnector()
        
        success = connector.run_etl_pipeline()
        
        if success:
            logger.info("ETL process completed successfully")
            sys.exit(0)
        else:
            logger.error("ETL process failed")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()