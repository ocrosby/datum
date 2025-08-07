import json
import boto3
import csv
import logging
from datetime import datetime
from typing import Dict, List, Optional
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
s3 = boto3.client('s3')

class TeamMetadataManager:
    """
    Manages team metadata including conference, organization, division, and gender
    Supports NCAA, NAIA, ECNL, GA, NWSL, MLS, and future leagues
    """
    
    def __init__(self):
        self.table = dynamodb.Table(os.environ.get('TEAM_METADATA_TABLE', 'ncaa-soccer-etl-team-metadata'))
    
    def load_team_from_csv(self, team_data: Dict) -> Dict:
        """
        Load team metadata from CSV row
        """
        return {
            'team_id': team_data.get('team_id'),
            'team_name': team_data.get('team_name'),
            'organization': team_data.get('organization', 'NCAA'),
            'division': team_data.get('division', 'DI'),
            'gender': team_data.get('gender', 'Women'),
            'conference': team_data.get('conference', 'Unknown'),
            'city': team_data.get('city', ''),
            'state': team_data.get('state', ''),
            'country': team_data.get('country', 'USA'),
            'active': team_data.get('active', 'true').lower() == 'true',
            'last_updated': datetime.now().isoformat()
        }
    
    def store_team_metadata(self, team_data: Dict):
        """
        Store team metadata in DynamoDB
        """
        try:
            self.table.put_item(Item=team_data)
            logger.info(f"Stored metadata for team: {team_data['team_id']}")
        except Exception as e:
            logger.error(f"Failed to store metadata for team {team_data['team_id']}: {str(e)}")
            raise
    
    def batch_store_teams(self, teams: List[Dict]):
        """
        Store multiple teams in batch
        """
        try:
            with self.table.batch_writer() as batch:
                for team in teams:
                    batch.put_item(Item=team)
            logger.info(f"Stored {len(teams)} teams in batch")
        except Exception as e:
            logger.error(f"Failed to batch store teams: {str(e)}")
            raise
    
    def get_team_metadata(self, team_id: str) -> Optional[Dict]:
        """
        Get team metadata by team_id
        """
        try:
            response = self.table.get_item(Key={'team_id': team_id})
            return response.get('Item')
        except Exception as e:
            logger.error(f"Failed to get metadata for team {team_id}: {str(e)}")
            return None
    
    def get_teams_by_organization(self, organization: str, division: str = None, gender: str = None) -> List[Dict]:
        """
        Get teams by organization and optional filters
        """
        try:
            if division and gender:
                response = self.table.query(
                    IndexName='organization-division-gender-index',
                    KeyConditionExpression='organization = :org AND division = :div',
                    FilterExpression='#gender = :gender',
                    ExpressionAttributeNames={'#gender': 'gender'},
                    ExpressionAttributeValues={
                        ':org': organization,
                        ':div': division,
                        ':gender': gender
                    }
                )
            elif division:
                response = self.table.query(
                    IndexName='organization-division-gender-index',
                    KeyConditionExpression='organization = :org AND division = :div',
                    ExpressionAttributeValues={
                        ':org': organization,
                        ':div': division
                    }
                )
            else:
                response = self.table.query(
                    IndexName='organization-division-gender-index',
                    KeyConditionExpression='organization = :org',
                    ExpressionAttributeValues={':org': organization}
                )
            
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Failed to get teams for {organization}: {str(e)}")
            return []
    
    def get_teams_by_conference(self, conference: str, organization: str = None) -> List[Dict]:
        """
        Get teams by conference and optional organization
        """
        try:
            if organization:
                response = self.table.query(
                    IndexName='conference-organization-index',
                    KeyConditionExpression='conference = :conf AND organization = :org',
                    ExpressionAttributeValues={
                        ':conf': conference,
                        ':org': organization
                    }
                )
            else:
                response = self.table.query(
                    IndexName='conference-organization-index',
                    KeyConditionExpression='conference = :conf',
                    ExpressionAttributeValues={':conf': conference}
                )
            
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Failed to get teams for conference {conference}: {str(e)}")
            return []
    
    def search_teams_by_name(self, team_name: str) -> List[Dict]:
        """
        Search teams by name (partial match)
        """
        try:
            response = self.table.query(
                IndexName='team_name-index',
                KeyConditionExpression='begins_with(team_name, :name)',
                ExpressionAttributeValues={':name': team_name}
            )
            return response.get('Items', [])
        except Exception as e:
            logger.error(f"Failed to search teams by name {team_name}: {str(e)}")
            return []
    
    def update_team_metadata(self, team_id: str, updates: Dict):
        """
        Update team metadata
        """
        try:
            update_expression = "SET "
            expression_attribute_names = {}
            expression_attribute_values = {}
            
            for key, value in updates.items():
                if key != 'team_id':  # Don't update the primary key
                    update_expression += f"#{key} = :{key}, "
                    expression_attribute_names[f"#{key}"] = key
                    expression_attribute_values[f":{key}"] = value
            
            update_expression += "last_updated = :timestamp"
            expression_attribute_values[":timestamp"] = datetime.now().isoformat()
            
            self.table.update_item(
                Key={'team_id': team_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values
            )
            
            logger.info(f"Updated metadata for team: {team_id}")
        except Exception as e:
            logger.error(f"Failed to update metadata for team {team_id}: {str(e)}")
            raise
    
    def delete_team_metadata(self, team_id: str):
        """
        Delete team metadata
        """
        try:
            self.table.delete_item(Key={'team_id': team_id})
            logger.info(f"Deleted metadata for team: {team_id}")
        except Exception as e:
            logger.error(f"Failed to delete metadata for team {team_id}: {str(e)}")
            raise

def load_teams_from_s3(bucket: str, key: str) -> List[Dict]:
    """
    Load team metadata from S3 CSV file
    """
    try:
        response = s3.get_object(Bucket=bucket, Key=key)
        csv_content = response['Body'].read().decode('utf-8')
        
        teams = []
        reader = csv.DictReader(csv_content.splitlines())
        
        for row in reader:
            team_data = {
                'team_id': row['team_id'],
                'team_name': row['team_name'],
                'organization': row.get('organization', 'NCAA'),
                'division': row.get('division', 'DI'),
                'gender': row.get('gender', 'Women'),
                'conference': row.get('conference', 'Unknown'),
                'city': row.get('city', ''),
                'state': row.get('state', ''),
                'country': row.get('country', 'USA'),
                'active': row.get('active', 'true').lower() == 'true',
                'last_updated': datetime.now().isoformat()
            }
            teams.append(team_data)
        
        return teams
    except Exception as e:
        logger.error(f"Failed to load teams from S3 {bucket}/{key}: {str(e)}")
        raise

def lambda_handler(event, context):
    """
    Lambda handler for team metadata management
    """
    try:
        manager = TeamMetadataManager()
        
        # Handle different operation types
        operation = event.get('operation')
        
        if operation == 'load_from_s3':
            # Load teams from S3 CSV file
            bucket = event['bucket']
            key = event['key']
            
            teams = load_teams_from_s3(bucket, key)
            manager.batch_store_teams(teams)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Successfully loaded {len(teams)} teams from S3',
                    'teams_loaded': len(teams)
                })
            }
        
        elif operation == 'get_team':
            # Get single team metadata
            team_id = event['team_id']
            team = manager.get_team_metadata(team_id)
            
            if team:
                return {
                    'statusCode': 200,
                    'body': json.dumps(team)
                }
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Team not found'})
                }
        
        elif operation == 'get_teams_by_organization':
            # Get teams by organization
            organization = event['organization']
            division = event.get('division')
            gender = event.get('gender')
            
            teams = manager.get_teams_by_organization(organization, division, gender)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'teams': teams,
                    'count': len(teams)
                })
            }
        
        elif operation == 'get_teams_by_conference':
            # Get teams by conference
            conference = event['conference']
            organization = event.get('organization')
            
            teams = manager.get_teams_by_conference(conference, organization)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'teams': teams,
                    'count': len(teams)
                })
            }
        
        elif operation == 'search_teams':
            # Search teams by name
            team_name = event['team_name']
            
            teams = manager.search_teams_by_name(team_name)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'teams': teams,
                    'count': len(teams)
                })
            }
        
        elif operation == 'update_team':
            # Update team metadata
            team_id = event['team_id']
            updates = event['updates']
            
            manager.update_team_metadata(team_id, updates)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Successfully updated team {team_id}'
                })
            }
        
        elif operation == 'delete_team':
            # Delete team metadata
            team_id = event['team_id']
            
            manager.delete_team_metadata(team_id)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Successfully deleted team {team_id}'
                })
            }
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid operation',
                    'supported_operations': [
                        'load_from_s3',
                        'get_team',
                        'get_teams_by_organization',
                        'get_teams_by_conference',
                        'search_teams',
                        'update_team',
                        'delete_team'
                    ]
                })
            }
    
    except Exception as e:
        logger.error(f"Error in team metadata manager: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Internal server error',
                'message': str(e)
            })
        } 