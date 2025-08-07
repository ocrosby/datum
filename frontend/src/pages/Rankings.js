import React, { useState, useMemo } from 'react';
import { Link } from 'react-router-dom';
import { MagnifyingGlassIcon, FunnelIcon, ArrowUpIcon, ArrowDownIcon, ChevronUpIcon, ChevronDownIcon } from '@heroicons/react/24/outline';
import { useRPI } from '../contexts/RPIContext';
import CalculationStatus from '../components/CalculationStatus';

const Rankings = () => {
  const { rankings, isLoading, error, filters, dispatch } = useRPI();
  const [sortConfig, setSortConfig] = useState({ key: 'rank', direction: 'asc' });
  const [searchTerm, setSearchTerm] = useState('');

  const conferences = useMemo(() => {
    const confs = [...new Set(rankings.map(team => team.conference))].filter(Boolean).sort();
    return confs;
  }, [rankings]);

  const divisions = useMemo(() => {
    const divs = [...new Set(rankings.map(team => team.division))].filter(Boolean).sort();
    return divs;
  }, [rankings]);

  const filteredRankings = useMemo(() => {
    let filtered = rankings;

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(team =>
        team.team.toLowerCase().includes(searchTerm.toLowerCase())
      );
    }

    // Apply conference filter
    if (filters.conference && filters.conference !== 'all') {
      filtered = filtered.filter(team => team.conference === filters.conference);
    }

    // Apply division filter
    if (filters.division && filters.division !== 'all') {
      filtered = filtered.filter(team => team.division === filters.division);
    }

    return filtered;
  }, [rankings, searchTerm, filters]);

  const sortedRankings = useMemo(() => {
    const sorted = [...filteredRankings];
    
    sorted.sort((a, b) => {
      let aValue = a[sortConfig.key];
      let bValue = b[sortConfig.key];
      
      // Handle numeric values
      if (typeof aValue === 'number' && typeof bValue === 'number') {
        if (sortConfig.direction === 'asc') {
          return aValue - bValue;
        } else {
          return bValue - aValue;
        }
      }
      
      // Handle string values
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        if (sortConfig.direction === 'asc') {
          return aValue.localeCompare(bValue);
        } else {
          return bValue.localeCompare(aValue);
        }
      }
      
      return 0;
    });
    
    return sorted;
  }, [filteredRankings, sortConfig]);

  const handleSort = (key) => {
    setSortConfig(prevConfig => ({
      key,
      direction: prevConfig.key === key && prevConfig.direction === 'asc' ? 'desc' : 'asc'
    }));
  };

  const handleFilterChange = (filterType, value) => {
    dispatch({
      type: 'SET_FILTER',
      payload: { filterType, value }
    });
  };

  const getSortIcon = (key) => {
    if (sortConfig.key !== key) {
      return <ChevronUpIcon className="h-4 w-4 text-gray-400" />;
    }
    
    return sortConfig.direction === 'asc' 
      ? <ChevronUpIcon className="h-4 w-4 text-primary-600" />
      : <ChevronDownIcon className="h-4 w-4 text-primary-600" />;
  };

  const getRPIChange = (team) => {
    // Mock RPI change - in real implementation, this would come from historical data
    const changes = [-0.02, -0.01, 0, 0.01, 0.02];
    return changes[Math.floor(Math.random() * changes.length)];
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
          <h3 className="text-red-800 font-medium">Error Loading Rankings</h3>
          <p className="text-red-600 mt-1">{error}</p>
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
        <h1 className="text-3xl font-bold text-gray-900 mb-2">RPI Rankings</h1>
        <p className="text-gray-600">
          Current Rating Percentage Index rankings for NCAA soccer teams
        </p>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="relative">
            <MagnifyingGlassIcon className="absolute left-3 top-1/2 transform -translate-y-1/2 h-5 w-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search teams..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
            />
          </div>

          {/* Conference Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Conference
            </label>
            <select
              value={filters.conference || 'all'}
              onChange={(e) => handleFilterChange('conference', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="all">All Conferences</option>
              {conferences.map(conference => (
                <option key={conference} value={conference}>
                  {conference}
                </option>
              ))}
            </select>
          </div>

          {/* Division Filter */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Division
            </label>
            <select
              value={filters.division || 'all'}
              onChange={(e) => handleFilterChange('division', e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-primary-500 focus:border-primary-500"
            >
              <option value="all">All Divisions</option>
              {divisions.map(division => (
                <option key={division} value={division}>
                  {division}
                </option>
              ))}
            </select>
          </div>

          {/* Results Count */}
          <div className="flex items-end">
            <div className="text-sm text-gray-600">
              Showing {sortedRankings.length} of {rankings.length} teams
            </div>
          </div>
        </div>
      </div>

      {/* Rankings Table */}
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
              {sortedRankings.map((team, index) => (
                <tr key={team.team} className="hover:bg-gray-50">
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {team.rank}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div>
                        <div className="text-sm font-medium text-gray-900">
                          <Link
                            to={`/team/${team.team}`}
                            className="hover:text-primary-600 hover:underline"
                          >
                            {team.team}
                          </Link>
                        </div>
                        <div className="text-sm text-gray-500">
                          {team.conference} • {team.division}
                        </div>
                      </div>
                    </div>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                    <div className="flex items-center space-x-1">
                      <span className="font-medium">{team.rpi.toFixed(4)}</span>
                      <span className={`text-xs ${getRPIChange(team) > 0 ? 'text-success-600' : getRPIChange(team) < 0 ? 'text-danger-600' : 'text-gray-500'}`}>
                        {getRPIChange(team) > 0 ? '↗' : getRPIChange(team) < 0 ? '↘' : '→'}
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
        {sortedRankings.length === 0 && (
          <div className="text-center py-12">
            <FunnelIcon className="mx-auto h-12 w-12 text-gray-400" />
            <h3 className="mt-2 text-sm font-medium text-gray-900">No teams found</h3>
            <p className="mt-1 text-sm text-gray-500">
              Try adjusting your search or filter criteria.
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default Rankings; 