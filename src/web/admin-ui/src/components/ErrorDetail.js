// src/admin-ui/src/components/ErrorDetail.js
import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { useDispatch, useSelector } from 'react-redux';
import { fetchErrorDetail, updateErrorStatus, retryError } from '../redux/errorsSlice';

function ErrorDetail() {
  const { errorId } = useParams(); // Get errorId from URL
  const navigate = useNavigate(); // For navigation after actions
  const dispatch = useDispatch();
  const { selectedError: error, loadingDetail, errorDetailError, updatingStatus, retryingError } = useSelector((state) => state.errors);

  const [newStatus, setNewStatus] = useState(''); // State for status update dropdown

  useEffect(() => {
    dispatch(fetchErrorDetail(errorId));
  }, [dispatch, errorId]); // Fetch error detail when errorId changes

  useEffect(() => {
      // Update the local status state when the error data is loaded
      if (error) {
          setNewStatus(error.status);
      }
  }, [error]); // Update when error data changes


  const handleStatusChange = (event) => {
    setNewStatus(event.target.value);
  };

  const handleUpdateStatus = () => {
    if (newStatus && error) {
      dispatch(updateErrorStatus({ errorId: error.id, newStatus }));
      // TODO: Show a success message or handle loading state feedback
    }
  };

  const handleRetry = () => {
      if (error) {
          // Confirm before retrying in a real application
          if (window.confirm(`Are you sure you want to retry processing for error ${error.trade_id || error.id}?`)) {
              dispatch(retryError(error.id));
              // TODO: Show feedback (e.g., "Retry initiated")
              // Optionally navigate back to the error list or update the status locally
          }
      }
  };


  if (loadingDetail) {
    return <div className="card">Loading Error Details...</div>;
  }

  if (errorDetailError) {
    return <div className="card error-message">Error loading error details: {errorDetailError}</div>;
  }

  if (!error) {
      // This case might be hit briefly or if the error ID was invalid
      return <div className="card">Error not found.</div>;
  }

  return (
    <div className="card">
      <div className="card-header">Error Details</div>

      <p><strong>Error ID:</strong> {error.id}</p>
      <p><strong>Trade ID/UTI:</strong> {error.trade_id || 'N/A'}</p>
      <p><strong>Source Module:</strong> {error.source_module}</p>
      <p><strong>Current Status:</strong> <span className={`status-badge ${error.status.toLowerCase().replace(' ', '-')}`}>{error.status}</span></p>
      <p><strong>Severity:</strong> {error.severity}</p>
      <p><strong>Timestamp:</strong> {new Date(error.timestamp).toLocaleString()}</p>

      <h4>Error Messages:</h4>
      {error.error_messages && error.error_messages.length > 0 ? (
        <ul>
          {error.error_messages.map((msg, index) => (
            <li key={index} className="error-message">{msg}</li>
          ))}
        </ul>
      ) : (
        <p>No specific error messages provided.</p>
      )}

      <h4>Data Payload:</h4>
      {/* Display data payload - format as needed */}
      <pre style={{ backgroundColor: '#f4f4f4', padding: '1rem', borderRadius: '4px', overflowX: 'auto', border: '1px solid var(--ghibli-border-color)' }}>
        {JSON.stringify(error.data_payload, null, 2)}
      </pre>

       {/* Optional: Display original source data if available */}
       {error.original_source_data_payload && (
            <>
                <h4>Original Source Data:</h4>
                 <pre style={{ backgroundColor: '#f4f4f4', padding: '1rem', borderRadius: '4px', overflowX: 'auto', border: '1px solid var(--ghibli-border-color)' }}>
                    {JSON.stringify(error.original_source_data_payload, null, 2)}
                </pre>
            </>
       )}


      {/* Actions */}
      <div style={{ marginTop: '1.5rem', borderTop: '1px solid var(--ghibli-border-color)', paddingTop: '1.5rem' }}>
        {/* Update Status Control */}
        <div>
          <label htmlFor="statusUpdate">Update Status:</label>
          <select id="statusUpdate" value={newStatus} onChange={handleStatusChange} style={{ marginLeft: '0.5rem', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--ghibli-border-color)' }}>
             <option value="Open">Open</option>
             <option value="Investigating">Investigating</option>
             <option value="Resolved">Resolved</option>
             <option value="Closed">Closed</option>
             {/* Add other relevant statuses */}
          </select>
          <button onClick={handleUpdateStatus} disabled={updatingStatus || newStatus === error.status} className="button" style={{ marginLeft: '1rem' }}>
            {updatingStatus ? 'Updating...' : 'Update Status'}
          </button>
           {updatingStatus && <span>Updating...</span>}
           {/* TODO: Show success/error feedback for status update */}
        </div>

        {/* Retry Button */}
        <div style={{ marginTop: '1rem' }}>
             <button onClick={handleRetry} disabled={retryingError} className="button button-danger">
                {retryingError ? 'Retrying...' : 'Retry Processing'}
             </button>
             {retryingError && <span>Initiating Retry...</span>}
             {/* TODO: Show success/error feedback for retry */}
        </div>

      </div>

      {/* Back button */}
      <div style={{ marginTop: '1.5rem' }}>
           <Link to="/errors" className="button">Back to Error List</Link>
      </div>

    </div>
  );
}

export default ErrorDetail;
