const express = require('express');
const router = express.Router();
const AWS = require('aws-sdk');
const { validateDate } = require('../middleware/validation');

// Initialize AWS DynamoDB
const dynamodb = new AWS.DynamoDB.DocumentClient({
  region: process.env.AWS_REGION || 'us-east-1'
});

// In-memory cache for ultra-fast access
const memoryCache = new Map();
const CACHE_TTL = 5 * 60 * 1000; // 5 minutes

// Get calculation status
router.get('/status', async (req, res) => {
  try {
    const { date } = req.query;
    const calculationDate = date || new Date().toISOString().split('T')[0];
    
    const statusTable = process.env.CALCULATION_STATUS_TABLE || 'ncaa-soccer-etl-calculation-status';
    
    // Check for ongoing calculations
    const ongoingParams = {
      TableName: statusTable,
      KeyConditionExpression: 'calculation_date = :date',
      FilterExpression: '#status = :status',
      ExpressionAttributeNames: {
        '#status': 'status'
      },
      ExpressionAttributeValues: {
        ':date': calculationDate,
        ':status': 'in_progress'
      }
    };

    const ongoingResult = await dynamodb.query(ongoingParams).promise();
    
    // Check for completed calculations
    const completedParams = {
      TableName: statusTable,
      KeyConditionExpression: 'calculation_date = :date',
      FilterExpression: '#status = :status',
      ExpressionAttributeNames: {
        '#status': 'status'
      },
      ExpressionAttributeValues: {
        ':date': calculationDate,
        ':status': 'completed'
      },
      ScanIndexForward: false, // Get most recent first
      Limit: 1
    };

    const completedResult = await dynamodb.query(completedParams).promise();
    
    const status = {
      calculation_date: calculationDate,
      has_ongoing_calculation: ongoingResult.Items.length > 0,
      has_completed_calculation: completedResult.Items.length > 0,
      ongoing_calculation: ongoingResult.Items[0] || null,
      latest_completed_calculation: completedResult.Items[0] || null
    };

    res.json(status);

  } catch (error) {
    console.error('Error fetching calculation status:', error);
    res.status(500).json({
      error: 'Failed to fetch calculation status',
      message: error.message
    });
  }
});

