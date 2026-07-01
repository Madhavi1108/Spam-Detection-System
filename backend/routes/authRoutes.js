const express = require('express');
const router = express.Router();
const { body } = require('express-validator');
const { register, login, getMe, googleLogin, updateAvatar, forgotPassword, resetPassword } = require('../controllers/authController');
const { protect } = require('../middleware/authMiddleware');
const { registerLimiter, loginLimiter, resetLimiter } = require('../middleware/rateLimiter');
const { handleAvatarUpload } = require('../middleware/avatarUpload');
const registerValidation = [
  body('username').trim().isLength({ min: 3, max: 30 }).withMessage('Username must be 3–30 characters'),
  body('email').isEmail().withMessage('Please enter a valid email'),
  body('password').isLength({ min: 6 }).withMessage('Password must be at least 6 characters'),
];

const loginValidation = [
  body('email').isEmail().withMessage('Please enter a valid email'),
  body('password').notEmpty().withMessage('Password is required'),
];

router.post('/login', loginValidation,loginLimiter, login);
router.post('/register', registerValidation,registerLimiter, register);
router.post('/google', loginLimiter, googleLogin);
router.get('/me', protect, getMe);
router.post('/avatar', protect, handleAvatarUpload, updateAvatar);

const forgotPasswordValidation = [
  body('email').isEmail().withMessage('Please enter a valid email'),
];

const resetPasswordValidation = [
  body('password').isLength({ min: 6 }).withMessage('Password must be at least 6 characters'),
];

router.post('/forgot-password', resetLimiter, forgotPasswordValidation, forgotPassword);
router.post('/reset-password/:id/:token', resetLimiter, resetPasswordValidation, resetPassword);

module.exports = router;
