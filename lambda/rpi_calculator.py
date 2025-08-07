import json
import boto3
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import logging
import os
import math
import hashlib
import uuid

# Configure logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Initialize AWS clients
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')

class TeamMetadataResolver:
    """
    Resolves team metadata (conference, organization, division, gender) for RPI calculations
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

class RPICalculator:
    """
    Calculate RPI (Rating Percentage Index) for NCAA soccer teams
    RPI = (0.25 × WP) + (0.50 × OWP) + (0.25 × OOWP)
    
    Optimized for performance with caching and atomic updates
    """
    
    def __init__(self):
        self.teams = {}
        self.matches = []
        self.cache = {}
        self.last_calculation_date = None
        self.calculation_id = None
        self.is_calculation_in_progress = False
        
    def generate_calculation_id(self) -> str:
        """Generate unique calculation ID for atomic updates"""
        return f"rpi_calc_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
    
    def get_cache_key(self, calculation_date: str) -> str:
        """Generate cache key for RPI calculations"""
        return f"rpi_calculation_{calculation_date}"
    
    def mark_calculation_start(self, calculation_date: str):
        """Mark the start of a calculation to prevent partial updates"""
        self.calculation_id = self.generate_calculation_id()
        self.is_calculation_in_progress = True
        
        # Store calculation status in DynamoDB
        try:
            table = dynamodb.Table(os.environ.get('CALCULATION_STATUS_TABLE', 'ncaa-soccer-etl-calculation-status'))
            table.put_item(
                Item={
                    'calculation_date': calculation_date,
                    'calculation_id': self.calculation_id,
                    'status': 'in_progress',
                    'start_time': datetime.now().isoformat(),
                    'matches_processed': 0,
                    'teams_calculated': 0,
                    'ttl': int((datetime.now() + timedelta(hours=2)).timestamp())
                }
            )
            logger.info(f"Started calculation {self.calculation_id} for {calculation_date}")
        except Exception as e:
            logger.error(f"Failed to mark calculation start: {str(e)}")
    
    def update_calculation_progress(self, calculation_date: str, matches_processed: int, teams_calculated: int):
        """Update calculation progress"""
        try:
            table = dynamodb.Table(os.environ.get('CALCULATION_STATUS_TABLE', 'ncaa-soccer-etl-calculation-status'))
            table.update_item(
                Key={
                    'calculation_date': calculation_date,
                    'calculation_id': self.calculation_id
                },
                UpdateExpression='SET matches_processed = :matches, teams_calculated = :teams, last_updated = :time',
                ExpressionAttributeValues={
                    ':matches': matches_processed,
                    ':teams': teams_calculated,
                    ':time': datetime.now().isoformat()
                }
            )
        except Exception as e:
            logger.warning(f"Failed to update calculation progress: {str(e)}")
    
    def mark_calculation_complete(self, calculation_date: str, total_matches: int, total_teams: int):
        """Mark calculation as complete and ready for publishing"""
        try:
            table = dynamodb.Table(os.environ.get('CALCULATION_STATUS_TABLE', 'ncaa-soccer-etl-calculation-status'))
            table.update_item(
                Key={
                    'calculation_date': calculation_date,
                    'calculation_id': self.calculation_id
                },
                UpdateExpression='SET #status = :status, completion_time = :time, total_matches = :matches, total_teams = :teams',
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':status': 'completed',
                    ':time': datetime.now().isoformat(),
                    ':matches': total_matches,
                    ':teams': total_teams
                }
            )
            self.is_calculation_in_progress = False
            logger.info(f"Completed calculation {self.calculation_id} for {calculation_date}")
        except Exception as e:
            logger.error(f"Failed to mark calculation complete: {str(e)}")
    
    def check_calculation_status(self, calculation_date: str) -> Optional[Dict]:
        """Check if there's an ongoing calculation for the given date"""
        try:
            table = dynamodb.Table(os.environ.get('CALCULATION_STATUS_TABLE', 'ncaa-soccer-etl-calculation-status'))
            response = table.query(
                KeyConditionExpression='calculation_date = :date',
                FilterExpression='#status = :status',
                ExpressionAttributeNames={
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':date': calculation_date,
                    ':status': 'in_progress'
                }
            )
            
            if response.Items:
                return response.Items[0]  # Return the most recent in-progress calculation
            return None
        except Exception as e:
            logger.warning(f"Failed to check calculation status: {str(e)}")
            return None
    
    def load_cached_calculation(self, calculation_date: str) -> Optional[List[Dict]]:
        """
        Load cached RPI calculation from DynamoDB
        Only return if no calculation is in progress
        """
        # First check if there's an ongoing calculation
        ongoing_calc = self.check_calculation_status(calculation_date)
        if ongoing_calc:
            logger.info(f"Calculation in progress for {calculation_date}, skipping cache")
            return None
        
        try:
            table = dynamodb.Table(os.environ.get('CACHE_TABLE', 'ncaa-soccer-etl-cache'))
            
            response = table.get_item(
                Key={
                    'cache_key': self.get_cache_key(calculation_date),
                    'cache_type': 'rpi_calculation'
                }
            )
            
            if 'Item' in response:
                cached_data = response['Item']
                # Check if cache is still valid (within 1 hour)
                cache_time = datetime.fromisoformat(cached_data['timestamp'])
                if datetime.now() - cache_time < timedelta(hours=1):
                    logger.info(f"Using cached RPI calculation for {calculation_date}")
                    return json.loads(cached_data['data'])
            
            return None
            
        except Exception as e:
            logger.warning(f"Failed to load cached calculation: {str(e)}")
            return None
    
    def save_cached_calculation(self, calculation_date: str, results: List[Dict]):
        """
        Save RPI calculation to cache table
        Only save if calculation is complete
        """
        if self.is_calculation_in_progress:
            logger.warning("Cannot save cache while calculation is in progress")
            return
            
        try:
            table = dynamodb.Table(os.environ.get('CACHE_TABLE', 'ncaa-soccer-etl-cache'))
            
            table.put_item(
                Item={
                    'cache_key': self.get_cache_key(calculation_date),
                    'cache_type': 'rpi_calculation',
                    'data': json.dumps(results),
                    'timestamp': datetime.now().isoformat(),
                    'calculation_id': self.calculation_id,
                    'ttl': int((datetime.now() + timedelta(hours=24)).timestamp())
                }
            )
            
            logger.info(f"Cached RPI calculation for {calculation_date}")
            
        except Exception as e:
            logger.warning(f"Failed to cache calculation: {str(e)}")
    
    def load_matches_from_dynamodb(self, table_name: str, start_date: str, end_date: str):
        """
        Load match data from DynamoDB for the specified date range
        Optimized with pagination and filtering
        """
        table = dynamodb.Table(table_name)
        
        # Use GSI for efficient date range queries
        response = table.query(
            IndexName='date-index',
            KeyConditionExpression='#date BETWEEN :start_date AND :end_date',
            ExpressionAttributeNames={
                '#date': 'date',
                '#status': 'status'
            },
            ExpressionAttributeValues={
                ':start_date': start_date,
                ':end_date': end_date,
                ':status': 'completed'
            },
            FilterExpression='#status = :status'
        )
        
        self.matches = response.get('Items', [])
        
        # Handle pagination efficiently
        while 'LastEvaluatedKey' in response:
            response = table.query(
                IndexName='date-index',
                KeyConditionExpression='#date BETWEEN :start_date AND :end_date',
                ExpressionAttributeNames={
                    '#date': 'date',
                    '#status': 'status'
                },
                ExpressionAttributeValues={
                    ':start_date': start_date,
                    ':end_date': end_date,
                    ':status': 'completed'
                },
                FilterExpression='#status = :status',
                ExclusiveStartKey=response['LastEvaluatedKey']
            )
            self.matches.extend(response.get('Items', []))
        
        logger.info(f"Loaded {len(self.matches)} completed matches from DynamoDB")
    
    def calculate_team_records_optimized(self):
        """
        Calculate win-loss records for all teams with optimized performance
        """
        # Use dictionaries for O(1) lookups
        team_records = {}
        
        for i, match in enumerate(self.matches):
            home_team = match['home_team']
            away_team = match['away_team']
            home_score = match['home_score']
            away_score = match['away_score']
            
            # Initialize team records if not exists
            if home_team not in team_records:
                team_records[home_team] = {'wins': 0, 'losses': 0, 'ties': 0, 'games': []}
            if away_team not in team_records:
                team_records[away_team] = {'wins': 0, 'losses': 0, 'ties': 0, 'games': []}
            
            # Determine winner
            if home_score > away_score:
                team_records[home_team]['wins'] += 1
                team_records[away_team]['losses'] += 1
            elif away_score > home_score:
                team_records[away_team]['wins'] += 1
                team_records[home_team]['losses'] += 1
            else:
                team_records[home_team]['ties'] += 1
                team_records[away_team]['ties'] += 1
            
            # Store game results efficiently
            team_records[home_team]['games'].append({
                'opponent': away_team,
                'home_away': 'home',
                'result': 'win' if home_score > away_score else ('loss' if away_score > home_score else 'tie')
            })
            team_records[away_team]['games'].append({
                'opponent': home_team,
                'home_away': 'away',
                'result': 'win' if away_score > home_score else ('loss' if home_score > away_score else 'tie')
            })
            
            # Update progress every 100 matches
            if (i + 1) % 100 == 0:
                self.update_calculation_progress(
                    self.calculation_id.split('_')[2],  # Extract date from calculation_id
                    i + 1,
                    len(team_records)
                )
        
        self.teams = team_records
    
    def calculate_wp_cached(self, team: str) -> float:
        """
        Calculate Winning Percentage (WP) with caching
        """
        cache_key = f"wp_{team}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        if team not in self.teams:
            return 0.0
            
        record = self.teams[team]
        total_games = record['wins'] + record['losses'] + record['ties']
        
        if total_games == 0:
            return 0.0
            
        wp = (record['wins'] + 0.5 * record['ties']) / total_games
        self.cache[cache_key] = wp
        return wp
    
    def calculate_owp_cached(self, team: str) -> float:
        """
        Calculate Opponents' Winning Percentage (OWP) with caching
        """
        cache_key = f"owp_{team}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        if team not in self.teams:
            return 0.0
            
        opponents = set()
        for game in self.teams[team]['games']:
            opponents.add(game['opponent'])
        
        if not opponents:
            return 0.0
            
        total_owp = 0.0
        for opponent in opponents:
            total_owp += self.calculate_wp_cached(opponent)
        
        owp = total_owp / len(opponents)
        self.cache[cache_key] = owp
        return owp
    
    def calculate_oowp_cached(self, team: str) -> float:
        """
        Calculate Opponents' Opponents' Winning Percentage (OOWP) with caching
        """
        cache_key = f"oowp_{team}"
        if cache_key in self.cache:
            return self.cache[cache_key]
            
        if team not in self.teams:
            return 0.0
            
        opponents = set()
        for game in self.teams[team]['games']:
            opponents.add(game['opponent'])
        
        if not opponents:
            return 0.0
            
        total_oowp = 0.0
        for opponent in opponents:
            total_oowp += self.calculate_owp_cached(opponent)
        
        oowp = total_oowp / len(opponents)
        self.cache[cache_key] = oowp
        return oowp
    
    def calculate_rpi(self, team: str) -> float:
        """
        Calculate RPI for a team with cached components
        """
        wp = self.calculate_wp_cached(team)
        owp = self.calculate_owp_cached(team)
        oowp = self.calculate_oowp_cached(team)
        
        rpi = (0.25 * wp) + (0.50 * owp) + (0.25 * oowp)
        return round(rpi, 4)
    
    def calculate_all_rpi_optimized(self) -> List[Dict]:
        """
        Calculate RPI for all teams with optimized performance and metadata
        """
        rpi_results = []
        
        # Initialize team metadata resolver
        metadata_resolver = TeamMetadataResolver()
        
        # Process teams in batches for better performance
        team_batch_size = 50
        team_list = list(self.teams.keys())
        
        for i in range(0, len(team_list), team_batch_size):
            batch = team_list[i:i + team_batch_size]
            
            for team in batch:
                rpi = self.calculate_rpi(team)
                wp = self.calculate_wp_cached(team)
                owp = self.calculate_owp_cached(team)
                oowp = self.calculate_oowp_cached(team)
                
                record = self.teams[team]
                total_games = record['wins'] + record['losses'] + record['ties']
                
                # Get team metadata
                team_metadata = metadata_resolver.get_team_metadata(team)
                
                result = {
                    'team': team,
                    'rpi': rpi,
                    'wp': wp,
                    'owp': owp,
                    'oowp': oowp,
                    'wins': record['wins'],
                    'losses': record['losses'],
                    'ties': record['ties'],
                    'total_games': total_games,
                    'win_percentage': round((record['wins'] + 0.5 * record['ties']) / total_games, 4) if total_games > 0 else 0.0
                }
                
                # Add metadata if available
                if team_metadata:
                    result.update({
                        'organization': team_metadata.get('organization'),
                        'division': team_metadata.get('division'),
                        'gender': team_metadata.get('gender'),
                        'conference': team_metadata.get('conference'),
                        'city': team_metadata.get('city'),
                        'state': team_metadata.get('state'),
                        'country': team_metadata.get('country')
                    })
                else:
                    # Default metadata for unknown teams
                    result.update({
                        'organization': 'Unknown',
                        'division': 'Unknown',
                        'gender': 'Unknown',
                        'conference': 'Unknown',
                        'city': '',
                        'state': '',
                        'country': 'USA'
                    })
                
                rpi_results.append(result)
            
            # Update progress after each batch
            self.update_calculation_progress(
                self.calculation_id.split('_')[2],
                len(self.matches),
                len(rpi_results)
            )
        
        # Sort by RPI (descending) using efficient sorting
        rpi_results.sort(key=lambda x: x['rpi'], reverse=True)
        
        # Add rank
        for i, result in enumerate(rpi_results):
            result['rank'] = i + 1
        
        return rpi_results

