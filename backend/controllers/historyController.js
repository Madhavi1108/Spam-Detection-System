const History = require("../models/History");
const mongoose = require("mongoose");

// Get logged-in user's history
const getHistory = async (req, res) => {
  try {
    const history = await History.find({ user: req.user.id })
      .sort({ createdAt: -1 });

    res.json(history);
  } catch (err) {
    console.error("Get history error:", err);
    res.status(500).json({ error: "Server error" });
  }
};

// Delete a single history item
const deleteHistoryItem = async (req, res) => {

  if (!mongoose.Types.ObjectId.isValid(req.params.id)) {
    return res.status(400).json({
      error: "Invalid history id",
    });
  }
  
  try {
    const historyItem = await History.findOneAndDelete({
      _id: req.params.id,
      user: req.user.id,
    });

    if (!historyItem) {
      return res.status(404).json({ error: "History item not found" });
    }

    res.json({ message: "History item deleted" });
  } catch (err) {
    console.error("Delete history error:", err);
    res.status(500).json({ error: "Server error" });
  }
};

// Clear all history for logged-in user
const clearHistory = async (req, res) => {
  try {
    await History.deleteMany({ user: req.user.id });

    res.json({ message: "History cleared successfully" });
  } catch (err) {
    console.error("Clear history error:", err);
    res.status(500).json({ error: "Server error" });
  }
};

module.exports = {
  getHistory,
  deleteHistoryItem,
  clearHistory,
};