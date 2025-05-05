# Swap Reporting Admin UI

This is the frontend application for the Swap Reporting MVP Admin UI.
It is built using React and Redux Toolkit.

## Getting Started

1.  **Navigate to the `src/admin-ui` directory:**
    ```bash
    cd src/admin-ui
    ```

2.  **Install dependencies:**
    ```bash
    npm install # or yarn install
    ```

3.  **Set up environment variables:**
    Create a `.env` file in the `src/admin-ui` directory and set the `REACT_APP_API_BASE_URL` to the URL of your `web` module backend API.
    ```env
    REACT_APP_API_BASE_URL=http://localhost:8006/api
    ```
    Make sure your backend services (especially the `web` module on port 8006) are running.

4.  **Run the application in development mode:**
    ```bash
    npm start # or yarn start
    ```
    This will start the React development server, usually on http://localhost:3000.

5.  **Build for production:**
    ```bash
    npm run build # or yarn build
    ```
    This command builds the app for production to the `build` folder. This is the folder whose contents you will copy to `../web/static/` to be served by the backend.

## Project Structure

- `public/`: Contains the public assets (like `index.html`).
- `src/`: Contains the main React application code.
    - `components/`: Reusable UI components (e.g., `ErrorList`, `ErrorDetail`).
    - `redux/`: Redux slices and store configuration.
    - `App.js`: Main application component and routing setup.
    - `App.css`: Main application styling.
    - `index.js`: Entry point for the React application.
    - `index.css`: Global CSS styles.

## Ghibli-Inspired Styling

Basic CSS variables and a font are used in `App.css` to provide a starting point for a Ghibli-inspired aesthetic. To achieve a more complete look, you would need to:

- Refine the color palette.
- Choose and apply more expressive typography.
- Design custom icons or illustrations.
- Implement more complex layouts and animations inspired by Ghibli films.
- Potentially use CSS-in-JS libraries or styled components for more advanced styling.

## Extending Functionality

- Add more components for Dashboard, Processed Data, Reports, and Submissions.
- Create corresponding Redux slices and async thunks to fetch data for these features from the backend API.
- Implement filtering and pagination controls in the components and pass the filter/pagination state to the Redux thunks.
- Add detailed views for Processed Data, Reports, and Submissions.
- Implement logic for linking to report files (requires backend support for secure file access).
- Enhance error handling with user-friendly messages and notifications (e.g., using a toast library).
- Implement authentication and authorization.