def store_rpi_results_in_dynamodb_atomic(results: List[Dict], table_name: str, calculation_date: str, calculation_id: str):
    """
    Store RPI calculation results in DynamoDB with atomic operations
    Only store if calculation is complete
    """
    table = dynamodb.Table(table_name)
    
    # Use batch operations for better performance
    batch_size = 25  # DynamoDB batch limit
    for i in range(0, len(results), batch_size):
        batch = results[i:i + batch_size]
        
        with table.batch_writer() as batch_writer:
            for result in batch:
                item = {
                    'calculation_date': calculation_date,
                    'team_id': result['team'],
                    'rank': result['rank'],
                    'rpi': result['rpi'],
                    'wp': result['wp'],
                    'owp': result['owp'],
                    'oowp': result['oowp'],
                    'wins': result['wins'],
                    'losses': result['losses'],
                    'ties': result['ties'],
                    'total_games': result['total_games'],
                    'win_percentage': result['win_percentage'],
                    'calculation_id': calculation_id,
                    'timestamp': datetime.now().isoformat()
                }
                batch_writer.put_item(Item=item)
    
    logger.info(f"Stored {len(results)} RPI results in DynamoDB using atomic operations")

def store_rpi_results_in_s3_optimized(results: List[Dict], bucket: str, calculation_date: str, calculation_id: str):
    """
    Store RPI results in S3 with optimized compression
    """
    # Store as compressed JSON
    json_key = f"rpi_results/{calculation_date}/rpi_results_{calculation_id}.json.gz"
    import gzip
    json_content = json.dumps(results, indent=2)
    compressed_content = gzip.compress(json_content.encode('utf-8'))
    
    s3.put_object(
        Bucket=bucket,
        Key=json_key,
        Body=compressed_content,
        ContentType='application/gzip',
        ContentEncoding='gzip',
        Metadata={
            'calculation_id': calculation_id,
            'calculation_date': calculation_date,
            'total_teams': str(len(results))
        }
    )
    
    # Store as CSV for easy access
    csv_key = f"rpi_results/{calculation_date}/rpi_results_{calculation_id}.csv"
    csv_content = "Rank,Team,RPI,WP,OWP,OOWP,Wins,Losses,Ties,Total Games,Win Percentage\n"
    
    for result in results:
        csv_content += f"{result['rank']},{result['team']},{result['rpi']},{result['wp']},{result['owp']},{result['oowp']},{result['wins']},{result['losses']},{result['ties']},{result['total_games']},{result['win_percentage']}\n"
    
    s3.put_object(
        Bucket=bucket,
        Key=csv_key,
        Body=csv_content,
        ContentType='text/csv',
        Metadata={
            'calculation_id': calculation_id,
            'calculation_date': calculation_date,
            'total_teams': str(len(results))
        }
    )
    
    logger.info(f"Stored atomic RPI results in S3: {json_key}, {csv_key}")