// Get RPI rankings with organization and metadata filtering
router.get('/rankings', async (req, res) => {
  try {
    const { date, organization, division, gender } = req.query;
    const calculationDate = date || new Date().toISOString().split('T')[0];
    
    // First check if there's an ongoing calculation
    const statusTable = process.env.CALCULATION_STATUS_TABLE || 'ncaa-soccer-etl-calculation-status';
    const ongoingParams = {
      TableName: statusTable,
      KeyConditionExpression: 'calculation_date = :date',
      FilterExpression: '#status = :status',
      ExpressionAttributeNames: {
        '#status': 'status'
      },
      ExpressionAttributeValues: {
        ':date': calculationDate,
        ':status': 'in_progress'
      }
    };

    const ongoingResult = await dynamodb.query(ongoingParams).promise();
    
    if (ongoingResult.Items.length > 0) {
      const ongoingCalc = ongoingResult.Items[0];
      return res.json({
        error: 'Calculation in progress',
        message: 'RPI calculation is currently in progress. Please try again in a few minutes.',
        calculation_id: ongoingCalc.calculation_id,
        start_time: ongoingCalc.start_time,
        matches_processed: ongoingCalc.matches_processed || 0,
        teams_calculated: ongoingCalc.teams_calculated || 0,
        status: 'in_progress'
      });
    }
    
    // Check memory cache first
    const cacheKey = `rankings_${calculationDate}_${organization || 'all'}_${division || 'all'}_${gender || 'all'}`;
    const cachedData = memoryCache.get(cacheKey);
    
    if (cachedData && (Date.now() - cachedData.timestamp) < CACHE_TTL) {
      logger.info('Serving from memory cache');
      return res.json(cachedData.data);
    }
    
    // Check DynamoDB cache
    const cacheTable = process.env.CACHE_TABLE || 'ncaa-soccer-etl-cache';
    const cacheKeyDynamo = `rpi_calculation_${calculationDate}`;
    
    try {
      const cacheResponse = await dynamodb.get({
        TableName: cacheTable,
        Key: {
          cache_key: cacheKeyDynamo,
          cache_type: 'rpi_calculation'
        }
      }).promise();
      
      if (cacheResponse.Item) {
        const cacheTime = new Date(cacheResponse.Item.timestamp);
        // Cache valid for 1 hour
        if (Date.now() - cacheTime.getTime() < 60 * 60 * 1000) {
          let cachedResults = JSON.parse(cacheResponse.Item.data);
          
          // Apply filters if specified
          if (organization || division || gender) {
            cachedResults = cachedResults.filter(team => {
              if (organization && team.organization !== organization) return false;
              if (division && team.division !== division) return false;
              if (gender && team.gender !== gender) return false;
              return true;
            });
          }
          
          // Store in memory cache for ultra-fast access
          memoryCache.set(cacheKey, {
            data: {
              rankings: cachedResults,
              calculation_date: calculationDate,
              total_teams: cachedResults.length,
              cached: true,
              filters: { organization, division, gender }
            },
            timestamp: Date.now()
          });
          
          logger.info('Serving from DynamoDB cache');
          return res.json({
            rankings: cachedResults,
            calculation_date: calculationDate,
            total_teams: cachedResults.length,
            cached: true,
            filters: { organization, division, gender }
          });
        }
      }
    } catch (cacheError) {
      logger.warn('Cache lookup failed:', cacheError.message);
    }
    
    // Fallback to main table
    const params = {
      TableName: process.env.RPI_TABLE || 'ncaa-soccer-etl-rpi-calculations',
      KeyConditionExpression: 'calculation_date = :date',
      ExpressionAttributeValues: {
        ':date': calculationDate
      },
      ScanIndexForward: true // Sort by rank (ascending)
    };

    const result = await dynamodb.query(params).promise();
    
    if (!result.Items || result.Items.length === 0) {
      // Try to get the most recent data if no data for requested date
      const recentParams = {
        TableName: process.env.RPI_TABLE || 'ncaa-soccer-etl-rpi-calculations',
        IndexName: 'calculation_date-index',
        KeyConditionExpression: 'calculation_date <= :date',
        ExpressionAttributeValues: {
          ':date': calculationDate
        },
        ScanIndexForward: false, // Get most recent first
        Limit: 1
      };

      const recentResult = await dynamodb.query(recentParams).promise();
      
      if (recentResult.Items && recentResult.Items.length > 0) {
        const mostRecentDate = recentResult.Items[0].calculation_date;
        const fallbackParams = {
          TableName: process.env.RPI_TABLE || 'ncaa-soccer-etl-rpi-calculations',
          KeyConditionExpression: 'calculation_date = :date',
          ExpressionAttributeValues: {
            ':date': mostRecentDate
          },
          ScanIndexForward: true
        };

        const fallbackResult = await dynamodb.query(fallbackParams).promise();
        
        // Transform data for frontend
        let rankings = fallbackResult.Items.map(item => ({
          rank: item.rank,
          team: item.team_id,
          rpi: item.rpi,
          wp: item.wp,
          owp: item.owp,
          oowp: item.oowp,
          wins: item.wins,
          losses: item.losses,
          ties: item.ties,
          total_games: item.total_games,
          win_percentage: item.win_percentage,
          organization: item.organization || 'Unknown',
          division: item.division || 'Unknown',
          gender: item.gender || 'Unknown',
          conference: item.conference || 'Unknown',
          city: item.city || '',
          state: item.state || '',
          calculation_date: item.calculation_date
        }));

        // Apply filters if specified
        if (organization || division || gender) {
          rankings = rankings.filter(team => {
            if (organization && team.organization !== organization) return false;
            if (division && team.division !== division) return false;
            if (gender && team.gender !== gender) return false;
            return true;
          });
        }

        const responseData = {
          rankings,
          calculation_date: mostRecentDate,
          requested_date: calculationDate,
          fallback: true,
          filters: { organization, division, gender }
        };

        // Cache the response
        memoryCache.set(cacheKey, {
          data: responseData,
          timestamp: Date.now()
        });

        return res.json(responseData);
      }
      
      return res.status(404).json({
        error: 'No RPI data found',
        message: 'No rankings available for the requested date'
      });
    }

    // Transform data for frontend
    let rankings = result.Items.map(item => ({
      rank: item.rank,
      team: item.team_id,
      rpi: item.rpi,
      wp: item.wp,
      owp: item.owp,
      oowp: item.oowp,
      wins: item.wins,
      losses: item.losses,
      ties: item.ties,
      total_games: item.total_games,
      win_percentage: item.win_percentage,
      organization: item.organization || 'Unknown',
      division: item.division || 'Unknown',
      gender: item.gender || 'Unknown',
      conference: item.conference || 'Unknown',
      city: item.city || '',
      state: item.state || '',
      calculation_date: item.calculation_date
    }));

    // Apply filters if specified
    if (organization || division || gender) {
      rankings = rankings.filter(team => {
        if (organization && team.organization !== organization) return false;
        if (division && team.division !== division) return false;
        if (gender && team.gender !== gender) return false;
        return true;
      });
    }

    const responseData = {
      rankings,
      calculation_date: calculationDate,
      total_teams: rankings.length,
      filters: { organization, division, gender }
    };

    // Cache the response
    memoryCache.set(cacheKey, {
      data: responseData,
      timestamp: Date.now()
    });

    res.json(responseData);

  } catch (error) {
    console.error('Error fetching RPI rankings:', error);
    res.status(500).json({
      error: 'Failed to fetch RPI rankings',
      message: error.message
    });
  }
});

