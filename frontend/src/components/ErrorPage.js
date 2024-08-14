import React from "react";

const ErrorPage = ({ error }) => {
  return (
    <div className="error-page">
      <h1>HS Trends App</h1>
      <h2>Oops! Something went wrong.</h2>
      <p>
        We're sorry for the inconvenience. Our team has been notified and is
        working on a fix.
      </p>
      <p>Error details: {error.message}</p>
      <button onClick={() => window.location.reload()}>Reload Page</button>
      <button
        onClick={() => {
          /* TODO: Implement error reporting */
        }}
      >
        Report This Issue
      </button>
    </div>
  );
};

export default ErrorPage;
