import json
import boto3
import uuid
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging
import os

logger = logging.getLogger()
logger.setLevel(logging.INFO)

dynamodb = boto3.resource('dynamodb')
lambda_client = boto3.client('lambda')

class SagaCoordinator:
    """
    Coordinates complex workflows using the Saga pattern
    Handles compensation for failed steps
    """
    
    def __init__(self):
        self.saga_table = dynamodb.Table(os.environ.get('SAGA_TABLE', 'ncaa-soccer-etl-saga'))
        self.event_publisher = EventPublisher()
    
    def start_saga(self, saga_type: str, saga_data: Dict[str, Any]) -> str:
        """
        Start a new saga
        """
        saga_id = str(uuid.uuid4())
        timestamp = datetime.now().isoformat()
        
        saga = {
            'saga_id': saga_id,
            'saga_type': saga_type,
            'status': 'started',
            'data': saga_data,
            'steps': [],
            'compensations': [],
            'start_time': timestamp,
            'last_updated': timestamp
        }
        
        self.saga_table.put_item(Item=saga)
        
        logger.info(f"Started saga {saga_id} of type {saga_type}")
        return saga_id
    
    def add_step(self, saga_id: str, step_name: str, step_data: Dict[str, Any], 
                 compensation_function: str = None):
        """
        Add a step to the saga
        """
        step = {
            'step_name': step_name,
            'step_data': step_data,
            'status': 'pending',
            'compensation_function': compensation_function,
            'start_time': None,
            'end_time': None,
            'error': None
        }
        
        self.saga_table.update_item(
            Key={'saga_id': saga_id},
            UpdateExpression='SET steps = list_append(steps, :step), last_updated = :time',
            ExpressionAttributeValues={
                ':step': [step],
                ':time': datetime.now().isoformat()
            }
        )
        
        logger.info(f"Added step {step_name} to saga {saga_id}")
    
    def execute_step(self, saga_id: str, step_index: int):
        """
        Execute a specific step in the saga
        """
        try:
            # Get saga
            response = self.saga_table.get_item(Key={'saga_id': saga_id})
            saga = response['Item']
            
            if step_index >= len(saga['steps']):
                raise ValueError(f"Step index {step_index} out of range")
            
            step = saga['steps'][step_index]
            step['status'] = 'running'
            step['start_time'] = datetime.now().isoformat()
            
            # Update step status
            self._update_step_status(saga_id, step_index, step)
            
            # Execute the step based on step_name
            result = self._execute_step_logic(step['step_name'], step['step_data'])
            
            # Mark step as completed
            step['status'] = 'completed'
            step['end_time'] = datetime.now().isoformat()
            step['result'] = result
            
            self._update_step_status(saga_id, step_index, step)
            
            logger.info(f"Completed step {step['step_name']} in saga {saga_id}")
            
            # Execute next step if available
            if step_index + 1 < len(saga['steps']):
                self.execute_step(saga_id, step_index + 1)
            else:
                # Saga completed successfully
                self._complete_saga(saga_id)
                
        except Exception as e:
            logger.error(f"Error executing step {step_index} in saga {saga_id}: {str(e)}")
            self._compensate_saga(saga_id, step_index)
            raise
    
    def _execute_step_logic(self, step_name: str, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute the logic for a specific step
        """
        if step_name == 'collect_matches':
            return self._collect_matches(step_data)
        elif step_name == 'calculate_rpi':
            return self._calculate_rpi(step_data)
        elif step_name == 'publish_results':
            return self._publish_results(step_data)
        elif step_name == 'update_cache':
            return self._update_cache(step_data)
        else:
            raise ValueError(f"Unknown step: {step_name}")
    
    def _collect_matches(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Collect match data
        """
        try:
            response = lambda_client.invoke(
                FunctionName=os.environ.get('MATCH_COLLECTOR_FUNCTION', 'ncaa-soccer-etl-match-collector'),
                InvocationType='RequestResponse',
                Payload=json.dumps(step_data)
            )
            
            result = json.loads(response['Payload'].read())
            return result
            
        except Exception as e:
            logger.error(f"Error collecting matches: {str(e)}")
            raise
    
    def _calculate_rpi(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate RPI
        """
        try:
            response = lambda_client.invoke(
                FunctionName=os.environ.get('RPI_CALCULATOR_FUNCTION', 'ncaa-soccer-etl-rpi-calculator'),
                InvocationType='RequestResponse',
                Payload=json.dumps(step_data)
            )
            
            result = json.loads(response['Payload'].read())
            return result
            
        except Exception as e:
            logger.error(f"Error calculating RPI: {str(e)}")
            raise
    
    def _publish_results(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Publish results
        """
        try:
            response = lambda_client.invoke(
                FunctionName=os.environ.get('GIST_PUBLISHER_FUNCTION', 'ncaa-soccer-etl-gist-publisher'),
                InvocationType='RequestResponse',
                Payload=json.dumps(step_data)
            )
            
            result = json.loads(response['Payload'].read())
            return result
            
        except Exception as e:
            logger.error(f"Error publishing results: {str(e)}")
            raise
    
    def _update_cache(self, step_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Update cache
        """
        try:
            # Cache update logic
            return {'status': 'success', 'message': 'Cache updated'}
            
        except Exception as e:
            logger.error(f"Error updating cache: {str(e)}")
            raise
    
    def _compensate_saga(self, saga_id: str, failed_step_index: int):
        """
        Compensate for failed saga by rolling back completed steps
        """
        try:
            response = self.saga_table.get_item(Key={'saga_id': saga_id})
            saga = response['Item']
            
            # Mark saga as failed
            saga['status'] = 'failed'
            saga['failed_step'] = failed_step_index
            saga['last_updated'] = datetime.now().isoformat()
            
            self.saga_table.put_item(Item=saga)
            
            # Execute compensations in reverse order
            for i in range(failed_step_index - 1, -1, -1):
                step = saga['steps'][i]
                if step['status'] == 'completed' and step['compensation_function']:
                    self._execute_compensation(saga_id, i, step['compensation_function'])
            
            logger.info(f"Compensated saga {saga_id} after step {failed_step_index} failed")
            
        except Exception as e:
            logger.error(f"Error compensating saga {saga_id}: {str(e)}")
            raise
    
    def _execute_compensation(self, saga_id: str, step_index: int, compensation_function: str):
        """
        Execute compensation for a specific step
        """
        try:
            # Execute compensation logic based on function name
            if compensation_function == 'rollback_matches':
                self._rollback_matches(saga_id, step_index)
            elif compensation_function == 'rollback_rpi':
                self._rollback_rpi(saga_id, step_index)
            elif compensation_function == 'rollback_publish':
                self._rollback_publish(saga_id, step_index)
            else:
                logger.warning(f"Unknown compensation function: {compensation_function}")
                
        except Exception as e:
            logger.error(f"Error executing compensation {compensation_function}: {str(e)}")
    
    def _rollback_matches(self, saga_id: str, step_index: int):
        """
        Rollback match collection
        """
        # Implementation for rolling back match collection
        pass
    
    def _rollback_rpi(self, saga_id: str, step_index: int):
        """
        Rollback RPI calculation
        """
        # Implementation for rolling back RPI calculation
        pass
    
    def _rollback_publish(self, saga_id: str, step_index: int):
        """
        Rollback result publishing
        """
        # Implementation for rolling back result publishing
        pass
    
    def _update_step_status(self, saga_id: str, step_index: int, step: Dict[str, Any]):
        """
        Update step status in saga
        """
        self.saga_table.update_item(
            Key={'saga_id': saga_id},
            UpdateExpression='SET steps[:index] = :step, last_updated = :time',
            ExpressionAttributeValues={
                ':index': step_index,
                ':step': step,
                ':time': datetime.now().isoformat()
            }
        )
    
    def _complete_saga(self, saga_id: str):
        """
        Mark saga as completed
        """
        self.saga_table.update_item(
            Key={'saga_id': saga_id},
            UpdateExpression='SET #status = :status, last_updated = :time',
            ExpressionAttributeNames={'#status': 'status'},
            ExpressionAttributeValues={
                ':status': 'completed',
                ':time': datetime.now().isoformat()
            }
        )
        
        logger.info(f"Completed saga {saga_id}")

def lambda_handler(event, context):
    """
    Lambda handler for saga coordination
    """
    try:
        coordinator = SagaCoordinator()
        
        action = event.get('action')
        
        if action == 'start_saga':
            saga_type = event['saga_type']
            saga_data = event.get('saga_data', {})
            
            saga_id = coordinator.start_saga(saga_type, saga_data)
            
            # Add steps based on saga type
            if saga_type == 'rpi_calculation':
                coordinator.add_step(saga_id, 'collect_matches', {'date_range': saga_data.get('date_range')})
                coordinator.add_step(saga_id, 'calculate_rpi', {'calculation_date': saga_data.get('calculation_date')})
                coordinator.add_step(saga_id, 'publish_results', {'calculation_date': saga_data.get('calculation_date')})
                coordinator.add_step(saga_id, 'update_cache', {'calculation_date': saga_data.get('calculation_date')})
            
            # Execute first step
            coordinator.execute_step(saga_id, 0)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': 'Saga started successfully',
                    'saga_id': saga_id
                })
            }
        
        elif action == 'execute_step':
            saga_id = event['saga_id']
            step_index = event['step_index']
            
            coordinator.execute_step(saga_id, step_index)
            
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Step {step_index} executed successfully'
                })
            }
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({
                    'error': 'Invalid action',
                    'supported_actions': ['start_saga', 'execute_step']
                })
            }
        
    except Exception as e:
        logger.error(f"Error in saga coordinator: {str(e)}")
        return {
            'statusCode': 500,
            'body': json.dumps({
                'error': 'Failed to coordinate saga',
                'message': str(e)
            })
        } 