// Fast endpoint for top teams only
router.get('/rankings/top', async (req, res) => {
  try {
    const { limit = 25, date } = req.query;
    const calculationDate = date || new Date().toISOString().split('T')[0];
    
    // Check memory cache first
    const cacheKey = `top_rankings_${calculationDate}_${limit}`;
    const cachedData = memoryCache.get(cacheKey);
    
    if (cachedData && (Date.now() - cachedData.timestamp) < CACHE_TTL) {
      return res.json(cachedData.data);
    }
    
    const params = {
      TableName: process.env.RPI_TABLE || 'ncaa-soccer-etl-rpi-calculations',
      KeyConditionExpression: 'calculation_date = :date',
      ExpressionAttributeValues: {
        ':date': calculationDate
      },
      ScanIndexForward: true, // Sort by rank (ascending)
      Limit: parseInt(limit)
    };

    const result = await dynamodb.query(params).promise();
    
    if (!result.Items || result.Items.length === 0) {
      return res.status(404).json({
        error: 'No RPI data found',
        message: 'No rankings available for the requested date'
      });
    }

    // Transform data for frontend
    const rankings = result.Items.map(item => ({
      rank: item.rank,
      team: item.team_id,
      rpi: item.rpi,
      wp: item.wp,
      owp: item.owp,
      oowp: item.oowp,
      wins: item.wins,
      losses: item.losses,
      ties: item.ties,
      total_games: item.total_games,
      win_percentage: item.win_percentage,
      conference: item.conference || 'Unknown',
      division: item.division || 'D1'
    }));

    const responseData = {
      rankings,
      calculation_date: calculationDate,
      total_teams: rankings.length,
      limit: parseInt(limit)
    };

    // Cache the response
    memoryCache.set(cacheKey, {
      data: responseData,
      timestamp: Date.now()
    });

    res.json(responseData);

  } catch (error) {
    console.error('Error fetching top RPI rankings:', error);
    res.status(500).json({
      error: 'Failed to fetch top RPI rankings',
      message: error.message
    });
  }
});

