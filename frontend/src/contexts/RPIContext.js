import React, { createContext, useContext, useReducer, useEffect } from 'react';
import { useQuery } from 'react-query';
import { fetchRPIData, fetchTeamDetails, fetchMatches } from '../services/api';

const RPIContext = createContext();

const initialState = {
  rankings: [],
  selectedTeam: null,
  selectedDate: new Date().toISOString().split('T')[0],
  isLoading: false,
  error: null,
  lastUpdated: null,
  filters: {
    conference: 'all',
    division: 'all',
    searchTerm: '',
  },
  autoRefresh: true,
  refreshInterval: 30000, // 30 seconds
};

function rpiReducer(state, action) {
  switch (action.type) {
    case 'SET_RANKINGS':
      return {
        ...state,
        rankings: action.payload,
        lastUpdated: new Date().toISOString(),
        isLoading: false,
        error: null,
      };
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
        isLoading: false,
      };
    case 'SET_SELECTED_TEAM':
      return {
        ...state,
        selectedTeam: action.payload,
      };
    case 'SET_SELECTED_DATE':
      return {
        ...state,
        selectedDate: action.payload,
      };
    case 'SET_FILTERS':
      return {
        ...state,
        filters: {
          ...state.filters,
          ...action.payload,
        },
      };
    case 'SET_AUTO_REFRESH':
      return {
        ...state,
        autoRefresh: action.payload,
      };
    case 'SET_REFRESH_INTERVAL':
      return {
        ...state,
        refreshInterval: action.payload,
      };
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };
    default:
      return state;
  }
}

export function RPIProvider({ children }) {
  const [state, dispatch] = useReducer(rpiReducer, initialState);

  // Fetch RPI data with auto-refresh
  const {
    data: rpiData,
    isLoading: rpiLoading,
    error: rpiError,
    refetch: refetchRPI,
  } = useQuery(
    ['rpi-data', state.selectedDate],
    () => fetchRPIData(state.selectedDate),
    {
      refetchInterval: state.autoRefresh ? state.refreshInterval : false,
      refetchIntervalInBackground: true,
      staleTime: 0, // Always consider data stale for real-time updates
      cacheTime: 5 * 60 * 1000, // 5 minutes
      onSuccess: (data) => {
        dispatch({ type: 'SET_RANKINGS', payload: data });
      },
      onError: (error) => {
        dispatch({ type: 'SET_ERROR', payload: error.message });
      },
    }
  );

  // Update loading state
  useEffect(() => {
    dispatch({ type: 'SET_LOADING', payload: rpiLoading });
  }, [rpiLoading]);

  // Update error state
  useEffect(() => {
    if (rpiError) {
      dispatch({ type: 'SET_ERROR', payload: rpiError.message });
    }
  }, [rpiError]);

  // Filter rankings based on current filters
  const filteredRankings = React.useMemo(() => {
    let filtered = state.rankings;

    // Apply search filter
    if (state.filters.searchTerm) {
      filtered = filtered.filter(team =>
        team.team.toLowerCase().includes(state.filters.searchTerm.toLowerCase())
      );
    }

    // Apply conference filter
    if (state.filters.conference !== 'all') {
      filtered = filtered.filter(team => team.conference === state.filters.conference);
    }

    // Apply division filter
    if (state.filters.division !== 'all') {
      filtered = filtered.filter(team => team.division === state.filters.division);
    }

    return filtered;
  }, [state.rankings, state.filters]);

  const value = {
    ...state,
    rankings: filteredRankings,
    allRankings: state.rankings,
    refetchRPI,
    dispatch,
  };

  return <RPIContext.Provider value={value}>{children}</RPIContext.Provider>;
}

export function useRPI() {
  const context = useContext(RPIContext);
  if (!context) {
    throw new Error('useRPI must be used within an RPIProvider');
  }
  return context;
} 