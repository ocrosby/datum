import React, { useState } from 'react';
import { useParams, useSearchParams, Link } from 'react-router-dom';
import { 
  ArrowLeftIcon,
  TrophyIcon, 
  UsersIcon, 
  ChartBarIcon, 
  StarIcon,
  TrendingUpIcon,
  TrendingDownIcon,
  ChevronUpIcon,
  ChevronDownIcon
} from '@heroicons/react/24/outline';
import { useQuery } from 'react-query';
import { fetchConferenceDetails } from '../services/api';
import { useRPI } from '../contexts/RPIContext';
import CalculationStatus from '../components/CalculationStatus';

const ConferenceDetails = () => {
  const { conference } = useParams();
  const [searchParams] = useSearchParams();
  const { selectedDate } = useRPI();
  const division = searchParams.get('division') || 'D1';
  const [sortConfig, setSortConfig] = useState({ key: 'rank', direction: 'asc' });

  const { data: conferenceData, isLoading, error } = useQuery(
    ['conference-details', conference, selectedDate, division],
    () => fetchConferenceDetails(conference, selectedDate, division),
    {
      refetchInterval: 30000, // Refresh every 30 seconds
      staleTime: 0,
      cacheTime: 5 * 60 * 1000,
    }
  );

  const handleSort = (key) => {
    setSortConfig(prevConfig => ({
      key,
      direction: prevConfig.key === key && prevConfig.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const getSortIcon = (key) => {
    if (sortConfig.key !== key) {
      return <ChevronUpIcon className="h-4 w-4 text-gray-400" />;
    }
    
    return sortConfig.direction === 'asc' 
      ? <ChevronUpIcon className="h-4 w-4 text-primary-600" />
      : <ChevronDownIcon className="h-4 w-4 text-primary-600" />;
  };

  const sortedTeams = React.useMemo(() => {
    if (!conferenceData?.teams) return [];
    
    const sorted = [...conferenceData.teams];
    sorted.sort((a, b) => {
      let aValue = a[sortConfig.key];
      let bValue = b[sortConfig.key];
      
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        return sortConfig.direction === 'asc' ? aValue - bValue : bValue - aValue;
      }
      
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        return sortConfig.direction === 'asc' 
          ? aValue.localeCompare(bValue) 
          : bValue.localeCompare(aValue);
      }
      
      return 0;
    });
    
    return sorted;
  }, [conferenceData?.teams, sortConfig]);

  const getStrengthColor = (rpi) => {
    if (rpi >= 0.6000) return 'text-success-600';
    if (rpi >= 0.5500) return 'text-warning-600';
    if (rpi >= 0.5000) return 'text-info-600';
    return 'text-gray-600';
  };

  const getStrengthLabel = (rpi) => {
    if (rpi >= 0.6000) return 'Elite';
    if (rpi >= 0.5500) return 'Strong';
    if (rpi >= 0.5000) return 'Average';
    return 'Weak';
  };

  if (isLoading) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="animate-pulse">
          <div className="h-8 bg-gray-200 rounded w-1/4 mb-6"></div>
          <div className="space-y-3">
            {[...Array(10)].map((_, i) => (
              <div key={i} className="h-12 bg-gray-200 rounded"></div>
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
          <h3 className="text-red-800 font-medium">Error Loading Conference Details</h3>
          <p className="text-red-600 mt-1">{error.message}</p>
        </div>
      </div>
    );
  }

  if (!conferenceData) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <h3 className="text-yellow-800 font-medium">Conference Not Found</h3>
          <p className="text-yellow-600 mt-1">No data available for this conference.</p>
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
        <div className="flex items-center mb-4">
          <Link
            to="/conferences"
            className="inline-flex items-center text-sm text-gray-500 hover:text-gray-700 mr-4"
          >
            <ArrowLeftIcon className="h-4 w-4 mr-1" />
            Back to Conferences
          </Link>
        </div>
        
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          {conferenceData.conference}
        </h1>
        <p className="text-gray-600">
          {conferenceData.division} • {conferenceData.teams_count} Teams
        </p>
      </div>

      {/* Conference Stats */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <ChartBarIcon className="h-8 w-8 text-blue-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Average RPI</p>
              <p className="text-2xl font-bold text-gray-900">
                {conferenceData.avg_rpi.toFixed(4)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <TrophyIcon className="h-8 w-8 text-yellow-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Average Rank</p>
              <p className="text-2xl font-bold text-gray-900">
                {conferenceData.avg_rank.toFixed(1)}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <StarIcon className="h-8 w-8 text-purple-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Top Rank</p>
              <p className="text-2xl font-bold text-gray-900">
                #{conferenceData.top_rank}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
          <div className="flex items-center">
            <UsersIcon className="h-8 w-8 text-green-500" />
            <div className="ml-3">
              <p className="text-sm font-medium text-gray-500">Win Percentage</p>
              <p className="text-2xl font-bold text-gray-900">
                {conferenceData.avg_win_percentage.toFixed(1)}%
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Top Teams Summary */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Conference Strength</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">{conferenceData.top_25_count}</div>
            <div className="text-sm text-gray-600">Top 25 Teams</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">{conferenceData.top_50_count}</div>
            <div className="text-sm text-gray-600">Top 50 Teams</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-purple-600">{conferenceData.top_100_count}</div>
            <div className="text-sm text-gray-600">Top 100 Teams</div>
          </div>
        </div>
      </div>

      {/* Team Rankings */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Team Rankings</h2>
          <p className="text-sm text-gray-600 mt-1">
            {conferenceData.teams_count} teams sorted by RPI rank
          </p>
        </div>
        
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
                  onClick={() => handleSort('team')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Team</span>
                    {getSortIcon('team')}
                  </div>
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('rpi')}
                >
                  <div className="flex items-center space-x-1">
                    <span>RPI</span>
                    {getSortIcon('rpi')}
                  </div>
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('wp')}
                >
                  <div className="flex items-center space-x-1">
                    <span>WP</span>
                    {getSortIcon('wp')}
                  </div>
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('owp')}
                >
                  <div className="flex items-center space-x-1">
                    <span>OWP</span>
                    {getSortIcon('owp')}
                  </div>
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('oowp')}
                >
                  <div className="flex items-center space-x-1">
                    <span>OOWP</span>
                    {getSortIcon('oowp')}
                  </div>
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('win_percentage')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Win %</span>
                    {getSortIcon('win_percentage')}
                  </div>
                </th>
                <th
                  scope="col"
                  className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100"
                  onClick={() => handleSort('total_games')}
                >
                  <div className="flex items-center space-x-1">
                    <span>Record</span>
                    {getSortIcon('total_games')}
                  </div>
                </th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {sortedTeams.map((team) => (
                <tr key={team.team} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    <div className="flex items-center">
                      {team.rank <= 25 && (
                        <StarIcon className="h-4 w-4 text-yellow-500 mr-2" />
                      )}
                      {team.rank}
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <Link
                      to={`/team/${team.team}`}
                      className="text-sm font-medium text-primary-600 hover:text-primary-900 hover:underline"
                    >
                      {team.team}
                    </Link>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center space-x-2">
                      <span className={`text-sm font-medium ${getStrengthColor(team.rpi)}`}>
                        {team.rpi.toFixed(4)}
                      </span>
                      <span className={`text-xs px-2 py-1 rounded-full ${getStrengthColor(team.rpi)} bg-opacity-10`}>
                        {getStrengthLabel(team.rpi)}
                      </span>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {team.wp.toFixed(4)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {team.owp.toFixed(4)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {team.oowp.toFixed(4)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {(team.win_percentage * 100).toFixed(1)}%
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    {team.wins}-{team.losses}-{team.ties} ({team.total_games})
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {/* Empty State */}
        {sortedTeams.length === 0 && (
          <div className="text-center py-12">
            <UsersIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No teams found</h3>
            <p className="mt-1 text-sm text-gray-500">
              No team data available for this conference.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ConferenceDetails; 