// Get RPI history for a specific team
router.get('/team/:teamId/history', async (req, res) => {
  try {
    const { teamId } = req.params;
    const { startDate, endDate } = req.query;

    let filterExpression = 'team_id = :teamId';
    let expressionAttributeValues = { ':teamId': teamId };

    if (startDate && endDate) {
      filterExpression += ' AND calculation_date BETWEEN :startDate AND :endDate';
      expressionAttributeValues[':startDate'] = startDate;
      expressionAttributeValues[':endDate'] = endDate;
    }

    const params = {
      TableName: process.env.RPI_TABLE || 'ncaa-soccer-etl-rpi-calculations',
      IndexName: 'team_id-calculation_date-index',
      KeyConditionExpression: filterExpression,
      ExpressionAttributeValues: expressionAttributeValues,
      ScanIndexForward: true // Sort by date (ascending)
    };

    const result = await dynamodb.query(params).promise();

    const history = result.Items.map(item => ({
      date: item.calculation_date,
      rpi: item.rpi,
      rank: item.rank,
      wp: item.wp,
      owp: item.owp,
      oowp: item.oowp,
      wins: item.wins,
      losses: item.losses,
      ties: item.ties,
      total_games: item.total_games,
      win_percentage: item.win_percentage
    }));

    res.json({
      team_id: teamId,
      history,
      total_records: history.length
    });

  } catch (error) {
    console.error('Error fetching team RPI history:', error);
    res.status(500).json({
      error: 'Failed to fetch team RPI history',
      message: error.message
    });
  }
});

// Get available calculation dates
router.get('/dates', async (req, res) => {
  try {
    const params = {
      TableName: process.env.RPI_TABLE || 'ncaa-soccer-etl-rpi-calculations',
      IndexName: 'calculation_date-index',
      ProjectionExpression: 'calculation_date',
      ScanIndexForward: false // Get most recent first
    };

    const result = await dynamodb.scan(params).promise();
    
    const dates = [...new Set(result.Items.map(item => item.calculation_date))].sort().reverse();

    res.json({
      dates,
      total_dates: dates.length,
      latest_date: dates[0] || null
    });

  } catch (error) {
    console.error('Error fetching calculation dates:', error);
    res.status(500).json({
      error: 'Failed to fetch calculation dates',
      message: error.message
    });
  }
});

// Get RPI statistics
router.get('/stats', async (req, res) => {
  try {
    const { date } = req.query;
    const calculationDate = date || new Date().toISOString().split('T')[0];

    const params = {
      TableName: process.env.RPI_TABLE || 'ncaa-soccer-etl-rpi-calculations',
      KeyConditionExpression: 'calculation_date = :date',
      ExpressionAttributeValues: {
        ':date': calculationDate
      }
    };

    const result = await dynamodb.query(params).promise();

    if (!result.Items || result.Items.length === 0) {
      return res.status(404).json({
        error: 'No RPI data found',
        message: 'No statistics available for the requested date'
      });
    }

    const rpiValues = result.Items.map(item => item.rpi);
    const wpValues = result.Items.map(item => item.wp);
    const owpValues = result.Items.map(item => item.owp);
    const oowpValues = result.Items.map(item => item.oowp);

    const stats = {
      total_teams: result.Items.length,
      average_rpi: rpiValues.reduce((a, b) => a + b, 0) / rpiValues.length,
      average_wp: wpValues.reduce((a, b) => a + b, 0) / wpValues.length,
      average_owp: owpValues.reduce((a, b) => a + b, 0) / owpValues.length,
      average_oowp: oowpValues.reduce((a, b) => a + b, 0) / oowpValues.length,
      max_rpi: Math.max(...rpiValues),
      min_rpi: Math.min(...rpiValues),
      calculation_date: calculationDate
    };

    res.json(stats);

  } catch (error) {
    console.error('Error fetching RPI statistics:', error);
    res.status(500).json({
      error: 'Failed to fetch RPI statistics',
      message: error.message
    });
  }
});

