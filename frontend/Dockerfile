# Use a lightweight Node.js image compatible with your version
FROM node:19-alpine

# Set the working directory
WORKDIR /app

# Copy package.json and package-lock.json to install dependencies
COPY package*.json ./

# Install dependencies
RUN npm install

# Copy all project files
COPY . .

# Build the React app for production
RUN npm run build

# Install 'serve' to serve the production build
RUN npm install -g serve

# Expose port 3000
EXPOSE 3000

# Use 'serve' to serve the production build
CMD ["serve", "-s", "build", "-l", "3000"]
