import json
import boto3
import uuid
from datetime import datetime
from typing import Dict, Any, Optional
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

events_client = boto3.client('events')
dynamodb = boto3.resource('dynamodb')

class EventPublisher:
    """
    Centralized event publisher for the EDA system
    Handles event sourcing and event bus publishing
    """
    
    def __init__(self):
        self.event_store = dynamodb.Table(os.environ.get('EVENT_STORE_TABLE', 'ncaa-soccer-etl-event-store'))
        self.main_bus = os.environ.get('MAIN_EVENT_BUS', 'ncaa-soccer-etl-event-bus')
        self.soccer_bus = os.environ.get('SOCCER_EVENT_BUS', 'ncaa-soccer-etl-soccer-events')
        self.calculation_bus = os.environ.get('CALCULATION_EVENT_BUS', 'ncaa-soccer-etl-calculation-events')
        self.metadata_bus = os.environ.get('METADATA_EVENT_BUS', 'ncaa-soccer-etl-metadata-events')
    
    def publish_event(self, event_type: str, event_data: Dict[str, Any], 
                     aggregate_id: str, bus_name: str = None) -> str:
        """
        Publish event to both event store and event bus
        """
        event_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        # Create event envelope
        event = {
            'event_id': event_id,
            'event_type': event_type,
            'aggregate_id': aggregate_id,
            'timestamp': timestamp,
            'data': event_data,
            'version': '1.0'
        }
        
        # Store in event store
        self._store_event(event)
        
        # Publish to event bus
        self._publish_to_bus(event, bus_name or self.main_bus)
        
        logger.info(f"Published event {event_type} with ID {event_id}")
        return event_id
    
    def _store_event(self, event: Dict[str, Any]):
        """
        Store event in DynamoDB event store
        """
        try:
            self.event_store.put_item(Item=event)
        except Exception as e:
            logger.error(f"Failed to store event: {str(e)}")
            raise
    
    def _publish_to_bus(self, event: Dict[str, Any], bus_name: str):
        """
        Publish event to CloudWatch Event Bus
        """
        try:
            events_client.put_events(
                Entries=[
                    {
                        'Source': 'ncaa-soccer-etl',
                        'DetailType': event['event_type'],
                        'Detail': json.dumps(event),
                        'EventBusName': bus_name
                    }
                ]
            )
        except Exception as e:
            logger.error(f"Failed to publish event to bus: {str(e)}")
            raise
    
    def publish_match_event(self, match_data: Dict[str, Any]) -> str:
        """
        Publish match-related events
        """
        return self.publish_event(
            event_type='MatchCreated',
            event_data=match_data,
            aggregate_id=f"match_{match_data.get('match_id', 'unknown')}",
            bus_name=self.soccer_bus
        )
    
    def publish_calculation_event(self, calculation_data: Dict[str, Any]) -> str:
        """
        Publish calculation-related events
        """
        return self.publish_event(
            event_type='CalculationStarted',
            event_data=calculation_data,
            aggregate_id=f"calculation_{calculation_data.get('calculation_id', 'unknown')}",
            bus_name=self.calculation_bus
        )
    
    def publish_metadata_event(self, metadata_data: Dict[str, Any]) -> str:
        """
        Publish metadata-related events
        """
        return self.publish_event(
            event_type='TeamMetadataUpdated',
            event_data=metadata_data,
            aggregate_id=f"team_{metadata_data.get('team_id', 'unknown')}",
            bus_name=self.metadata_bus
        )

def lambda_handler(event, context):
    """
    Lambda handler for event publishing
    """
    try:
        publisher = EventPublisher()
        
        event_type = event.get('event_type')
        event_data = event.get('event_data', {})
        aggregate_id = event.get('aggregate_id')
        bus_name = event.get('bus_name')
        
        if not all([event_type, event_data, aggregate_id]):
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Missing required parameters',
                    'required': ['event_type', 'event_data', 'aggregate_id']
                })
            }
        
        event_id = publisher.publish_event(
            event_type=event_type,
            event_data=event_data,
            aggregate_id=aggregate_id,
            bus_name=bus_name
        )
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': 'Event published successfully',
                'event_id': event_id,
                'event_type': event_type,
                'aggregate_id': aggregate_id
            })
        }
        
    except Exception as e:
        logger.error(f"Error publishing event: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to publish event',
                'message': str(e)
            })
        } 