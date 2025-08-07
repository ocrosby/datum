import json
import boto3
import requests
from datetime import datetime, timedelta
from bs4 import BeautifulSoup
from typing import Dict, List, Optional
import logging
import os

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

class TeamMetadataResolver:
    """
    Resolves team metadata (conference, organization, division, gender) for match data
    """
    
    def __init__(self):
        self.table = dynamodb.Table(os.environ.get('TEAM_METADATA_TABLE', 'ncaa-soccer-etl-team-metadata'))
        self.cache = {}
    
    def get_team_metadata(self, team_id: str) -> Optional[Dict]:
        """
        Get team metadata from DynamoDB with caching
        """
        if team_id in self.cache:
            return self.cache[team_id]
        
        try:
            response = self.table.get_item(Key={'team_id': team_id})
            metadata = response.get('Item')
            
            if metadata:
                self.cache[team_id] = metadata
            
            return metadata
        except Exception as e:
            logger.warning(f"Failed to get metadata for team {team_id}: {str(e)}")
            return None
    
    def resolve_team_metadata(self, team_name: str, organization: str = None) -> Optional[Dict]:
        """
        Resolve team metadata by name and optional organization
        """
        try:
            # Search by team name
            response = self.table.query(
                IndexName='team_name-index',
                KeyConditionExpression='team_name = :name',
                ExpressionAttributeValues={':name': team_name}
            )
            
            teams = response.get('Items', [])
            
            if not teams:
                return None
            
            # If organization specified, filter by it
            if organization:
                teams = [team for team in teams if team.get('organization') == organization]
            
            # Return the first match (or implement more sophisticated matching)
            return teams[0] if teams else None
            
        except Exception as e:
            logger.warning(f"Failed to resolve metadata for team {team_name}: {str(e)}")
            return None
    
    def enrich_match_with_metadata(self, match: Dict) -> Dict:
        """
        Enrich match data with team metadata
        """
        enriched_match = match.copy()
        
        # Get metadata for home team
        home_metadata = self.get_team_metadata(match.get('home_team'))
        if home_metadata:
            enriched_match['home_team_metadata'] = {
                'organization': home_metadata.get('organization'),
                'division': home_metadata.get('division'),
                'gender': home_metadata.get('gender'),
                'conference': home_metadata.get('conference'),
                'city': home_metadata.get('city'),
                'state': home_metadata.get('state')
            }
        
        # Get metadata for away team
        away_metadata = self.get_team_metadata(match.get('away_team'))
        if away_metadata:
            enriched_match['away_team_metadata'] = {
                'organization': away_metadata.get('organization'),
                'division': away_metadata.get('division'),
                'gender': away_metadata.get('gender'),
                'conference': away_metadata.get('conference'),
                'city': away_metadata.get('city'),
                'state': away_metadata.get('state')
            }
        
        return enriched_match

def get_ncaa_match_data(start_date: str, end_date: str) -> List[Dict]:
    """
    Scrape NCAA match data for the given date range
    """
    matches = []
    
    # NCAA soccer schedule URL pattern
    base_url = "https://www.ncaa.com/scoreboard/soccer-women/d1"
    
    current_date = datetime.strptime(start_date, "%Y-%m-%d")
    end_date_obj = datetime.strptime(end_date, "%Y-%m-%d")
    
    while current_date <= end_date_obj:
        date_str = current_date.strftime("%Y/%m/%d")
        url = f"{base_url}/{date_str}"
        
        try:
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find match containers
            match_containers = soup.find_all('div', class_='gamePod')
            
            for container in match_containers:
                match_data = parse_match_container(container, current_date.strftime("%Y-%m-%d"))
                if match_data:
                    matches.append(match_data)
                    
        except Exception as e:
            logger.error(f"Error scraping data for {date_str}: {str(e)}")
            
        current_date += timedelta(days=1)
    
    return matches

