const rateLimit = require("express-rate-limit");
const { RedisStore } = require("rate-limit-redis");
const redis = require("../config/redis");

const createLimiter = (windowMs, max, message) =>
  rateLimit({
    windowMs,
    max,
    standardHeaders: true,
    legacyHeaders: false,
    message: { message },

    store: new RedisStore({
      sendCommand: (...args) => redis.call(...args),
    }),
  });

const loginLimiter = createLimiter(
  15 * 60 * 1000,
  5,
  "Too many login attempts. Try again later."
);

const registerLimiter = createLimiter(
  60 * 60 * 1000,
  3,
  "Too many registration attempts. Try again later."
);

module.exports = {
  loginLimiter,
  registerLimiter,
};
