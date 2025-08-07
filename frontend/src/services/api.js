import axios from 'axios';

// Create axios instance with default configuration
const api = axios.create({
  baseURL: process.env.REACT_APP_API_URL || 'http://localhost:3001/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for adding auth tokens
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized access
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

// RPI Data API
export const fetchRPIData = async (date = null) => {
  try {
    const params = date ? `?date=${date}` : '';
    const response = await api.get(`/rpi/rankings${params}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching RPI data:', error);
    throw error;
  }
};

export const fetchConferenceRankings = async (date = null, division = 'D1') => {
  try {
    const params = new URLSearchParams();
    if (date) params.append('date', date);
    if (division) params.append('division', division);
    
    const response = await api.get(`/rpi/conferences?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching conference rankings:', error);
    throw error;
  }
};

export const fetchConferenceDetails = async (conference, date = null, division = 'D1') => {
  try {
    const params = new URLSearchParams();
    if (date) params.append('date', date);
    if (division) params.append('division', division);
    
    const response = await api.get(`/rpi/conferences/${encodeURIComponent(conference)}?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching conference details:', error);
    throw error;
  }
};

export const fetchTeamDetails = async (teamId) => {
  try {
    const response = await api.get(`/teams/${teamId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching team details:', error);
    throw new Error('Failed to fetch team details');
  }
};

export const fetchTeamHistory = async (teamId, startDate, endDate) => {
  try {
    const response = await api.get(`/teams/${teamId}/history`, {
      params: { startDate, endDate },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching team history:', error);
    throw new Error('Failed to fetch team history');
  }
};

// Matches API
export const fetchMatches = async (params = {}) => {
  try {
    const response = await api.get('/matches', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching matches:', error);
    throw new Error('Failed to fetch matches');
  }
};

export const fetchMatchDetails = async (matchId) => {
  try {
    const response = await api.get(`/matches/${matchId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching match details:', error);
    throw new Error('Failed to fetch match details');
  }
};

// Analytics API
export const fetchAnalytics = async (params = {}) => {
  try {
    const response = await api.get('/analytics', { params });
    return response.data;
  } catch (error) {
    console.error('Error fetching analytics:', error);
    throw new Error('Failed to fetch analytics');
  }
};

export const fetchConferenceStats = async () => {
  try {
    const response = await api.get('/analytics/conferences');
    return response.data;
  } catch (error) {
    console.error('Error fetching conference stats:', error);
    throw new Error('Failed to fetch conference statistics');
  }
};

export const fetchTrendingTeams = async (days = 7) => {
  try {
    const response = await api.get('/analytics/trending', {
      params: { days },
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching trending teams:', error);
    throw new Error('Failed to fetch trending teams');
  }
};

// Settings API
export const fetchUserSettings = async () => {
  try {
    const response = await api.get('/settings');
    return response.data;
  } catch (error) {
    console.error('Error fetching user settings:', error);
    throw new Error('Failed to fetch user settings');
  }
};

export const updateUserSettings = async (settings) => {
  try {
    const response = await api.put('/settings', settings);
    return response.data;
  } catch (error) {
    console.error('Error updating user settings:', error);
    throw new Error('Failed to update user settings');
  }
};

// System Status API
export const fetchSystemStatus = async () => {
  try {
    const response = await api.get('/status');
    return response.data;
  } catch (error) {
    console.error('Error fetching system status:', error);
    throw new Error('Failed to fetch system status');
  }
};

// WebSocket connection for real-time updates
export const createWebSocketConnection = (onMessage, onError) => {
  const wsUrl = process.env.REACT_APP_WS_URL || 'ws://localhost:3001/ws';
  const ws = new WebSocket(wsUrl);

  ws.onopen = () => {
    console.log('WebSocket connected');
  };

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      onMessage(data);
    } catch (error) {
      console.error('Error parsing WebSocket message:', error);
    }
  };

  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
    onError(error);
  };

  ws.onclose = () => {
    console.log('WebSocket disconnected');
    // Attempt to reconnect after 5 seconds
    setTimeout(() => {
      createWebSocketConnection(onMessage, onError);
    }, 5000);
  };

  return ws;
};

// Mock data for development (remove in production)
export const getMockRPIData = () => {
  return [
    {
      rank: 1,
      team: 'Stanford',
      conference: 'Pac-12',
      division: 'D1',
      rpi: 0.8234,
      wp: 0.8500,
      owp: 0.7200,
      oowp: 0.6500,
      wins: 15,
      losses: 2,
      ties: 1,
      total_games: 18,
      win_percentage: 0.8611,
    },
    {
      rank: 2,
      team: 'North Carolina',
      conference: 'ACC',
      division: 'D1',
      rpi: 0.8156,
      wp: 0.8333,
      owp: 0.7300,
      oowp: 0.6800,
      wins: 14,
      losses: 2,
      ties: 2,
      total_games: 18,
      win_percentage: 0.8333,
    },
    {
      rank: 3,
      team: 'UCLA',
      conference: 'Pac-12',
      division: 'D1',
      rpi: 0.7989,
      wp: 0.8000,
      owp: 0.7500,
      oowp: 0.6200,
      wins: 13,
      losses: 3,
      ties: 2,
      total_games: 18,
      win_percentage: 0.7778,
    },
    // Add more mock data as needed
  ];
};

export default api; 