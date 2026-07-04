const rateLimit = require('express-rate-limit');

// 1. Strict Auth Limiters (Your Code)
const loginLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5,
  message: { success: false, message: 'Too many login attempts from this IP, please try again after 15 minutes.' },
  standardHeaders: true,
  legacyHeaders: false,
});

const registerLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 5,
  message: { success: false, message: 'Too many registration attempts from this IP, please try again after 15 minutes.' },
  standardHeaders: true,
  legacyHeaders: false,
});

const resetLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 3,
  message: { success: false, message: 'Too many password reset requests, please try again later.' },
  standardHeaders: true,
  legacyHeaders: false,
});

const apiLimiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  message: { success: false, message: 'Too many API requests from this IP, please try again after 15 minutes.' },
  standardHeaders: true,
  legacyHeaders: false,
});

// 2. Maintainer's Limiters (Incoming Code)
const chatLimiter = rateLimit({
  windowMs: 60 * 1000,
  max: 15,
  message: { success: false, error: "Too many chat requests. Please slow down." }
});

const PREDICT_WINDOW_MS = Number(process.env.PREDICT_RATE_LIMIT_WINDOW_MS) || 60 * 1000;
const PREDICT_MAX = Number(process.env.PREDICT_RATE_LIMIT_MAX) || 30;

const predictLimiter = rateLimit({
  windowMs: PREDICT_WINDOW_MS,
  max: PREDICT_MAX,
  standardHeaders: true,
  legacyHeaders: false,
  handler: (req, res, next, options) => {
    const retryAfterSeconds = Math.ceil(options.windowMs / 1000);
    res.status(429).json({
      success: false,
      error: "Too many predict requests. Please slow down.",
      retryAfter: retryAfterSeconds
    });
  }
});

module.exports = { loginLimiter, registerLimiter, resetLimiter, apiLimiter, chatLimiter, predictLimiter, PREDICT_MAX, PREDICT_WINDOW_MS };