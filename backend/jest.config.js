module.exports = {
    testEnvironment: "node",

    collectCoverage: true,

    coverageDirectory: "coverage",

    collectCoverageFrom: [
        "src/**/*.js"
    ],

    testMatch: [
        "**/tests/**/*.test.js"
    ]
};