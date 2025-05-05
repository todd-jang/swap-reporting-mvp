// src/admin-ui/src/redux/errorsSlice.js
import { createSlice, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios'; // Using Axios for API calls

// Define the base URL for your web module backend API
// In production, this would be configured via environment variables or build process
const API_BASE_URL = process.env.REACT_APP_API_BASE_URL || 'http://localhost:8006/api';

// Async Thunk for fetching errors
export const fetchErrors = createAsyncThunk(
  'errors/fetchErrors',
  async (filters = {}) => {
    const response = await axios.get(`${API_BASE_URL}/errors`, { params: filters });
    return response.data; // Assuming the backend returns { status: 'success', errors: [...], total_count: ... }
  }
);

// Async Thunk for fetching a single error detail
export const fetchErrorDetail = createAsyncThunk(
  'errors/fetchErrorDetail',
  async (errorId) => {
    const response = await axios.get(`${API_BASE_URL}/errors/${errorId}`);
    return response.data.error; // Assuming the backend returns { status: 'success', error: {...} }
  }
);

// Async Thunk for updating error status
export const updateErrorStatus = createAsyncThunk(
  'errors/updateErrorStatus',
  async ({ errorId, newStatus }) => {
    const response = await axios.put(`${API_BASE_URL}/errors/${errorId}/status`, null, { params: { new_status: newStatus } });
    return response.data.error; // Assuming the backend returns the updated error object
  }
);

// Async Thunk for retrying error processing
export const retryError = createAsyncThunk(
  'errors/retryError',
  async (errorId) => {
    const response = await axios.post(`${API_BASE_URL}/errors/${errorId}/retry`);
    // The backend might return a success message or the updated error status (e.g., 'Retrying')
    return response.data;
  }
);


const errorsSlice = createSlice({
  name: 'errors',
  initialState: {
    list: [],
    loadingList: false,
    errorListError: null,
    selectedError: null,
    loadingDetail: false,
    errorDetailError: null,
    updatingStatus: false,
    updateStatusError: null,
    retryingError: false,
    retryErrorError: null,
    totalCount: 0, // For pagination
  },
  reducers: {
    // You can add synchronous reducers here if needed
  },
  extraReducers: (builder) => {
    builder
      // Fetch Errors List
      .addCase(fetchErrors.pending, (state) => {
        state.loadingList = true;
        state.errorListError = null;
      })
      .addCase(fetchErrors.fulfilled, (state, action) => {
        state.loadingList = false;
        state.list = action.payload.errors;
        state.totalCount = action.payload.total_count;
      })
      .addCase(fetchErrors.rejected, (state, action) => {
        state.loadingList = false;
        state.errorListError = action.error.message;
      })
      // Fetch Error Detail
      .addCase(fetchErrorDetail.pending, (state) => {
        state.loadingDetail = true;
        state.errorDetailError = null;
        state.selectedError = null; // Clear previous detail
      })
      .addCase(fetchErrorDetail.fulfilled, (state, action) => {
        state.loadingDetail = false;
        state.selectedError = action.payload;
      })
      .addCase(fetchErrorDetail.rejected, (state, action) => {
        state.loadingDetail = false;
        state.errorDetailError = action.error.message;
      })
      // Update Error Status
      .addCase(updateErrorStatus.pending, (state) => {
        state.updatingStatus = true;
        state.updateStatusError = null;
      })
      .addCase(updateErrorStatus.fulfilled, (state, action) => {
        state.updatingStatus = false;
        // Update the error in the list if it exists
        const index = state.list.findIndex(error => error.id === action.payload.id);
        if (index !== -1) {
          state.list[index] = action.payload;
        }
        // Update the selected error if it's the one being updated
        if (state.selectedError && state.selectedError.id === action.payload.id) {
           state.selectedError = action.payload;
        }
      })
      .addCase(updateErrorStatus.rejected, (state, action) => {
        state.updatingStatus = false;
        state.updateStatusError = action.error.message;
        // TODO: Maybe show a toast notification for the error
      })
       // Retry Error
      .addCase(retryError.pending, (state) => {
        state.retryingError = true;
        state.retryErrorError = null;
      })
      .addCase(retryError.fulfilled, (state, action) => {
        state.retryingError = false;
        // The backend might return status 'Retrying', update the list/detail accordingly
         if (state.selectedError && state.selectedError.id === action.meta.arg) {
             state.selectedError = { ...state.selectedError, status: 'Retrying' }; // Optimistic update
         }
         // TODO: Refresh the error list or update the specific item in the list
      })
      .addCase(retryError.rejected, (state, action) => {
        state.retryingError = false;
        state.retryErrorError = action.error.message;
         // TODO: Show a toast notification for the error
      });
  },
});

// Export the reducer
export default errorsSlice.reducer;

// Export actions if you have synchronous ones
// export const { someAction } = errorsSlice.actions;
