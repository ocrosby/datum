import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  TrendingUpIcon, 
  TrendingDownIcon, 
  MinusIcon,
  EyeIcon,
  CalendarIcon,
  ChartBarIcon
} from '@heroicons/react/24/outline';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, BarChart, Bar } from 'recharts';
import { useRPI } from '../contexts/RPIContext';
import { fetchTrendingTeams, fetchConferenceStats } from '../services/api';
import { useQuery } from 'react-query';

const Dashboard = () => {
  const { rankings, isLoading, error, lastUpdated } = useRPI();
  const [selectedTimeframe, setSelectedTimeframe] = useState('7d');

  // Fetch trending teams
  const { data: trendingTeams } = useQuery(
    ['trending-teams', selectedTimeframe],
    () => fetchTrendingTeams(selectedTimeframe === '7d' ? 7 : 30),
    { staleTime: 5 * 60 * 1000 }
  );

  // Fetch conference stats
  const { data: conferenceStats } = useQuery(
    'conference-stats',
    fetchConferenceStats,
    { staleTime: 10 * 60 * 1000 }
  );

  // Calculate key metrics
  const topTeams = rankings.slice(0, 10);
  const totalTeams = rankings.length;
  const averageRPI = rankings.length > 0 
    ? (rankings.reduce((sum, team) => sum + team.rpi, 0) / rankings.length).toFixed(4)
    : 0;

  // Mock data for charts (replace with real data)
  const rpiTrendData = [
    { date: '2024-01-01', rpi: 0.750 },
    { date: '2024-01-02', rpi: 0.755 },
    { date: '2024-01-03', rpi: 0.760 },
    { date: '2024-01-04', rpi: 0.758 },
    { date: '2024-01-05', rpi: 0.765 },
    { date: '2024-01-06', rpi: 0.770 },
    { date: '2024-01-07', rpi: 0.775 },
  ];

  const conferenceData = conferenceStats || [
    { conference: 'Pac-12', avgRPI: 0.650, teams: 12 },
    { conference: 'ACC', avgRPI: 0.645, teams: 14 },
    { conference: 'Big Ten', avgRPI: 0.640, teams: 14 },
    { conference: 'SEC', avgRPI: 0.635, teams: 14 },
    { conference: 'Big 12', avgRPI: 0.630, teams: 10 },
  ];

  const getTrendIcon = (trend) => {
    if (trend > 0) return <TrendingUpIcon className="w-4 h-4 text-success-500" />;
    if (trend < 0) return <TrendingDownIcon className="w-4 h-4 text-danger-500" />;
    return <MinusIcon className="w-4 h-4 text-gray-400" />;
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-primary-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="bg-danger-50 border border-danger-200 rounded-lg p-4">
          <h3 className="text-lg font-medium text-danger-800">Error Loading Data</h3>
          <p className="text-danger-600">{error}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900">NCAA Soccer RPI Dashboard</h1>
        <p className="text-gray-600 mt-2">
          Real-time Rating Percentage Index rankings and analytics
        </p>
      </div>

      {/* Key Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <ChartBarIcon className="h-8 w-8 text-primary-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Total Teams</p>
              <p className="text-2xl font-bold text-gray-900">{totalTeams}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <TrendingUpIcon className="h-8 w-8 text-success-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Average RPI</p>
              <p className="text-2xl font-bold text-gray-900">{averageRPI}</p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <CalendarIcon className="h-8 w-8 text-warning-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Last Updated</p>
              <p className="text-sm font-bold text-gray-900">
                {lastUpdated ? new Date(lastUpdated).toLocaleTimeString() : 'Never'}
              </p>
            </div>
          </div>
        </div>

        <div className="bg-white rounded-lg shadow p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <EyeIcon className="h-8 w-8 text-secondary-600" />
            </div>
            <div className="ml-4">
              <p className="text-sm font-medium text-gray-500">Active Sessions</p>
              <p className="text-2xl font-bold text-gray-900">24</p>
            </div>
          </div>
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Top Teams */}
        <div className="lg:col-span-2">
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <h3 className="text-lg font-medium text-gray-900">Top 10 Teams</h3>
            </div>
            <div className="overflow-hidden">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Rank
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Team
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      RPI
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Record
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Trend
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {topTeams.map((team, index) => (
                    <tr key={team.team} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                        {team.rank}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <Link 
                          to={`/team/${team.team}`}
                          className="text-sm font-medium text-primary-600 hover:text-primary-900"
                        >
                          {team.team}
                        </Link>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {team.rpi.toFixed(4)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {team.wins}-{team.losses}-{team.ties}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {getTrendIcon(Math.random() - 0.5)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Trending Teams */}
        <div className="lg:col-span-1">
          <div className="bg-white rounded-lg shadow">
            <div className="px-6 py-4 border-b border-gray-200">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-gray-900">Trending Teams</h3>
                <select
                  value={selectedTimeframe}
                  onChange={(e) => setSelectedTimeframe(e.target.value)}
                  className="text-sm border border-gray-300 rounded-md px-2 py-1"
                >
                  <option value="7d">7 Days</option>
                  <option value="30d">30 Days</option>
                </select>
              </div>
            </div>
            <div className="p-6">
              {trendingTeams?.slice(0, 5).map((team, index) => (
                <div key={team.team} className="flex items-center justify-between mb-4 last:mb-0">
                  <div className="flex items-center">
                    <span className="text-sm font-medium text-gray-900 mr-2">
                      {index + 1}.
                    </span>
                    <span className="text-sm text-gray-700">{team.team}</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <span className="text-sm text-gray-500">
                      {team.rpiChange > 0 ? '+' : ''}{team.rpiChange.toFixed(3)}
                    </span>
                    {getTrendIcon(team.rpiChange)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mt-8">
        {/* RPI Trend Chart */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">RPI Trend (Last 7 Days)</h3>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={rpiTrendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Line type="monotone" dataKey="rpi" stroke="#3b82f6" strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Conference Performance */}
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Conference Average RPI</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={conferenceData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="conference" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="avgRPI" fill="#3b82f6" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="mt-8">
        <div className="bg-white rounded-lg shadow p-6">
          <h3 className="text-lg font-medium text-gray-900 mb-4">Quick Actions</h3>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Link
              to="/rankings"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors duration-200"
            >
              <ChartBarIcon className="h-6 w-6 text-primary-600 mr-3" />
              <div>
                <p className="font-medium text-gray-900">View Full Rankings</p>
                <p className="text-sm text-gray-500">Complete RPI standings</p>
              </div>
            </Link>

            <Link
              to="/matches"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors duration-200"
            >
              <CalendarIcon className="h-6 w-6 text-primary-600 mr-3" />
              <div>
                <p className="font-medium text-gray-900">Recent Matches</p>
                <p className="text-sm text-gray-500">Latest game results</p>
              </div>
            </Link>

            <Link
              to="/analytics"
              className="flex items-center p-4 border border-gray-200 rounded-lg hover:border-primary-300 hover:bg-primary-50 transition-colors duration-200"
            >
              <TrendingUpIcon className="h-6 w-6 text-primary-600 mr-3" />
              <div>
                <p className="font-medium text-gray-900">Advanced Analytics</p>
                <p className="text-sm text-gray-500">Detailed insights</p>
              </div>
            </Link>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard; 