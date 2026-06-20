const Joi = require('joi');

class ValidationMiddleware {
    /**
     * Validate request body against schema
     */
    static validate(schema) {
        return (req, res, next) => {
            const { error, value } = schema.validate(req.body, {
                abortEarly: false,
                stripUnknown: true
            });

            if (error) {
                const errors = error.details.map(detail => ({
                    field: detail.path.join('.'),
                    message: detail.message
                }));

                return res.status(400).json({
                    success: false,
                    error: 'Validation failed',
                    details: errors
                });
            }

            // Replace req.body with validated value
            req.body = value;
            next();
        };
    }
}

module.exports = ValidationMiddleware;