import React, { useState, useEffect } from 'react';
import { ClockIcon, CheckCircleIcon, ExclamationTriangleIcon, ArrowPathIcon } from '@heroicons/react/24/outline';
import { useRPI } from '../contexts/RPIContext';
import toast from 'react-hot-toast';

const CalculationStatus = () => {
  const [status, setStatus] = useState(null);
  const [isChecking, setIsChecking] = useState(false);
  const { selectedDate } = useRPI();

  const checkCalculationStatus = async () => {
    setIsChecking(true);
    try {
      const response = await fetch(`/api/rpi/status?date=${selectedDate}`);
      const data = await response.json();
      setStatus(data);
    } catch (error) {
      console.error('Error checking calculation status:', error);
    } finally {
      setIsChecking(false);
    }
  };

  useEffect(() => {
    checkCalculationStatus();
    
    // Check status every 30 seconds if there's an ongoing calculation
    const interval = setInterval(() => {
      if (status?.has_ongoing_calculation) {
        checkCalculationStatus();
      }
    }, 30000);

    return () => clearInterval(interval);
  }, [selectedDate]);

  if (!status) {
    return null;
  }

  if (status.has_ongoing_calculation) {
    const ongoingCalc = status.ongoing_calculation;
    const startTime = new Date(ongoingCalc.start_time);
    const duration = Math.floor((Date.now() - startTime.getTime()) / 1000);
    
    return (
      <div className="bg-warning-50 border border-warning-200 rounded-lg p-4 mb-6">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <ClockIcon className="h-6 w-6 text-warning-600 animate-pulse" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-medium text-warning-800">
              RPI Calculation in Progress
            </h3>
            <div className="mt-2 text-sm text-warning-700">
              <p>
                Calculating RPI values for {selectedDate}. This may take a few minutes.
              </p>
              <div className="mt-2 space-y-1">
                <div className="flex justify-between">
                  <span>Calculation ID:</span>
                  <span className="font-mono text-xs">{ongoingCalc.calculation_id}</span>
                </div>
                <div className="flex justify-between">
                  <span>Duration:</span>
                  <span>{Math.floor(duration / 60)}m {duration % 60}s</span>
                </div>
                <div className="flex justify-between">
                  <span>Matches Processed:</span>
                  <span>{ongoingCalc.matches_processed || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Teams Calculated:</span>
                  <span>{ongoingCalc.teams_calculated || 0}</span>
                </div>
              </div>
            </div>
            <div className="mt-3">
              <button
                onClick={checkCalculationStatus}
                disabled={isChecking}
                className="inline-flex items-center px-3 py-1.5 border border-warning-300 text-xs font-medium rounded text-warning-700 bg-white hover:bg-warning-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-warning-500 disabled:opacity-50"
              >
                <ArrowPathIcon className={`h-4 w-4 mr-1 ${isChecking ? 'animate-spin' : ''}`} />
                {isChecking ? 'Checking...' : 'Refresh Status'}
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (status.has_completed_calculation) {
    const completedCalc = status.latest_completed_calculation;
    const completionTime = new Date(completedCalc.completion_time);
    
    return (
      <div className="bg-success-50 border border-success-200 rounded-lg p-4 mb-6">
        <div className="flex items-start space-x-3">
          <div className="flex-shrink-0">
            <CheckCircleIcon className="h-6 w-6 text-success-600" />
          </div>
          <div className="flex-1 min-w-0">
            <h3 className="text-sm font-medium text-success-800">
              RPI Calculation Complete
            </h3>
            <div className="mt-2 text-sm text-success-700">
              <p>
                Latest calculation completed for {selectedDate}.
              </p>
              <div className="mt-2 space-y-1">
                <div className="flex justify-between">
                  <span>Calculation ID:</span>
                  <span className="font-mono text-xs">{completedCalc.calculation_id}</span>
                </div>
                <div className="flex justify-between">
                  <span>Completed:</span>
                  <span>{completionTime.toLocaleString()}</span>
                </div>
                <div className="flex justify-between">
                  <span>Total Matches:</span>
                  <span>{completedCalc.total_matches || 0}</span>
                </div>
                <div className="flex justify-between">
                  <span>Total Teams:</span>
                  <span>{completedCalc.total_teams || 0}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-info-50 border border-info-200 rounded-lg p-4 mb-6">
      <div className="flex items-start space-x-3">
        <div className="flex-shrink-0">
          <ExclamationTriangleIcon className="h-6 w-6 text-info-600" />
        </div>
        <div className="flex-1 min-w-0">
          <h3 className="text-sm font-medium text-info-800">
            No RPI Data Available
          </h3>
          <div className="mt-2 text-sm text-info-700">
            <p>
              No RPI calculations have been performed for {selectedDate}.
            </p>
            <p className="mt-1">
              This could mean:
            </p>
            <ul className="mt-1 list-disc list-inside space-y-1">
              <li>No matches have been played yet</li>
              <li>The calculation hasn't been triggered</li>
              <li>There was an error in the calculation process</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default CalculationStatus; 