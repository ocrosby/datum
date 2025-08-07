import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  TrophyIcon, 
  UsersIcon, 
  ChartBarIcon, 
  ChevronRightIcon,
  StarIcon,
  TrendingUpIcon,
  TrendingDownIcon
} from '@heroicons/react/24/outline';
import { useQuery } from 'react-query';
import { fetchConferenceRankings } from '../services/api';
import { useRPI } from '../contexts/RPIContext';
import CalculationStatus from '../components/CalculationStatus';

const Conferences = () => {
  const { selectedDate } = useRPI();
  const [selectedDivision, setSelectedDivision] = useState('D1');
  const [sortConfig, setSortConfig] = useState({ key: 'avg_rpi', direction: 'desc' });

  const { data: conferenceData, isLoading, error, refetch } = useQuery(
    ['conference-rankings', selectedDate, selectedDivision],
    () => fetchConferenceRankings(selectedDate, selectedDivision),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
      staleTime: 0,
      cacheTime: 5 * 60 * 1000,
    }
  );

  const handleSort = (key) => {
    setSortConfig(prevConfig => ({
      key,
      direction: prevConfig.key === key && prevConfig.direction === 'desc' ? 'asc' : 'desc'
    }));
  };

  const getSortIcon = (key) => {
    if (sortConfig.key !== key) {
      return null;
    }
    
    return sortConfig.direction === 'desc' 
      ? <TrendingDownIcon className="h-4 w-4 text-primary-600" />
      : <TrendingUpIcon className="h-4 w-4 text-primary-600" />;
  };

  const sortedConferences = React.useMemo(() => {
    if (!conferenceData?.conferences) return [];
    
    const sorted = [...conferenceData.conferences];
    sorted.sort((a, b) => {
      let aValue = a[sortConfig.key];
      let bValue = b[sortConfig.key];
      
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortConfig.direction === 'desc' ? bValue - aValue : aValue - bValue;
      }
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortConfig.direction === 'desc' 
          ? bValue.localeCompare(aValue) 
          : aValue.localeCompare(bValue);
      }
      
      return 0;
    });
    
    return sorted;
  }, [conferenceData?.conferences, sortConfig]);

  const getStrengthColor = (avgRpi) => {
    if (avgRpi >= 0.6000) return 'text-success-600';
    if (avgRpi >= 0.5500) return 'text-warning-600';
    if (avgRpi >= 0.5000) return 'text-info-600';
    return 'text-gray-600';
  };

  const getStrengthLabel = (avgRpi) => {
    if (avgRpi >= 0.6000) return 'Elite';
    if (avgRpi >= 0.5500) return 'Strong';
    if (avgRpi >= 0.5000) return 'Average';
    return 'Weak';
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="space-y-3">
            {[...Array(10)].map((_, i) => (
              <div key={i} className="h-16 bg-gray-200 rounded"></div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <h3 className="text-red-800 font-medium">Error Loading Conference Rankings</h3>
          <p className="text-red-600 mt-1">{error.message}</p>
        </div>
      </div>
    );
  }

  if (conferenceData?.error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-warning-50 border border-warning-200 rounded-lg p-4">
          <h3 className="text-warning-800 font-medium">Calculation in Progress</h3>
          <p className="text-warning-600 mt-1">{conferenceData.message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Calculation Status */}
      <CalculationStatus />
      
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Conference Rankings</h1>
        <p className="text-gray-600">
          Conference strength rankings based on average RPI values
        </p>
      </div>

      {/* Division Filter */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="flex items-center justify-between">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Division
            </label>
            <select
              value={selectedDivision}
              onChange={(e) => setSelectedDivision(e.target.value)}
              className="px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="D1">Division I</option>
              <option value="D2">Division II</option>
              <option value="D3">Division III</option>
              <option value="NAIA">NAIA</option>
            </select>
          </div>
          
          {conferenceData && (
            <div className="text-right">
              <div className="text-sm text-gray-600">
                {conferenceData.total_conferences} Conferences
              </div>
              <div className="text-sm text-gray-600">
                {conferenceData.total_teams} Teams
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Conference Rankings */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="overflow-x-auto">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('rank')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Rank</span>
                    {getSortIcon('rank')}
                  </div>
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('conference')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Conference</span>
                    {getSortIcon('conference')}
                  </div>
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('avg_rpi')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Avg RPI</span>
                    {getSortIcon('avg_rpi')}
                  </div>
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('avg_rank')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Avg Rank</span>
                    {getSortIcon('avg_rank')}
                  </div>
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('teams_count')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Teams</span>
                    {getSortIcon('teams_count')}
                  </div>
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('top_rank')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Top Rank</span>
                    {getSortIcon('top_rank')}
                  </div>
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider"
                >
                  <span>Top Teams</span>
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('avg_win_percentage')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Win %</span>
                    {getSortIcon('avg_win_percentage')}
                  </div>
                </th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                  <span>Actions</span>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sortedConferences.map((conference) => (
                <tr key={conference.conference} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    <div className="flex items-center">
                      {conference.rank <= 3 && (
                        <TrophyIcon className="h-4 w-4 text-yellow-500 mr-2" />
                      )}
                      {conference.rank}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          {conference.conference}
                        </div>
                        <div className="text-sm text-gray-500">
                          {conference.division}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      <span className={`text-sm font-medium ${getStrengthColor(conference.avg_rpi)}`}>
                        {conference.avg_rpi.toFixed(4)}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded-full ${getStrengthColor(conference.avg_rpi)} bg-opacity-10`}>
                        {getStrengthLabel(conference.avg_rpi)}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {conference.avg_rank.toFixed(1)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center">
                      <UsersIcon className="h-4 w-4 text-gray-400 mr-1" />
                      {conference.teams_count}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center">
                      <StarIcon className="h-4 w-4 text-yellow-500 mr-1" />
                      #{conference.top_rank}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center space-x-2">
                      <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded">
                        Top 25: {conference.top_25_count}
                      </span>
                      <span className="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                        Top 50: {conference.top_50_count}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {conference.avg_win_percentage.toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <Link
                      to={`/conferences/${encodeURIComponent(conference.conference)}?division=${selectedDivision}`}
                      className="inline-flex items-center px-3 py-1.5 border border-gray-300 text-xs font-medium rounded text-gray-700 bg-white hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500"
                    >
                      View Details
                      <ChevronRightIcon className="h-4 w-4 ml-1" />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Empty State */}
        {sortedConferences.length === 0 && (
          <div className="text-center py-12">
            <ChartBarIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No conferences found</h3>
            <p className="mt-1 text-sm text-gray-500">
              No conference data available for the selected criteria.
            </p>
          </div>
        )}
      </div>

      {/* Summary Stats */}
      {conferenceData && (
        <div className="mt-6 grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center">
              <TrophyIcon className="h-8 w-8 text-yellow-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Strongest Conference</p>
                <p className="text-lg font-semibold text-gray-900">
                  {sortedConferences[0]?.conference || 'N/A'}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center">
              <ChartBarIcon className="h-8 w-8 text-blue-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Avg Conference RPI</p>
                <p className="text-lg font-semibold text-gray-900">
                  {(sortedConferences.reduce((sum, conf) => sum + conf.avg_rpi, 0) / sortedConferences.length).toFixed(4)}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center">
              <UsersIcon className="h-8 w-8 text-green-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Total Teams</p>
                <p className="text-lg font-semibold text-gray-900">
                  {conferenceData.total_teams}
                </p>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-4">
            <div className="flex items-center">
              <StarIcon className="h-8 w-8 text-purple-500" />
              <div className="ml-3">
                <p className="text-sm font-medium text-gray-500">Top 25 Teams</p>
                <p className="text-lg font-semibold text-gray-900">
                  {sortedConferences.reduce((sum, conf) => sum + conf.top_25_count, 0)}
                </p>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Conferences; 