require('dotenv').config();

const express = require('express');
const cors = require('cors');

const documentRoutes = require('./src/routes/documentRoutes');

const app = express();

app.use(cors());
app.use(express.json());

app.get('/health', (req, res) => {
    res.json({
        status: 'ok',
        service: 'RIBIL Backend'
    });
});

app.get('/api/verification/start', (req, res) => {
    res.json({
        success: true,
        surveyNumber: '47/3',
        village: 'Kadubeesanahalli',
        status: 'Verification Started'
    });
});

app.use('/api/documents', documentRoutes);

const PORT = process.env.PORT || 3000;

if (require.main === module) {
    app.listen(PORT, () => {
        console.log(`Server running on port ${PORT}`);
    });
}

module.exports = app;