// Clear cache endpoint (admin only)
router.post('/cache/clear', async (req, res) => {
  try {
    // Clear memory cache
    memoryCache.clear();
    
    // Clear DynamoDB cache
    const cacheTable = process.env.CACHE_TABLE || 'ncaa-soccer-etl-cache';
    const scanParams = {
      TableName: cacheTable,
      FilterExpression: 'cache_type = :cacheType',
      ExpressionAttributeValues: {
        ':cacheType': 'rpi_calculation'
      }
    };

    const result = await dynamodb.scan(scanParams).promise();
    
    if (result.Items.length > 0) {
      const deletePromises = result.Items.map(item => 
        dynamodb.delete({
          TableName: cacheTable,
          Key: {
            cache_key: item.cache_key,
            cache_type: item.cache_type
          }
        }).promise()
      );
      
      await Promise.all(deletePromises);
    }

    res.json({
      message: 'Cache cleared successfully',
      memory_cache_cleared: true,
      dynamodb_cache_cleared: result.Items.length
    });

  } catch (error) {
    console.error('Error clearing cache:', error);
    res.status(500).json({
      error: 'Failed to clear cache',
      message: error.message
    });
  }
});

// Get conference rankings
router.get('/conferences', async (req, res) => {
  try {
    const { date, division = 'D1' } = req.query;
    const calculationDate = date || new Date().toISOString().split('T')[0];
    
    // First check if there's an ongoing calculation
    const statusTable = process.env.CALCULATION_STATUS_TABLE || 'ncaa-soccer-etl-calculation-status';
    const ongoingParams = {
      TableName: statusTable,
      KeyConditionExpression: 'calculation_date = :date',
      FilterExpression: '#status = :status',
      ExpressionAttributeNames: {
        '#status': 'status'
      },
      ExpressionAttributeValues: {
        ':date': calculationDate,
        ':status': 'in_progress'
      }
    };

    const ongoingResult = await dynamodb.query(ongoingParams).promise();
    
    if (ongoingResult.Items.length > 0) {
      const ongoingCalc = ongoingResult.Items[0];
      return res.json({
        error: 'Calculation in progress',
        message: 'RPI calculation is currently in progress. Conference rankings will be available once complete.',
        calculation_id: ongoingCalc.calculation_id,
        status: 'in_progress'
      });
    }
    
    // Get team rankings for the date
    const teamParams = {
      TableName: process.env.RPI_TABLE || 'ncaa-soccer-etl-rpi-calculations',
      KeyConditionExpression: 'calculation_date = :date',
      ExpressionAttributeValues: {
        ':date': calculationDate
      },
      ScanIndexForward: true
    };

    const teamResult = await dynamodb.query(teamParams).promise();
    
    if (!teamResult.Items || teamResult.Items.length === 0) {
      return res.status(404).json({
        error: 'No RPI data found',
        message: 'No team rankings available for the requested date'
      });
    }

    // Group teams by conference and calculate conference statistics
    const conferenceStats = {};
    
    teamResult.Items.forEach(team => {
      const conference = team.conference || 'Unknown';
      const teamDivision = team.division || 'D1';
      
      // Filter by division if specified
      if (division && teamDivision !== division) {
        return;
      }
      
      if (!conferenceStats[conference]) {
        conferenceStats[conference] = {
          conference: conference,
          division: teamDivision,
          teams: [],
          total_rpi: 0,
          total_wp: 0,
          total_owp: 0,
          total_oowp: 0,
          total_wins: 0,
          total_losses: 0,
          total_ties: 0,
          total_games: 0,
          top_rank: Infinity,
          teams_count: 0
        };
      }
      
      const stats = conferenceStats[conference];
      stats.teams.push({
        team: team.team_id,
        rank: team.rank,
        rpi: team.rpi,
        wp: team.wp,
        owp: team.owp,
        oowp: team.oowp,
        wins: team.wins,
        losses: team.losses,
        ties: team.ties,
        total_games: team.total_games,
        win_percentage: team.win_percentage
      });
      
      stats.total_rpi += team.rpi;
      stats.total_wp += team.wp;
      stats.total_owp += team.owp;
      stats.total_oowp += team.oowp;
      stats.total_wins += team.wins;
      stats.total_losses += team.losses;
      stats.total_ties += team.ties;
      stats.total_games += team.total_games;
      stats.top_rank = Math.min(stats.top_rank, team.rank);
      stats.teams_count += 1;
    });

    // Calculate averages and additional metrics
    const conferenceRankings = Object.values(conferenceStats).map(conf => {
      const avg_rpi = conf.total_rpi / conf.teams_count;
      const avg_wp = conf.total_wp / conf.teams_count;
      const avg_owp = conf.total_owp / conf.teams_count;
      const avg_oowp = conf.total_oowp / conf.teams_count;
      const avg_win_percentage = conf.total_games > 0 
        ? ((conf.total_wins + 0.5 * conf.total_ties) / conf.total_games) * 100 
        : 0;
      
      // Calculate conference strength (weighted average of team ranks)
      const rank_sum = conf.teams.reduce((sum, team) => sum + team.rank, 0);
      const avg_rank = rank_sum / conf.teams_count;
      
      // Calculate teams in top 25, 50, 100
      const top_25_count = conf.teams.filter(team => team.rank <= 25).length;
      const top_50_count = conf.teams.filter(team => team.rank <= 50).length;
      const top_100_count = conf.teams.filter(team => team.rank <= 100).length;
      
      return {
        conference: conf.conference,
        division: conf.division,
        avg_rpi: parseFloat(avg_rpi.toFixed(4)),
        avg_wp: parseFloat(avg_wp.toFixed(4)),
        avg_owp: parseFloat(avg_owp.toFixed(4)),
        avg_oowp: parseFloat(avg_oowp.toFixed(4)),
        avg_win_percentage: parseFloat(avg_win_percentage.toFixed(1)),
        avg_rank: parseFloat(avg_rank.toFixed(1)),
        top_rank: conf.top_rank,
        teams_count: conf.teams_count,
        total_wins: conf.total_wins,
        total_losses: conf.total_losses,
        total_ties: conf.total_ties,
        total_games: conf.total_games,
        top_25_count,
        top_50_count,
        top_100_count,
        teams: conf.teams.sort((a, b) => a.rank - b.rank) // Sort teams by rank within conference
      };
    });

    // Sort conferences by average RPI (descending)
    conferenceRankings.sort((a, b) => b.avg_rpi - a.avg_rpi);

    // Add rank to each conference
    conferenceRankings.forEach((conf, index) => {
      conf.rank = index + 1;
    });

    const responseData = {
      conferences: conferenceRankings,
      calculation_date: calculationDate,
      division: division,
      total_conferences: conferenceRankings.length,
      total_teams: conferenceRankings.reduce((sum, conf) => sum + conf.teams_count, 0)
    };

    res.json(responseData);

  } catch (error) {
    console.error('Error fetching conference rankings:', error);
    res.status(500).json({
      error: 'Failed to fetch conference rankings',
      message: error.message
    });
  }
});

