import json
import boto3
import logging
from typing import Dict, Any, List
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

class MatchEventHandler:
    """
    Handles match-related events
    """
    
    def __init__(self):
        self.matches_table = dynamodb.Table(os.environ.get('MATCHES_TABLE', 'ncaa-soccer-etl-matches'))
        self.raw_data_bucket = os.environ.get('RAW_DATA_BUCKET', 'ncaa-soccer-etl-raw-data')
    
    def handle_match_created(self, event_data: Dict[str, Any]):
        """
        Handle MatchCreated events
        """
        try:
            match_id = event_data.get('match_id')
            logger.info(f"Processing match created event for match {match_id}")
            
            # Store match in DynamoDB
            self.matches_table.put_item(Item=event_data)
            
            # Trigger RPI calculation if needed
            self._trigger_rpi_calculation_if_needed(event_data)
            
            logger.info(f"Successfully processed match {match_id}")
            
        except Exception as e:
            logger.error(f"Error handling match created event: {str(e)}")
            raise
    
    def _trigger_rpi_calculation_if_needed(self, match_data: Dict[str, Any]):
        """
        Trigger RPI calculation if conditions are met
        """
        # Check if we have enough new matches to warrant a calculation
        # This could be based on time, match count, or other criteria
        pass

class CalculationEventHandler:
    """
    Handles calculation-related events
    """
    
    def __init__(self):
        self.calculation_status_table = dynamodb.Table(os.environ.get('CALCULATION_STATUS_TABLE', 'ncaa-soccer-etl-calculation-status'))
        self.rpi_table = dynamodb.Table(os.environ.get('RPI_TABLE', 'ncaa-soccer-etl-rpi-calculations'))
    
    def handle_calculation_started(self, event_data: Dict[str, Any]):
        """
        Handle CalculationStarted events
        """
        try:
            calculation_id = event_data.get('calculation_id')
            logger.info(f"Processing calculation started event for {calculation_id}")
            
            # Update calculation status
            self.calculation_status_table.put_item(Item={
                'calculation_date': event_data.get('calculation_date'),
                'calculation_id': calculation_id,
                'status': 'in_progress',
                'start_time': event_data.get('timestamp'),
                'matches_processed': 0,
                'teams_calculated': 0
            })
            
            logger.info(f"Successfully processed calculation started event for {calculation_id}")
            
        except Exception as e:
            logger.error(f"Error handling calculation started event: {str(e)}")
            raise
    
    def handle_calculation_completed(self, event_data: Dict[str, Any]):
        """
        Handle CalculationCompleted events
        """
        try:
            calculation_id = event_data.get('calculation_id')
            logger.info(f"Processing calculation completed event for {calculation_id}")
            
            # Update calculation status
            self.calculation_status_table.update_item(
                Key={
                    'calculation_date': event_data.get('calculation_date'),
                    'calculation_id': calculation_id
                },
                UpdateExpression='SET #status = :status, completion_time = :time, total_teams = :teams',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={
                    ':status': 'completed',
                    ':time': event_data.get('timestamp'),
                    ':teams': event_data.get('total_teams', 0)
                }
            )
            
            # Trigger downstream processes
            self._trigger_downstream_processes(event_data)
            
            logger.info(f"Successfully processed calculation completed event for {calculation_id}")
            
        except Exception as e:
            logger.error(f"Error handling calculation completed event: {str(e)}")
            raise
    
    def _trigger_downstream_processes(self, event_data: Dict[str, Any]):
        """
        Trigger downstream processes like gist publishing, cache updates, etc.
        """
        try:
            # Trigger gist publisher
            lambda_client.invoke(
                FunctionName=os.environ.get('GIST_PUBLISHER_FUNCTION', 'ncaa-soccer-etl-gist-publisher'),
                InvocationType='Event',
                Payload=json.dumps({
                    'calculation_date': event_data.get('calculation_date'),
                    'trigger': 'calculation_completed',
                    'calculation_id': event_data.get('calculation_id')
                })
            )
            
            # Trigger cache update
            lambda_client.invoke(
                FunctionName=os.environ.get('CACHE_UPDATER_FUNCTION', 'ncaa-soccer-etl-cache-updater'),
                InvocationType='Event',
                Payload=json.dumps({
                    'calculation_date': event_data.get('calculation_date'),
                    'trigger': 'calculation_completed'
                })
            )
            
        except Exception as e:
            logger.error(f"Error triggering downstream processes: {str(e)}")

class MetadataEventHandler:
    """
    Handles metadata-related events
    """
    
    def __init__(self):
        self.team_metadata_table = dynamodb.Table(os.environ.get('TEAM_METADATA_TABLE', 'ncaa-soccer-etl-team-metadata'))
    
    def handle_team_metadata_updated(self, event_data: Dict[str, Any]):
        """
        Handle TeamMetadataUpdated events
        """
        try:
            team_id = event_data.get('team_id')
            logger.info(f"Processing team metadata updated event for team {team_id}")
            
            # Update team metadata
            self.team_metadata_table.put_item(Item=event_data)
            
            # Trigger cache invalidation if needed
            self._trigger_cache_invalidation(team_id)
            
            logger.info(f"Successfully processed team metadata updated event for {team_id}")
            
        except Exception as e:
            logger.error(f"Error handling team metadata updated event: {str(e)}")
            raise
    
    def _trigger_cache_invalidation(self, team_id: str):
        """
        Trigger cache invalidation for affected data
        """
        try:
            # This could trigger cache updates for rankings, conference data, etc.
            pass
        except Exception as e:
            logger.error(f"Error triggering cache invalidation: {str(e)}")

def lambda_handler(event, context):
    """
    Lambda handler for event processing
    """
    try:
        # Parse the event
        if 'detail' in event:
            event_detail = json.loads(event['detail'])
        else:
            event_detail = event
        
        event_type = event_detail.get('event_type')
        event_data = event_detail.get('data', {})
        
        logger.info(f"Processing event: {event_type}")
        
        # Route to appropriate handler
        if event_type == 'MatchCreated':
            handler = MatchEventHandler()
            handler.handle_match_created(event_data)
            
        elif event_type == 'CalculationStarted':
            handler = CalculationEventHandler()
            handler.handle_calculation_started(event_data)
            
        elif event_type == 'CalculationCompleted':
            handler = CalculationEventHandler()
            handler.handle_calculation_completed(event_data)
            
        elif event_type == 'TeamMetadataUpdated':
            handler = MetadataEventHandler()
            handler.handle_team_metadata_updated(event_data)
            
        else:
            logger.warning(f"Unknown event type: {event_type}")
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Unknown event type',
                    'event_type': event_type
                })
            }
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully processed {event_type} event'
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to process event',
                'message': str(e)
            })
        } 