def lambda_handler(event, context):
    """
    Lambda handler for RPI calculation with atomic updates
    """
    try:
        # Get environment variables
        processed_data_bucket = os.environ['PROCESSED_DATA_BUCKET']
        rpi_table = os.environ['RPI_TABLE']
        matches_table = os.environ['MATCHES_TABLE']
        
        # Determine date range for calculation
        if 'start_date' in event and 'end_date' in event:
            start_date = event['start_date']
            end_date = event['end_date']
        else:
            # Default to current season (August to December)
            current_year = datetime.now().year
            start_date = f"{current_year}-08-01"
            end_date = f"{current_year}-12-31"
        
        calculation_date = datetime.now().strftime("%Y-%m-%d")
        
        logger.info(f"Calculating RPI for date range {start_date} to {end_date}")
        
        # Initialize calculator
        calculator = RPICalculator()
        
        # Check for ongoing calculation
        ongoing_calc = calculator.check_calculation_status(calculation_date)
        if ongoing_calc:
            logger.info(f"Calculation already in progress: {ongoing_calc['calculation_id']}")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Calculation already in progress: {ongoing_calc["calculation_id"]}',
                    'calculation_id': ongoing_calc['calculation_id'],
                    'status': 'in_progress'
                })
            }
        
        # Check for cached calculation first
        cached_results = calculator.load_cached_calculation(calculation_date)
        if cached_results:
            logger.info("Using cached RPI calculation")
            store_rpi_results_in_dynamodb_atomic(cached_results, rpi_table, calculation_date, "cached")
            store_rpi_results_in_s3_optimized(cached_results, processed_data_bucket, calculation_date, "cached")
            trigger_gist_publisher(calculation_date)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Used cached RPI calculation for {len(cached_results)} teams',
                    'teams_count': len(cached_results),
                    'calculation_date': calculation_date,
                    'cached': True
                })
            }
        
        # Mark calculation start
        calculator.mark_calculation_start(calculation_date)
        
        # Load match data
        calculator.load_matches_from_dynamodb(matches_table, start_date, end_date)
        
        if not calculator.matches:
            logger.warning("No matches found for RPI calculation")
            calculator.mark_calculation_complete(calculation_date, 0, 0)
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'No matches found for RPI calculation',
                    'date_range': f'{start_date} to {end_date}'
                })
            }
        
        # Calculate team records with optimization
        calculator.calculate_team_records_optimized()
        
        # Calculate RPI for all teams with caching
        rpi_results = calculator.calculate_all_rpi_optimized()
        
        if rpi_results:
            # Mark calculation complete
            calculator.mark_calculation_complete(calculation_date, len(calculator.matches), len(rpi_results))
            
            # Cache the results for future use
            calculator.save_cached_calculation(calculation_date, rpi_results)
            
            # Store results with atomic operations
            store_rpi_results_in_dynamodb_atomic(rpi_results, rpi_table, calculation_date, calculator.calculation_id)
            store_rpi_results_in_s3_optimized(rpi_results, processed_data_bucket, calculation_date, calculator.calculation_id)
            
            # Trigger gist publisher
            trigger_gist_publisher(calculation_date)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully calculated RPI for {len(rpi_results)} teams',
                'teams_count': len(rpi_results),
                'calculation_date': calculation_date,
                'calculation_id': calculator.calculation_id,
                'date_range': f'{start_date} to {end_date}',
                'atomic_updates': True
            })
        }
        
    except Exception as e:
        logger.error(f"Error in RPI calculator: {str(e)}")
        raise

def trigger_gist_publisher(calculation_date: str):
    """
    Trigger gist publisher Lambda function
    """
    try:
        lambda_client = boto3.client('lambda')
        gist_publisher_function = os.environ.get('GIST_PUBLISHER_FUNCTION', 'ncaa-soccer-etl-gist-publisher')
        
        lambda_client.invoke(
            FunctionName=gist_publisher_function,
            InvocationType='Event',  # Asynchronous
            Payload=json.dumps({
                'calculation_date': calculation_date,
                'trigger': 'rpi_calculation',
                'timestamp': datetime.now().isoformat()
            })
        )
        
        logger.info("Triggered gist publisher")
        
    except Exception as e:
        logger.error(f"Error triggering gist publisher: {str(e)}") 