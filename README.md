# Survey Accelerator

A specialized search engine designed to help researchers, policymakers, and development practitioners quickly find relevant information across a wide range of high-quality surveys and research documents.

## Overview

Survey Accelerator is a free, fast, and completely open-source tool that provides access to surveys and research documents from organizations like IDHS, IDinsight, UNICEF, USAID, World Bank, and more. It uses advanced search algorithms to identify the most relevant matches to user queries across these documents.

### Key Features

- **Advanced Search**: Find relevant information quickly using powerful search algorithms
- **Document Library**: Browse a collection of high-quality surveys and research documents
- **Organization Filters**: Filter search results by organization (IDHS, IDinsight, UNICEF, etc.)
- **Survey Type Filters**: Filter by survey types (DHS Surveys, MICS7 questionnaires, household income surveys, etc.)
- **Survey Contribution**: Users can contribute new surveys to the database for review
- **Highlighted PDFs**: View matches directly within PDF documents with relevant text highlighted

## Getting Started

### Prerequisites

- Node.js (for frontend)
- Python 3.10+ (for backend)
- Docker (optional, for containerized deployment)

### Installation

#### Backend Setup

1. Navigate to the backend directory:
   ```
   cd backend
   ```

2. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

3. Set up environment variables (create a .env file with the required configurations)

4. Run the backend server:
   ```
   python main.py
   ```

#### Frontend Setup

1. Navigate to the frontend directory:
   ```
   cd frontend
   ```

2. Install dependencies:
   ```
   npm install
   ```

3. Run the development server:
   ```
   npm start
   ```

### Docker Deployment

For containerized deployment, use the provided Dockerfiles and docker-compose configuration:

```
# From the project root
docker-compose -f deployment/docker-compose/docker-compose.yml up -d
```

## Usage

1. Enter your search query in the search box
2. Optionally filter by organization or survey type using the dropdown menus
3. Click the Search button or press Enter
4. Browse the results and click on any document card to view it
5. Click on specific matches within a document to navigate directly to that page

## Contributing

Survey Accelerator is an open-source project and welcomes contributions. You can contribute in several ways:

1. **Code Contributions**: Submit pull requests with bug fixes or new features
2. **Survey Contributions**: Add new surveys to the database using the "Contribute Survey" feature
3. **Documentation**: Help improve documentation and usage guides
4. **Bug Reports**: Report issues or suggest enhancements

## License

This project is licensed under the GNU Affero General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## About IDinsight

Survey Accelerator is developed and maintained by [IDinsight](https://www.idinsight.org/), a global advisory, data analytics, and research organization that helps development leaders maximize their social impact.
