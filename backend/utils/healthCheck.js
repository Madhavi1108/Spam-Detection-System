const mongoose = require('mongoose');
const axios = require('axios');

/**
 * Check MongoDB connection status
 */ 
const checkMongoDB = () => {
    const state = mongoose.connection.readyState;
    const states = {
        0: 'disconnected',
        1: 'connected',
        2: 'connecting',
        3: 'disconnecting'
    };
    return {
        status: states[state] || 'unknown',
        state: state
    };
};

/**
 * Check Flask API status
 */
const checkFlaskAPI = async () => {
    try {
        const apiUrl = process.env.FLASK_API_URL || 'http://localhost:5000/health';
        const response = await axios.get(`${apiUrl}/health`, {
        timeout:2000
    });
        return {
            status: response.status === 200 ? 'healthy' : 'unhealthy',
            ready: response.status === 200,
            url: apiUrl
        };
} catch (error) {
        return {
            status: 'error',
            ready: false,
            url: process.env.FLASK_API_URL || 'http://localhost:5000/health',
            error: error.message
        };
    }
};
/**
 * Get comprehensive health status
 */
const getHealthStatus = async () => {
    const mongodb = checkMongoDB();
    const flask = await checkFlaskAPI();

    const allReady = mongodb.ready && flask.ready;

    return {
        status: allReady ? 'healthy' : 'unhealthy',
        timestamp: new Date().toISOString(),
        uptime: process.uptime(),
        dependencies: {
            mongodb: mongodb,
            flask: flask
        }
    };
};

module.exports = { getHealthStatus };
