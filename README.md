# Swap Reporting MVP

To run this locally, you would need to start each of the five modules (data-ingestion, data-processing, validation, report-generation, report-submission, error-monitoring, web) in separate terminals, ensuring they are listening on the ports specified in the httpx calls (8000, 8001, 8002, 8003, 8004, 8005, 8006).



# frontend Development Process:

Set up Frontend Project: Initialize a new project using your chosen framework's CLI (e.g., create-react-app, vue create, ng new).

Design UI/UX: Plan the layout, components, and user flow based on the required functionalities.

Implement Components: Build reusable UI components (tables, forms, buttons, charts).

Connect to Backend API: Implement the logic to fetch and send data to the /api/* endpoints using fetch or Axios.

Implement Routing: Set up client-side routing to navigate between different views (e.g., list errors, view error details).

Build and Test: Build the frontend application using your build tool and test it thoroughly in a local development environment, ensuring it correctly interacts with your running backend modules.

Integrate with Backend Serving: Configure your build process to output the static files into the src/web/static/ directory so the web module can serve them.
