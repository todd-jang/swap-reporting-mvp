// src/admin-ui/src/components/ErrorList.js
import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { fetchErrors } from '../redux/errorsSlice';
import { Link } from 'react-router-dom';

function ErrorList() {
  const dispatch = useDispatch();
  const { list: errors, loadingList, errorListError, totalCount } = useSelector((state) => state.errors);

  // State for pagination and filtering (basic example)
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage] = useState(10); // Fixed items per page
  const [filters, setFilters] = useState({}); // State for filters

  useEffect(() => {
    // Calculate offset based on current page and items per page
    const offset = (currentPage - 1) * itemsPerPage;
    // Fetch errors with current filters and pagination
    dispatch(fetchErrors({ ...filters, limit: itemsPerPage, offset }));
  }, [dispatch, currentPage, itemsPerPage, filters]); // Refetch when page or filters change

  // Basic pagination handlers
  const handleNextPage = () => {
    if (currentPage * itemsPerPage < totalCount) {
      setCurrentPage(currentPage + 1);
    }
  };

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  // Basic filter handler (example for status)
  const handleStatusFilterChange = (event) => {
    setFilters({ ...filters, status: event.target.value || undefined }); // Use undefined to remove filter
    setCurrentPage(1); // Reset to first page on filter change
  };


  if (loadingList) {
    return <div className="card">Loading Errors...</div>;
  }

  if (errorListError) {
    return <div className="card error-message">Error loading errors: {errorListError}</div>;
  }

  return (
    <div className="card">
      <div className="card-header">Error List</div>

      {/* Basic Filtering Controls */}
      <div className="filter-controls" style={{ marginBottom: '1rem' }}>
        <label htmlFor="statusFilter">Status:</label>
        <select id="statusFilter" onChange={handleStatusFilterChange} style={{ marginLeft: '0.5rem', padding: '0.5rem', borderRadius: '4px', border: '1px solid var(--ghibli-border-color)' }}>
          <option value="">All</option>
          <option value="Open">Open</option>
          <option value="Investigating">Investigating</option>
          <option value="Resolved">Resolved</option>
          <option value="Closed">Closed</option>
          <option value="Failed">Failed</option> {/* Add other relevant statuses */}
          <option value="Retrying">Retrying</option>
        </select>
        {/* TODO: Add more filters (module, trade ID/UTI, date range) */}
      </div>


      {errors.length === 0 ? (
        <p>No errors found.</p>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Trade ID/UTI</th>
              <th>Source Module</th>
              <th>Status</th>
              <th>Severity</th>
              <th>Timestamp</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {errors.map((error) => (
              <tr key={error.id}>
                <td>{error.id.substring(0, 8)}...</td> {/* Truncate ID */}
                <td>{error.trade_id || 'N/A'}</td>
                <td>{error.source_module}</td>
                <td><span className={`status-badge ${error.status.toLowerCase().replace(' ', '-')}`}>{error.status}</span></td>
                <td>{error.severity}</td>
                <td>{new Date(error.timestamp).toLocaleString()}</td>
                <td>
                  <Link to={`/errors/${error.id}`} className="button" style={{ marginRight: '0.5rem' }}>View Details</Link>
                  {/* TODO: Add quick actions like "Resolve" button here if needed */}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {/* Basic Pagination Controls */}
      <div className="pagination-controls" style={{ marginTop: '1rem', textAlign: 'center' }}>
        <button onClick={handlePreviousPage} disabled={currentPage === 1} className="button" style={{ marginRight: '1rem' }}>Previous</button>
        <span>Page {currentPage} of {Math.ceil(totalCount / itemsPerPage)}</span>
        <button onClick={handleNextPage} disabled={currentPage * itemsPerPage >= totalCount} className="button" style={{ marginLeft: '1rem' }}>Next</button>
         <span style={{ marginLeft: '1rem' }}>Total Errors: {totalCount}</span>
      </div>

    </div>
  );
}

export default ErrorList;
