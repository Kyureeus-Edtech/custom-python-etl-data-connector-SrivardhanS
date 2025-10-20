"""
Cloudflare Multi-Endpoint ETL Connector
Author: Srivardhan S - 3122225001704
Course: Software Architecture Assignment 2 - SSN CSE B
Institution: Kyureeus EdTech Program

This ETL connector extracts data from THREE Cloudflare endpoints:
1. Trace API - Connection information
2. DNS over HTTPS (DoH) - DNS query results  
3. Speed Test API - Network performance metrics
"""

import os
import sys
import time
import json
import logging
import requests
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING
from pymongo.errors import ConnectionFailure, BulkWriteError

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('etl_connector.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class CloudflareETLConnector:
    """
    ETL Connector for Cloudflare Multi-Endpoint Data Pipeline
    Handles Extract, Transform, and Load operations for three Cloudflare APIs
    """
    
    def __init__(self):
        """Initialize the ETL connector with configuration"""
        # MongoDB Configuration
        self.mongo_uri = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
        self.database_name = os.getenv('MONGODB_DATABASE', 'etl_data')
        
        # Cloudflare API Endpoints
        self.trace_url = os.getenv('CLOUDFLARE_TRACE_URL', 'https://1.1.1.1/cdn-cgi/trace')
        self.doh_url = os.getenv('CLOUDFLARE_DOH_URL', 'https://cloudflare-dns.com/dns-query')
        self.speed_test_url = os.getenv('CLOUDFLARE_SPEED_URL', 'https://speed.cloudflare.com/__down')
        
        # Collection names
        self.trace_collection = 'cloudflare_trace_raw'
        self.doh_collection = 'cloudflare_doh_raw'
        self.speed_collection = 'cloudflare_speed_raw'
        
        # Request configuration
        self.timeout = int(os.getenv('REQUEST_TIMEOUT', '10'))
        self.retry_attempts = int(os.getenv('RETRY_ATTEMPTS', '3'))
        self.retry_delay = int(os.getenv('RETRY_DELAY', '2'))
        
        # MongoDB client
        self.client = None
        self.db = None
        
        # ETL metadata
        self.etl_version = "2.0"
        self.source_provider = "Cloudflare"
        
        logger.info("Cloudflare Multi-Endpoint ETL Connector initialized")
    
    def connect_mongodb(self) -> bool:
        """
        Establish connection to MongoDB
        Returns: True if successful, False otherwise
        """
        try:
            self.client = MongoClient(self.mongo_uri, serverSelectionTimeoutMS=5000)
            self.client.admin.command('ping')
            self.db = self.client[self.database_name]
            
            # Create indexes for each collection
            self.db[self.trace_collection].create_index([("ingestion_timestamp", ASCENDING)])
            self.db[self.doh_collection].create_index([("query_name", ASCENDING)])
            self.db[self.speed_collection].create_index([("ingestion_timestamp", ASCENDING)])
            
            logger.info(f"Connected to MongoDB: {self.database_name}")
            return True
            
        except ConnectionFailure as e:
            logger.error(f"MongoDB connection failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error connecting to MongoDB: {e}")
            return False
    
    def make_request(self, url: str, params: Optional[Dict] = None, 
                    headers: Optional[Dict] = None, method: str = 'GET') -> Optional[requests.Response]:
        """
        Make HTTP request with retry logic
        
        Args:
            url: API endpoint URL
            params: Query parameters
            headers: Request headers
            method: HTTP method (GET/POST)
            
        Returns:
            Response object or None if failed
        """
        for attempt in range(self.retry_attempts):
            try:
                if method == 'GET':
                    response = requests.get(url, params=params, headers=headers, timeout=self.timeout)
                else:
                    response = requests.post(url, json=params, headers=headers, timeout=self.timeout)
                
                if response.status_code == 200:
                    return response
                elif response.status_code == 429:
                    logger.warning(f"Rate limited. Waiting {self.retry_delay} seconds...")
                    time.sleep(self.retry_delay)
                else:
                    logger.warning(f"Request failed with status {response.status_code}: {response.text}")
                    
            except requests.Timeout:
                logger.warning(f"Request timeout (attempt {attempt + 1}/{self.retry_attempts})")
            except requests.RequestException as e:
                logger.error(f"Request error: {e}")
            
            if attempt < self.retry_attempts - 1:
                time.sleep(self.retry_delay)
        
        return None
    
    # =================================================================================
    # ENDPOINT 1: CLOUDFLARE TRACE API
    # =================================================================================
    
    def extract_trace_data(self) -> Optional[Dict[str, Any]]:
        """
        Extract data from Cloudflare Trace API
        Returns connection/request information
        """
        logger.info("Extracting data from Cloudflare Trace API...")
        
        try:
            response = self.make_request(self.trace_url)
            
            if not response:
                logger.error("Failed to retrieve trace data")
                return None
            
            # Parse trace response (text format)
            trace_data = {}
            for line in response.text.strip().split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    trace_data[key.strip()] = value.strip()
            
            logger.info(f"Successfully extracted trace data with {len(trace_data)} fields")
            return trace_data
            
        except Exception as e:
            logger.error(f"Error extracting trace data: {e}")
            return None
    
    def transform_trace_data(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Transform Cloudflare Trace data for MongoDB
        
        Args:
            raw_data: Raw trace data from API
            
        Returns:
            Transformed document ready for MongoDB
        """
        logger.info("Transforming trace data...")
        
        current_time = datetime.now(timezone.utc).isoformat()
        
        transformed = {
            "_id": f"trace_{current_time}",
            "ip_address": raw_data.get('ip', 'unknown'),
            "timestamp": raw_data.get('ts', ''),
            "visit_scheme": raw_data.get('visit_scheme', ''),
            "user_agent": raw_data.get('uag', ''),
            "colo": raw_data.get('colo', ''),
            "http_version": raw_data.get('http', ''),
            "location": raw_data.get('loc', ''),
            "tls_version": raw_data.get('tls', ''),
            "sni": raw_data.get('sni', ''),
            "warp": raw_data.get('warp', 'off'),
            "gateway": raw_data.get('gateway', 'off'),
            "ingestion_timestamp": current_time,
            "etl_version": self.etl_version,
            "source_api": "Cloudflare Trace",
            "raw_data": raw_data
        }
        
        logger.info("Trace data transformed successfully")
        return transformed
    
    def load_trace_data(self, transformed_data: Dict[str, Any]) -> bool:
        """
        Load trace data into MongoDB
        
        Args:
            transformed_data: Transformed trace document
            
        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self.db[self.trace_collection]
            result = collection.insert_one(transformed_data)
            
            logger.info(f"Trace data loaded to MongoDB: {result.inserted_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading trace data: {e}")
            return False
    
    # =================================================================================
    # ENDPOINT 2: CLOUDFLARE DNS OVER HTTPS (DoH)
    # =================================================================================
    
    def extract_doh_data(self, domain_list: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """
        Extract DNS query results from Cloudflare DoH API
        
        Args:
            domain_list: List of domains to query (defaults to common domains)
            
        Returns:
            List of DNS query results
        """
        if domain_list is None:
            domain_list = ['google.com', 'github.com', 'cloudflare.com', 'amazon.com', 'microsoft.com']
        
        logger.info(f"Extracting DNS data for {len(domain_list)} domains...")
        
        dns_results = []
        headers = {'Accept': 'application/dns-json'}
        
        for domain in domain_list:
            try:
                params = {
                    'name': domain,
                    'type': 'A'
                }
                
                response = self.make_request(self.doh_url, params=params, headers=headers)
                
                if response:
                    data = response.json()
                    data['queried_domain'] = domain
                    dns_results.append(data)
                    logger.info(f"Retrieved DNS data for {domain}")
                
                time.sleep(0.5)  # Rate limiting
                
            except Exception as e:
                logger.error(f"Error querying DNS for {domain}: {e}")
        
        logger.info(f"Successfully extracted DNS data for {len(dns_results)} domains")
        return dns_results
    
    def transform_doh_data(self, raw_data_list: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Transform DNS query results for MongoDB
        
        Args:
            raw_data_list: List of raw DNS query results
            
        Returns:
            List of transformed documents
        """
        logger.info(f"Transforming {len(raw_data_list)} DNS records...")
        
        transformed_list = []
        current_time = datetime.now(timezone.utc).isoformat()
        
        for raw_data in raw_data_list:
            domain = raw_data.get('queried_domain', 'unknown')
            
            # Extract answer records
            answers = []
            for answer in raw_data.get('Answer', []):
                answers.append({
                    'name': answer.get('name', ''),
                    'type': answer.get('type', 0),
                    'ttl': answer.get('TTL', 0),
                    'data': answer.get('data', '')
                })
            
            transformed = {
                "_id": f"dns_{domain}_{current_time}",
                "query_name": domain,
                "query_type": raw_data.get('Question', [{}])[0].get('type', 1),
                "status": raw_data.get('Status', -1),
                "response_code": self._get_dns_response_code(raw_data.get('Status', -1)),
                "answers": answers,
                "answer_count": len(answers),
                "truncated": raw_data.get('TC', False),
                "recursion_desired": raw_data.get('RD', False),
                "recursion_available": raw_data.get('RA', False),
                "authenticated_data": raw_data.get('AD', False),
                "ingestion_timestamp": current_time,
                "etl_version": self.etl_version,
                "source_api": "Cloudflare DoH",
                "raw_data": raw_data
            }
            
            transformed_list.append(transformed)
        
        logger.info(f"Transformed {len(transformed_list)} DNS records")
        return transformed_list
    
    def _get_dns_response_code(self, status: int) -> str:
        """Helper to convert DNS status code to readable string"""
        codes = {
            0: 'NOERROR',
            1: 'FORMERR',
            2: 'SERVFAIL',
            3: 'NXDOMAIN',
            4: 'NOTIMP',
            5: 'REFUSED'
        }
        return codes.get(status, 'UNKNOWN')
    
    def load_doh_data(self, transformed_data_list: List[Dict[str, Any]]) -> bool:
        """
        Load DNS data into MongoDB
        
        Args:
            transformed_data_list: List of transformed DNS documents
            
        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self.db[self.doh_collection]
            result = collection.insert_many(transformed_data_list)
            
            logger.info(f"DNS data loaded to MongoDB: {len(result.inserted_ids)} records")
            return True
            
        except BulkWriteError as e:
            logger.error(f"Bulk write error: {e.details}")
            return False
        except Exception as e:
            logger.error(f"Error loading DNS data: {e}")
            return False
    
    # =================================================================================
    # ENDPOINT 3: CLOUDFLARE SPEED TEST API
    # =================================================================================
    
    def extract_speed_data(self, test_iterations: int = 3) -> List[Dict[str, Any]]:
        """
        Extract network speed data from Cloudflare Speed Test
        
        Args:
            test_iterations: Number of speed tests to perform
            
        Returns:
            List of speed test results
        """
        logger.info(f"Running {test_iterations} speed test iterations...")
        
        speed_results = []
        
        for i in range(test_iterations):
            try:
                start_time = time.time()
                
                # Download speed test (fetching data)
                response = self.make_request(self.speed_test_url)
                
                end_time = time.time()
                elapsed_time = end_time - start_time
                
                if response:
                    data_size = len(response.content)
                    speed_mbps = (data_size * 8) / (elapsed_time * 1_000_000)
                    
                    result = {
                        'iteration': i + 1,
                        'timestamp': datetime.now(timezone.utc).isoformat(),
                        'data_size_bytes': data_size,
                        'elapsed_time_seconds': round(elapsed_time, 3),
                        'speed_mbps': round(speed_mbps, 2),
                        'status_code': response.status_code
                    }
                    
                    speed_results.append(result)
                    logger.info(f"Speed test {i+1}: {speed_mbps:.2f} Mbps")
                
                time.sleep(1)  # Delay between tests
                
            except Exception as e:
                logger.error(f"Error in speed test iteration {i+1}: {e}")
        
        logger.info(f"Completed {len(speed_results)} speed tests")
        return speed_results
    
    def transform_speed_data(self, raw_data_list: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Transform speed test results for MongoDB
        Aggregates multiple tests into a single document
        
        Args:
            raw_data_list: List of raw speed test results
            
        Returns:
            Transformed document with aggregated statistics
        """
        logger.info(f"Transforming {len(raw_data_list)} speed test results...")
        
        current_time = datetime.now(timezone.utc).isoformat()
        
        if not raw_data_list:
            return None
        
        # Calculate statistics
        speeds = [test['speed_mbps'] for test in raw_data_list]
        avg_speed = sum(speeds) / len(speeds)
        min_speed = min(speeds)
        max_speed = max(speeds)
        
        transformed = {
            "_id": f"speed_{current_time}",
            "test_timestamp": current_time,
            "test_count": len(raw_data_list),
            "average_speed_mbps": round(avg_speed, 2),
            "min_speed_mbps": round(min_speed, 2),
            "max_speed_mbps": round(max_speed, 2),
            "speed_variance": round(max_speed - min_speed, 2),
            "individual_tests": raw_data_list,
            "ingestion_timestamp": current_time,
            "etl_version": self.etl_version,
            "source_api": "Cloudflare Speed Test",
            "raw_data": raw_data_list
        }
        
        logger.info("Speed test data transformed successfully")
        return transformed
    
    def load_speed_data(self, transformed_data: Dict[str, Any]) -> bool:
        """
        Load speed test data into MongoDB
        
        Args:
            transformed_data: Transformed speed test document
            
        Returns:
            True if successful, False otherwise
        """
        try:
            collection = self.db[self.speed_collection]
            result = collection.insert_one(transformed_data)
            
            logger.info(f"Speed test data loaded to MongoDB: {result.inserted_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error loading speed test data: {e}")
            return False
    
    # =================================================================================
    # MAIN ETL PIPELINE
    # =================================================================================
    
    def run_etl_pipeline(self, include_trace: bool = True, include_doh: bool = True, 
                        include_speed: bool = True, dns_domains: Optional[List[str]] = None,
                        speed_iterations: int = 3) -> bool:
        """
        Execute the complete ETL pipeline for all three endpoints
        
        Args:
            include_trace: Whether to run Trace API ETL
            include_doh: Whether to run DoH API ETL
            include_speed: Whether to run Speed Test ETL
            dns_domains: Custom list of domains for DNS queries
            speed_iterations: Number of speed test iterations
            
        Returns:
            True if all enabled pipelines succeeded, False otherwise
        """
        logger.info("=" * 80)
        logger.info("Starting Cloudflare Multi-Endpoint ETL Pipeline")
        logger.info("=" * 80)
        
        # Connect to MongoDB
        if not self.connect_mongodb():
            logger.error("Failed to connect to MongoDB. Aborting pipeline.")
            return False
        
        success = True
        
        # ENDPOINT 1: Trace API
        if include_trace:
            logger.info("\n--- Processing Endpoint 1: Trace API ---")
            trace_data = self.extract_trace_data()
            if trace_data:
                transformed_trace = self.transform_trace_data(trace_data)
                if not self.load_trace_data(transformed_trace):
                    success = False
            else:
                logger.warning("Trace API ETL failed")
                success = False
        
        # ENDPOINT 2: DNS over HTTPS
        if include_doh:
            logger.info("\n--- Processing Endpoint 2: DNS over HTTPS ---")
            doh_data = self.extract_doh_data(dns_domains)
            if doh_data:
                transformed_doh = self.transform_doh_data(doh_data)
                if not self.load_doh_data(transformed_doh):
                    success = False
            else:
                logger.warning("DoH API ETL failed")
                success = False
        
        # ENDPOINT 3: Speed Test
        if include_speed:
            logger.info("\n--- Processing Endpoint 3: Speed Test ---")
            speed_data = self.extract_speed_data(speed_iterations)
            if speed_data:
                transformed_speed = self.transform_speed_data(speed_data)
                if transformed_speed and not self.load_speed_data(transformed_speed):
                    success = False
            else:
                logger.warning("Speed Test ETL failed")
                success = False
        
        # Summary
        logger.info("\n" + "=" * 80)
        if success:
            logger.info("ETL Pipeline completed successfully!")
            self._print_summary()
        else:
            logger.error("ETL Pipeline completed with errors")
        logger.info("=" * 80)
        
        return success
    
    def _print_summary(self):
        """Print summary statistics for all collections"""
        try:
            trace_count = self.db[self.trace_collection].count_documents({})
            doh_count = self.db[self.doh_collection].count_documents({})
            speed_count = self.db[self.speed_collection].count_documents({})
            
            logger.info(f"\nCollection Statistics:")
            logger.info(f"  - {self.trace_collection}: {trace_count} documents")
            logger.info(f"  - {self.doh_collection}: {doh_count} documents")
            logger.info(f"  - {self.speed_collection}: {speed_count} documents")
            
        except Exception as e:
            logger.error(f"Error generating summary: {e}")
    
    def close(self):
        """Close MongoDB connection"""
        if self.client:
            self.client.close()
            logger.info("MongoDB connection closed")


def main():
    """Main entry point for the ETL connector"""
    print("\n" + "=" * 80)
    print("Cloudflare Multi-Endpoint ETL Connector")
    print("Author: Srivardhan S - 3122225001704")
    print("=" * 80 + "\n")
    
    # Initialize connector
    connector = CloudflareETLConnector()
    
    try:
        # Run complete ETL pipeline
        success = connector.run_etl_pipeline(
            include_trace=True,
            include_doh=True,
            include_speed=True,
            dns_domains=['google.com', 'github.com', 'cloudflare.com', 'amazon.com', 'microsoft.com'],
            speed_iterations=3
        )
        
        if success:
            print("\n✅ ETL Pipeline executed successfully!")
            print("📊 Check MongoDB for processed data in:")
            print(f"   - {connector.trace_collection}")
            print(f"   - {connector.doh_collection}")
            print(f"   - {connector.speed_collection}")
        else:
            print("\n❌ ETL Pipeline completed with errors. Check logs for details.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️  Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error in main: {e}", exc_info=True)
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)
    finally:
        connector.close()


if __name__ == "__main__":
    main()