def parse_match_container(container, date: str) -> Optional[Dict]:
    """
    Parse individual match container to extract match data
    """
    try:
        # Extract team names
        teams = container.find_all('div', class_='team-name')
        if len(teams) < 2:
            return None
            
        home_team = teams[0].text.strip()
        away_team = teams[1].text.strip()
        
        # Extract scores
        scores = container.find_all('div', class_='team-score')
        home_score = None
        away_score = None
        
        if len(scores) >= 2:
            try:
                home_score = int(scores[0].text.strip())
                away_score = int(scores[1].text.strip())
            except ValueError:
                pass
        
        # Generate unique match ID
        match_id = f"{date}_{home_team}_{away_team}".replace(" ", "_").replace("'", "").replace(".", "")
        
        return {
            'match_id': match_id,
            'date': date,
            'home_team': home_team,
            'away_team': away_team,
            'home_score': home_score,
            'away_score': away_score,
            'status': 'completed' if home_score is not None and away_score is not None else 'scheduled',
            'timestamp': datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error parsing match container: {str(e)}")
        return None

def store_matches_in_dynamodb(matches: List[Dict], table_name: str):
    """
    Store match data in DynamoDB
    """
    table = dynamodb.Table(table_name)
    
    with table.batch_writer() as batch:
        for match in matches:
            batch.put_item(Item=match)
    
    logger.info(f"Stored {len(matches)} matches in DynamoDB")

def store_raw_data_in_s3(matches: List[Dict], bucket: str, date: str):
    """
    Store raw match data in S3 for backup and audit
    """
    if not matches:
        return
        
    key = f"raw_matches/{date}/matches.json"
    
    try:
        s3.put_object(
            Bucket=bucket,
            Key=key,
            Body=json.dumps(matches, indent=2),
            ContentType='application/json'
        )
        logger.info(f"Stored raw data in S3: {key}")
    except Exception as e:
        logger.error(f"Error storing data in S3: {str(e)}")

def lambda_handler(event, context):
    """
    Lambda handler for match data collection
    """
    try:
        # Get environment variables
        raw_data_bucket = os.environ['RAW_DATA_BUCKET']
        matches_table = os.environ['MATCHES_TABLE']
        
        # Determine date range (default to last 7 days if not specified)
        if 'start_date' in event and 'end_date' in event:
            start_date = event['start_date']
            end_date = event['end_date']
        else:
            end_date = datetime.now().strftime("%Y-%m-%d")
            start_date = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        
        logger.info(f"Collecting match data from {start_date} to {end_date}")
        
        # Collect match data
        matches = get_ncaa_match_data(start_date, end_date)
        
        if matches:
            # Store in DynamoDB
            store_matches_in_dynamodb(matches, matches_table)
            
            # Store raw data in S3
            store_raw_data_in_s3(matches, raw_data_bucket, start_date)
            
            # Trigger RPI calculation if we have new completed matches
            completed_matches = [m for m in matches if m['status'] == 'completed']
            if completed_matches:
                trigger_rpi_calculation()
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully collected {len(matches)} matches',
                'matches_count': len(matches),
                'date_range': f'{start_date} to {end_date}'
            })
        }
        
    except Exception as e:
        logger.error(f"Error in match collector: {str(e)}")
        raise

def trigger_rpi_calculation():
    """
    Trigger RPI calculation Lambda function
    """
    try:
        lambda_client = boto3.client('lambda')
        rpi_calculator_function = os.environ.get('RPI_CALCULATOR_FUNCTION', 'ncaa-soccer-etl-rpi-calculator')
        
        lambda_client.invoke(
            FunctionName=rpi_calculator_function,
            InvocationType='Event',  # Asynchronous
            Payload=json.dumps({
                'trigger': 'match_collection',
                'timestamp': datetime.now().isoformat()
            })
        )
        
        logger.info("Triggered RPI calculation")
        
    except Exception as e:
        logger.error(f"Error triggering RPI calculation: {str(e)}") 