const express = require('express');
const router = express.Router();

const coingeckoController = require('../controllers/coingecko');

router.route('/coingecko/yield').get(coingeckoController.getCoinGeckoYield);

module.exports = router;