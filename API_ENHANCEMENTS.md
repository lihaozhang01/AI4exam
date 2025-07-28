# API Enhancements for History Page

This document outlines the API specifications for the new "Test Paper Library" and the enhanced "Submission History" features.

## 1. Test Paper Library

This endpoint retrieves a list of unique test paper templates, supporting searching and sorting.

*   **Endpoint:** `GET /api/history_test_papers`
*   **Description:** Fetches a list of unique test paper templates.
*   **Query Parameters:**
    *   `search` (string, optional): Filters papers where the name contains the search term.
    *   `sort_by` (string, optional, enum: `name`, `created_at`): The field to sort by. Defaults to `created_at`.
    *   `order` (string, optional, enum: `asc`, `desc`): The sort order. Defaults to `desc`.
*   **Success Response (200 OK):**
    *   **Content-Type:** `application/json`
    *   **Body:** An array of test paper objects.

    ```json
    [
      {
        "id": "integer",
        "name": "string",
        "description": "string",
        "created_at": "datetime string (ISO 8601)"
      }
    ]
    ```

## 2. Enhanced Submission History

This endpoint retrieves a list of all test paper submissions, with added support for filtering and sorting.

*   **Endpoint:** `GET /api/history_sub`
*   **Description:** Fetches a list of all test paper submissions, now with filtering and sorting capabilities.
*   **Query Parameters:**
    *   `search` (string, optional): Filters history records by the associated test paper's name.
    *   `sort_by` (string, optional, enum: `name`, `created_at`): Sorts by the test paper's name or the submission's creation date. Defaults to `created_at`.
    *   `order` (string, optional, enum: `asc`, `desc`): The sort order. Defaults to `desc`.
*   **Success Response (200 OK):**
    *   **Content-Type:** `application/json`
    *   **Body:** An array of history objects, structured as it is currently, but pre-filtered and sorted by the backend.