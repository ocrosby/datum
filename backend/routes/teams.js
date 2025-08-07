const express = require('express');
const router = express.Router();
const AWS = require('aws-sdk');

const dynamodb = new AWS.DynamoDB.DocumentClient({
  region: process.env.AWS_REGION || 'us-east-1'
});

// Get all teams with optional filters
router.get('/', async (req, res) => {
  try {
    const { organization, division, gender, conference, active } = req.query;
    
    let params = {
      TableName: process.env.TEAM_METADATA_TABLE || 'ncaa-soccer-etl-team-metadata',
      ScanIndexForward: true
    };

    // Apply filters
    if (organization) {
      params.IndexName = 'organization-division-gender-index';
      params.KeyConditionExpression = 'organization = :org';
      params.ExpressionAttributeValues = { ':org': organization };
      
      if (division) {
        params.KeyConditionExpression += ' AND division = :div';
        params.ExpressionAttributeValues[':div'] = division;
        
        if (gender) {
          params.FilterExpression = '#gender = :gender';
          params.ExpressionAttributeNames = { '#gender': 'gender' };
          params.ExpressionAttributeValues[':gender'] = gender;
        }
      }
    } else if (conference) {
      params.IndexName = 'conference-organization-index';
      params.KeyConditionExpression = 'conference = :conf';
      params.ExpressionAttributeValues = { ':conf': conference };
    }

    const result = await dynamodb.query(params).promise();
    
    let teams = result.Items || [];
    
    // Apply active filter if specified
    if (active !== undefined) {
      const isActive = active === 'true';
      teams = teams.filter(team => team.active === isActive);
    }

    res.json({
      teams,
      total_teams: teams.length,
      filters: { organization, division, gender, conference, active }
    });

  } catch (error) {
    console.error('Error fetching teams:', error);
    res.status(500).json({
      error: 'Failed to fetch teams',
      message: error.message
    });
  }
});

// Get team by ID
router.get('/:teamId', async (req, res) => {
  try {
    const { teamId } = req.params;
    
    const params = {
      TableName: process.env.TEAM_METADATA_TABLE || 'ncaa-soccer-etl-team-metadata',
      Key: { team_id: teamId }
    };

    const result = await dynamodb.get(params).promise();
    
    if (!result.Item) {
      return res.status(404).json({
        error: 'Team not found',
        message: `No team found with ID: ${teamId}`
      });
    }

    res.json(result.Item);

  } catch (error) {
    console.error('Error fetching team:', error);
    res.status(500).json({
      error: 'Failed to fetch team',
      message: error.message
    });
  }
});

// Search teams by name
router.get('/search/:query', async (req, res) => {
  try {
    const { query } = req.params;
    const { organization } = req.query;
    
    let params = {
      TableName: process.env.TEAM_METADATA_TABLE || 'ncaa-soccer-etl-team-metadata',
      IndexName: 'team_name-index',
      KeyConditionExpression: 'begins_with(team_name, :name)',
      ExpressionAttributeValues: { ':name': query }
    };

    if (organization) {
      params.FilterExpression = 'organization = :org';
      params.ExpressionAttributeValues[':org'] = organization;
    }

    const result = await dynamodb.query(params).promise();
    
    res.json({
      teams: result.Items || [],
      total_teams: result.Items ? result.Items.length : 0,
      query,
      organization
    });

  } catch (error) {
    console.error('Error searching teams:', error);
    res.status(500).json({
      error: 'Failed to search teams',
      message: error.message
    });
  }
});

// Get organizations
router.get('/organizations/list', async (req, res) => {
  try {
    const params = {
      TableName: process.env.TEAM_METADATA_TABLE || 'ncaa-soccer-etl-team-metadata',
      IndexName: 'organization-division-gender-index',
      ProjectionExpression: 'organization',
      ScanIndexForward: true
    };

    const result = await dynamodb.scan(params).promise();
    
    const organizations = [...new Set(result.Items.map(item => item.organization))].sort();
    
    res.json({
      organizations,
      total_organizations: organizations.length
    });

  } catch (error) {
    console.error('Error fetching organizations:', error);
    res.status(500).json({
      error: 'Failed to fetch organizations',
      message: error.message
    });
  }
});

// Get divisions for an organization
router.get('/organizations/:organization/divisions', async (req, res) => {
  try {
    const { organization } = req.params;
    
    const params = {
      TableName: process.env.TEAM_METADATA_TABLE || 'ncaa-soccer-etl-team-metadata',
      IndexName: 'organization-division-gender-index',
      KeyConditionExpression: 'organization = :org',
      ExpressionAttributeValues: { ':org': organization },
      ProjectionExpression: 'division'
    };

    const result = await dynamodb.query(params).promise();
    
    const divisions = [...new Set(result.Items.map(item => item.division))].sort();
    
    res.json({
      organization,
      divisions,
      total_divisions: divisions.length
    });

  } catch (error) {
    console.error('Error fetching divisions:', error);
    res.status(500).json({
      error: 'Failed to fetch divisions',
      message: error.message
    });
  }
});

// Get conferences for an organization
router.get('/organizations/:organization/conferences', async (req, res) => {
  try {
    const { organization } = req.params;
    const { division } = req.query;
    
    let params = {
      TableName: process.env.TEAM_METADATA_TABLE || 'ncaa-soccer-etl-team-metadata',
      IndexName: 'conference-organization-index',
      KeyConditionExpression: 'organization = :org',
      ExpressionAttributeValues: { ':org': organization },
      ProjectionExpression: 'conference, division'
    };

    if (division) {
      params.FilterExpression = 'division = :div';
      params.ExpressionAttributeValues[':div'] = division;
    }

    const result = await dynamodb.query(params).promise();
    
    const conferences = [...new Set(result.Items.map(item => item.conference))].sort();
    
    res.json({
      organization,
      division,
      conferences,
      total_conferences: conferences.length
    });

  } catch (error) {
    console.error('Error fetching conferences:', error);
    res.status(500).json({
      error: 'Failed to fetch conferences',
      message: error.message
    });
  }
});

module.exports = router; 