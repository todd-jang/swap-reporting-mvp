// src/admin-ui/src/components/HealthStatus.js
import React, { useEffect, useState } from 'react';
import axios from 'axios'; // Using Axios for API calls

// Define the base URL for your web module backend API
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8006/api';

function HealthStatus() {
    const [healthData, setHealthData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    useEffect(() => {
        const fetchHealth = async () => {
            try {
                setLoading(true);
                const response = await axios.get(`${API_BASE_URL}/health`);
                setHealthData(response.data);
                setLoading(false);
            } catch (err) {
                setError(err.message);
                setLoading(false);
            }
        };

        fetchHealth();
        // Optional: poll for health status updates periodically
        // const intervalId = setInterval(fetchHealth, 15000); // Fetch every 15 seconds
        // return () => clearInterval(intervalId); // Cleanup interval on component unmount

    }, []); // Empty dependency array means this runs once on mount


    if (loading) {
        return <div className="card">Loading Health Status...</div>;
    }

    if (error) {
        return <div className="card error-message">Error loading health status: {error}</div>;
    }

    if (!healthData) {
         return <div className="card">No health data available.</div>;
    }


    return (
        <div className="card">
            <div className="card-header">System Health Status</div>

            <p>Overall Status: <span className={`status-badge ${healthData.status.toLowerCase()}`}>{healthData.status}</span></p>

            <h4>Module Statuses:</h4>
            {healthData.dependencies ? (
                <ul>
                    {Object.entries(healthData.dependencies).map(([moduleName, statusData]) => (
                        <li key={moduleName}>
                            <strong>{moduleName}:</strong> <span className={`status-badge ${statusData.status.toLowerCase()}`}>{statusData.status}</span>
                            {statusData.status !== 'ok' && statusData.error && (
                                <span className="error-message" style={{ marginLeft: '1rem' }}>Error: {statusData.error}</span>
                            )}
                             {/* Display database status if available */}
                            {statusData.database_status && (
                                <span style={{ marginLeft: '1rem' }}>DB: <span className={`status-badge ${statusData.database_status.split(':')[0].toLowerCase()}`}>{statusData.database_status}</span></span>
                            )}
                             {/* Display S3 status if available */}
                            {statusData.s3_storage_status && (
                                <span style={{ marginLeft: '1rem' }}>S3: <span className={`status-badge ${statusData.s3_storage_status.split(':')[0].toLowerCase()}`}>{statusData.s3_storage_status}</span></span>
                            )}
                             {/* Display SDR status if available */}
                            {statusData.sdr_connectivity_status && (
                                <span style={{ marginLeft: '1rem' }}>SDR: <span className={`status-badge ${statusData.sdr_connectivity_status.split(':')[0].toLowerCase()}`}>{statusData.sdr_connectivity_status}</span></span>
                            )}
                             {/* Display other statuses as needed */}
                        </li>
                    ))}
                </ul>
            ) : (
                <p>No dependency status information available.</p>
            )}

            {/* TODO: Add more detailed health information if available from backend */}

        </div>
    );
}

export default HealthStatus;
