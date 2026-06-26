const express = require("express");
const router = express.Router();

const {
  getSummary,
  getTrends,
  getBreakdown,
} = require("../controllers/analyticsController");

const { protect } = require("../middleware/authMiddleware");

router.get("/summary", protect, getSummary);
router.get("/trends", protect, getTrends);
router.get("/breakdown", protect, getBreakdown);

module.exports = router;
