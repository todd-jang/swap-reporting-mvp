// src/admin-ui/src/redux/store.js
import { configureStore } from '@reduxjs/toolkit';
import errorsReducer from './errorsSlice';
// Import other reducers here as you add features
// import processedDataReducer from './processedDataSlice';
// import reportsReducer from './reportsSlice';
// import submissionsReducer from './submissionsSlice';
// import healthReducer from './healthSlice';

const store = configureStore({
  reducer: {
    errors: errorsReducer,
    // Add other reducers here
    // processedData: processedDataReducer,
    // reports: reportsReducer,
    // submissions: submissionsReducer,
    // health: healthReducer,
  },
});

export default store;