// Get conference details for a specific conference
router.get('/conferences/:conference', async (req, res) => {
  try {
    const { conference } = req.params;
    const { date, division = 'D1' } = req.query;
    const calculationDate = date || new Date().toISOString().split('T')[0];
    
    // Get team rankings for the date
    const teamParams = {
      TableName: process.env.RPI_TABLE || 'ncaa-soccer-etl-rpi-calculations',
      KeyConditionExpression: 'calculation_date = :date',
      ExpressionAttributeValues: {
        ':date': calculationDate
      },
      ScanIndexForward: true
    };

    const teamResult = await dynamodb.query(teamParams).promise();
    
    if (!teamResult.Items || teamResult.Items.length === 0) {
      return res.status(404).json({
        error: 'No RPI data found',
        message: 'No team rankings available for the requested date'
      });
    }

    // Filter teams by conference and division
    const conferenceTeams = teamResult.Items.filter(team => {
      const teamConference = team.conference || 'Unknown';
      const teamDivision = team.division || 'D1';
      return teamConference === conference && teamDivision === division;
    });

    if (conferenceTeams.length === 0) {
      return res.status(404).json({
        error: 'Conference not found',
        message: `No teams found for conference '${conference}' in division '${division}'`
      });
    }

    // Calculate conference statistics
    const total_rpi = conferenceTeams.reduce((sum, team) => sum + team.rpi, 0);
    const total_wp = conferenceTeams.reduce((sum, team) => sum + team.wp, 0);
    const total_owp = conferenceTeams.reduce((sum, team) => sum + team.owp, 0);
    const total_oowp = conferenceTeams.reduce((sum, team) => sum + team.oowp, 0);
    const total_wins = conferenceTeams.reduce((sum, team) => sum + team.wins, 0);
    const total_losses = conferenceTeams.reduce((sum, team) => sum + team.losses, 0);
    const total_ties = conferenceTeams.reduce((sum, team) => sum + team.ties, 0);
    const total_games = conferenceTeams.reduce((sum, team) => sum + team.total_games, 0);
    const rank_sum = conferenceTeams.reduce((sum, team) => sum + team.rank, 0);
    const top_rank = Math.min(...conferenceTeams.map(team => team.rank));

    const teams_count = conferenceTeams.length;
    const avg_rpi = total_rpi / teams_count;
    const avg_wp = total_wp / teams_count;
    const avg_owp = total_owp / teams_count;
    const avg_oowp = total_oowp / teams_count;
    const avg_rank = rank_sum / teams_count;
    const avg_win_percentage = total_games > 0 
      ? ((total_wins + 0.5 * total_ties) / total_games) * 100 
      : 0;

    // Calculate top teams counts
    const top_25_count = conferenceTeams.filter(team => team.rank <= 25).length;
    const top_50_count = conferenceTeams.filter(team => team.rank <= 50).length;
    const top_100_count = conferenceTeams.filter(team => team.rank <= 100).length;

    // Sort teams by rank
    const sortedTeams = conferenceTeams
      .map(team => ({
        team: team.team_id,
        rank: team.rank,
        rpi: team.rpi,
        wp: team.wp,
        owp: team.owp,
        oowp: team.oowp,
        wins: team.wins,
        losses: team.losses,
        ties: team.ties,
        total_games: team.total_games,
        win_percentage: team.win_percentage
      }))
      .sort((a, b) => a.rank - b.rank);

    const conferenceData = {
      conference: conference,
      division: division,
      calculation_date: calculationDate,
      avg_rpi: parseFloat(avg_rpi.toFixed(4)),
      avg_wp: parseFloat(avg_wp.toFixed(4)),
      avg_owp: parseFloat(avg_owp.toFixed(4)),
      avg_oowp: parseFloat(avg_oowp.toFixed(4)),
      avg_win_percentage: parseFloat(avg_win_percentage.toFixed(1)),
      avg_rank: parseFloat(avg_rank.toFixed(1)),
      top_rank: top_rank,
      teams_count: teams_count,
      total_wins: total_wins,
      total_losses: total_losses,
      total_ties: total_ties,
      total_games: total_games,
      top_25_count,
      top_50_count,
      top_100_count,
      teams: sortedTeams
    };

    res.json(conferenceData);

  } catch (error) {
    console.error('Error fetching conference details:', error);
    res.status(500).json({
      error: 'Failed to fetch conference details',
      message: error.message
    });
  }
});

module.exports = router; 